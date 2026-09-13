"""
Log de eventos append-only + bus en memoria para SSE.

En produccion esto seria Kafka. Aqui es una tabla y una cola asyncio, y para
la demo se comporta igual. Lo que NO es sustituible es el contrato canonico.

Duenio: Wilbert
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from .canonical import CanonicalEvent
from .db import conn, x

# Suscriptores SSE activos (uno por pestania abierta del Command Center).
_subs: list[asyncio.Queue] = []


def subscribe() -> asyncio.Queue:
    qq: asyncio.Queue = asyncio.Queue(maxsize=200)
    _subs.append(qq)
    return qq


def unsubscribe(qq: asyncio.Queue) -> None:
    if qq in _subs:
        _subs.remove(qq)


def publish(kind: str, data: dict[str, Any]) -> None:
    """Empuja a todas las pestanias abiertas. Nunca bloquea ni revienta."""
    msg = {"kind": kind, "data": data}
    for qq in list(_subs):
        try:
            qq.put_nowait(msg)
        except asyncio.QueueFull:
            pass


def append(ev: CanonicalEvent, idempotency_key: str | None = None) -> int | None:
    """
    Escribe el evento en el log. Devuelve el id, o None si era duplicado.
    La clave de idempotencia es lo que hace segura la sincronizacion de la PWA
    offline: reenviar la misma mutacion diez veces no duplica nada.
    """
    payload = ev.model_dump(mode="json")
    try:
        return x(
            "INSERT INTO events (asset_identifier, event_timestamp, source, payload, idempotency_key)"
            " VALUES (?,?,?,?,?)",
            (ev.asset_identifier, ev.event_timestamp.isoformat(), ev.source.value,
             json.dumps(payload, ensure_ascii=False), idempotency_key),
        )
    except Exception as exc:  # sqlite3.IntegrityError = duplicado
        if "UNIQUE" in str(exc):
            return None
        raise


def bump_connector(source: str, ok: bool, error: str | None = None) -> None:
    c = conn()
    c.execute(
        "INSERT INTO connector_stats (source, accepted, rejected, last_event, last_error)"
        " VALUES (?, ?, ?, datetime('now'), ?)"
        " ON CONFLICT(source) DO UPDATE SET"
        "   accepted = accepted + excluded.accepted,"
        "   rejected = rejected + excluded.rejected,"
        "   last_event = datetime('now'),"
        "   last_error = COALESCE(excluded.last_error, connector_stats.last_error)",
        (source, 1 if ok else 0, 0 if ok else 1, error),
    )
    c.commit()
