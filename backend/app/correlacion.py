"""
Correlacion Prisma/Nexus + Startrack — la integracion oficial del sandbox.

Nexus (Prisma) tiene la solicitud, la asignacion y el estado del RECURSO.
Startrack tiene la tarea de traslado, la ubicacion y el estado de LA TAREA.
Son dos sistemas de registro distintos que describen la misma operacion desde
dos angulos, y el reto pide exactamente esto: consultarlos juntos,
relacionarlos, interpretar sin asumir que una diferencia es un error, y
alertar cuando la combinacion SI representa un riesgo.

Es la misma filosofia que rules/*.py y cargas.py: no fusionar en silencio,
interpretar, y abrir alerta solo cuando corresponde.

ANCLADO A DATOS REALES POR LOS DOS LADOS. De Nexus (Modulos 8 y 9) salen los
estados del recurso, los identificadores y las tarifas. De la documentacion de
la API de Startrack salen el catalogo de estados de tarea (workflow_role), el
catalogo de estado del vehiculo, la antiguedad del ultimo reporte (coms_age) y
las horas de ignicion medidas. Aqui ya no se adivina nada: los dos lados son
catalogos oficiales. Ver docs/PRISMA_STARTRACK.md.

Duenio: Wilbert
"""
from __future__ import annotations

import os
import unicodedata
from datetime import datetime, timezone
from typing import Any

from .db import q

# ---------------------------------------------------------------------------
# CATALOGO REAL DE ESTADOS — Nexus, Modulo 8 (Maquinaria y equipo)
#
# El manual muestra los contadores del inventario: Disponible 194, Ocupada 5,
# Mant. Preventivo 1, Mant. Correctivo 53, Obsoletas 0, sobre 253 equipos.
# Esto ya NO es una heuristica por palabras clave: es el catalogo cerrado.
# ---------------------------------------------------------------------------
DISPONIBLE = "disponible"
OCUPADA = "ocupada"
MANT_PREVENTIVO = "mantenimiento preventivo"
MANT_CORRECTIVO = "mantenimiento correctivo"
OBSOLETA = "obsoleta"

ESTADOS_NEXUS = (DISPONIBLE, OCUPADA, MANT_PREVENTIVO, MANT_CORRECTIVO, OBSOLETA)

# Un equipo en estos estados no puede cumplir un traslado ni producir.
NO_OPERABLES = {MANT_PREVENTIVO, MANT_CORRECTIVO, OBSOLETA}

# ---------------------------------------------------------------------------
# CATALOGO REAL DE ESTADOS DE TAREA — Startrack, GET /api/job/status
#
# Startrack no expone estados de RECURSO sino de TAREA, y cada cliente puede
# inventar los suyos ("Limpiando", "Devolucion", "No se pudo entregar"). Lo que
# NO es libre es el `workflow_role`: todo estado, con el nombre que sea, cae en
# uno de estos tres. Por eso la decision se toma sobre el rol y no sobre el
# nombre — es lo que hace que esto funcione contra un tenant que no conocemos.
# ---------------------------------------------------------------------------
ROL_PENDIENTE = "0"
ROL_COMPLETADA = "1"
ROL_CANCELADA = "2"

ROLES_ACTIVOS = {ROL_PENDIENTE}
ROLES_CERRADOS = {ROL_COMPLETADA, ROL_CANCELADA}

# Respaldo para filas sin rol: los tres estados preset que Startrack trae de
# fabrica (ids 0, 1 y 2). Solo esos tres — un estado personalizado sin rol NO
# se adivina por el nombre, se trata como desconocido, que es lo honesto.
#
# 13/09: el nombre NO es fijo como decia este comentario antes. La doc
# oficial trae el preset de fabrica en espanol (`client_id: "-1"` en
# /api/job/status), pero la cuenta real del sandbox (4034) esta configurada
# en ingles — confirmado en jobs-4034-...xlsx. Un cliente puede renombrar
# hasta los tres presets, no solo agregar custom. Por eso van los dos
# idiomas: esto sigue siendo un respaldo de mejor esfuerzo, no una garantia
# contra un tenant que no conocemos — para eso esta el chequeo de
# workflow_role primero.
ROL_POR_NOMBRE_PRESET = {
    "pendiente": ROL_PENDIENTE,
    "completada": ROL_COMPLETADA,
    "cancelada": ROL_CANCELADA,
    "pending": ROL_PENDIENTE,
    "completed": ROL_COMPLETADA,
    "canceled": ROL_CANCELADA,
    "cancelled": ROL_CANCELADA,
}


