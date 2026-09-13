"""Flota, obras y alertas para el Command Center. Duenio: Wilbert / consume Majo."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..db import jloads, q, q1

router = APIRouter(prefix="/api", tags=["flota"])


def _hydrate(a: dict[str, Any]) -> dict[str, Any]:
    a["provenance"] = jloads(a.get("provenance"), {})
    horas = a.get("operating_hours") or 0
    ultimo = a.get("last_service_h") or 0
    cada = a.get("service_every_h") or 250
    a["horas_desde_servicio"] = round(horas - ultimo, 1)
    a["pct_servicio"] = round(min(1.0, (horas - ultimo) / cada) * 100, 1) if cada else 0
    return a


@router.get("/assets")
def listar(estado: str | None = None, obra: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM assets"
    where, params = [], []
    if estado:
        where.append("state = ?")
        params.append(estado)
    if obra:
        where.append("assigned_project = ?")
        params.append(obra)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY state, asset_identifier"
    return [_hydrate(a) for a in q(sql, tuple(params))]


@router.get("/assets/{asset_id}")
def detalle(asset_id: str) -> dict[str, Any]:
    a = q1("SELECT * FROM assets WHERE asset_identifier = ?", (asset_id,))
    if not a:
        raise HTTPException(status_code=404, detail="activo no encontrado")
    a = _hydrate(a)
    a["alertas"] = q(
        "SELECT * FROM alerts WHERE asset_identifier = ? AND status = 'abierta'"
        " ORDER BY created_at DESC LIMIT 20", (asset_id,))
    a["eventos"] = q(
        "SELECT id, source, event_timestamp, received_at FROM events"
        " WHERE asset_identifier = ? ORDER BY id DESC LIMIT 20", (asset_id,))
    return a


@router.get("/projects")
def proyectos() -> list[dict[str, Any]]:
    return q("SELECT * FROM projects ORDER BY name")


@router.get("/alerts")
def alertas(status: str = "abierta", limit: int = 50) -> list[dict[str, Any]]:
    rows = q("SELECT * FROM alerts WHERE status = ? ORDER BY id DESC LIMIT ?", (status, limit))
    for r in rows:
        r["payload"] = jloads(r.get("payload"), {})
    return rows


@router.post("/alerts/{alert_id}/cerrar")
def cerrar(alert_id: int) -> dict[str, str]:
    from ..db import x

    x("UPDATE alerts SET status = 'cerrada' WHERE id = ?", (alert_id,))
    return {"status": "cerrada"}


@router.post("/assets/{asset_id}/servicio")
def cerrar_servicio(asset_id: str) -> dict[str, Any]:
    """
    El taller cierra el servicio: mueve el ultimo mantenimiento al horometro
    actual, cierra las alertas de mantenimiento y devuelve la maquina a
    operacion. Sin esto una maquina entra a EN_MANTENIMIENTO y no sale nunca.
    """
    from ..canonical import AssetState
    from ..db import x
    from ..events import publish

    a = q1("SELECT * FROM assets WHERE asset_identifier = ?", (asset_id,))
    if not a:
        raise HTTPException(status_code=404, detail="activo no encontrado")

    horas = a.get("operating_hours") or 0
    x("UPDATE assets SET last_service_h = ?, state = ? WHERE asset_identifier = ?",
      (horas, AssetState.DISPONIBLE.value, asset_id))
    x("UPDATE alerts SET status = 'cerrada'"
      " WHERE asset_identifier = ? AND kind = 'mantenimiento' AND status = 'abierta'",
      (asset_id,))

    publish("asset", {"asset_identifier": asset_id,
                      "state": AssetState.DISPONIBLE.value,
                      "operating_hours": horas})
    return {"status": "servicio cerrado", "asset_identifier": asset_id,
            "last_service_h": horas}
