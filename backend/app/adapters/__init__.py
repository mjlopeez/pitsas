"""
Registro de adaptadores. Cada uno traduce la forma propietaria de un
fabricante al contrato canonico. Agregar un fabricante nuevo = un archivo
nuevo aqui, sin tocar nada mas del Hub. Eso es la tesis del proyecto.

Duenio: Emily (hasta 15:00)
"""
from __future__ import annotations

from typing import Any, Callable

from ..canonical import CanonicalEvent
from . import cat, j1939, komatsu, volvo

ADAPTERS: dict[str, Callable[[dict[str, Any]], CanonicalEvent]] = {
    "cat": cat.to_canonical,
    "komatsu": komatsu.to_canonical,
    "volvo": volvo.to_canonical,
    "j1939": j1939.to_canonical,
}


def normalize(vendor: str, payload: dict[str, Any]) -> CanonicalEvent:
    vendor = vendor.lower().strip()
    if vendor not in ADAPTERS:
        raise ValueError(
            f"fabricante '{vendor}' sin adaptador. Disponibles: {sorted(ADAPTERS)}"
        )
    return ADAPTERS[vendor](payload)
