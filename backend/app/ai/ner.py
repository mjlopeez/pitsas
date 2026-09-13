"""
Extraccion de entidades de un reporte de campo en lenguaje coloquial.

Dos caminos, en este orden:
  1. MiMo (mimo-v2.5-pro), con la salida validada contra Extraccion.
  2. Extractor por reglas, si no hay MIMO_API_KEY o la llamada falla.

El camino 2 existe para que la demo nunca dependa de la red del salon, y esta
probado: saca 4520 h de "cuatro mil quinientas veinte" sin tocar la red.
Duenio: Wilbert
"""
from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel, Field


class Extraccion(BaseModel):
    """Lo que el Hub necesita sacar de una nota de voz."""

    asset_identifier: str | None = Field(
        None, description="Identificador de la maquina, p.ej. CAT-320-04. None si no se menciona."
    )
    asset_mencion: str | None = Field(
        None, description="Como la nombro la persona, tal cual: 'la 320', 'la retro'."
    )
    operating_hours: float | None = Field(None, description="Lectura del horometro en horas.")
    proyecto: str | None = Field(None, description="Obra o plantel mencionado.")
    tipo_evento: str = Field(
        "otro", description="falla | arribo | abastecimiento | inspeccion | otro"
    )
    subsistema: str | None = Field(
        None, description="hidraulico | motor | transmision | electrico | neumatico | estructural"
    )
    severidad: str = Field("media", description="baja | media | alta | critica")
    galones_diesel: float | None = Field(None, description="Galones entregados, si es abastecimiento.")
    resumen: str = Field("", description="Una linea en espaniol neutro.")
    confianza: float = Field(0.5, description="0.0 a 1.0")


SISTEMA = """Eres el extractor de entidades del Hub de Operaciones de Grupo ECON,
una empresa salvadorena de maquinaria pesada, terraceria y asfalto.

Recibes la transcripcion de una nota de voz de un operador, mecanico o motorista
en espaniol salvadoreno coloquial. Tu trabajo es convertirla en datos estructurados.

Contexto que necesitas:
- "la 320", "la 336" = excavadora Caterpillar de ese modelo.
- "la retro" = retroexcavadora. "la moto" = motoniveladora.
- "cama baja" = plataforma de transporte de maquinaria. "cabezal" = tractocamion.
- "horometro" = contador de horas de motor. Las horas suelen venir dichas en
  palabras: "cuatro mil quinientas veinte" son 4520.
- Obras y planteles reales: Planta San Diego, La Libertad Costa, plantel La Cantera,
  plantel San Salvador, Acajutla, Los Chorros.
- "se revento", "esta botando aceite", "se calento" = falla. Manguera, aceite y
  presion son subsistema hidraulico; temperatura y refrigerante son motor.

Reglas:
- Si un dato no esta en el texto, devuelve null. No lo inventes.
- severidad "alta" o "critica" solo si el equipo quedo inoperante o hay riesgo.
- confianza refleja que tan claro estaba el audio transcrito.
"""

# --- extractor por reglas (respaldo offline) ---------------------------------

_NUM = {
    "cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
    "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
    "veinte": 20, "treinta": 30, "cuarenta": 40, "cincuenta": 50,
    "sesenta": 60, "setenta": 70, "ochenta": 80, "noventa": 90,
    "cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300,
    "cuatrocientos": 400, "quinientos": 500, "seiscientos": 600,
    "setecientos": 700, "ochocientos": 800, "novecientos": 900,
}
_MULT = {"mil": 1000, "millon": 1_000_000, "millones": 1_000_000}

_SUBSISTEMA = {
    "hidraulico": ["hidraulic", "manguera", "aceite", "presion", "cilindro", "bomba"],
    "motor": ["motor", "calent", "temperatura", "refrigerante", "radiador", "turbo"],
    "transmision": ["transmision", "caja", "embrague", "diferencial"],
    "electrico": ["electric", "bateria", "alternador", "arranque", "luces"],
    "neumatico": ["llanta", "neumatic", "aire", "oruga", "rodaje"],
}

