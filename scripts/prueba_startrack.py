#!/usr/bin/env python3
"""
Prueba del conector de Startrack SIN tocar la red.

sincronizar() es el codigo que corre en vivo el dia que alguien ponga las
credenciales, y contra un tenant real no lo podemos probar desde aqui. Asi que
se le da una respuesta con la forma EXACTA que documenta
`GET /api/fleet/status` y se verifica que cada campo aterrice donde debe.

Si Startrack cambia un nombre de campo, o si alguien toca el mapeo, esto lo
canta antes de que se vea en el escenario.

Uso:  python3 scripts/prueba_startrack.py
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import startrack                                    # noqa: E402
from app.db import init_db, q1, x                            # noqa: E402
from app.seed.prisma_startrack import sembrar_casos          # noqa: E402

# Respuesta calcada del ejemplo de la documentacion, con los identificadores
# de nuestra semilla. epoch = hace 2 horas.
HACE_2H = int(time.time()) - 7200
FLOTA_FALSA = [
    {
        "vehId": 218, "driverId": 15,
        "vehDescr": "EXC-01 - Excavadora 01", "description": "Excavadora 01",
        "vehStat": 1,                      # 1 = en reparacion / mantenimiento
        "place": "Ahuachapan", "orgn": "Plantel", "refId": 132,
        "epoch": str(HACE_2H),
        "x": "-89.845000", "y": "13.921000",   # x = longitud, y = latitud
        "event": 2, "eventDescription": "ignicion apagada",
        "speed": 0, "heading": 34, "odometer": 512.08,
        "ignOn": 0, "ignOnHrs": 4525.5, "tripDist": 2.8, "direction": 229,
    },
]

fallos: list[str] = []


def check(nombre: str, obtenido, esperado) -> None:
    ok = obtenido == esperado
    print(f"  {'OK  ' if ok else 'FALLA'} {nombre}")
    if not ok:
        print(f"        esperaba: {esperado!r}\n        obtuvo:   {obtenido!r}")
        fallos.append(nombre)


def main() -> int:
    init_db()
    sembrar_casos()

    # Credenciales falsas solo para pasar el switch; _get se reemplaza.
    os.environ.update(STARTRACK_HOST="ejemplo.invalido",
                      STARTRACK_API_KEY="x", STARTRACK_PASSWORD="y")
    startrack._get = lambda ruta, params=None: (          # type: ignore[assignment]
        FLOTA_FALSA if ruta == "fleet/status" else None)

    print("== primera sincronizacion: fija la linea base ==")
    r = startrack.sincronizar()
    check("una sola peticion para toda la flota", r.get("peticiones"), 1)
    check("cruza EXC-01 por la descripcion del vehiculo", r.get("actualizadas"), 1)

    t = q1("SELECT * FROM ps_tareas WHERE maquinaria = 'EXC-01'") or {}
    check("y = latitud", t.get("lat"), 13.921)
    check("x = longitud", t.get("lon"), -89.845)
    check("vehStat -> estado_vehiculo", t.get("estado_vehiculo"), 1)
    check("epoch -> coms_age en segundos", round((t.get("coms_age_s") or 0) / 3600), 2)
    check("mas de una hora sin reportar -> Sin conexion", t.get("conexion"), "Sin conexion")
    check("eventDescription -> ultimo evento", t.get("ultimo_evento"), "ignicion apagada")
    check("ignOnHrs es ACUMULADO: la 1a lectura es linea base",
          t.get("horometro_base"), 4525.5)
    check("y por lo tanto 0 horas medidas, no 4525", t.get("ign_on_time_s"), 0)

    print("\n== segunda sincronizacion: 3 h de ignicion despues ==")
    FLOTA_FALSA[0]["ignOnHrs"] = 4528.5
    startrack.sincronizar()
    t = q1("SELECT * FROM ps_tareas WHERE maquinaria = 'EXC-01'") or {}
    check("mide la diferencia contra la base", t.get("ign_on_time_s"), 3 * 3600)
    check("la base NO se mueve", t.get("horometro_base"), 4525.5)

    print("\n== un vehiculo que no cruza ==")
    FLOTA_FALSA.append({"vehId": 999, "vehDescr": "NO-EXISTE-99",
                        "epoch": str(HACE_2H), "x": "0", "y": "0"})
    r = startrack.sincronizar()
    check("no rompe nada y sigue actualizando lo que si cruza",
          r.get("actualizadas"), 1)

    print("\n== sin credenciales ==")
    for v in ("STARTRACK_HOST", "STARTRACK_API_KEY", "STARTRACK_PASSWORD"):
        os.environ.pop(v, None)
    r = startrack.sincronizar()
    check("lo dice y no revienta", r.get("origen"), "semilla")

    print()
    if fallos:
        print(f"\033[31m{len(fallos)} FALLAN: {fallos}\033[0m")
        return 1
    print("\033[32mConector de Startrack: mapeo de campos verificado.\033[0m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
