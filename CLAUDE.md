# Brief para sesiones de IA — Hub de Operaciones ECON

Si eres una sesión de IA entrando a este repo, **lee esto completo antes de
tocar nada**, y después lee `docs/ESTADO.md` para saber en qué punto va el día.

## Lo primero y lo último

1. **Al entrar**: leer `docs/ESTADO.md` (estado vivo + bitácora + bloqueos).
2. **Al terminar cualquier cambio**: correr `./scripts/smoke.sh` y anotar con
   `./scripts/bitacora.sh "qué cambiaste"`. No es opcional. Si no queda en la
   bitácora, el siguiente que entre no lo sabe y lo va a rehacer.

## Pivote de las 15:48 — Prisma + Startrack, y el manual de Nexus

El equipo recibió `Entropy_Hack_Grupo_ECON_Casos_de_Uso_Final.docx`: la
especificación oficial del sandbox, con dos plataformas concretas — **Prisma**
(solicitudes y estado del recurso) y **Startrack** (tareas de traslado).
Después llegó el **manual de usuario de Nexus ECON**, que documenta el sistema
real módulo por módulo. **Prisma y Nexus son el mismo sistema**: la
especificación lo llama Prisma, el manual lo llama Nexus, y la interfaz dice
«Prisma / Nexus» para que el jurado lo reconozca con cualquiera de los dos
nombres. En el código el prefijo sigue siendo `ps_` / `/api/ps/`.

**Los tres minutos del guion van completos a esta integración.** El minuto de
WhatsApp salió del guion escrito. Ver `docs/PRISMA_STARTRACK.md` y
`docs/DEMO.md`.

Y después llegó la **documentación de la API de Startrack** (38 páginas). Entre
los dos, este módulo pasó de heurística a catálogo: **hoy `correlacion.py` no
adivina nada, los dos lados del cruce son catálogos oficiales.** No vuelvas a
adivinar lo que ya está documentado:

- El estado del recurso es un **catálogo cerrado** de Módulo 8 — Disponible,
  Ocupada, Mant. Preventivo, Mant. Correctivo, Obsoleta. Lo que se normaliza
  es la ortografía, no el catálogo.
- Hay **dos identificadores**: `Clave` (`EQ142`, logística interna) y
  `No. de activo` (`EXC22017LC`, contable). **La llave de cruce con Startrack
  es el No. de activo**, no la Clave.
- La tarifa existe: `precio_hora` y `horas_minimas` (8.00) de Módulo 8. La KPI
  se expresa en dólares, no en horas abstractas.
- Nexus **ya bloquea** solicitar un equipo en mantenimiento
  (`TRANSIT_EQUIPMENT_IN_MAINTENANCE`). Nuestro caso de riesgo es el cambio de
  estado **después** de aprobada la solicitud. No lo presentes como si su
  sistema no validara nada: se cae en tres segundos.
- Lo del rezago del EV (CPI saltando de 0.51 a 4.44) es **hipótesis nuestra**,
  no una afirmación del manual. Se dice así, siempre.

**Y llegó el Diccionario de Datos oficial** (`docs/DATA.md`). Es la fuente
contra la que evalúan, y corrigió tres cosas nuestras:

- **La llave es `No. de activo` ↔ `Vehículos > Descripción`**, el código corto
  del equipo. **`ID remoto` NO es el activo fijo**: el diccionario lo
  ejemplifica como `78093`, un número de la organización. Lo afirmábamos mal
  en el guion.
- **Clase de equipo son cinco y nada más**: Excavadora, Retroexcavadora,
  Motoniveladora, Minicargador, Cargador frontal. El generador sintético solo
  produce esas.
- **Las coordenadas vienen escaladas por 1e7** (`133376152` = 13.3376152) en
  las geocercas y en el formato 2 del rebote. `_coord()` lo normaliza. Era un
  bug real: mandaba los equipos a cien millones de grados.

Del lado de Startrack (`docs/PRISMA_STARTRACK.md` tiene las citas textuales):

- `remote_id` existe en la API y acepta letras, números y `- _ ( ) :`, y se
  consulta con `GET /api/vehicle/<id>?is_remote_id=true`. **Pero no es la
  llave del sandbox** — ver arriba. Es donde se pondría el No. de activo en
  una implementación real. El motor busca por las tres llaves.
