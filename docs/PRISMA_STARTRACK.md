# Prisma / Nexus + Startrack — la integración que se demuestra

**Añadido a las 15:48, anclado a datos reales en dos pasos.** Primero llegó
`Entropy_Hack_Grupo_ECON_Casos_de_Uso_Final.docx` (la especificación del
sandbox: dos plataformas, tres casos de uso). Después el **manual de usuario
de Nexus ECON**. Y por último la **documentación de la API de Startrack**
(38 páginas, `support.gps-platform.com`).

Los dos últimos documentos convirtieron este módulo de heurística a catálogo.
**Hoy `correlacion.py` no adivina nada: los dos lados del cruce son catálogos
oficiales.** Lo único que sigue siendo criterio nuestro está marcado como tal.

**Esta es la integración completa del guion de hoy — los tres minutos.**

No hay acceso real al sandbox. Se construyó una versión simulada de las dos
plataformas, sembrada con datos que salen de sus propios documentos — mismo
patrón que los adaptadores OEM: si el acceso real aparece, se conecta sin
tocar `correlacion.py`.

## Nomenclatura: Prisma es Nexus

La especificación del sandbox la llama **Prisma**. El manual de usuario la
llama **Nexus ECON**. Es el mismo sistema y por eso la interfaz dice
«Prisma / Nexus»: si el jurado usa un nombre, lo reconoce; si usa el otro,
también. En el código el prefijo sigue siendo `ps_` / `/api/ps/`.

## Las dos plataformas

| | Prisma / Nexus | Startrack |
|---|---|---|
| Qué gestiona | La **solicitud** y el estado del **recurso** | La **tarea de traslado** y el rastreo |
| Módulo del manual | 8 (Maquinaria y equipo) · 9 (Solicitud de maquinaria) | — |
| Campos clave | `Clave`, `No. de activo`, `Clase de equipo`, `Precio x hora`, `Horas mínimas`, `estado_solicitud`, `estado_maquinaria` | `estado_tarea`, `fecha_programada`, destino, motorista, **conexión**, **último evento** |
| Lo que **no** tiene | ubicación GPS, conexión, conductor | solicitud, estado del recurso, tarifa |

## Los dos identificadores — y cuál es la llave

Módulo 8 expone dos códigos distintos para cada equipo, y confundirlos es el
error clásico de una integración así:

| Campo | Ejemplo | Qué es | ¿Sirve de llave? |
|---|---|---|---|
| **Clave** | `EQ142` | correlativo logístico interno | **No.** No existe en Startrack |
| **No. de activo** | `EXC22017LC` | activo fijo contable | **Sí.** Es lo que Startrack expone |

El formato del No. de activo es `clase + correlativo + empresa`, donde el
sufijo es la empresa del grupo: `EC` = ECON, `LC` = La Cantera. El
`EXC-17006EC` de nuestro caso calza con ese patrón — es una excavadora de
ECON. Por eso la llave de cruce es el **No. de activo**, no la Clave.

## El catálogo de estados es cerrado, no una heurística

Módulo 8 muestra los contadores del inventario real: **253 equipos**.

| Estado | Equipos | ¿Puede operar? |
|---|---|---|
| Disponible | 194 | sí |
| Ocupada | 5 | sí, asignada |
| Mant. Preventivo | 1 | **no** |
| Mant. Correctivo | **53** | **no** |
| Obsoleta | 0 | **no** |

Esas 53 unidades en Mant. Correctivo — el 21 % de la flota — son el volumen
que hace que el caso de riesgo no sea teórico.

`correlacion.py` ya no adivina por palabras clave: mapea contra este
catálogo. Lo único tolerante que queda es la **escritura** (`Mant.` →
`mantenimiento`, mayúsculas, tildes), porque Nexus y Startrack no la
escriben igual. El catálogo no se infiere; la ortografía sí se normaliza.

## Los cinco estados del Hub

