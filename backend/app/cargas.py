"""
Proyeccion de cargas de material, con duenio exclusivo por campo.

Aqui se ve mas claro que en ningun otro lado la tercera friccion del reto
—responsables de la informacion— porque los duenios son unidades de negocio
distintas de ECON y ninguna puede pisar el campo de otra:

    la planta      es duenia del reloj de dosificacion y del diseno de mezcla
    el laboratorio es duenio del veredicto de cumplimiento
    el motorista   es duenio de la llegada

Que la obra declare "este lote cumple" no lo vuelve cierto. Solo el laboratorio
puede escribir ese campo. Un intento de otra fuente no sobrescribe en silencio:
queda rechazado y con ticket.

Duenio: Wilbert
"""
from __future__ import annotations

import json
from datetime import datetime

from .canonical import (
    CanonicalEvent,
    FieldProvenance,
    Source,
    TipoCarga,
    gana,
    puede_escribir,
)
from .db import jloads, q1, x

# Campos de la carga que se proyectan a la tabla.
CAMPOS = ("tipo", "cantidad", "unidad", "diseno", "dosificado_en",
          "temperatura_c", "planta_origen", "obra_destino",
          "cumple_especificacion")


def nuevo_lote(tipo: TipoCarga | str, ahora: datetime) -> str:
    """Lote legible: el laboratorio y la obra lo dicen en voz alta por radio."""
    t = tipo.value if isinstance(tipo, TipoCarga) else str(tipo)
    return f"{t[:1]}-{ahora.strftime('%d%H%M%S')}"


def _valor_sql(campo: str, valor):
    if valor is None:
        return None
    if campo == "dosificado_en":
        return valor.isoformat() if isinstance(valor, datetime) else str(valor)
    if campo == "cumple_especificacion":
        return 1 if valor else 0
    if campo == "tipo":
        return valor.value if isinstance(valor, TipoCarga) else str(valor)
    return valor


def proyectar(ev: CanonicalEvent, ahora: datetime) -> tuple[str | None, list[dict]]:
    """
    Aplica la carga del evento. Devuelve (lote, alertas).

    Las alertas son de dos clases: rechazos de escritura (una unidad intentando
    escribir un campo que no es suyo) y las que devuelve rules/carga.py.
    """
    c = ev.carga
    if c is None:
        return None, []

    lote = c.lote or nuevo_lote(c.tipo, ahora)
    fila = q1("SELECT * FROM cargas WHERE lote = ?", (lote,))
    prov: dict = jloads(fila.get("provenance"), {}) if fila else {}

    cambios: dict = {}
    alertas: list[dict] = []

    for campo in CAMPOS:
        valor = getattr(c, campo, None)
        if valor is None:
            continue

        # --- duenio exclusivo: la barrera mas fuerte ------------------------
        if not puede_escribir(campo, ev.source):
            alertas.append({
                "kind": "gobernanza",
                "severity": "alta",
                "title": f"Escritura rechazada: {campo}",
                "detail": (
                    f"{ev.source.value} intento escribir '{campo}' en el lote "
                    f"{lote}, pero ese campo tiene duenio exclusivo. "
                    + ("Solo el laboratorio dictamina si un lote cumple."
                       if campo == "cumple_especificacion"
                       else "Solo la planta define la dosificacion y el diseno.")
                ),
                "payload": {"lote": lote, "campo": campo,
                            "fuente_rechazada": ev.source.value,
                            "valor_propuesto": str(valor)},
            })
            continue

        # --- precedencia ordinaria para los campos compartidos --------------
        duenio_actual = None
        if campo in prov:
            try:
                duenio_actual = Source(prov[campo]["source"])
            except (KeyError, ValueError):
                duenio_actual = None
        if not gana(campo, ev.source, duenio_actual):
            continue

        cambios[campo] = _valor_sql(campo, valor)
        prov[campo] = FieldProvenance(source=ev.source).model_dump(mode="json")

    if ev.asset_identifier:
        cambios["asset_identifier"] = ev.asset_identifier

    # El estado de la carga lo mueve quien reporta: la planta la dosifica, el
    # camion la lleva, la obra la descarga.
    if ev.source in (Source.PLANTA_CONCRETO, Source.PLANTA_ASFALTO) and c.dosificado_en:
        cambios.setdefault("estado", "en_transito")

    if not fila:
        estado = cambios.pop("estado", "en_planta")
        cols = ["lote", "estado", "created_at", "updated_at", "provenance"] + list(cambios)
        vals = [lote, estado, ahora.isoformat(), ahora.isoformat(),
                json.dumps(prov, ensure_ascii=False)] + list(cambios.values())
        x(f"INSERT INTO cargas ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
          tuple(vals))
    elif cambios:
        cambios["updated_at"] = ahora.isoformat()
        sets = ", ".join(f"{k} = ?" for k in cambios)
        x(f"UPDATE cargas SET {sets}, provenance = ? WHERE lote = ?",
          (*cambios.values(), json.dumps(prov, ensure_ascii=False), lote))

    # --- reglas de perecibilidad --------------------------------------------
    from .rules import carga as r_carga

    fila = q1("SELECT * FROM cargas WHERE lote = ?", (lote,))
    if fila:
        r = r_carga.revisar(fila, ahora)
        if r:
            alertas.append(r)

        # Un ensayo que no cumple sobre una carga que ya salio es el caso que
        # obliga a cruzar silos: hay que detenerla antes de que se coloque.
        if fila.get("cumple_especificacion") == 0:
            x("UPDATE cargas SET estado = 'retenida' WHERE lote = ?", (lote,))
            alertas.append({
                "kind": "gobernanza",
                "severity": "critica",
                "title": f"Lote {lote} NO cumple: entrega retenida",
                "detail": (
                    f"El laboratorio dictamino que el lote {lote} no cumple "
                    f"({fila.get('ensayo') or 'ensayo sin detalle'}). La carga "
                    f"iba a {fila.get('obra_destino') or 'obra sin asignar'} en "
                    f"{fila.get('asset_identifier') or 'unidad sin asignar'}. "
                    "Detener antes de la colocacion y notificar al residente."
                ),
                "payload": {"lote": lote, "estado": "retenida",
                            "ensayo": fila.get("ensayo"),
                            "obra": fila.get("obra_destino"),
                            "unidad": fila.get("asset_identifier")},
            })

    return lote, alertas


def estado_carga(lote: str) -> dict | None:
    fila = q1("SELECT * FROM cargas WHERE lote = ?", (lote,))
    if not fila:
        return None
    fila["provenance"] = jloads(fila.get("provenance"), {})
    if fila.get("cumple_especificacion") is not None:
        fila["cumple_especificacion"] = bool(fila["cumple_especificacion"])
    return fila