def rol_tarea(tarea: dict[str, Any] | None) -> str | None:
    """El workflow_role de la tarea, o None si no se puede determinar."""
    if not tarea:
        return None
    rol = tarea.get("workflow_role")
    if rol not in (None, ""):
        return str(rol)
    return ROL_POR_NOMBRE_PRESET.get(_norm(tarea.get("estado_tarea")))


# ---------------------------------------------------------------------------
# CATALOGO REAL DE ESTADO DEL VEHICULO — Startrack, O: Default Vehicle Status
#
# Startrack lleva su PROPIO estado de mantenimiento, independiente del de
# Nexus. Que las dos plataformas registren mantenimiento por separado y ninguna
# le avise a la otra es justamente la tesis del Hub.
# ---------------------------------------------------------------------------
VEH_NORMAL = 0
VEH_MANTENIMIENTO = 1
VEH_FUERA_SERVICIO = 2
VEH_EN_REPARACION = 3
VEH_USO_OCASIONAL = 4

ETIQUETA_ESTADO_VEHICULO = {
    VEH_NORMAL: "Normal",
    VEH_MANTENIMIENTO: "En Mantenimiento",
    VEH_FUERA_SERVICIO: "Fuera de Servicio",
    VEH_EN_REPARACION: "En Reparacion",
    VEH_USO_OCASIONAL: "Se usa de vez en cuando",
}

# El dispositivo en reparacion (3) NO impide operar la maquina: lo que esta
# averiado es el rastreador, no el equipo. Por eso no entra aqui.
VEH_NO_OPERABLES = {VEH_MANTENIMIENTO, VEH_FUERA_SERVICIO}

# Segundos sin reportar a partir de los cuales dejamos de dar por confirmada la
# operacion. CRITERIO NUESTRO, no de la documentacion de Startrack: una jornada
# completa sin un solo reporte es el umbral que elegimos para no disparar por
# el hueco normal de la noche. Si ECON opera turnos, esto se ajusta.
UMBRAL_CONEXION_S = int(os.getenv("HUB_STARTRACK_UMBRAL_CONEXION", "86400"))


def sin_confirmacion(tarea: dict[str, Any] | None) -> bool:
    """True si Startrack no confirma operacion reciente.

    Manda `coms_age_s` (el numero que da la API). El texto de `conexion` solo
    se usa cuando no hay numero — en la demo sembrada, por ejemplo.
    """
    if not tarea:
        return False
    edad = tarea.get("coms_age_s")
    if edad is not None:
        return int(edad) >= UMBRAL_CONEXION_S
    return "sin conexion" in _norm(tarea.get("conexion"))


def _norm(texto: str | None) -> str:
    """Minusculas, sin tildes, con 'mant.' expandido.

    Nexus y Startrack pueden escribir el mismo estado distinto ('Obsoleta
    (mantenimiento correctivo)' vs 'MANT. CORRECTIVO'). El catalogo es fijo;
    la forma de escribirlo no.
    """
    if not texto:
        return ""
    t = "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                if unicodedata.category(c) != "Mn")
    return t.replace("mant.", "mantenimiento").strip()


def estado_nexus(texto: str | None) -> str | None:
    """Mapea el texto crudo al catalogo cerrado de Modulo 8, o None."""
    t = _norm(texto)
    if not t:
        return None
    # El orden importa: 'mantenimiento correctivo' antes que 'mantenimiento'.
    for estado in (MANT_CORRECTIVO, MANT_PREVENTIVO, OBSOLETA, OCUPADA, DISPONIBLE):
        if estado in t:
            return estado
    return None


