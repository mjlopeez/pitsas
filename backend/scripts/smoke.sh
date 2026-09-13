#!/usr/bin/env bash
# Prueba de humo de la ruta completa de la demo.
#
# CORRE ESTO DESPUES DE CADA CAMBIO. Si algo aqui falla, la demo falla.
#   ./scripts/smoke.sh
#
# Tiene que quedar verde CON y SIN MIMO_API_KEY: los respaldos por reglas son la
# red de seguridad contra el wifi del salon.
#
# Los identificadores de activos y nodos se resuelven contra la API, no se
# escriben a mano: Emily va a cambiar el catalogo y los nombres durante el dia y
# las pruebas no se pueden caer por eso.
set -uo pipefail
B="${HUB_URL:-http://127.0.0.1:8000}"
ok=0; fallo=0
RUN="$(date +%s)-$$-$RANDOM"   # sufijo de corrida: unico aunque dos
                                # corridas caigan en el mismo segundo

check() { # nombre, comando, patron esperado
  local nombre="$1" out
  out=$(eval "$2" 2>&1)
  if echo "$out" | grep -q "$3"; then
    printf '  \033[32mOK\033[0m   %s\n' "$nombre"; ok=$((ok+1))
  else
    printf '  \033[31mFALLA\033[0m %s\n       esperaba: %s\n       obtuvo:   %s\n' \
      "$nombre" "$3" "$(echo "$out" | head -c 220)"; fallo=$((fallo+1))
  fi
}

check_no() { # nombre, comando, patron que NO debe aparecer
  local nombre="$1" out
  out=$(eval "$2" 2>&1)
  if echo "$out" | grep -q "$3"; then
    printf '  \033[31mFALLA\033[0m %s\n       NO esperaba: %s\n' "$nombre" "$3"
    fallo=$((fallo+1))
  else
    printf '  \033[32mOK\033[0m   %s\n' "$nombre"; ok=$((ok+1))
  fi
}

j() { curl -s --max-time 20 -X POST "$B$1" -H 'content-type: application/json' -d "$2"; }

# --- resolucion dinamica de identificadores ---------------------------------
activo_de() {  # categoria -> primer asset_identifier de esa categoria
  curl -s --max-time 5 "$B/api/assets" | python3 -c "
import json,sys
cat=sys.argv[1]
for a in json.load(sys.stdin):
    if (a.get('kind') or '')==cat: print(a['asset_identifier']); break
" "$1"
}
nodo_de() {  # tipo -> primer project_id de ese tipo
  curl -s --max-time 5 "$B/api/projects" | python3 -c "
import json,sys
k=sys.argv[1]
for p in json.load(sys.stdin):
    if p['kind']==k: print(p['project_id']); break
" "$1"
}

echo "== Hub de Operaciones: prueba de humo =="
echo "   $B"
echo

echo "-- salud"
check "el Hub responde" "curl -s --max-time 5 $B/health" '"ok":true'

MIXER=$(activo_de "camion mezclador")
EXCAV=$(activo_de "excavadora")
PLANTA=$(nodo_de "planta_concreto")
CANTERA=$(nodo_de "cantera")
OBRA=$(nodo_de "obra")
if [ -z "${MIXER:-}" ] || [ -z "${PLANTA:-}" ] || [ -z "${OBRA:-}" ]; then
  printf '  \033[31mFALLA\033[0m no se pudo resolver la flota o los nodos. Sembro el Hub?\n'
  exit 1
fi
# Los escenarios de carga perecedera dependen de la GEOGRAFIA concreta: las
# distancias PCSS->PDUT (~35 min), PCSS->APLL (~54 min) y PCSS->BSON (~97 min)
# son las que hacen alcanzables las tres salidas del motor. Ese nodo va fijo a
# proposito; si Emily lo renombra, la prueba falla ruidosamente y esta bien:
# el escenario de la demo depende de el.
PLANTA_DEMO=PCSS
check "el nodo del escenario de la demo existe" \
  "curl -s $B/api/projects" "\"project_id\":\"$PLANTA_DEMO\""
echo "   mixer=$MIXER excavadora=$EXCAV planta_demo=$PLANTA_DEMO cantera=$CANTERA"
echo

