#!/usr/bin/env bash
B="${1:-http://localhost:8000}"
ok=0; fail=0
verde() { printf "  \033[32m✓\033[0m %s\n" "$1"; ok=$((ok+1)); }
rojo()  { printf "  \033[31m✗\033[0m %s\n     esperado: %s\n     obtuve  : %s\n" "$1" "$2" "$3"; fail=$((fail+1)); }
check() { [ "$2" = "$3" ] && verde "$1" || rojo "$1" "$2" "$3"; }
contiene() { case "$3" in *"$2"*) verde "$1";; *) rojo "$1" "contiene '$2'" "${3:0:70}";; esac; }

echo ""; echo "═══ Hub de Operaciones — verificacion"; echo "    contra: $B"; echo ""
echo "1. La API responde"
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$B/health")
check "GET /health" "200" "$code"
[ "$code" != "200" ] && { echo "  La API no responde. Arrancala primero."; exit 1; }

echo ""; echo "2. Datos del sandbox real"
maq=$(curl -s "$B/api/ps/maquinas")
check "6 maquinas" "6" "$(printf '%s' "$maq" | grep -o '"maquinaria"' | wc -l | tr -d ' ')"
check "0 fantasmas" "0" "$(printf '%s' "$maq" | grep -o 'EXC22017LC\|RC03004EC\|RM19003EC' | wc -l | tr -d ' ')"
for m in EXC-01 EXC-02 EXC-03 RE-01; do contiene "$m existe" "$m" "$maq"; done
check "15 geocercas" "15" "$(curl -s "$B/api/ps/geocercas" | grep -o '"poi_id"' | wc -l | tr -d ' ')"
geo=$(curl -s "$B/api/ps/geocercas")
contiene "PROY-001 coordenada real" "13.9290675" "$geo"
contiene "PROY-014 escalado 1e7" "13.3376152" "$geo"

echo ""; echo "3. Los numeros del guion"
contiene "EXC-01 en 1200" '"costo_expuesto_usd":1200' "$maq"
contiene "EXC-02 en 75 (KPI calla)" '"costo_expuesto_usd":75' "$maq"
exc01=$(curl -s "$B/api/ps/vista-unificada/EXC-01")
contiene "EXC-01 alerta_operativa" '"estado_hub":"alerta_operativa"' "$exc01"
contiene "responsable Maquinaria" '"responsable":"Maquinaria"' "$exc01"
contiene "estado en ingles" '"estado_tarea":"Pending"' "$exc01"
contiene "medicion sin datos" '"medicion":"sin datos"' "$exc01"
contiene "geocerca destino" '"destino_poi_id":"5455284"' "$exc01"

echo ""; echo "4. Los cinco estados"
for par in "EXC-02:diferencia_valida" "RE-01:riesgo_critico" "SOL-RETRO-SIN-UNIDAD:vinculo_no_confirmado"; do
  m="${par%%:*}"; esp="${par##*:}"
  got=$(curl -s "$B/api/ps/vista-unificada/$m" | grep -o '"estado_hub":"[a-z_]*"' | head -1 | cut -d'"' -f4)
  check "$m -> $esp" "$esp" "$got"
done
contiene "sin unidad trae tarea:null" '"tarea":null' "$(curl -s "$B/api/ps/vista-unificada/SOL-RETRO-SIN-UNIDAD")"

echo ""; echo "5. WhatsApp retirado"
check "0 rutas whatsapp" "0" "$(curl -s "$B/openapi.json" | grep -o '/ingest/whatsapp' | wc -l | tr -d ' ')"
check "whatsapp/sim -> 404" "404" "$(curl -s -o /dev/null -w "%{http_code}" -X POST "$B/ingest/whatsapp/sim")"

echo ""; echo "6. Lecturas abiertas"
for r in /api/ps/maquinas /api/ps/mapeo /api/ps/geocercas /api/ps/sangrado /api/assets /api/connectors /api/analytics; do
  check "GET $r" "200" "$(curl -s -o /dev/null -w "%{http_code}" "$B$r")"
done

echo ""; echo "7. Seguridad"
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$B/admin/seed-ps")
if [ "$code" = "401" ]; then
  verde "sin token -> 401"
  if [ -n "${HUB_ADMIN_TOKEN:-}" ]; then
    check "con token -> 200" "200" "$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "X-Hub-Token: $HUB_ADMIN_TOKEN" "$B/admin/seed-ps")"
  else
    printf "  \033[33m·\033[0m exporta HUB_ADMIN_TOKEN para probar el token valido\n"
  fi
elif [ "$code" = "200" ]; then
  printf "  \033[33m⚠\033[0m  MUTADORES ABIERTOS (200). OK en local, PELIGROSO en ngrok.\n"
  printf "     Pone HUB_ADMIN_TOKEN en backend/.env y arranca con: set -a; source .env; set +a\n"
  fail=$((fail+1))
else rojo "POST /admin/seed-ps" "401 o 200" "$code"; fi

echo ""; echo "═══════════════════════════════════════"
printf "  pasaron: %s    fallaron: %s\n" "$ok" "$fail"
echo "═══════════════════════════════════════"; echo ""
[ "$fail" -eq 0 ] && echo "  Todo en orden." || echo "  Revisa lo marcado arriba."
echo ""
exit "$fail"
