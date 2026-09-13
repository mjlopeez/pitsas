"""
SSE: el canal en vivo del Command Center.

Se eligio Server-Sent Events sobre WebSockets a proposito: reconexion
automatica del navegador, una sola direccion (que es lo que necesitamos) y
cero libreria del lado del cliente.

Duenio: Wilbert / consume Majo
"""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ..events import subscribe, unsubscribe

router = APIRouter(prefix="/api", tags=["stream"])


@router.get("/stream")
async def stream(request: Request) -> StreamingResponse:
    qq = subscribe()

    async def gen():
        try:
            yield "event: hello\ndata: {\"ok\":true}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(qq.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"      # evita que proxies corten
                    continue
                yield f"event: {msg['kind']}\ndata: {json.dumps(msg['data'], ensure_ascii=False)}\n\n"
        finally:
            unsubscribe(qq)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