Es la tabla de decisión de la especificación (hoja 4), y cada estado lleva su
acción textual y el rol responsable de la matriz RACI. El Hub no fusiona: **clasifica**.

| Estado | Cuándo | Acción | Área |
|---|---|---|---|
| `en_operacion_normal` | las dos plataformas coinciden y hay conexión | Continuar monitoreo | Logística |
| `diferencia_valida` | recurso `Ocupada` + tarea `Completada` | **No marcar conflicto** | Logística |
| `alerta_operativa` | asignación válida, pero Startrack sin conexión | Validar ubicación y conectividad del equipo | **Maquinaria** |
| `riesgo_critico` | recurso no operable + tarea todavía viva | Detener el traslado y confirmar estado | **Maquinaria** |
| `vinculo_no_confirmado` | sin unidad asignada, o sin tarea que cruzar | Asignar unidad o validar identificador | Logística |

Las áreas son las tres que confirmaron los organizadores: **Maquinaria,
Logística y Proyectos**. No es taxonomía nuestra — es como está partida la
operación en ECON, y por eso cada alerta cae donde alguien puede actuar.

El reparto tiene una lógica que conviene poder defender: **la decisión de si
un equipo sale o no sale es de Maquinaria**, porque es quien es dueño del
activo. Logística ejecuta el traslado pero no autoriza una máquina averiada.
Y Proyectos no recibe alertas operativas: recibe el costo, que es lo que
sufre. Ver `docs/SANGRADO.md`.

El orden de evaluación importa y está en ese orden en `clasificar_estado()`:
primero lo que impide siquiera comparar, después el riesgo, después la falta
de confirmación, y de último los dos casos sanos.

## Honestidad sobre `riesgo_critico`

Nexus **ya bloquea** el caso obvio. El manual documenta el error
`TRANSIT_EQUIPMENT_IN_MAINTENANCE`: no se puede *solicitar* un equipo que
está en mantenimiento. Presentar eso como hallazgo nuestro se cae en tres
segundos frente a un juez de ECON.

El hueco real es **temporal, no de validación**: el bloqueo actúa al momento
de solicitar. Lo que nadie revisa es el cambio de estado **después** de
aprobada la solicitud — la máquina entra a Mant. Correctivo el martes y la
tarea de traslado del jueves sigue viva en Startrack. Así se dice frente al
jurado, y así está escrito en el `detalle` que devuelve la API.

## El lado Startrack — también es catálogo cerrado

### La llave: `No. de activo` ↔ `Descripción`

El **Diccionario de Datos oficial** (hoja PRISMA y hoja STARTRACK) lo define
así:

| Plataforma | Campo | Ejemplo |
|---|---|---|
| Prisma | `No. de activo` | `CF-03 - Cargador frontal 03` |
| Startrack | `Vehículos > Descripción` | `CF-03` |

Se cruza por el **código corto del equipo**. `CF-03` es su ejemplo (equipo 14,
«The Hub»); el nuestro es `EXC-01`.

> ⚠️ **Corrección.** Antes afirmábamos aquí que la llave era el campo
> `remote_id` de la API de Startrack. Eso era una lectura nuestra de la
> documentación de la plataforma, no del sandbox de ECON. El diccionario
> ejemplifica `ID remoto` como **`78093`** — un identificador numérico de la
> organización, no el activo fijo.
>
> Las dos cosas son ciertas y conviene poder explicarlo: la API **sí** ofrece
> `remote_id` para integraciones externas —y es donde se pondría el No. de
> activo en una implementación real— pero **el sandbox de ECON hoy cruza por
> la Descripción**. `_tareas_de()` busca por las tres llaves para no depender
> de cuál esté poblada.

Ver `docs/DATA.md` para el diccionario completo.

### `workflow_role`: el nombre del estado es libre, el rol no

`GET /api/job/status` devuelve los estados de tarea. Un cliente puede
inventarse los que quiera — el ejemplo oficial trae "Limpiando", "Devolución",
"No se pudo entregar", "Entregado" — pero **todos llevan un `workflow_role`
que solo puede ser uno de tres**:

