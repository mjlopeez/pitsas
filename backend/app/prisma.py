"""
Conector de Prisma / Nexus — el sandbox oficial del hackaton.

Escrito contra `openapi-prisma-econ-1.0.0-hackathon.json`. A diferencia de
Startrack, que usa basic auth, Prisma autentica con **cookie de sesion**:
se hace POST a /api/auth/login y httpx.Client conserva la cookie.

    PRISMA_BASE_URL   https://econ-key.maic.ai
    PRISMA_EMAIL
    PRISMA_PASSWORD

Mismo patron que startrack.py y ai/provider.py: `disponible()` es el switch,
ninguna funcion lanza excepcion, y sin credenciales el Hub sigue con la
semilla. La demo no se cae por la red del salon.

Duenio: Wilbert
"""
from __future__ import annotations

import os
import threading
from typing import Any

from .db import q1, x

BASE_URL_DEFECTO = "https://econ-key.maic.ai"
TIMEOUT = float(os.getenv("PRISMA_TIMEOUT", "20"))

_lock = threading.Lock()
_cliente: Any = None
_sesion_ok = False


def base_url() -> str:
    return (os.getenv("PRISMA_BASE_URL") or BASE_URL_DEFECTO).rstrip("/")


def disponible() -> bool:
    return bool(os.getenv("PRISMA_EMAIL") and os.getenv("PRISMA_PASSWORD"))


def _client() -> Any:
    """Cliente unico: la cookie de sesion vive en el, no en cada llamada."""
    global _cliente
    if _cliente is None:
        import httpx

        _cliente = httpx.Client(base_url=base_url(), timeout=TIMEOUT,
                                follow_redirects=True)
    return _cliente


def _login() -> bool:
    global _sesion_ok
    if _sesion_ok:
        return True
    if not disponible():
        return False
    with _lock:
        if _sesion_ok:
            return True
        try:
            r = _client().post("/api/auth/login", json={
                "email": os.getenv("PRISMA_EMAIL"),
                "password": os.getenv("PRISMA_PASSWORD"),
            })
            if r.status_code >= 400:
                print(f"[prisma] login HTTP {r.status_code}")
                return False
            _sesion_ok = True
            return True
        except Exception as e:  # noqa: BLE001 — aqui nada escala
            print(f"[prisma] login fallo: {type(e).__name__}: {e}")
            return False


def _get(ruta: str, params: dict[str, Any] | None = None) -> Any:
    """GET autenticado. Devuelve el JSON o None. Nunca lanza."""
    global _sesion_ok
    if not _login():
        return None
    try:
        r = _client().get(ruta, params=params or {})
        if r.status_code in (401, 403):
            # La sesion caduco: se reintenta una sola vez.
            _sesion_ok = False
            if not _login():
                return None
            r = _client().get(ruta, params=params or {})
        if r.status_code >= 400:
            print(f"[prisma] {ruta} -> HTTP {r.status_code}")
            return None
        return r.json()
    except Exception as e:  # noqa: BLE001
        print(f"[prisma] {ruta} fallo: {type(e).__name__}: {e}")
        return None


def _lista(data: Any) -> list[dict[str, Any]]:
    """El sandbox a veces envuelve en {items|data|results} y a veces no."""
    if isinstance(data, list):
        return [d for d in data if isinstance(d, dict)]
    if isinstance(data, dict):
        for k in ("items", "data", "results", "rows"):
            if isinstance(data.get(k), list):
                return [d for d in data[k] if isinstance(d, dict)]
    return []


# --- lecturas del sandbox --------------------------------------------------
def yo() -> dict[str, Any] | None:
    return _get("/api/auth/me")


def equipos(**params: Any) -> list[dict[str, Any]]:
    return _lista(_get("/api/maquinaria/equipos", params))


def equipo(eq_id: str) -> dict[str, Any] | None:
    return _get(f"/api/maquinaria/equipos/{eq_id}")


def solicitudes(**params: Any) -> list[dict[str, Any]]:
    return _lista(_get("/api/maquinaria/requests", params))


def solicitud(req_id: str) -> dict[str, Any] | None:
    return _get(f"/api/maquinaria/requests/{req_id}")


def proyectos() -> list[dict[str, Any]]:
    return _lista(_get("/api/projects"))


def fallas(**params: Any) -> list[dict[str, Any]]:
    return _lista(_get("/api/maquinaria/fallas", params))


