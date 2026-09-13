"""
Salud de conectores: el unico lugar donde el jurado VE la integracion.

El documento original muestra los resultados de integrar pero nunca el acto
de integrar. Esta vista lo corrige: cuatro origenes distintos, un contrato,
y los rechazos a la vista en vez de escondidos.

Duenio: Majo (vista) / Wilbert (datos)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ..adapters import ADAPTERS
from ..db import q, q1

router = APIRouter(prefix="/api", tags=["conectores"])

ETIQUETAS = {
    "oem_cat": ("Caterpillar", "ISO 15143-3 / AEMP 2.0"),
    "oem_komatsu": ("Komatsu", "API propietaria"),
    "oem_volvo": ("Volvo CE", "Machine Data API"),
    "retrofit_j1939": ("Retrofit CAN", "SAE J1939 (SPN 247/250, DM1)"),
    "field_whatsapp": ("WhatsApp campo", "Voz + NER"),
    "field_ocr": ("OCR tablero", "Vision artificial"),
    "field_pwa": ("PWA offline", "Cola local + sync"),
}


@router.get("/connectors")
def conectores() -> list[dict[str, Any]]:
    stats = {r["source"]: r for r in q("SELECT * FROM connector_stats")}
    out = []
    for src, (nombre, protocolo) in ETIQUETAS.items():
        s = stats.get(src, {})
        acc = s.get("accepted", 0) or 0
        rej = s.get("rejected", 0) or 0
        if rej and acc:
            estado = "degradado"
        elif rej and not acc:
            estado = "caido"
        elif acc:
            estado = "ok"
        else:
            estado = "sin_trafico"
        out.append({
            "source": src,
            "nombre": nombre,
            "protocolo": protocolo,
            "aceptados": acc,
            "rechazados": rej,
            "estado": estado,
            "ultimo_evento": s.get("last_event"),
            "ultimo_error": s.get("last_error"),
        })
    return out


@router.get("/contract")
def contrato() -> dict[str, Any]:
    """El contrato canonico servido como dato: la UI lo pinta como tabla."""
    from ..canonical import PRECEDENCIA, TOLERANCIA

    total = q1("SELECT COUNT(*) AS n FROM events") or {"n": 0}
    return {
        "adaptadores": sorted(ADAPTERS),
        "precedencia": {k: [s.value for s in v] for k, v in PRECEDENCIA.items()},
        "tolerancias": TOLERANCIA,
        "eventos_normalizados": total["n"],
    }
