// Cliente API para Hub de Operaciones — Grupo ECON

class ApiClient {
  constructor() {
    this.baseUrl = localStorage.getItem('ECON_API_URL') || window.ECON_CONFIG.API_BASE;
    this.isOnline = true;
    this.lastSync = null;
    this.listeners = [];
  }

  setBaseUrl(url) {
    this.baseUrl = url.trim().replace(/\/+$/, '');
    localStorage.setItem('ECON_API_URL', this.baseUrl);
    this.notifyStatusChange();
  }

  getBaseUrl() {
    return this.baseUrl;
  }

  onStatusChange(callback) {
    this.listeners.push(callback);
  }

  notifyStatusChange() {
    this.listeners.forEach(cb => cb({ isOnline: this.isOnline, lastSync: this.lastSync, url: this.baseUrl }));
  }

  async request(path, options = {}) {
    const url = `${this.baseUrl}${path}`;
    const method = options.method || 'GET';
    const headers = {
      'Accept': 'application/json',
      'ngrok-skip-browser-warning': 'true',
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(options.headers || {})
    };

    const fetchOptions = {
      method,
      headers,
      ...(options.body ? { body: typeof options.body === 'string' ? options.body : JSON.stringify(options.body) } : {})
    };

    try {
      const response = await fetch(url, fetchOptions);
      if (!response.ok) {
        let errorDetails = '';
        try {
          const errData = await response.json();
          errorDetails = errData.detail ? JSON.stringify(errData.detail) : JSON.stringify(errData);
        } catch {
          errorDetails = response.statusText;
        }
        throw new Error(`HTTP ${response.status}: ${errorDetails}`);
      }

      const data = await response.json();
      this.isOnline = true;
      this.lastSync = new Date();
      this.notifyStatusChange();

      // Guardar en caché local para resiliencia
      if (method === 'GET') {
        try {
          localStorage.setItem(`cache_${path}`, JSON.stringify({ timestamp: Date.now(), data }));
        } catch (e) {
          // ignore localStorage quota
        }
      }

      return data;
    } catch (err) {
      console.warn(`[API] Error al consultar ${url}:`, err.message);
      this.isOnline = false;
      this.notifyStatusChange();

      // Si es GET y tenemos caché, usar respaldo
      if (method === 'GET') {
        const cached = localStorage.getItem(`cache_${path}`);
        if (cached) {
          try {
            const parsed = JSON.parse(cached);
            console.info(`[API] Utilizando datos de respaldo en caché para ${path}`);
            return parsed.data;
          } catch (e) {
            // ignore
          }
        }
      }
      throw err;
    }
  }

  // Métodos de conveniencia
  getHealth() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.health);
  }

  getAssets(params = {}) {
    let query = '';
    const searchParams = new URLSearchParams();
    if (params.estado) searchParams.append('estado', params.estado);
    if (params.obra) searchParams.append('obra', params.obra);
    const qs = searchParams.toString();
    if (qs) query = `?${qs}`;
    return this.request(`${window.ECON_CONFIG.ENDPOINTS.assets}${query}`);
  }

  getAssetDetail(id) {
    return this.request(window.ECON_CONFIG.ENDPOINTS.assetDetail(id));
  }

  closeAssetService(id) {
    return this.request(window.ECON_CONFIG.ENDPOINTS.assetService(id), { method: 'POST' });
  }

  getProjects() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.projects);
  }

  getAlerts(status = 'abierta', limit = 50) {
    return this.request(`${window.ECON_CONFIG.ENDPOINTS.alerts}?status=${encodeURIComponent(status)}&limit=${limit}`);
  }

  closeAlert(id) {
    return this.request(window.ECON_CONFIG.ENDPOINTS.closeAlert(id), { method: 'POST' });
  }

  getCorridors() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.corridors);
  }

  getDispatches() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.dispatch);
  }

  createDispatch(payload) {
    return this.request(window.ECON_CONFIG.ENDPOINTS.dispatch, { method: 'POST', body: payload });
  }

  confirmDispatch(id) {
    return this.request(window.ECON_CONFIG.ENDPOINTS.confirmarDispatch(id), { method: 'POST' });
  }

  checkDispatchCarga(payload) {
    return this.request(window.ECON_CONFIG.ENDPOINTS.dispatchCarga, { method: 'POST', body: payload });
  }

  getCargas(estado = null) {
    const q = estado ? `?estado=${encodeURIComponent(estado)}` : '';
    return this.request(`${window.ECON_CONFIG.ENDPOINTS.cargas}${q}`);
  }

  dosificarCarga(payload) {
    return this.request(window.ECON_CONFIG.ENDPOINTS.dosificar, { method: 'POST', body: payload });
  }

  dictaminarLab(payload) {
    return this.request(window.ECON_CONFIG.ENDPOINTS.dictaminarLab, { method: 'POST', body: payload });
  }

  getConnectors() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.connectors);
  }

  getContract() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.contract);
  }

  getAnalytics() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.analytics);
  }

  getPsMaquinas() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.psMaquinas);
  }

  getPsVistaUnificada(maquinaria) {
    return this.request(window.ECON_CONFIG.ENDPOINTS.psVistaUnificada(maquinaria));
  }

  getPsSangrado(area = null) {
    const q = area ? `?area=${encodeURIComponent(area)}` : '';
    return this.request(`${window.ECON_CONFIG.ENDPOINTS.psSangrado}${q}`);
  }

  getPsGeocercas() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.psGeocercas);
  }

  getPsMapeo() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.psMapeo);
  }

  getPsPea() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.psPea);
  }

  emitirPea(maquinaria, aprobadoPor, proyectoId = null) {
    let q = `?aprobado_por=${encodeURIComponent(aprobadoPor)}`;
    if (proyectoId) q += `&proyecto_id=${encodeURIComponent(proyectoId)}`;
    return this.request(`${window.ECON_CONFIG.ENDPOINTS.psPeaEmitir(maquinaria)}${q}`, { method: 'POST' });
  }

  verificarPea(id) {
    return this.request(window.ECON_CONFIG.ENDPOINTS.psPeaVerificar(id));
  }

  getSinteticoEstado() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.sinteticoEstado);
  }

  generarSintetico(equipos = 120, seed = 42) {
    return this.request(`${window.ECON_CONFIG.ENDPOINTS.sinteticoGenerar}?equipos=${equipos}&seed=${seed}`, { method: 'POST' });
  }

  limpiarSintetico() {
    return this.request(window.ECON_CONFIG.ENDPOINTS.sinteticoLimpiar, { method: 'POST' });
  }

  getStartrackWebhookEjemplo(remoteId = 'EXC-17006EC') {
    return this.request(window.ECON_CONFIG.ENDPOINTS.sinteticoWebhookEjemplo(remoteId));
  }

  sendStartrackUbicacion(payload) {
    return this.request(window.ECON_CONFIG.ENDPOINTS.startrackUbicaciones, { method: 'POST', body: payload });
  }

  sendStartrackAlerta(payload) {
    return this.request(window.ECON_CONFIG.ENDPOINTS.startrackAlertas, { method: 'POST', body: payload });
  }
}

window.apiClient = new ApiClient();