def _campo(d: dict[str, Any], *nombres: str,
           faltantes: set[str] | None = None) -> Any:
    """El sandbox no garantiza el nombre exacto: se prueban los candidatos.

    Si ninguno acierta se anota en `faltantes`. Sin esto, un nombre que no
    adivinamos entra como NULL EN SILENCIO — y un precio_hora en NULL
    significa exposicion $0, o sea que el Hub diria que no se pierde nada.
    Mejor que la respuesta diga que no supo leerlo.
    """
    for n in nombres:
        if d.get(n) not in (None, ""):
            return d[n]
    if faltantes is not None:
        faltantes.add(nombres[0])
    return None


def sincronizar() -> dict[str, Any]:
    """Trae solicitudes reales del sandbox a ps_solicitudes.

    No borra nada: hace UPSERT. Si el sandbox no responde, la semilla queda
    intacta y la demo sigue igual.
    """
    if not disponible():
        return {"ok": False, "motivo": "sin credenciales de Prisma",
                "origen": "semilla"}

    sols = solicitudes()
    if not sols:
        return {"ok": False, "motivo": "el sandbox no devolvio solicitudes",
                "origen": "semilla"}

    escritas = 0
    faltantes: set[str] = set()
    for s in sols:
        sid = str(_campo(s, "id", "request_id", "solicitud_id",
                         faltantes=faltantes) or "")
        if not sid:
            continue
        eq = s.get("maquinaria") or s.get("equipo") or {}
        if not isinstance(eq, dict):
            eq = {}
        maq = str(_campo(s, "maquinaria_id", "equipo_id")
                  or _campo(eq, "no_activo", "clave", "id")
                  or f"SOL-{sid}-SIN-UNIDAD")

        # Si la semilla YA tiene una solicitud para esta maquina, se escribe
        # sobre ESA fila en vez de crear `PRISMA-<id>`. Sin esto el
        # INSERT OR REPLACE no reemplazaba: duplicaba. El roster terminaba
        # sumando la misma operacion dos veces, una de la semilla y otra del
        # sandbox, y la exposicion salia al doble.
        existente = q1("SELECT solicitud_id FROM ps_solicitudes"
                       " WHERE maquinaria = ? ORDER BY solicitud_id LIMIT 1",
                       (maq,))
        destino_id = (existente or {}).get("solicitud_id") or f"PRISMA-{sid}"

        x("INSERT OR REPLACE INTO ps_solicitudes"
          " (solicitud_id, proyecto_id, proyecto_nombre, tipo_solicitado,"
          "  fecha_inicio, fecha_fin, estado_solicitud, maquinaria,"
          "  estado_maquinaria, clave, no_activo, empresa, clase_equipo,"
          "  precio_hora, horas_minimas, operador, partida_asignada)"
          " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (destino_id,
           str(_campo(s, "proyecto_id", "project_id", faltantes=faltantes) or ""),
           _campo(s, "proyecto_nombre", "project_name", "proyecto", faltantes=faltantes),
           _campo(s, "tipo_solicitado", "tipo", "clase_equipo"),
           _campo(s, "fecha_inicio", "start_date"),
           _campo(s, "fecha_fin", "end_date"),
           _campo(s, "estado", "status", "estado_solicitud", faltantes=faltantes),
           maq,
           _campo(eq, "estado", "estado_maquinaria", faltantes=faltantes),
           _campo(eq, "clave"), _campo(eq, "no_activo"),
           _campo(eq, "empresa"), _campo(eq, "clase_equipo", "tipo"),
           _campo(eq, "precio_hora", "precio_x_hora", faltantes=faltantes),
           _campo(eq, "horas_minimas", "horas_minimas_jornada", faltantes=faltantes),
           _campo(s, "operador", "operador_nombre"),
           _campo(s, "partida", "partida_asignada")))
        escritas += 1

    total = (q1("SELECT COUNT(*) AS n FROM ps_solicitudes") or {"n": 0})["n"]
    resultado = {"ok": True, "origen": "prisma", "escritas": escritas,
                 "solicitudes_totales": total}
    if faltantes:
        # Que salga en la respuesta y no en un log que nadie mira: si
        # `precio_hora` esta aqui, la exposicion en dolares NO es confiable.
        resultado["campos_no_reconocidos"] = sorted(faltantes)
        resultado["aviso"] = ("Hay campos que no se pudieron leer del sandbox."
                              " Revisar la respuesta cruda antes de confiar en"
                              " las cifras derivadas.")
    return resultado