| `workflow_role` | Significa | En el Hub |
|---|---|---|
| `0` | Pendiente | tarea **activa** |
| `1` | Completada | tarea cerrada |
| `2` | Cancelada | tarea cerrada |

Por eso la decisión se toma sobre el rol y nunca sobre el nombre: es lo que
hace que esto funcione contra un tenant que no conocemos. El respaldo por
nombre cubre **solo** los tres presets documentados (ids 0, 1 y 2); un estado
personalizado sin rol se trata como desconocido en vez de adivinarlo.

### Startrack lleva su propio estado de mantenimiento

`O: Default Vehicle Status` — y es independiente del de Nexus:

| id | Estado | ¿Bloquea operar? |
|---|---|---|
| 0 | Normal | no |
| 1 | Mantenimiento | **sí** |
| 2 | Fuera de servicio | **sí** |
| 3 | En reparación | no — lo averiado es el **rastreador**, no la máquina |
| 4 | Se usa de vez en cuando | no |

Que las dos plataformas registren mantenimiento por separado y ninguna le
avise a la otra **es la tesis del Hub, demostrada con sus propios campos**.
Cualquiera de los dos dispara `riesgo_critico`, y el detalle dice cuál de los
dos lo reportó. Cuando lo reportan los dos — el caso `RM19003EC` — esa es la
frase del minuto 2.

### `coms_age`: la falta de conexión es un número

`GET /api/devices` devuelve `coms_age`, *"segundos transcurridos desde el
último reporte"*. Se acabó decidir sobre el string `"Sin conexión"`.

> ⚠️ **El umbral sí es criterio nuestro.** `HUB_STARTRACK_UMBRAL_CONEXION`,
> por defecto 86 400 s: una jornada completa sin un solo reporte. Lo elegimos
> para no disparar por el hueco normal de la noche. La documentación no define
> ningún umbral. Si ECON opera turnos, esto se ajusta — y se dice así, igual
> que los horarios de veda del VMT.

### Autenticación y límites

Basic HTTP auth: el **API key va en el campo de usuario** y la contraseña es
**la misma del login normal**. El API key sale de la interfaz: administrador
de usuarios → pestaña *"Integraciones (API)"* (formato `22_5995decd5a025`).

Límite: **240 peticiones por IP cada 2 minutos**, y `GET /api/devices` es mucho
más estricto — **10 cada 5 minutos**. Pasarse devuelve `HTTP 529` y bloquea
todo hasta que pase la ventana. Por eso `startrack.py` cachea el catálogo de
estados y llama a `/api/devices` **una vez por sincronización**, nunca por
vehículo.

## La KPI: lo que Nexus factura contra lo que Startrack mide

Aquí se cruzan las dos plataformas en un solo número, y ese es el punto.

**Nexus factura.** Módulo 8 registra `Precio x hora de operación interna` y
`Horas de uso mínimo por jornada` — **8.00**. El mínimo se cobra aunque el
equipo no produzca.

**Startrack mide.** `GET /api/vehicles/stats` devuelve `ign_on_time`: segundos
con ignición encendida. El webhook de alertas manda `ignOnTime`, descrito
literalmente como *"el valor del horómetro"*.

```
horas_facturadas   = jornadas × horas_mínimas      (Nexus)
horas_medidas      = ign_on_time / 3600            (Startrack)
horas_sin_respaldo = facturadas − medidas
costo              = horas_sin_respaldo × precio_hora
```

Eso es **Costo Real (AC) sin Valor Ganado (EV)**, calculado en vez de
argumentado. Ya no es inferencia nuestra: es una resta entre dos sistemas.

**Sin medición se dice «sin datos», nunca «midió cero».** Presentar una
ausencia de medición como una medición de cero es exactamente lo que le
criticamos a sus tableros; hacerlo nosotros sería perder el argumento del
minuto 1 por descuido. Cuando no hay telemetría, la exposición vale lo mismo
que antes y el campo `medicion` lo declara.

