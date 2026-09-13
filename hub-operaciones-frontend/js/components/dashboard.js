// Componente Dashboard General — Estética Azul Frío Pizarra & Acero (Amigable & Sin AI Slop)

let fleetChartInstance = null;
let savingsChartInstance = null;

function renderDashboard(container) {
  const state = window.appStore.state;
  const assets = state.assets || [];
  const cargas = state.cargas || [];
  const analytics = state.analytics || {};
  const corridors = state.corridors || [];
  const sangrado = state.psSangrado || {};

  // Desglose de estados de motor
  const engineOn = assets.filter(a => a.engine_state === 'ON').length;
  const engineIdle = assets.filter(a => a.engine_state === 'IDLE').length;
  const engineOff = assets.filter(a => a.engine_state === 'OFF').length;

  // Cargas de concreto
  const cargasRetenidas = cargas.filter(c => c.estado === 'retenida' || c.cumple_especificacion === false).length;
  const cargasEnTransito = cargas.filter(c => c.estado === 'en_transito').length;

  // Sangrado económico
  let sangradoTotalUsd = 0;
  if (sangrado.areas) {
    sangrado.areas.forEach(a => {
      a.cifras.forEach(c => {
        if (c.unidad === 'USD' || c.unidad === 'USD/semana') {
          sangradoTotalUsd += c.valor;
        }
      });
    });
  }

  container.innerHTML = `
    <div class="space-y-6">
      
      <!-- Banner de Bienvenida y Resumen Ejecutivo -->
      <div class="gl-card p-6 sm:p-8 bg-white border border-[#d4dfe8] relative">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-5 relative z-10">
          <div>
            <span class="gl-subtitle text-[#2e5b82] block mb-1">OPERACIONES EN TIEMPO REAL • GRUPO ECON</span>
            <h1 class="font-sans text-2xl sm:text-3xl font-bold text-[#1e293b] tracking-tight">
              Torre de Control de Maquinaria y Materiales
            </h1>
            <div class="gl-separator justify-start my-2"></div>
            <p class="text-xs sm:text-sm text-[#475569] max-w-2xl leading-relaxed">
              Integración continua de telemetría de campo OEM (Caterpillar, Komatsu), sensores CAN J1939 y sincronización de ERP Nexus con rastreo Startrack bajo norma ISO 15143-3 en las 18 obras activas de El Salvador.
            </p>
          </div>
          
          <div class="flex flex-wrap items-center gap-2.5 shrink-0">
            <button onclick="window.switchTab('materials')" class="gl-btn-gold">
              <i data-lucide="plus-circle" class="w-4 h-4"></i>
              <span>Dosificar Concreto</span>
            </button>
            <button onclick="window.switchTab('reconciliation')" class="gl-btn-outline">
              <i data-lucide="git-compare" class="w-4 h-4 text-[#2e5b82]"></i>
              <span>Auditoría Silos</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Métricas Principales (KPI Cards) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <!-- Card 1: Flota Total -->
        <div class="gl-card p-5 bg-white border border-[#d4dfe8]">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold uppercase tracking-wider text-[#64748b]">Total Maquinaria</span>
            <div class="w-8 h-8 rounded-lg bg-[#f1f5f9] border border-[#cbd5e1] flex items-center justify-center text-[#2e5b82]">
              <i data-lucide="truck" class="w-4 h-4 text-[#2e5b82]"></i>
            </div>
          </div>
          <div class="mt-3 flex items-baseline gap-2">
            <span class="font-sans text-3xl font-bold text-[#1e293b] font-mono">${assets.length || 152}</span>
            <span class="text-xs text-[#64748b] font-semibold">unidades</span>
          </div>
          <div class="mt-3 pt-3 border-t border-[#d4dfe8] flex items-center justify-between text-xs text-[#64748b]">
            <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-500"></span> ${engineOn} ON</span>
            <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-amber-500"></span> ${engineIdle} Ralentí</span>
            <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-slate-400"></span> ${engineOff} OFF</span>
          </div>
        </div>

        <!-- Card 2: Beneficio Económico Hub -->
        <div class="gl-card p-5 bg-white border border-[#d4dfe8]">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold uppercase tracking-wider text-[#64748b]">Ahorro Anual Estimado</span>
            <div class="w-8 h-8 rounded-lg bg-[#edf7f2] border border-[#bfe5d3] flex items-center justify-center text-[#2b7a59]">
              <i data-lucide="trending-up" class="w-4 h-4"></i>
            </div>
          </div>
          <div class="mt-3 flex items-baseline gap-2">
            <span class="font-sans text-3xl font-bold text-[#2b7a59] font-mono">$${(analytics.modelo_anual?.beneficio_total || 228000).toLocaleString()}</span>
            <span class="text-xs text-[#64748b]">USD/año</span>
          </div>
          <div class="mt-3 pt-3 border-t border-[#d4dfe8] flex items-center justify-between text-xs text-[#64748b]">
            <span class="text-[#2b7a59] font-semibold">30k gal diésel evitado</span>
            <span class="text-[#64748b]">ROI: 2.5 meses</span>
          </div>
        </div>

        <!-- Card 3: Cargas Vivas de Materiales -->
        <div class="gl-card p-5 bg-white border border-[#d4dfe8]">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold uppercase tracking-wider text-[#64748b]">Cargas de Concreto</span>
            <div class="w-8 h-8 rounded-lg bg-[#f1f5f9] border border-[#cbd5e1] flex items-center justify-center text-[#2e5b82]">
              <i data-lucide="package" class="w-4 h-4"></i>
            </div>
          </div>
          <div class="mt-3 flex items-baseline gap-2">
            <span class="font-sans text-3xl font-bold text-[#1e293b] font-mono">${cargas.length}</span>
            <span class="text-xs text-[#64748b]">lotes activos</span>
          </div>
          <div class="mt-3 pt-3 border-t border-[#d4dfe8] flex items-center justify-between text-xs text-[#64748b]">
            <span class="text-[#1e293b] font-semibold">${cargasEnTransito} en tránsito</span>
            ${cargasRetenidas > 0 
              ? `<span class="gl-badge gl-badge-danger">${cargasRetenidas} RETENIDA</span>` 
              : `<span class="gl-badge gl-badge-success">100% OK</span>`
            }
          </div>
        </div>

        <!-- Card 4: Costo Expuesto Silos -->
        <div class="gl-card p-5 bg-white border border-[#d4dfe8]">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold uppercase tracking-wider text-[#64748b]">Costo Expuesto Silos</span>
            <div class="w-8 h-8 rounded-lg bg-[#fdf2f2] border border-[#f7caca] flex items-center justify-center text-[#a33d3d]">
              <i data-lucide="alert-triangle" class="w-4 h-4"></i>
            </div>
          </div>
          <div class="mt-3 flex items-baseline gap-2">
            <span class="font-sans text-3xl font-bold text-[#a33d3d] font-mono">$${(sangradoTotalUsd || 1696.9).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</span>
            <span class="text-xs text-[#64748b]">USD</span>
          </div>
          <div class="mt-3 pt-3 border-t border-[#d4dfe8] flex items-center justify-between text-xs text-[#64748b]">
            <span class="text-[#a33d3d] font-semibold">Sin respaldo</span>
            <button onclick="window.switchTab('reconciliation')" class="text-[#2e5b82] font-semibold hover:underline">Ver detalle</button>
          </div>
        </div>

      </div>

      <!-- Estado de Vedas VMT y Corredores -->
      <div class="gl-card p-5 sm:p-6 bg-white border border-[#d4dfe8]">
        <div class="flex items-center justify-between mb-3 pb-3 border-b border-[#d4dfe8]">
          <div class="flex items-center gap-2">
            <i data-lucide="shield-alert" class="w-4 h-4 text-[#2e5b82]"></i>
            <h3 class="font-bold text-xs uppercase tracking-wider text-[#1e293b]">Estado de Tránsito Pesado VMT (AMSS & Corredores)</h3>
          </div>
          <button onclick="window.switchTab('dispatch')" class="text-xs text-[#2e5b82] hover:text-[#234563] font-semibold flex items-center gap-1">
            Ver Programación <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
          </button>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          ${corridors.map(cor => {
            const hasVedas = cor.vedas && cor.vedas.length > 0;
            return `
              <div class="p-3.5 rounded-lg border border-[#d4dfe8] bg-[#f8fafc] flex flex-col justify-between">
                <div>
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-xs font-bold text-[#1e293b] truncate" title="${cor.nombre}">${cor.nombre.split('—')[0]}</span>
                    <span class="gl-badge ${hasVedas ? 'gl-badge-gold' : 'gl-badge-success'} text-[9px]">
                      ${hasVedas ? 'Restringido' : 'Vía Libre'}
                    </span>
                  </div>
                  <p class="text-[11px] text-[#64748b] line-clamp-1">${cor.nombre}</p>
                </div>
                <div class="mt-2 text-[11px] font-mono text-[#64748b]">
                  ${hasVedas ? 'Pico 06:00-09:00 / 15:30-19:30' : `Alterna (+${cor.penalidad_min} min)`}
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>

      <!-- Gráficos de Operación y Modelo Económico -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        <!-- Gráfico 1: Desglose de Maquinaria por Tipo -->
        <div class="gl-card p-5 sm:p-6 bg-white border border-[#d4dfe8]">
          <div class="flex items-center justify-between mb-4 pb-3 border-b border-[#d4dfe8]">
            <div>
              <h3 class="font-sans text-lg font-bold text-[#1e293b]">Composición de Flota Activa</h3>
              <p class="text-xs text-[#64748b]">Distribución de maquinaria por categoría de trabajo</p>
            </div>
            <i data-lucide="pie-chart" class="w-4 h-4 text-[#2e5b82]"></i>
          </div>
          <div class="h-64 relative flex items-center justify-center">
            <canvas id="chart-fleet-types"></canvas>
          </div>
        </div>

        <!-- Gráfico 2: Desglose del Beneficio Total -->
        <div class="gl-card p-5 sm:p-6 bg-white border border-[#d4dfe8]">
          <div class="flex items-center justify-between mb-4 pb-3 border-b border-[#d4dfe8]">
            <div>
              <h3 class="font-sans text-lg font-bold text-[#1e293b]">Impacto Económico del Hub (USD/año)</h3>
              <p class="text-xs text-[#64748b]">Ahorro directo en diésel, logística y taller</p>
            </div>
            <i data-lucide="bar-chart-3" class="w-4 h-4 text-[#2b7a59]"></i>
          </div>
          <div class="h-64 relative flex items-center justify-center">
            <canvas id="chart-savings-breakdown"></canvas>
          </div>
        </div>

      </div>

      <!-- KPIs Operativos de Nexus vs Hub de Operaciones -->
      <div class="gl-card p-5 sm:p-6 bg-white border border-[#d4dfe8]">
        <div class="pb-3 mb-3 border-b border-[#d4dfe8]">
          <span class="gl-subtitle text-[#2e5b82] block mb-0.5">BENCHMARK DE EFICIENCIA OPERATIVA</span>
          <h3 class="font-sans text-lg font-bold text-[#1e293b]">Línea Base vs Operación con Hub ECON</h3>
        </div>
        <div class="gl-table-wrap">
          <table class="gl-table">
            <thead>
              <tr>
                <th>Indicador Clave (KPI)</th>
                <th>Línea Base (Manual)</th>
                <th>Con Hub ECON</th>
                <th>Mecanismo de Automatización</th>
              </tr>
            </thead>
            <tbody>
              ${(analytics.kpis || []).map(kpi => `
                <tr>
                  <td class="font-semibold text-[#1e293b]">${kpi.kpi}</td>
                  <td class="text-[#a33d3d] font-mono">${kpi.base}</td>
                  <td class="text-[#2b7a59] font-mono font-bold">${kpi.con_hub}</td>
                  <td class="text-[#475569]">${kpi.mecanismo}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: container });

  // Inicializar Gráficos con Chart.js
  setTimeout(() => initCharts(assets, analytics), 50);
}

function initCharts(assets, analytics) {
  if (typeof Chart === 'undefined') return;

  if (fleetChartInstance) fleetChartInstance.destroy();
  if (savingsChartInstance) savingsChartInstance.destroy();

  // Gráfico 1: Tipos de Máquinas
  const kindCounts = {};
  assets.forEach(a => {
    const k = a.kind || 'otro';
    kindCounts[k] = (kindCounts[k] || 0) + 1;
  });

  const topKinds = Object.entries(kindCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  const canvas1 = document.getElementById('chart-fleet-types');
  if (canvas1) {
    fleetChartInstance = new Chart(canvas1, {
      type: 'doughnut',
      data: {
        labels: topKinds.map(k => k[0].charAt(0).toUpperCase() + k[0].slice(1)),
        datasets: [{
          data: topKinds.map(k => k[1]),
          backgroundColor: [
            '#1e293b', // Azul pizarra oscuro
            '#2e5b82', // Azul acero frío
            '#475569', // Pizarra medio
            '#699cc4', // Azul acero suave
            '#2b7a59', // Verde esmeralda frío
            '#94a3b8'  // Gris frío slate
          ],
          borderColor: '#ffffff',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: '#334155', font: { size: 11, family: 'Plus Jakarta Sans' } }
          }
        },
        cutout: '65%'
      }
    });
  }

  // Gráfico 2: Ahorros
  const modelo = analytics?.modelo_anual || {
    ahorro_diesel: 120000,
    ahorro_logistica: 48000,
    ahorro_taller: 60000
  };

  const canvas2 = document.getElementById('chart-savings-breakdown');
  if (canvas2) {
    savingsChartInstance = new Chart(canvas2, {
      type: 'bar',
      data: {
        labels: ['Diésel Evitado', 'Logística & Despacho', 'Mantenimiento / Taller'],
        datasets: [{
          label: 'Ahorro Anual (USD)',
          data: [modelo.ahorro_diesel, modelo.ahorro_logistica, modelo.ahorro_taller],
          backgroundColor: ['#2e5b82', '#437aa7', '#2b7a59'],
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            grid: { color: 'rgba(212, 223, 232, 0.4)' },
            ticks: {
              color: '#64748b',
              font: { family: 'JetBrains Mono', size: 10 },
              callback: val => `$${val / 1000}k`
            }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#334155', font: { size: 11, family: 'Plus Jakarta Sans' } }
          }
        }
      }
    });
  }
}

window.renderDashboard = renderDashboard;
