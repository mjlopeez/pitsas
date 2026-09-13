// Configuración Central del Hub de Operaciones — Grupo ECON

// Detección automática del proxy local o conexión directa
const isHttpServer = typeof window !== 'undefined' && window.location && window.location.protocol.startsWith('http');
const defaultBase = isHttpServer ? '' : 'https://ebook-shun-moonwalk.ngrok-free.dev';

window.ECON_CONFIG = {
  // URL base de la API backend (usa proxy local transparente para celulares/desktop si está disponible)
  API_BASE: defaultBase,
  DIRECT_NGROK_BASE: 'https://ebook-shun-moonwalk.ngrok-free.dev',
  
  // Intervalo de auto-refresco por defecto en milisegundos (15s)
  AUTO_REFRESH_INTERVAL: 15000,

  // Headers requeridos por ngrok free tier y backend
  HEADERS: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true'
  },

  // Mapa exhaustivo de endpoints de la API
  ENDPOINTS: {
    health: '/health',
    assets: '/api/assets',
    assetDetail: (id) => `/api/assets/${encodeURIComponent(id)}`,
    assetService: (id) => `/api/assets/${encodeURIComponent(id)}/servicio`,
    projects: '/api/projects',
    alerts: '/api/alerts',
    closeAlert: (id) => `/api/alerts/${encodeURIComponent(id)}/cerrar`,
    corridors: '/api/dispatch/corridors',
    dispatch: '/api/dispatch',
    dispatchCarga: '/api/dispatch/carga',
    confirmarDispatch: (id) => `/api/dispatch/${encodeURIComponent(id)}/confirmar`,
    cargas: '/ingest/cargas',
    dosificar: '/ingest/planta',
    dictaminarLab: '/ingest/lab',
    connectors: '/api/connectors',
    contract: '/api/contract',
    analytics: '/api/analytics',
    psMaquinas: '/api/ps/maquinas',
    psVistaUnificada: (maq) => `/api/ps/vista-unificada/${encodeURIComponent(maq)}`,
    psSangrado: '/api/ps/sangrado',
    psGeocercas: '/api/ps/geocercas',
    psMapeo: '/api/ps/mapeo',
    psPea: '/api/ps/pea',
    psPeaEmitir: (maq) => `/api/ps/pea/${encodeURIComponent(maq)}`,
    psPeaVerificar: (id) => `/api/ps/pea/${encodeURIComponent(id)}/verificar`,
    sinteticoEstado: '/api/sintetico/estado',
    sinteticoGenerar: '/api/sintetico/generar',
    sinteticoLimpiar: '/api/sintetico/limpiar',
    sinteticoWebhookEjemplo: (id) => `/api/sintetico/webhook-ejemplo/${encodeURIComponent(id)}`,
    startrackUbicaciones: '/webhooks/startrack/ubicaciones',
    startrackAlertas: '/webhooks/startrack/alertas'
  }
};
