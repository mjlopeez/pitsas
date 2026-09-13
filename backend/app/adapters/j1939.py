"""
Modulo retrofit de bajo coste sobre el bus CAN (SAE J1939).

Es el adaptador que iguala la flota vieja con la nueva: el volteo de 2009
sin telemetria de fabrica entra al Hub con el mismo contrato que una CAT 320
recien salida de agencia. Ese es el argumento central frente al jurado.

SPN 247 = Total Engine Hours
SPN 250 = Total Fuel Used
DM1     = codigos de falla activos
"""
from __future__ import annotations

from typing import Any

from ..canonical import CanonicalEvent, DiagnosticAlert, EngineState, Point, Source
from .base import gal, need, ts

# Ralenti segun el bus: motor girando pero sin carga ni traslacion.
RPM_MIN_ENCENDIDO = 200
CARGA_RALENTI_PCT = 25


def to_canonical(p: dict[str, Any]) -> CanonicalEvent:
    asset = p.get("vin") or need(p, "device_id")
    spn = p.get("spn") or {}
    gnss = p.get("gnss") or {}

    rpm = p.get("rpm")
    carga = p.get("load_pct")
    state = None
    if rpm is not None:
        if rpm < RPM_MIN_ENCENDIDO:
            state = EngineState.OFF
        elif carga is not None and carga < CARGA_RALENTI_PCT:
            state = EngineState.IDLE
        else:
            state = EngineState.ON

    alerts = [
        DiagnosticAlert(
            code=f"SPN{d.get('spn')}/FMI{d.get('fmi')}",
            spn=d.get("spn"),
            fmi=d.get("fmi"),
            severity=d.get("severity", "media"),
            description=d.get("desc"),
        )
        for d in (p.get("dm1") or [])
    ]

    horas = spn.get("247", spn.get(247))
    combustible = spn.get("250", spn.get(250))

    ev = CanonicalEvent(
        asset_identifier=str(asset),
        event_timestamp=ts(p.get("epoch") or p.get("ts")),
        source=Source.RETROFIT_J1939,
        location=Point(lat=gnss["lat"], lon=gnss["lon"]) if "lat" in gnss else None,
        operating_hours=float(horas) if horas is not None else None,
        engine_state=state,
        cumulative_fuel=gal(combustible, p.get("fuel_unit", "l")),
        diagnostic_alerts=alerts,
        raw=p,
    )
    return ev.with_provenance()