# ---------------------------------------------------------------------------
# LOS CINCO ESTADOS DEL HUB — tabla de decision de la especificacion (hoja 4)
#
# Cada uno lleva la accion textual del Excel y el AREA responsable.
#
# Las areas son las tres que confirmaron los organizadores: Maquinaria,
# Logistica y Proyectos. No es una taxonomia nuestra — es como esta partida
# la operacion en ECON, y por eso cada alerta cae en el escritorio de alguien
# que de verdad puede actuar sobre ella.
#
#   Maquinaria   dueña del activo. Decide si un equipo puede operar o no.
#   Logistica    mueve el equipo. Asigna unidades y ejecuta los traslados.
#   Proyectos    consume el equipo y paga las horas. Sufre el costo y el atraso.
# ---------------------------------------------------------------------------
# Las tres areas de ECON. Todo lo que el Hub produce cae en una de ellas.
AREA_MAQUINARIA = "maquinaria"
AREA_LOGISTICA = "logistica"
AREA_PROYECTOS = "proyectos"

AREAS = (AREA_MAQUINARIA, AREA_LOGISTICA, AREA_PROYECTOS)

EN_OPERACION_NORMAL = "en_operacion_normal"
DIFERENCIA_VALIDA = "diferencia_valida"
ALERTA_OPERATIVA = "alerta_operativa"
RIESGO_CRITICO = "riesgo_critico"
VINCULO_NO_CONFIRMADO = "vinculo_no_confirmado"

CATALOGO_ESTADOS_HUB = {
    EN_OPERACION_NORMAL: {
        "etiqueta": "En operacion normal",
        "nivel": "ok",
        "accion": "Continuar monitoreo",
        "area": AREA_LOGISTICA,
        "responsable": "Logistica",
    },
    DIFERENCIA_VALIDA: {
        "etiqueta": "En operacion en destino",
        "nivel": "info",
        "accion": "No marcar conflicto",
        "area": AREA_LOGISTICA,
        "responsable": "Logistica",
    },
    ALERTA_OPERATIVA: {
        "etiqueta": "Asignada con alerta operativa",
        "nivel": "alerta",
        # El equipo esta asignado pero no confirma que opera. Quien puede
        # decir si la maquina esta bien es quien es dueño de la maquina.
        "accion": "Validar ubicacion y conectividad del equipo",
        "area": AREA_MAQUINARIA,
        "responsable": "Maquinaria",
    },
    RIESGO_CRITICO: {
        "etiqueta": "Riesgo de despacho",
        "nivel": "critico",
        # La decision de si un equipo sale o no sale es de Maquinaria.
        # Logistica ejecuta el traslado, pero no autoriza al equipo averiado.
        "accion": "Detener el traslado y confirmar estado del equipo",
        "area": AREA_MAQUINARIA,
        "responsable": "Maquinaria",
    },
    VINCULO_NO_CONFIRMADO: {
        "etiqueta": "Relacion pendiente",
        "nivel": "indeterminado",
        # Una solicitud aprobada sin unidad es una asignacion que falta hacer.
        "accion": "Asignar unidad o validar identificador",
        "area": AREA_LOGISTICA,
        "responsable": "Logistica",
    },
}


def clasificar_estado(solicitud: dict[str, Any],
                      tarea: dict[str, Any] | None) -> dict[str, Any]:
    """
    Devuelve uno de los cinco estados del Hub, con su accion y responsable.

    El orden de evaluacion importa: primero lo que impide siquiera comparar
    (vinculo), despues el riesgo, despues la falta de confirmacion, y de
    ultimo los dos casos sanos.
    """
    est_maq = estado_nexus(solicitud.get("estado_maquinaria"))
    rol = rol_tarea(tarea)

    # --- 1. sin poder cruzar: no hay tarea, o no hay unidad asignada --------
    # El propio portafolio de Nexus tiene solicitudes "Aprobada / Sin asignar".
    sin_unidad = not (solicitud.get("no_activo") or solicitud.get("maquinaria"))
    if tarea is None or sin_unidad:
        motivo = ("la solicitud no tiene unidad asignada" if sin_unidad
                  else "no hay tarea de Startrack relacionada")
        return _resultado(VINCULO_NO_CONFIRMADO, solicitud, tarea, motivo=motivo)

    # --- 2. riesgo: el recurso no puede operar y la tarea sigue viva --------
    # Cualquiera de los dos sistemas puede reportar el mantenimiento, y el
    # riesgo es el mismo. Que solo uno lo sepa es precisamente el problema.
    no_operable_nexus = est_maq in NO_OPERABLES
    no_operable_startrack = tarea.get("estado_vehiculo") in VEH_NO_OPERABLES
    if (no_operable_nexus or no_operable_startrack) and rol in ROLES_ACTIVOS:
        return _resultado(RIESGO_CRITICO, solicitud, tarea)

    # --- 3. asignada pero sin confirmacion operativa ------------------------
    if sin_confirmacion(tarea):
        return _resultado(ALERTA_OPERATIVA, solicitud, tarea)

    # --- 4. diferencia valida: la tarea cerro, el recurso sigue ocupado -----
    if est_maq == OCUPADA and rol in ROLES_CERRADOS:
        return _resultado(DIFERENCIA_VALIDA, solicitud, tarea)

    # --- 5. todo confirmado -------------------------------------------------
    return _resultado(EN_OPERACION_NORMAL, solicitud, tarea)