echo "-- los cuatro adaptadores normalizan al mismo contrato"
check "Caterpillar (ISO 15143-3)" \
  "j /ingest/telemetry/cat '{\"EquipmentHeader\":{\"SerialNumber\":\"CAT-320-04\"},\"SnapshotTime\":\"2026-09-12T14:00:00Z\",\"CumulativeOperatingHours\":{\"Hour\":4516.0},\"EngineStatus\":{\"Running\":true}}'" \
  '"status":"ok"'
check "Komatsu (propietario, litros)" \
  "j /ingest/telemetry/komatsu '{\"machine\":{\"id\":\"KOM-PC200-03\"},\"ts\":1757689380,\"smr\":9812.5,\"fuel_l\":31000,\"engine\":\"IDLING\"}'" \
  '"status":"ok"'
check "Volvo (value/unit)" \
  "j /ingest/telemetry/volvo '{\"equipmentId\":\"VOL-EC220-04\",\"snapshotTime\":\"2026-09-12T14:00:00Z\",\"hourMeter\":{\"value\":3311,\"unit\":\"h\"},\"engineRunning\":false}'" \
  '"status":"ok"'
check "Retrofit J1939 (SPN 247/250)" \
  "j /ingest/telemetry/j1939 '{\"vin\":\"$MIXER\",\"epoch\":1757689400,\"spn\":{\"247\":9241,\"250\":54000},\"rpm\":720,\"load_pct\":4}'" \
  '"status":"ok"'

echo "-- un payload malformado se rechaza y queda visible"
check "rechazo con motivo"     "j /ingest/telemetry/volvo '{\"machineId\":\"X\"}'" 'payload rechazado'
check "el conector lo reporta" "curl -s $B/api/connectors" 'rechazados\|degradado'

echo "-- minuto 1: nota de voz -> evento canonico"
echo "   (bloque WhatsApp/sim retirado 13/09 — decision del equipo, ver main.py)"

echo "-- gobernanza: precedencia e idempotencia"
check "idempotencia (reenvio no duplica)" \
  "j /ingest/events '{\"asset_identifier\":\"CAT-320-04\",\"event_timestamp\":\"2026-09-12T14:10:00Z\",\"source\":\"field_pwa\",\"operating_hours\":4521.5,\"idempotency_key\":\"idem-$RUN\"}' >/dev/null; j /ingest/events '{\"asset_identifier\":\"CAT-320-04\",\"event_timestamp\":\"2026-09-12T14:10:00Z\",\"source\":\"field_pwa\",\"operating_hours\":4521.5,\"idempotency_key\":\"idem-$RUN\"}'" \
  'duplicado'
check "rechaza asset_identifier vacio" \
  "j /ingest/events '{\"asset_identifier\":\"\",\"event_timestamp\":\"2026-09-12T14:40:00Z\",\"source\":\"field_pwa\"}'" \
  '422\|detail'

echo "-- conciliacion de diesel (la tolerancia del 5% del documento)"
curl -s --max-time 5 -X POST "$B/admin/base-diesel?asset=CAT-320-04&consumido=60" >/dev/null 2>&1
check "un vale de 120 gal contra 60 consumidos abre ticket" \
  "j /ingest/events '{\"asset_identifier\":\"CAT-320-04\",\"event_timestamp\":\"2026-09-12T14:30:00Z\",\"source\":\"field_whatsapp\",\"fuel_delivered\":120,\"idempotency_key\":\"vale-alto-$RUN\"}' >/dev/null; curl -s $B/api/assets/CAT-320-04" \
  'Descuadre de diesel'
curl -s --max-time 5 -X POST "$B/admin/base-diesel?asset=$EXCAV&consumido=60" >/dev/null 2>&1
check_no "un vale dentro del 5% no abre ticket" \
  "j /ingest/events '{\"asset_identifier\":\"$EXCAV\",\"event_timestamp\":\"2026-09-12T14:31:00Z\",\"source\":\"field_whatsapp\",\"fuel_delivered\":61.5,\"idempotency_key\":\"vale-ok-$RUN\"}' >/dev/null; curl -s $B/api/assets/$EXCAV" \
  'Descuadre de diesel'

