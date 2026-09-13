"""
Conector real de Startrack (plataforma GPS).

Escrito contra la documentacion oficial de su API. Sigue el mismo patron que
ai/provider.py, que es el unico que ya probamos bajo presion:

  * `disponible()` es el switch. Sin credenciales, todo esto no existe.
  * NINGUNA funcion lanza excepcion. Devuelven None o lista vacia y el Hub
    sigue con la semilla. La demo no se cae por la red del salon.

Credenciales (backend/.env):
    STARTRACK_HOST       el mismo dominio donde el equipo entra al sistema
    STARTRACK_API_KEY    administrador de usuarios -> pestania "Integraciones (API)"
    STARTRACK_PASSWORD   la MISMA contrasenia del login normal

La autenticacion es basic http auth con el API key en el campo de usuario.

LIMITE DE PETICIONES: 240 por IP cada 2 minutos, y GET /api/devices es mucho
mas estricto (10 cada 5 minutos). Pasarse devuelve HTTP 529 y bloquea TODAS
las peticiones hasta que pase la ventana. Por eso el catalogo de estados se
cachea y /api/devices se llama una sola vez por sincronizacion, nunca por
vehiculo.

Duenio: Wilbert
"""
from __future__ import annotations

import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

from .db import q, x

TIMEOUT = float(os.getenv("STARTRACK_TIMEOUT", "15"))


def _host() -> str | None:
    h = (os.getenv("STARTRACK_HOST") or "").strip().rstrip("/")
    if not h:
        return None
    return h if h.startswith("http") else f"https://{h}"


def disponible() -> bool:
    """El switch. Mientras esto sea False, la vista unificada usa la semilla."""
    return bool(_host() and os.getenv("STARTRACK_API_KEY")
                and os.getenv("STARTRACK_PASSWORD"))


