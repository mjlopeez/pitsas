# Roadmap — lo que no entró en 12 horas

Este archivo tiene dos usos: es el destino de todo lo que alguien proponga
después de las 16:00, y es la diapositiva de cierre del pitch.

Se nombra como roadmap explícito frente al jurado. Decirlo así suma
credibilidad; presentar cualquiera de estas cosas como hecha se cae en la
primera pregunta técnica.

## Integridad de datos distribuidos

**Hoy:** log de mutaciones append-only con clave de idempotencia por registro
(`dispositivo:secuencia:reloj`) y resolución por precedencia de campo en el
servidor. Converge de forma determinista, que es lo que el caso de uso necesita.

**Roadmap:** CRDTs de conjuntos con marcas temporales vectoriales, para que dos
supervisores puedan editar listas del mismo activo sin que una gane sobre la
otra. Hace falta cuando varias cuadrillas registren inspecciones simultáneas
sobre la misma máquina en la misma jornada sin cobertura.

## Retrofit de telemetría en flota legada

**Hoy:** simulador que emite tramas J1939 (SPN 247 horas de motor, SPN 250
combustible total, DM1 códigos activos) con el mismo contrato canónico que la
telemetría de fábrica.

**Roadmap:** módulo ESP32 o Quectel con GNSS y conectividad celular en el puerto
de diagnóstico. Hardware commodity de ~$40 por unidad; la instrumentación de
150 activos está presupuestada dentro de los $45 000 de CAPEX. No se pudo
demostrar en el hackatón porque requiere una máquina real y permiso de ECON
para conectarse a su bus.

## Infraestructura de escala

| Hoy | Roadmap | Cuándo hace falta |
|---|---|---|
| Tabla `events` + bus en memoria | Apache Kafka | cuando la telemetría pase de ~50 eventos/s |
| SQLite | PostgreSQL + TimescaleDB | desde el día uno de producción; Timescale es una extensión, no un rediseño |
| Máquina de estados en Python | Temporal.io | cuando los flujos necesiten durabilidad y reintentos ante caídas |
| Vista de analítica | Apache Superset | cuando gerencia quiera armar sus propios tableros |

## Integraciones empresariales reales

**Hoy:** el contrato canónico y los adaptadores de entrada están listos; la
salida hacia ERP y CMMS está modelada pero no conectada.

**Roadmap:** conectores bidireccionales con el ERP (facturación por horómetro,
contabilidad de proyectos) y el CMMS del taller (órdenes de trabajo, inventario
de repuestos). Es trabajo de integración con sistemas de ECON que requiere
acceso, credenciales y un responsable de cada lado — precisamente la tercera
fricción que el reto nombra, y la razón por la que el Hub declara precedencia
por campo antes de escribir en ningún sistema ajeno.

## Mantenimiento predictivo

**Hoy:** mantenimiento preventivo por horómetro real (240 de 250 h) en lugar de
por calendario, más captura temprana de códigos de falla.

**Roadmap:** modelos sobre las series de tiempo de presiones hidráulicas,
temperaturas y consumo para anticipar fallas antes de que aparezca el DTC.
Necesita histórico real de la flota; con datos sintéticos un modelo así no
demuestra nada.

## Piloto propuesto

**90 días, 10 máquinas y 2 cabezales.** Suficiente para medir los tres KPI del
modelo financiero (ralentí, tiempo de respuesta de despacho, desfase de
facturación) contra la línea base real de ECON, y para validar que los
operadores adoptan la captura por WhatsApp sin resistencia.