echo "-- servicio vencido saca la maquina de operacion"
check "pasa a EN_MANTENIMIENTO y el taller lo puede cerrar" \
  "curl -s -X POST '$B/admin/vencer-servicio?asset=$EXCAV' >/dev/null; j /ingest/telemetry/cat '{\"EquipmentHeader\":{\"SerialNumber\":\"$EXCAV\"},\"SnapshotTime\":\"2026-09-12T14:35:00Z\",\"EngineStatus\":{\"Running\":true}}' | grep -o EN_MANTENIMIENTO; curl -s -X POST $B/api/assets/$EXCAV/servicio" \
  'servicio cerrado'

echo "-- minuto 3: carga perecedera contra la veda del VMT (lunes)"
# PDUT esta a ~35 min: el desvio (+40) todavia cabe en los 90 min del concreto.
check "sale a las 15:10 y el desvio salva la carga" \
  "j /api/dispatch/carga '{\"tipo\":\"CONCRETO\",\"planta_origen\":\"$PLANTA_DEMO\",\"obra_destino\":\"PDUT\",\"asset_identifier\":\"$MIXER\",\"listo_desde\":\"2026-09-14T21:10:00Z\"}'" \
  '"decision":"reruta"'
# APLL esta a ~54 min: ni el desvio cabe. La respuesta correcta no es mover el
# camion, es que la planta no dosifique todavia.
check "no alcanza por ninguna ruta -> NO DOSIFICAR" \
  "j /api/dispatch/carga '{\"tipo\":\"CONCRETO\",\"planta_origen\":\"$PLANTA_DEMO\",\"obra_destino\":\"APLL\",\"asset_identifier\":\"$MIXER\",\"listo_desde\":\"2026-09-14T20:45:00Z\"}'" \
  '"decision":"no_dosificar"'
check "y dice a que hora dosificar" \
  "j /api/dispatch/carga '{\"tipo\":\"CONCRETO\",\"planta_origen\":\"$PLANTA_DEMO\",\"obra_destino\":\"APLL\",\"asset_identifier\":\"$MIXER\",\"listo_desde\":\"2026-09-14T20:45:00Z\"}'" \
  'dosificar_a_las'
check "obra fuera de la vida del material -> sugiere otra planta" \
  "j /api/dispatch/carga '{\"tipo\":\"CONCRETO\",\"planta_origen\":\"$PLANTA_DEMO\",\"obra_destino\":\"BSON\",\"asset_identifier\":\"$MIXER\",\"listo_desde\":\"2026-09-14T20:45:00Z\"}'" \
  'plantas_alternativas'
check "fuera de veda llega directo" \
  "j /api/dispatch/carga '{\"tipo\":\"CONCRETO\",\"planta_origen\":\"$PLANTA_DEMO\",\"obra_destino\":\"PDUT\",\"asset_identifier\":\"$MIXER\",\"listo_desde\":\"2026-09-14T16:00:00Z\"}'" \
  '"decision":"autoriza"'
check "el agregado no perece: manda solo la veda" \
  "j /api/dispatch/carga '{\"tipo\":\"AGREGADO\",\"planta_origen\":\"$CANTERA\",\"obra_destino\":\"PDUT\",\"listo_desde\":\"2026-09-14T21:10:00Z\"}'" \
  '"vida_minutos":null'

echo "-- carga perecedera: el reloj y la temperatura"
LOTE="C-SMOKE-$RUN"
check "la planta dosifica y arranca el reloj" \
  "j /ingest/planta '{\"tipo\":\"CONCRETO\",\"planta_origen\":\"$PLANTA_DEMO\",\"obra_destino\":\"PDUT\",\"asset_identifier\":\"$MIXER\",\"cantidad\":8,\"diseno\":\"fc280\",\"lote\":\"$LOTE\"}'" \
  '"estado": *"en_transito"'
check "asfalto bajo la temperatura minima se rechaza" \
  "j /ingest/planta '{\"tipo\":\"ASFALTO\",\"planta_origen\":\"$(nodo_de planta_asfalto)\",\"obra_destino\":\"BSON\",\"asset_identifier\":\"ETN-Black-Topper-08\",\"temperatura_c\":108,\"lote\":\"A-SMOKE-$RUN\"}' >/dev/null; curl -s $B/api/alerts" \
  'Asfalto bajo temperatura'

echo "-- gobernanza: DUENIO EXCLUSIVO de campo"
check_no "la obra NO puede declarar que un lote cumple" \
  "j /ingest/events '{\"asset_identifier\":\"$MIXER\",\"event_timestamp\":\"2026-09-12T15:00:00Z\",\"source\":\"field_whatsapp\",\"carga\":{\"tipo\":\"CONCRETO\",\"lote\":\"$LOTE\",\"cumple_especificacion\":true},\"idempotency_key\":\"obra-$RUN\"}' >/dev/null; curl -s '$B/ingest/cargas' | python3 -c \"
