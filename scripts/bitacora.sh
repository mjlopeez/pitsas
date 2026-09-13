#!/usr/bin/env bash
# Anota un cambio en docs/ESTADO.md y estampa el resultado de las pruebas.
#
# Existe porque la disciplina de documentar se cae a las 14:00 si cuesta mas de
# un comando. Uso:
#   ./scripts/bitacora.sh "conciliacion de diesel conectada al orquestador"
#   ./scripts/bitacora.sh --sin-pruebas "notas del pitch"
set -uo pipefail
cd "$(dirname "$0")/.."

PROBAR=1
if [ "${1:-}" = "--sin-pruebas" ]; then PROBAR=0; shift; fi

MSG="${*:-}"
if [ -z "$MSG" ]; then
  echo "uso: ./scripts/bitacora.sh [--sin-pruebas] \"que cambiaste\"" >&2
  exit 1
fi

QUIEN="${BITACORA_AUTOR:-$(git config user.name 2>/dev/null || echo "$(whoami)")}"
HORA=$(TZ=America/El_Salvador date "+%H:%M" 2>/dev/null || date -u -d '-6 hours' "+%H:%M")
FECHA=$(TZ=America/El_Salvador date "+%Y-%m-%d %H:%M" 2>/dev/null || date -u -d '-6 hours' "+%Y-%m-%d %H:%M")

SMOKE="sin correr"
if [ "$PROBAR" -eq 1 ]; then
  echo "==> corriendo pruebas de humo"
  if OUT=$(./scripts/smoke.sh 2>&1); then
    SMOKE=$(echo "$OUT" | sed 's/\x1b\[[0-9;]*m//g' | grep -oE '[0-9]+ pruebas OK' | tail -1)
    SMOKE="${SMOKE:-verdes}"
  else
    SMOKE=$(echo "$OUT" | sed 's/\x1b\[[0-9;]*m//g' | grep -oE '[0-9]+ OK, [0-9]+ FALLAN' | tail -1)
    SMOKE="⚠️ ${SMOKE:-FALLAN}"
    echo "$OUT" | sed 's/\x1b\[[0-9;]*m//g' | grep -A2 FALLA | head -20
  fi
fi

LINEA="- **${HORA} · ${QUIEN}** · ${MSG} · **smoke ${SMOKE}**"

python3 - "$LINEA" "$FECHA" << 'PY'
import re, sys, pathlib
linea, fecha = sys.argv[1], sys.argv[2]
p = pathlib.Path("docs/ESTADO.md")
s = p.read_text()

# sella la fecha de ultima actualizacion
s = re.sub(r"\*\*Última actualización:\*\* .*", f"**Última actualización:** {fecha} SV", s, count=1)

# estampa el resultado de las pruebas en el encabezado
m = re.search(r"\*\*smoke (.+?)\*\*", linea)
if m:
    s = re.sub(r"\*\*Pruebas de humo:\*\* .*", f"**Pruebas de humo:** {m.group(1)}", s, count=1)

# inserta la entrada arriba de la bitacora, despues del comentario de formato
marca = "<!-- Lo más nuevo arriba. Formato: HH:MM · quién · qué · smoke -->"
if marca in s:
    s = s.replace(marca, marca + "\n\n" + linea, 1)
else:
    s = s.rstrip() + "\n" + linea + "\n"

p.write_text(s)
print("==> anotado en docs/ESTADO.md")
print("   ", linea)
PY
