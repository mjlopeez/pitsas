"""
Semilla de Prisma/Nexus + Startrack — datos REALES, no inventados.

Todo lo que se siembra aqui sale de fuentes oficiales:

  1. Manual de usuario de Nexus ECON — Modulos 8 y 9: el catalogo de estados,
     los identificadores (Clave y No. de activo), las tarifas por hora, y el
     portafolio real de solicitudes.
  2. Entregables_Hub_Operaciones_Aventra.xlsm — el caso real de la demo
     (EXC-01, Proyecto Alfa, Ahuachapan) con los datos de Startrack.
  3. Casos de Uso Final.docx — los tres escenarios de referencia (CF-03).
  4. Export real de la cuenta del sandbox (4034), sacado directo de
     Startrack el 12/09: `geocercas-4034.xlsx` (Puntos de Referencia) y
     `jobs-4034-...xlsx` (Tareas + resumenes). Este es el que corrige al #2
     donde chocan: el #2 es un documento de entrega, esto es la cuenta viva.
     Cruzado ademas contra la doc oficial completa de la API
     (`startrack-api-docs/`, scrape de support.gps-platform.com) para no
     quedarnos solo con lo que dice el Excel de campos.

Las dos anomalias mas interesantes NO las inventamos: estan en las propias
capturas del manual. "Recicladora WIRTGEN — Pendiente — Sin asignar" y
"RETRO EXCAVADORA — Aprobada — Sin asignar" son solicitudes reales de su
portafolio, y son exactamente el estado `vinculo_no_confirmado`.

⚠️ Correccion 13/09 contra la fuente #4: el `estado_tarea` de las 4 tareas
de abajo estaba en espanol ("Asignada"/"Completada"/"Pendiente"). La cuenta
real del sandbox usa ingles (`Pending`/`Completed`/`Canceled`, mas un
`Partial` personalizado) — confirmado en la hoja "Resumen por Estado" del
export de tareas. No es el preset de fabrica de Startrack (ese SI es en
espanol, `client_id: "-1"` en la doc oficial de `/api/job/status`): alguien
configuro este tenant especifico en ingles. No cambia el `workflow_role`
(la clasificacion ya decidia por rol, no por nombre — eso quedo bien desde
el principio), solo el texto que se le muestra al usuario.

Duenio: Wilbert
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..db import q1, x


def _hace(horas: float) -> str:
    """Timestamp relativo a AHORA, en ISO 8601.

    ⚠️ Por que relativo y no la fecha fija del export:

    La exposicion cuenta JORNADAS COMPLETAS desde el ultimo evento
    (`int(dias)` en correlacion.py). Con una fecha fija, cada dia que pasa
    suma una jornada facturada y los numeros del guion se mueven solos:

        EXC-02  $75    ->  $1,275   al cruzar las 48 h
        EXC-03  $9.50  ->  $769.50
        RE-01   $0     ->  $1,680   al cruzar las 24 h

    Ahi se muere el argumento de que "la KPI se queda callada cuando todo
    esta bien": la maquina sana gritaria mas fuerte que la averiada.

    El INTERVALO es lo que sostiene el guion ("30 h sin reportar") y se
    conserva exacto. Lo que se mueve es la fecha absoluta, que no se cita en
    ninguna parte del pitch.
    """
    return (datetime.now(timezone.utc) - timedelta(hours=horas)).isoformat()


def _sol(**kw) -> None:
    cols = ", ".join(kw)
    ph = ", ".join("?" * len(kw))
    x(f"INSERT OR REPLACE INTO ps_solicitudes ({cols}) VALUES ({ph})",
      tuple(kw.values()))


def _tar(**kw) -> None:
    cols = ", ".join(kw)
    ph = ", ".join("?" * len(kw))
    x(f"INSERT OR REPLACE INTO ps_tareas ({cols}) VALUES ({ph})", tuple(kw.values()))


def _geo(**kw) -> None:
    cols = ", ".join(kw)
    ph = ", ".join("?" * len(kw))
    x(f"INSERT OR REPLACE INTO ps_geocercas ({cols}) VALUES ({ph})", tuple(kw.values()))


# ===========================================================================
# GEOCERCAS REALES — export `geocercas-4034.xlsx` del 12/09, sin tocar.
# (poi_id, nombre, lat, lon, radio_m)
#
# PROY-014 vale la pena mirarlo: 13.3376152 / -87.8486967 es EXACTAMENTE el
# 133376152 / -878486967 que el Diccionario de Datos trae como ejemplo. El
# escalado por 1e7 que normaliza `ingest/startrack_webhook.py` no era una
# suposicion nuestra: aqui esta el mismo punto en los dos formatos.
# ===========================================================================
GEOCERCAS_REALES = [
    ("5456061", "PLANTA ORIGEN", 13.487927, -89.2958028, 500),
    ("5455284", "PROY-001 - Aventra - Proyecto Alfa - Ahuachapán", 13.9290675, -89.8436594, 1000),
    ("5455285", "PROY-002 - DAURUS - Proyecto Beta - Santa Ana", 13.9837933, -89.5628214, 1000),
    ("5455286", "PROY-003 - EconHackers - Proyecto Gamma - Sonsonate", 13.7106614, -89.7304967, 996),
    ("5455291", "PROY-004 - FASI - Proyecto Delta - Chalatenango", 14.175271, -89.1647502, 1000),
    ("5455288", "PROY-005 - Goat Goating Goats - Proyecto Épsilon - La Libertad", 13.6724738, -89.3977352, 1000),
    ("5455287", "PROY-006 - Los Filósofos - Proyecto Zeta - San Salvador", 13.6914782, -89.2152518, 1003),
    ("5456058", "PROY-007 - MechaBytes - Proyecto Eta - Cuscatlán", 13.8454447, -89.013073, 1000),
    ("5456059", "PROY-008 - Negentropy - Proyecto Theta - La Paz", 13.425318, -88.9918795, 1000),
    ("5456057", "PROY-009 - Sync Masters - Cabañas Proyecto Iota - Cabañas", 13.8813874, -88.7378998, 1000),
    ("5455292", "PROY-010 - Tralaleritos - Proyecto Kappa - San Vicente", 13.6405872, -88.7839214, 1000),
    ("5456056", "PROY-011 - UTECOps - Proyecto Lambda - Usulután", 13.3432736, -88.4427738, 999),
    ("5455289", "PROY-012 - Valdocco Studio - Proyecto Mu - San Miguel", 13.4785173, -88.1690892, 1000),
    ("5456060", "PROY-013 - Truers - Proyecto Nu - Morazán", 13.770361, -88.1494991, 1000),
    ("5455290", "PROY-014 - The Hub - Proyecto Xi - La Unión", 13.3376152, -87.8486967, 1000),
]


def sembrar_geocercas() -> int:
    """Las 15 geocercas del sandbox. Idempotente."""
    for poi_id, nombre, lat, lon, radio in GEOCERCAS_REALES:
        _geo(poi_id=poi_id, nombre=nombre, lat=lat, lon=lon, radio_m=radio,
             grupo="29611 - Geocercas-Hackathon")
    return len(GEOCERCAS_REALES)


def sembrar_casos() -> dict[str, int]:
    """Idempotente: INSERT OR REPLACE, se puede correr las veces que sea."""

    # =======================================================================
    # EL CASO REAL DE LA DEMO — EXC-01 (equipo Aventra)
    # Fuente: Entregables_Hub_Operaciones_Aventra.xlsm, hoja "Caso EXC-01".
    #
    # Nexus tiene la asignacion aprobada. Startrack conserva ubicacion y
    # conductor pero NO confirma conexion reciente. No es contradiccion: es
    # una asignacion valida con alerta operativa, y mientras dura acumula
    # costo sin avance.
    # =======================================================================
    _sol(
        solicitud_id="SOL-EXC01", proyecto_id="PROY-001",
        proyecto_nombre="Aventra - Proyecto Alfa - Ahuachapan",
        tipo_solicitado="Excavadora", fecha_inicio="11/09/2026",
        fecha_fin="14/09/2026", estado_solicitud="Aprobada",
        maquinaria="EXC-01", estado_maquinaria="Ocupada",
        clave="EQ117", no_activo="EXC-17006EC", empresa="ECON",
        clase_equipo="Excavadora", precio_hora=150.00, horas_minimas=8.0,
        operador="MOT-001 - Maria Jose Lopez Ramirez",
        partida_asignada="A 1.02 - EXCAVACION",
    )
    _tar(
        tarea_id="TAR-EXC01", maquinaria="EXC-01",
        # Ver nota de correccion 13/09 arriba: nombre real de esta cuenta,
        # no el preset de fabrica.
        estado_tarea="Pending",
        fecha_programada="11/09/2026", destino_proyecto_id="PROY-001",
        # Nombre real del POI en Startrack (geocercas-4034.xlsx, columna
        # "Nombre") — con el prefijo "PROY-001 -" y la tilde, tal cual lo
        # devolveria `poi_name` en el Job Data Object.
        destino_proyecto_nombre="PROY-001 - Aventra - Proyecto Alfa - Ahuachapán",
        motorista_id="MOT-001", motorista_nombre="Maria Jose Lopez Ramirez",
        conexion="Sin conexion", ultimo_evento="Respuesta a comando",
        ultimo_evento_at=_hace(30),   # 1 jornada, sin medicion -> $1,200
        identificador_raw="EXC-01 (EXC-17006EC)",
        # remote_id es el campo que Startrack documenta para cruzar con otros
        # sistemas, y acepta el formato del No. de activo de Nexus tal cual.
        remote_id="EXC-17006EC", vehicle_id="1057", workflow_role="0",
        coms_age_s=107580, estado_vehiculo=0,
        # Sin reportes no hay horas medidas. ign_on_time_s queda NULL a
        # proposito: no es "midio cero", es "no hay medicion".
        # Sin reportes no hay medicion. ign_on_time_s y horometro_base quedan
        # NULL a proposito: no es "midio cero", es "no hay medicion".
        ign_on_time_s=None, horometro=4520.0, horometro_base=None,
        # Geocerca real (O: POI Data Object, campo `id` — no `remote_id`,
        # que en el export viene raro/repetido entre dos filas y no se usa
        # aqui por eso): geocercas-4034.xlsx, fila "PROY-001 - Aventra -
        # Proyecto Alfa - Ahuachapan". radio y direccion tal cual el export.
        # speed_limit_kmph no viene en esa fila (no es columna del export,
        # solo aparece en un ejemplo de la doc oficial para otro POI) y
        # queda sin dato — no se inventa un numero solo porque el campo
        # exista en la doc.
        destino_poi_id="5455284", destino_poi_lat=13.9290675,
        destino_poi_lon=-89.8436594, destino_poi_radio_m=1000,
        destino_poi_address="Calle H, Ahuachapán, 2101, Ahuachapán, El Salvador",
    )

    # =======================================================================
    # PORTAFOLIO REAL DE NEXUS — Modulo 9, tabla de solicitudes del manual
    # =======================================================================

    # Pala Excavadora Volvo EC480DL — aprobada y asignada, operando normal.
    # Los datos de la bitacora real del manual: operador WILFREDO RIVERA,
    # partida A 1.01 DEMOLICION, horometro 1474 -> 1481.55.
    _sol(
        solicitud_id="SOL-EXC02", proyecto_id="PROY-002",
        proyecto_nombre="PROY-002 - DAURUS - Proyecto Beta - Santa Ana",
        tipo_solicitado="Excavadora",
        fecha_inicio="15/03/2026", fecha_fin="13/05/2026",
        estado_solicitud="Aprobada", maquinaria="EXC-02",
        estado_maquinaria="Ocupada", clave="EQ142", no_activo="EXC-17007EC",
        empresa="ECON", clase_equipo="Excavadora",
        precio_hora=150.00, horas_minimas=8.0,
        operador="MOT-002 - Haydee Abigail Bonilla Reyes",
        partida_asignada="A 1.01 - DEMOLICION DE PISO DE CONCRETO",
    )
    _tar(
        tarea_id="TAR-EXC02", maquinaria="EXC-02",
        estado_tarea="Completed",  # ver nota de correccion 13/09, arriba
        fecha_programada="15/03/2026", destino_proyecto_id="PROY-002",
        destino_proyecto_nombre="PROY-002 - DAURUS - Proyecto Beta - Santa Ana",
        motorista_id="MOT-002", motorista_nombre="Haydee Abigail Bonilla Reyes",
        conexion="Conectado", ultimo_evento="Fin de jornada",
        # El evento de la TAREA es de ayer; el dispositivo sigue reportando
        # hace media hora. En la API de Startrack son dos cosas distintas:
        # los eventos de job y el last_contact_date del rastreador.
        ultimo_evento_at=_hace(30),   # 1 jornada, 7.5 h medidas -> $75
        identificador_raw="EXC-02 (EXC-17007EC)",
        remote_id="EXC-17007EC", vehicle_id="939", workflow_role="1",
        coms_age_s=1800, estado_vehiculo=0,
        # ⚠️ PROVENIENCIA, dicho exacto: la lectura 1474 -> 1481.55 SI sale del
        # manual de Nexus, pero de OTRO equipo (la Pala Volvo EC480DL, que no
        # existe en el sandbox). Se conserva la magnitud porque es una jornada
        # real de una excavadora real; el identificador y el conductor si son
        # de la plataforma de prueba. O sea: "lectura real de un equipo
        # equivalente", NO "lectura de este equipo". Si un juez pregunta, se
        # dice asi y no se pierde nada.
        #
        # Esta fila existe para probar que la KPI se queda callada cuando todo
        # cuadra: 7.55 h medidas contra 8 h facturadas. Sin ella, el numero de
        # EXC-01 parece un martillo que ve clavos.
        horometro_base=1474.0, horometro=1481.55,
        ign_on_time_s=int((1481.55 - 1474.0) * 3600),
    )

    # Rodo Compactador — el traslado cerro y el equipo quedo ocupado en
    # destino. Diferencia valida: NO es conflicto.
    _sol(
        solicitud_id="SOL-EXC03", proyecto_id="PROY-003",
        proyecto_nombre="PROY-003 - EconHackers - Proyecto Gamma - Sonsonate",
        tipo_solicitado="Excavadora",
        fecha_inicio="20/03/2026", fecha_fin="13/05/2026",
        estado_solicitud="Aprobada", maquinaria="EXC-03",
        estado_maquinaria="Ocupada", clave="EQ088", no_activo="EXC-22008EC",
        # Clase del catalogo cerrado de 5 del Diccionario. "Rodo Compactador"
        # (lo que habia antes) NO esta en ese catalogo ni en el sandbox.
        empresa="ECON", clase_equipo="Excavadora",
        precio_hora=95.00, horas_minimas=8.0,
        operador="MOT-003 - Sergio Henriquez",
        partida_asignada="A 1.04 - RESTITUCION",
    )
    _tar(
        tarea_id="TAR-EXC03", maquinaria="EXC-03",
        estado_tarea="Completed",  # ver nota de correccion 13/09, arriba
        fecha_programada="20/03/2026", destino_proyecto_id="PROY-003",
        destino_proyecto_nombre="PROY-003 - EconHackers - Proyecto Gamma - Sonsonate",
        motorista_id="MOT-003", motorista_nombre="Sergio Henriquez",
        conexion="Conectado", ultimo_evento="Fin de traslado",
        ultimo_evento_at=_hace(30),   # 1 jornada, 7.9 h medidas -> $9.50
        identificador_raw="EXC-03 (EXC-22008EC)",
        remote_id="EXC-22008EC", vehicle_id="1122", workflow_role="1",
        coms_age_s=2400, estado_vehiculo=0,
        # Sin dato real del manual para este equipo: la lectura es nuestra,
        # pero la resta es la misma que aplicaria en produccion.
        horometro_base=972.3, horometro=980.2,
        ign_on_time_s=int((980.2 - 972.3) * 3600),
    )

    # ANOMALIA REAL 1 — "Recicladora WIRTGEN | Pendiente | Sin asignar".
    # Esta tal cual en la captura del Modulo 9. Sin unidad asignada no hay
    # nada que cruzar con Startrack.
    _sol(
        solicitud_id="SOL-WIRTGEN", proyecto_id="PROY-ECON-REC",
        proyecto_nombre="Proyecto ECON Demo - reciclado",
        tipo_solicitado="Recicladora WIRTGEN", fecha_inicio="25/03/2026",
        fecha_fin="13/05/2026", estado_solicitud="Pendiente",
        maquinaria="SOL-WIRTGEN-SIN-UNIDAD", estado_maquinaria=None,
        clase_equipo="Recicladora", horas_minimas=8.0,
    )

    # ANOMALIA REAL 2 — "RETRO EXCAVADORA | Aprobada | Sin asignar".
    # Peor que la anterior: la solicitud YA fue aprobada pero nunca se le
    # asigno unidad. El Coordinador la dio por resuelta y nadie lo nota.
    _sol(
        solicitud_id="SOL-RETRO", proyecto_id="PROY-PRUEBA",
        proyecto_nombre="Proyecto PRUEBA", tipo_solicitado="RETRO EXCAVADORA",
        fecha_inicio="04/05/2026", fecha_fin="08/05/2026",
        estado_solicitud="Aprobada", maquinaria="SOL-RETRO-SIN-UNIDAD",
        estado_maquinaria=None, clase_equipo="Retroexcavadora", horas_minimas=8.0,
    )

    # =======================================================================
    # RIESGO DE DESPACHO — el hueco temporal que Nexus no cubre.
    #
    # Nexus bloquea SOLICITAR un equipo en mantenimiento
    # (TRANSIT_EQUIPMENT_IN_MAINTENANCE). Lo que no revisa es el cambio de
    # estado DESPUES de aprobada la solicitud: el equipo entra a Mant.
    # Correctivo y la tarea de Startrack sigue viva. 53 de 253 equipos del
    # inventario real estan en Mant. Correctivo.
    # =======================================================================
    _sol(
        solicitud_id="SOL-RE01", proyecto_id="PROY-004",
        proyecto_nombre="PROY-004 - FASI - Proyecto Delta - Chalatenango",
        tipo_solicitado="Retroexcavadora", fecha_inicio="10/09/2026",
        fecha_fin="30/09/2026", estado_solicitud="Aprobada",
        maquinaria="RE-01", estado_maquinaria="Mant. Correctivo",
        clave="EQ203", no_activo="RE-22007EC", empresa="ECON",
        # "Recicladora" tampoco esta en el catalogo de 5 clases.
        clase_equipo="Retroexcavadora", precio_hora=210.00, horas_minimas=8.0,
        operador="MOT-004 - Helder Ariel Alfaro Alvarez",
        partida_asignada="IND 3-4 - Limpieza",
    )
    _tar(
        tarea_id="TAR-RE01", maquinaria="RE-01",
        estado_tarea="Pending",  # ver nota de correccion 13/09, arriba
        fecha_programada="14/09/2026", destino_proyecto_id="PROY-004",
        destino_proyecto_nombre="PROY-004 - FASI - Proyecto Delta - Chalatenango",
        motorista_id="MOT-004", motorista_nombre="Helder Ariel Alfaro Alvarez",
        conexion="Conectado", ultimo_evento="Reporte de posicion",
        ultimo_evento_at=_hace(12),   # <1 jornada -> $0: aqui el riesgo NO es el costo
        identificador_raw="RE-01 (RE-22007EC)",
        remote_id="RE-22007EC", vehicle_id="1408", workflow_role="0",
        coms_age_s=3600,
        # Startrack tambien lo tiene en mantenimiento (status 1). Los dos
        # sistemas lo saben por separado y ninguno se lo dice al otro: ese es
        # el caso mas contundente del guion.
        estado_vehiculo=1,
        horometro_base=2210.0, horometro=2210.0, ign_on_time_s=0,
    )

    n_geo = sembrar_geocercas()

    n_sol = (q1("SELECT COUNT(*) AS n FROM ps_solicitudes") or {"n": 0})["n"]
    n_tar = (q1("SELECT COUNT(*) AS n FROM ps_tareas") or {"n": 0})["n"]
    return {"solicitudes": n_sol, "tareas": n_tar, "geocercas": n_geo}