import json,sys
c=[x for x in json.load(sys.stdin) if x['lote']=='$LOTE']
print(c[0]['cumple_especificacion'] if c else 'sin lote')
\"" \
  'True'
check "y el intento queda con ticket de gobernanza" \
  "curl -s $B/api/alerts" 'Escritura rechazada'
check "solo el laboratorio dictamina, y retiene la entrega" \
  "j /ingest/lab '{\"lote\":\"$LOTE\",\"cumple\":false,\"ensayo\":\"compresion 7 dias 231 kg/cm2\"}'" \
  '"estado": *"retenida"'

echo "-- Prisma + Startrack: los 5 estados del Hub sobre datos reales de Nexus"
PS="curl -s --max-time 5 $B/api/ps"
E1="$PS/vista-unificada/EXC-01"
estado_de() {  # maquinaria -> estado_hub de su primera operacion
  curl -s --max-time 5 "$B/api/ps/vista-unificada/$1" | python3 -c "
import json,sys
ops=json.load(sys.stdin)
print(ops[0]['estado_hub'] if ops else 'sin operaciones')
"
}

check "EXC-01 cruza Nexus y Startrack por el No. de activo" \
  "$E1" 'EXC-17006EC'
check "EXC-01: asignada valida pero sin confirmacion -> alerta_operativa" \
  "estado_de EXC-01" 'alerta_operativa'
check "y la alerta viene con su accion y su area responsable" \
  "$E1 | python3 -c \"import json,sys; o=json.load(sys.stdin)[0]; print(o['accion'],'|',o['area'])\"" \
  'Validar ubicacion y conectividad del equipo | maquinaria'
check "la exposicion se valoriza en dolares, no en horas abstractas" \
  "$E1 | python3 -c \"import json,sys; e=json.load(sys.stdin)[0]['exposicion']; print(e['horas_expuestas'], e['costo_usd'])\"" \
  '^[1-9]'
check "y se explica como AC sin EV (la metrica que Control de Costos mira)" \
  "$E1" 'Valor Ganado'
check "solicitud aprobada sin unidad asignada -> vinculo_no_confirmado" \
  "estado_de SOL-RETRO-SIN-UNIDAD" 'vinculo_no_confirmado'
check "solicitud pendiente sin unidad tambien queda en vinculo" \
  "estado_de SOL-WIRTGEN-SIN-UNIDAD" 'vinculo_no_confirmado'
check_no "Ocupada + Completada NO se marca como riesgo" \
  "estado_de RC03004EC" 'riesgo_critico'
check "Ocupada + Completada se explica como diferencia valida" \
  "estado_de RC03004EC" 'diferencia_valida'
check "Mant. Correctivo con tarea viva SI dispara riesgo_critico" \
  "estado_de RM19003EC" 'riesgo_critico'
check "la decision de si el equipo sale es de Maquinaria, no de Logistica" \
  "$PS/vista-unificada/RM19003EC | python3 -c \"import json,sys; print(json.load(sys.stdin)[0]['area'])\"" \
  '^maquinaria$'
check "el catalogo de estados sale del Modulo 8, no de palabras clave" \
  "$PS/vista-unificada/RM19003EC" 'Mant. Correctivo'
check "el roster agrega el costo expuesto de toda la flota" \
  "$PS/maquinas | python3 -c \"import json,sys; print(sum(m['costo_expuesto_usd'] for m in json.load(sys.stdin)))\"" \
  '^[1-9]'
check "el mapeo nombra la llave real: No. de activo contra Descripcion" \
  "$PS/mapeo | python3 -c \"import json,sys; f=[c for c in json.load(sys.stdin)['campos'] if 'LLAVE' in c['decision']][0]; print(f['nexus'],'|',f['startrack'])\"" \
  'No. de activo | Vehiculos > Descripcion'
check "y distingue el ID remoto, que es un numero de la organizacion" \
  "$PS/mapeo" '78093'
check "y trae los cinco estados del Hub con su accion" \
  "$PS/mapeo | python3 -c \"import json,sys; print(len(json.load(sys.stdin)['estados_hub']))\"" \
  '^5$'

