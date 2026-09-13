"""
API de la integracion Prisma + Startrack.

Es la integracion que se demuestra en vivo: solo lectura y correlacion, sin
tocar el pipeline de eventos del resto del Hub — Prisma y Startrack son
sistemas de registro externos, no fuentes de telemetria.

Duenio: Wilbert
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..correlacion import (AREAS, CATALOGO_ESTADOS_HUB, MAPEO_CAMPOS,
                           listar_maquinas, vista_unificada)
from ..pea import construir as pea_construir
from ..pea import recomputar as pea_recomputar
from ..pea import registrar as pea_registrar
from ..prisma import disponible as prisma_disponible
from ..sangrado import por_area
from ..startrack import disponible as startrack_disponible
from ..db import q

router = APIRouter(prefix="/api/ps", tags=["prisma-startrack"])


@router.get("/maquinas")
def maquinas() -> list[dict[str, Any]]:
    return listar_maquinas()


@router.get("/vista-unificada/{maquinaria}")
def vista(maquinaria: str) -> list[dict[str, Any]]:
    ops = vista_unificada(maquinaria)
    if not ops:
        raise HTTPException(
            status_code=404,
            detail=f"sin solicitudes ni tareas para la maquinaria '{maquinaria}'",
        )
    return ops


@router.get("/geocercas")
def geocercas() -> list[dict[str, Any]]:
    """Las geocercas reales del sandbox, para que el mapa tenga donde ubicar.

    Son el universo de destinos posibles: el `poi_name` de una tarea de
    Startrack apunta a uno de estos nombres.
    """
    return q("SELECT poi_id, nombre, lat, lon, radio_m, grupo"
             " FROM ps_geocercas ORDER BY nombre")


@router.get("/mapeo")
def mapeo() -> dict[str, Any]:
    """El mapeo de campos entre las dos plataformas y el catalogo de estados.

    La especificacion dice que "el mapeo entre plataformas debera ser definido
    por cada equipo": esto es esa definicion, servida como dato y no enterrada
    en un anexo, para que se pueda mostrar en pantalla durante la demo.
    """
    return {
        "campos": MAPEO_CAMPOS,
        "estados_hub": [
            {"estado": k, **v} for k, v in CATALOGO_ESTADOS_HUB.items()
        ],
        # De donde salen los datos que se estan viendo. El tablero lo muestra
        # para que nunca presentemos la semilla como si fuera el sistema real:
        # es la misma regla que no llamar hardware al simulador J1939.
        "origen": "startrack" if startrack_disponible() else "simulado",
        "origen_prisma": "prisma" if prisma_disponible() else "simulado",
    }


@router.get("/sangrado")
def sangrado(area: str | None = None) -> dict[str, Any]:
    """Donde sangra la compania, repartido entre Maquinaria, Logistica y Proyectos.

    `area` filtra a una sola para que el tablero de cada jefe cargue lo suyo.

    Toda cifra derivada trae `base_medida` (real) y `supuesto_aplicado` (lo
    que asumimos). Ver sangrado.py: la separacion no es decorativa.
    """
    if area and area.lower() not in AREAS:
        raise HTTPException(
            status_code=400,
            detail=f"area debe ser una de {list(AREAS)}")
    return por_area(area)


@router.post("/pea/{maquinaria}")
def emitir_pea(maquinaria: str, aprobado_por: str,
               proyecto_id: str | None = None) -> dict[str, Any]:
    """Sella la evidencia de una operacion. `aprobado_por` es una PERSONA.

    El Hub automatiza la evidencia, no la decision.
    """
    registro = pea_construir(maquinaria, aprobado_por, proyecto_id)
    if not registro:
        raise HTTPException(
            status_code=404,
            detail=f"no hay operacion con tarea para '{maquinaria}'")
    pea_id = pea_registrar(registro)
    return {"id": pea_id, **registro}


@router.get("/pea")
def listar_pea() -> list[dict[str, Any]]:
    return q("SELECT id, maquinaria, proyecto_id, estado_hub,"
             " horas_facturables, monto_facturable, exposicion_usd, medicion,"
             " aprobado_por, hash, created_at FROM pea_registros"
             " ORDER BY id DESC LIMIT 50")


@router.get("/pea/{pea_id}/verificar")
def verificar_pea(pea_id: int) -> dict[str, Any]:
    """Recomputa el hash desde el contenido guardado.

    Es la demostracion de que no hay que confiar en el Hub: el mismo
    contenido da el mismo hash en cualquier lenguaje.
    """
    r = pea_recomputar(pea_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"no existe el PEA {pea_id}")
    return r
