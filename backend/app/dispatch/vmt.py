"""
Motor de veda del VMT — restricciones horarias de carga pesada en el AMSS.

Es una funcion pura y determinista: entra una hora de salida y un corredor,
sale una hora de salida valida. Se puede probar, no depende de red, y en
pantalla se ve como una barra roja sobre la linea de tiempo del traslado.
Alto valor, bajo costo. Es la pieza que nadie mas va a tener.

ADVERTENCIA PARA EMILY: los horarios de abajo son los del documento base.
Verificalos contra la resolucion vigente del VMT antes de las 12:00 y
corregi la matriz aqui. Un dato regulatorio inventado lo detecta un juez
de ECON en tres segundos.

Duenio: Emily (matriz) / Wilbert (integracion)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone

# El Salvador no usa horario de verano.
SV = timezone(timedelta(hours=-6))

LUN, MAR, MIE, JUE, VIE, SAB, DOM = range(7)
HABILES = (LUN, MAR, MIE, JUE, VIE)

# ---------------------------------------------------------------------------
# OJO — TRAMPA DE DEMO
# La veda solo corre en dias habiles. Si el ensayo o la presentacion caen en
# sabado o domingo, el motor responde "ventana libre" y el minuto 3 de la
# demo no dispara nada.
#
# Dos formas de manejarlo, en orden de preferencia:
#   1. Que la solicitud de traslado de la demo se pida para un dia habil
#      (es lo natural: "el traslado es para el lunes"). Ver docs/DEMO.md.
#   2. HUB_DEMO_WEEKDAY=0..4 fuerza la evaluacion como si fuera ese dia.
#      Es una ayuda de ensayo. Si se usa en vivo, hay que decirlo.
# ---------------------------------------------------------------------------
def _dia_efectivo(cuando: datetime) -> int:
    forzado = os.getenv("HUB_DEMO_WEEKDAY")
    if forzado not in (None, ""):
        try:
            return int(forzado) % 7
        except ValueError:
            pass
    return cuando.astimezone(SV).weekday()


@dataclass(frozen=True)
class Ventana:
    """Una franja en que el transporte de carga no puede circular."""

    desde: time
    hasta: time
    etiqueta: str
    dias: tuple[int, ...] = HABILES

    def contiene(self, t: time) -> bool:
        return self.desde <= t < self.hasta


@dataclass(frozen=True)
class Corredor:
    corredor_id: str
    nombre: str
    vedas: tuple[Ventana, ...] = field(default_factory=tuple)
    penalidad_min: int = 0          # minutos extra de recorrido vs la ruta directa


PICO_AM = Ventana(time(6, 0), time(9, 0), "pico matutino")
PICO_PM = Ventana(time(15, 30), time(19, 30), "pico vespertino")

CORREDORES: dict[str, Corredor] = {
    "panamericana_poniente": Corredor(
        "panamericana_poniente",
        "Carretera Panamericana — salida a occidente (tramo Los Chorros)",
        (PICO_AM, PICO_PM),
    ),
    "bulevar_monsenor_romero": Corredor(
        "bulevar_monsenor_romero", "Bulevar Monsenior Romero", (PICO_AM, PICO_PM)
    ),
    "autopista_comalapa": Corredor(
        "autopista_comalapa", "Autopista a Comalapa", (PICO_AM, PICO_PM)
    ),
    "bypass_quezaltepeque": Corredor(
        "bypass_quezaltepeque",
        "Desvio por Quezaltepeque",
        (),                  # sin veda: es la valvula de escape
        penalidad_min=40,
    ),
}

DEFAULT_CORREDOR = "panamericana_poniente"


def _vedas_activas(c: Corredor, cuando: datetime) -> tuple[Ventana, ...]:
    dia = _dia_efectivo(cuando)
    return tuple(v for v in c.vedas if dia in v.dias)


def en_veda(cuando: datetime, corredor: str = DEFAULT_CORREDOR) -> Ventana | None:
    """La ventana que aplica en ese instante, o None."""
    c = CORREDORES.get(corredor) or CORREDORES[DEFAULT_CORREDOR]
    local = cuando.astimezone(SV)
    for v in _vedas_activas(c, cuando):
        if v.contiene(local.time()):
            return v
    return None


@dataclass
class Plan:
    """Resultado del motor. Esto es lo que consume la UI y lo que se manda por WhatsApp."""

    corredor: str
    corredor_nombre: str
    salida: datetime
    llegada: datetime
    eta_minutos: int
    reprogramado: bool
    razon: str
    veda_evitada: str | None = None

    def to_dict(self) -> dict:
        return {
            "corredor": self.corredor,
            "corredor_nombre": self.corredor_nombre,
            "salida": self.salida.isoformat(),
            "salida_local": self.salida.astimezone(SV).strftime("%Y-%m-%d %H:%M"),
            "llegada": self.llegada.isoformat(),
            "llegada_local": self.llegada.astimezone(SV).strftime("%Y-%m-%d %H:%M"),
            "eta_minutos": self.eta_minutos,
            "reprogramado": self.reprogramado,
            "razon": self.razon,
            "veda_evitada": self.veda_evitada,
        }


def _fin_de_veda(v: Ventana, ref: datetime) -> datetime:
    local = ref.astimezone(SV)
    fin = local.replace(hour=v.hasta.hour, minute=v.hasta.minute, second=0, microsecond=0)
    if fin <= local:
        fin += timedelta(days=1)
    return fin.astimezone(timezone.utc)


def _conflicto(salida: datetime, eta: int, c: Corredor) -> Ventana | None:
    """
    Revisa el trayecto completo en pasos de 10 min. Lo que importa no es solo
    la hora de salida: si el convoy va a estar rodando dentro de la veda, lo
    paran igual. Ese es el error que comete la programacion manual.
    """
    paso = timedelta(minutes=10)
    t = salida
    fin = salida + timedelta(minutes=eta)
    while t <= fin:
        v = en_veda(t, c.corredor_id)
        if v:
            return v
        t += paso
    return None


def planificar(
    listo_desde: datetime,
    eta_minutos: int,
    corredor: str = DEFAULT_CORREDOR,
    permitir_desvio: bool = True,
) -> Plan:
    """
    Devuelve la primera salida viable. Tres salidas posibles, en orden:
      1. Sale ya y no toca veda.
      2. El desvio por Quezaltepeque lo saca hoy pagando 40 min extra.
      3. Se reprograma al final de la veda.
    """
    c = CORREDORES.get(corredor) or CORREDORES[DEFAULT_CORREDOR]
    eta_total = eta_minutos + c.penalidad_min

    choque = _conflicto(listo_desde, eta_total, c)
    if choque is None:
        return Plan(
            corredor=c.corredor_id,
            corredor_nombre=c.nombre,
            salida=listo_desde,
            llegada=listo_desde + timedelta(minutes=eta_total),
            eta_minutos=eta_total,
            reprogramado=False,
            razon="Ventana libre. Sale sin restriccion.",
        )

    if permitir_desvio and c.corredor_id != "bypass_quezaltepeque":
        alt = CORREDORES["bypass_quezaltepeque"]
        eta_alt = eta_minutos + alt.penalidad_min
        if _conflicto(listo_desde, eta_alt, alt) is None:
            return Plan(
                corredor=alt.corredor_id,
                corredor_nombre=alt.nombre,
                salida=listo_desde,
                llegada=listo_desde + timedelta(minutes=eta_alt),
                eta_minutos=eta_alt,
                reprogramado=True,
                razon=(
                    f"El trayecto por {c.nombre} cae en {choque.etiqueta} "
                    f"({choque.desde.strftime('%H:%M')}–{choque.hasta.strftime('%H:%M')}). "
                    f"Se desvia por Quezaltepeque: +{alt.penalidad_min} min, pero sale hoy."
                ),
                veda_evitada=choque.etiqueta,
            )

    nueva = _fin_de_veda(choque, listo_desde)
    # El fin de una veda puede caer dentro de otra; se reintenta.
    for _ in range(4):
        if _conflicto(nueva, eta_total, c) is None:
            break
        siguiente = en_veda(nueva, c.corredor_id) or _conflicto(nueva, eta_total, c)
        if siguiente is None:
            break
        nueva = _fin_de_veda(siguiente, nueva)

    return Plan(
        corredor=c.corredor_id,
        corredor_nombre=c.nombre,
        salida=nueva,
        llegada=nueva + timedelta(minutes=eta_total),
        eta_minutos=eta_total,
        reprogramado=True,
        razon=(
            f"No completa la salida antes de las {choque.desde.strftime('%H:%M')} "
            f"({choque.etiqueta}). Se reprograma a las "
            f"{nueva.astimezone(SV).strftime('%H:%M')} para no quedar detenido en via."
        ),
        veda_evitada=choque.etiqueta,
    )
