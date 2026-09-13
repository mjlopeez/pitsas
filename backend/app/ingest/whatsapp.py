"""
Entrada conversacional: WhatsApp como interfaz principal de campo.

Dos puertas:
  /ingest/whatsapp          webhook real de Meta (GET verifica, POST recibe)
  /ingest/whatsapp/sim      simulador con la MISMA tuberia aguas abajo

El simulador no es una maqueta: recibe el mismo texto/audio/foto y pasa por
el mismo NER, el mismo OCR y el mismo orquestador. Es el respaldo si el alta
en Meta no sale a tiempo, y el jurado ve exactamente el mismo resultado.

Duenio: Wilbert
"""
from __future__ import annotations

import base64
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..ai import ner, ocr, stt
from ..canonical import (
    CanonicalEvent,
    DiagnosticAlert,
    FieldProvenance,
    Point,
    Source,
)
from ..db import q1
from ..orchestrator import procesar

router = APIRouter(prefix="/ingest/whatsapp", tags=["whatsapp"])

VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN", "hub-econ-2026")


def resolver_activo(
    mencion: str | None, extraido: str | None, proyecto_id: str | None = None
) -> str | None:
    """
    'la 320 aqui en San Diego' -> CAT-320-04.

    La persona no dice el serial, dice el modelo y donde esta. El Hub tiene que
    cerrar esa brecha contra los datos maestros o el operador no lo va a usar.
    La obra desambigua: hay veinte "320" en la flota, pero una sola en San Diego.
    """
    for candidato in (extraido, mencion):
        if not candidato:
            continue

        # 1. coincidencia exacta de serial
        row = q1("SELECT asset_identifier FROM assets WHERE asset_identifier = ?", (candidato,))
        if row:
            return row["asset_identifier"]

        # 2. el modelo dentro de la obra mencionada (el caso normal en campo)
        if proyecto_id:
            row = q1(
                "SELECT asset_identifier FROM assets"
                " WHERE (asset_identifier LIKE ? OR model LIKE ?) AND assigned_project = ?"
                " ORDER BY asset_identifier LIMIT 1",
                (f"%{candidato}%", f"%{candidato}%", proyecto_id),
            )
            if row:
                return row["asset_identifier"]

        # 3. el modelo en cualquier parte de la flota
        row = q1(
            "SELECT asset_identifier FROM assets"
            " WHERE asset_identifier LIKE ? OR model LIKE ?"
            " ORDER BY asset_identifier LIMIT 1",
            (f"%{candidato}%", f"%{candidato}%"),
        )
        if row:
            return row["asset_identifier"]
    return None


def _proyecto_id(nombre: str | None) -> str | None:
    if not nombre:
        return None
    row = q1("SELECT project_id FROM projects WHERE name = ? OR project_id = ?",
             (nombre, nombre))
    if row:
        return row["project_id"]
    row = q1("SELECT project_id FROM projects WHERE name LIKE ? LIMIT 1", (f"%{nombre}%",))
    return row["project_id"] if row else None


class MensajeCampo(BaseModel):
    """Lo que manda el simulador (y lo que el webhook real arma tras bajar los medios)."""

    de: str = "+503-0000-0000"          # telefono del emisor
    texto: str | None = None            # mensaje escrito
    audio_ref: str | None = None        # clave del audio sembrado, o nombre de archivo
    audio_b64: str | None = None        # audio real en base64
    foto_b64: str | None = None         # foto del tablero en base64
    lat: float | None = None
    lon: float | None = None
    idempotency_key: str | None = None