echo "-- Startrack: catalogos reales de su API, cero heuristica"
exposicion_de() {  # maquinaria, campo
  curl -s --max-time 5 "$B/api/ps/vista-unificada/$1" | python3 -c "
import json,sys
e=(json.load(sys.stdin)[0].get('exposicion') or {})
print(e.get('$2'))
"
}

check "el estado de tarea se decide por workflow_role, no por el nombre" \
  "$PS/vista-unificada/RM19003EC | python3 -c \"import json,sys; print(json.load(sys.stdin)[0]['tarea']['workflow_role'])\"" \
  '^0$'
check "la falta de conexion se mide en segundos, no se adivina del texto" \
  "$PS/vista-unificada/EXC-01" '30 h sin reportar'
check "el cruce usa el remote_id que Startrack documenta para eso" \
  "$PS/vista-unificada/EXC-01 | python3 -c \"import json,sys; print(json.load(sys.stdin)[0]['tarea']['remote_id'])\"" \
  '^EXC-17006EC$'
check "mantenimiento reportado por los DOS sistemas a la vez" \
  "$PS/vista-unificada/RM19003EC" 'Las DOS plataformas lo saben'
check "y Startrack lo tiene en su propio catalogo de estado de vehiculo" \
  "$PS/vista-unificada/RM19003EC | python3 -c \"import json,sys; print(json.load(sys.stdin)[0]['tarea']['estado_vehiculo'])\"" \
  '^1$'

echo "-- KPI: horas facturadas (Nexus) contra horas medidas (Startrack)"
check "sin telemetria NO se dice 'midio cero', se dice 'sin datos'" \
  "exposicion_de EXC-01 medicion" 'sin datos'
check "y sin medicion la exposicion es la jornada completa" \
  "exposicion_de EXC-01 horas_sin_respaldo" '^8.0$'
check "EXC-01 sigue anclado en \$1,200 (el numero del guion)" \
  "exposicion_de EXC-01 costo_usd" '^1200.0$'
check "con medicion real, la exposicion se descuenta" \
  "exposicion_de EXC22017LC horas_medidas" '^7.5$'
check "y el equipo conectado casi no expone nada: la KPI no grita lobo" \
  "exposicion_de EXC22017LC horas_sin_respaldo" '^0.5$'
check "el mapeo incorpora los campos de Startrack" \
  "$PS/mapeo" 'ign_on_time'

echo "-- el conector real, apagado: la demo no depende de la red"
check "sin credenciales el Hub lo dice y no se rompe" \
  "curl -s -X POST $B/admin/sync-startrack" 'sin credenciales'
check "y la vista unificada sigue sirviendo la semilla" \
  "estado_de EXC-01" 'alerta_operativa'
check "el tablero declara que los datos son simulados" \
  "$PS/mapeo | python3 -c \"import json,sys; print(json.load(sys.stdin)['origen'])\"" \
  '^simulado$'
check "y lo mismo para Prisma" \
  "$PS/mapeo | python3 -c \"import json,sys; print(json.load(sys.stdin)['origen_prisma'])\"" \
  '^simulado$'
check "sin credenciales de Prisma tampoco se rompe" \
  "curl -s -X POST $B/admin/sync-prisma" 'sin credenciales'

echo "-- webhooks de Startrack: tiempo real, sin polling"
WH="$B/webhooks/startrack"
UB='{"code":3,"vid":1057,"remote_id":"EXC-17006EC","hourmeter":%s,"veh_status":%s,"event_time":"2026-09-13T04:10:00-06:00","placename":"Ahuachapan"}'

check "el rebote de ubicaciones cruza por remote_id" \
  "curl -s -X POST $WH/ubicaciones -H 'content-type: application/json' -d \"\$(printf '$UB' 9000.0 0)\"" \
  '"procesados": *1'
check "la PRIMERA lectura del horometro es linea base, no horas trabajadas" \
  "$PS/vista-unificada/EXC-01 | python3 -c \"import json,sys; e=json.load(sys.stdin)[0]['exposicion'] or {}; print(e.get('horas_medidas'))\"" \
  '^0.0$'
