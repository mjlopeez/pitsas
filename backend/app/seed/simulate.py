"""
Emisor continuo de telemetria sintetica, en las cuatro formas propietarias.

Da vida al mapa durante la demo: sin esto el Command Center se ve estatico y
el jurado no sabe si esta viendo un sistema o una captura de pantalla.

Uso:  python -m app.seed.simulate --intervalo 3
"""
from __future__ import annotations

import argparse
import random
import time
from datetime import datetime, timezone

import httpx

BASE = "http://127.0.0.1:8000"


def payload_cat(a: dict, rnd: random.Random) -> dict:
    return {
        "EquipmentHeader": {"OEMName": "Caterpillar", "Model": a["model"],
                            "SerialNumber": a["asset_identifier"]},
        "SnapshotTime": datetime.now(timezone.utc).isoformat(),
        "Location": {"Latitude": a["lat"] + rnd.uniform(-0.0004, 0.0004),
                     "Longitude": a["lon"] + rnd.uniform(-0.0004, 0.0004)},
        "CumulativeOperatingHours": {"Hour": round((a["operating_hours"] or 0) + 0.05, 2)},
        "CumulativeFuelUsed": {"FuelConsumed": round((a["cumulative_fuel"] or 0) + 0.4, 1),
                               "FuelUnits": "gal"},
        "EngineStatus": {"Running": a["engine_state"] != "OFF",
                         "Idle": a["engine_state"] == "IDLE"},
        "FaultCodes": [],
    }


def payload_komatsu(a: dict, rnd: random.Random) -> dict:
    return {
        "machine": {"id": a["asset_identifier"], "type": a["kind"]},
        "ts": int(time.time()),
        "smr": round((a["operating_hours"] or 0) + 0.05, 2),
        "fuel_l": round((a["cumulative_fuel"] or 0) * 3.785 + 1.5, 1),
        "gps": {"lat": a["lat"] + rnd.uniform(-0.0004, 0.0004),
                "lng": a["lon"] + rnd.uniform(-0.0004, 0.0004)},
        "engine": {"ON": "RUNNING", "IDLE": "IDLING", "OFF": "STOPPED"}.get(
            a["engine_state"] or "OFF", "STOPPED"),
        "alarms": [],
    }


def payload_volvo(a: dict, rnd: random.Random) -> dict:
    return {
        "equipmentId": a["asset_identifier"],
        "snapshotTime": datetime.now(timezone.utc).isoformat(),
        "hourMeter": {"value": round((a["operating_hours"] or 0) + 0.05, 2), "unit": "h"},
        "fuelUsed": {"value": round((a["cumulative_fuel"] or 0) * 3.785 + 1.5, 1), "unit": "l"},
        "position": {"latitude": a["lat"] + rnd.uniform(-0.0004, 0.0004),
                     "longitude": a["lon"] + rnd.uniform(-0.0004, 0.0004)},
        "engineRunning": a["engine_state"] != "OFF",
        "engineIdle": a["engine_state"] == "IDLE",
        "activeCodes": [],
    }


def payload_j1939(a: dict, rnd: random.Random) -> dict:
    encendido = a["engine_state"] != "OFF"
    return {
        "device_id": f"ESP32-{abs(hash(a['asset_identifier'])) % 9999:04d}",
        "vin": a["asset_identifier"],
        "epoch": int(time.time()),
        "spn": {"247": round((a["operating_hours"] or 0) + 0.05, 2),
                "250": round((a["cumulative_fuel"] or 0) * 3.785 + 1.5, 1)},
        "fuel_unit": "l",
        "gnss": {"lat": a["lat"] + rnd.uniform(-0.0004, 0.0004),
                 "lon": a["lon"] + rnd.uniform(-0.0004, 0.0004)},
        "rpm": 0 if not encendido else (rnd.randint(650, 820)
                                        if a["engine_state"] == "IDLE"
                                        else rnd.randint(1300, 1900)),
        "load_pct": 0 if not encendido else (rnd.randint(0, 15)
                                             if a["engine_state"] == "IDLE"
                                             else rnd.randint(45, 90)),
        "dm1": [],
    }


VENDOR = {"Caterpillar": ("cat", payload_cat), "Komatsu": ("komatsu", payload_komatsu),
          "Volvo": ("volvo", payload_volvo), "Mack": ("j1939", payload_j1939)}


def main() -> None:
    ap = argparse.ArgumentParser(description="Emisor de telemetria sintetica del Hub")
    ap.add_argument("--intervalo", type=float, default=3.0, help="segundos entre lotes")
    ap.add_argument("--lote", type=int, default=6, help="activos por lote")
    ap.add_argument("--base", default=BASE)
    args = ap.parse_args()

    rnd = random.Random()
    with httpx.Client(base_url=args.base, timeout=10.0) as c:
        activos = c.get("/api/assets").json()
        if not activos:
            print("No hay flota sembrada. Corre primero: POST /admin/seed")
            return
        print(f"Emitiendo telemetria de {len(activos)} activos. Ctrl-C para parar.")
        while True:
            for a in rnd.sample(activos, min(args.lote, len(activos))):
                if a.get("lat") is None:
                    continue
                # Un activo retrofit siempre entra por J1939, sin importar la marca.
                if a.get("telemetry") == "retrofit":
                    vendor, fn = "j1939", payload_j1939
                else:
                    vendor, fn = VENDOR.get(a.get("make"), ("j1939", payload_j1939))
                try:
                    r = c.post(f"/ingest/telemetry/{vendor}", json=fn(a, rnd))
                    if r.status_code >= 400:
                        print(f"  {a['asset_identifier']} {vendor} -> {r.status_code}")
                except Exception as exc:  # noqa: BLE001
                    print(f"  error: {exc}")
            time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
