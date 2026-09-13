"""
Carga perecedera: la restriccion fisica mas fuerte que tiene ECON.

El premezclado tiene una vida corta desde la dosificacion. La mezcla asfaltica
en caliente muere si baja de la temperatura minima de colocacion. Cuando un
mixer queda atrapado en la veda del VMT no se pierde tiempo: se pierde la carga,
y hay que volver a dosificar, volver a transportar y volver a coordinar la
cuadrilla que ya estaba esperando en la obra.

Por eso el Hub no puede tratar un traslado de material como un traslado de
maquinaria. Y por eso, cuando la carga no alcanza por ninguna ruta, la respuesta
correcta no es reprogramar el camion: es decirle a la planta que NO DOSIFIQUE
todavia. Esa decision cruza tres silos (planta, logistica, obra) y es
exactamente lo que el reto pide resolver.

⚠️ EMILY, antes de las 12:00: los dos umbrales de abajo son TIPICOS DE INDUSTRIA,
   no especificaciones verificadas de ECON. Confirmalos con su laboratorio o su
   manual de mezclas y corregilos aqui. Hasta entonces no se le presentan al
   jurado como datos de ECON.

Duenio: Wilbert (regla) / Emily (umbrales)
"""
from __future__ import annotations

from datetime import datetime, timedelta

from ..canonical import TipoCarga

# Vida del concreto premezclado desde la dosificacion.
VIDA_CONCRETO_MIN = 90
AVISO_CONCRETO_MIN = 60          # a los 60 min ya hay que estar descargando

# Ventana practica de transporte de mezcla asfaltica en caliente.
VIDA_ASFALTO_MIN = 120
# Temperatura minima de colocacion. Por debajo no compacta y el pavimento falla.
TEMP_MINIMA_COLOCACION_C = 120.0

VIDA = {
    TipoCarga.CONCRETO: VIDA_CONCRETO_MIN,
    TipoCarga.ASFALTO: VIDA_ASFALTO_MIN,
    TipoCarga.AGREGADO: None,        # el basalto no perece
}


def vida_minutos(tipo: TipoCarga | str) -> int | None:
    t = TipoCarga(tipo) if isinstance(tipo, str) else tipo
    return VIDA.get(t)


def vence_en(dosificado_en: datetime, tipo: TipoCarga | str) -> datetime | None:
    """El instante en que la carga deja de servir."""
    v = vida_minutos(tipo)
    return None if v is None else dosificado_en + timedelta(minutes=v)


def minutos_restantes(dosificado_en: datetime, tipo: TipoCarga | str,
                      ahora: datetime) -> float | None:
    limite = vence_en(dosificado_en, tipo)
    return None if limite is None else (limite - ahora).total_seconds() / 60.0


def revisar(carga: dict, ahora: datetime) -> dict | None:
    """
    Misma forma que las otras reglas: recibe estado, devuelve alerta o None.
    `carga` es una fila de la tabla cargas.
    """
    tipo = carga.get("tipo")
    if not tipo or tipo == TipoCarga.AGREGADO.value:
        return None
    if carga.get("estado") in ("descargada", "descartada"):
        return None

    lote = carga.get("lote") or "sin lote"
    obra = carga.get("obra_destino") or "obra sin asignar"

    # --- asfalto: manda la temperatura, no el reloj -------------------------
    if tipo == TipoCarga.ASFALTO.value:
        t = carga.get("temperatura_c")
        if t is not None and t < TEMP_MINIMA_COLOCACION_C:
            return {
                "kind": "carga",
                "severity": "critica",
                "title": f"Asfalto bajo temperatura: {t:.0f} °C",
                "detail": (
                    f"El lote {lote} va a {t:.0f} °C, debajo de los "
                    f"{TEMP_MINIMA_COLOCACION_C:.0f} °C minimos de colocacion. "
                    f"No se coloca en {obra}: no compacta y el pavimento falla. "
                    "Redestinar o descartar."
                ),
                "payload": {"lote": lote, "temperatura_c": t,
                            "minima_c": TEMP_MINIMA_COLOCACION_C},
            }

    # --- reloj de vida ------------------------------------------------------
    dos = carga.get("dosificado_en")
    if not dos:
        return None
    try:
        t0 = datetime.fromisoformat(dos)
    except ValueError:
        return None
    if t0.tzinfo is None:
        t0 = t0.replace(tzinfo=ahora.tzinfo)

    restan = minutos_restantes(t0, tipo, ahora)
    if restan is None:
        return None

    aviso = AVISO_CONCRETO_MIN if tipo == TipoCarga.CONCRETO.value else 30
    limite_total = vida_minutos(tipo) or 0

    if restan <= 0:
        return {
            "kind": "carga",
            "severity": "critica",
            "title": f"Carga vencida: lote {lote}",
            "detail": (
                f"Pasaron {limite_total - restan:.0f} min desde la dosificacion "
                f"({limite_total} min de vida). El lote {lote} ya no sirve para "
                f"{obra}: descartar y re-dosificar."
            ),
            "payload": {"lote": lote, "minutos_restantes": round(restan, 1),
                        "vida_min": limite_total, "vencida": True},
        }

    if restan <= (limite_total - aviso):
        return {
            "kind": "carga",
            "severity": "alta" if restan <= 15 else "media",
            "title": f"Carga con {restan:.0f} min de vida: lote {lote}",
            "detail": (
                f"El lote {lote} tiene que estar descargado en {obra} antes de "
                f"{restan:.0f} min. Confirmar que la cuadrilla y la bomba esten "
                "listas en el frente."
            ),
            "payload": {"lote": lote, "minutos_restantes": round(restan, 1),
                        "vida_min": limite_total, "vencida": False},
        }

    return None