| Equipo | Facturadas | Medidas | Exposición |
|---|---|---|---|
| EXC-01 — sin conexión | 8 h | *sin datos* | **$1 200** |
| Pala Volvo — conectada | 8 h | 7.6 h | $60 |
| Rodo Lombardine — conectado | 8 h | 7.9 h | $9.50 |

**Las dos últimas filas existen para que la KPI se pueda ver callada.** Un
número que grita en toda operación no prueba nada; uno que da casi cero en la
máquina sana es el que vuelve creíble el $1 200 de la otra.

> ⚠️ **`ign_on_hrs` NO se usa.** El ejemplo de la propia documentación
> (`GET /api/vehicle/<id>/stats`) trae `ign_on_hrs: "100.8000"` **para un solo
> día** — imposible — junto a `init_ign_on_hrs: "584186.4000"`. Parecen
> lecturas de horómetro acumulado, no duración diaria. Se usa `ign_on_time`
> del endpoint agregado, que está documentado en segundos. Verificar contra un
> tenant real antes de tocarlo: inventarle unidades a un campo ajeno es
> exactamente el tipo de error que un juez de ECON detecta.

## El hallazgo del rezago — y cómo se dice

El manual trae su propia tabla de CPI por período:

| Período | CPI | EV | AC |
|---|---|---|---|
| S14 | 0.37 | $47 850 | $130 922 |
| S20 | 0.51 | $21 873 | $43 089 |
| S23 | **4.44** | $230 703 | $51 935 |
| S24 | 3.98 | $99 460 | $24 986 |

Y su propia regla crítica: *«el EV solo se actualiza cuando se aprueban
bitácoras en el Módulo 4; mientras existan RDOs pendientes de validación, el
dashboard mostrará un avance menor al real»*.

Un CPI que salta de 0.51 a 4.44 en tres semanas no es un cambio de
productividad: es consistente con el EV aterrizando semanas después del AC
que le corresponde.

> ⚠️ **Esto es una inferencia nuestra, no algo que el manual afirme.** Se
> presenta así: «estos saltos son consistentes con rezago de aprobación, no
> con productividad real» — hipótesis fuerte y verificable. Si un juez la
> desmiente con datos internos, no perdimos nada; si la afirmamos como hecho
> y se cae, perdemos toda la credibilidad ganada.

## El mapeo de campos — lo que el documento pide que definamos

> «El mapeo entre plataformas y la solución tecnológica deberán ser definidos
> por cada equipo.»

Está en `MAPEO_CAMPOS` (`correlacion.py`), se sirve en `GET /api/ps/mapeo` y
se muestra en pantalla. Doce conceptos; el patrón que importa es que cada uno
declara **de quién es el dato**:

| Concepto | Prisma / Nexus | Startrack | Decisión |
|---|---|---|---|
| Identificador | No. de activo | Vehículo / descripción | llave de cruce |
| Clave logística | `EQ142` | no existe | referencia interna, no llave |
| Estado del recurso | catálogo Módulo 8 | no existe | exclusivo Nexus |
| Ubicación / conexión | no existe | GPS, conectado | exclusivo Startrack |
| Tarifa | $/h + horas mínimas | no existe | valoriza la exposición |
| Estado del Hub | calculado | calculado | separa riesgo de diferencia válida |

Es la misma tesis de **precedencia por campo** que ya está en `canonical.py`
para la telemetría: la tercera fricción del reto — *responsables de la
información* — resuelta también aquí.

## Los datos sembrados (todos reales)

`seed/prisma_startrack.py`. Ninguna fila es inventada:

| Equipo | No. de activo | Nexus | Startrack | Estado del Hub |
|---|---|---|---|---|
| EXC-01 — Excavadora | `EXC-17006EC` | Aprobada / Ocupada | Asignada, **sin conexión** desde 11/09 11:07 | `alerta_operativa` |
| Pala Volvo EC480DL | `EXC22017LC` | Aprobada / Ocupada | Completada, conectada | `diferencia_valida` |
| Rodo Lombardine RT820 | `RC03004EC` | Aprobada / Ocupada | Completada, conectada | `diferencia_valida` |
| Recicladora | `RM19003EC` | Aprobada / **Mant. Correctivo** | Pendiente, viva | `riesgo_critico` |
| Recicladora WIRTGEN | — | **Pendiente / Sin asignar** | — | `vinculo_no_confirmado` |
| RETRO EXCAVADORA | — | **Aprobada / Sin asignar** | — | `vinculo_no_confirmado` |

Las dos últimas **están en las propias capturas del manual**. La segunda es
la peor: una solicitud que ya fue aprobada y nunca recibió unidad. El
Coordinador la dio por resuelta y nadie lo nota. No tuvimos que inventar el
caso — ya existe en su portafolio.

## Endpoints

| Método | Ruta | Para qué |
|---|---|---|
| GET | `/api/ps/maquinas` | roster con exposición agregada en dólares |
| GET | `/api/ps/vista-unificada/{maquinaria}` | operaciones correlacionadas, estado del Hub, acción, responsable, exposición |
| GET | `/api/ps/mapeo` | el mapeo de campos y los cinco estados, como dato |
| POST | `/admin/seed-ps` | resembrar (idempotente) |
| POST | `/admin/sync-startrack` | refrescar contra la API real (a mano, nunca en el arranque) |

### Cómo sincroniza, y por qué así

`GET /api/fleet/status` — **una sola petición para toda la flota**. Devuelve
por vehículo: `vehId`, `vehDescr` (la Descripción, donde ECON pone el código
del equipo), `vehStat`, `x`/`y`, `epoch`, `eventDescription`, `ignOnHrs` y
`odometer`.

La primera versión pedía `/api/vehicle/<id>` uno por uno más `/api/devices`.
Con 120 equipos eso son **241 peticiones contra un límite de 240 cada dos
minutos**: se autobloqueaba. Y `/api/devices` tiene un límite propio de 10
cada 5 minutos. Como `epoch` ya da el último reporte, la antigüedad se calcula
sola y ese endpoint no hace falta.

`scripts/prueba_startrack.py` verifica el mapeo campo por campo **sin tocar la
red**, con una respuesta calcada de su documentación: `y`→latitud,
`x`→longitud, `epoch`→`coms_age`, `vehStat`→estado, y que `ignOnHrs` se trate
como acumulado. Está enganchado a `smoke.sh`.

El conector (`backend/app/startrack.py`) está **apagado por defecto**. Se
enciende con `STARTRACK_HOST`, `STARTRACK_API_KEY` y `STARTRACK_PASSWORD` en
`backend/.env`. Sigue el patrón de `ai/provider.py`: ninguna función lanza
excepción, y sin credenciales el Hub sigue con la semilla. **El tablero
declara en pantalla si los datos son `en vivo` o `simulados`** — nunca
presentamos la semilla como si fuera el sistema real.

## Por qué es el mismo patrón que ya usa el Hub

No es un módulo pegado aparte. Es la misma filosofía que `rules/fuel.py` (no
sobrescribir en silencio, conciliar y abrir ticket) y `cargas.py` (dueño
exclusivo de campo, interpretar antes de fusionar), aplicada a la fuente que
el propio reto definió. Vale la pena decirlo así frente al jurado.

## Qué queda fuera del guion, no del repo

WhatsApp con voz y OCR, la telemetría OEM de cuatro fabricantes, el retrofit
J1939 y el concreto perecedero **siguen construidos y probados** — están en
las 49 aserciones de `smoke.sh` y en las pestañas **Captura de campo**,
**Integración** y **Despacho**. Salen del guion escrito porque los tres
minutos se van completos a esta integración, no porque estén incompletos.
Si un juez pregunta por cualquiera de ellos, se abre la pestaña y corre.
