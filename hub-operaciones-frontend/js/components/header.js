// Componente Header Dinámico con Estética Azul Frío Pizarra & Acero
// Amigable, ergonómico, sin AI slop, optimizado para móvil y escritorio

let isMenuDeployed = false;

const MODULES_LIST = [
  { key: 'dashboard', name: 'Dashboard & KPIs', icon: 'layout-dashboard', desc: 'Analítica general e indicadores ejecutivos' },
  { key: 'map', name: 'Mapa & Geocercas', icon: 'map', desc: '18 Frentes de obra en El Salvador' },
  { key: 'fleet', name: 'Flota ISO 15143-3', icon: 'truck', desc: '152 Maquinarias, telemetría y taller' },
  { key: 'reconciliation', name: 'Conciliación Silos', icon: 'scale', desc: 'Nexus vs Startrack & Emisión PEA' },
  { key: 'materials', name: 'Materiales & Concreto', icon: 'hourglass', desc: 'Vida útil en tránsito y veredicto de laboratorio' },
  { key: 'dispatch', name: 'Vedas VMT & Rutas', icon: 'navigation-2', desc: 'Restricciones de circulación vial AMSS' },
  { key: 'connectors', name: 'Conectores & Pruebas', icon: 'cpu', desc: '7 Canales de ingesta y simulación telemática' }
];