- El estado de tarea se decide por **`workflow_role`** (`0` pendiente, `1`
  completada, `2` cancelada), nunca por el nombre: el nombre es libre y el rol
  no. Un estado personalizado sin rol se trata como desconocido, no se adivina.
- Startrack lleva **su propio estado de vehículo** (`0..4`). El `3` es el
  rastreador averiado, no la máquina: no bloquea operar.
- La falta de conexión se decide con **`coms_age`** (segundos). El umbral
  (`HUB_STARTRACK_UMBRAL_CONEXION`, default una jornada) **sí es criterio
  nuestro** y va marcado como tal.
- **`ign_on_time` sí, `ign_on_hrs` no.** El segundo trae 100.8 "horas" en un
  solo día en su propio ejemplo: parece horómetro acumulado. Sin verificar
  contra un tenant real, no se usa.
- **API key:** administrador de usuarios → pestaña *"Integraciones (API)"*. La
  contraseña es **la misma del login normal**. Límite de 240 peticiones cada
  2 minutos, y `/api/devices` solo 10 cada 5 minutos.
- **Se sincroniza con `GET /api/fleet/status`: UNA llamada para toda la
  flota.** Trae `vehId`, `vehDescr` (donde vive el código del equipo),
  `vehStat`, `x`/`y`, `epoch`, `eventDescription` e `ignOnHrs`. No vuelvas a
  pedir `/api/vehicle/<id>` uno por uno: con 120 equipos son 241 peticiones
  contra un límite de 240 cada 2 minutos y se autobloquea. `epoch` da la
  recencia, así que tampoco hace falta `/api/devices` (10 cada 5 min).
- **`x` es longitud e `y` es latitud**, no al revés. Y `ignOnHrs` es
  acumulado, igual que `hourmeter`.
- **`ignOn` no se usa.** En el propio ejemplo de la documentación un vehículo
  «en movimiento» trae `ignOn: 0` y otro con «ignition off» trae `ignOn: 1`.
- `scripts/prueba_startrack.py` verifica el mapeo completo **sin red**, con
  una respuesta calcada de su documentación. Si tocás `sincronizar()`, eso es
  lo que te avisa.
- El conector está **apagado por defecto** y el tablero declara en pantalla si
  los datos son `en vivo` o `simulados`. No lo enciendas sin verlo funcionar
  en un ensayo.

El trabajo anterior (WhatsApp, telemetría OEM, concreto perecedero) sigue
construido y probado — no se borró nada, sigue en `smoke.sh` y en sus
pestañas. Si vas a tocar `correlacion.py`, `api/prisma_startrack.py` o
`seed/prisma_startrack.py`: son nuevos, dueño Wilbert, y el patrón de
`docs/PRISMA_STARTRACK.md` explica el porqué de cada decisión.

## Las tres áreas — confirmado con los organizadores

**Maquinaria · Logística · Proyectos.** Tres áreas, tres pérdidas distintas,
tres pantallas distintas. Un tablero que les muestra lo mismo a las tres no le
sirve a ninguna. Ver `docs/SANGRADO.md` y `GET /api/ps/sangrado?area=...`.

Los cinco estados del Hub escalan a esas mismas áreas (`area` en cada
operación). **La decisión de si un equipo sale es de Maquinaria**, no de
Logística: Logística ejecuta el traslado pero no autoriza una máquina
averiada. Proyectos no recibe alertas operativas — recibe el costo.

**Regla que no se negocia:** los conteos salen de la base y son auditables.
Los costos unitarios son **supuestos nuestros** y viajan marcados como tales,
con su base medida al lado. No inventamos el costo-hora de ECON: lo dejamos
configurable para poder decirle al jurado «cambiame este número».

## Datos sintéticos para el equipo

`POST /api/sintetico/generar?equipos=120&seed=42`. Ver `docs/SINTETICO.md`.

- **Determinista**: mismo seed, mismos datos. **Si reportás un bug, reportá el
  seed** — sin eso nadie reproduce tu pantalla.
- Todo lleva `sintetico = 1` y `POST /api/sintetico/limpiar` lo borra sin
  tocar las seis filas de la demo.
- La proporción de estados es la **real** del Módulo 8 (1 de cada 5 en
  Mant. Correctivo). Los nombres, tarifas y horómetros son inventados.
- ⚠️ **Nunca cites un agregado sintético como pérdida real de ECON.** Para el
  pitch se usa la semilla de seis filas, que sí sale de sus documentos.

## PEA — sin cadena, desde el 13/09