check "la SEGUNDA lectura si mide: 2.5 h contra la base" \
  "curl -s -X POST $WH/ubicaciones -H 'content-type: application/json' -d \"\$(printf '$UB' 9002.5 0)\" >/dev/null; $PS/vista-unificada/EXC-01 | python3 -c \"import json,sys; e=json.load(sys.stdin)[0]['exposicion'] or {}; print(e.get('horas_medidas'))\"" \
  '^2.5$'
check "acepta el formato 2 (lote) que tambien documentan" \
  "curl -s -X POST $WH/ubicaciones -H 'content-type: application/json' -d '[1,[{\"code\":0,\"vid\":939,\"remote_id\":\"EXC22017LC\",\"hourmeter\":1482.0,\"event_time\":\"2026-09-13T08:00:00-06:00\"}]]'" \
  '"procesados": *1'
check "un cuerpo invalido responde 200 y queda contado, nunca 5xx" \
  "curl -s -o /dev/null -w '%{http_code}' -X POST $WH/ubicaciones -H 'content-type: application/json' -d 'no soy json'" \
  '^200$'
check "una alerta de Startrack tambien refresca la tarea" \
  "curl -s -X POST $WH/alertas -H 'content-type: application/json' -d '{\"messageId\":\"enteredPoi\",\"remote_id\":\"EXC-17006EC\",\"ignOnTime\":9003.0,\"vehicle\":\"EXC-01\"}'" \
  '"procesados": *1'
check "las coordenadas escaladas del formato 2 se normalizan a grados" \
  "curl -s -X POST $WH/ubicaciones -H 'content-type: application/json' -d '[1,[{\"code\":0,\"vid\":939,\"remote_id\":\"EXC22017LC\",\"lat\":133376152,\"lon\":-878486967,\"event_time\":\"2026-09-13T09:00:00-06:00\"}]]' >/dev/null; $PS/vista-unificada/EXC22017LC | python3 -c \"import json,sys; t=json.load(sys.stdin)[0]['tarea']; print(round(t['lat'],4), round(t['lon'],4))\"" \
  '^13.3376 -87.8487$'
check "y las decimales del formato 1 pasan intactas" \
  "curl -s -X POST $WH/ubicaciones -H 'content-type: application/json' -d '{\"code\":0,\"vid\":939,\"remote_id\":\"EXC22017LC\",\"lat\":\"13.92\",\"lon\":\"-89.84\",\"event_time\":\"2026-09-13T09:05:00-06:00\"}' >/dev/null; $PS/vista-unificada/EXC22017LC | python3 -c \"import json,sys; t=json.load(sys.stdin)[0]['tarea']; print(t['lat'], t['lon'])\"" \
  '^13.92 -89.84$'
check "un vehiculo que no cruza no rompe nada" \
  "curl -s -X POST $WH/ubicaciones -H 'content-type: application/json' -d '{\"code\":0,\"remote_id\":\"NO-EXISTE-99\"}'" \
  '"procesados": *0'

echo "-- PEA: evidencia sellada y recomputable, sin cadena"
curl -s -X POST "$B/admin/seed-ps" >/dev/null
PEA=$(curl -s -X POST "$B/api/ps/pea/EXC22017LC?aprobado_por=prueba-smoke")

check "el PEA separa lo facturable de la exposicion" \
  "echo '$PEA' | python3 -c \"import json,sys; d=json.load(sys.stdin); print(d['monto_facturable'], d['exposicion_usd'])\"" \
  '1200.0 75.0'
check "y lo aprueba una PERSONA, no el sistema" \
  "echo '$PEA' | python3 -c \"import json,sys; print(json.load(sys.stdin)['aprobado_por'])\"" \
  'prueba-smoke'
check "el hash es sha256, sin dependencias de cadena" \
  "echo '$PEA'" 'sha256:'
check "el registro se puede recomputar y verifica" \
  "curl -s $PS/pea/1/verificar | python3 -c \"import json,sys; print(json.load(sys.stdin)['verifica'])\"" \
  'True'
check "y queda en el log append-only" \
  "curl -s $PS/pea" '"maquinaria": *"EXC22017LC"'

echo "-- sangrado: donde pierde la compania, por area"
check "las tres areas que confirmaron los organizadores" \
  "$PS/sangrado | python3 -c \"import json,sys; print(','.join(a['area'] for a in json.load(sys.stdin)['areas']))\"" \
  '^maquinaria,logistica,proyectos$'
