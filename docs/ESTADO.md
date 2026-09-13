# Estado vivo

> Única fuente de verdad del avance. Lee esto al entrar, actualízalo al salir.
> Para anotar: `./scripts/bitacora.sh "lo que cambiaste"` — corre `smoke.sh` y
> estampa el resultado solo.

**Última actualización:** 2026-09-12 23:13 SV
**Pruebas de humo:** 104 pruebas OK

---

## Hitos

| Hito | Hora | Criterio | Estado |
|---|---|---|---|
| **M1** | 10:30 | Un evento entra por HTTP y aparece en el mapa, de punta a punta | ✅ **adelantado** — el andamiaje ya lo cubre |
| **M2** | 13:00 | Mensaje de WhatsApp → evento canónico → marcador rojo | ✅ **adelantado** (con respaldo por reglas) · falta con IA real |
| **M3 (nuevo)** | 15:48 | Prisma + Startrack: los 3 casos oficiales correlacionados | ✅ **listo** |
| **M3b** | 17:10 | Anclado al manual de Nexus: catálogo real, No. de activo, KPI en dólares | ✅ **listo** — y se lleva los **tres** minutos del guion |
| **M3c** | 20:50 | Anclado a la API de Startrack: cero heurística en el motor, horas medidas | ✅ **listo** |
| **Congelamiento** | 17:00 | Cero funciones nuevas, cero refactors | ⏳ |
| **M4** | 19:00 | Tres ensayos cronometrados + video de respaldo | ⏳ |

M1 y M2 salieron adelantados porque el andamiaje ya traía la ruta completa
funcionando con los respaldos. **El tiempo ganado va a IA real y a ensayos, no
a alcance nuevo.**

---

## Emily · 08:00 – 15:00

- [ ] **Alta en Meta / WhatsApp Business** — timebox duro, decisión 09:15
  - [ ] cuenta de negocio y número de prueba
  - [ ] registrar los 5 números del equipo (el número de prueba solo manda a esos)
  - [ ] `WA_ACCESS_TOKEN` y `WA_PHONE_NUMBER_ID` en `backend/.env`
  - [ ] webhook verificado contra `GET /ingest/whatsapp`
- [ ] Verificar coordenadas de obras contra `econ.com.sv` → `seed/fleet.py:9`
- [ ] Verificar la matriz real de veda del VMT → `dispatch/vmt.py:9`
- [ ] Ampliar el catálogo de modelos con el equipo real de ECON
- [x] **`docs/DATA.md` llenado** con el Diccionario de Datos oficial

## Wilbert · 08:00 – 20:00

- [x] Columna vertebral: API, log de eventos, SSE, orquestador
- [x] Contrato canónico con precedencia por campo y tickets de conciliación
- [x] Reglas: mantenimiento 240/250 h · ralentí 15 min · diésel 5 %
- [x] Capa de IA reescrita para MiMo (`ai/provider.py`)
- [ ] **Spike de MiMo — 4 curl, bloqueante** → `docs/mimo-spike.md`
- [ ] Ajustar `ai/provider.py` con lo que salga del spike
- [ ] Bajar media (audio y foto) del webhook de Meta → `ingest/whatsapp.py:226`
- [ ] Probar transcripción con la voz de Josué (15:00, no a las 19:00)

## Majo · 08:00 – 20:00

- [x] Command Center: mapa en vivo por SSE, fichas, feed, chips de procedencia
- [x] Panel de conectores, despacho con barra de veda, tablero de ROI
- [x] PWA de campo con cola en IndexedDB e idempotencia
- [ ] Leer el repo, `npm install`, correr todo y confirmar que se ve
- [ ] Input de archivo real para la foto del tablero → `FieldSim.jsx:27`
- [ ] Botón de cerrar servicio en la ficha (el endpoint ya existe)
- [ ] Pulido visual (después de las 17:00, no antes)

## Josué · 15:00 – 20:00

- [ ] Integración de punta a punta y siembra del escenario
- [x] Guion de 3 minutos reescrito (`docs/DEMO.md`) — síntoma / causa / costo
- [ ] Leerlo en voz alta y ajustar tiempos: sobra o falta texto, se sabe ensayando
- [ ] Deck ejecutivo + números de ROI
- [ ] Video de respaldo grabado (19:00)
- [ ] Tres ensayos cronometrados

---

## Bloqueos abiertos