Se eliminó la capa on-chain. El escrow con RPC y llaves privadas es ahora un
**Protocolo de Ejecución Automatizada**: evidencia sellada con SHA-256 sobre
una forma canónica, guardada append-only en `pea_registros`. Ver `docs/PEA.md`.

- La respuesta a *«sin cadena, ¿por qué te creo el hash?»* es que **es
  recomputable** desde Nexus y Startrack. No hay que confiar en el Hub.
- `aprobado_por` es **siempre una persona**. Automatizamos la evidencia, no
  la decisión. Decirlo así importa: «ejecución automatizada» a un CFO le
  suena a que se paga solo.
- `monto_facturable` y `exposicion_usd` son cosas distintas y en EXC-01
  coinciden en $1 200. Etiquetarlos sin ambigüedad o se confunden en vivo.
- Si cambia `_canonico()` en `pea.py`, **todos los hashes emitidos dejan de
  verificar**.

## Webhooks de Startrack — tiempo real, sin polling

`POST /webhooks/startrack/ubicaciones` y `/alertas`. El rebote trae
`remote_id`, `hourmeter`, `ign_on` y `veh_status`: todo lo que el motor
necesita, empujado, sin gastar el límite de 240 peticiones.

- **`hourmeter` es el horómetro ACUMULADO de toda la vida del equipo**, no las
  horas de la jornada. Las horas del periodo son la diferencia contra
  `horometro_base`, que se fija con la primera lectura. Ya caímos en ese error
  una vez; no lo repitas.
- Los webhooks **nunca devuelven 4xx/5xx**. Un webhook que falla hace que la
  plataforma reintente o deshabilite el rebote. Se responde 200 con el detalle
  y queda contado en `connector_stats`.

## Qué es esto

Hackatón de 12 horas (Entropy Hack, Key Institute, El Salvador). Reto de Grupo
ECON: los silos de información paralizan la logística de maquinaria pesada.

**El Hub no reemplaza los sistemas de ECON: los traduce.** Telemetría OEM
(Caterpillar, Komatsu, Volvo), módulos retrofit sobre bus CAN J1939 y los
canales que la gente ya usa (WhatsApp) entran por la misma puerta y salen con
la misma forma: un contrato canónico basado en ISO 15143-3 / AEMP 2.0.

El reto nombra tres fricciones y las tres tienen que quedar cubiertas:
estructura de datos, procesos, y **responsables de la información** — esta
última es la que casi todos ignoran y la que resolvemos con precedencia por
campo. No la sacrifiques cuando recortes alcance.

## Arrancar y verificar

```bash
./backend/run.sh --prod                             # DEMO: todo en :8000, un proceso
./backend/run.sh                                    # dev: API en :8000, PWA en /campo
cd frontend && npm install && npm run dev           # Command Center en :5173
cd backend && python -m app.seed.simulate --intervalo 3   # telemetría en vivo
./scripts/smoke.sh                                  # 104 aserciones
```

**`smoke.sh` tiene que quedar verde con Y sin `MIMO_API_KEY`.** Los respaldos
por reglas son la red de seguridad contra el wifi del salón; si un cambio los
rompe, el cambio está mal, no el respaldo.

## Dueños — no edites fuera de tu carril sin avisar

| Área | Archivos | Dueño |
|---|---|---|
| Contrato, adaptadores, datos maestros, matriz VMT | `canonical.py`, `adapters/`, `seed/fleet.py`, `dispatch/vmt.py` | **Emily** (hasta 15:00) |
| Columna vertebral, IA, orquestador, reglas | `main.py`, `orchestrator.py`, `ai/`, `ingest/`, `rules/` | **Wilbert** |
| Prisma + Startrack | `correlacion.py`, `startrack.py`, `prisma.py`, `api/prisma_startrack.py`, `seed/prisma_startrack.py` | **Wilbert** |
| PEA, sangrado y webhooks | `pea.py`, `sangrado.py`, `ingest/startrack_webhook.py` | **Wilbert** |
| Datos sintéticos | `seed/sintetico.py`, `api/sintetico.py` | **Wilbert** |
| Command Center y PWA | `frontend/`, `field-pwa/` | **Majo** |
| Integración, guion, pitch | `docs/DEMO.md` | **Josué** (desde 15:00) |

## Reglas del día

1. **La ruta de la demo es sagrada.** Si un bug no aparece en los tres minutos
   de `docs/DEMO.md`, va al backlog. Nadie gana puntos por código que el jurado
   no ve.
