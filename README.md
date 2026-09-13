# Hub de Operaciones — Grupo ECON

Integrador de silos para la logística de maquinaria pesada.
Reto Grupo ECON · **Entropy Hack** · Key Institute, El Salvador.

El Hub no reemplaza los sistemas de ECON: los **traduce**. Telemetría OEM
(Caterpillar, Komatsu, Volvo), módulos retrofit sobre bus CAN J1939 y los
canales de campo que la gente ya usa (WhatsApp) entran por la misma puerta y
salen con la misma forma: un contrato canónico basado en **ISO 15143-3 / AEMP 2.0**.

---

## Arranque en 3 minutos

```bash
# 1. Backend (siembra la flota automáticamente en el primer arranque)
./backend/run.sh
#    -> http://127.0.0.1:8000        API + docs en /docs
#    -> http://127.0.0.1:8000/campo  PWA de captura offline

# 2. Command Center (en otra terminal)
cd frontend && npm install && npm run dev
#    -> http://localhost:5173

# 3. Telemetría en vivo, para que el mapa no se vea estático (otra terminal)
cd backend && source .venv/bin/activate && python -m app.seed.simulate --intervalo 3
```

### Antes de correr `scripts/smoke.sh` en un clon nuevo

```bash
cd frontend && npm install && npm run build
```

`frontend/dist/` está en `.gitignore` porque es artefacto de compilación, así
que un clon recién bajado no lo tiene. Sin ese build, `./backend/run.sh --prod`
sirve un JSON en la raíz en vez del Command Center, y el smoke reporta **3
fallos** que no son tales:

```
la raiz devuelve la aplicacion, no un JSON de instrucciones
y CADA asset que ese HTML pide responde 200
la aplicacion tambien responde por /app
```

Con el build hecho: **107 OK**.

### Los endpoints que mutan piden token cuando la API está expuesta

```bash
export HUB_ADMIN_TOKEN=<el que esté en backend/.env>
./scripts/smoke.sh
```

Sin esta variable, los `POST /admin/*` responden `401` y el smoke falla en
bloque. Ver `backend/.env.example`.

Sin llaves de API el sistema **funciona completo**: la transcripción usa audios
sembrados, el NER usa un extractor por reglas (saca 4 520 h de «cuatro mil
quinientas veinte») y el OCR devuelve una lectura determinista. Con
`MIMO_API_KEY` en `backend/.env` se activan los caminos de IA reales. Esa es la
red de seguridad para la demo: el wifi del salón no puede tumbarnos.

**Verificar siempre las dos rutas:**

```bash
MIMO_API_KEY=... ./scripts/smoke.sh   # con IA real
MIMO_API_KEY=     ./scripts/smoke.sh   # con los respaldos por reglas
```

---

## Estructura

```
backend/
  app/
    canonical.py         CONTRATO CANÓNICO + precedencia por campo   [CONGELADO 08:30]
    orchestrator.py      proyección, gobernanza, reglas, estado, SSE
    db.py  events.py     SQLite + log append-only + bus en memoria
    adapters/            cat · komatsu · volvo · j1939   (un archivo por fuente)
    rules/               maintenance (240/250 h) · idle (15 min) · fuel (5 %)
    dispatch/vmt.py      motor de veda del VMT en el AMSS
    ai/                  provider (MiMo) · stt · ner · ocr  (+ respaldo offline)
    ingest/              telemetry · whatsapp (webhook real + simulador)
    api/                 assets · stream (SSE) · connectors · dispatch · analytics
    seed/                flota sintética · emisor de telemetría
frontend/                Command Center (React + Vite + Leaflet)
field-pwa/               captura offline (IndexedDB + cola idempotente)
CLAUDE.md                brief para sesiones de IA — LEER PRIMERO
ROADMAP.md               lo que no entró hoy, y la diapositiva de cierre
docs/ESTADO.md           estado vivo + bitácora — SE ACTUALIZA TODO EL DÍA
docs/                    CONTRATO · DATA · DEMO · PLAN · mimo-spike
scripts/smoke.sh         22 aserciones de la ruta de la demo
scripts/bitacora.sh      anota un cambio y estampa el resultado de las pruebas
```

## Dueños

| Área | Dueño | Ventana |
|---|---|---|
| Contrato canónico, adaptadores, datos maestros, matriz VMT | **Emily** | 08:00–15:00 |
| Columna vertebral, WhatsApp, IA, orquestador, reglas | **Wilbert** | 08:00–20:00 |
| Command Center, PWA de campo, procedencia, conectores | **Majo** | 08:00–20:00 |
| Integración E2E, guion, pitch, ensayos, video | **Josué** | 15:00–20:00 |

## Reglas del día

1. **La ruta de la demo es sagrada.** Si un bug no aparece en los tres minutos del guion, va al backlog.
2. **El contrato canónico se congela a las 08:30.** Cambiarlo después requiere acuerdo de los presentes.
3. **Un commit cada 30 minutos.** Nada vive solo en una laptop.
4. **Nadie refactoriza después de las 17:00.** El código va a estar feo y está bien.
5. **Prohibido decir «ya casi».** A cada hito se responde con lo que corre en pantalla.

## Endpoints que importan

| Método | Ruta | Para qué |
|---|---|---|
| POST | `/ingest/telemetry/{cat\|komatsu\|volvo\|j1939}` | telemetría en forma propietaria |
| POST | `/ingest/events` | quien ya habla canónico (PWA) |
| POST | `/ingest/whatsapp/sim` | simulador de campo: voz + foto → evento |
| GET | `/ingest/whatsapp` | handshake de verificación de Meta |
| GET | `/api/stream` | SSE en vivo (`asset`, `event`, `alert`, `dispatch`) |
| GET | `/api/assets` · `/api/assets/{id}` | flota y ficha con procedencia |
| GET | `/api/connectors` · `/api/contract` | salud de la integración |
| POST | `/api/dispatch` | traslado: aptitud + ETA + veda VMT |
| GET | `/api/analytics` | modelo de ROI e impacto de la sesión |
| POST | `/api/assets/{id}/servicio` | el taller cierra el mantenimiento |
| POST | `/admin/reset` · `/admin/seed` | limpiar entre ensayos |

## Decisiones tomadas y por qué

| En el documento | Aquí | Razón |
|---|---|---|
| Kafka / RabbitMQ | tabla `events` + bus en memoria | el broker es despliegue; el contrato es la tesis |
| TimescaleDB | SQLite (SQL plano, migrable) | cero setup en cuatro laptops a las 08:00 |
| Temporal.io | máquina de estados en Python | la orquestación ya está modelada |
| CRDTs completos | log de mutaciones + precedencia por campo | converge determinista; el CRDT de conjuntos es roadmap |
| ESP32 físico | simulador J1939 (SPN 247/250, DM1) | lo que probamos es que el Hub no distingue el origen |
| Mapbox GL JS | Leaflet + OpenStreetMap | sin token, sin facturación, mismo resultado |
| Apache Superset | vista de analítica | el jurado quiere el número, no un BI configurado |
| Anthropic / OpenAI | **Xiaomi MiMo** | es la llave que tiene el equipo |

**No vendas lo que no está.** Los CRDTs y el retrofit físico son roadmap
(`ROADMAP.md`); decirlo así suma credibilidad, presentarlos como hechos la
destruye en la primera pregunta.

## Si eres una sesión de IA

Lee `CLAUDE.md` completo y después `docs/ESTADO.md`. Al terminar cualquier
cambio: `./scripts/bitacora.sh "qué cambiaste"`.
