"""
Proveedor de IA — Xiaomi MiMo (compatible con la API de OpenAI).

Un solo punto de contacto con el modelo. Si maniana cambia el proveedor, se
cambia este archivo y nada mas: ner.py, ocr.py y stt.py no conocen al proveedor.

Reparto de modelos (confirmado en la documentacion publica de MiMo):
  mimo-v2.5-pro   solo texto. SI soporta response_format JSON.   -> NER
  mimo-v2.5       omnimodal (imagen, audio, video, PDF).
                  NO soporta response_format.                    -> OCR y voz

MiMo NO fuerza el esquema del JSON, solo el formato. Por eso toda respuesta se
valida contra el modelo Pydantic del lado nuestro, con un reintento que le
devuelve el error de validacion. Si vuelve a fallar, el llamador cae a su
respaldo por reglas. Sin esa validacion, un campo mal tipeado entra al Hub y
termina facturando horas equivocadas.

CUIDADO — sin confirmar: la forma exacta de las partes de contenido de audio e
imagen. Se implemento la convencion de OpenAI (`image_url` con data URI,
`input_audio` con base64), que es lo que MiMo declara soportar, pero el dominio
de su documentacion estaba bloqueado al escribir esto. Correr el spike de
docs/mimo-spike.md ANTES de confiar en esto, y ajustar aqui si hace falta.

Duenio: Wilbert
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

BASE_URL = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
MODEL_TEXTO = os.getenv("MIMO_MODEL_TEXTO", "mimo-v2.5-pro")
MODEL_MULTIMODAL = os.getenv("MIMO_MODEL_MULTIMODAL", "mimo-v2.5")
TIMEOUT = float(os.getenv("MIMO_TIMEOUT", "45"))


def api_key() -> str | None:
    return os.getenv("MIMO_API_KEY") or None


def disponible() -> bool:
    """El switch que consultan ner/ocr/stt. Sin llave, todo cae al respaldo."""
    return bool(api_key())


_cliente = None


def _client():
    """Import perezoso: la app tiene que arrancar aunque `openai` no este instalado."""
    global _cliente
    if _cliente is not None:
        return _cliente
    from openai import OpenAI

    _cliente = OpenAI(api_key=api_key(), base_url=BASE_URL, timeout=TIMEOUT)
    return _cliente


def _solo_json(texto: str) -> str:
    """
    MiMo puede envolver el JSON en ``` o meterle un preambulo. Se recorta al
    primer objeto balanceado en vez de confiar en que venga limpio.
    """
    t = texto.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.IGNORECASE).strip()
    i = t.find("{")
    if i == -1:
        return t
    prof = 0
    for k in range(i, len(t)):
        if t[k] == "{":
            prof += 1
        elif t[k] == "}":
            prof -= 1
            if prof == 0:
                return t[i:k + 1]
    return t[i:]


def _esquema_legible(modelo: type[BaseModel]) -> str:
    """El esquema se mete en el prompt porque MiMo no lo impone por parametro."""
    props = modelo.model_json_schema().get("properties", {})
    lineas = []
    for nombre, info in props.items():
        desc = info.get("description", "")
        tipo = info.get("type") or "any"
        if "anyOf" in info:
            tipo = " | ".join(t.get("type", "null") for t in info["anyOf"])
        lineas.append(f'  "{nombre}": {tipo}  // {desc}')
    return "{\n" + ",\n".join(lineas) + "\n}"


def chat_json(
    modelo_salida: type[T],
    system: str,
    user: str,
    *,
    imagen_b64: str | None = None,
    imagen_tipo: str = "image/jpeg",
    audio_b64: str | None = None,
    audio_formato: str = "ogg",
    max_tokens: int = 1500,
) -> T | None:
    """
    Pide JSON y devuelve una instancia validada, o None si no se pudo.

    None NO es un error a propagar: es la senial de que el llamador use su
    respaldo. Nada en la ruta de la demo puede reventar por el proveedor.
    """
    if not disponible():
        return None

    multimodal = bool(imagen_b64 or audio_b64)
    model = MODEL_MULTIMODAL if multimodal else MODEL_TEXTO

    instruccion = (
        f"{user}\n\n"
        "Responde UNICAMENTE con un objeto JSON valido, sin texto antes ni "
        "despues, sin bloques de codigo, con exactamente esta forma:\n"
        f"{_esquema_legible(modelo_salida)}\n"
        "Si un dato no esta presente, usa null. No inventes valores."
    )

    partes: list[dict[str, Any]] = [{"type": "text", "text": instruccion}]
    if imagen_b64:
        partes.insert(0, {
            "type": "image_url",
            "image_url": {"url": f"data:{imagen_tipo};base64,{imagen_b64}"},
        })
    if audio_b64:
        partes.insert(0, {
            "type": "input_audio",
            "input_audio": {"data": audio_b64, "format": audio_formato},
        })

    mensajes = [
        {"role": "system", "content": system},
        {"role": "user", "content": partes if multimodal else instruccion},
    ]

    kwargs: dict[str, Any] = {"model": model, "messages": mensajes, "max_tokens": max_tokens}
    # Solo el modelo de texto acepta response_format; al omnimodal lo rechaza.
    if not multimodal:
        kwargs["response_format"] = {"type": "json_object"}

    ultimo_error = ""
    for intento in (1, 2):
        try:
            r = _client().chat.completions.create(**kwargs)
            crudo = (r.choices[0].message.content or "").strip()
        except Exception as exc:  # noqa: BLE001
            print(f"[mimo] {model} fallo en la llamada: {exc}")
            return None

        try:
            return modelo_salida(**json.loads(_solo_json(crudo)))
        except (ValidationError, ValueError, TypeError) as exc:
            ultimo_error = str(exc)[:400]
            print(f"[mimo] intento {intento}: respuesta invalida ({ultimo_error[:120]})")
            if intento == 2:
                break
            # Reintento con el error de validacion adentro: suele arreglarlo.
            mensajes.append({"role": "assistant", "content": crudo})
            mensajes.append({
                "role": "user",
                "content": (
                    f"Ese JSON no valido: {ultimo_error}\n"
                    "Devuelve solo el objeto JSON corregido."
                ),
            })
            kwargs["messages"] = mensajes

    return None


def chat_texto(
    system: str,
    user: str,
    *,
    audio_b64: str | None = None,
    audio_formato: str = "ogg",
    max_tokens: int = 1200,
) -> str | None:
    """Texto libre. Se usa para transcribir: la salida no es JSON, es la frase."""
    if not disponible():
        return None

    multimodal = bool(audio_b64)
    partes: list[dict[str, Any]] = [{"type": "text", "text": user}]
    if audio_b64:
        partes.insert(0, {
            "type": "input_audio",
            "input_audio": {"data": audio_b64, "format": audio_formato},
        })

    try:
        r = _client().chat.completions.create(
            model=MODEL_MULTIMODAL if multimodal else MODEL_TEXTO,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": partes if multimodal else user},
            ],
            max_tokens=max_tokens,
        )
        return (r.choices[0].message.content or "").strip() or None
    except Exception as exc:  # noqa: BLE001
        print(f"[mimo] transcripcion fallo: {exc}")
        return None