def _resultado(clave: str, solicitud: dict, tarea: dict | None,
               motivo: str | None = None) -> dict[str, Any]:
    base = dict(CATALOGO_ESTADOS_HUB[clave])
    base["estado"] = clave
    base["detalle"] = _detalle(clave, solicitud, tarea, motivo)
    return base


def _detalle(clave: str, solicitud: dict, tarea: dict | None,
             motivo: str | None) -> str:
    em = solicitud.get("estado_maquinaria") or "sin estado"
    et = (tarea or {}).get("estado_tarea") or "sin tarea"

    if clave == VINCULO_NO_CONFIRMADO:
        return (
            f"No se puede correlacionar todavia: {motivo}. Nexus registra la "
            f"solicitud en '{solicitud.get('estado_solicitud') or 'sin estado'}', "
            "pero falta el dato que permite cruzarla con Startrack."
        )
    if clave == RIESGO_CRITICO:
        veh = (tarea or {}).get("estado_vehiculo")
        en_nexus = estado_nexus(solicitud.get("estado_maquinaria")) in NO_OPERABLES
        en_startrack = veh in VEH_NO_OPERABLES
        etq = ETIQUETA_ESTADO_VEHICULO.get(veh, "sin estado")

        if en_nexus and en_startrack:
            origen = (
                f"Las DOS plataformas lo saben — Nexus en '{em}', Startrack en "
                f"'{etq}' — y ninguna se lo dice a la otra: la tarea sigue en "
                f"'{et}'."
            )
        elif en_startrack:
            origen = (
                f"Solo Startrack lo sabe: tiene el vehiculo en '{etq}' mientras "
                f"Nexus lo reporta en '{em}' y la tarea sigue en '{et}'."
            )
        else:
            origen = (
                f"Solo Nexus lo sabe: reporta el equipo en '{em}' y Startrack "
                f"mantiene la tarea en '{et}'."
            )
        return (
            f"{origen} Nexus bloquea SOLICITAR un equipo en mantenimiento, pero "
            "no revisa el cambio de estado despues de aprobada la solicitud: "
            "ese es el hueco. La tarea no se puede cumplir."
        )
    if clave == ALERTA_OPERATIVA:
        ult = (tarea or {}).get("ultimo_evento_at") or "sin registro"
        edad = (tarea or {}).get("coms_age_s")
        cuanto = (f"{round(int(edad) / 3600)} h sin reportar" if edad is not None
                  else (tarea or {}).get("conexion") or "sin reportar")
        return (
            f"La asignacion es valida — Nexus la tiene en '{em}' — pero "
            f"Startrack no confirma operacion: {cuanto}, ultimo evento {ult}. "
            "No es una contradiccion: es falta de confirmacion, y mientras dure "
            "se acumula costo sin avance."
        )
    if clave == DIFERENCIA_VALIDA:
        return (
            f"'{em}' describe el RECURSO en Nexus y '{et}' describe LA TAREA "
            "en Startrack. Los dos son correctos a la vez: el traslado "
            "termino y el equipo quedo ocupado en el destino. No es conflicto."
        )
    return (
        f"Nexus: '{em}'. Startrack: '{et}', conectado. Las dos plataformas "
        "coinciden y la operacion esta confirmada."
    )


