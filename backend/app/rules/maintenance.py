"""
Mantenimiento preventivo disparado por horometro real, no por calendario.

Regla del documento: servicio cada 250 h, se avisa al llegar a 240.
Duenio: Wilbert
"""
from __future__ import annotations

AVISO_ANTES_H = 10.0


def revisar(asset: dict) -> dict | None:
    horas = asset.get("operating_hours") or 0.0
    ultimo = asset.get("last_service_h") or 0.0
    cada = asset.get("service_every_h") or 250.0

    desde_servicio = horas - ultimo
    if desde_servicio < cada - AVISO_ANTES_H:
        return None

    vencido = desde_servicio >= cada
    return {
        "kind": "mantenimiento",
        "severity": "alta" if vencido else "media",
        "title": (
            f"Servicio {'VENCIDO' if vencido else 'proximo'}: "
            f"{desde_servicio:.0f} h de {cada:.0f}"
        ),
        "detail": (
            f"Horometro {horas:.1f} h. Ultimo servicio a las {ultimo:.1f} h. "
            "Apartar lubricantes y filtros en taller central y proponer la "
            "intervencion en la ventana de menor demanda de la obra."
        ),
        "payload": {
            "horas_desde_servicio": round(desde_servicio, 1),
            "intervalo": cada,
            "vencido": vencido,
        },
    }
