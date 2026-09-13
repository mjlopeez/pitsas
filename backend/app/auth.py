"""
Proteccion de los endpoints que MUTAN estado.

Por que existe: la API se expone por ngrok para que el equipo y el jurado
entren desde fuera de la LAN. En el momento en que deja de ser localhost,
`POST /admin/reset` deja de ser una ayuda de desarrollo y pasa a ser un boton
de autodestruccion que cualquiera con la URL puede apretar — y `/docs`
publica la lista completa de rutas para quien la quiera.

Como funciona, y por que asi:

  HUB_ADMIN_TOKEN sin definir  -> todo abierto, como siempre.
  HUB_ADMIN_TOKEN definido     -> los mutadores exigen la cabecera X-Hub-Token.

El default es "abierto" a proposito. Cuatro personas trabajando en local a las
tres de la manana no pueden quedarse fuera de su propio Hub porque alguien
puso una variable de entorno; y una demo que pide credencial en el minuto 2
es una demo que se cae. La proteccion se enciende SOLO cuando se expone por
ngrok, y eso esta escrito en .env.example.

Que NO se protege, y por que:

  - Todos los GET. El Command Center lee sin credencial; si el front tuviera
    que autenticarse, habria que tocar el front, y tocar el front a estas
    horas es exactamente lo que no queremos.
  - POST /api/ps/pea/{maquinaria}. Es append-only: lo peor que puede hacer un
    extranio es agregar registros de evidencia, que quedan firmados con el
    nombre que haya escrito. No borra ni altera nada.

Duenio: Wilbert
"""
from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException


def _token_configurado() -> str:
    """Se lee en cada peticion, no al importar.

    Asi se puede encender y apagar sin reiniciar el proceso durante los
    ensayos — y sobre todo, los tests pueden probar los dos modos sin
    recargar el modulo.
    """
    return os.getenv("HUB_ADMIN_TOKEN", "").strip()


def proteger(x_hub_token: str | None = Header(default=None)) -> None:
    """Dependencia de FastAPI para los endpoints que mutan estado.

    Sin token configurado no hace nada. Con token configurado, exige que la
    cabecera coincida.
    """
    esperado = _token_configurado()
    if not esperado:
        return

    # compare_digest en vez de == : evita filtrar el token por el tiempo que
    # tarda la comparacion. Es barato y es lo correcto.
    if not x_hub_token or not hmac.compare_digest(x_hub_token, esperado):
        raise HTTPException(
            status_code=401,
            detail=("Este endpoint modifica estado y el Hub esta expuesto. "
                    "Manda la cabecera X-Hub-Token."),
        )
