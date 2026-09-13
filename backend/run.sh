#!/usr/bin/env bash
# Arranque del Hub. Idempotente: se puede correr las veces que sea.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "==> creando entorno virtual"
  python3 -m venv .venv
fi
source .venv/bin/activate

if [ ! -f .venv/.deps-ok ]; then
  echo "==> instalando dependencias"
  pip install --quiet --upgrade pip
  pip install --quiet -r requirements.txt
  touch .venv/.deps-ok
fi

[ -f .env ] || cp .env.example .env
set -a; source .env; set +a

PROD=0
[ "${1:-}" = "--prod" ] && PROD=1

if [ "$PROD" -eq 1 ]; then
  # Modo demo: un solo proceso sirve API, Command Center y PWA. Sin dev server
  # de Vite, sin segundo puerto, sin --reload recompilando a media frase.
  DIST=../frontend/dist
  if [ ! -d "$DIST" ] || [ -n "$(find ../frontend/src -newer "$DIST/index.html" 2>/dev/null | head -1)" ]; then
    echo "==> compilando el Command Center"
    (cd ../frontend && npm install --silent && npm run build)
  fi

  # La IP de la LAN: el jurado y el resto del equipo entran por aqui desde el
  # celular. Sin esto hay que adivinarla a las 19:55, que es justo cuando no
  # se quiere estar adivinando nada.
  # `|| true` en cada intento: sin esto, en Mac (`hostname -I` no existe ahi,
  # es de Linux) el `set -e` de arriba mata el script ENTERO en silencio antes
  # de llegar al fallback de abajo. Nadie ve el banner, nadie ve un error, el
  # prompt vuelve solo. Bug real, no de quien lo corre.
  IP=$(hostname -I 2>/dev/null | awk '{print $1}' || true)
  [ -z "$IP" ] && IP=$(ipconfig getifaddr en0 2>/dev/null || true)
  [ -z "$IP" ] && IP=$(ipconfig getifaddr en1 2>/dev/null || true)
  echo
  echo "  ==============================================="
  echo "   Hub de Operaciones — listo"
  echo
  echo "   En esta laptop : http://localhost:8000"
  [ -n "$IP" ] && echo "   Desde la red   : http://$IP:8000"
  echo "   PWA de campo   : /campo        API: /docs"
  echo "  ==============================================="
  echo
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi

echo "==> Hub en http://127.0.0.1:8000  (docs /docs, PWA /campo)"
echo "    para la demo:  ./backend/run.sh --prod"
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
