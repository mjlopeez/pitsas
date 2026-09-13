"""
Webhooks de Startrack — la integracion en tiempo real.

La diferencia con el conector de `startrack.py` es el sentido de la flecha.
El conector PREGUNTA (y paga el limite de 240 peticiones cada 2 minutos).
Esto ESCUCHA: Startrack empuja cada evento en cuanto ocurre, sin polling.

Startrack define dos rebotes distintos y aqui se atienden los dos:

  Ubicaciones  Tech -> Rebote de datos. Una copia de cada evento de cada
               dispositivo. Trae `remote_id` (nuestra llave), `hourmeter`,
               `ign_on` y `veh_status`: TODO lo que el motor de correlacion
               necesita, sin consultar nada.
  Alertas      Las reglas que el usuario configura en Startrack. Trae el
               horometro al momento de la alerta (`ignOnTime`).

Ninguno de los dos endpoint falla con 4xx/5xx si el cuerpo viene raro: un
webhook que devuelve error hace que la plataforma de origen reintente o
deshabilite el rebote. Se responde 200 con el detalle de lo que se ignoro, y
queda contado en connector_stats para que sea VISIBLE en el tablero. Es la
misma decision que ya tomamos con los adaptadores OEM: rechazar a la vista,
nunca en silencio.

Duenio: Wilbert
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from ..correlacion import vista_unificada
from ..db import q, q1, x
from ..events import bump_connector, publish

router = APIRouter(prefix="/webhooks/startrack", tags=["webhooks"])

# Codigos del Location Data Object. El 3/2 son los que mueven el horometro.
COD_EN_MOVIMIENTO = 0
COD_PARO = 1
COD_IGNICION_OFF = 2
COD_IGNICION_ON = 3

ETIQUETA_CODIGO = {
    COD_EN_MOVIMIENTO: "En movimiento",
    COD_PARO: "Paro",
    COD_IGNICION_OFF: "Ignicion apagada",
    COD_IGNICION_ON: "Ignicion encendida",
}


def _tareas_de(remote_id: str) -> list[dict[str, Any]]:
    """Tareas que cruzan con ese remote_id.

    Se busca por las tres llaves posibles porque el rebote puede llegar antes
    de que alguien haya llenado `remote_id` en Startrack: en ese caso el
    identificador que manda es el que ya teniamos de Nexus.
    """
    return q(
        "SELECT t.* FROM ps_tareas t"
        " WHERE t.remote_id = ? OR t.maquinaria = ?"
        "    OR EXISTS (SELECT 1 FROM ps_solicitudes s"
        "               WHERE s.maquinaria = t.maquinaria AND s.no_activo = ?)",
        (remote_id, remote_id, remote_id),
    )


def _aplicar(tarea: dict[str, Any], campos: dict[str, Any]) -> None:
    campos = {k: v for k, v in campos.items() if v is not None}
    if not campos:
        return
    sets = ", ".join(f"{k} = ?" for k in campos)
    x(f"UPDATE ps_tareas SET {sets} WHERE tarea_id = ?",
      (*campos.values(), tarea["tarea_id"]))


def _coord(v: Any) -> float | None:
    """Grados decimales, venga como venga.

    Startrack manda las coordenadas de dos formas segun el formato del rebote:
    el formato 1 en grados decimales ("lat": "10.67338") y el formato 2 en
    enteros escalados por 1e7 ("lat": 1067338). El Diccionario de Datos de
    ECON documenta las geocercas igual: 133376152 son 13.3376152 grados.

    Ninguna latitud valida pasa de 90 ni ninguna longitud de 180, asi que el
    valor absoluto por encima de 180 solo puede ser la version escalada.
    Sin esto, el primer lote en formato 2 manda los equipos a cien millones
    de grados y el mapa queda vacio.
    """
    n = _num(v)
    if n is None:
        return None
    return n / 1e7 if abs(n) > 180 else n


def _num(v: Any, entero: bool = False) -> Any:
    try:
        if v is None or v == "":
            return None
        return int(float(v)) if entero else float(v)
    except (TypeError, ValueError):
        return None


def _procesar_ubicacion(u: dict[str, Any]) -> dict[str, Any] | None:
    """Un Location Data Object -> ps_tareas. None si no se pudo cruzar."""
    remote = str(u.get("remote_id") or "").strip()
    if not remote:
        return None

    tareas = _tareas_de(remote)
    if not tareas:
        return None

    codigo = _num(u.get("code"), entero=True)
    # CUIDADO: `hourmeter` es el horometro ACUMULADO de toda la vida del
    # equipo (4523.5 h), no las horas de la jornada. Tomarlo como horas
    # medidas es el mismo error que ya habiamos marcado para `ign_on_hrs`.
    # Las horas del periodo son la DIFERENCIA contra la lectura del inicio,
    # y esa linea base se fija con la primera lectura que llega.
    horas = _num(u.get("hourmeter"))
    campos = {
        "vehicle_id": str(u["vid"]) if u.get("vid") is not None else None,
        "remote_id": remote,
        "estado_vehiculo": _num(u.get("veh_status"), entero=True),
        "horometro": horas,
        "lat": _coord(u.get("lat")),
        "lon": _coord(u.get("lon")),
        "ultimo_evento": ETIQUETA_CODIGO.get(codigo, f"Evento {codigo}"),
        "ultimo_evento_at": u.get("event_time") or u.get("system_time"),
        # Acaba de reportar: por definicion la antiguedad del ultimo contacto
        # es cero. Esto es lo que apaga la alerta de conexion sola.
        "coms_age_s": 0,
    }
    if u.get("placename"):
        campos["conexion"] = "Conectado"

    for t in tareas:
        propios = dict(campos)
        if horas is not None:
            base = t.get("horometro_base")
            if base is None:
                # Primera lectura: es la linea base, no 4523 horas trabajadas.
                propios["horometro_base"] = horas
                propios["ign_on_time_s"] = 0
            else:
                propios["ign_on_time_s"] = max(0, int((horas - float(base)) * 3600))
        _aplicar(t, propios)
    return {"remote_id": remote, "tareas": [t["tarea_id"] for t in tareas],
            "evento": campos["ultimo_evento"]}


def _revisar_riesgo(remote_id: str) -> None:
    """Si el evento deja la operacion en riesgo, se abre alerta y se avisa.

    Aqui esta el valor real del webhook: Startrack cambia el estado del
    vehiculo a Mantenimiento un martes y el Hub lo sabe EN ESE MOMENTO, no
    cuando alguien abra el tablero el jueves.
    """
    for t in q("SELECT * FROM ps_tareas WHERE remote_id = ?", (remote_id,)):
        for op in vista_unificada(t["maquinaria"]):
            if op["nivel"] not in ("critico", "alerta"):
                continue
            ya = q1(
                "SELECT id FROM alerts WHERE asset_identifier = ? AND kind = ?"
                " AND status = 'abierta' AND title = ?",
                (op["maquinaria"], "conciliacion", op["etiqueta"]),
            )
            if ya:
                continue
            aid = x(
                "INSERT INTO alerts (asset_identifier, kind, severity, title, detail)"
                " VALUES (?,?,?,?,?)",
                (op["maquinaria"], "conciliacion",
                 "alta" if op["nivel"] == "critico" else "media",
                 op["etiqueta"], f"{op['interpretacion']} Accion: {op['accion']}"
                 f" ({op['responsable']})."),
            )
            publish("alert", {"id": aid, "asset_identifier": op["maquinaria"],
                              "kind": "conciliacion", "title": op["etiqueta"],
                              "responsable": op["responsable"]})


@router.post("/ubicaciones")
async def ubicaciones(req: Request) -> dict[str, Any]:
    """Rebote de datos de Startrack. Acepta los dos formatos documentados.

    Formato 1: un objeto.   Formato 2: [n, [objetos]].
    """
    try:
        cuerpo = await req.json()
    except Exception:
        bump_connector("startrack_webhook", False, "cuerpo no es JSON")
        return {"ok": False, "motivo": "cuerpo no es JSON", "procesados": 0}

    # Formato 2 llega como [cantidad, [ ... ]]; formato 1 como un objeto solo.
    if isinstance(cuerpo, list):
        lote = cuerpo[1] if len(cuerpo) == 2 and isinstance(cuerpo[1], list) else cuerpo
    else:
        lote = [cuerpo]

    aplicados, sin_cruce = [], []
    for u in lote:
        if not isinstance(u, dict):
            continue
        r = _procesar_ubicacion(u)
        (aplicados if r else sin_cruce).append(
            r or str(u.get("remote_id") or u.get("vid") or "?"))

    for r in aplicados:
        _revisar_riesgo(r["remote_id"])
        publish("ps_tarea", r)

    bump_connector("startrack_webhook", bool(aplicados),
                   f"{len(sin_cruce)} sin cruce" if sin_cruce else None)
    return {"ok": True, "procesados": len(aplicados),
            "sin_cruce": sin_cruce, "detalle": aplicados}


@router.post("/alertas")
async def alertas(req: Request) -> dict[str, Any]:
    """Alert Webhook: las reglas que el usuario configura dentro de Startrack.

    `ignOnTime` es, textual en su documentacion, "el valor del horometro en el
    momento de la alerta". Se usa para refrescar las horas medidas.
    """
    try:
        a = await req.json()
    except Exception:
        bump_connector("startrack_alertas", False, "cuerpo no es JSON")
        return {"ok": False, "motivo": "cuerpo no es JSON"}

    if not isinstance(a, dict):
        bump_connector("startrack_alertas", False, "cuerpo no es un objeto")
        return {"ok": False, "motivo": "cuerpo no es un objeto"}

    # El Alert Data Object no garantiza remote_id: trae `vehicle` como texto
    # ("descripcion (PLACA)"). Se intenta el remote_id y se cae al texto.
    remote = str(a.get("remote_id") or "").strip()
    tareas = _tareas_de(remote) if remote else []
    if not tareas and a.get("vehicle"):
        # El identificador de Nexus suele venir dentro de la descripcion.
        for t in q("SELECT * FROM ps_tareas"):
            llave = t.get("remote_id") or t.get("maquinaria") or ""
            if llave and llave in str(a["vehicle"]):
                tareas = [t]
                break

    if not tareas:
        bump_connector("startrack_alertas", False,
                       f"sin cruce: {a.get('vehicle') or remote or '?'}")
        return {"ok": True, "procesados": 0,
                "motivo": "ninguna tarea cruza con ese vehiculo"}

    # `ignOnTime` es, textual, "el valor del horometro": lectura acumulada,
    # no duracion. Mismo trato que en el rebote de ubicaciones.
    horas = _num(a.get("ignOnTime"))
    campos = {
        "ultimo_evento": a.get("event") or a.get("messageId") or "Alerta",
        "horometro": horas,
        "lat": _coord(a.get("lat")),
        "lon": _coord(a.get("lon")),
        "coms_age_s": 0,
    }
    for t in tareas:
        propios = dict(campos)
        if horas is not None:
            base = t.get("horometro_base")
            if base is None:
                propios["horometro_base"] = horas
                propios["ign_on_time_s"] = 0
            else:
                propios["ign_on_time_s"] = max(0, int((horas - float(base)) * 3600))
        _aplicar(t, propios)
        publish("ps_tarea", {"tarea_id": t["tarea_id"],
                             "evento": campos["ultimo_evento"]})

    for t in tareas:
        if t.get("remote_id"):
            _revisar_riesgo(t["remote_id"])

    bump_connector("startrack_alertas", True)
    return {"ok": True, "procesados": len(tareas),
            "tareas": [t["tarea_id"] for t in tareas],
            "evento": campos["ultimo_evento"]}
