"""
Persistencia. SQLite a proposito: cero setup, cero docker, funciona en las
cuatro laptops a las 08:00. El SQL es plano para que migrar a Postgres sea
cambiar la conexion, no reescribir queries.

Duenio: Wilbert
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from typing import Any

DB_PATH = os.getenv("HUB_DB", os.path.join(os.path.dirname(__file__), "..", "hub.db"))

_local = threading.local()

SCHEMA = """
-- Log de eventos append-only. Nunca se hace UPDATE ni DELETE aqui.
CREATE TABLE IF NOT EXISTS events (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_identifier TEXT NOT NULL,
    event_timestamp  TEXT NOT NULL,
    source           TEXT NOT NULL,
    payload          TEXT NOT NULL,   -- CanonicalEvent completo en JSON
    received_at      TEXT NOT NULL DEFAULT (datetime('now')),
    idempotency_key  TEXT UNIQUE
);
CREATE INDEX IF NOT EXISTS ix_events_asset ON events(asset_identifier);
CREATE INDEX IF NOT EXISTS ix_events_ts    ON events(event_timestamp);

-- Datos maestros de la flota (MDM). Los siembra Emily.
CREATE TABLE IF NOT EXISTS assets (
    asset_identifier TEXT PRIMARY KEY,
    make             TEXT,            -- Caterpillar | Komatsu | Volvo | Mack
    model            TEXT,
    kind             TEXT,            -- excavadora | motoniveladora | cargador | cabezal | volteo
    telemetry        TEXT,            -- oem | retrofit
    state            TEXT DEFAULT 'DISPONIBLE',
    operating_hours  REAL DEFAULT 0,
    cumulative_fuel  REAL DEFAULT 0,
    engine_state     TEXT,
    lat              REAL,
    lon              REAL,
    assigned_project TEXT,
    last_service_h   REAL DEFAULT 0,  -- horometro del ultimo servicio
    service_every_h  REAL DEFAULT 250,
    last_refuel_fuel REAL,            -- cumulative_fuel en el abastecimiento anterior
    last_refuel_at   TEXT,
    alquilado_a      TEXT,            -- el alquiler a terceros es linea de negocio
                                      -- propia: una maquina alquilada no esta parada
    idle_since       TEXT,
    provenance       TEXT DEFAULT '{}',
    updated_at       TEXT
);

-- Obras y planteles con su geocerca (radio simple, no poligono: alcanza).
CREATE TABLE IF NOT EXISTS projects (
    project_id  TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    lat         REAL NOT NULL,
    lon         REAL NOT NULL,
    radius_m    REAL DEFAULT 1500,
    kind        TEXT             -- obra | plantel | planta
);