# ---------------------------------------------------------------------------
# KPI — "Horas facturadas sin respaldo de operacion medida"
#
# Aqui se cruzan los dos sistemas en un solo numero, y ese es el punto:
#
#   Nexus FACTURA    Modulo 8: precio_hora x horas_minimas por jornada (8.00),
#                    y el minimo se cobra aunque el equipo no produzca.
#   Startrack MIDE   GET /api/vehicles/stats devuelve `ign_on_time`: segundos
#                    con ignicion encendida. Son las horas que de verdad hubo.
#
# La diferencia entre lo facturado y lo medido es Costo Real (AC) sin Valor
# Ganado (EV): fuga de CPI directa, en la metrica que Control de Costos ya
# mira. Y deja de ser inferencia nuestra — es resta.
#
# OJO: `ign_on_hrs` de GET /api/vehicle/<id>/stats NO se usa. El ejemplo de la
# documentacion trae 100.8 "horas" en un solo dia, que es imposible, junto a un
# init_ign_on_hrs de 584186.4: parecen lecturas de horometro acumulado y no
# duracion diaria. Se usa `ign_on_time`, que esta documentado en segundos.
# Verificar contra un tenant real antes de tocar esto.
# ---------------------------------------------------------------------------
HORAS_MINIMAS_DEFECTO = 8.0


def exposicion(solicitud: dict[str, Any], tarea: dict[str, Any] | None,
               ahora: datetime | None = None) -> dict[str, Any] | None:
    """Horas facturadas, horas medidas y el costo de la diferencia.

    None si no hay con que calcular.
    """
    if not tarea:
        return None
    ref = tarea.get("ultimo_evento_at")
    if not ref:
        return None
    try:
        t0 = datetime.fromisoformat(str(ref).replace("Z", "+00:00"))
    except ValueError:
        return None
    if t0.tzinfo is None:
        t0 = t0.replace(tzinfo=timezone.utc)

    ahora = ahora or datetime.now(timezone.utc)
    dias = max(0.0, (ahora - t0).total_seconds() / 86400.0)

    horas_min = solicitud.get("horas_minimas") or HORAS_MINIMAS_DEFECTO
    precio = solicitud.get("precio_hora")

    # Jornadas completas: el minimo se factura por jornada, no por fraccion.
    jornadas = int(dias)
    facturadas = round(jornadas * horas_min, 1)

    # Sin telemetria no decimos "midio cero": decimos que no hay medicion. Un
    # cero medido y la ausencia de medicion son cosas distintas, y presentar
    # una como la otra es exactamente lo que le criticamos a sus tableros.
    ign = tarea.get("ign_on_time_s")
    hay_medicion = ign is not None
    medidas = round(int(ign) / 3600.0, 1) if hay_medicion else 0.0
    sin_respaldo = round(max(0.0, facturadas - medidas), 1)

    return {
        "dias_sin_confirmacion": round(dias, 1),
        "jornadas_facturables": jornadas,
        "horas_minimas_jornada": horas_min,
        "horas_facturadas": facturadas,
        "horas_medidas": medidas if hay_medicion else None,
        "horas_sin_respaldo": sin_respaldo,
        "medicion": "startrack" if hay_medicion else "sin datos",
        # Se conserva el nombre viejo: el panel y las pruebas lo usan, y
        # cuando no hay medicion vale exactamente lo mismo que antes.
        "horas_expuestas": sin_respaldo,
        "precio_hora": precio,
        "costo_usd": round(sin_respaldo * precio, 2) if precio else None,
        "explicacion": (
            f"Nexus facturo {facturadas:g} h (minimo de {horas_min:.0f} h por "
            f"jornada) y Startrack midio {medidas:g} h de ignicion: "
            f"{sin_respaldo:g} h de Costo Real (AC) sin Valor Ganado (EV). "
            "Impacta el CPI del proyecto."
        ) if hay_medicion else (
            f"Costo Real (AC) acumulado sin Valor Ganado (EV): el minimo de "
            f"{horas_min:.0f} h por jornada se factura aunque el equipo no "
            "produzca. Startrack no reporta horas de ignicion para este "
            "equipo, asi que no hay nada que descontar. Impacta el CPI."
        ),
    }


