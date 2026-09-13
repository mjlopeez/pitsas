"""Utilidades compartidas por los adaptadores."""
from __future__ import annotations

from datetime import datetime, timezone

L_PER_GAL = 3.78541


def gal(value: float | None, unit: str | None) -> float | None:
    """Todo el Hub trabaja en galones — el modelo de ROI usa $4.00/galon."""
    if value is None:
        return None
    u = (unit or "gal").lower()
    if u in ("l", "lt", "litros", "liter", "liters"):
        return round(value / L_PER_GAL, 2)
    return round(float(value), 2)


def ts(value: str | int | float | None) -> datetime:
    """Acepta ISO 8601, epoch en segundos o milisegundos. Siempre devuelve UTC."""
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, (int, float)):
        secs = value / 1000 if value > 1e11 else value
        return datetime.fromtimestamp(secs, tz=timezone.utc)
    s = str(value).strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def need(payload: dict, *path: str):
    """Lee una ruta anidada y falla claro si no esta. El error va al panel de conectores."""
    cur = payload
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            raise ValueError(f"campo obligatorio ausente: {'.'.join(path)}")
        cur = cur[key]
    return cur
