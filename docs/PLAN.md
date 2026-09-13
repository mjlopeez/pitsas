# Plan del día

Plan completo, visual y compartible (roles, reloj hora por hora, hitos, riesgos):
**https://claude.ai/code/artifact/b29e0348-b078-45c0-97bf-083f98fb5d83**

## Resumen

12 horas de reloj (08:00 → 20:00), 36 horas-persona.

| Hito | Hora | Criterio | Si no está |
|---|---|---|---|
| **M1** | 10:30 | Un evento entra por HTTP y aparece en el mapa, de punta a punta | se recorta la PWA offline |
| **M2** | 13:00 | Mensaje de WhatsApp → evento canónico → marcador rojo | se abandona el trámite de Meta, se usa el simulador |
| **M3** | 15:00 | Nota de voz + OCR funcionando; la veda reprograma la salida | la demo se cuenta con datos sembrados y voz pregrabada |
| **Congelamiento** | 17:00 | Cero funciones nuevas, cero refactors | — |
| **M4** | 19:00 | Tres ensayos cronometrados + video de respaldo grabado | — |

Los hitos no son metas de ánimo: son **puntos de decisión**. Si M1 no está a
las 10:30, se recorta alcance ahí mismo y no a las 18:00 cuando ya no hay nada
que hacer.

## Lo que ya está construido

El andamiaje de este repo cubre, verificado y corriendo:

- contrato canónico con precedencia por campo y tickets de conciliación
- los cuatro adaptadores (CAT, Komatsu, Volvo, retrofit J1939) con rechazo visible
- pipeline de campo completo: voz → NER → OCR → validación cruzada → evento
  *(extrae 4 520 h de «cuatro mil quinientas veinte», sin llaves de API)*
- motor de veda del VMT con desvío y reprogramación
- reglas de mantenimiento (240/250 h), ralentí (15 min) y conciliación de diésel (5 %)
- Command Center con mapa en vivo por SSE, chips de procedencia, panel de
  conectores, panel de despacho con la veda dibujada y tablero de ROI
- PWA de campo offline con cola en IndexedDB e idempotencia
- flota sintética de 150 unidades con geocercas de obras reales y emisor de telemetría
- capa de IA sobre Xiaomi MiMo (`mimo-v2.5-pro` para NER, `mimo-v2.5` para voz
  e imagen) con respaldo automático por reglas si no hay llave o si falla la red
- conciliación de diésel al 5 % conectada al orquestador y estado
  `EN_MANTENIMIENTO` con cierre de servicio por el taller

El estado vivo está en `docs/ESTADO.md`, no aquí: este archivo es el plan, ese
es el avance.

## Lo que falta y quién lo hace

| Pendiente | Dueño | Ventana |
|---|---|---|
| Alta en Meta / WhatsApp Business, token y webhook verificado | Emily | 08:00–09:00, timebox duro |
| Verificar coordenadas de obras y la matriz real del VMT | Emily | antes de 12:00 |
| Ampliar catálogo de modelos con el equipo real de ECON | Emily | 09:00–12:00 |
| Bajar media del webhook de WhatsApp (audio y foto) | Wilbert | 10:00–13:00 |
| Spike de MiMo (`docs/mimo-spike.md`) — **bloqueante** | Wilbert | 08:15–08:45 |
| Probar transcripción con la voz de Josué | Wilbert + Josué | 15:00 |
| Input de archivo real para la foto del tablero | Majo | 15:00–17:00 |
| Pulido visual y tablero de analítica | Majo | 17:00–20:00 |
| Integración E2E, guion, deck, ensayos, video | Josué | 15:00–20:00 |
