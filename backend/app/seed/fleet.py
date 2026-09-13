"""
Nodos y flota de Grupo ECON.

ECON esta integrada verticalmente, y eso cambia el modelo de datos: los nodos
no son solo obras, son tambien la cantera, las plantas de concreto y asfalto,
los planteles y el aeropuerto. Cada uno es origen o destino de carga, y los
silos estan tambien ENTRE esas unidades.

⚠️ EMILY, antes de las 12:00 — dos cosas que NO estan verificadas:

  1. Las coordenadas de los pasos a desnivel del AMSS y de las plantas son
     APROXIMADAS. Se sabe que estan donde dice, pero no con precision de metros.
     Verificalas y corregilas aqui. La regla de CLAUDE.md aplica: un dato
     inventado sobre su propio pais lo detecta un juez de ECON en segundos.

  2. Los numeros de modelo del equipo estan marcados con MODELO_A_VERIFICAR.
     Las CATEGORIAS si son las que ECON publica textualmente en su catalogo de
     alquiler; las marcas son las estandar de la industria para cada categoria.
     Cambia los modelos por los del catalogo real.

Duenio: Emily
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from ..db import x

# ---------------------------------------------------------------------------
# NODOS  (project_id, nombre, lat, lon, radio_m, tipo)
#
# tipo: obra | aeropuerto | cantera | planta_concreto | planta_asfalto | plantel
#
# Las distancias entre estos nodos estan elegidas para que las cuatro salidas
# del motor de despacho de carga sean alcanzables con obras reales:
#   PCSS -> PDUT  ( ~8 km)  el desvio salva la carga        -> reruta
#   PCSS -> APLL  (~22 km)  no alcanza por ninguna ruta      -> no dosificar
#   PCSS -> BSON  (~54 km)  fuera de la vida del concreto    -> fuera de alcance
# ---------------------------------------------------------------------------
PROYECTOS = [
    # --- obras que ECON publica ---
    ("PDUT", "Paso desnivel Utila",                   13.6731, -89.2900, 800,  "obra"),
    ("PDEJ", "Paso desnivel El Jaguar",               13.7000, -89.2050, 800,  "obra"),
    ("PDNU", "Paso desnivel Naciones Unidas",         13.6950, -89.2350, 800,  "obra"),
    ("PDCL", "Paso desnivel Claudia Lars",            13.7080, -89.2420, 800,  "obra"),
    ("BSON", "Bypass de Sonsonate",                   13.7190, -89.7240, 2500, "obra"),
    ("PGBA", "Periferico Gerardo Barrios, San Miguel", 13.4780, -88.1780, 3000, "obra"),
    ("APLL", "Ampliacion carretera al Puerto de La Libertad", 13.5200, -89.3100, 2500, "obra"),
    ("CHOR", "Tramo Los Chorros",                     13.6633, -89.3606, 3000, "obra"),
    ("QZTP", "Quezaltepeque",                         13.8342, -89.2747, 2000, "obra"),
    ("AIES", "Aeropuerto Internacional — pista principal", 13.4409, -89.0557, 2000, "aeropuerto"),

    # --- cantera: la fuente de agregado basaltico (empresa hermana) ---
    ("LCSD", "La Cantera San Diego",                  13.4869, -89.2958, 1800, "cantera"),

    # --- 4 plantas de concreto ---
    ("PCSS", "Planta de concreto San Salvador",       13.7000, -89.2200, 700,  "planta_concreto"),
    ("PCLL", "Planta de concreto La Libertad Costa",  13.4883, -89.3222, 700,  "planta_concreto"),
    ("PCSM", "Planta de concreto San Miguel",         13.4800, -88.1830, 700,  "planta_concreto"),
    ("PCSO", "Planta de concreto Sonsonate",          13.7200, -89.7250, 700,  "planta_concreto"),

    # --- plantas de asfalto ---
    ("PASS", "Planta de asfalto San Salvador",        13.7050, -89.2300, 700,  "planta_asfalto"),
    ("PASD", "Planta de asfalto San Diego",           13.4900, -89.2980, 700,  "planta_asfalto"),

    # --- plantel / taller central ---
    ("PLSS", "Plantel y taller central San Salvador", 13.7010, -89.2390, 900,  "plantel"),
]

PLANTAS_CONCRETO = [p[0] for p in PROYECTOS if p[5] == "planta_concreto"]
OBRAS = [p[0] for p in PROYECTOS if p[5] in ("obra", "aeropuerto")]

# ---------------------------------------------------------------------------
# CATALOGO DE EQUIPO
#
# Las categorias son las que ECON publica en su catalogo de alquiler. Las marcas
# son las estandar de la industria para cada categoria. Los modelos estan
# marcados: Emily los cambia por los del catalogo real.
#
# telemetria: oem      = tiene telemetria de fabrica, entra por su API
#             retrofit = no tiene, entra por el modulo CAN J1939
# ---------------------------------------------------------------------------
EQUIPOS = [
    # (marca, modelo, categoria, telemetria)
    ("Caterpillar", "320",    "excavadora",              "oem"),
    ("Caterpillar", "336",    "excavadora",              "oem"),
    ("Komatsu",     "PC200",  "excavadora",              "oem"),
    ("Volvo",       "EC220",  "excavadora",              "oem"),
    ("Caterpillar", "140",    "motoniveladora",          "oem"),
    ("Komatsu",     "GD555",  "motoniveladora",          "oem"),
    ("Caterpillar", "950",    "cargador frontal",        "oem"),
    ("Volvo",       "L120",   "cargador frontal",        "oem"),
    ("Komatsu",     "D65",    "tractor de bandas",       "oem"),
    ("Caterpillar", "D6",     "tractor de bandas",       "oem"),
    ("Caterpillar", "426",    "retroexcavadora",         "retrofit"),
    ("Komatsu",     "WB93",   "retroexcavadora",         "retrofit"),
    ("Caterpillar", "246",    "minicargador",            "retrofit"),
    ("Wirtgen",     "W200",   "perfiladora",             "retrofit"),
    ("Wirtgen",     "WR240",  "recicladora",             "retrofit"),
    ("Wirtgen",     "WR250",  "estabilizadora de suelo", "retrofit"),
    ("Vogele",      "S1800",  "terminadora de asfalto",  "retrofit"),
    ("Hamm",        "HD120",  "rodillo liso mixto",      "retrofit"),
    ("Hamm",        "H13i",   "rodillo compactador",     "retrofit"),
    ("Hamm",        "GRW280", "rodillo neumatico",       "retrofit"),
    ("Caterpillar", "815",    "rodillo pata de cabra",   "retrofit"),
    ("Putzmeister", "BSA1409", "bomba de concreto",      "retrofit"),
    ("Schwing",     "S36X",   "bomba de concreto",       "retrofit"),
    ("Terex",       "RT555",  "grua telescopica",        "retrofit"),
    ("Grove",       "GMK3060", "grua telescopica",       "retrofit"),
    ("Genie",       "S65",    "grua plataforma",         "retrofit"),
    ("Wacker",      "LTN6",   "torre de iluminacion",    "retrofit"),
    ("Ver-Mac",     "PCMS",   "pantalla electronica",    "retrofit"),
    ("Ver-Mac",     "AFAD",   "flecha electronica",      "retrofit"),
]

# Transporte y distribucion. Los mixers y los distribuidores de asfalto son los
# que cargan material perecedero: son el centro del minuto 3 de la demo.
TRANSPORTE = [
    ("Mack",  "GR64BTX", "cabezal",                     "retrofit"),
    ("Volvo", "FMX",     "cabezal",                     "oem"),
    ("Mack",  "RD688S",  "camion de volteo",            "retrofit"),
    ("Freightliner", "114SD", "camion de volteo",       "retrofit"),
    ("Mack",  "GU813",   "camion mezclador",            "retrofit"),
    ("Volvo", "FM440",   "camion mezclador",            "oem"),
    ("Mack",  "MR688",   "camion cisterna",             "retrofit"),
    ("Etnyre","Black-Topper", "camion distribuidor de asfalto", "retrofit"),
    ("Etnyre","Chip-Spreader", "distribuidor de agregados",     "retrofit"),
    ("Talbert", "55SA",  "lowboy",                      "retrofit"),
]

PREFIJO = {
    "Caterpillar": "CAT", "Komatsu": "KOM", "Volvo": "VOL", "Mack": "MACK",
    "Wirtgen": "WIR", "Vogele": "VOG", "Hamm": "HAM", "Putzmeister": "PUT",
    "Schwing": "SCH", "Terex": "TRX", "Grove": "GRV", "Genie": "GEN",
    "Wacker": "WAC", "Ver-Mac": "VMC", "Freightliner": "FRL",
    "Etnyre": "ETN", "Talbert": "TAL",
}

# Alquiler a terceros: es una linea de negocio propia de ECON, y cambia el KPI
# de utilizacion. Una maquina alquilada NO es una maquina parada.
CLIENTES_ALQUILER = [
    "MOP — contrato de mantenimiento vial",
    "PUNTTO — desarrollo habitacional",
    "Constructora tercera",
]


def sembrar(n_equipos: int = 100, n_transporte: int = 50, semilla: int = 12) -> dict[str, int]:
    """Idempotente (INSERT OR REPLACE) y determinista (misma semilla, misma flota)."""
    rnd = random.Random(semilla)
    ahora = datetime.now(timezone.utc)

    for p in PROYECTOS:
        x("INSERT OR REPLACE INTO projects (project_id, name, lat, lon, radius_m, kind)"
          " VALUES (?,?,?,?,?,?)", p)

    def crear(catalogo, cantidad, arranque=1):
        creados = 0
        for i in range(cantidad):
            marca, modelo, categoria, tele = catalogo[i % len(catalogo)]
            asset_id = f"{PREFIJO[marca]}-{modelo}-{arranque + i:02d}"
            nodo = rnd.choice(PROYECTOS)
            horas = round(rnd.uniform(800, 19000), 1)

            # Un 15 % queda cerca del umbral de servicio a proposito, para que el
            # motor de mantenimiento dispare solo durante la demo. Mas que eso
            # llena el mapa de maquinas en mantenimiento y ahoga la senial de FALLA.
            desde_serv = (rnd.uniform(238, 252) if rnd.random() < 0.15
                          else rnd.uniform(0, 200))

            # Un solo sorteo del combustible: la base del ciclo de abastecimiento
            # se deriva de EL MISMO valor, no de otro sorteo.
            fuel = round(horas * rnd.uniform(2.5, 4.5), 1)
            # En un 20 % el hueco se deja grande a proposito: asi un vale de
            # 120 gal dispara el ticket del 5 % sin forzar nada.
            hueco = rnd.uniform(55, 70) if rnd.random() < 0.20 else rnd.uniform(95, 125)

            estado_motor = rnd.choice(["ON", "ON", "IDLE", "OFF"])
            # Un 12 % de la flota esta alquilada a terceros.
            alquilado = rnd.choice(CLIENTES_ALQUILER) if rnd.random() < 0.12 else None

            x(
                "INSERT OR REPLACE INTO assets (asset_identifier, make, model, kind,"
                " telemetry, state, operating_hours, cumulative_fuel, engine_state,"
                " lat, lon, assigned_project, last_service_h, service_every_h,"
                " last_refuel_fuel, last_refuel_at, alquilado_a, idle_since,"
                " provenance, updated_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    asset_id, marca, modelo, categoria, tele,
                    {"ON": "OPERANDO", "IDLE": "RALENTI", "OFF": "DISPONIBLE"}[estado_motor],
                    horas, fuel, estado_motor,
                    nodo[2] + rnd.uniform(-0.006, 0.006),
                    nodo[3] + rnd.uniform(-0.006, 0.006),
                    nodo[0], round(horas - desde_serv, 1), 250,
                    round(fuel - hueco, 1), None, alquilado,
                    (ahora - timedelta(minutes=rnd.randint(3, 70))).isoformat()
                    if estado_motor == "IDLE" else None,
                    "{}", ahora.isoformat(),
                ),
            )
            creados += 1
        return creados

    eq = crear(EQUIPOS, n_equipos)
    tr = crear(TRANSPORTE, n_transporte)

    # --- activos del guion de la demo ---------------------------------------
    # Existen siempre, en el mismo lugar y sanos al arrancar. Josue depende de
    # esto a las 15:00 y los ensayos tienen que ser reproducibles.

    # Minutos 1 y 2: la excavadora que reporta la falla hidraulica.
    x(
        "INSERT OR REPLACE INTO assets (asset_identifier, make, model, kind, telemetry,"
        " state, operating_hours, cumulative_fuel, engine_state, lat, lon,"
        " assigned_project, last_service_h, service_every_h, provenance, updated_at)"
        " VALUES ('CAT-320-04','Caterpillar','320','excavadora','oem','OPERANDO',"
        " 4515.0, 18120.0,'ON', 13.7085, -89.2425,'PDCL', 4300.0, 250,'{}', ?)",
        (ahora.isoformat(),),
    )
    # Minuto 3: el mixer que sale de la Planta de concreto San Salvador.
    x(
        "INSERT OR REPLACE INTO assets (asset_identifier, make, model, kind, telemetry,"
        " state, operating_hours, cumulative_fuel, engine_state, lat, lon,"
        " assigned_project, last_service_h, service_every_h, provenance, updated_at)"
        " VALUES ('MACK-GU813-01','Mack','GU813','camion mezclador','retrofit',"
        " 'DISPONIBLE', 9240.0, 31500.0,'OFF', 13.7002, -89.2202,'PCSS', 9100.0, 250,"
        " '{}', ?)",
        (ahora.isoformat(),),
    )

    # Determinismo del guion: CAT-320-04 tiene que ser LA UNICA 320 en el paso a
    # desnivel Claudia Lars. Si no, "la 320 aqui en Claudia Lars" resuelve a otra
    # maquina y el minuto 1 apunta al marcador equivocado.
    x("UPDATE assets SET assigned_project = 'PDNU'"
      " WHERE model = '320' AND assigned_project = 'PDCL'"
      "   AND asset_identifier <> 'CAT-320-04'")

    return {
        "nodos": len(PROYECTOS),
        "equipos": eq,
        "transporte": tr,
        "plantas_concreto": len(PLANTAS_CONCRETO),
        "categorias": len({e[2] for e in EQUIPOS} | {t[2] for t in TRANSPORTE}),
    }
