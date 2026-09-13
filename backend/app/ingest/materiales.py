"""
Ingesta de las unidades de negocio aguas arriba de la obra.

ECON esta integrada verticalmente: la cantera, las cuatro plantas de concreto,
las plantas de asfalto y el laboratorio son fuentes de datos tan legitimas como
la telemetria de una excavadora, y hoy viven en silos distintos.

Dos puertas, las dos desembocan en el mismo orchestrator.procesar():

  POST /ingest/planta   la planta dosifica: arranca el reloj de la carga
  POST /ingest/lab      el laboratorio dictamina: puede invalidar una entrega
                        que ya va en camino

Duenio: Wilbert
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..canonical import CanonicalEvent, Carga, Source, TipoCarga
from ..cargas import estado_carga, nuevo_lote
from ..db import q, q1
from ..orchestrator import procesar

router = APIRouter(prefix="/ingest", tags=["materiales"])


class Dosificacion(BaseModel):
    """Lo que manda el sistema de dosificacion de la planta."""

    tipo: TipoCarga
    planta_origen: str
    obra_destino: str
    asset_identifier: str = Field(min_length=1)   # el mixer o el distribuidor
    cantidad: float | None = None
    unidad: str | None = None
    diseno: str | None = None
    temperatura_c: float | None = None
    lote: str | None = None
    dosificado_en: datetime | None = None


class Ensayo(BaseModel):
    """Lo que manda el laboratorio. Es el unico que puede dictaminar."""

    lote: str
    cumple: bool
    ensayo: str | None = None          # "compresion a 7 dias: 231 kg/cm2"
    asset_identifier: str | None = None


@router.post("/planta")
def dosificar(d: Dosificacion) -> dict[str, Any]:
    """
    La planta dosifica y arranca el reloj de vida de la carga.

    Este endpoint es el que hace que el Hub deje de ser un tablero de maquinaria
    y pase a coordinar materiales: desde aqui el concreto tiene una hora de
    muerte, y todo lo de abajo (despacho, veda del VMT, cuadrilla en obra)
    queda amarrado a ella.
    """
    if not q1("SELECT 1 FROM projects WHERE project_id = ?", (d.planta_origen,)):
        raise HTTPException(status_code=404, detail=f"planta {d.planta_origen} no encontrada")
    if not q1("SELECT 1 FROM projects WHERE project_id = ?", (d.obra_destino,)):
        raise HTTPException(status_code=404, detail=f"obra {d.obra_destino} no encontrada")

    ahora = datetime.now(timezone.utc)
    fuente = (Source.PLANTA_ASFALTO if d.tipo == TipoCarga.ASFALTO
              else Source.PLANTA_CONCRETO)
    lote = d.lote or nuevo_lote(d.tipo, ahora)

    ev = CanonicalEvent(
        asset_identifier=d.asset_identifier,
        event_timestamp=ahora,
        source=fuente,
        assigned_project=d.planta_origen,
        carga=Carga(
            tipo=d.tipo,
            cantidad=d.cantidad,
            unidad=d.unidad or ("m3" if d.tipo == TipoCarga.CONCRETO else "ton"),
            dosificado_en=d.dosificado_en or ahora,
            temperatura_c=d.temperatura_c,
            diseno=d.diseno,
            planta_origen=d.planta_origen,
            obra_destino=d.obra_destino,
            lote=lote,
        ),
        note=f"Dosificacion {d.tipo.value} lote {lote}",
        reported_by=d.planta_origen,
    )
    ev.with_provenance()

    resultado = procesar(ev, idempotency_key=f"dosif:{lote}")
    return {"resultado": resultado, "carga": estado_carga(lote)}


@router.post("/lab")
def dictaminar(e: Ensayo) -> dict[str, Any]:
    """
    Resultado de ensayo sobre un lote.

    El laboratorio es duenio EXCLUSIVO de `cumple_especificacion`: ni la planta
    ni la obra pueden escribirlo (ver canonical.EXCLUSIVOS). Si el lote no
    cumple y la carga ya salio, el Hub la retiene y abre ticket critico — es el
    caso que obliga a cruzar silos antes de que el material se coloque.
    """
    fila = q1("SELECT * FROM cargas WHERE lote = ?", (e.lote,))
    if not fila:
        raise HTTPException(status_code=404, detail=f"lote {e.lote} no encontrado")

    ahora = datetime.now(timezone.utc)
    from ..db import x

    if e.ensayo:
        x("UPDATE cargas SET ensayo = ? WHERE lote = ?", (e.ensayo, e.lote))

    ev = CanonicalEvent(
        asset_identifier=e.asset_identifier or fila.get("asset_identifier") or e.lote,
        event_timestamp=ahora,
        source=Source.LAB,
        carga=Carga(
            tipo=TipoCarga(fila["tipo"]),
            lote=e.lote,
            cumple_especificacion=e.cumple,
        ),
        note=f"Ensayo lote {e.lote}: {'cumple' if e.cumple else 'NO CUMPLE'}"
             + (f" ({e.ensayo})" if e.ensayo else ""),
        reported_by="laboratorio",
    )
    ev.with_provenance()

    resultado = procesar(ev, idempotency_key=f"lab:{e.lote}:{e.cumple}")
    return {"resultado": resultado, "carga": estado_carga(e.lote)}


@router.get("/cargas")
def listar_cargas(estado: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM cargas"
    params: tuple = ()
    if estado:
        sql += " WHERE estado = ?"
        params = (estado,)
    sql += " ORDER BY created_at DESC LIMIT 60"

    from ..rules import carga as r_carga

    ahora = datetime.now(timezone.utc)
    filas = q(sql, params)
    for f in filas:
        if f.get("cumple_especificacion") is not None:
            f["cumple_especificacion"] = bool(f["cumple_especificacion"])
        f["minutos_restantes"] = None
        if f.get("dosificado_en"):
            try:
                t0 = datetime.fromisoformat(f["dosificado_en"])
                if t0.tzinfo is None:
                    t0 = t0.replace(tzinfo=timezone.utc)
                f["minutos_restantes"] = r_carga.minutos_restantes(t0, f["tipo"], ahora)
                if f["minutos_restantes"] is not None:
                    f["minutos_restantes"] = round(f["minutos_restantes"], 1)
            except ValueError:
                pass
    return filas
