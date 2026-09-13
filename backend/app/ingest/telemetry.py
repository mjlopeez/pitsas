"""
Ingesta de telemetria: OEM y retrofit por el mismo endpoint.

El jurado tiene que ver esto: CAT, Komatsu, Volvo y un ESP32 sobre bus CAN
entran por la MISMA puerta y salen con la MISMA forma.

Duenio: Emily (adaptadores) / Wilbert (endpoint)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..adapters import ADAPTERS, normalize
from ..events import bump_connector
from ..orchestrator import procesar

router = APIRouter(prefix="/ingest", tags=["ingesta"])


@router.get("/vendors")
def vendors() -> dict[str, list[str]]:
    return {"adaptadores": sorted(ADAPTERS)}


@router.post("/telemetry/{vendor}")
def telemetry(vendor: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Recibe la forma propietaria del fabricante y la normaliza.
    Un payload que no cumple el contrato se RECHAZA y se cuenta: el panel de
    salud de conectores lo muestra. Un rechazo visible vale mas que un dato
    inventado en silencio.
    """
    try:
        ev = normalize(vendor, payload)
    except Exception as exc:  # noqa: BLE001
        bump_connector(f"oem_{vendor}" if vendor != "j1939" else "retrofit_j1939",
                       ok=False, error=str(exc))
        raise HTTPException(status_code=422, detail=f"payload rechazado: {exc}") from exc

    return procesar(ev)


@router.post("/events")
def canonical_passthrough(payload: dict[str, Any]) -> dict[str, Any]:
    """Para quien ya habla canonico (la PWA de campo, por ejemplo)."""
    from ..canonical import CanonicalEvent

    try:
        ev = CanonicalEvent(**payload).with_provenance()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return procesar(ev, idempotency_key=payload.get("idempotency_key"))