def procesar_mensaje(m: MensajeCampo) -> dict[str, Any]:
    """
    Tuberia completa: voz -> texto -> entidades -> foto -> OCR -> validacion
    cruzada -> evento canonico. Es el minuto 1 de la demo.
    """
    pasos: list[dict[str, Any]] = []

    # 1. voz a texto
    texto = m.texto or ""
    conf_stt = 1.0
    if not texto and (m.audio_ref or m.audio_b64):
        audio_bytes = base64.b64decode(m.audio_b64) if m.audio_b64 else None
        texto, conf_stt = stt.transcribir(m.audio_ref or "", audio_bytes)
    pasos.append({"paso": "transcripcion", "texto": texto, "confianza": round(conf_stt, 2)})

    if not texto:
        raise HTTPException(status_code=422, detail="mensaje sin texto ni audio")

    # 2. entidades
    e = ner.extraer(texto)
    pasos.append({"paso": "entidades", "datos": e.model_dump(), "confianza": e.confianza})

    # 3. foto del tablero -> OCR
    lectura = None
    if m.foto_b64:
        lectura = ocr.leer(base64.b64decode(m.foto_b64))
        pasos.append({"paso": "ocr_tablero", "datos": lectura.model_dump(),
                      "confianza": lectura.confianza})

    # 4. validacion cruzada audio vs foto
    horas = e.operating_hours
    fuente_horas = Source.FIELD_WHATSAPP
    conf_horas = e.confianza
    confirmado = None
    if lectura and lectura.operating_hours is not None:
        acuerdo = ocr.concuerdan(e.operating_hours, lectura.operating_hours)
        if acuerdo:
            horas = lectura.operating_hours
            fuente_horas = Source.FIELD_OCR
            conf_horas = min(0.99, max(lectura.confianza, e.confianza) + 0.05)
            confirmado = "audio+foto"
        elif acuerdo is False:
            # Discrepan: gana la foto (mas autoridad) pero queda el registro.
            horas = lectura.operating_hours
            fuente_horas = Source.FIELD_OCR
            conf_horas = lectura.confianza
            confirmado = None
        else:
            horas = lectura.operating_hours
            fuente_horas = Source.FIELD_OCR
            conf_horas = lectura.confianza
        pasos.append({"paso": "validacion_cruzada",
                      "audio_h": e.operating_hours,
                      "foto_h": lectura.operating_hours,
                      "concuerdan": acuerdo})

    # 5. resolver contra datos maestros (la obra mencionada desambigua el modelo)
    proyecto_id = _proyecto_id(e.proyecto)
    asset_id = resolver_activo(e.asset_mencion, e.asset_identifier, proyecto_id)
    if not asset_id:
        raise HTTPException(
            status_code=422,
            detail=(f"no se pudo identificar la maquina en: '{texto[:80]}'. "
                    "Confirmar con el usuario por WhatsApp."),
        )
    pasos.append({"paso": "resolucion_activo", "mencion": e.asset_mencion,
                  "obra": proyecto_id, "asset": asset_id})

    # 6. evento canonico
    alertas = []
    if e.tipo_evento == "falla":
        alertas.append(DiagnosticAlert(
            code=f"CAMPO-{(e.subsistema or 'general').upper()}",
            severity=e.severidad,
            subsystem=e.subsistema,
            description=e.resumen or texto[:160],
        ))

    ev = CanonicalEvent(
        asset_identifier=asset_id,
        event_timestamp=datetime.now(timezone.utc),
        source=Source.FIELD_WHATSAPP,
        operating_hours=horas,
        location=Point(lat=m.lat, lon=m.lon) if m.lat is not None and m.lon is not None else None,
        assigned_project=proyecto_id,
        diagnostic_alerts=alertas,
        fuel_delivered=e.galones_diesel,
        note=texto,
        reported_by=m.de,
        raw={"transcripcion": texto, "extraccion": e.model_dump()},
    )
    ev.with_provenance(confidence=e.confianza, confirmed_by=m.de)
    if horas is not None:
        ev.provenance["operating_hours"] = FieldProvenance(
            source=fuente_horas,
            confidence=round(conf_horas, 2),
            confirmed_by=confirmado or m.de,
            raw_value=str(e.operating_hours) if e.operating_hours is not None else None,
        )

    resultado = procesar(ev, idempotency_key=m.idempotency_key)
    return {"pipeline": pasos, "evento": ev.model_dump(mode="json"), "resultado": resultado}


@router.get("")
def verificar(request: Request):
    """Handshake de verificacion de Meta. Emily: esto es lo que Meta llama al dar de alta."""
    p = request.query_params
    if p.get("hub.mode") == "subscribe" and p.get("hub.verify_token") == VERIFY_TOKEN:
        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(p.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="verify token invalido")


@router.post("")
async def webhook(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Webhook real de WhatsApp Cloud API.

    TODO (Wilbert, ventana 10:00-13:00):
      - bajar el media (audio/imagen) con WA_ACCESS_TOKEN desde
        GET /{media_id} y luego la URL firmada que devuelve
      - mapear el telefono del emisor a un usuario de ECON
      - responder por WhatsApp con el mensaje de confirmacion
    Por ahora traduce texto e ids de media a MensajeCampo y delega.
    """
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        msg = value["messages"][0]
    except (KeyError, IndexError):
        return {"status": "ignorado", "motivo": "payload sin mensajes"}

    m = MensajeCampo(
        de=msg.get("from", "desconocido"),
        texto=(msg.get("text") or {}).get("body"),
        audio_ref=(msg.get("audio") or {}).get("id"),
        idempotency_key=msg.get("id"),
    )
    if (msg.get("location") or {}).get("latitude") is not None:
        m.lat = msg["location"]["latitude"]
        m.lon = msg["location"]["longitude"]

    return procesar_mensaje(m)


@router.post("/sim")
def simulador(m: MensajeCampo) -> dict[str, Any]:
    """Misma tuberia, sin depender de Meta. Es la red de seguridad de la demo."""
    return procesar_mensaje(m)