check "Maquinaria ve el equipo detenido con traslado vivo" \
  "$PS/sangrado?area=maquinaria" 'traslado vivo'
check "Logistica ve las solicitudes sin unidad y el tiempo de su gente" \
  "$PS/sangrado?area=logistica" 'horas/semana'
check "Proyectos ve que partidas WBS reciben horas sin respaldo" \
  "$PS/sangrado?area=proyectos" 'Partidas WBS'
check "el filtro por area devuelve una sola" \
  "$PS/sangrado?area=proyectos | python3 -c \"import json,sys; print(len(json.load(sys.stdin)['areas']))\"" \
  '^1$'
check "y un area inventada se rechaza" \
  "curl -s -o /dev/null -w '%{http_code}' '$B/api/ps/sangrado?area=contabilidad'" \
  '^400$'
check "TODO supuesto va declarado como supuesto, nunca como dato" \
  "$PS/sangrado | python3 -c \"
import json,sys
d=json.load(sys.stdin)
malos=[s for s in d['supuestos'].values() if 'supuesto' not in s['fuente']]
print('TODOS DECLARADOS' if not malos else 'HAY SUPUESTOS SIN MARCAR')\"" \
  'TODOS DECLARADOS'
check "y cada cifra derivada dice sobre que base real se calculo" \
  "$PS/sangrado | python3 -c \"
import json,sys
d=json.load(sys.stdin)
faltan=[c['titulo'] for a in d['areas'] for c in a['cifras'] if not c['base_medida']]
print('TODAS CON BASE' if not faltan else faltan)\"" \
  'TODAS CON BASE'

echo "-- conector de Startrack: mapeo de campos, sin tocar la red"
# sincronizar() es el codigo que corre en vivo el dia que pongan credenciales.
# prueba_startrack.py le da una respuesta con la forma exacta de fleet/status
# y verifica que cada campo aterrice donde debe.
check "el mapeo de fleet/status esta verificado campo por campo" \
  "HUB_DB=/tmp/hub-prueba-st-$RUN.db python3 scripts/prueba_startrack.py 2>&1 | tail -1" \
  'mapeo de campos verificado'

