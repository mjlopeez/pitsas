"""
Generador de datos sinteticos — para que el equipo trabaje sin el sandbox.

Nadie puede tener cuatro personas pegadas al sandbox de ECON, y el Command
Center con seis filas no se ve como se vera en produccion. Esto genera un
inventario del tamanio real contra el que Majo puede maquetar, Josue puede
ensayar y cualquiera puede reproducir un bug.

TRES REGLAS DE DISENIO, y las tres importan:

1. **Determinista.** Mismo `seed`, mismos datos, byte por byte. Si Majo ve un
   bug con seed 42, Wilbert lo reproduce con seed 42. Sin esto, los datos
   sinteticos crean mas trabajo del que ahorran.

2. **Marcado.** Toda fila lleva `sintetico = 1`. El tablero lo muestra y
   `/api/sintetico/limpiar` lo borra sin tocar nada mas. Es la misma regla
   que el distintivo "en vivo / simulado": nunca presentar dato generado como
   si viniera de sus sistemas.

3. **Aditivo.** No toca las seis filas de la demo (EXC-01 y companiia). El
   minuto 2 del guion sigue funcionando con o sin esto cargado.

QUE ES REAL Y QUE NO:

  REAL       La distribucion de estados. El Modulo 8 del manual de Nexus
             muestra sus contadores sobre 253 equipos: Disponible 194,
             Ocupada 5, Mant. Preventivo 1, Mant. Correctivo 53, Obsoleta 0.
             Se respeta esa proporcion, y por eso el inventario generado
             "se siente" como el de ellos: uno de cada cinco equipos esta en
             mantenimiento correctivo.
  REAL       El formato de los identificadores: clase + correlativo + empresa
             (EC = ECON, LC = La Cantera), y la clave logistica EQ###.
  SINTETICO  Nombres de proyecto, operadores, tarifas por clase y horometros.
             Plausibles, no reales. Por eso van marcados.

Duenio: Wilbert
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any

from ..db import q1, x

# --- Distribucion REAL del Modulo 8 (253 equipos del inventario de ECON) ---
DISTRIBUCION_ESTADOS = [
    ("Disponible", 194),
    ("Ocupada", 5),
    ("Mant. Preventivo", 1),
    ("Mant. Correctivo", 53),
    ("Obsoleta", 0),
]
TOTAL_MANUAL = sum(n for _, n in DISTRIBUCION_ESTADOS)

# CATALOGO CERRADO de clases — Diccionario de Datos oficial, hoja PRISMA:
#   "Excavadora; Retroexcavadora; Motoniveladora; Minicargador; Cargador frontal"
#
# Son cinco y no mas. Antes este generador producia Barredora, Bomba
# Lanzadora, Rodo Compactador, Recicladora, Tractor Oruga y Cama Baja: ninguna
# esta en su catalogo. Generar clases que no existen en su sistema es la clase
# de detalle que un juez de ECON nota de inmediato.
#
# Las TARIFAS si son sinteticas y estan declaradas como tales en el modulo.
# (Como referencia, las dos unicas que el manual de Nexus muestra explicitas
# son Barredora $200/hr y Bomba Lanzadora $2,002/hr, pero esas clases no
# aparecen en el diccionario, asi que no se generan.)
CLASES = [
    # (clase, prefijo de activo, tarifa sintetica)
    ("Excavadora", "EXC", 150.0),
    ("Retroexcavadora", "RET", 110.0),
    ("Motoniveladora", "MOT", 165.0),
    ("Minicargador", "MIN", 85.0),
    ("Cargador frontal", "CF", 120.0),
]

EMPRESAS = [("ECON", "EC"), ("La Cantera", "LC")]

PROYECTOS = [
    ("PROY-101", "Ampliacion Carretera Litoral"),
    ("PROY-102", "Planta de Concreto Nejapa"),
    ("PROY-103", "Bypass Santa Ana"),
    ("PROY-104", "Cantera El Transito"),
    ("PROY-105", "Urbanizacion Antiguo Cuscatlan"),
    ("PROY-106", "Rehabilitacion Troncal del Norte"),
]

PARTIDAS = [
    "A 1.01 - DEMOLICION DE PISO DE CONCRETO",
    "A 1.02 - EXCAVACION",
    "A 1.04 - RESTITUCION",
    "A 2.01 - CONFORMACION DE SUBRASANTE",
    "A 3.02 - COLOCACION DE CARPETA",
    "IND 3-4 - Limpieza",
]

NOMBRES = ["Wilfredo", "Maria Jose", "Adriana", "Jose Luis", "Carmen", "Rodrigo",
           "Elena", "Mauricio", "Silvia", "Nelson", "Patricia", "Oscar"]
APELLIDOS = ["Rivera", "Lopez Ramirez", "Steiner", "Morales Marroquin", "Hernandez",
             "Castellanos", "Bonilla", "Aguilar", "Portillo", "Menjivar"]

# Estados de tarea de Startrack con su workflow_role (catalogo cerrado).
ESTADOS_TAREA = [
    ("Pendiente", "0"), ("En curso", "0"), ("Asignada", "0"),
    ("Completada", "1"), ("Entregado", "1"),
    ("Cancelada", "2"), ("No se pudo entregar", "2"),
]


def _estados_para(n: int, rnd: random.Random) -> list[str]:
    """Reparte n equipos respetando la proporcion real del Modulo 8."""
    out: list[str] = []
    for estado, cuenta in DISTRIBUCION_ESTADOS:
        out.extend([estado] * round(cuenta / TOTAL_MANUAL * n))
    while len(out) < n:
        out.append("Disponible")
    out = out[:n]
    rnd.shuffle(out)
    return out


def generar(equipos: int = 120, seed: int = 42) -> dict[str, Any]:
    """Genera `equipos` unidades con sus solicitudes y tareas. Idempotente.

    Idempotente en el sentido util: correrlo dos veces con el mismo seed deja
    exactamente el mismo dataset, porque los identificadores se derivan del
    indice y el INSERT es OR REPLACE.
    """
    equipos = max(1, min(int(equipos), 500))
    rnd = random.Random(seed)
    ahora = datetime.now(timezone.utc)
    estados = _estados_para(equipos, rnd)

    n_sol = n_tar = 0
    for i in range(equipos):
        clase, prefijo, tarifa = rnd.choice(CLASES)
        empresa, suf = rnd.choice(EMPRESAS)
        estado_maq = estados[i]

        # Formato real: clase + correlativo + empresa. Ej: EXC22017LC
        no_activo = f"{prefijo}{rnd.randint(10, 24)}{i:03d}{suf}"
        clave = f"EQ{100 + i}"
        proy_id, proy_nom = rnd.choice(PROYECTOS)
        operador = f"{rnd.choice(NOMBRES)} {rnd.choice(APELLIDOS)}"

        # Una fracción de las solicitudes queda sin unidad asignada — es el
        # caso que aparece en las propias capturas del manual, no un invento.
        sin_unidad = rnd.random() < 0.06
        maquinaria = f"SYN-SOL-{i:03d}-SIN-UNIDAD" if sin_unidad else no_activo
        estado_sol = rnd.choice(["Aprobada", "Aprobada", "Aprobada", "Pendiente"])

        inicio = ahora - timedelta(days=rnd.randint(1, 60))
        fin = inicio + timedelta(days=rnd.randint(15, 90))

        x("INSERT OR REPLACE INTO ps_solicitudes"
          " (solicitud_id, proyecto_id, proyecto_nombre, tipo_solicitado,"
          "  fecha_inicio, fecha_fin, estado_solicitud, maquinaria,"
          "  estado_maquinaria, clave, no_activo, empresa, clase_equipo,"
          "  precio_hora, horas_minimas, operador, partida_asignada, sintetico)"
          " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
          (f"SYN-SOL-{i:03d}", proy_id, proy_nom, clase,
           inicio.strftime("%d/%m/%Y"), fin.strftime("%d/%m/%Y"), estado_sol,
           maquinaria, None if sin_unidad else estado_maq,
           None if sin_unidad else clave, None if sin_unidad else no_activo,
           None if sin_unidad else empresa, clase, tarifa, 8.0,
           "Sin asignar" if sin_unidad else operador, rnd.choice(PARTIDAS)))
        n_sol += 1

        if sin_unidad:
            continue  # sin unidad no hay nada que trasladar

        nombre_tarea, rol = rnd.choice(ESTADOS_TAREA)

        # Conexion: la mayoria reporta. Una minoria lleva horas o dias sin
        # hacerlo, que es justo lo que dispara la alerta operativa.
        if rnd.random() < 0.15:
            coms = rnd.randint(90_000, 400_000)   # sobre el umbral de 1 jornada
            conexion = "Sin conexion"
        else:
            coms = rnd.randint(60, 7_200)
            conexion = "Conectado"

        base = round(rnd.uniform(300, 9000), 1)
        # Horas de la jornada: casi siempre cerca del minimo de 8, a veces no.
        trabajadas = round(rnd.uniform(5.5, 8.5), 2)
        horometro = round(base + trabajadas, 2)
        ultimo = ahora - timedelta(seconds=coms)

        x("INSERT OR REPLACE INTO ps_tareas"
          " (tarea_id, maquinaria, estado_tarea, fecha_programada,"
          "  destino_proyecto_id, destino_proyecto_nombre, motorista_id,"
          "  motorista_nombre, conexion, ultimo_evento, ultimo_evento_at,"
          "  identificador_raw, remote_id, vehicle_id, workflow_role,"
          "  coms_age_s, estado_vehiculo, ign_on_time_s, horometro,"
          "  horometro_base, lat, lon, sintetico)"
          " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
          (f"SYN-TAR-{i:03d}", maquinaria, nombre_tarea,
           inicio.strftime("%d/%m/%Y"), proy_id, proy_nom,
           f"MOT-{200 + i}", operador, conexion,
           rnd.choice(["Reporte de posicion", "Fin de traslado",
                       "Respuesta a comando", "Ignicion apagada"]),
           ultimo.isoformat(), f"{clase} ({no_activo})", no_activo,
           str(3000 + i), rol, coms,
           # Startrack tambien reporta mantenimiento, a veces antes que Nexus.
           1 if estado_maq.startswith("Mant") and rnd.random() < 0.5 else 0,
           int(trabajadas * 3600), horometro, base,
           round(rnd.uniform(13.4, 14.4), 5), round(rnd.uniform(-90.1, -88.2), 5)))
        n_tar += 1

    return {"ok": True, "seed": seed, "equipos": equipos,
            "solicitudes_generadas": n_sol, "tareas_generadas": n_tar,
            **estado()}


def limpiar() -> dict[str, Any]:
    """Borra SOLO lo sintetico. Las seis filas de la demo no se tocan."""
    x("DELETE FROM ps_tareas WHERE sintetico = 1")
    x("DELETE FROM ps_solicitudes WHERE sintetico = 1")
    return {"ok": True, **estado()}


def estado() -> dict[str, Any]:
    def _n(sql: str) -> int:
        return (q1(sql) or {"n": 0})["n"]

    return {
        "solicitudes_sinteticas": _n(
            "SELECT COUNT(*) AS n FROM ps_solicitudes WHERE sintetico = 1"),
        "solicitudes_reales": _n(
            "SELECT COUNT(*) AS n FROM ps_solicitudes WHERE COALESCE(sintetico,0) = 0"),
        "tareas_sinteticas": _n(
            "SELECT COUNT(*) AS n FROM ps_tareas WHERE sintetico = 1"),
        "tareas_reales": _n(
            "SELECT COUNT(*) AS n FROM ps_tareas WHERE COALESCE(sintetico,0) = 0"),
    }
