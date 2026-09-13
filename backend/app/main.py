"""
Hub de Operaciones — Grupo ECON / Entropy Hack.

Un solo proceso a proposito. En produccion esto se parte en microservicios y
el bus pasa a Kafka; lo que NO cambia es el contrato canonico, que es la tesis
del proyecto. Ver docs/CONTRATO.md.

Arranque:  ./backend/run.sh     (o uvicorn app.main:app --reload)
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import (analytics, assets, connectors, dispatch_api,
                  prisma_startrack, sintetico, stream)
from .auth import proteger
from .db import init_db, q1
from .ingest import materiales, startrack_webhook, telemetry

app = FastAPI(
    title="Hub de Operaciones — Grupo ECON",
    description=(
        "Integrador de silos para logistica de maquinaria pesada. "
        "Normaliza telemetria OEM y retrofit CAN J1939 a un contrato "
        "canonico ISO 15143-3."
    ),
    version="0.1.0",
)

# Abierto a proposito: son 12 horas y cuatro laptops en la misma red.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry.router)
app.include_router(materiales.router)
# app.include_router(whatsapp.router) — sacado del guion, decision del equipo
# (13/09). ingest/whatsapp.py y ai/{stt,ocr,ner}.py se dejan intactos en el
# repo, sin borrar, por si se retoma. Ver tambien scripts/smoke.sh: se quito
# el bloque "minuto 1" que probaba /ingest/whatsapp/sim.
app.include_router(startrack_webhook.router)
app.include_router(assets.router)
app.include_router(stream.router)
app.include_router(connectors.router)
app.include_router(dispatch_api.router)
app.include_router(analytics.router)
app.include_router(prisma_startrack.router)
app.include_router(sintetico.router)


@app.on_event("startup")
def arrancar() -> None:
    init_db()
    vacio = (q1("SELECT COUNT(*) AS n FROM assets") or {"n": 0})["n"] == 0
    if vacio and os.getenv("HUB_AUTOSEED", "1") == "1":
        from .seed.fleet import sembrar

        r = sembrar()
        print(f"[hub] flota sembrada: {r}")

    # Prisma + Startrack: los tres casos oficiales del sandbox. Semilla propia,
    # independiente de la flota.
    vacio_ps = (q1("SELECT COUNT(*) AS n FROM ps_solicitudes") or {"n": 0})["n"] == 0
    if vacio_ps and os.getenv("HUB_AUTOSEED", "1") == "1":
        from .seed.prisma_startrack import sembrar_casos

        r = sembrar_casos()
        print(f"[hub] Prisma+Startrack sembrado: {r}")
    print("[hub] listo en http://127.0.0.1:8000  (docs en /docs)")


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "activos": (q1("SELECT COUNT(*) AS n FROM assets") or {"n": 0})["n"],
        "eventos": (q1("SELECT COUNT(*) AS n FROM events") or {"n": 0})["n"],
        "alertas_abiertas": (q1("SELECT COUNT(*) AS n FROM alerts WHERE status='abierta'")
                             or {"n": 0})["n"],
    }


@app.post("/admin/seed", dependencies=[Depends(proteger)])
def resembrar(equipos: int = 100, transporte: int = 50) -> dict[str, int]:
    from .seed.fleet import sembrar

    return sembrar(equipos, transporte)


@app.post("/admin/seed-ps", dependencies=[Depends(proteger)])
def resembrar_ps() -> dict[str, int]:
    from .seed.prisma_startrack import sembrar_casos

    return sembrar_casos()


@app.post("/admin/sync-prisma", dependencies=[Depends(proteger)])
def sync_prisma() -> dict[str, object]:
    """Trae solicitudes reales del sandbox de Prisma. A mano, como Startrack."""
    from .prisma import sincronizar

    return sincronizar()


@app.post("/admin/sync-startrack", dependencies=[Depends(proteger)])
def sync_startrack() -> dict[str, object]:
    """Refresca ps_tareas contra la API real de Startrack.

    A MANO, nunca en el arranque: una llamada de red colgada en startup mata
    la demo entera. Sin credenciales responde que no esta disponible y la
    vista unificada sigue sirviendo la semilla.
    """
    from .startrack import sincronizar

    return sincronizar()


@app.post("/admin/base-diesel", dependencies=[Depends(proteger)])
def base_diesel(asset: str, consumido: float) -> dict[str, object]:
    """
    Ayuda de prueba: fija la base del ciclo de abastecimiento para que la
    conciliacion de diesel de un resultado determinista en scripts/smoke.sh.
    No se usa en la demo.
    """
    from .db import q1, x

    a = q1("SELECT cumulative_fuel FROM assets WHERE asset_identifier = ?", (asset,))
    if not a:
        return {"error": "activo no encontrado"}
    base = (a["cumulative_fuel"] or 0) - consumido
    x("UPDATE assets SET last_refuel_fuel = ? WHERE asset_identifier = ?", (base, asset))
    return {"asset": asset, "last_refuel_fuel": round(base, 1), "consumido": consumido}


@app.post("/admin/vencer-servicio", dependencies=[Depends(proteger)])
def vencer_servicio(asset: str) -> dict[str, object]:
    """Ayuda de prueba: deja el servicio vencido. No se usa en la demo."""
    from .db import q1, x

    a = q1("SELECT operating_hours, service_every_h FROM assets WHERE asset_identifier = ?",
           (asset,))
    if not a:
        return {"error": "activo no encontrado"}
    nuevo = (a["operating_hours"] or 0) - (a["service_every_h"] or 250) - 5
    x("UPDATE assets SET last_service_h = ?, state = 'OPERANDO' WHERE asset_identifier = ?",
      (nuevo, asset))
    return {"asset": asset, "last_service_h": round(nuevo, 1)}


@app.post("/admin/reset", dependencies=[Depends(proteger)])
def reset() -> dict[str, str]:
    """Borra eventos, alertas y traslados pero deja la flota. Util entre ensayos."""
    from .db import x

    for t in ("events", "alerts", "dispatches", "connector_stats"):
        x(f"DELETE FROM {t}")
    # Los estados derivados tambien se limpian, si no un ensayo arranca con la
    # flota en el estado que dejo el anterior.
    x("UPDATE assets SET state = 'DISPONIBLE', idle_since = NULL, provenance = '{}'")
    return {"status": "limpio"}


# La PWA de campo se sirve desde el mismo proceso: el supervisor abre una URL
# en el celular, sin tienda de aplicaciones y sin instalar nada.
PWA = Path(__file__).resolve().parents[2] / "field-pwa"
if PWA.is_dir():
    app.mount("/campo", StaticFiles(directory=str(PWA), html=True), name="campo")


# El Command Center compilado (frontend/dist) si existe; si no, se usa el dev
# server de Vite en el puerto 5173.
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.is_dir():
    # OJO: Vite compila el index.html pidiendo sus assets en la RAIZ
    # (<script src="/assets/index-XXX.js">). Si solo se monta /app, la pagina
    # carga y despues se cae con 404 en el JS y el CSS: pantalla en blanco.
    # Nadie lo nota corriendo `npm run dev`, y desplegar es exactamente correr
    # sin el dev server. Por eso /assets va montado aparte, en la raiz.
    ASSETS = DIST / "assets"
    if ASSETS.is_dir():
        app.mount("/assets", StaticFiles(directory=str(ASSETS)), name="assets")

    app.mount("/app", StaticFiles(directory=str(DIST), html=True), name="app")

    @app.get("/")
    def raiz() -> FileResponse:
        return FileResponse(str(DIST / "index.html"))
else:
    @app.get("/")
    def raiz() -> dict[str, str]:
        return {
            "hub": "Grupo ECON",
            "command_center": "http://localhost:5173 (npm run dev en frontend/)",
            "pwa_campo": "/campo",
            "docs": "/docs",
        }