| Bloqueo | Espera | Quién |
|---|---|---|
| IA real (NER, OCR, voz) | el spike de MiMo y la llave en `backend/.env` | Wilbert |
| Nota de voz real en la demo | decisión de Meta a las 09:15 | Emily |
| Coordenadas y horarios del VMT verificados | revisión contra fuentes reales | Emily |
| Congelamiento corrido más allá de las 17:00 originales | el pivote de Prisma+Startrack de las 15:48 | todos |
| Ensayar el guion nuevo completo (3 min, Prisma+Startrack) | que Josué lo lea en `docs/DEMO.md` | Josué |
| Encender el conector real de Startrack | el API key (admin de usuarios → «Integraciones (API)») | Josué |
| Confirmar que la hipótesis del rezago del EV se dice **como hipótesis** | ensayo cronometrado | Josué |

---

## Bitácora

<!-- Lo más nuevo arriba. Formato: HH:MM · quién · qué · smoke -->

- **23:13 · Claude** · sincronizacion por fleet/status (1 peticion en vez de 241) + prueba del mapeo sin red · **smoke 104 pruebas OK**

- **23:06 · Claude** · verificado el frontend en navegador real: arreglada la legibilidad de los campos, favicon, y .env.example con las 6 variables · **smoke 103 pruebas OK**

- **23:02 · Claude** · alineado al Diccionario de Datos oficial: llave real, catalogo de 5 clases y bug de coordenadas escaladas · **smoke 103 pruebas OK**

- **22:34 · Claude** · panel por area, sello PEA en pantalla, y el Hub servido en un solo proceso (arreglado el 404 de assets) · **smoke 99 pruebas OK**

- **22:25 · Claude** · correccion: las tres areas son Maquinaria, Logistica y Proyectos (no el desglose que habia asumido) · **smoke 95 pruebas OK**

- **22:18 · Claude** · generador de datos sinteticos determinista + API para que el equipo trabaje sin el sandbox · **smoke 93 pruebas OK**

- **22:08 · Claude** · webhooks de Startrack en tiempo real, PEA sin cadena, y sangrado por rol (logistica / mantenimiento / administracion) · **smoke 83 pruebas OK**

- **20:50 · Claude** · lado Startrack anclado a su API real: workflow_role, coms_age, estado de vehiculo, KPI facturado vs medido y conector apagado por defecto · **smoke 63 pruebas OK**

- **17:06 · Claude** · panel, mapeo de campos y guion nuevo de 3 minutos anclados al manual de Nexus · **smoke 49 pruebas OK**

- **16:32 · Claude** · columnas de conexion/ultimo evento/identificador_raw en ps_tareas + migracion para bases ya existentes · **smoke 39 pruebas OK**

- **16:01 · Claude** · Pivote: Prisma + Startrack reemplaza el minuto 3, sobre los 3 casos oficiales del sandbox · **smoke 39 pruebas OK**

- **08:31 · Claude** · claves de idempotencia unicas por corrida en smoke.sh (con claves fijas la segunda corrida fallaba sola) + check_no · **smoke 22 pruebas OK**

- **08:30 · Claude** · memoria del repo: CLAUDE.md, docs/ESTADO.md, ROADMAP.md, docs/mimo-spike.md y scripts/bitacora.sh · **smoke ⚠️ 21 OK, 1 FALLAN**

- **08:25 · Claude** · Capa de IA migrada de Anthropic a MiMo (`ai/provider.py` nuevo,
  `ner/ocr/stt` reescritos con las firmas intactas). `mimo-v2.5` acepta audio, así
  que la misma llave cubre transcripción: se elimina el proveedor de voz aparte.
  Cerrados dos huecos del andamiaje: `rules/fuel.py` **nunca se invocaba** (la
  tolerancia del 5 % era código muerto) y `EN_MANTENIMIENTO` solo se leía, nunca
  se escribía. Nuevo `POST /api/assets/{id}/servicio` para que el taller cierre.
  Corregidos dos bugs propios: el seed sorteaba el combustible dos veces (la base
  del ciclo de abastecimiento salía absurda) y la API aceptaba
  `asset_identifier` vacío, creando activos fantasma. · **smoke 22/22**
- **07:55 · Claude** · Andamiaje inicial: contrato canónico, 4 adaptadores,
  pipeline de campo, motor de veda del VMT, Command Center, PWA offline, flota
  sintética de 150 unidades. · **smoke 18/18**