def _get(ruta: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """GET autenticado. Devuelve el JSON o None. Nunca lanza."""
    host = _host()
    if not host:
        return None
    try:
        import httpx

        r = httpx.get(
            f"{host}/api/{ruta.lstrip('/')}",
            params=params or {},
            auth=(os.getenv("STARTRACK_API_KEY", ""),
                  os.getenv("STARTRACK_PASSWORD", "")),
            timeout=TIMEOUT,
        )
        if r.status_code == 529:
            # Rate limit. No reintentamos en caliente: durante la demo es mejor
            # quedarse con el dato anterior que encadenar esperas de minutos.
            print("[startrack] 529: limite de peticiones alcanzado")
            return None
        if r.status_code >= 400:
            print(f"[startrack] {ruta} -> HTTP {r.status_code}")
            return None
        return r.json()
    except Exception as e:  # noqa: BLE001 — a proposito: aqui nada escala
        print(f"[startrack] {ruta} fallo: {type(e).__name__}: {e}")
        return None


_roles: dict[str, str] | None = None


def catalogo_estados_tarea() -> dict[str, str]:
    """Mapa `status id -> workflow_role`, cacheado.

    Es el catalogo que vuelve innecesario adivinar por el nombre del estado:
    un cliente puede llamarle "Limpiando" a lo que sea, pero el rol es 0, 1 o 2.
    No cambia durante una demo, asi que se pide una sola vez.
    """
    global _roles
    if _roles is not None:
        return _roles
    data = _get("job/status") or {}
    _roles = {str(e.get("id")): str(e.get("workflow_role"))
              for e in (data.get("data") or []) if e.get("id") is not None}
    return _roles


def estado_flota() -> list[dict[str, Any]]:
    """GET /api/fleet/status — TODA la flota en UNA sola llamada.

    Es el camino correcto para sincronizar y no lo teniamos. La version
    anterior pedia /api/vehicle/<id> uno por uno mas /api/devices: con 120
    equipos son 241 peticiones contra un limite de 240 cada 2 minutos, o sea
    que se autobloqueaba sola. Esta ruta da lo mismo en una:

        vehId  vehDescr  vehStat  x/y  epoch  event  ignOnHrs  odometer

    `vehDescr` es la Descripcion del vehiculo, que segun el Diccionario de
    Datos de ECON es donde vive el codigo del equipo (CF-03, EXC-01): o sea,
    nuestra llave de cruce viene incluida.

    OJO con `ignOn`: en el propio ejemplo de la documentacion un vehiculo
    "en movimiento" trae ignOn 0 y otro con "ignition off" trae ignOn 1.
    Parece invertido o poco fiable, asi que NO se usa. Para saber si opera
    estan `event` y el avance del horometro.
    """
    d = _get("fleet/status")
    if isinstance(d, list):
        return [x_ for x_ in d if isinstance(x_, dict)]
    return (d or {}).get("data") or []


def vehiculo_por_activo(no_activo: str) -> dict[str, Any] | None:
    """Busca por remote_id — el No. de activo de Nexus tal cual."""
    d = _get(f"vehicle/{no_activo}",
             {"is_remote_id": "true", "include_last_report": "true"})
    return (d or {}).get("data")


def tareas(page_size: int = 500) -> list[dict[str, Any]]:
    d = _get("job", {"page_size": page_size, "sort_by": "start_date",
                     "sort_dir": "desc"})
    return (d or {}).get("data") or []


def dispositivos() -> dict[str, dict[str, Any]]:
    """`vehicle_id -> dispositivo`. UNA sola llamada: el limite aqui es 10/5min."""
    d = _get("devices") or {}
    return {str(x_["vehicle_id"]): x_ for x_ in (d.get("detail") or [])
            if x_.get("vehicle_id") is not None}


def horas_ignicion(vehicle_id: str, dias: int = 2) -> int | None:
    """Segundos con ignicion encendida en los ultimos `dias`.

    Usa `ign_on_time` del resumen agregado, que la documentacion define en
    segundos. NO usa `ign_on_hrs` del detalle por vehiculo: el ejemplo oficial
    trae 100.8 "horas" en un solo dia junto a un init_ign_on_hrs de 584186.4,
    asi que esas dos parecen lecturas de horometro y no duracion. Verificar
    contra un tenant real antes de cambiar esto.
    """
    hasta = date.today()
    desde = hasta - timedelta(days=dias)
    d = _get("vehicles/stats", {"vehicles": vehicle_id,
                                "start_date": desde.isoformat(),
                                "end_date": hasta.isoformat()})
    dias_data = (d or {}).get("data") or {}
    if not dias_data:
        return None
    total = 0
    for dia in dias_data.values():
        try:
            total += int(float(dia.get("ign_on_time") or 0))
        except (TypeError, ValueError):
            continue
    return total


def _codigo_en(texto: str | None) -> str:
    """El codigo del equipo dentro de una descripcion de Startrack.

    `vehDescr` llega como "Mazda - Protege (P-453QRR)" o, en el sandbox de
    ECON, como "CF-03" o "EXC-01 - Excavadora 01". Se normaliza para comparar.
    """
    return (texto or "").strip().upper()


def sincronizar() -> dict[str, Any]:
    """Refresca ps_tareas con lo que Startrack reporta AHORA.

    UNA sola peticion para toda la flota. Solo toca filas que ya existen: la
    correlacion con Nexus la define la solicitud, no el rastreador. Esto
    enriquece, no inventa operaciones.
    """
    if not disponible():
        return {"ok": False, "motivo": "sin credenciales de Startrack",
                "origen": "semilla"}

    flota = estado_flota()
    if not flota:
        return {"ok": False, "motivo": "fleet/status no devolvio vehiculos",
                "origen": "semilla"}

    # Indice por todo lo que puede servir de llave: id interno, descripcion y
    # el codigo suelto dentro de la descripcion.
    indice: dict[str, dict[str, Any]] = {}
    for v in flota:
        for llave in (v.get("vehId"), v.get("vehDescr"), v.get("description")):
            if llave not in (None, ""):
                indice[_codigo_en(str(llave))] = v
        descr = str(v.get("vehDescr") or "")
        if " - " in descr:                     # "EXC-01 - Excavadora 01"
            indice.setdefault(_codigo_en(descr.split(" - ")[0]), v)
        if "(" in descr:                       # "Mazda - Protege (P-453QRR)"
            indice.setdefault(_codigo_en(descr.split("(")[0]), v)

    ahora = time.time()
    actualizadas, sin_encontrar = 0, []

    for fila in q(
        "SELECT t.tarea_id, t.maquinaria, t.remote_id, t.horometro_base,"
        " (SELECT s.no_activo FROM ps_solicitudes s"
        "  WHERE s.maquinaria = t.maquinaria AND s.no_activo IS NOT NULL"
        "  LIMIT 1) AS no_activo"
        " FROM ps_tareas t"
    ):
        v = None
        for cand in (fila.get("remote_id"), fila.get("no_activo"),
                     fila["maquinaria"]):
            if cand and _codigo_en(str(cand)) in indice:
                v = indice[_codigo_en(str(cand))]
                break
        if not v:
            sin_encontrar.append(fila["maquinaria"])
            continue

        # `epoch` es el ultimo reporte en Unix time: de ahi sale coms_age sin
        # tener que tocar /api/devices, cuyo limite es 10 cada 5 minutos.
        epoch = _real(v.get("epoch"))
        coms = int(max(0, ahora - epoch)) if epoch else None

        # ignOnHrs es ACUMULADO, igual que hourmeter. Las horas del periodo
        # son la diferencia contra la linea base, que fija la primera lectura.
        horas = _real(v.get("ignOnHrs"))
        base = fila.get("horometro_base")
        campos: dict[str, Any] = {
            "vehicle_id": str(v.get("vehId") or ""),
            "estado_vehiculo": _entero(v.get("vehStat")),
            "horometro": horas,
            "lat": _real(v.get("y")),          # y = latitud, x = longitud
            "lon": _real(v.get("x")),
            "coms_age_s": coms,
            "ultimo_evento": v.get("eventDescription") or v.get("place"),
        }
        if horas is not None:
            if base is None:
                campos["horometro_base"] = horas
                campos["ign_on_time_s"] = 0
            else:
                campos["ign_on_time_s"] = max(0, int((horas - float(base)) * 3600))
        if epoch:
            campos["ultimo_evento_at"] = datetime.fromtimestamp(
                epoch, timezone.utc).isoformat()
        if coms is not None:
            campos["conexion"] = ("Conectado" if coms < 3600 else "Sin conexion")

        campos = {k: v_ for k, v_ in campos.items() if v_ not in (None, "")}
        sets = ", ".join(f"{k} = ?" for k in campos)
        x(f"UPDATE ps_tareas SET {sets} WHERE tarea_id = ?",
          (*campos.values(), fila["tarea_id"]))
        actualizadas += 1

    return {"ok": True, "origen": "startrack", "peticiones": 1,
            "vehiculos_en_flota": len(flota), "actualizadas": actualizadas,
            "sin_encontrar": sin_encontrar}


def _entero(v: Any) -> int | None:
    try:
        return int(float(v)) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _real(v: Any) -> float | None:
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None
