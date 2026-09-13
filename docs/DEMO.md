# Guion de demo — 3 minutos

**Dueño: Josué.** Tres ensayos cronometrados antes de las 19:00 y video de
respaldo grabado.

**Los tres minutos van completos a la integración Prisma / Nexus ↔ Startrack.**
Es lo que el reto define y contra lo que probablemente se evalúa. Todo lo
demás que está construido (WhatsApp con voz, telemetría OEM, retrofit J1939,
concreto perecedero) sale del guion escrito y queda como respuesta a
preguntas, no como minuto propio. Ver la tabla del final.

## Antes de empezar (17:45, checklist)

- [ ] `POST /admin/reset` y `POST /admin/seed` — escenario limpio
- [ ] `POST /admin/seed-ps` — Prisma/Startrack sembrado
- [ ] `./backend/run.sh --prod` y abrir la URL de red **desde el celular**
- [ ] `./scripts/smoke.sh` verde (99 aserciones)
- [ ] `POST /api/sintetico/limpiar` — el pitch va con las seis filas reales
- [ ] Command Center abierto en la pestaña **Prisma + Startrack**, `EXC-01` seleccionado
- [ ] Simulador de telemetría corriendo (`--intervalo 3`) para que el mapa respire de fondo
- [ ] Hotspot del celular como red, **no** el wifi del salón
- [ ] Video de respaldo listo para reproducir sin pedir permiso

---

## Minuto 1 — El síntoma: sus propios números no cuadran

Se abre con **su** dashboard, no con el nuestro. La tabla de CPI del manual
de Nexus, en pantalla:

| Período | CPI | EV | AC |
|---|---|---|---|
| S14 | 0.37 | $47 850 | $130 922 |
| S20 | 0.51 | $21 873 | $43 089 |
| S23 | **4.44** | $230 703 | $51 935 |

> «Un CPI que pasa de 0.51 a 4.44 en tres semanas. Ninguna obra cambia de
> productividad así. Y el propio manual dice por qué: el Valor Ganado solo
> se actualiza cuando se aprueban las bitácoras. Mientras haya RDOs sin
> validar, el tablero muestra menos avance del que hay en campo.»

> «**No estamos diciendo que su sistema esté mal.** Estamos diciendo que
> estos saltos son consistentes con rezago de aprobación, no con
> productividad real. Es una hipótesis, y es verificable.»

**La frase:** «ECON no tiene un problema de sistemas. Tienen Nexus, tienen
app móvil, tienen Startrack. Tienen un problema de datos que llegan tarde y
sin conciliar entre plataformas — y se decide sobre eso.»

⚠️ **Decir «hipótesis» en voz alta.** Si la afirmamos como hecho y un juez la
desmiente con datos internos, se cae toda la credibilidad. Dicha como
hipótesis, gana igual y no se puede perder.

---

## Minuto 2 — La causa: dos verdades que nadie cruza

Pestaña **Prisma + Startrack**, `EXC-01` ya seleccionado. Una sola tarjeta
en pantalla, dos columnas:

```
Prisma / Nexus                     Startrack
  Solicitud   SOL-EXC01              Tarea         TAR-EXC01
  Estado sol. Aprobada               Estado tarea  Asignada
  No. activo  EXC-17006EC            Identificador EXC-01 (EXC-17006EC)
  Estado maq. Ocupada                Conexión      Sin conexión
  Operador    María José López       Último evento 11/09 11:07
```

> «Nexus dice: aprobada, asignada, ocupada. Todo correcto. Startrack dice:
> sin conexión desde el once de septiembre a las once y siete. También
> correcto. **Ninguno de los dos está mintiendo, y ninguno de los dos sabe
> lo que sabe el otro.**»

Se señala la llave de cruce:

> «Los cruzamos por el **No. de activo** — no por la clave logística. Y eso no
> lo decidimos nosotros: **está en su Diccionario de Datos.** Prisma identifica
> el equipo con el número de activo y Startrack con la descripción del
> vehículo, y es el mismo código corto en las dos. **Usamos el mapeo que
> ustedes ya definieron.** Ese detalle es la diferencia entre una integración
> que funciona y una que empareja mal.»

Se abre el **mapeo de campos** (el botón de abajo, dos segundos):

> «El documento pide que cada equipo defina el mapeo entre plataformas. Este
> es el nuestro, y lo importante no es la tabla: es que cada campo declara
> **de quién es el dato**. La ubicación es de Startrack. El estado del recurso
> es de Nexus. Nadie sobrescribe al dueño.»

Y se cambia de máquina en el selector, rápido, para mostrar que clasifica:

| Máquina | Qué muestra |
|---|---|
| `EXC-03` | `Ocupada` + `Completada` → **diferencia válida**, no conflicto |
| `RE-01` | Mant. Correctivo + tarea viva → **riesgo de despacho**, en rojo · a Maquinaria |
| `SOL-RETRO-SIN-UNIDAD` | Aprobada, **sin unidad asignada** → vínculo pendiente |

