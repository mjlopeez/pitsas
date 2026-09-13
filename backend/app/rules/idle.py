"""
Ralenti improductivo: motor encendido, sin carga hidraulica ni traslacion,
por mas de 15 minutos.

Es el renglon mas grande del modelo de ahorro: 1 h/dia x 100 maquinas
= ~30,000 galones/anio = ~$120,000.
Duenio: Wilbert
"""
from __future__ import annotations

from datetime import datetime, timedelta

UMBRAL_MIN = 15
GAL_POR_HORA_RALENTI = 1.1     # rango del documento: 0.8 - 1.4
PRECIO_GALON = 4.00


def revisar(asset: dict, ahora: datetime) -> dict | None:
    if (asset.get("engine_state") or "") != "IDLE":
        return None

    desde = asset.get("idle_since")
    if not desde:
        return None

    try:
        t0 = datetime.fromisoformat(desde)
    except ValueError:
        return None
    if t0.tzinfo is None:
        t0 = t0.replace(tzinfo=ahora.tzinfo)

    minutos = (ahora - t0).total_seconds() / 60.0
    if minutos < UMBRAL_MIN:
        return None

    galones = (minutos / 60.0) * GAL_POR_HORA_RALENTI
    return {
        "kind": "ralenti",
        "severity": "media",
        "title": f"Ralenti improductivo: {minutos:.0f} min",
        "detail": (
            f"Sin carga ni traslacion desde hace {minutos:.0f} min en "
            f"{asset.get('assigned_project') or 'obra sin asignar'}. "
            f"Consumo estimado {galones:.1f} gal (${galones * PRECIO_GALON:.2f})."
        ),
        "payload": {
            "minutos": round(minutos, 1),
            "galones": round(galones, 2),
            "costo_usd": round(galones * PRECIO_GALON, 2),
        },
    }
