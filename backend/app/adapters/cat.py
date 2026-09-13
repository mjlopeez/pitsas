"""
Caterpillar — ISO 15143-3 / AEMP 2.0 nativo.
El caso facil: el fabricante ya habla el estandar.
"""
from __future__ import annotations

from typing import Any

from ..canonical import CanonicalEvent, DiagnosticAlert, EngineState, Point, Source
from .base import gal, need, ts


def to_canonical(p: dict[str, Any]) -> CanonicalEvent:
    header = need(p, "EquipmentHeader")
    asset = header.get("SerialNumber") or need(p, "EquipmentHeader", "OEMSerialNumber")

    loc = p.get("Location") or {}
    hours = (p.get("CumulativeOperatingHours") or {}).get("Hour")
    fuel = p.get("CumulativeFuelUsed") or {}

    running = (p.get("EngineStatus") or {}).get("Running")
    state = None
    if running is True:
        state = EngineState.IDLE if (p.get("EngineStatus") or {}).get("Idle") else EngineState.ON
    elif running is False:
        state = EngineState.OFF

    alerts = [
        DiagnosticAlert(
            code=f"SPN{f.get('SPN')}/FMI{f.get('FMI')}",
            spn=f.get("SPN"),
            fmi=f.get("FMI"),
            severity=f.get("Severity", "media"),
            description=f.get("Description"),
        )
        for f in (p.get("FaultCodes") or [])
    ]

    ev = CanonicalEvent(
        asset_identifier=str(asset),
        event_timestamp=ts(p.get("SnapshotTime") or loc.get("datetime")),
        source=Source.OEM_CAT,
        location=Point(lat=loc["Latitude"], lon=loc["Longitude"]) if "Latitude" in loc else None,
        operating_hours=float(hours) if hours is not None else None,
        engine_state=state,
        cumulative_fuel=gal(fuel.get("FuelConsumed"), fuel.get("FuelUnits")),
        diagnostic_alerts=alerts,
        raw=p,
    )
    return ev.with_provenance()
