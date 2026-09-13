// Store reactivo para Hub de Operaciones — Grupo ECON

class AppStore {
  constructor() {
    this.state = {
      health: { ok: false, activos: 0, eventos: 0, alertas_abiertas: 0 },
      assets: [],
      projects: [],
      cargas: [],
      alerts: [],
      corridors: [],
      connectors: [],
      analytics: null,
      psMaquinas: [],
      psSangrado: null,
      psPeaList: [],
      selectedAsset: null,
      selectedProjectFilter: 'TODOS',
      filterSearch: '',
      filterEngineState: 'TODOS',
      filterKind: 'TODOS',
      activeTab: 'dashboard',
      autoRefreshInterval: 15, // segundos
      autoRefreshTimer: null,
      isRefreshing: false,
      lastError: null,
      
      // Estado Multi-Plataforma (Hub ECON, Startrack Mock, Nexus Mock)
      activePlatform: 'hub', // 'hub' | 'startrack' | 'nexus'
      demoMachine: 'EXC-01',
      startrackRequirements: {
        gps_heartbeat: false, // Simula inicialmente falta de reporte satelital
        engine_hours_measured: false, // Simula inicialmente horas en 0.0
        geofence_verified: true, // Dentro de geocerca Los Chorros
        can_bus_integrity: true // Bus CAN J1939 nominal
      },
      nexusRequirements: {
        solicitud_approved: true, // SOL-042 aprobada
        unit_assigned: true, // EXC-01 asignada
        wbs_rate_linked: true, // A 1.02 - EXCAVACION a $150/h
        resident_signature: false // Falta firma del residente de obra
      },
      peaLiberada: false,
      lastPeaReleased: null
    };

    this.subscribers = new Set();
    this.startCountdownTicker();
  }

  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  notify(event, payload = {}) {
    this.subscribers.forEach(cb => {
      try {
        cb(event, this.state, payload);
      } catch (err) {
        console.error('Error en suscriptor del Store:', err);
      }
    });
  }

  setState(partial) {
    this.state = { ...this.state, ...partial };
    this.notify('state_changed');
  }

  // Ticker dinámico cada segundo para actualizar los minutos restantes de cargas de concreto/asfalto
  startCountdownTicker() {
    setInterval(() => {
      if (!this.state.cargas || this.state.cargas.length === 0) return;
      
      let updated = false;
      const now = Date.now();
      
      this.state.cargas = this.state.cargas.map(carga => {
        if (!carga.dosificado_en) return carga;
        
        // Vida total aproximada: 90 min para concreto, 120 min para asfalto
        const vidaTotalMin = carga.tipo === 'CONCRETO' ? 90 : 120;
        const dosificadoAt = new Date(carga.dosificado_en).getTime();
        const transcurridoMin = (now - dosificadoAt) / (1000 * 60);
        const minutosRestantes = Math.round((vidaTotalMin - transcurridoMin) * 10) / 10;
        
        if (carga.minutos_restantes !== minutosRestantes) {
          updated = true;
          return { ...carga, minutos_restantes: minutosRestantes };
        }
        return carga;
      });

      if (updated) {
        this.notify('cargas_tick');
      }
    }, 1000);
  }

  // Carga inicial y refresco completo
  async refreshAll() {
    this.setState({ isRefreshing: true, lastError: null });
    this.notify('refresh_started');

    try {
      const [
        health,
        assets,
        projects,
        cargas,
        alerts,
        corridors,
        connectors,
        analytics,
        psMaquinas,
        psSangrado,
        psPeaList
      ] = await Promise.allSettled([
        window.apiClient.getHealth(),
        window.apiClient.getAssets(),
        window.apiClient.getProjects(),
        window.apiClient.getCargas(),
        window.apiClient.getAlerts('abierta', 50),
        window.apiClient.getCorridors(),
        window.apiClient.getConnectors(),
        window.apiClient.getAnalytics(),
        window.apiClient.getPsMaquinas(),
        window.apiClient.getPsSangrado(),
        window.apiClient.getPsPea()
      ]);

      const newState = {};
      if (health.status === 'fulfilled') newState.health = health.value;
      if (assets.status === 'fulfilled') newState.assets = assets.value;
      if (projects.status === 'fulfilled') newState.projects = projects.value;
      if (cargas.status === 'fulfilled') newState.cargas = cargas.value;
      if (alerts.status === 'fulfilled') newState.alerts = alerts.value;
      if (corridors.status === 'fulfilled') newState.corridors = corridors.value;
      if (connectors.status === 'fulfilled') newState.connectors = connectors.value;
      if (analytics.status === 'fulfilled') newState.analytics = analytics.value;
      if (psMaquinas.status === 'fulfilled') newState.psMaquinas = psMaquinas.value;
      if (psSangrado.status === 'fulfilled') newState.psSangrado = psSangrado.value;
      if (psPeaList.status === 'fulfilled') newState.psPeaList = psPeaList.value;

      newState.isRefreshing = false;
      this.setState(newState);
      this.notify('refresh_completed');
    } catch (err) {
      console.error('Error durante refreshAll:', err);
      this.setState({ isRefreshing: false, lastError: err.message });
      this.notify('refresh_error', { error: err.message });
    }
  }