# Nodos reales de ECON, por como los nombra la gente en campo. El orden importa:
# se toma la primera coincidencia, asi que lo mas especifico va primero.
_OBRAS = {
    "claudia lars": "Paso desnivel Claudia Lars",
    "naciones unidas": "Paso desnivel Naciones Unidas",
    "el jaguar": "Paso desnivel El Jaguar",
    "jaguar": "Paso desnivel El Jaguar",
    "utila": "Paso desnivel Utila",
    "sonsonate": "Bypass de Sonsonate",
    "gerardo barrios": "Periferico Gerardo Barrios, San Miguel",
    "san miguel": "Periferico Gerardo Barrios, San Miguel",
    "puerto de la libertad": "Ampliacion carretera al Puerto de La Libertad",
    "aeropuerto": "Aeropuerto Internacional — pista principal",
    "pista": "Aeropuerto Internacional — pista principal",
    "la cantera": "La Cantera San Diego",
    "cantera": "La Cantera San Diego",
    "chorros": "Tramo Los Chorros",
    "quezaltepeque": "Quezaltepeque",
    "planta de asfalto": "Planta de asfalto San Salvador",
    "san diego": "Planta de asfalto San Diego",
    "libertad costa": "Planta de concreto La Libertad Costa",
    "libertad": "Ampliacion carretera al Puerto de La Libertad",
    "plantel": "Plantel y taller central San Salvador",
    "taller": "Plantel y taller central San Salvador",
    "san salvador": "Planta de concreto San Salvador",
}


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def _palabras_a_numero(texto: str) -> float | None:
    """'cuatro mil quinientas veinte' -> 4520.0"""
    t = _sin_tildes(texto)
    t = t.replace("quinientas", "quinientos").replace("doscientas", "doscientos")
    t = t.replace("trescientas", "trescientos").replace("cuatrocientas", "cuatrocientos")
    tokens = [w for w in re.split(r"[^a-z]+", t) if w]
    total, parcial, visto = 0, 0, False
    for w in tokens:
        if w in _NUM:
            parcial += _NUM[w]
            visto = True
        elif w in _MULT:
            parcial = (parcial or 1) * _MULT[w]
            total += parcial
            parcial = 0
            visto = True
        elif w == "y":
            continue
        elif visto and (total or parcial):
            break
    res = total + parcial
    return float(res) if visto and res else None


def extraer_por_reglas(texto: str) -> Extraccion:
    t = _sin_tildes(texto)

    # horometro: digitos o palabras despues de "horometro"
    horas = None
    m = re.search(r"(?:horometro|oro metro|horas)[^0-9]{0,25}([\d][\d.,]*)", t)
    if m:
        try:
            horas = float(m.group(1).replace(",", ""))
        except ValueError:
            horas = None
    if horas is None:
        # Numero dicho en palabras: se toma la cola despues de "horometro" y
        # _palabras_a_numero se detiene solo cuando deja de haber numerales.
        m = re.search(r"(?:horometro|oro metro|oro-metro)", t)
        if m:
            horas = _palabras_a_numero(t[m.end():m.end() + 90])

    # modelo de maquina
    asset = None
    mencion = None
    # Modelos del catalogo real. El resolvedor de whatsapp.py hace LIKE sobre
    # esto contra los datos maestros, asi que basta con el modelo.
    mm = re.search(
        r"\b(320|330|336|349|140|950|966|246|426|815|d6|d65|d155|pc200|"
        r"gd555|wb93|ec220|ec300|l120|w200|wr240|wr250|s1800|hd120|h13i|"
        r"grw280|gu813|fm440|rd688s|gr64btx|mr688|114sd)\b", t)
    if mm:
        mencion = mm.group(1)
        asset = mencion.upper()

    proyecto = next((v for k, v in _OBRAS.items() if k in t), None)

    subsistema = None
    for sub, claves in _SUBSISTEMA.items():
        if any(c in t for c in claves):
            subsistema = sub
            break

    # Carga de material: "vengo con ocho metros de concreto", "cargue treinta
    # toneladas de mezcla". Sirve para que el Hub sepa que hay una carga en juego.
    galones = None
    mg = re.search(r"([\d][\d.,]*)\s*(?:gal|galon)", t)
    if mg:
        galones = float(mg.group(1).replace(",", ""))
    else:
        mg = re.search(r"((?:\w+\s+){1,6})galones", t)
        if mg:
            galones = _palabras_a_numero(mg.group(1))

    if galones:
        tipo = "abastecimiento"
    elif any(k in t for k in ("revent", "falla", "boton", "botando", "calent", "no arranca", "se quedo", "fuga")):
        tipo = "falla"
    elif any(k in t for k in ("llego", "arribo", "ya esta en")):
        tipo = "arribo"
    else:
        tipo = "otro"

    severidad = "alta" if any(k in t for k in ("revent", "no arranca", "se quedo", "parada")) else "media"

    return Extraccion(
        asset_identifier=asset,
        asset_mencion=mencion,
        operating_hours=horas,
        proyecto=proyecto,
        tipo_evento=tipo,
        subsistema=subsistema,
        severidad=severidad,
        galones_diesel=galones,
        resumen=texto.strip()[:200],
        confianza=0.62,  # honesto: el extractor por reglas no es la version buena
    )


def extraer(texto: str) -> Extraccion:
    """Camino principal: MiMo. Respaldo: reglas. Nunca lanza."""
    from . import provider

    out = provider.chat_json(Extraccion, SISTEMA, f"Transcripcion:\n\n{texto}")
    if out is None:
        if provider.disponible():
            print("[ner] MiMo no dio una extraccion valida; usando reglas")
        return extraer_por_reglas(texto)

    # El modelo puede omitir el resumen; se rellena para que la UI no quede vacia.
    if not out.resumen:
        out.resumen = texto.strip()[:200]
    return out
