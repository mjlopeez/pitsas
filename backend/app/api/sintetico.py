"""
API de datos sinteticos — la puerta de entrada del equipo.

Para que Majo maquete contra volumen real, Josue ensaye con un inventario
que se parece al de ECON, y cualquiera reproduzca un bug con un solo numero:
el seed.

Todo lo que se genera queda marcado `sintetico = 1` y se borra con un POST.
Nunca se mezcla en silencio con lo que viene de Nexus o Startrack.

Duenio: Wilbert
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..auth import proteger

from ..db import q1
from ..seed.sintetico import estado as estado_sintetico
from ..seed.sintetico import generar as generar_sintetico
from ..seed.sintetico import limpiar as limpiar_sintetico

router = APIRouter(prefix="/api/sintetico", tags=["sinteticos"])


@router.get("/estado")
def estado() -> dict[str, Any]:
    """Cuanto hay cargado, separando lo generado de lo real."""
    return estado_sintetico()


@router.post("/generar", dependencies=[Depends(proteger)])
def generar(equipos: int = 120, seed: int = 42) -> dict[str, Any]:
    """Genera un inventario del tamanio que pidas.

    El mismo `seed` produce SIEMPRE el mismo dataset. Si reportas un bug,
    reporta el seed: con eso cualquiera lo reproduce identico.

    La proporcion de estados respeta la del Modulo 8 del manual de Nexus
    (194 disponibles, 53 en mantenimiento correctivo sobre 253), asi que el
    inventario se comporta como el de ellos aunque los datos sean generados.
    """
    if equipos < 1 or equipos > 500:
        raise HTTPException(status_code=400,
                            detail="equipos tiene que estar entre 1 y 500")
    return generar_sintetico(equipos=equipos, seed=seed)


@router.post("/limpiar", dependencies=[Depends(proteger)])
def limpiar() -> dict[str, Any]:
    """Borra SOLO lo sintetico. Las filas de la demo quedan intactas."""
    return limpiar_sintetico()


@router.get("/webhook-ejemplo/{remote_id}")
def webhook_ejemplo(remote_id: str, horometro: float | None = None) -> dict[str, Any]:
    """Un payload de webhook valido, listo para disparar.

    Sirve para probar la ruta de tiempo real sin tener Startrack enfrente:
    se copia el `payload` y se manda con POST a la `url` que viene al lado.

    Si no pasas `horometro`, se usa la ultima lectura conocida mas una hora,
    que es lo que hace que la KPI de horas medidas se mueva de verdad.
    """
    t = q1("SELECT * FROM ps_tareas WHERE remote_id = ? OR maquinaria = ?",
           (remote_id, remote_id))
    if not t:
        raise HTTPException(
            status_code=404,
            detail=f"ninguna tarea cruza con '{remote_id}'. "
                   "Prueba con GET /api/ps/maquinas para ver los disponibles.")

    if horometro is None:
        actual = t.get("horometro")
        horometro = round(float(actual) + 1.0, 2) if actual else 1000.0

    return {
        "url": "POST /webhooks/startrack/ubicaciones",
        "nota": "Formato 1 (objeto). El formato 2 es [n, [objetos]] y tambien"
                " se acepta. La PRIMERA lectura de un equipo fija la linea"
                " base del horometro; la segunda ya mide la diferencia.",
        "payload": {
            "code": 3,
            "vid": int(t.get("vehicle_id") or 0) or 1057,
            "remote_id": t.get("remote_id") or t["maquinaria"],
            "license_plate": "P-000AAA",
            "hourmeter": horometro,
            "ign_on": True,
            "veh_status": t.get("estado_vehiculo") or 0,
            "lat": t.get("lat") or 13.92,
            "lon": t.get("lon") or -89.84,
            "event_time": "2026-09-13T08:00:00-06:00",
            "placename": "Troncal del Norte, El Salvador",
            "valid_position": True,
        },
    }
