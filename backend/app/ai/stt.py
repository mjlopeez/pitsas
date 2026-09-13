"""
Transcripcion de notas de voz.

Se transcribe con mimo-v2.5, el modelo omnimodal: acepta audio directo, asi que
la misma llave que hace NER y OCR cubre la voz. No hace falta un proveedor de
voz aparte.

El stub NO es un placeholder inutil: es la ruta de demo a prueba de wifi.
Devuelve transcripciones deterministas para los audios sembrados, asi el
pipeline completo (NER, OCR, orquestador, mapa) se puede ensayar y presentar
sin depender de una red ajena. Si no hay llave, o si MiMo no responde, se cae
al stub sin que la demo lo note.

Duenio: Wilbert
"""
from __future__ import annotations

import base64

# Guion sembrado. La clave es lo que manda el simulador o el nombre del audio.
CANNED: dict[str, str] = {
    "demo_hidraulica": (
        "Mira, se reventó una manguera hidráulica de la 320 aquí en Claudia Lars, "
        "y el horómetro va en cuatro mil quinientas veinte. Está botando aceite "
        "y se calentó el motor."
    ),
    "demo_diesel": (
        "Le acabo de echar ciento veinte galones de diésel a la motoniveladora "
        "en La Cantera San Diego."
    ),
    "demo_arribo": (
        "Ya llegó el mixer con el concreto al paso a desnivel Utila, "
        "vamos a empezar a bombear."
    ),
    "demo_asfalto": (
        "Mira, la mezcla viene fría, el termómetro del distribuidor marca "
        "ciento ocho grados y ya vamos llegando al bypass de Sonsonate."
    ),
}

# Vocabulario tecnico salvadoreno. Se le pasa al proveedor real como pista.
# Wilbert: sembrar esto es la diferencia entre que entienda "horometro" y que
# escriba "oro metro". Probarlo con la voz de Josue a las 15:00, no a las 19:00.
VOCABULARIO = [
    # equipo
    "horómetro", "cama baja", "lowboy", "cabezal", "motoniveladora",
    "retroexcavadora", "excavadora", "cargador frontal", "minicargador",
    "tractor de bandas", "rodillo", "perfiladora", "recicladora",
    "estabilizadora", "terminadora", "bomba de concreto", "grúa telescópica",
    "torre de iluminación", "volteo", "cisterna", "mixer", "camión mezclador",
    "distribuidor de asfalto",
    # materiales y proceso
    "premezclado", "concreto hidráulico", "mezcla asfáltica", "asfalto modificado",
    "agregado", "basalto", "dosificación", "revenimiento", "fraguado",
    "compactación", "terracería", "talud", "subrasante", "diésel",
    "manguera hidráulica", "oruga",
    # nodos reales de ECON
    "Claudia Lars", "Naciones Unidas", "El Jaguar", "Útila",
    "bypass de Sonsonate", "Periférico Gerardo Barrios", "San Miguel",
    "Puerto de La Libertad", "La Cantera San Diego", "Los Chorros",
    "Quezaltepeque", "Acajutla", "La Libertad Costa", "plantel", "taller",
    # marcas
    "CAT", "Caterpillar", "Komatsu", "Volvo", "Mack", "Wirtgen", "Vögele",
    "Hamm", "Putzmeister",
]


SISTEMA = (
    "Transcribes notas de voz de operadores, mecanicos y motoristas de "
    "maquinaria pesada en El Salvador. El audio viene de una obra: hay ruido de "
    "motor, viento y eco.\n\n"
    "Reglas:\n"
    "- Transcribe literal, en espaniol salvadoreno, sin corregir el habla "
    "coloquial ni traducir modismos.\n"
    "- Los numeros dichos en palabras se dejan en palabras.\n"
    "- No agregues comentarios, encabezados ni comillas: solo la transcripcion.\n"
    "- Vocabulario tecnico que aparece seguido y hay que escribir bien:\n  "
    + ", ".join(VOCABULARIO)
)


def _stub(audio_ref: str) -> tuple[str, float]:
    texto = CANNED.get(audio_ref)
    if texto:
        return texto, 0.99
    return (audio_ref or ""), 0.50


def transcribir(
    audio_ref: str,
    audio_bytes: bytes | None = None,
    formato: str = "ogg",
) -> tuple[str, float]:
    """
    Devuelve (texto, confianza). Nunca lanza: la demo no se cae por esto.

    Sin bytes de audio (el caso del simulador) se usa el guion sembrado.
    Con bytes y con llave, transcribe de verdad con mimo-v2.5.
    """
    from . import provider

    if audio_bytes is None or not provider.disponible():
        return _stub(audio_ref)

    texto = provider.chat_texto(
        SISTEMA,
        "Transcribe esta nota de voz.",
        audio_b64=base64.standard_b64encode(audio_bytes).decode(),
        audio_formato=formato,
    )
    if not texto:
        print("[stt] MiMo no transcribio; cayendo al guion sembrado")
        return _stub(audio_ref)

    # Confianza moderada a proposito: el NER y la confirmacion por WhatsApp
    # son los que corrigen una transcripcion imperfecta, no una cifra optimista.
    return texto, 0.85