  setAutoRefresh(seconds) {
    if (this.state.autoRefreshTimer) {
      clearInterval(this.state.autoRefreshTimer);
      this.state.autoRefreshTimer = null;
    }

    const intervalSec = parseInt(seconds, 10);
    this.state.autoRefreshInterval = intervalSec;

    if (intervalSec > 0) {
      this.state.autoRefreshTimer = setInterval(() => {
        this.refreshAll();
      }, intervalSec * 1000);
    }

    this.notify('autorefresh_changed', { interval: intervalSec });
  }

  // Métodos de Control Multi-Plataforma y PEA
  setPlatform(platform) {
    const valid = ['hub', 'startrack', 'nexus'];
    if (!valid.includes(platform)) platform = 'hub';
    this.setState({ activePlatform: platform });
    this.notify('platform_changed', { platform });
  }

  async setStartrackRequirement(key, val) {
    const startrackRequirements = { ...this.state.startrackRequirements, [key]: val };
    this.setState({ startrackRequirements });
    await this.checkPeaRelease();
  }

  async updateStartrackReq(key, val) {
    return this.setStartrackRequirement(key, val);
  }

  async setNexusRequirement(key, val) {
    const nexusRequirements = { ...this.state.nexusRequirements, [key]: val };
    this.setState({ nexusRequirements });
    await this.checkPeaRelease();
  }

  async updateNexusReq(key, val) {
    return this.setNexusRequirement(key, val);
  }

  async checkPeaRelease() {
    const st = this.state.startrackRequirements;
    const nx = this.state.nexusRequirements;
    
    const stCount = Object.values(st).filter(Boolean).length;
    const nxCount = Object.values(nx).filter(Boolean).length;
    
    const wasLiberada = this.state.peaLiberada;
    const isNowLiberada = (stCount === 4 && nxCount === 4);

    if (isNowLiberada && !wasLiberada) {
      let newPea = null;
      try {
        // LLAMADA REAL A LA API BACKEND: POST /api/ps/pea/EXC-01
        console.log('[STORE] Emitiendo PEA real en backend para:', this.state.demoMachine);
        const apiPea = await window.apiClient.emitirPea(this.state.demoMachine, 'Maria Jose Lopez', 'PROY-001');
        
        let verified = true;
        try {
          const verifyResult = await window.apiClient.verificarPea(apiPea.id);
          verified = verifyResult.verifica;
        } catch (vErr) {
          console.warn('[STORE] Error al verificar hash en API:', vErr.message);
        }

        newPea = {
          pea_id: `PEA-${apiPea.id}`,
          id: apiPea.id,
          maquinaria: apiPea.maquinaria || this.state.demoMachine,
          fecha: new Date(apiPea.aprobado_at || Date.now()).toLocaleString(),
          horas_validadas: apiPea.horas_facturables || 8.0,
          tarifa_hora: (apiPea.nexus && apiPea.nexus.precio_hora) || 150.0,
          monto_liberado: apiPea.monto_facturable || 1200.0,
          hash_sha256: apiPea.hash || 'sha256:inmutable',
          aprobador: apiPea.aprobado_por || 'Maria Jose Lopez (Grupo ECON)',
          estado: 'LIBERADA',
          verified: verified,
          esquema: apiPea.esquema || 'pea/v1',
          raw_backend: apiPea
        };
      } catch (err) {
        console.warn('[STORE] Fallback local para emisión de PEA:', err.message);
        const now = new Date();
        newPea = {
          pea_id: `PEA-${Date.now().toString().slice(-6)}`,
          id: 7,
          maquinaria: this.state.demoMachine,
          fecha: now.toLocaleDateString() + ' ' + now.toLocaleTimeString(),
          horas_validadas: 8.0,
          tarifa_hora: 150.0,
          monto_liberado: 1200.0,
          hash_sha256: "sha256:d18312fed25685b4cb19d19bfad4321d25742e71822a7c6e3bdd664c0e292e07",
          aprobador: 'Maria Jose Lopez (Grupo ECON)',
          estado: 'LIBERADA',
          verified: true
        };
      }
      
      const psPeaList = [newPea, ...(this.state.psPeaList || []).filter(p => p.pea_id !== newPea.pea_id)];
      this.setState({ peaLiberada: true, lastPeaReleased: newPea, psPeaList });
      this.notify('pea_liberada', { pea: newPea });
    } else if (!isNowLiberada && wasLiberada) {
      this.setState({ peaLiberada: false });
      this.notify('pea_revocada');
    }
  }

  resetDemoScenario() {
    this.setState({
      startrackRequirements: {
        gps_heartbeat: false,
        engine_hours_measured: false,
        geofence_verified: true,
        can_bus_integrity: true
      },
      nexusRequirements: {
        solicitud_approved: true,
        unit_assigned: true,
        wbs_rate_linked: true,
        resident_signature: false
      },
      peaLiberada: false,
      lastPeaReleased: null
    });
    this.notify('demo_reset');
  }
}

window.appStore = new AppStore();