# ---------------------------------------------------------------------------
# MAPEO DE CAMPOS — hoja 2 de la especificacion.
# Es la respuesta literal a "el mapeo entre plataformas debera ser definido
# por cada equipo". Se sirve en /api/ps/mapeo y se muestra en la demo.
# ---------------------------------------------------------------------------
MAPEO_CAMPOS = [
    # LA LLAVE. El Diccionario de Datos es explicito: Prisma identifica el
    # equipo con "No. de activo" (ej. "CF-03 - Cargador frontal 03") y
    # Startrack con "Descripcion" (ej. "CF-03"). Se cruza por el codigo corto.
    {"concepto": "Identificador del equipo", "nexus": "No. de activo",
     "startrack": "Vehiculos > Descripcion", "relacion": "1:1 por codigo corto",
     "decision": "LLAVE DE CRUCE — normalizando el sufijo descriptivo",
     "ejemplo": "EXC-01"},
    {"concepto": "Identificador externo", "nexus": "No expuesto",
     "startrack": "Vehiculos > ID remoto", "relacion": "Exclusivo Startrack",
     "decision": "Identificador numerico de la organizacion, NO el activo fijo",
     "ejemplo": "78093"},
    {"concepto": "Clave logistica", "nexus": "Clave (EQ142)",
     "startrack": "No existe", "relacion": "Exclusivo Nexus",
     "decision": "Referencia interna, no sirve de llave", "ejemplo": "EQ142"},
    {"concepto": "Nombre del equipo", "nexus": "Nombre del equipo",
     "startrack": "Descripcion", "relacion": "Redundante con la llave",
     "decision": "Solo para mostrar", "ejemplo": "Cargador frontal 03"},
    {"concepto": "Clase", "nexus": "Clase de equipo",
     "startrack": "Vehiculos > Tipo", "relacion": "1:1",
     "decision": "Catalogo cerrado de 5 clases en el diccionario",
     "ejemplo": "Excavadora"},
    {"concepto": "Estado del recurso", "nexus": "Estado (catalogo)",
     "startrack": "Vehiculos > Estado", "relacion": "Ambos, independientes",
     "decision": "Cualquiera de los dos dispara el riesgo",
     "ejemplo": "Mant. correctivo / Normal"},
    {"concepto": "Proyecto", "nexus": "Solicitudes > Proyecto",
     "startrack": "Geocercas > Nombre", "relacion": "Por nombre de geocerca",
     "decision": "Nexus define el proyecto; la geocerca valida la ubicacion",
     "ejemplo": "PROY-014 - Proyecto Xi"},
    {"concepto": "Solicitud", "nexus": "Estado de solicitud",
     "startrack": "No existe", "relacion": "Exclusivo Nexus",
     "decision": "Catalogo: Aprobada o Pendiente", "ejemplo": "Aprobada"},
    {"concepto": "Quien solicita", "nexus": "Solicitudes > Solicita",
     "startrack": "No existe", "relacion": "Exclusivo Nexus",
     "decision": "Gerente de Proyecto — responsable del pedido",
     "ejemplo": "Maria Jose Lopez Ramirez"},
    {"concepto": "Periodo", "nexus": "Solicitudes > Periodo",
     "startrack": "Tareas > Fecha programada", "relacion": "Parcial",
     "decision": "Nexus da la vigencia; Startrack la fecha del traslado",
     "ejemplo": "11/09/2026 - 14/09/2026"},
    {"concepto": "Estado de la tarea", "nexus": "No existe",
     "startrack": "Tareas > Estado (workflow_role)",
     "relacion": "Exclusivo Startrack",
     "decision": "El nombre es libre, el rol 0/1/2 no", "ejemplo": "Pendiente"},
    {"concepto": "Origen y destino", "nexus": "No existe",
     "startrack": "Tareas > Origen / Destino", "relacion": "Exclusivo Startrack",
     "decision": "Geocercas del ejercicio", "ejemplo": "PROY-014"},
    {"concepto": "Conductor", "nexus": "No expuesto",
     "startrack": "Vehiculos > Conductor", "relacion": "Exclusivo Startrack",
     "decision": "Responsable operativo del traslado",
     "ejemplo": "MOT-014 - Adriana Steiner"},
    {"concepto": "Recencia del reporte", "nexus": "No existe",
     "startrack": "coms_age (segundos)", "relacion": "Exclusivo Startrack",
     "decision": "Umbral de una jornada — criterio nuestro",
     "ejemplo": "107 580 s = 30 h"},
    {"concepto": "Horas de operacion", "nexus": "Horas minimas facturadas",
     "startrack": "Mantenimiento > Horometro / ign_on_time",
     "relacion": "Complementarios",
     "decision": "Facturado menos medido = AC sin EV", "ejemplo": "8 h vs 7.5 h"},
    {"concepto": "Tarifa", "nexus": "Precio x hora + horas minimas",
     "startrack": "No existe", "relacion": "Exclusivo Nexus",
     "decision": "Valoriza la exposicion en dolares", "ejemplo": "$150/h x 8 h"},
    {"concepto": "Ubicacion", "nexus": "No existe",
     "startrack": "Latitud / Longitud", "relacion": "Exclusivo Startrack",
     "decision": "Vienen escaladas por 1e7 en el formato 2",
     "ejemplo": "133376152 = 13.3376152"},
    {"concepto": "Estado del Hub", "nexus": "Calculado", "startrack": "Calculado",
     "relacion": "Calculado por el Hub",
     "decision": "Separa riesgo real de diferencia valida",
     "ejemplo": "Asignada con alerta"},
]