echo "-- datos sinteticos: el equipo trabaja sin depender del sandbox"
SIN="$B/api/sintetico"
huella() { curl -s --max-time 10 "$B/api/ps/maquinas" | python3 -c "
import json,sys,hashlib
print(hashlib.sha256(json.dumps(json.load(sys.stdin),sort_keys=True).encode()).hexdigest()[:16])
"; }

curl -s -X POST "$SIN/limpiar" >/dev/null
check "de arranque no hay nada sintetico cargado" \
  "curl -s $SIN/estado | python3 -c \"import json,sys; print(json.load(sys.stdin)['solicitudes_sinteticas'])\"" \
  '^0$'
check "genera el inventario pedido" \
  "curl -s -X POST '$SIN/generar?equipos=40&seed=42'" '"equipos": *40'

H_A=$(huella)
curl -s -X POST "$SIN/limpiar" >/dev/null
curl -s -X POST "$SIN/generar?equipos=40&seed=42" >/dev/null
H_B=$(huella)
curl -s -X POST "$SIN/limpiar" >/dev/null
curl -s -X POST "$SIN/generar?equipos=40&seed=99" >/dev/null
H_C=$(huella)

check "mismo seed = mismos datos (si no, los bugs no se reproducen)" \
  "echo '$H_A vs $H_B'" "$H_A vs $H_A"
check_no "seed distinto = datos distintos" \
  "echo '$H_A|$H_C'" "^$H_A|$H_A\$"
check "respeta la proporcion del Modulo 8: ~1 de cada 5 en correctivo" \
  "python3 -c \"
import sqlite3, collections
c = sqlite3.connect('backend/hub.db'); c.row_factory = sqlite3.Row
f = c.execute('SELECT estado_maquinaria e FROM ps_solicitudes WHERE sintetico=1').fetchall()
n = collections.Counter(r['e'] or 'sin' for r in f)
pct = 100 * n['Mant. Correctivo'] / max(1, sum(n.values()))
print('PROPORCION OK' if 12 <= pct <= 30 else f'FUERA DE RANGO: {pct:.0f}%')\"" \
  'PROPORCION OK'
check "solo genera clases del catalogo oficial del Diccionario de Datos" \
  "python3 -c \"
import sqlite3
oficial = {'Excavadora','Retroexcavadora','Motoniveladora','Minicargador','Cargador frontal'}
c = sqlite3.connect('backend/hub.db'); c.row_factory = sqlite3.Row
f = c.execute('SELECT DISTINCT clase_equipo e FROM ps_solicitudes WHERE sintetico=1').fetchall()
fuera = {r['e'] for r in f} - oficial
print('SOLO OFICIALES' if not fuera else f'INVENTADAS: {fuera}')\"" \
  'SOLO OFICIALES'
check "el ejemplo de webhook sale armado y listo para disparar" \
  "curl -s $SIN/webhook-ejemplo/EXC-17006EC" '"hourmeter"'
check "y ese ejemplo de verdad funciona contra el webhook" \
  "curl -s $SIN/webhook-ejemplo/EXC-17006EC | python3 -c \"
import json,sys,urllib.request
p = json.load(sys.stdin)['payload']
r = urllib.request.urlopen(urllib.request.Request(
    '$B/webhooks/startrack/ubicaciones', method='POST',
    data=json.dumps(p).encode(), headers={'content-type':'application/json'}))
print(json.load(r)['procesados'])\"" \
  '^1$'

curl -s -X POST "$SIN/limpiar" >/dev/null
check "limpiar borra lo generado" \
  "curl -s $SIN/estado | python3 -c \"import json,sys; print(json.load(sys.stdin)['tareas_sinteticas'])\"" \
  '^0$'
check "pero NO toca las filas de la demo" \
  "curl -s $SIN/estado | python3 -c \"import json,sys; d=json.load(sys.stdin); print(d['solicitudes_reales'], d['tareas_reales'])\"" \
  '^6 4$'
curl -s -X POST "$B/admin/seed-ps" >/dev/null
check "y EXC-01 sigue anclado en \$1,200 despues de todo el ciclo" \
  "exposicion_de EXC-01 costo_usd" '^1200.0$'

echo "-- cierre: los numeros cuadran con el documento"
check "beneficio \$228,000"     "curl -s $B/api/analytics" '"beneficio_total":228000'
check "30,000 galones evitados" "curl -s $B/api/analytics" '"galones_evitados":30000'

echo "-- Command Center"
check "flota expuesta"       "curl -s $B/api/assets" 'asset_identifier'
check "contrato expuesto"    "curl -s $B/api/contract" 'precedencia'
check "cargas expuestas"     "curl -s $B/ingest/cargas" 'lote'
check "nodos tipados"        "curl -s $B/api/projects" 'planta_concreto'
check "PWA de campo servida" "curl -s $B/campo/" 'Captura de campo'

echo "-- servido en un solo proceso (esto es lo que significa desplegar)"
check "la raiz devuelve la aplicacion, no un JSON de instrucciones" \
  "curl -s $B/" 'id="root"'
# La que hubiera cazado el bug: el HTML compilado pide sus assets en la raiz,
# y por un tiempo solo estaban montados bajo /app. Cargaba y se caia en blanco.
check "y CADA asset que ese HTML pide responde 200" \
  "python3 -c \"
import re, urllib.request
html = urllib.request.urlopen('$B/').read().decode()
assets = re.findall(r'/assets/[^\\\"]+', html)
if not assets:
    print('NINGUN ASSET EN EL HTML')          # vacuo = falla, no pasa de largo
else:
    malos = []
    for a in assets:
        try:
            malos += [] if urllib.request.urlopen('$B' + a).status == 200 else [a]
        except Exception as e:
            malos.append(f'{a} ({e})')
    print(f'{len(assets)} ASSETS OK' if not malos else f'ROTOS: {malos}')\"" \
  '^[0-9]\+ ASSETS OK$'
check "la aplicacion tambien responde por /app" \
  "curl -s -o /dev/null -w '%{http_code}' $B/app/" '^200$'
check "y la PWA de campo sigue en su ruta" \
  "curl -s -o /dev/null -w '%{http_code}' $B/campo/" '^200$' 

echo
if [ "$fallo" -eq 0 ]; then
  printf '\033[32m%s pruebas OK. La ruta de la demo esta viva.\033[0m\n' "$ok"
else
  printf '\033[31m%s OK, %s FALLAN. Arreglar antes de seguir.\033[0m\n' "$ok" "$fallo"
  exit 1
fi
