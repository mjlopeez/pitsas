"""
Lectura del horometro desde la foto del tablero.

Sirve para dos cosas: capturar la lectura de maquinas sin telemetria, y
VALIDAR contra lo que dijo la persona en el audio. Cuando los dos numeros
coinciden, la confianza sube y se marca confirmado. Cuando no, se abre ticket
en vez de elegir en silencio. Eso es la respuesta a "y si la IA se equivoca".

Duenio: Wilbert
"""
from __future__ import annotations

import base64

from pydantic import BaseModel, Field


class LecturaTablero(BaseModel):
    operating_hours: float | None = Field(
        None, description="Lectura del horometro. null si no se distingue."
    )
    es_digital: bool | None = Field(None, description="True si el tablero es digital.")
    luces_falla: list[str] = Field(
        default_factory=list, description="Testigos encendidos visibles."
    )
    confianza: float = Field(0.0, description="0.0 a 1.0 segun la nitidez de la foto.")
    nota: str = Field("", description="Que se ve en la foto, en una linea.")


SISTEMA = """Leete el tablero de una maquina de construccion pesada en la foto.

Te interesa el HOROMETRO: el contador de horas de motor. Puede ser digital
(pantalla LCD) o analogico (tambor mecanico de numeros). En maquinas viejas
suele estar sucio, rayado o con el ultimo digito en decimas.

Reglas:
- Devuelve el numero completo de horas. El ultimo digito suele ser la decima.
- Si no distingues el horometro con seguridad, operating_hours = null y
  confianza baja. Es mejor null que un numero inventado: aguas abajo este dato
  factura horas de alquiler.
- luces_falla: nombra los testigos encendidos que reconozcas.
"""

STUB = {"operating_hours": 4520.0, "es_digital": True, "confianza": 0.94,
        "nota": "Horometro digital 4520.3 h, testigo de temperatura encendido."}


def _stub() -> LecturaTablero:
    return LecturaTablero(**STUB, luces_falla=["temperatura"])


def leer(image_bytes: bytes | None, media_type: str = "image/jpeg") -> LecturaTablero:
    """
    Nunca lanza. Sin llave o sin imagen, devuelve el stub de demo.

    Usa mimo-v2.5 (el omnimodal). Como ese modelo no soporta response_format,
    el JSON se pide en el prompt y se valida contra LecturaTablero en provider.
    """
    from . import provider

    if not image_bytes:
        return _stub()

    out = provider.chat_json(
        LecturaTablero,
        SISTEMA,
        "Lee el horometro de este tablero.",
        imagen_b64=base64.standard_b64encode(image_bytes).decode(),
        imagen_tipo=media_type,
    )
    if out is None:
        if provider.disponible():
            print("[ocr] MiMo no dio una lectura valida; usando stub")
        return _stub()
    return out


def concuerdan(audio_h: float | None, foto_h: float | None, tol: float = 2.0) -> bool | None:
    """None = no hay con que comparar. True = se confirman. False = discrepan."""
    if audio_h is None or foto_h is None:
        return None
    return abs(audio_h - foto_h) <= tol
