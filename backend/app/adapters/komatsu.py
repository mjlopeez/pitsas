"""
Komatsu — forma propietaria. Nombres distintos, litros en vez de galones,
horometro llamado SMR (Service Meter Reading) y alarmas con codigo de texto.
Este es el adaptador que demuestra por que hace falta el Hub.
"""
from __future__ import annotations

from typing import Any

from ..canonical import CanonicalEvent, DiagnosticAlert, EngineState, Point, Source
from .base import gal, need, ts

_ESTADO = {
    "RUNNING": EngineState.ON,
    "IDLING": EngineState.IDLE,
    "STOPPED": EngineState.OFF,
    "OFF": EngineState.OFF,
}


def to_canonical(p: dict[str, Any]) -> CanonicalEvent:
    asset = need(p, "machine", "id")
    gps = p.get("gps") or {}

    alerts = [
        DiagnosticAlert(
            code=str(a.get("code")),
            severity=a.get("level", "media"),
            subsystem=a.get("system"),
            description=a.get("desc"),
        )
        for a in (p.get("alarms") or [])
    ]

    ev = CanonicalEvent(
        asset_identifier=str(asset),
        event_timestamp=ts(p.get("ts")),
        source=Source.OEM_KOMATSU,
        location=Point(lat=gps["lat"], lon=gps["lng"]) if "lat" in gps else None,
        operating_hours=float(p["smr"]) if p.get("smr") is not None else None,
        engine_state=_ESTADO.get(str(p.get("engine", "")).upper()),
        cumulative_fuel=gal(p.get("fuel_l"), "l"),
        diagnostic_alerts=alerts,
        raw=p,
    )
    return ev.with_provenance()
