"""
Donde sangra la compania — en tiempo y en mano de obra, por area.

Los organizadores confirmaron como esta partida la operacion en ECON:
**Maquinaria, Logistica y Proyectos**. Tres areas, tres perdidas distintas,
tres pantallas distintas. Un tablero que les muestra lo mismo a las tres no
le sirve a ninguna.

    Maquinaria   dueña del activo. Decide si un equipo puede operar.
                 Le duele: equipo detenido con traslado vivo, equipo que no
                 reporta, y flota sin ninguna medicion de horas.
    Logistica    mueve el equipo. Asigna unidades y ejecuta traslados.
                 Le duele: solicitudes aprobadas sin unidad, traslados que no
                 se pueden cumplir, y el tiempo de su gente cruzando dos
                 plataformas a mano.
    Proyectos    consume el equipo y paga las horas.
                 Le duele: pagar horas sin evidencia, partidas cargadas sin
                 respaldo, y frentes parados esperando una maquina.

REGLA DE HONESTIDAD, y no es negociable:

Los CONTEOS salen de la base — son reales, se pueden auditar uno por uno.
Los COSTOS UNITARIOS son supuestos NUESTROS: no tenemos la planilla de ECON
ni su tarifa de cama baja. Cada cifra derivada viaja con `base_medida` (lo
que contamos) y `supuesto_aplicado` (lo que asumimos), y el tablero los
muestra por separado.

Inventar el costo-hora de una empresa salvadorena frente a un juez que la
conoce es la forma mas rapida de perder todo el credito ganado.
Preguntarle el parametro, en cambio, lo vuelve complice del calculo.

Duenio: Wilbert
"""
from __future__ import annotations

import os
from typing import Any

from .correlacion import (ALERTA_OPERATIVA, AREA_LOGISTICA, AREA_MAQUINARIA,
                          AREA_PROYECTOS, RIESGO_CRITICO,
                          VINCULO_NO_CONFIRMADO, listar_maquinas,
                          vista_unificada)

# ---------------------------------------------------------------------------
# SUPUESTOS — todos configurables por variable de entorno.
#
# Ninguno sale de un documento de ECON. Estan aqui juntos, a la vista, para
# que en la demo se pueda decir "cambiame este numero" y el tablero responda.
# ---------------------------------------------------------------------------
def _p(env: str, defecto: float) -> float:
    try:
        return float(os.getenv(env, defecto))
    except (TypeError, ValueError):
        return defecto


SUPUESTOS: dict[str, dict[str, Any]] = {
    "minutos_por_conciliacion": {
        "valor": _p("HUB_MIN_CONCILIACION", 12),
        "unidad": "minutos",
        "que_es": "Tiempo de una persona abriendo Nexus y Startrack y "
                  "comparando una operacion a mano",
        "fuente": "supuesto — confirmar con ECON",
    },
    "costo_hora_administrativa": {
        "valor": _p("HUB_COSTO_HORA_ADMIN", 9.0),
        "unidad": "USD/hora",
        "que_es": "Costo cargado de una hora de personal administrativo",
        "fuente": "supuesto — confirmar con ECON",
    },
    "costo_traslado_perdido": {
        "valor": _p("HUB_COSTO_TRASLADO", 380.0),
        "unidad": "USD",
        "que_es": "Cama baja, combustible y cuadrilla de un traslado que "
                  "sale y se devuelve porque el equipo no podia operar",
        "fuente": "supuesto — confirmar con ECON",
    },
    "conciliaciones_por_operacion_semana": {
        "valor": _p("HUB_CONCILIACIONES_SEMANA", 3),
        "unidad": "veces por semana",
        "que_es": "Cuantas veces por semana alguien revisa la misma operacion "
                  "en las dos plataformas",
        "fuente": "supuesto — confirmar con ECON",
    },
}


def _v(clave: str) -> float:
    return float(SUPUESTOS[clave]["valor"])


