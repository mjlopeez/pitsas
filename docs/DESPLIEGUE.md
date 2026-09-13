# Despliegue — una laptop, un comando

El Hub corre en **un solo proceso** que sirve la API, el Command Center y la
PWA de campo en el puerto 8000. Sin dev server de Vite, sin segundo puerto,
sin dependencia de internet.

## El comando

```bash
./backend/run.sh --prod
```

Compila el Command Center si hace falta, arranca sin `--reload` y escucha en
`0.0.0.0:8000`. Al terminar imprime las dos URLs:

```
   En esta laptop : http://localhost:8000
   Desde la red   : http://192.168.1.42:8000
```

Esa segunda es la que se le pasa al jurado y al resto del equipo. **Si no
pueden abrirla desde el celular en la misma red, no está desplegado** — esa
es la única prueba que cuenta.

## Qué queda servido

| Ruta | Qué es |
|---|---|
| `/` y `/app` | Command Center |
| `/campo` | PWA de campo (se abre en el celular, sin instalar nada) |
| `/docs` | la API, documentada sola |

## La trampa que ya nos mordió

El `index.html` que produce Vite pide sus assets **en la raíz**:

```html
<script src="/assets/index-XXX.js">
```

Durante un rato solo estaban montados bajo `/app/assets/`. Resultado: la
página cargaba y se quedaba **en blanco**, porque el JS y el CSS daban 404.
Nadie lo notó porque todos corrían `npm run dev` en el 5173 — y desplegar es
exactamente correr sin el dev server.

Por eso `main.py` monta `/assets` aparte, en la raíz, y hay una aserción en
`smoke.sh` que toma el HTML servido, extrae **cada** asset que pide y verifica
que los dos respondan 200. Está probada contra el bug: si se quita el mount,
la prueba falla nombrando los archivos rotos.

**Si alguien cambia el `base` de Vite, esa aserción es la que avisa.**

## Antes de la demo

- [ ] `./scripts/smoke.sh` → 99 verdes
- [ ] `./backend/run.sh --prod` y abrir la URL de red **desde el celular**
- [ ] Hotspot del celular como red, no el wifi del salón
- [ ] `POST /admin/reset` y `POST /admin/seed-ps` → escenario limpio
- [ ] Verificar que la pestaña **Prisma + Startrack** abre en `EXC-01` con
      **$1 200**
- [ ] `POST /api/sintetico/limpiar` si quedó data generada de las pruebas —
      el pitch va con las seis filas reales, no con el inventario sintético
- [ ] Video de respaldo listo

## Si algo falla en vivo

| Síntoma | Qué es |
|---|---|
| Pantalla en blanco | Los assets. Recompilar: `cd frontend && npm run build` |
| El tablero dice «simulado» | Es correcto y es honesto: no hay credenciales cargadas |
| Nadie entra desde la red | El firewall de la laptop, o están en otra red |
| Números distintos a los del guion | Quedó data sintética: `POST /api/sintetico/limpiar` |
