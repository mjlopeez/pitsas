# PEA — Protocolo de Ejecución Automatizada

**Decisión del 13/09: se elimina la capa on-chain.** Lo que era un escrow con
contrato `MachineryEscrow`, RPC y llaves privadas pasa a ser un protocolo de
evidencia que corre dentro del Hub. Este documento explica por qué, qué se
gana, qué se pierde y cómo se responde a la pregunta difícil.

## Por qué sin cadena

**El reto nunca pidió blockchain.** Pidió romper silos. Una cadena agregaba un
sistema nuevo que ECON tendría que adoptar, y eso contradice nuestra propia
tesis — *el Hub no reemplaza sus sistemas, los traduce*. Un protocolo que
corre **sobre** Nexus y Startrack no les pide adoptar nada.

**El mecanismo no la necesitaba.** Lo que da valor es que la evidencia sea
determinista y la regla se ejecute sola. El log `events` ya es append-only y
la precedencia por campo ya define quién es dueño de cada dato.

**Y saca el riesgo del escenario.** Sin RPC, sin llaves privadas en un `.env`,
sin gas, sin testnet que se cae. Cada cosa que sale del camino de la demo es
una cosa menos que se puede romper en vivo.

## La pregunta difícil, y su respuesta

> «Sin cadena, ¿por qué le creo al hash?»

Porque **es recomputable**. Cualquiera con acceso de lectura a Nexus y a
Startrack puede reconstruir el registro y obtener el mismo hash. Verificar no
exige confiar en el Hub: exige leer los sistemas que ECON ya tiene.

`GET /api/ps/pea/{id}/verificar` hace exactamente eso en pantalla — recalcula
el hash desde el contenido guardado y muestra los dos lado a lado.

Lo que **sí** se pierde: inmutabilidad ante terceros. Con cadena, ni ECON ni
el contratista pueden reescribir la historia por su cuenta. Sin cadena, el
Hub es el custodio. Si eso llega a importar para un contrato real, la cadena
es roadmap y el registro ya está en la forma correcta para anclarse.

## No automatiza la decisión

`aprobado_por` es **siempre una persona**. El Hub automatiza la evidencia que
la aprobación necesita, no la aprobación.

Decirlo así importa: «ejecución automatizada» a un CFO le puede sonar a que
se paga solo, y eso asusta en lugar de convencer.

## Los dos montos que no hay que confundir

| Campo | Qué es |
|---|---|
| `monto_facturable` | Lo que Nexus cobra: `max(horas medidas, mínimo) × tarifa` |
| `exposicion_usd` | Lo que se cobra **sin respaldo** de operación medida |

En un equipo sano el primero es alto y el segundo casi cero — la Pala Volvo
factura $1 200 y expone $75. **Si los dos coinciden es que no hay medición**,
y el registro lo declara en `medicion: "sin datos"` en vez de dejarlo a la
interpretación. EXC-01 es justo ese caso: $1 200 y $1 200.

⚠️ En el guion hay que etiquetarlos sin ambigüedad. Son el mismo número con
significados opuestos en la misma tarjeta.

## El sello

SHA-256 sobre la forma canónica del registro — llaves ordenadas, sin espacios,
UTF-8 — excluyendo el propio campo `hash`. Sin dependencias de cadena.

Si esa serialización cambia, **todos los hashes emitidos dejan de verificar**.
No se toca `_canonico()` sin migrar lo ya emitido.

## Endpoints

| Método | Ruta | Para qué |
|---|---|---|
| POST | `/api/ps/pea/{maquinaria}?aprobado_por=...` | sella la evidencia de la operación |
| GET | `/api/ps/pea` | los últimos 50 registros |
| GET | `/api/ps/pea/{id}/verificar` | recomputa el hash y lo compara |

La tabla `pea_registros` es append-only, igual que `events`: un registro
sellado nunca se corrige — se emite otro.
