"""
Despacho de traslados: valida aptitud tecnica, calcula ETA y aplica la veda del VMT.

Es el minuto 3 de la demo. Duenio: Wilbert
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..canonical import AssetState, TipoCarga
from ..db import jloads, q, q1, x
from ..dispatch.vmt import CORREDORES, SV, planificar
from ..events import publish
from ..rules import carga as r_carga
from ..rules.maintenance import revisar as revisar_mant

router = APIRouter(prefix="/api/dispatch", tags=["despacho"])

VEL_CAMA_BAJA_KMH = 35.0     # 60 t en carretera salvadorena, con pendientes
MIN_CARGA = 45               # acondicionamiento y amarre en plantel

# Un mixer no es una cama baja: va mas rapido y carga en minutos, no en una hora.
VEL_MIXER_KMH = 45.0
MIN_CARGA_MATERIAL = 10      # dosificar y salir de la planta
MIN_DESCARGA = 15            # posicionar y bombear en el frente


class Solicitud(BaseModel):
    asset_identifier: str
    dest_project: str
    corredor: str = "panamericana_poniente"
    truck: str | None = None
    listo_desde: datetime | None = None   # por defecto: ahora


def _km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@router.get("/corridors")
def corredores() -> list[dict[str, Any]]:
    return [{
        "corredor_id": c.corredor_id,
        "nombre": c.nombre,
        "penalidad_min": c.penalidad_min,
        "vedas": [{"desde": v.desde.strftime("%H:%M"),
                   "hasta": v.hasta.strftime("%H:%M"),
                   "etiqueta": v.etiqueta,
                   "dias": list(v.dias)} for v in c.vedas],
    } for c in CORREDORES.values()]


@router.get("")
def listar() -> list[dict[str, Any]]:
    return q("SELECT * FROM dispatches ORDER BY id DESC LIMIT 50")


@router.post("")
def crear(s: Solicitud) -> dict[str, Any]:
    a = q1("SELECT * FROM assets WHERE asset_identifier = ?", (s.asset_identifier,))
    if not a:
        raise HTTPException(status_code=404, detail="activo no encontrado")
    dest = q1("SELECT * FROM projects WHERE project_id = ?", (s.dest_project,))
    if not dest:
        raise HTTPException(status_code=404, detail="obra destino no encontrada")

    # --- 1. aptitud tecnica: no se despacha una maquina que va a fallar en ruta
    bloqueos: list[str] = []
    fallas = q1(
        "SELECT COUNT(*) AS n FROM alerts WHERE asset_identifier = ?"
        " AND kind = 'falla' AND status = 'abierta'", (s.asset_identifier,))
    if (fallas or {}).get("n"):
        bloqueos.append(f"{fallas['n']} codigo(s) de falla abiertos")
    m = revisar_mant(a)
    if m and m["payload"].get("vencido"):
        bloqueos.append(f"servicio vencido ({m['payload']['horas_desde_servicio']} h)")
    if a.get("state") == AssetState.EN_TRASLADO.value:
        bloqueos.append("ya esta en traslado")

    # --- 2. ETA
    origen = None
    if a.get("lat") is not None and a.get("lon") is not None:
        origen = (a["lat"], a["lon"])
    km = _km(origen[0], origen[1], dest["lat"], dest["lon"]) if origen else 40.0
    eta = int(MIN_CARGA + (km / VEL_CAMA_BAJA_KMH) * 60)

    # --- 3. veda del VMT
    listo = s.listo_desde or datetime.now(timezone.utc)
    if listo.tzinfo is None:
        listo = listo.replace(tzinfo=SV)
    plan = planificar(listo, eta, s.corredor)

    # Alternativa sin desvio, para mostrarle al jurado las dos opciones.
    alterna = planificar(listo, eta, s.corredor, permitir_desvio=False)

    did = x(
        "INSERT INTO dispatches (asset_identifier, origin_project, dest_project, truck,"
        " corridor, requested_at, eta_minutes, departure_at, rescheduled, reason, status)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (s.asset_identifier, a.get("assigned_project"), s.dest_project,
         s.truck or "Mack GR64BTX 60 t", plan.corredor, listo.isoformat(),
         plan.eta_minutos, plan.salida.isoformat(), 1 if plan.reprogramado else 0,
         plan.razon, "bloqueado" if bloqueos else "propuesto"),
    )

    if plan.reprogramado:
        x("INSERT INTO alerts (asset_identifier, kind, severity, title, detail, payload)"
          " VALUES (?,?,?,?,?,?)",
          (s.asset_identifier, "despacho", "alta",
           f"Traslado reprogramado: {plan.salida.astimezone(SV).strftime('%H:%M')}",
           plan.razon, json.dumps(plan.to_dict(), ensure_ascii=False)))

    resp = {
        "dispatch_id": did,
        "asset_identifier": s.asset_identifier,
        "destino": dest["name"],
        "km": round(km, 1),
        "aptitud": {"apto": not bloqueos, "bloqueos": bloqueos},
        "plan": plan.to_dict(),
        "alternativa_sin_desvio": alterna.to_dict(),
        "mensaje_whatsapp": (
            f"Hoja de ruta {did}: {s.asset_identifier} -> {dest['name']}. "
            f"Salida {plan.salida.astimezone(SV).strftime('%H:%M')} por {plan.corredor_nombre}. "
            f"ETA {plan.eta_minutos} min. {plan.razon}"
        ),
    }
    publish("dispatch", resp)
    return resp


@router.post("/{dispatch_id}/confirmar")
def confirmar(dispatch_id: int) -> dict[str, Any]:
    d = q1("SELECT * FROM dispatches WHERE id = ?", (dispatch_id,))
    if not d:
        raise HTTPException(status_code=404, detail="traslado no encontrado")
    x("UPDATE dispatches SET status = 'confirmado' WHERE id = ?", (dispatch_id,))
    x("UPDATE assets SET state = ? WHERE asset_identifier = ?",
      (AssetState.EN_TRASLADO.value, d["asset_identifier"]))
    publish("asset", {"asset_identifier": d["asset_identifier"],
                      "state": AssetState.EN_TRASLADO.value})
    return {"status": "confirmado", "dispatch_id": dispatch_id}


# ---------------------------------------------------------------------------
# DESPACHO DE MATERIAL PERECEDERO
#
# Es lo que separa a este Hub de un tablero de maquinaria. Un traslado de
# material no se planifica igual que un traslado de una excavadora: la carga
# tiene hora de muerte. Y cuando no alcanza por ninguna ruta, la respuesta
# correcta no es reprogramar el camion — es decirle a la planta que NO
# DOSIFIQUE todavia. Esa decision cruza planta, logistica y obra de un golpe.
# ---------------------------------------------------------------------------


class SolicitudCarga(BaseModel):
    tipo: TipoCarga
    planta_origen: str
    obra_destino: str
    asset_identifier: str | None = None      # el mixer asignado
    cantidad: float | None = None
    diseno: str | None = None
    corredor: str = "panamericana_poniente"
    # Si viene, la carga YA esta dosificada y el reloj corre. Si no, todavia se
    # puede decidir CUANDO dosificar, que es la salida mas valiosa.
    dosificado_en: datetime | None = None
    # Momento desde el que el camion puede salir. Por defecto ahora. Igual que
    # en el despacho de maquinaria, se puede fijar para ensayar y para las
    # pruebas: la veda del VMT corre de lunes a viernes.
    listo_desde: datetime | None = None


def _nodo(pid: str) -> dict[str, Any]:
    n = q1("SELECT * FROM projects WHERE project_id = ?", (pid,))
    if not n:
        raise HTTPException(status_code=404, detail=f"nodo {pid} no encontrado")
    return n


def _eta_material(origen: dict, destino: dict) -> tuple[float, int]:
    km = _km(origen["lat"], origen["lon"], destino["lat"], destino["lon"])
    eta = int(MIN_CARGA_MATERIAL + (km / VEL_MIXER_KMH) * 60 + MIN_DESCARGA)
    return round(km, 1), eta


@router.post("/carga")
def despachar_carga(s: SolicitudCarga) -> dict[str, Any]:
    """Tres salidas: autoriza, reruta, o manda a la planta a esperar."""
    planta = _nodo(s.planta_origen)
    obra = _nodo(s.obra_destino)
    km, eta = _eta_material(planta, obra)

    vida = r_carga.vida_minutos(s.tipo)
    ahora = s.listo_desde or datetime.now(timezone.utc)
    if ahora.tzinfo is None:
        ahora = ahora.replace(tzinfo=SV)

    # El agregado no perece: es un traslado normal, manda solo la veda. Se
    # devuelve con el MISMO juego de llaves que los demas casos para que la UI
    # no tenga que ramificar.
    if vida is None:
        plan = planificar(ahora, eta, s.corredor)
        r = {
            "decision": "autoriza", "tipo": s.tipo.value,
            "planta": planta["name"], "obra": obra["name"],
            "km": km, "eta_minutos": eta,
            "vida_minutos": None, "vence_a_las": None, "holgura_minutos": None,
            "plan": plan.to_dict(),
            "mensaje": ("El agregado basaltico no perece: aqui manda solo la "
                        "restriccion horaria del VMT."),
        }
        publish("dispatch_carga", r)
        return r

    ya_dosificada = s.dosificado_en is not None
    t0 = s.dosificado_en or ahora
    if t0.tzinfo is None:
        t0 = t0.replace(tzinfo=SV)
    limite = t0 + timedelta(minutes=vida)

    directo = planificar(ahora, eta, s.corredor, permitir_desvio=False)
    desvio = planificar(ahora, eta, s.corredor, permitir_desvio=True)

    def _resp(decision: str, plan, mensaje: str, **extra) -> dict[str, Any]:
        holgura = (limite - plan.llegada).total_seconds() / 60.0 if plan else None
        r = {
            "decision": decision,
            "tipo": s.tipo.value,
            "lote_previsto": None if ya_dosificada else "se asigna al dosificar",
            "planta": planta["name"],
            "obra": obra["name"],
            "km": km,
            "eta_minutos": eta,
            "vida_minutos": vida,
            "vence_a_las": limite.astimezone(SV).strftime("%H:%M"),
            "holgura_minutos": round(holgura, 1) if holgura is not None else None,
            "plan": plan.to_dict() if plan else None,
            "mensaje": mensaje,
            **extra,
        }
        publish("dispatch_carga", r)
        return r

    # --- 1. llega por la ruta directa ---------------------------------------
    if not directo.reprogramado and directo.llegada <= limite:
        return _resp(
            "autoriza", directo,
            f"Llega con {(limite - directo.llegada).total_seconds() / 60:.0f} min "
            f"de holgura sobre los {vida} min de vida. Sale ya.",
        )

    # --- 2. no llega directo pero si por el desvio --------------------------
    if desvio.corredor == "bypass_quezaltepeque" and desvio.llegada <= limite:
        return _resp(
            "reruta", desvio,
            f"Por {CORREDORES[s.corredor].nombre} el trayecto cae en la veda y la "
            f"carga vence antes de llegar. Por el desvio de Quezaltepeque llega "
            f"con {(limite - desvio.llegada).total_seconds() / 60:.0f} min de "
            "holgura. Se reruta y se avisa al motorista.",
            veda_evitada=desvio.veda_evitada,
        )

    # --- 3. no llega por ninguna ruta ---------------------------------------
    if ya_dosificada:
        # Demasiado tarde: el reloj ya corria. Se salva redestinando o se pierde.
        alternativas = _obras_alcanzables(planta, ahora, limite, s.corredor)
        return _resp(
            "carga_en_riesgo", desvio,
            f"El lote ya esta dosificado y no alcanza {obra['name']} por ninguna "
            f"ruta antes de las {limite.astimezone(SV).strftime('%H:%M')}. "
            "Redestinar a un frente mas cercano o descartar y re-dosificar.",
            redestinos=alternativas,
        )

    # La salida que ningun tablero da: no reprogramar el camion, reprogramar la
    # DOSIFICACION. La planta espera; el material no se fabrica para morir en
    # la carretera.
    if eta > vida:
        cercanas = _plantas_alternativas(obra, s.tipo, vida)
        return _resp(
            "fuera_de_alcance", None,
            f"{obra['name']} esta a {eta} min de {planta['name']}, mas que los "
            f"{vida} min de vida del {s.tipo.value.lower()}. Esta obra no se "
            f"puede servir desde esta planta con este diseno.",
            plantas_alternativas=cercanas,
        )

    dosificar_a_las = directo.salida
    return _resp(
        "no_dosificar", directo,
        f"NO DOSIFICAR todavia. Si se dosifica ahora, el trayecto cae en la veda "
        f"del VMT y la carga vence en la carretera. Dosificar a las "
        f"{dosificar_a_las.astimezone(SV).strftime('%H:%M')}, salir de inmediato y "
        f"llegar a las {directo.llegada.astimezone(SV).strftime('%H:%M')}. "
        "Avisar a la planta, al motorista y al residente de obra.",
        dosificar_a_las=dosificar_a_las.astimezone(SV).strftime("%H:%M"),
        cuadrilla_en_obra_a_las=(
            (directo.llegada - timedelta(minutes=MIN_DESCARGA))
            .astimezone(SV).strftime("%H:%M")
        ),
    )


def _obras_alcanzables(planta: dict, ahora, limite, corredor: str) -> list[dict]:
    """Frentes de obra a los que la carga todavia llega en pie."""
    out = []
    for n in q("SELECT * FROM projects WHERE kind IN ('obra','aeropuerto')"):
        km, eta = _eta_material(planta, n)
        p = planificar(ahora, eta, corredor)
        if p.llegada <= limite:
            out.append({"project_id": n["project_id"], "name": n["name"],
                        "km": km, "eta_minutos": eta,
                        "llega": p.llegada.astimezone(SV).strftime("%H:%M")})
    return sorted(out, key=lambda o: o["eta_minutos"])[:3]


def _plantas_alternativas(obra: dict, tipo: TipoCarga, vida: int) -> list[dict]:
    """Plantas desde las que si se alcanza la obra dentro de la vida del material."""
    kinds = (("planta_asfalto",) if tipo == TipoCarga.ASFALTO
             else ("planta_concreto",))
    out = []
    for n in q(f"SELECT * FROM projects WHERE kind IN ({','.join('?' * len(kinds))})", kinds):
        km, eta = _eta_material(n, obra)
        if eta <= vida:
            out.append({"project_id": n["project_id"], "name": n["name"],
                        "km": km, "eta_minutos": eta})
    return sorted(out, key=lambda o: o["eta_minutos"])[:3]
