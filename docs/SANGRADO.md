# Dónde sangra la compañía — y quién lo ve

Los organizadores confirmaron cómo está partida la operación en ECON:
**Maquinaria, Logística y Proyectos**. Tres áreas, tres pérdidas distintas,
tres pantallas distintas. Un tablero que les muestra lo mismo a las tres no le
sirve a ninguna.

Esto no es una vista más: es lo que conecta el Hub con la tercera fricción del
reto —*responsables de la información*— del lado del negocio en vez del lado
del dato.

## La regla de honestidad

**Los conteos salen de la base y son auditables uno por uno. Los costos
unitarios son supuestos nuestros.** No tenemos la planilla de ECON ni su
tarifa de cama baja.

Cada cifra derivada viaja con dos campos separados:

- `base_medida` — lo que contamos de verdad
- `supuesto_aplicado` — lo que asumimos, con su valor, unidad y fuente

Todos los supuestos están en un solo lugar (`SUPUESTOS`, en `sangrado.py`) y
son configurables por variable de entorno. En la demo eso permite decirle a un
juez de ECON **«cambiame este número»** y que el tablero responda en vivo.

Inventar el costo-hora administrativo de una empresa salvadoreña frente a
alguien que la conoce es la forma más rápida de perder todo el crédito
ganado. Preguntárselo lo vuelve cómplice del cálculo.

| Supuesto | Defecto | Variable |
|---|---|---|
| Minutos de una conciliación manual | 12 | `HUB_MIN_CONCILIACION` |
| Costo hora administrativa | $9.00 | `HUB_COSTO_HORA_ADMIN` |
| Costo de un traslado perdido | $380 | `HUB_COSTO_TRASLADO` |
| Conciliaciones por operación/semana | 3 | `HUB_CONCILIACIONES_SEMANA` |

## Qué ve cada área

### Maquinaria — dueña del activo
> *¿Alguno de mis equipos va a salir a carretera sin estar en condiciones, o
> dejó de reportar?*

Equipos no operables con traslado vivo · equipos asignados que no confirman
operación · equipos sin ninguna medición de horas. **Las tres son medidas,
sin ningún supuesto encima.**

Nexus valida al *solicitar*; nadie revisa el cambio de estado **después** de
aprobada la solicitud. Ese hueco es de esta área y hoy no lo ve nadie.

La decisión de si un equipo sale **es de Maquinaria**, no de Logística. Vale
la pena poder defender ese reparto: Logística ejecuta el traslado, pero no
autoriza una máquina averiada.

### Logística — mueve el equipo
> *¿Qué traslados tengo comprometidos que no se van a poder cumplir, y cuánto
> tiempo gasta mi gente cuadrando sistemas?*

Solicitudes aprobadas sin unidad asignada · costo de los traslados que no se
pueden cumplir · **horas-persona por semana cruzando las dos plataformas a
mano**.

Esa última es la pérdida que nadie contabiliza, porque está repartida en ratos
de veinte minutos entre varias personas. Es mano de obra pura, y es el trabajo
que el Hub no acelera: lo elimina.

### Proyectos — consume el equipo y paga las horas
> *¿Qué le estoy cargando a mis partidas sin evidencia, y qué frentes están
> parados esperando equipo?*

Horas cargadas sin respaldo · Costo Real sin Valor Ganado en contra ·
**qué partidas WBS reciben horas sin respaldo, nombradas una por una** ·
frentes esperando una unidad que nunca se asignó.

Proyectos no recibe alertas operativas — recibe el costo. Es el área que
sufre el CPI distorsionado del minuto 1 del guion.

## Endpoint

`GET /api/ps/sangrado` devuelve las tres áreas con sus cifras, los supuestos
completos y la base medida de cada una.

`GET /api/ps/sangrado?area=maquinaria` (o `logistica`, o `proyectos`) filtra a
una sola, para que el tablero de cada jefe cargue solo lo suyo. Un área que no
existe responde 400.
