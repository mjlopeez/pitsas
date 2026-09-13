# Contrato canónico — ISO 15143-3 / AEMP 2.0 adaptado

**Congelado a las 08:30.** Cambiarlo después rompe trabajo de los otros tres.
Fuente de verdad ejecutable: `backend/app/canonical.py`.

## Campos

| Campo canónico | Tipo | Telemetría OEM | Retrofit J1939 | WhatsApp / campo |
|---|---|---|---|---|
| `asset_identifier` | String | `OEMSerialNumber` | `VIN_Broadcast` | extraído por NER |
| `event_timestamp` | ISO 8601 UTC | `SnapshotTime` | epoch RTC | hora del mensaje |
| `location` | Point (lat, lon) | `Latitude`/`Longitude` | NMEA `$GPGGA` | GPS del teléfono |
| `operating_hours` | Decimal (h) | `CumulativeOperatingHours` | **SPN 247** | OCR del tablero |
| `engine_state` | Enum ON/OFF/IDLE | `EngineStatus` | RPM + carga | texto interpretado |
| `cumulative_fuel` | Decimal (gal) | `CumulativeFuelUsed` | **SPN 250** | vale digital |
| `diagnostic_alerts` | Array | `DiagnosticCodes` (SPN/FMI) | **DM1** activos | síntoma clasificado |
| `assigned_project` | String | geocerca | geocerca | validado en audio |

Campos propios del Hub, fuera del estándar: `fuel_delivered`, `note`,
`reported_by`, `provenance`, `raw`.

**Todo el Hub trabaja en galones.** Komatsu y Volvo reportan litros; los
adaptadores convierten. El modelo de ROI usa $4.00/galón.

## Precedencia por campo

Esto es lo que **no** está en el documento base y es lo que contesta la tercera
fricción del enunciado: *responsables de la información*.

```
operating_hours:   OEM  →  retrofit J1939  →  OCR de foto  →  declaración humana
cumulative_fuel:   OEM  →  retrofit J1939  →  vale de campo
location:          OEM  →  retrofit J1939  →  GPS del teléfono
engine_state:      OEM  →  retrofit J1939  →  texto del operador
assigned_project:  geocerca siempre gana sobre lo que diga la persona
```

Cuando llega un valor de una fuente con **menos** autoridad que la vigente y
además **contradice** más allá de la tolerancia, el Hub **no elige en silencio**:
mantiene el valor de mayor autoridad y abre un ticket de conciliación.

Tolerancias: `operating_hours` 2 h · `cumulative_fuel` 5 % (el número del documento).

Verificado en pruebas: la PWA reportando 7 000 h no sobrescribe las 9 000 h de la
telemetría OEM, y queda el ticket abierto.

## Procedencia

Cada campo lleva su `FieldProvenance`: `source`, `confidence`, `confirmed_by`,
`raw_value`. Es lo que la UI pinta como chip y lo que responde la pregunta
«¿y si la IA se equivoca?». Cuando el audio y la foto del horómetro coinciden,
la confianza sube y `confirmed_by` queda en `audio+foto`.

## Idempotencia

Todo evento acepta `idempotency_key`. La PWA la construye como
`dispositivo:secuencia:reloj`. Reenviar la misma mutación diez veces produce
un solo registro — sin esto, un reintento duplica horas facturables, y eso lo
nota el cliente.

## Agregar una fuente nueva

1. Un archivo en `backend/app/adapters/`, con una función `to_canonical(payload)`.
2. Registrarlo en `adapters/__init__.py`.
3. Declarar su autoridad en `PRECEDENCIA` si aporta campos disputados.

Nada más del Hub se toca. **Eso** es la tesis del proyecto.

---

## Extensión — carga de material perecedero

**Añadida sobre el contrato congelado, 08:45. Solo aditiva: todo campo nuevo es
opcional, ningún evento anterior deja de validar.**

ECON está integrada verticalmente (cantera → plantas de concreto y asfalto →
laboratorio → maquinaria y transporte → obra), y ahí aparece la restricción
física más fuerte que tiene la empresa: **el concreto y el asfalto son
perecederos.** Si un mixer queda atrapado en la veda del VMT no se pierde
tiempo, se pierde la carga.

### Campos nuevos

`CanonicalEvent.carga: Carga | None`, con `tipo` (`CONCRETO` · `ASFALTO` ·
`AGREGADO`), `cantidad`, `unidad`, `dosificado_en` (el reloj de vida),
`temperatura_c`, `diseno`, `planta_origen`, `obra_destino`, `lote`,
`cumple_especificacion`.

Tres fuentes nuevas en `Source`: `PLANTA_CONCRETO`, `PLANTA_ASFALTO`, `LAB`.

### Dueño exclusivo de campo — más fuerte que la precedencia

La precedencia ordinaria dice qué fuente **gana** cuando varias pueden
reportar. Esto es distinto: hay campos que **una sola** unidad de negocio tiene
derecho a escribir, ninguna otra, ni siquiera la primera vez.

```
dosificado_en          → SOLO la planta
diseno                 → SOLO la planta
cumple_especificacion  → SOLO el laboratorio
```

Que la obra declare por WhatsApp «este lote está bien» no lo vuelve cierto. Un
intento de escribir un campo ajeno **no sobrescribe en silencio**: se rechaza y
abre un ticket de gobernanza (`canonical.puede_escribir()`,
`cargas.proyectar()`). Verificado: la obra y la propia planta intentando
declarar `cumple_especificacion` quedan en `None`; solo `LAB` lo puede fijar.

### El caso que cruza tres silos

Cuando el laboratorio dictamina que un lote **no cumple** y la carga ya salió,
el Hub la marca `retenida` y abre ticket crítico — hay que detenerla antes de
que se coloque, aunque ya esté en la carretera.

Y en el despacho (`api/dispatch_api.py::despachar_carga`), cuando la carga no
alcanza por **ninguna** ruta antes de vencer, la respuesta correcta no es
reprogramar el camión: es decirle a la planta que **no dosifique todavía**.
Esa decisión cruza planta, logística y obra de un solo golpe — es,
literalmente, el enunciado del reto.

⚠️ `VIDA_CONCRETO_MIN = 90` y `TEMP_MINIMA_COLOCACION_C = 120` en
`rules/carga.py` son típicos de industria, **no especificaciones verificadas de
ECON**. Emily los confirma antes de las 12:00.