function renderHeader(container) {
  const state = window.appStore.state;
  const isOnline = window.apiClient.isOnline;
  const activeTabKey = state.activeTab || 'dashboard';
  const currentMeta = MODULES_LIST.find(m => m.key === activeTabKey) || MODULES_LIST[0];

  container.innerHTML = `
    <header id="main-header" class="relative border-b border-[#d4dfe8] bg-white sticky top-0 z-40 transition-all">
      
      <div class="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16 sm:h-18 gap-2">
          
          <!-- Logo & Brand Grupo ECON -->
          <div class="flex items-center gap-3 cursor-pointer group" onclick="window.toggleModuleMenu()" title="Ver módulos de operación">
            <div class="w-10 h-10 rounded-lg bg-[#eef4f9] border border-[#cbd5e1] flex items-center justify-center text-[#2e5b82] group-hover:border-[#2e5b82] transition-colors shrink-0">
              <i data-lucide="shield" class="w-5 h-5 text-[#2e5b82]"></i>
            </div>

            <div>
              <div class="flex items-center gap-2">
                <span class="font-sans text-xl sm:text-2xl font-bold tracking-tight text-[#1e293b]">
                  GRUPO ECON
                </span>
                <span class="hidden sm:inline-block px-1.5 py-0.2 text-[9px] font-bold font-sans tracking-widest uppercase rounded bg-[#f1f5f9] text-[#475569] border border-[#cbd5e1]">
                  El Salvador
                </span>
              </div>
              <span class="gl-subtitle text-[9px] sm:text-[10px] text-[#2e5b82] block -mt-0.5">
                HUB DE OPERACIONES & FLOTA
              </span>
            </div>
          </div>

          <!-- Métricas Resumen Centrales (Escritorio) -->
          <div class="hidden lg:flex items-center gap-3 text-xs">
            <div class="px-3 py-1.5 rounded-lg bg-[#f8fafc] border border-[#d4dfe8] flex items-center gap-2">
              <span class="text-[#64748b] text-[11px] uppercase tracking-wider font-semibold">Flota:</span>
              <span class="font-bold text-[#1e293b] font-mono">${state.assets.length || state.health.activos || 0} maq</span>
            </div>
            <div class="px-3 py-1.5 rounded-lg bg-[#f8fafc] border border-[#d4dfe8] flex items-center gap-2">
              <span class="text-[#64748b] text-[11px] uppercase tracking-wider font-semibold">Cargas Concreto:</span>
              <span class="font-bold text-[#1e293b] font-mono">${state.cargas.length || 0}</span>
            </div>
            <div class="px-3 py-1.5 rounded-lg bg-[#f8fafc] border border-[#d4dfe8] flex items-center gap-2">
              <span class="text-[#64748b] text-[11px] uppercase tracking-wider font-semibold">Alertas:</span>
              <span class="font-bold font-mono ${state.alerts.length > 0 ? 'text-[#a33d3d]' : 'text-[#2b7a59]'}">
                ${state.alerts.length || state.health.alertas_abiertas || 0}
              </span>
            </div>
          </div>

          <!-- Controles del Lado Derecho: Selector de Módulo, Estado API y Refresco -->
          <div class="flex items-center gap-2">
            
            <!-- Selector de Módulo -->
            <button 
              id="btn-toggle-menu" 
              onclick="window.toggleModuleMenu()" 
              title="Abrir menú de módulos" 
              class="px-3 sm:px-4 py-2 rounded-lg border transition-all flex items-center gap-2 cursor-pointer min-h-[42px] ${
                isMenuDeployed 
                  ? 'bg-[#1e293b] border-[#1e293b] text-white shadow-sm' 
                  : 'bg-white border-[#cbd5e1] hover:border-[#1e293b] text-[#1e293b]'
              }"
            >
              <i data-lucide="${currentMeta.icon}" class="w-4 h-4 ${isMenuDeployed ? 'text-[#9ec1dc]' : 'text-[#2e5b82]'}"></i>
              <div class="text-left">
                <span class="text-[9px] uppercase tracking-wider text-[#64748b] font-bold block sm:hidden">Módulo</span>
                <span class="font-bold text-xs max-w-[120px] sm:max-w-none truncate block ${isMenuDeployed ? 'text-white' : 'text-[#1e293b]'}">
                  ${currentMeta.name}
                </span>
              </div>
              <i data-lucide="chevron-down" id="menu-icon" class="w-3.5 h-3.5 transition-transform duration-200 ml-0.5 ${isMenuDeployed ? 'rotate-180 text-[#9ec1dc]' : 'text-[#64748b]'}"></i>
            </button>

            <!-- Indicador Visual de API Backend (Solo Lectura) -->
            <div 
              title="${isOnline ? 'API Backend en línea' : 'API Backend Desconectada'}" 
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold select-none min-h-[42px] ${
                isOnline 
                  ? 'bg-[#edf7f2] border-[#bfe5d3] text-[#2b7a59]' 
                  : 'bg-[#fdf2f2] border-[#f7caca] text-[#a33d3d]'
              }"
            >
              <span class="w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-500' : 'bg-rose-500'} shrink-0"></span>
              <span class="hidden md:inline font-mono text-[11px]">${isOnline ? 'API Conectada' : 'API Desconectada'}</span>
            </div>

            <!-- Botón de Sincronización Manual -->
            <button 
              onclick="window.refreshAllData()" 
              title="Sincronizar datos con la API" 
              class="w-10 h-10 rounded-lg bg-white hover:bg-[#f1f5f9] border border-[#cbd5e1] text-[#334155] hover:text-[#1e293b] flex items-center justify-center transition-colors shrink-0 min-h-[42px]"
            >
              <i data-lucide="refresh-cw" class="w-4 h-4 ${state.isLoading ? 'animate-spin text-[#2e5b82]' : ''}"></i>
            </button>

          </div>

        </div>
      </div>

      <!-- Menú Desplegable de Módulos (Drawer Limpio) -->
      <div id="module-drawer" class="gl-drawer ${isMenuDeployed ? 'open' : ''} border-t border-[#d4dfe8] bg-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4 py-6">
          
          <div class="flex items-center justify-between pb-3 mb-4 border-b border-[#d4dfe8]">
            <div>
              <span class="gl-subtitle block text-[#2e5b82]">CATÁLOGO DE OPERACIONES</span>
              <h3 class="font-sans text-xl font-bold text-[#1e293b]">Módulos del Hub de Operaciones</h3>
            </div>
            <button 
              onclick="window.toggleModuleMenu(false)" 
              class="p-2 rounded-lg text-[#64748b] hover:text-[#1e293b] hover:bg-[#f1f5f9] text-xs flex items-center gap-1 font-semibold"
            >
              <i data-lucide="x" class="w-4 h-4"></i>
              <span class="hidden sm:inline">Cerrar</span>
            </button>
          </div>

          <!-- Grid de Módulos con Tarjetas Táctiles -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            ${MODULES_LIST.map(m => {
              const isSelected = m.key === activeTabKey;
              return `
                <div 
                  onclick="window.selectModule('${m.key}')" 
                  class="p-3.5 rounded-lg border transition-all cursor-pointer flex items-start gap-3 select-none ${
                    isSelected 
                      ? 'bg-[#eef4f9] border-[#9ec1dc] text-[#1e293b] shadow-sm' 
                      : 'bg-[#f8fafc] border-[#d4dfe8] hover:border-[#9ec1dc] hover:bg-white text-[#334155]'
                  }"
                >
                  <div class="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                    isSelected ? 'bg-[#2e5b82] text-white font-bold' : 'bg-white border border-[#cbd5e1] text-[#2e5b82]'
                  }">
                    <i data-lucide="${m.icon}" class="w-4 h-4"></i>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between gap-1">
                      <span class="font-bold text-xs text-[#1e293b] truncate">${m.name}</span>
                      ${isSelected ? '<span class="text-[9px] font-bold text-[#2e5b82] uppercase font-mono">Activo</span>' : ''}
                    </div>
                    <p class="text-[11px] text-[#64748b] leading-tight mt-0.5 truncate">${m.desc}</p>
                  </div>
                </div>
              `;
            }).join('')}
          </div>

        </div>
      </div>

    </header>
  `;

  if (window.lucide) window.lucide.createIcons({ root: container });
}

// Controladores Interactivos del Menú
window.toggleModuleMenu = function(forceState) {
  if (navigator.vibrate) navigator.vibrate(12);
  isMenuDeployed = typeof forceState === 'boolean' ? forceState : !isMenuDeployed;
  const headerContainer = document.getElementById('header-root');
  if (headerContainer) renderHeader(headerContainer);
};

window.selectModule = function(moduleKey) {
  if (navigator.vibrate) navigator.vibrate(15);
  isMenuDeployed = false;
  window.switchTab(moduleKey);
  const headerContainer = document.getElementById('header-root');
  if (headerContainer) renderHeader(headerContainer);
};

window.refreshAllData = async function() {
  if (navigator.vibrate) navigator.vibrate(20);
  if (window.appStore) {
    await window.appStore.refreshAll();
    const state = window.appStore.state;
    if (window.showToast) {
      window.showToast(`GET /health: 200 OK — ${state.assets.length} maquinarias y ${state.cargas.length} cargas sincronizadas`, 'success');
    }
  }
};

window.renderHeader = renderHeader;
