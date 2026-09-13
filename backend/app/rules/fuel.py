"""
Conciliacion de combustible: lo que dice el cisterna contra lo que dice el activo.

Cualquier desviacion arriba del 5% abre ticket — derrame, caudalimetro
descalibrado o extraccion indebida. El 5% es el numero del documento y es el
detalle que demuestra que el equipo entendio el negocio, no solo la API.
Duenio: Wilbert
"""
from __future__ import annotations

TOLERANCIA = 0.05


def conciliar(asset_id: str, galones_declarados: float, delta_telemetria: float | None) -> dict | None:
    """
    galones_declarados: lo que el motorista del cisterna registro por WhatsApp.
    delta_telemetria:   el aumento que vio el sensor/contador del activo.
    """
    if delta_telemetria is None or galones_declarados <= 0:
        return None

    desvio = abs(galones_declarados - delta_telemetria) / galones_declarados
    if desvio <= TOLERANCIA:
        return None

    return {
        "kind": "conciliacion",
        "severity": "alta",
        "title": f"Descuadre de diesel: {desvio * 100:.1f}%",
        "detail": (
            f"El vale declara {galones_declarados:.1f} gal y la telemetria de "
            f"{asset_id} registra {delta_telemetria:.1f} gal. "
            "Fuera de la tolerancia del 5%: revisar derrame, calibracion del "
            "caudalimetro o extraccion indebida."
        ),
        "payload": {
            "declarado": round(galones_declarados, 2),
            "telemetria": round(delta_telemetria, 2),
            "desvio_pct": round(desvio * 100, 2),
            "tolerancia_pct": TOLERANCIA * 100,
        },
    }
