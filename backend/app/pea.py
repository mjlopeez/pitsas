"""
PEA — Protocolo de Ejecucion Automatizada.

Un registro PEA es la evidencia de que una jornada de maquinaria ocurrio de
verdad, armada cruzando las DOS plataformas y sellada con un hash
determinista. Responde la pregunta que hoy nadie puede contestar sin abrir
tres sistemas y discutir por telefono: *que se trabajo, quien lo aprobo, y
con que respaldo*.

No hay cadena de bloques, y es a proposito. Lo que da valor no es el bloque:
es que la evidencia sea RECOMPUTABLE. Cualquiera con acceso de lectura a
Nexus y a Startrack puede reconstruir el mismo registro y obtener el mismo
hash. Verificar no exige confiar en el Hub — exige leer los sistemas que
ECON ya tiene. Para ellos eso es mas fuerte que una cadena, porque la fuente
de verdad se queda donde siempre estuvo.

Y no automatiza la decision, automatiza la evidencia que la decision
necesita: `aprobado_por` es una persona, siempre.

Dos montos distintos que NO hay que confundir nunca:

  monto_facturable   lo que Nexus cobra: max(horas reales, minimo) x tarifa.
  exposicion_usd     lo que se cobra SIN respaldo de operacion medida.

En un equipo sano el primero es alto y el segundo casi cero. Si los dos son
iguales, es que no hay medicion — y eso el registro lo dice con todas sus
letras en vez de dejarlo a la interpretacion.

Duenio: Wilbert
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .correlacion import exposicion, vista_unificada
from .db import q1, x

ESQUEMA = "pea/v1"


def _canonico(obj: dict[str, Any]) -> bytes:
    """Serializacion canonica: llaves ordenadas, sin espacios.

    Es lo que hace el hash reproducible en cualquier lenguaje. Si esto cambia,
    todos los hashes emitidos dejan de verificar.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sellar(registro: dict[str, Any]) -> str:
    """SHA-256 sobre la forma canonica. El campo `hash` no entra en el hash."""
    sin_sello = {k: v for k, v in registro.items() if k != "hash"}
    return "sha256:" + hashlib.sha256(_canonico(sin_sello)).hexdigest()


def verificar(registro: dict[str, Any]) -> bool:
    return bool(registro.get("hash")) and sellar(registro) == registro["hash"]


def construir(maquinaria: str, aprobado_por: str,
              proyecto_id: str | None = None) -> dict[str, Any] | None:
    """Arma el registro desde el estado actual de las dos plataformas.

    None si no hay una operacion que respaldar.
    """
    ops = vista_unificada(maquinaria)
    if proyecto_id:
        ops = [o for o in ops if o["proyecto_id"] == proyecto_id]
    ops = [o for o in ops if o.get("tarea")]
    if not ops:
        return None

    op = ops[0]
    s, t = op["solicitud"], op["tarea"]
    exp = op.get("exposicion") or exposicion(s, t) or {}

    horas_min = s.get("horas_minimas") or 0.0
    medidas = exp.get("horas_medidas")
    precio = s.get("precio_hora")
    # Regla de Nexus: se cobra el minimo de la jornada aunque se trabaje menos.
    facturables = max(float(medidas or 0.0), float(horas_min))

    registro = {
        "esquema": ESQUEMA,
        "maquinaria": maquinaria,
        "no_activo": s.get("no_activo"),
        "remote_id": t.get("remote_id"),
        "proyecto_id": op["proyecto_id"],
        "proyecto_nombre": op["proyecto_nombre"],
        "solicitud_id": s.get("solicitud_id"),
        "tarea_id": t.get("tarea_id"),
        "partida": s.get("partida_asignada"),
        "operador": s.get("operador"),
        # --- lo que dice cada plataforma, literal -------------------------
        "nexus": {
            "estado_solicitud": s.get("estado_solicitud"),
            "estado_maquinaria": s.get("estado_maquinaria"),
            "precio_hora": precio,
            "horas_minimas": horas_min,
        },
        "startrack": {
            "estado_tarea": t.get("estado_tarea"),
            "workflow_role": t.get("workflow_role"),
            "estado_vehiculo": t.get("estado_vehiculo"),
            "horometro": t.get("horometro"),
            "ign_on_time_s": t.get("ign_on_time_s"),
            "coms_age_s": t.get("coms_age_s"),
            "ultimo_evento": t.get("ultimo_evento"),
            "ultimo_evento_at": t.get("ultimo_evento_at"),
        },
        # --- lo que el Hub calcula ----------------------------------------
        "estado_hub": op["estado_hub"],
        "responsable": op["responsable"],
        "horas_medidas": medidas,
        "horas_facturables": round(facturables, 2),
        "monto_facturable": round(facturables * precio, 2) if precio else None,
        "exposicion_usd": exp.get("costo_usd"),
        "medicion": exp.get("medicion", "sin datos"),
        "moneda": "USD",
        # --- quien responde por esto --------------------------------------
        "aprobado_por": aprobado_por,
        "aprobado_at": datetime.now(timezone.utc).isoformat(),
    }
    registro["hash"] = sellar(registro)
    return registro


def registrar(registro: dict[str, Any]) -> int:
    """Guarda el registro. Append-only: nunca se hace UPDATE aqui."""
    return x(
        "INSERT INTO pea_registros (maquinaria, proyecto_id, solicitud_id,"
        " estado_hub, horas_facturables, monto_facturable, exposicion_usd,"
        " medicion, aprobado_por, hash, registro)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (registro["maquinaria"], registro["proyecto_id"],
         registro["solicitud_id"], registro["estado_hub"],
         registro["horas_facturables"], registro["monto_facturable"],
         registro["exposicion_usd"], registro["medicion"],
         registro["aprobado_por"], registro["hash"],
         json.dumps(registro, ensure_ascii=False)),
    )


def recomputar(pea_id: int) -> dict[str, Any] | None:
    """Verifica un registro guardado contra su propio hash.

    Es la demostracion de que no hace falta confiar en nosotros: el hash se
    recalcula desde el contenido y tiene que dar identico.
    """
    fila = q1("SELECT * FROM pea_registros WHERE id = ?", (pea_id,))
    if not fila:
        return None
    guardado = json.loads(fila["registro"])
    return {
        "id": pea_id,
        "hash_guardado": fila["hash"],
        "hash_recomputado": sellar(guardado),
        "verifica": verificar(guardado),
        "registro": guardado,
    }