def _cifra(titulo: str, base: dict[str, Any],
           supuestos: list[str], valor: float | None,
           unidad: str, detalle: str) -> dict[str, Any]:
    """Toda cifra derivada declara de donde sale cada mitad."""
    return {
        "titulo": titulo,
        "valor": round(valor, 2) if valor is not None else None,
        "unidad": unidad,
        "base_medida": base,
        "supuesto_aplicado": [
            {"clave": k, **SUPUESTOS[k]} for k in supuestos
        ],
        "detalle": detalle,
    }


def _operaciones() -> list[dict[str, Any]]:
    out = []
    for m in listar_maquinas():
        out.extend(vista_unificada(m["maquinaria"]))
    return out


def por_area(area: str | None = None) -> dict[str, Any]:
    """El sangrado de hoy, repartido entre las tres areas que lo sufren.

    `area` filtra a una sola ('maquinaria', 'logistica' o 'proyectos') para
    que el tablero de cada jefe cargue solo lo suyo.
    """
    ops = _operaciones()

    sin_confirmar = [o for o in ops if o["estado_hub"] == ALERTA_OPERATIVA]
    sin_unidad = [o for o in ops if o["estado_hub"] == VINCULO_NO_CONFIRMADO]
    en_riesgo = [o for o in ops if o["estado_hub"] == RIESGO_CRITICO]
    con_exposicion = [o for o in ops if (o.get("exposicion") or {}).get("costo_usd")]

    horas_exp = sum((o.get("exposicion") or {}).get("horas_sin_respaldo") or 0
                    for o in ops)
    usd_exp = sum((o.get("exposicion") or {}).get("costo_usd") or 0 for o in ops)
    sin_medicion = [o for o in ops
                    if (o.get("exposicion") or {}).get("medicion") == "sin datos"]

    # Partidas (WBS) que reciben horas sin respaldo: es lo que descuadra el
    # control de costos del proyecto, y se puede nombrar una por una.
    partidas = sorted({o["solicitud"].get("partida_asignada")
                       for o in con_exposicion
                       if o["solicitud"].get("partida_asignada")})
    proyectos_afectados = sorted({o["proyecto_id"] for o in con_exposicion
                                  if o.get("proyecto_id")})

    # Reconciliacion manual: cada operacion viva se revisa a mano N veces por
    # semana. Es el trabajo que el Hub borra por completo, y el que nadie
    # contabiliza porque esta repartido en ratos de veinte minutos.
    n_ops = len(ops)
    horas_concil = (n_ops * _v("conciliaciones_por_operacion_semana")
                    * _v("minutos_por_conciliacion") / 60.0)

    areas = [
        {
            "area": AREA_MAQUINARIA,
            "titulo": "Maquinaria",
            "pregunta": "¿Alguno de mis equipos va a salir a carretera sin "
                        "estar en condiciones, o dejo de reportar?",
            "cifras": [
                _cifra(
                    "Equipos no operables con traslado vivo",
                    {"operaciones": len(en_riesgo),
                     "maquinas": [o["maquinaria"] for o in en_riesgo]},
                    [], float(len(en_riesgo)), "equipos",
                    "El equipo esta en mantenimiento y la tarea de traslado "
                    "sigue abierta. Nexus valida al SOLICITAR, no despues de "
                    "aprobada la solicitud: ese hueco es de esta area.",
                ),
                _cifra(
                    "Equipos asignados que no confirman operacion",
                    {"operaciones": len(sin_confirmar),
                     "maquinas": [o["maquinaria"] for o in sin_confirmar]},
                    [], float(len(sin_confirmar)), "equipos",
                    "Nexus los da por asignados y Startrack no confirma "
                    "reporte reciente. Puede ser el rastreador, puede ser la "
                    "maquina — y hasta saberlo, acumula costo sin avance.",
                ),
                _cifra(
                    "Equipos sin ninguna medicion de horas",
                    {"operaciones": len(sin_medicion)},
                    [], float(len(sin_medicion)), "equipos",
                    "No es que midieran cero: es que no hay medicion. Sin "
                    "horometro no hay forma de defender ni una hora cobrada.",
                ),
            ],
        },
        {
            "area": AREA_LOGISTICA,
            "titulo": "Logistica",
            "pregunta": "¿Que traslados tengo comprometidos que no se van a "
                        "poder cumplir, y cuanto tiempo gasta mi gente "
                        "cuadrando sistemas?",
            "cifras": [
                _cifra(
                    "Solicitudes aprobadas sin unidad asignada",
                    {"operaciones": len(sin_unidad),
                     "solicitudes": [o["solicitud"]["solicitud_id"]
                                     for o in sin_unidad]},
                    [], float(len(sin_unidad)), "solicitudes",
                    "Alguien las dio por resueltas. No hay unidad que mover y "
                    "el frente de obra las esta esperando.",
                ),
                _cifra(
                    "Costo de los traslados que no se pueden cumplir",
                    {"traslados": len(en_riesgo)},
                    ["costo_traslado_perdido"],
                    len(en_riesgo) * _v("costo_traslado_perdido"), "USD",
                    "Cama baja, combustible y cuadrilla de un viaje que sale "
                    "y se devuelve sin descargar.",
                ),
                _cifra(
                    "Horas-persona por semana cuadrando las dos plataformas "
                    "a mano",
                    {"operaciones_vivas": n_ops},
                    ["conciliaciones_por_operacion_semana",
                     "minutos_por_conciliacion"],
                    round(horas_concil, 1), "horas/semana",
                    "El trabajo que el Hub no acelera: lo elimina. Nadie lo "
                    "contabiliza porque esta repartido en ratos sueltos.",
                ),
                _cifra(
                    "Costo de esas horas-persona",
                    {"operaciones_vivas": n_ops},
                    ["conciliaciones_por_operacion_semana",
                     "minutos_por_conciliacion",
                     "costo_hora_administrativa"],
                    round(horas_concil * _v("costo_hora_administrativa"), 2),
                    "USD/semana",
                    "Mano de obra gastada en reconciliar datos que deberian "
                    "llegar ya cruzados.",
                ),
            ],
        },
        {
            "area": AREA_PROYECTOS,
            "titulo": "Proyectos",
            "pregunta": "¿Que le estoy cargando a mis partidas sin evidencia, "
                        "y que frentes estan parados esperando equipo?",
            "cifras": [
                _cifra(
                    "Horas cargadas sin respaldo de operacion",
                    {"horas": round(horas_exp, 1),
                     "operaciones": len(con_exposicion)},
                    [], round(horas_exp, 1), "horas",
                    "Diferencia entre lo que Nexus factura por jornada minima "
                    "y lo que Startrack midio de ignicion.",
                ),
                _cifra(
                    "Costo Real sin Valor Ganado en contra",
                    {"usd": round(usd_exp, 2),
                     "operaciones": len(con_exposicion)},
                    [], round(usd_exp, 2), "USD",
                    "AC que entra al proyecto sin EV que lo respalde. Es "
                    "exactamente lo que hunde el CPI que ya miran.",
                ),
                _cifra(
                    "Partidas WBS que reciben horas sin respaldo",
                    {"partidas": partidas, "cantidad": len(partidas)},
                    [], float(len(partidas)), "partidas",
                    "Se pueden nombrar una por una. Es donde el control de "
                    "costos va a descuadrar cuando alguien revise.",
                ),
                _cifra(
                    "Frentes esperando una unidad que nunca se asigno",
                    {"proyectos": sorted({o["proyecto_id"] for o in sin_unidad
                                          if o.get("proyecto_id")}),
                     "solicitudes": len(sin_unidad)},
                    [], float(len(sin_unidad)), "frentes",
                    "La solicitud quedo aprobada y sin unidad. El proyecto "
                    "cuenta con esa maquina en su programacion.",
                ),
            ],
            "proyectos_afectados": proyectos_afectados,
        },
    ]

    if area:
        areas = [a for a in areas if a["area"] == area.lower()]

    return {"supuestos": SUPUESTOS, "areas": areas}


# Nombre anterior, conservado para no romper a quien ya lo llamaba.
def por_rol(area: str | None = None) -> dict[str, Any]:
    return por_area(area)
