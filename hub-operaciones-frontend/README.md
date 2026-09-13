# Hub de Operaciones — Grupo ECON (Frontend Web)

Frontend interactivo, dinámico y moderno con paleta azul de alta tecnología para la torre de control de maquinaria, materiales y logística de **Grupo ECON El Salvador**, conectado a la API de backend en `https://ebook-shun-moonwalk.ngrok-free.dev`.

---

## 🚀 Inicio Rápido

Para iniciar el servidor local en tu equipo:

```bash
cd /Users/mjlopez/.gemini/antigravity/scratch/hub-operaciones-frontend
node server.js
```

Abre en tu navegador:
👉 **[http://localhost:3001](http://localhost:3001)** (o el puerto indicado en la consola si el 3000 está ocupado).

---

## 🎨 Paleta de Colores & Diseño

- **Fondo Primario**: Deep Navy Blue (`#070e1e` a `#0a172e`) con gradiente sutil.
- **Tarjetas y Superficies**: Glassmorphism (`rgba(13, 27, 51, 0.75)`) con bordes zafiro y blur de 14px.
- **Acentos**:
  - Azul Eléctrico / Real (`#2563eb` y `#1d4ed8`): Acciones principales, botones y pestañas activas.
  - Cyan Neón (`#06b6d4`): Horómetros, telemetría y contadores de vida de material.
  - Esmeralda (`#10b981`): Motor encendido (ON), cargas válidas y beneficios económicos.
  - Ámbar (`#f59e0b`): Ralentí (IDLE), advertencias de veda VMT y tiempos próximos a fraguado.
  - Carmesí (`#f43f5e`): Alertas críticas, sobrecostos expuestos y cargas retenidas por laboratorio.

---

## 📦 Módulos y Funcionalidades

### 1. 📊 Dashboard & KPIs
- Indicadores en tiempo real: Flota total (152 equipos), ahorro proyectado (\$228,000 USD/año, 30,000 gal diésel), lotes de material y costo expuesto en silos (\$1,284.5+ USD).
- Gráficos interactivos **Chart.js**: Distribución de maquinaria por tipo y desglose del modelo económico.
- Semáforo y ticker de restricciones horarias VMT.
- Comparativa cuantitativa: Operación manual vs Automatizada con Hub ECON.

### 2. 🗺️ Mapa & Geocercas (Leaflet)
- Mapa satelital centrado en **El Salvador**.
- Geocercas circulares translúcidas para los **18 proyectos y plantas** (San Salvador, La Libertad, Sonsonate, San Miguel, Claudia Lars, Utila, Aeropuerto, etc.).
- Marcadores de vehículos con código de color dinámico por estado de motor (`ON`, `IDLE`, `OFF`).
- Popups con fichas rápidas y acceso al modal de telemetría completa.

### 3. 🚜 Flota ISO 15143-3
- Búsqueda en tiempo real por identificador, marca o modelo.
- Filtros multicriterio: Obra asignada, estado de motor (`ON`, `IDLE`, `OFF`) y categoría de maquinaria.
- Vista intercambiable entre **Cuadrícula de Tarjetas** y **Tabla Detallada**.
- Barra de progreso del ciclo de mantenimiento preventivo (intervalos de 250 horas).
- Modal de ficha técnica completa y acción de **Cerrar Servicio de Taller** (`POST /api/assets/{id}/servicio`).

### 4. ⚖️ Conciliación Prisma vs Startrack & Sangrado Operativo
- Cruce automático de **ERP Nexus** (horas facturadas por jornada mínima) vs **Startrack** (ignición satelital medida).
- Vista unificada lado a lado con diagnóstico de impacto y costo expuesto.
- Tablero de **Sangrado Operativo** con segmentación en Maquinaria, Logística y Proyectos, diferenciando base medida real de supuestos aplicados.
- Emisión de **Pruebas de Evidencia Automatizadas (PEA)** con sello criptográfico SHA-256 y validador de integridad.

### 5. ⏳ Materiales, Concreto & Laboratorio
- **Reloj de Vida Decreciente en Vivo**: Contador regresivo en tiempo real que descuenta minuto a minuto la manejabilidad del concreto y asfalto en carretera.
- Alerta visual inmediata si el lote vence o es marcado como retenido.
- Formulario modal para **Dosificar Nueva Carga** (`POST /ingest/planta`) con planta de origen, obra de destino, diseño de mezcla y temperatura.
- Formulario de **Dictamen de Laboratorio** (`POST /ingest/lab`) con retención instantánea de lote en caso de no conformidad.

### 6. 🚦 Vedas VMT & Despacho
- Catálogo de corredores viales clave: Panamericana Poniente (Los Chorros), Bulevar Monseñor Romero, Autopista a Comalapa y Bypass Quezaltepeque.
- Horarios de restricción matutina (06:00-09:00) y vespertina (15:30-19:30).
- **Validador de Despacho en Tiempo Real**: Evalúa algorítmicamente si un vehículo puede salir inmediatamente o si debe desviarse por Quezaltepeque (+40 min).

### 7. 🔌 Conectores & Simulación
- Monitor de salud de 7 canales de ingesta: Caterpillar OEM, Komatsu, Volvo CE, Sensores Retrofit CAN J1939, WhatsApp de campo, OCR de tableros y PWA offline.
- Generador de inventarios sintéticos deterministas con seed para pruebas de estrés.

---

## ⚙️ Conectividad con Ngrok

La aplicación envía en todas las cabeceras el header:
```http
ngrok-skip-browser-warning: true
```
Si el túnel ngrok cambia en el futuro, puedes actualizar la URL directamente desde el botón **API Conectada / Configuración** en la esquina superior derecha sin reiniciar el servidor.
