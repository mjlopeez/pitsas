"""
Contrato canonico del Hub de Operaciones — ISO 15143-3 / AEMP 2.0 adaptado.

CONGELADO A LAS 08:30. Cambiar algo aqui rompe trabajo de los otros tres.
Si hay que cambiarlo, se avisa en voz alta y se actualiza docs/CONTRATO.md.

Duenio: Emily (hasta 15:00) -> Wilbert
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Source(str, Enum):
    """De donde viene un dato. El orden importa: ver PRECEDENCIA."""

    OEM_CAT = "oem_cat"
    OEM_KOMATSU = "oem_komatsu"
    OEM_VOLVO = "oem_volvo"
    RETROFIT_J1939 = "retrofit_j1939"
    FIELD_OCR = "field_ocr"
    FIELD_WHATSAPP = "field_whatsapp"
    FIELD_PWA = "field_pwa"
    # Unidades de negocio de ECON aguas arriba de la obra. La empresa esta
    # integrada verticalmente (cantera -> plantas -> laboratorio -> maquinaria
    # -> obra), asi que los silos tambien estan ENTRE unidades, no solo entre
    # la telemetria y el ERP.
    PLANTA_CONCRETO = "planta_concreto"
    PLANTA_ASFALTO = "planta_asfalto"
    LAB = "laboratorio"


OEM_SOURCES = {Source.OEM_CAT, Source.OEM_KOMATSU, Source.OEM_VOLVO}
PLANTA_SOURCES = {Source.PLANTA_CONCRETO, Source.PLANTA_ASFALTO}


class EngineState(str, Enum):
    ON = "ON"
    OFF = "OFF"
    IDLE = "IDLE"


class AssetState(str, Enum):
    """Maquina de estados del activo. Duenio: Wilbert."""

    DISPONIBLE = "DISPONIBLE"
    OPERANDO = "OPERANDO"
    RALENTI = "RALENTI"
    FALLA = "FALLA"
    EN_MANTENIMIENTO = "EN_MANTENIMIENTO"
    EN_TRASLADO = "EN_TRASLADO"


class TipoCarga(str, Enum):
    CONCRETO = "CONCRETO"    # premezclado: ~90 min de vida desde la dosificacion
    ASFALTO = "ASFALTO"      # mezcla en caliente: muere si baja de temperatura
    AGREGADO = "AGREGADO"    # basalto de La Cantera San Diego: no perece


class Point(BaseModel):
    lat: float
    lon: float


class Carga(BaseModel):
    """
    Una carga de material en transito.

    El concreto y el asfalto son PERECEDEROS, y eso cambia el problema: si el
    mixer queda atrapado en la veda del VMT no se pierde tiempo, se pierde la
    carga y hay que volver a dosificar. La coordinacion planta-logistica-obra
    deja de ser una conveniencia y pasa a ser una restriccion fisica con costo.
    """

    tipo: TipoCarga
    cantidad: float | None = None
    unidad: str | None = None                  # m3 para concreto, ton para asfalto
    dosificado_en: datetime | None = None      # el reloj de vida arranca aqui
    temperatura_c: float | None = None         # critica en asfalto
    diseno: str | None = None                  # "f'c 280 kg/cm2", "mezcla modificada"
    planta_origen: str | None = None
    obra_destino: str | None = None
    lote: str | None = None                    # lo que el laboratorio ensaya
    cumple_especificacion: bool | None = None  # SOLO lo escribe el laboratorio


class DiagnosticAlert(BaseModel):
    """Un codigo de falla. SPN/FMI en J1939, o texto clasificado si viene de campo."""

    code: str
    spn: int | None = None
    fmi: int | None = None
    severity: str = "media"          # baja | media | alta | critica
    subsystem: str | None = None     # hidraulico | motor | transmision | electrico | neumatico
    description: str | None = None


class FieldProvenance(BaseModel):
    """
    Procedencia de UN campo. Esto es lo que se pinta como chip en la UI
    y lo que responde la pregunta del jurado: "y si la IA se equivoca?".
    """

    source: Source
    confidence: float = 1.0                 # 0.0 - 1.0
    confirmed_by: str | None = None         # usuario que confirmo por WhatsApp
    raw_value: str | None = None            # lo que dijo la fuente antes de normalizar


# ---------------------------------------------------------------------------
# PRECEDENCIA POR CAMPO  (el aporte que no esta en el documento original)
#
# Contesta "quien es el duenio del dato". Menor indice = mas autoridad.
# Si llega un valor de una fuente con menos autoridad que la que ya tenemos
# y difiere mas alla de la tolerancia, NO se sobrescribe: se abre un ticket
# de conciliacion. Ver rules/fuel.py y dispatch/orchestrator.py.
# ---------------------------------------------------------------------------
PRECEDENCIA: dict[str, list[Source]] = {
    "operating_hours": [
        Source.OEM_CAT, Source.OEM_KOMATSU, Source.OEM_VOLVO,
        Source.RETROFIT_J1939,
        Source.FIELD_OCR,
        Source.FIELD_WHATSAPP, Source.FIELD_PWA,
    ],
    "cumulative_fuel": [
        Source.OEM_CAT, Source.OEM_KOMATSU, Source.OEM_VOLVO,
        Source.RETROFIT_J1939,
        Source.FIELD_PWA, Source.FIELD_WHATSAPP,
    ],
    "location": [
        Source.OEM_CAT, Source.OEM_KOMATSU, Source.OEM_VOLVO,
        Source.RETROFIT_J1939,
        Source.FIELD_PWA, Source.FIELD_WHATSAPP,
    ],
    "engine_state": [
        Source.OEM_CAT, Source.OEM_KOMATSU, Source.OEM_VOLVO,
        Source.RETROFIT_J1939,
        Source.FIELD_WHATSAPP,
    ],
    # assigned_project lo manda la geocerca, no la persona
    "assigned_project": [
        Source.OEM_CAT, Source.OEM_KOMATSU, Source.OEM_VOLVO,
        Source.RETROFIT_J1939,
        Source.FIELD_WHATSAPP, Source.FIELD_PWA,
    ],
}

PRECEDENCIA.update({
    # Temperatura: la planta la mide al cargar, el sensor del camion en ruta, y
    # el motorista de ultimo. Los tres pueden reportar; el orden decide.
    "temperatura_c": [
        Source.PLANTA_ASFALTO, Source.PLANTA_CONCRETO,
        Source.RETROFIT_J1939,
        Source.FIELD_WHATSAPP, Source.FIELD_PWA,
    ],
    "obra_destino": [
        Source.PLANTA_CONCRETO, Source.PLANTA_ASFALTO,
        Source.RETROFIT_J1939,
        Source.FIELD_WHATSAPP, Source.FIELD_PWA,
    ],
})

# ---------------------------------------------------------------------------
# DUENIO EXCLUSIVO DE CAMPO
#
# La precedencia ordena a varias fuentes que SI pueden reportar un campo. Esto
# es mas fuerte: hay campos que una sola unidad de negocio tiene derecho a
# escribir, y nadie mas, ni la primera vez.
#
# Sale directo de como opera ECON:
#   la planta es duenia del reloj de dosificacion y del diseno de mezcla,
#   el laboratorio es duenio del veredicto de cumplimiento,
#   el motorista es duenio de la llegada.
#
# Que la obra declare "este lote cumple" no lo vuelve cierto. Solo el
# laboratorio puede. Un intento de otra fuente no sobrescribe: abre ticket.
# ---------------------------------------------------------------------------
EXCLUSIVOS: dict[str, set[Source]] = {
    "cumple_especificacion": {Source.LAB},
    "dosificado_en": PLANTA_SOURCES,
    "diseno": PLANTA_SOURCES,
}


def puede_escribir(campo: str, source: Source) -> bool:
    """False si el campo tiene duenio exclusivo y `source` no es uno de ellos."""
    duenios = EXCLUSIVOS.get(campo)
    return source in duenios if duenios else True


# Tolerancias de conciliacion antes de abrir ticket.
TOLERANCIA = {
    "operating_hours": 2.0,      # horas
    "cumulative_fuel": 0.05,     # 5% — el numero del documento
}


def autoridad(campo: str, source: Source) -> int:
    """Menor = mas autoridad. 99 si la fuente no esta declarada para ese campo."""
    orden = PRECEDENCIA.get(campo, [])
    try:
        return orden.index(source)
    except ValueError:
        return 99


def gana(campo: str, nueva: Source, actual: Source | None) -> bool:
    """True si `nueva` tiene derecho a sobrescribir a `actual`."""
    if actual is None:
        return True
    return autoridad(campo, nueva) <= autoridad(campo, actual)


class CanonicalEvent(BaseModel):
    """
    El unico formato que circula dentro del Hub.

    Todo entra por POST /ingest/*. Si un origen nuevo necesita un endpoint
    con forma distinta, el contrato esta mal — no el origen.
    """

    # min_length=1: un identificador vacio creaba un activo fantasma en la
    # flota. Se descubrio probando la conciliacion de diesel.
    asset_identifier: str = Field(min_length=1)
    event_timestamp: datetime
    source: Source

    location: Point | None = None
    operating_hours: float | None = None
    engine_state: EngineState | None = None
    cumulative_fuel: float | None = None
    diagnostic_alerts: list[DiagnosticAlert] = Field(default_factory=list)
    assigned_project: str | None = None

    # Campos que no vienen del estandar pero el Hub necesita
    fuel_delivered: float | None = None      # galones de un vale de diesel
    carga: Carga | None = None               # material perecedero en transito
    note: str | None = None                  # texto libre / transcripcion
    reported_by: str | None = None           # telefono o nombre del emisor

    provenance: dict[str, FieldProvenance] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)

    def with_provenance(self, confidence: float = 1.0, confirmed_by: str | None = None) -> "CanonicalEvent":
        """Marca todos los campos presentes con la fuente del evento."""
        for campo in ("location", "operating_hours", "engine_state",
                      "cumulative_fuel", "assigned_project"):
            if getattr(self, campo) is not None and campo not in self.provenance:
                self.provenance[campo] = FieldProvenance(
                    source=self.source, confidence=confidence, confirmed_by=confirmed_by
                )
        return self


def ahora() -> datetime:
    return datetime.now(timezone.utc)