2. **El contrato canónico está congelado** (`canonical.py`, desde las 08:30).
   Cambiarlo rompe trabajo de los otros tres: avisar en voz alta y actualizar
   `docs/CONTRATO.md` en el mismo commit.
3. **Un commit cada 30 minutos.** Nada vive solo en una laptop.
4. **Nadie refactoriza después de las 17:00.** El código va a estar feo en la
   entrega y está bien.
5. **Prohibido decir «ya casi».** A cada hito se responde con lo que corre en
   pantalla.

## Decisiones ya tomadas — no las vuelvas a discutir

| En el documento base | Aquí | Por qué |
|---|---|---|
| Kafka / RabbitMQ | tabla `events` + bus en memoria | el broker es despliegue; el contrato es la tesis |
| TimescaleDB | SQLite con SQL plano | cero setup en cuatro laptops a las 08:00 |
| Temporal.io | máquina de estados en Python | la orquestación ya está modelada |
| CRDTs completos | log de mutaciones + precedencia por campo | converge determinista; el CRDT de conjuntos es roadmap |
| ESP32 físico en bus CAN | simulador J1939 | sin excavadora ni permiso de ECON no hay forma; y no es la parte difícil |
| Mapbox GL JS | Leaflet + OpenStreetMap | sin token, sin facturación, sin registro |
| Apache Superset | una vista de analítica | el jurado quiere el número, no un BI |
| Anthropic / OpenAI | **Xiaomi MiMo** | es la llave que tiene el equipo |

## Qué NO se le dice al jurado

- **No** decir que usamos CRDTs. Usamos un log de mutaciones con precedencia
  por campo, que converge determinista. Si alguien pregunta por relojes
  vectoriales y no los tenemos, se cae toda la credibilidad ganada.
- **No** presentar el retrofit J1939 como hardware real en operación. Es
  simulador, y el hardware es commodity de $40. Decirlo así suma.
- **No** inventar datos regulatorios. Los horarios de veda del VMT están
  marcados como pendientes de verificar en `dispatch/vmt.py`. Un dato inventado
  sobre su propio país lo detecta un juez de ECON en tres segundos.

## Trampas ya descubiertas — no las repitas

- **La veda del VMT corre de lunes a viernes.** Si ensayas en fin de semana el
  motor responde «ventana libre» y el minuto 3 no dispara. Pide el traslado
  para un día hábil, o usa `HUB_DEMO_WEEKDAY`.
- **Los números del tablero tienen que cuadrar con el pitch.** Están fijados a
  los del documento: $228 000/año, 30 000 galones, ROI 2.5 meses. Si cambias un
  parámetro en `api/analytics.py`, cambia también `docs/DEMO.md`.
- **MiMo no fuerza el esquema del JSON**, solo el formato. Toda respuesta se
  valida con Pydantic en `ai/provider.py`. No quites esa validación.
- **`mimo-v2.5-pro` es solo texto; `mimo-v2.5` es el omnimodal.** El primero
  acepta `response_format`, el segundo no. Ya está repartido así en `ai/`.
- **El `index.html` de Vite pide sus assets en la raíz** (`/assets/...`), no
  bajo el mount. Si solo se monta `/app`, la página carga y se queda **en
  blanco** con 404 en el JS y el CSS. No se nota con `npm run dev` — y
  desplegar es correr sin el dev server. `main.py` monta `/assets` aparte y
  hay una aserción probada contra el bug. Si cambiás el `base` de Vite, esa
  aserción es la que avisa. Ver `docs/DESPLIEGUE.md`.
- **Un `asset_identifier` vacío creaba activos fantasma.** Ya hay `min_length=1`
  en `canonical.py`; no lo relajes.

## Convenciones de código

- Comentarios y nombres **en español**, sin tildes en identificadores.
- Los comentarios explican **por qué**, no qué. Si el comentario repite la
  línea, bórralo.
- Todo lo que entra al Hub pasa por `orchestrator.procesar()`. Si un origen
  nuevo necesita un endpoint con forma distinta, el contrato está mal.
- Los módulos de IA (`ai/stt.py`, `ai/ner.py`, `ai/ocr.py`) mantienen su firma
  sin importar el proveedor. Cambiar de proveedor toca `ai/provider.py` y nada
  más.
- Ninguna función de IA lanza excepción: devuelve el respaldo. La demo no se
  cae por la red.
