"""
Tablero de costos: el cierre de la demo y el argumento para los jueces directivos.

Los parametros vienen del modelo financiero del documento. Se calculan sobre
las alertas reales que genero el Hub durante la sesion, no sobre numeros fijos:
cuando el jurado ve el ahorro moverse porque acaba de pasar un evento, el
modelo deja de ser una diapositiva.

Duenio: Josue (numeros) / Majo (vista)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ..db import jloads, q, q1

router = APIRouter(prefix="/api", tags=["analitica"])

# ---------------------------------------------------------------------------
# Parametros del modelo financiero. CUADRAN CON EL DOCUMENTO BASE a proposito:
# si el tablero dice un numero y el pitch dice otro, el jurado caza la
# contradiccion en tres segundos y pierdes el renglon completo.
#
# Cadena del ahorro en diesel (documento):
#   100 equipos x 1 h/dia x 300 dias operativos x 1.0 gal/h = 30,000 gal
#   30,000 gal x $4.00 = $120,000/anio
# ---------------------------------------------------------------------------
PRECIO_GALON = 4.00             # galon de diesel en El Salvador
FLOTA_EQUIPOS = 100
FLOTA_TRANSPORTE = 50
HORA_RALENTI_DIA = 1.0          # hora de ralenti evitada por maquina por dia
DIAS_OPERATIVOS = 300           # dias de obra al anio, no 365
GAL_HORA_RALENTI = 1.0          # documento: rango 0.8 - 1.4, se toma el conservador
TRASLADOS_ANIO = 200
HORAS_DEMORA_EVITADA = 3.0
COSTO_HORA_DETENCION = 80.0     # cabezal + activo inmovilizado
REPARACIONES_EVITADAS = 4
COSTO_REPARACION = 15_000.0     # 4 x 15,000 = $60,000 en taller evitado
CAPEX = 45_000.0                # desarrollo + instrumentacion retrofit
OPEX_ANIO = 15_000.0            # nube + conectividad


@router.get("/analytics")
def analitica() -> dict[str, Any]:
    galones_evitados = FLOTA_EQUIPOS * HORA_RALENTI_DIA * DIAS_OPERATIVOS * GAL_HORA_RALENTI
    ahorro_diesel = galones_evitados * PRECIO_GALON
    ahorro_logistica = TRASLADOS_ANIO * HORAS_DEMORA_EVITADA * COSTO_HORA_DETENCION
    ahorro_taller = REPARACIONES_EVITADAS * COSTO_REPARACION
    beneficio = ahorro_diesel + ahorro_logistica + ahorro_taller
    neto = beneficio - OPEX_ANIO
    meses_roi = (CAPEX / (neto / 12)) if neto > 0 else None

    # --- impacto observado en esta sesion -----------------------------------
    ralenti = q("SELECT payload FROM alerts WHERE kind = 'ralenti'")
    gal_detectados = sum(jloads(r["payload"], {}).get("galones", 0) for r in ralenti)

    reprog = q1("SELECT COUNT(*) AS n FROM dispatches WHERE rescheduled = 1") or {"n": 0}
    detenciones_evitadas = reprog["n"] * HORAS_DEMORA_EVITADA * COSTO_HORA_DETENCION

    conteos = {
        r["kind"]: r["n"]
        for r in q("SELECT kind, COUNT(*) AS n FROM alerts GROUP BY kind")
    }
    eventos = q1("SELECT COUNT(*) AS n FROM events") or {"n": 0}

    return {
        "modelo_anual": {
            "galones_evitados": round(galones_evitados),
            "ahorro_diesel": round(ahorro_diesel),
            "ahorro_logistica": round(ahorro_logistica),
            "ahorro_taller": round(ahorro_taller),
            "beneficio_total": round(beneficio),
            "capex": CAPEX,
            "opex_anual": OPEX_ANIO,
            "beneficio_neto": round(neto),
            "roi_meses": round(meses_roi, 1) if meses_roi else None,
        },
        "kpis": [
            {"kpi": "Ralenti improductivo", "base": "35% – 42%", "con_hub": "15% – 18%",
             "mecanismo": "Alertas telematicas en tiempo real por WhatsApp"},
            {"kpi": "Respuesta de despacho", "base": "4 – 6 h", "con_hub": "< 45 min",
             "mecanismo": "Inventario unificado y validacion automatica de rutas"},
            {"kpi": "Desfase de facturacion", "base": "5 – 8 dias", "con_hub": "Conciliacion horaria",
             "mecanismo": "Telemetria ISO 15143-3 + validacion OCR"},
            {"kpi": "MTTR", "base": "24 – 48 h", "con_hub": "15 – 30 h (-35%)",
             "mecanismo": "Captura temprana de DTC y reserva de repuestos"},
            {"kpi": "Retenciones por veda VMT", "base": "12% – 16%", "con_hub": "< 2%",
             "mecanismo": "Programacion algoritmica de salidas del AMSS"},
        ],
        "sesion": {
            "eventos_normalizados": eventos["n"],
            "alertas_por_tipo": conteos,
            "galones_ralenti_detectados": round(gal_detectados, 1),
            "costo_ralenti_detectado": round(gal_detectados * PRECIO_GALON, 2),
            "traslados_reprogramados": reprog["n"],
            "detenciones_evitadas_usd": round(detenciones_evitadas, 2),
        },
    }