-- Alertas y ordenes que genera el motor de reglas.
CREATE TABLE IF NOT EXISTS alerts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_identifier TEXT,
    kind             TEXT NOT NULL,   -- falla | mantenimiento | ralenti | conciliacion | despacho
    severity         TEXT DEFAULT 'media',
    title            TEXT NOT NULL,
    detail           TEXT,
    payload          TEXT DEFAULT '{}',
    status           TEXT DEFAULT 'abierta',
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Solicitudes de traslado en cama baja.
CREATE TABLE IF NOT EXISTS dispatches (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_identifier TEXT NOT NULL,
    origin_project   TEXT,
    dest_project     TEXT,
    truck            TEXT,
    corridor         TEXT,
    requested_at     TEXT NOT NULL,
    eta_minutes      INTEGER,
    departure_at     TEXT,
    rescheduled      INTEGER DEFAULT 0,
    reason           TEXT,
    status           TEXT DEFAULT 'propuesto',
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Cargas de material en transito. El concreto y el asfalto son perecederos,
-- asi que una carga tiene reloj propio y el laboratorio tiene la ultima palabra
-- sobre si el lote cumple. Ver rules/carga.py.
CREATE TABLE IF NOT EXISTS cargas (
    lote                  TEXT PRIMARY KEY,
    tipo                  TEXT NOT NULL,        -- CONCRETO | ASFALTO | AGREGADO
    cantidad              REAL,
    unidad                TEXT,                 -- m3 | ton
    diseno                TEXT,                 -- f'c 280 kg/cm2, mezcla modificada
    dosificado_en         TEXT,                 -- arranca el reloj de vida
    temperatura_c         REAL,
    planta_origen         TEXT,
    obra_destino          TEXT,
    asset_identifier      TEXT,                 -- el mixer o el distribuidor
    cumple_especificacion INTEGER,              -- solo lo escribe el laboratorio
    ensayo                TEXT,                 -- que ensayo y que resultado
    estado                TEXT DEFAULT 'en_planta',
                          -- en_planta | en_transito | descargada | descartada | retenida
    provenance            TEXT DEFAULT '{}',
    created_at            TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at            TEXT
);
CREATE INDEX IF NOT EXISTS ix_cargas_asset ON cargas(asset_identifier);
CREATE INDEX IF NOT EXISTS ix_cargas_estado ON cargas(estado);

-- ---------------------------------------------------------------------
-- Prisma + Startrack — la integracion oficial del sandbox.
--
-- Independientes de assets/projects a proposito: traen su propio universo
-- de identificadores (CF-03, PROY-014...) que el propio documento dice que
-- "no corresponden necesariamente" al proyecto asignado a cada equipo.
-- Se correlacionan entre si por `maquinaria`. Ver correlacion.py.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ps_solicitudes (
    solicitud_id      TEXT PRIMARY KEY,
    proyecto_id       TEXT,
    proyecto_nombre   TEXT,
    tipo_solicitado   TEXT,
    fecha_inicio      TEXT,
    fecha_fin         TEXT,
    fecha_requerida   TEXT,
    estado_solicitud  TEXT,
    maquinaria        TEXT NOT NULL,
    estado_maquinaria TEXT,
    -- Campos reales de Nexus Modulo 8 (Maquinaria y equipo)
    clave             TEXT,   -- clave logistica interna (EQ142)
    no_activo         TEXT,   -- activo fijo contable (EXC22017LC) — llave de cruce
    empresa           TEXT,   -- ECON | La Cantera
    clase_equipo      TEXT,   -- Excavadora | Recicladora | Rodo Compactador...
    precio_hora       REAL,   -- Precio x hora de operacion interna
    horas_minimas     REAL,   -- Horas de uso minimo por jornada (8.00)
    operador          TEXT,
    partida_asignada  TEXT,   -- codigo WBS donde imputa horas (A 1.01)
    sintetico         INTEGER DEFAULT 0  -- 1 = generado, no viene de Nexus
);
CREATE INDEX IF NOT EXISTS ix_ps_sol_maq ON ps_solicitudes(maquinaria);

CREATE TABLE IF NOT EXISTS ps_tareas (
    tarea_id             TEXT PRIMARY KEY,
    maquinaria           TEXT NOT NULL,
    estado_tarea         TEXT,
    fecha_programada     TEXT,
    destino_proyecto_id  TEXT,
    destino_proyecto_nombre TEXT,
    motorista_id         TEXT,
    motorista_nombre     TEXT,
    conexion             TEXT,   -- 'Conectado' | 'Sin conexion' (solo para mostrar)
    ultimo_evento        TEXT,   -- p.ej. "Respuesta a comando"
    ultimo_evento_at     TEXT,   -- timestamp del ultimo reporte de Startrack
    identificador_raw    TEXT,   -- codigo tal cual lo expone Startrack (EXC-17006EC)
    -- Campos reales de la API de Startrack. Ver docs/PRISMA_STARTRACK.md.
    remote_id            TEXT,   -- identificador externo del vehiculo — la llave
    vehicle_id           TEXT,   -- id interno de Startrack, para las rutas /api/vehicle/<id>
    workflow_role        TEXT,   -- '0' pendiente | '1' completada | '2' cancelada
    coms_age_s           INTEGER,-- segundos desde el ultimo reporte del dispositivo
    estado_vehiculo      INTEGER,-- 0 normal | 1 mant | 2 fuera servicio | 3 reparacion | 4 ocasional
    ign_on_time_s        INTEGER,-- segundos con ignicion encendida: las horas MEDIDAS
    horometro            REAL,   -- lectura ACUMULADA de toda la vida del equipo
    horometro_base       REAL,   -- lectura al iniciar el periodo. medidas = actual - base
    lat                  REAL,   -- posicion ACTUAL del vehiculo (Startrack vehicle status)
    lon                  REAL,
    -- Geocerca de destino real (Startrack O: POI Data Object). NO confundir
    -- con lat/lon de arriba, que es la posicion del vehiculo, no de la obra.
    -- destino_poi_address y destino_poi_speed_limit_kmph no estan en la tabla
    -- oficial de campos del POI, solo en un ejemplo de respuesta real de
    -- /api/pois — ver docs/PRISMA_STARTRACK.md.
    destino_poi_id             TEXT,  -- id real del POI (no remote_id)
    destino_poi_lat            REAL,  -- y del POI
    destino_poi_lon            REAL,  -- x del POI
    destino_poi_radio_m        REAL,  -- radius del POI, en metros
    destino_poi_address        TEXT,
    destino_poi_speed_limit_kmph REAL,
    sintetico            INTEGER DEFAULT 0  -- 1 = generado, no viene de Startrack
);
CREATE INDEX IF NOT EXISTS ix_ps_tarea_maq ON ps_tareas(maquinaria);

-- Geocercas REALES del sandbox (export geocercas-4034.xlsx, 12/09). Son el
-- universo de destinos posibles: sin esto, el campo `Destino` de una tarea
-- apunta a un nombre que no existe en ninguna parte, y el mapa no tiene donde
-- ubicar nada. Coordenadas verificadas una por una contra el export.
CREATE TABLE IF NOT EXISTS ps_geocercas (
    poi_id      TEXT PRIMARY KEY,   -- `id` del POI Data Object, no `remote_id`
    nombre      TEXT NOT NULL,      -- `name` — es lo que devuelve `poi_name`
    lat         REAL NOT NULL,      -- `y`
    lon         REAL NOT NULL,      -- `x`
    radio_m     REAL,               -- `radius`, en metros
    grupo       TEXT,               -- `group_id` ya resuelto por la plataforma
    direccion   TEXT,
    sintetico   INTEGER DEFAULT 0
);

-- PEA — Protocolo de Ejecucion Automatizada. Append-only como `events`:
-- un registro sellado nunca se corrige, se emite otro. Ver pea.py.
CREATE TABLE IF NOT EXISTS pea_registros (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    maquinaria        TEXT NOT NULL,
    proyecto_id       TEXT,
    solicitud_id      TEXT,
    estado_hub        TEXT,
    horas_facturables REAL,
    monto_facturable  REAL,
    exposicion_usd    REAL,
    medicion          TEXT,      -- 'startrack' | 'sin datos'
    aprobado_por      TEXT NOT NULL,
    hash              TEXT NOT NULL,
    registro          TEXT NOT NULL,   -- el JSON completo, tal cual se sello
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_pea_maq ON pea_registros(maquinaria);

-- Salud de conectores: hace visible la integracion misma.
CREATE TABLE IF NOT EXISTS connector_stats (
    source       TEXT PRIMARY KEY,
    accepted     INTEGER DEFAULT 0,
    rejected     INTEGER DEFAULT 0,
    last_event   TEXT,
    last_error   TEXT
);
"""


def conn() -> sqlite3.Connection:
    """Una conexion por hilo. check_same_thread=False porque uvicorn usa varios."""
    c = getattr(_local, "conn", None)
    if c is None:
        c = sqlite3.connect(DB_PATH, check_same_thread=False)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA foreign_keys=ON")
        _local.conn = c
    return c


# Columnas agregadas despues del primer arranque. CREATE TABLE IF NOT EXISTS no
# las agrega a una base que ya existe, y todos tenemos un hub.db local.
MIGRACIONES = {
    "assets": {
        "last_refuel_fuel": "REAL",
        "last_refuel_at": "TEXT",
        "alquilado_a": "TEXT",
    },
    "ps_tareas": {
        "conexion": "TEXT",
        "ultimo_evento": "TEXT",
        "ultimo_evento_at": "TEXT",
        "identificador_raw": "TEXT",
        "remote_id": "TEXT",
        "vehicle_id": "TEXT",
        "workflow_role": "TEXT",
        "coms_age_s": "INTEGER",
        "estado_vehiculo": "INTEGER",
        "ign_on_time_s": "INTEGER",
        "horometro": "REAL",
        "horometro_base": "REAL",
        "lat": "REAL",
        "lon": "REAL",
        "destino_poi_id": "TEXT",
        "destino_poi_lat": "REAL",
        "destino_poi_lon": "REAL",
        "destino_poi_radio_m": "REAL",
        "destino_poi_address": "TEXT",
        "destino_poi_speed_limit_kmph": "REAL",
        "sintetico": "INTEGER DEFAULT 0",
    },
    "ps_solicitudes": {
        "clave": "TEXT",
        "no_activo": "TEXT",
        "empresa": "TEXT",
        "clase_equipo": "TEXT",
        "precio_hora": "REAL",
        "horas_minimas": "REAL",
        "operador": "TEXT",
        "partida_asignada": "TEXT",
        "sintetico": "INTEGER DEFAULT 0",
    },
}


def _migrar() -> None:
    c = conn()
    for tabla, columnas in MIGRACIONES.items():
        existentes = {r["name"] for r in c.execute(f"PRAGMA table_info({tabla})")}
        for col, tipo in columnas.items():
            if col not in existentes:
                c.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo}")
                print(f"[db] migracion: {tabla}.{col}")
    c.commit()


def init_db() -> None:
    c = conn()
    c.executescript(SCHEMA)
    c.commit()
    _migrar()


def q(sql: str, params: tuple | dict = ()) -> list[dict[str, Any]]:
    cur = conn().execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def q1(sql: str, params: tuple | dict = ()) -> dict[str, Any] | None:
    rows = q(sql, params)
    return rows[0] if rows else None


def x(sql: str, params: tuple | dict = ()) -> int:
    c = conn()
    cur = c.execute(sql, params)
    c.commit()
    return cur.lastrowid or 0


def jloads(s: str | None, default: Any = None) -> Any:
    if not s:
        return default if default is not None else {}
    try:
        return json.loads(s)
    except (ValueError, TypeError):
        return default if default is not None else {}
