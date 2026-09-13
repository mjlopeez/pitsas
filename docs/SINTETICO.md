# Datos sintéticos — guía para el equipo

Para que nadie dependa del sandbox de ECON y el Command Center se vea como se
verá en producción. Todo lo generado queda **marcado y es borrable**.

## Arrancar

```bash
./backend/run.sh                       # API en :8000
curl -X POST "localhost:8000/api/sintetico/generar?equipos=120&seed=42"
```

Listo: 120 equipos con sus solicitudes y tareas. `GET /api/ps/maquinas` y
`GET /api/ps/vista-unificada/{id}` ya los sirven, sin cambiar nada más.

Documentación viva de todos los endpoints: **http://localhost:8000/docs**

## Las tres reglas

**1. Determinista.** Mismo `seed`, mismos datos, byte por byte.

> **Si reportás un bug, reportá el seed.** Con `seed=42` cualquiera del equipo
> reproduce exactamente tu pantalla. Sin esto, los datos sintéticos crean más
> trabajo del que ahorran.

**2. Marcado.** Toda fila lleva `sintetico = 1`. `GET /api/sintetico/estado`
dice cuánto hay de cada cosa. Nunca se mezcla en silencio con lo que viene de
Nexus o Startrack.

**3. Aditivo.** No toca las seis filas de la demo (EXC-01 y compañía).
`POST /api/sintetico/limpiar` borra solo lo generado. El minuto 2 del guion
funciona con o sin esto cargado — hay una aserción en `smoke.sh` que lo
verifica después de un ciclo completo de generar y limpiar.

## Qué es real y qué no

| | |
|---|---|
| **Real** | La proporción de estados. El Módulo 8 del manual muestra 194 disponibles, 53 en Mant. Correctivo y 5 ocupadas sobre 253 equipos. Se respeta, y por eso el inventario *se siente* como el de ellos: uno de cada cinco equipos está en correctivo. |
| **Real** | El formato de identificadores: clase + correlativo + empresa (`EXC22017LC`, `EC` = ECON, `LC` = La Cantera) y la clave logística `EQ###`. |
| **Real** | Dos tarifas que el manual muestra: Barredora $200/hr y Bomba Lanzadora $2,002/hr. |
| **Sintético** | Nombres de proyecto, operadores, el resto de tarifas y los horómetros. Plausibles, no reales. |

> ⚠️ **Nunca cites un agregado sintético como si fuera la pérdida real de
> ECON.** `GET /api/ps/sangrado` con 120 equipos cargados devuelve seis cifras
> grandes que **no son de ECON**: son de un inventario inventado. Para el
> pitch se usa la semilla de seis filas, que sí sale de sus documentos.

## Endpoints

| Método | Ruta | Para qué |
|---|---|---|
| GET | `/api/sintetico/estado` | cuánto hay cargado, separando generado de real |
| POST | `/api/sintetico/generar?equipos=120&seed=42` | genera (1 a 500 equipos) |
| POST | `/api/sintetico/limpiar` | borra solo lo sintético |
| GET | `/api/sintetico/webhook-ejemplo/{remote_id}` | un payload de webhook listo para disparar |

## Probar la ruta de tiempo real sin tener Startrack

```bash
# 1. pedí el payload de ejemplo
curl "localhost:8000/api/sintetico/webhook-ejemplo/EXC-17006EC"

# 2. mandalo al webhook (copiá el campo `payload`)
curl -X POST localhost:8000/webhooks/startrack/ubicaciones \
  -H 'content-type: application/json' \
  -d '{"code":3,"vid":1057,"remote_id":"EXC-17006EC","hourmeter":4521.0,"veh_status":0,"event_time":"2026-09-13T08:00:00-06:00","placename":"Ahuachapan"}'
```

**Ojo con el horómetro.** `hourmeter` es la lectura **acumulada** del equipo,
no las horas de la jornada. La primera lectura de un equipo fija la línea
base; a partir de la segunda, las horas medidas son la diferencia. Si mandás
una sola, vas a ver `horas_medidas = 0` y está bien.

## Por dónde entrar, según en qué trabajes

| Si trabajás en... | Empezá por |
|---|---|
| Command Center | `GET /api/ps/maquinas` y `/api/ps/vista-unificada/{id}` |
| Vista por rol | `GET /api/ps/sangrado` — trae los tres roles con sus cifras |
| Evidencia / PEA | `POST /api/ps/pea/{maq}?aprobado_por=...` y `/pea/{id}/verificar` |
| Tiempo real | `/api/sintetico/webhook-ejemplo/{id}` y disparalo al webhook |
| Mapa | las tareas sintéticas traen `lat`/`lon` dentro de El Salvador |
