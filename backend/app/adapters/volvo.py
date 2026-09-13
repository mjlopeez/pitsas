"""
Volvo CE — Machine Data API. Otra forma mas: valores envueltos en
{value, unit} y codigos activos en una lista aparte.
"""
from __future__ import annotations

from typing import Any

from ..canonical import CanonicalEvent, DiagnosticAlert, EngineState, Point, Source
from .base import gal, need, ts


def _val(node: Any) -> float | None:
    if isinstance(node, dict):
        v = node.get("value")
        return float(v) if v is not None else None
    return float(node) if node is not None else None


def _unit(node: Any) -> str | None:
    return node.get("unit") if isinstance(node, dict) else None


def to_canonical(p: dict[str, Any]) -> CanonicalEvent:
    asset = need(p, "equipmentId")
    pos = p.get("position") or {}
    fuel = p.get("fuelUsed")

    running = p.get("engineRunning")
    state = None
    if running is True:
        state = EngineState.IDLE if p.get("engineIdle") else EngineState.ON
    elif running is False:
        state = EngineState.OFF

    alerts = [
        DiagnosticAlert(
            code=str(c.get("code")),
            severity=c.get("severity", "media"),
            description=c.get("text"),
        )
        for c in (p.get("activeCodes") or [])
    ]

    ev = CanonicalEvent(
        asset_identifier=str(asset),
        event_timestamp=ts(p.get("snapshotTime")),
        source=Source.OEM_VOLVO,
        location=Point(lat=pos["latitude"], lon=pos["longitude"]) if "latitude" in pos else None,
        operating_hours=_val(p.get("hourMeter")),
        engine_state=state,
        cumulative_fuel=gal(_val(fuel), _unit(fuel)),
        diagnostic_alerts=alerts,
        raw=p,
    )
    return ev.with_provenance()
