# Diccionario de Datos — qué campo es qué

Resumen de `Entropy Hack_Grupo ECON_Diccionario de Datos_Final.xlsx`, el
archivo oficial de los organizadores, y de a qué mapea cada campo en el Hub.

**Este es el documento que se le enseña a un juez que pregunta «¿de dónde
sacaron esto?».** Todo lo de aquí sale de su archivo; lo que es nuestro está
marcado como nuestro.

## La llave de cruce

| Plataforma | Campo | Ejemplo del diccionario |
|---|---|---|
| Prisma | `No. de activo` | `CF-03 - Cargador frontal 03` |
| Startrack | `Vehículos > Descripción` | `CF-03` |

**Se cruza por el código corto del equipo.** Nuestro caso es `EXC-01`; `CF-03`
es el ejemplo del diccionario (equipo 14, «The Hub»).

⚠️ **`ID remoto` NO es el número de activo.** El diccionario lo ejemplifica
como `78093`: es un identificador numérico de la organización. La API de
Startrack sí documenta `remote_id` como campo para integraciones externas —
las dos cosas son ciertas, pero **el sandbox de ECON cruza por Descripción**.
El motor busca por las tres llaves para no depender de cuál esté poblada.

## Catálogos cerrados

Los tres coinciden con lo que ya teníamos del manual de Nexus.

**Estado de la maquinaria** (Prisma → `estado_maquinaria`)
`Disponible` · `Ocupada` · `Mant. preventivo` · `Mant. correctivo` · `Obsoletas`

**Estado de la solicitud** (Prisma → `estado_solicitud`)
`Aprobada` · `Pendiente` — y nada más.

**Clase de equipo** (Prisma → `clase_equipo`) — **solo cinco**
`Excavadora` · `Retroexcavadora` · `Motoniveladora` · `Minicargador` · `Cargador frontal`

> El generador sintético produce **solo estas cinco**. Antes inventaba
> Barredora, Bomba Lanzadora, Rodo Compactador y tres más; ninguna está en su
> catálogo. Hay una aserción que lo verifica.

**Estado de la tarea** (Startrack → `workflow_role`)
`Pendiente` · `Completada` · `Cancelada` · *estados personalizados* — que es
exactamente por qué se decide sobre el rol y no sobre el nombre.

## Coordenadas: vienen escaladas

```
Latitud   133376152   →  13.3376152
Longitud  -878486967  →  -87.8486967
```

> ✅ **Ya no es interpretacion: esta probado con dato de su plataforma.**
> El export real de geocercas (`geocercas-4034.xlsx`, 12/09) trae
> `PROY-014 - The Hub - Proyecto Xi - La Union` en **13.3376152 /
> -87.8486967** — exactamente el mismo punto que el Diccionario de Datos
> ejemplifica como `133376152 / -878486967`. El mismo lugar, en los dos
> formatos, en dos documentos suyos distintos.
>
> Si un juez pregunta de donde salio la normalizacion de `_coord()`, la
> respuesta es esta fila, no un razonamiento nuestro.

Enteros por 10⁷. El formato 2 del rebote de Startrack hace lo mismo; el
formato 1 manda decimales. `_coord()` en `ingest/startrack_webhook.py`
normaliza los dos: por encima de 180 en valor absoluto solo puede ser la
versión escalada, porque ninguna coordenada válida llega ahí.

**Fue un bug real.** Sin eso, el primer lote en formato 2 mandaba los equipos
a cien millones de grados y el mapa quedaba vacío. La aserción está probada
contra el bug.

## Campos que solo tiene una plataforma

Esto es la tercera fricción del reto —*responsables de la información*—
resuelta con datos concretos:

| Solo Prisma | Solo Startrack |
|---|---|
| Estado de solicitud, Solicita (Gerente de Proyecto) | Descripción, ID remoto, Conductor |
| Clave logística, Precio × hora, Horas mínimas | Geocercas (origen/destino), Latitud/Longitud |
| Partida WBS | Estado del vehículo, Horómetro, Odómetro |

Ninguna de las dos puede responder sola si una operación está bien. Ese es el
Hub.

## Lo que es nuestro, y va marcado

| Qué | Dónde |
|---|---|
| Umbral de «sin conexión» (1 jornada) | `HUB_STARTRACK_UMBRAL_CONEXION` |
| Los 4 costos unitarios del sangrado | `SUPUESTOS` en `sangrado.py` |
| Tarifas del generador sintético | `CLASES` en `seed/sintetico.py` |
| La hipótesis del rezago del EV | `docs/PRISMA_STARTRACK.md` |

Todo configurable, todo declarado. Ver `GET /api/ps/mapeo` para la matriz
completa servida como dato.
