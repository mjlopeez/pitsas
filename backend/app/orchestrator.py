"""
Orquestador: lo que convierte el Hub de un tablero en un sistema.

Cada evento canonico pasa por aqui una sola vez:
  1. se guarda en el log append-only
  2. se proyecta sobre el activo RESPETANDO LA PRECEDENCIA POR CAMPO
  3. si una fuente de menor autoridad contradice a una mayor -> ticket
  4. corren las reglas (falla, mantenimiento, ralenti)
  5. se recalcula el estado del activo
  6. se publica por SSE al Command Center

Duenio: Wilbert
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from .canonical import (
    TOLERANCIA,
    AssetState,
    CanonicalEvent,
    EngineState,
    FieldProvenance,
    Source,
    gana,
)
from .db import jloads, q1, x
from .events import append, bump_connector, publish
from .rules import fuel as r_fuel
from .rules import idle as r_idle
from .rules import maintenance as r_maint

# Campos que se proyectan del evento al estado actual del activo.
CAMPOS_PROYECTADOS = ("operating_hours", "cumulative_fuel", "engine_state",
                      "assigned_project", "location")


def _geocerca(lat: float, lon: float) -> str | None:
    """
    Asigna la obra por geocerca. Radio simple en grados aproximados:
    alcanza de sobra para El Salvador y evita traer una libreria geoespacial.
    """
    rows = q1(
        "SELECT project_id, name,"
        "  ((lat-?)*(lat-?) + (lon-?)*(lon-?)) AS d2, radius_m"
        " FROM projects ORDER BY d2 ASC LIMIT 1",
        (lat, lat, lon, lon),
    )
    if not rows:
        return None
    # 1 grado ~ 111 km
    radio_grados = (rows["radius_m"] or 1500) / 111_000.0
    return rows["project_id"] if rows["d2"] <= radio_grados ** 2 else None


def _asegurar_activo(asset_id: str, ev: CanonicalEvent) -> dict:
    a = q1("SELECT * FROM assets WHERE asset_identifier = ?", (asset_id,))
    if a:
        return a
    # Activo desconocido: se crea igual. Un dato que llega no se descarta
    # porque el maestro este incompleto — eso es justo el silo que atacamos.
    marca = {
        Source.OEM_CAT: "Caterpillar",
        Source.OEM_KOMATSU: "Komatsu",
        Source.OEM_VOLVO: "Volvo",
    }.get(ev.source, "Desconocido")
    x(
        "INSERT INTO assets (asset_identifier, make, telemetry, state) VALUES (?,?,?,?)",
        (asset_id, marca,
         "oem" if ev.source.value.startswith("oem") else "retrofit",
         AssetState.DISPONIBLE.value),
    )
    return q1("SELECT * FROM assets WHERE asset_identifier = ?", (asset_id,))


def _alerta(asset_id: str, a: dict) -> int:
    aid = x(
        "INSERT INTO alerts (asset_identifier, kind, severity, title, detail, payload)"
        " VALUES (?,?,?,?,?,?)",
        (asset_id, a["kind"], a.get("severity", "media"), a["title"],
         a.get("detail"), json.dumps(a.get("payload", {}), ensure_ascii=False)),
    )
    publish("alert", {"id": aid, "asset_identifier": asset_id, **a})
    return aid


def _estado(a: dict, tiene_falla_activa: bool) -> str:
    if a.get("state") in (AssetState.EN_MANTENIMIENTO.value, AssetState.EN_TRASLADO.value):
        return a["state"]
    if tiene_falla_activa:
        return AssetState.FALLA.value
    motor = a.get("engine_state")
    if motor == EngineState.IDLE.value:
        return AssetState.RALENTI.value
    if motor == EngineState.ON.value:
        return AssetState.OPERANDO.value
    return AssetState.DISPONIBLE.value


def procesar(ev: CanonicalEvent, idempotency_key: str | None = None) -> dict:
    """Punto unico de entrada. Devuelve un resumen para la respuesta HTTP."""
    ahora = datetime.now(timezone.utc)

    ev_id = append(ev, idempotency_key)
    if ev_id is None:
        return {"status": "duplicado", "asset_identifier": ev.asset_identifier}

    bump_connector(ev.source.value, ok=True)

    a = _asegurar_activo(ev.asset_identifier, ev)
    prov_actual: dict = jloads(a.get("provenance"), {})

    # Se guarda antes de proyectar: la conciliacion de diesel necesita el valor
    # previo, y la proyeccion lo sobrescribe unas lineas mas abajo.
    fuel_previo = a.get("cumulative_fuel")
    base_refuel = a.get("last_refuel_fuel")

    cambios: dict = {}
    tickets: list[dict] = []

    # --- proyeccion con precedencia ------------------------------------------
    for campo in CAMPOS_PROYECTADOS:
        nuevo = getattr(ev, campo, None)
        if nuevo is None:
            continue

        duenio_actual = None
        if campo in prov_actual:
            try:
                duenio_actual = Source(prov_actual[campo]["source"])
            except (KeyError, ValueError):
                duenio_actual = None

        if not gana(campo, ev.source, duenio_actual):
            # Fuente con menos autoridad. Solo abre ticket si además contradice.
            tol = TOLERANCIA.get(campo)
            actual = a.get(campo)
            if tol is not None and isinstance(actual, (int, float)) and isinstance(nuevo, (int, float)):
                if actual and abs(nuevo - actual) / max(abs(actual), 1e-9) > (
                    tol if tol < 1 else tol / max(abs(actual), 1e-9)
                ):
                    tickets.append({
                        "kind": "conciliacion",
                        "severity": "media",
                        "title": f"Discrepancia en {campo}",
                        "detail": (
                            f"{ev.source.value} reporta {nuevo} pero la fuente de "
                            f"mayor autoridad ({duenio_actual.value if duenio_actual else 'n/d'}) "
                            f"tiene {actual}. No se sobrescribio."
                        ),
                        "payload": {"campo": campo, "propuesto": nuevo, "vigente": actual,
                                    "fuente_propuesta": ev.source.value},
                    })
            continue

        if campo == "location":
            cambios["lat"] = nuevo.lat
            cambios["lon"] = nuevo.lon
            obra = _geocerca(nuevo.lat, nuevo.lon)
            if obra:
                cambios["assigned_project"] = obra
                prov_actual["assigned_project"] = FieldProvenance(
                    source=ev.source, confidence=1.0
                ).model_dump(mode="json")
        elif campo == "engine_state":
            cambios["engine_state"] = nuevo.value
            if nuevo == EngineState.IDLE and a.get("engine_state") != EngineState.IDLE.value:
                cambios["idle_since"] = ahora.isoformat()
            elif nuevo != EngineState.IDLE:
                cambios["idle_since"] = None
        else:
            cambios[campo] = nuevo

        p = ev.provenance.get(campo)
        prov_actual[campo] = (p or FieldProvenance(source=ev.source)).model_dump(mode="json")

    if cambios:
        cambios["updated_at"] = ahora.isoformat()
        sets = ", ".join(f"{k} = ?" for k in cambios)
        x(f"UPDATE assets SET {sets}, provenance = ? WHERE asset_identifier = ?",
          (*cambios.values(), json.dumps(prov_actual, ensure_ascii=False), ev.asset_identifier))

    a = q1("SELECT * FROM assets WHERE asset_identifier = ?", (ev.asset_identifier,))

    # --- reglas ---------------------------------------------------------------
    alertas: list[dict] = list(tickets)

    for d in ev.diagnostic_alerts:
        alertas.append({
            "kind": "falla",
            "severity": d.severity or "media",
            "title": f"Codigo de falla {d.code}",
            "detail": d.description or (f"Subsistema {d.subsystem}" if d.subsystem else None),
            "payload": d.model_dump(mode="json"),
        })

    m = r_maint.revisar(a)
    if m:
        alertas.append(m)

    i = r_idle.revisar(a, ahora)
    if i:
        alertas.append(i)

    # --- carga de material ----------------------------------------------------
    # El concreto y el asfalto son perecederos y sus campos tienen duenio
    # exclusivo por unidad de negocio. Ver cargas.py.
    lote = None
    if ev.carga is not None:
        from .cargas import proyectar

        lote, alertas_carga = proyectar(ev, ahora)
        alertas.extend(alertas_carga)

    # --- conciliacion de diesel -----------------------------------------------
    # Sobre un ciclo de abastecimiento, lo entregado deberia igualar lo
    # consumido. Si no cuadra mas del 5 %, es derrame, caudalimetro
    # descalibrado o extraccion indebida. Es el numero del documento.
    if ev.fuel_delivered:
        consumido = None
        base = base_refuel if base_refuel is not None else fuel_previo
        actual = a.get("cumulative_fuel")
        if base is not None and actual is not None:
            consumido = round(actual - base, 2)

        t = r_fuel.conciliar(ev.asset_identifier, ev.fuel_delivered, consumido)
        if t:
            alertas.append(t)

        x("UPDATE assets SET last_refuel_fuel = ?, last_refuel_at = ?"
          " WHERE asset_identifier = ?",
          (actual, ahora.isoformat(), ev.asset_identifier))

    ids = [_alerta(ev.asset_identifier, al) for al in alertas]

    # --- estado ---------------------------------------------------------------
    # Un servicio vencido saca la maquina de operacion: es lo que le da respaldo
    # a la orden de trabajo del minuto 2 de la demo.
    if m and m["payload"].get("vencido") and a.get("state") != AssetState.EN_TRASLADO.value:
        x("UPDATE assets SET state = ? WHERE asset_identifier = ?",
          (AssetState.EN_MANTENIMIENTO.value, ev.asset_identifier))
        a["state"] = AssetState.EN_MANTENIMIENTO.value

    nuevo_estado = _estado(a, tiene_falla_activa=bool(ev.diagnostic_alerts))
    if nuevo_estado != a.get("state"):
        x("UPDATE assets SET state = ? WHERE asset_identifier = ?",
          (nuevo_estado, ev.asset_identifier))
        a["state"] = nuevo_estado

    publish("asset", {
        "asset_identifier": a["asset_identifier"],
        "state": a["state"],
        "engine_state": a.get("engine_state"),
        "operating_hours": a.get("operating_hours"),
        "cumulative_fuel": a.get("cumulative_fuel"),
        "lat": a.get("lat"), "lon": a.get("lon"),
        "assigned_project": a.get("assigned_project"),
        "provenance": prov_actual,
        "make": a.get("make"), "model": a.get("model"), "kind": a.get("kind"),
    })
    publish("event", {
        "id": ev_id,
        "asset_identifier": ev.asset_identifier,
        "source": ev.source.value,
        "event_timestamp": ev.event_timestamp.isoformat(),
        "note": ev.note,
        "alertas": len(ids),
    })

    if lote:
        from .cargas import estado_carga

        publish("carga", estado_carga(lote) or {"lote": lote})

    return {
        "status": "ok",
        "event_id": ev_id,
        "asset_identifier": ev.asset_identifier,
        "state": a["state"],
        "alertas": ids,
        "tickets_conciliacion": len(tickets),
        "lote": lote,
    }