def vista_unificada(maquinaria: str) -> list[dict[str, Any]]:
    """
    Todas las operaciones conocidas de una maquina: una por solicitud, con su
    tarea relacionada, el estado calculado del Hub y la exposicion en dolares.
    """
    solicitudes = q(
        "SELECT * FROM ps_solicitudes WHERE maquinaria = ? ORDER BY solicitud_id",
        (maquinaria,),
    )
    tareas = q(
        "SELECT * FROM ps_tareas WHERE maquinaria = ? ORDER BY tarea_id",
        (maquinaria,),
    )
    tareas_por_proyecto = {t.get("destino_proyecto_id"): t for t in tareas}

    operaciones = []
    for s in solicitudes:
        t = tareas_por_proyecto.get(s.get("proyecto_id"))
        estado = clasificar_estado(s, t)
        # La exposicion se calcula para toda operacion con tarea, no solo para
        # las que estan en alerta: un equipo conectado y medido tiene que poder
        # dar ~0. Si la KPI solo apareciera donde ya hay alerta, no probaria
        # nada — hay que verla quedarse callada cuando todo esta bien.
        exp = exposicion(s, t)
        operaciones.append({
            "maquinaria": maquinaria,
            "no_activo": s.get("no_activo"),
            "proyecto_id": s.get("proyecto_id"),
            "proyecto_nombre": s.get("proyecto_nombre"),
            "solicitud": s,
            "tarea": t,
            "estado_hub": estado["estado"],
            "etiqueta": estado["etiqueta"],
            "nivel": estado["nivel"],
            "accion": estado["accion"],
            "area": estado["area"],
            "responsable": estado["responsable"],
            "interpretacion": estado["detalle"],
            "exposicion": exp,
        })
    return operaciones


def listar_maquinas() -> list[dict[str, Any]]:
    """Roster para el selector, con la exposicion total acumulada."""
    filas = q(
        "SELECT DISTINCT maquinaria FROM ps_solicitudes"
        " UNION SELECT DISTINCT maquinaria FROM ps_tareas"
    )
    out = []
    for f in filas:
        m = f["maquinaria"]
        ops = vista_unificada(m)
        costo = sum((o["exposicion"] or {}).get("costo_usd") or 0 for o in ops)
        out.append({
            "maquinaria": m,
            "operaciones": len(ops),
            "con_alerta": sum(1 for o in ops if o["nivel"] in ("alerta", "critico")),
            "costo_expuesto_usd": round(costo, 2),
        })
    return out