> «Esta de aquí» *(EXC-03)* «un sistema tonto la marcaría como
> inconsistencia. No lo es: uno describe el recurso, el otro la tarea. El
> traslado terminó y el equipo quedó ocupado en el destino. **No asumimos
> inconsistencia donde no la hay** — si alertáramos de todo, nadie haría caso
> a la alerta que sí importa.»

> «Esta otra» *(RE-01)* «sí. El equipo entró a Mantenimiento Correctivo y
> la tarea de traslado sigue viva. Y sean honestos: Nexus **ya bloquea**
> solicitar un equipo en mantenimiento, tienen el error
> `TRANSIT_EQUIPMENT_IN_MAINTENANCE`. Lo que no revisa es el cambio de estado
> **después** de aprobada la solicitud. Ese es el hueco, y son 53 de sus 253
> equipos los que están en ese estado hoy.»

> «Y esta» *(SOL-RETRO)* «no la inventamos: está en las capturas de su propio
> manual. Una solicitud aprobada que nunca recibió unidad. Alguien la dio por
> resuelta y nadie lo nota.»

**La frase:** «Cinco estados. El Hub no fusiona los datos: los clasifica, y
le pone nombre y dueño a cada situación.»

---

## Minuto 3 — El costo: lo que esa alerta vale en dólares

Se vuelve a `EXC-01` y se señala el bloque ámbar de la tarjeta:

```
$1,200.00 de exposición
  Nexus facturó        Startrack midió      Sin respaldo
  8 h                  sin datos            8 h
Costo Real (AC) acumulado sin Valor Ganado (EV).
```

> «Su propio Módulo 8 registra el precio por hora de operación interna y las
> horas de uso mínimo por jornada: ocho. **Ese mínimo se factura aunque el
> equipo no produzca.** Una excavadora asignada y sin confirmar son mil
> doscientos dólares de Costo Real por jornada, sin un dólar de Valor Ganado
> en contra.»

Y aquí viene el giro. Se cambia el selector a la **Pala Volvo**:

```
$75.00 de exposición
  Nexus facturó        Startrack midió      Sin respaldo
  8 h                  7.5 h                0.5 h
```

> «La misma cuenta, en la máquina que sí está reportando. Startrack **mide**
> las horas de ignición; Nexus **factura** el mínimo. Aquí midió siete punto
> seis contra ocho facturadas: sesenta dólares. Prácticamente nada.»

> «Y esa es la diferencia entre una alerta y una alarma. Si este número gritara
> en toda operación, nadie le haría caso. **Se queda callado cuando la máquina
> está sana, y por eso el de la otra pantalla significa algo.**»

⚠️ **Decir «sin datos», nunca «midió cero».** EXC-01 no reporta: no es que
midiera cero horas, es que no hay medición. Confundir las dos cosas es
exactamente lo que le criticamos a su tablero en el minuto 1.

> «Y esto cierra el círculo del minuto uno. El Valor Ganado llega tarde porque
> depende de bitácoras aprobadas. El Costo Real, no: se acumula solo. Por eso
> el CPI se ve como se ve.»

Se señala la línea de acción, al pie de la tarjeta:

```
Validar ubicación y conectividad del equipo → Maquinaria
```

> «No termina en un número. Termina en una acción con destinatario, y el
> destinatario es una de sus tres áreas. Si el equipo no puede salir, eso lo
> decide **Maquinaria** — Logística ejecuta el traslado, pero no autoriza una
> máquina averiada. Si una solicitud quedó aprobada sin unidad, eso es de
> **Logística**. Y lo que se le cargó a una partida sin respaldo lo sufre
> **Proyectos**. **Una alerta sin dueño no es una alerta, es ruido.**»

### El remate: la evidencia sellada

Al pie de la tarjeta, **«Sellar evidencia»**. Se escribe un nombre de verdad
—el de quien aprueba— y sale el registro con su hash.

> «Y esto no termina en una pantalla que hay que creerme. Miren.»

Se aprieta **«Verificar recomputando»**:

```
Verifica ✓
El hash se recalculó desde el contenido y dio idéntico.
```

> «El sello se recalcula desde los datos de Nexus y Startrack. Cualquiera con
> acceso de lectura a **sus** sistemas puede repetir esta cuenta y obtener el
> mismo hash. **No hay que confiar en nosotros: hay que leer lo que ustedes ya
> tienen.**»

> «Y fíjense en el campo de arriba: dice el nombre de una persona. **No
> automatizamos la aprobación — automatizamos la evidencia que la aprobación
> necesita.**»

### Y para cerrar, la pestaña «Por área»

Tres botones: **Maquinaria · Logística · Proyectos**. Se abre el de Proyectos.

> «Cada área ve lo suyo. Proyectos no ve alertas de mantenimiento: ve qué
> partidas están recibiendo horas sin respaldo, con nombre y apellido.»

Se señala el distintivo de una cifra que dice **con supuesto**:

> «Y aquí está lo que más nos importa que vean. Este número lleva un supuesto
> nuestro y lo dice en la cara: el costo-hora, la tarifa de cama baja. **No
> tenemos su planilla y no la vamos a inventar.** Los conteos son reales y se
> auditan uno por uno; los supuestos están todos aquí y son un parámetro.
> Díganos el número correcto y el tablero se recalcula.»

Ese es el mejor momento para que un juez de ECON se involucre: pedirle el dato
en vez de fingir que lo tenemos.

**El pedido concreto:**

> «Queremos un piloto de 90 días sobre diez máquinas y dos cabezales, con
> acceso de lectura a Nexus y a Startrack. Sin tocar sus sistemas.»

Un pitch que pide algo gana sobre uno que solo describe.

---

## Hilo del pitch (para el deck)

1. ECON invirtió **$18 M** en flota. Las unidades no se paran por falta de
   sistemas: se paran por descoordinación entre taller, obra y logística.
2. Sus propios KPIs lo muestran — CPI saltando de 0.51 a 4.44 — y su propio
   manual explica el mecanismo: el EV depende de bitácoras aprobadas.
3. El Hub **no reemplaza Nexus ni Startrack: los traduce.** Lectura, mapeo
   declarado campo por campo, y clasificación.
4. Lo que devuelve no es un tablero más: es un estado, una acción y un
   responsable, valorizado en dólares.
5. **Lo mismo ya funciona con telemetría OEM y con WhatsApp.** El contrato
   canónico es el mismo; Prisma y Startrack son dos orígenes más.
6. Piloto de 90 días. ROI en menos de cuatro meses.

## Preguntas que van a hacer, y la respuesta

| Pregunta | Respuesta |
|---|---|
| ¿No hace Nexus ya esto? | Nexus valida al **solicitar**. No revisa el cambio de estado después de aprobada la solicitud, y no ve la conexión de Startrack. Ese hueco es el que cubrimos. |
| ¿Lo del CPI es un hecho? | **No, es nuestra hipótesis**, consistente con la regla del EV que documenta su propio manual. Es verificable con sus RDOs pendientes. |
| ¿Esto reemplaza nuestro ERP? | No. Los conecta. Por eso es un contrato canónico y no una plataforma nueva. |
| ¿Y el resto de fuentes? | *(Pestaña **Integración**.)* Caterpillar por ISO 15143-3, Komatsu, Volvo, retrofit J1939 y WhatsApp entran por la misma puerta y salen con la misma forma. Prisma y Startrack son dos orígenes más, no un caso especial. |
| ¿Captura desde campo? | *(Pestaña **Captura de campo**.)* Nota de voz por WhatsApp → transcripción, entidades, OCR del horómetro y validación cruzada audio/foto. Sin formularios. |
| ¿Funciona en cantera sin señal? | La PWA guarda en el teléfono y sincroniza con clave de idempotencia. *(Modo avión y guardar un registro.)* |
| ¿Usan CRDTs de verdad? | Hoy es un log de mutaciones con precedencia por campo, que converge determinista. El CRDT de conjuntos es roadmap. **No lo vendemos como hecho.** |
| ¿Y las máquinas viejas sin telemetría? | Retrofit sobre bus CAN J1939. En el prototipo es simulador; el hardware es commodity de $40. Lo que probamos es que el Hub no distingue el origen. |
| ¿Cuánto cuesta montarlo? | $45 000 CAPEX incluyendo instrumentación, $15 000/año de operación. |
| ¿Tienen acceso real al sandbox? | No lo tuvimos hoy, y el tablero lo dice en pantalla: *datos simulados*. El conector contra la API real de Startrack **está escrito** (`startrack.py`), contra su documentación oficial — basic auth, `workflow_role`, respeto del límite de 240 peticiones, y el cruce por el No. de activo que define su Diccionario de Datos. Le falta la credencial, no el código. |
| ¿Cómo sabemos que el número no está inflado? | Porque se ve caer. La Pala Volvo, conectada, expone $75 sobre 8 h facturadas y 7.5 h medidas — y ese horómetro (1474 → 1481.55) sale del manual de ustedes, no de nosotros. La KPI se queda callada cuando la máquina está sana. |

## Lo que está construido y NO está en el guion

No es relleno: cada uno tiene pestaña propia y aserciones en `smoke.sh`. Se
abren solo si preguntan.

| Qué | Dónde | Aserciones |
|---|---|---|
| WhatsApp: voz, NER, OCR, validación cruzada | pestaña **Captura de campo** | 3 |
| Cuatro adaptadores OEM + retrofit J1939 | pestaña **Integración** | 6 |
| Conciliación de diésel al 5 % | alertas | 2 |
| Concreto y asfalto perecederos + veda del VMT | pestaña **Despacho** | 9 |
| Precedencia y dueño exclusivo de campo | pestaña **Integración** | 5 |
| ROI: $228 000/año, ROI 2.5 meses | pestaña **Costos** | 2 |
| Conector real de Startrack (apagado, sin API key) | `backend/app/startrack.py` | 3 |
