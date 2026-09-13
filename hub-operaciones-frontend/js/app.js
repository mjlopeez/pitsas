// Aplicación Principal - Hub de Operaciones — Grupo ECON

// Sistema de Notificaciones Toast
window.showToast = function(message, type = 'info') {
  const toastContainer = document.getElementById('toast-container');
  if (!toastContainer) return;

  const toast = document.createElement('div');
  const borderCol = type === 'success' ? 'border-[#bbf7d0] bg-white text-[#15803d]' :
                    type === 'error' ? 'border-[#fca5a5] bg-white text-[#c62828]' :
                    type === 'warning' ? 'border-[#fde68a] bg-white text-[#8c6a05]' :
                    'border-[#e8e6e1] bg-white text-[#111111]';

  const iconName = type === 'success' ? 'check-circle' :
                   type === 'error' ? 'alert-octagon' :
                   type === 'warning' ? 'alert-triangle' : 'info';

  toast.className = `p-3.5 rounded border shadow-lg flex items-center gap-2.5 text-xs font-semibold transition-all transform translate-y-2 opacity-0 ${borderCol}`;
  toast.innerHTML = `
    <i data-lucide="${iconName}" class="w-4 h-4 shrink-0"></i>
    <span class="flex-1 text-[#222222]">${message}</span>
    <button class="text-[#888888] hover:text-[#111111] ml-2 text-sm">&times;</button>
  `;

  toastContainer.appendChild(toast);
  if (window.lucide) window.lucide.createIcons({ root: toast });

  setTimeout(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  }, 10);

  const closeBtn = toast.querySelector('button');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      toast.classList.add('opacity-0', 'translate-x-4');
      setTimeout(() => toast.remove(), 250);
    });
  }

  setTimeout(() => {
    if (toast.parentElement) {
      toast.classList.add('opacity-0', 'translate-x-4');
      setTimeout(() => toast.remove(), 250);
    }
  }, 4500);
};

// Navegación por pestañas
window.switchTab = function(tabName) {
  const tabs = ['dashboard', 'map', 'fleet', 'reconciliation', 'materials', 'dispatch', 'connectors'];
  if (!tabs.includes(tabName)) tabName = 'dashboard';

  window.appStore.setState({ activeTab: tabName });

  // Actualizar visibilidad de paneles de pestañas
  tabs.forEach(t => {
    const tabEl = document.getElementById(`tab-${t}`);
    if (tabEl) {
      if (t === tabName) {
        tabEl.classList.remove('hidden');
        renderActiveTab(t, tabEl);
      } else {
        tabEl.classList.add('hidden');
      }
    }
  });

  // Actualizar botón de módulo en el header
  const headerContainer = document.getElementById('header-root');
  if (headerContainer && window.renderHeader) {
    window.renderHeader(headerContainer);
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
};

function renderActiveTab(tabName, container) {
  switch (tabName) {
    case 'dashboard':
      if (window.renderDashboard) window.renderDashboard(container);
      break;
    case 'map':
      if (window.renderFleetMap) window.renderFleetMap(container);
      break;
    case 'fleet':
      if (window.renderFleetList) window.renderFleetList(container);
      break;
    case 'reconciliation':
      if (window.renderReconciliation) window.renderReconciliation(container);
      break;
    case 'materials':
      if (window.renderMaterials) window.renderMaterials(container);
      break;
    case 'dispatch':
      if (window.renderDispatch) window.renderDispatch(container);
      break;
    case 'connectors':
      if (window.renderConnectors) window.renderConnectors(container);
      break;
  }
}

// Navegación Multi-Plataforma (Hub ECON, Startrack Mock, Nexus Mock)
window.switchPlatform = function(platformName) {
  const platforms = ['hub', 'startrack', 'nexus'];
  if (!platforms.includes(platformName)) platformName = 'hub';

  window.appStore.setPlatform(platformName);

  const hubEl = document.getElementById('platform-hub');
  const startrackEl = document.getElementById('platform-startrack');
  const nexusEl = document.getElementById('platform-nexus');
  const barEl = document.getElementById('global-portal-bar');

  if (hubEl) hubEl.classList.toggle('hidden', platformName !== 'hub');
  if (startrackEl) startrackEl.classList.toggle('hidden', platformName !== 'startrack');
  if (nexusEl) nexusEl.classList.toggle('hidden', platformName !== 'nexus');

  if (barEl && window.renderGlobalPortalBar) {
    window.renderGlobalPortalBar(barEl);
  }

  if (platformName === 'startrack' && startrackEl && window.renderStartrackMock) {
    window.renderStartrackMock(startrackEl);
  } else if (platformName === 'nexus' && nexusEl && window.renderNexusMock) {
    window.renderNexusMock(nexusEl);
  } else if (platformName === 'hub') {
    const currentTab = window.appStore.state.activeTab || 'dashboard';
    const activeEl = document.getElementById(`tab-${currentTab}`);
    if (activeEl) renderActiveTab(currentTab, activeEl);
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
};

window.resetDemoScenario = function() {
  window.appStore.resetDemoScenario();
  const barEl = document.getElementById('global-portal-bar');
  if (barEl && window.renderGlobalPortalBar) window.renderGlobalPortalBar(barEl);

  const startrackEl = document.getElementById('platform-startrack');
  if (startrackEl && window.renderStartrackMock) window.renderStartrackMock(startrackEl);

  const nexusEl = document.getElementById('platform-nexus');
  if (nexusEl && window.renderNexusMock) window.renderNexusMock(nexusEl);

  if (window.showToast) {
    window.showToast('Escenario demo reiniciado. Criterios de Startrack y Nexus en estado inicial.', 'info');
  }
};

// Modal de Celebración de PEA Liberada (Estética Editorial Goodlife El Salvador)
window.showPeaLiberadaModal = function(pea) {
  const modalRoot = document.getElementById('modal-root');
  if (!modalRoot) return;

  modalRoot.innerHTML = `
    <div class="fixed inset-0 modal-overlay z-50 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
      <div class="gl-card max-w-lg w-full p-6 sm:p-8 bg-white border border-[#e8e6e1] shadow-2xl my-auto text-[#222222]">
        
        <!-- Header Editorial Goodlife -->
        <div class="text-center pb-3 mb-4 border-b border-[#e8e6e1]">
          <span class="gl-subtitle text-[#bf9410] block mb-1">HOMOLOGACIÓN DE SILOS CONCLUIDA</span>
          <h2 class="font-editorial-serif text-2xl sm:text-3xl font-normal text-[#111111]">¡Prueba de Evidencia Liberada!</h2>
          <div class="gl-separator">
            <svg width="65" height="12" viewBox="0 0 65 12" fill="none">
              <path stroke="#bf9410" stroke-width="1.2" stroke-miterlimit="3" d="M1 10 L9 2 L17 10 L24 2 L32 10 L39 2 L47 10 L54 2 L64 10"/>
            </svg>
          </div>
          <p class="text-xs text-[#555555] max-w-sm mx-auto leading-relaxed">
            Los <strong>4 criterios de Startrack</strong> (físicos) y los <strong>4 criterios de Nexus ERP</strong> (contractuales) coinciden al 100%. La liquidación horaria queda legal y técnicamente respaldada.
          </p>
        </div>

        <div class="space-y-4 text-xs text-[#333333] leading-relaxed mb-6">
          <div class="grid grid-cols-2 gap-3 p-4 rounded border border-[#e8e6e1] bg-[#faf9f6] text-xs">
            <div>
              <span class="text-[#777777] text-[10px] uppercase font-bold tracking-wider block">Unidad Auditada:</span>
              <span class="text-[#111111] font-bold text-sm font-mono">${pea.maquinaria} (Cat 320D)</span>
            </div>
            <div>
              <span class="text-[#777777] text-[10px] uppercase font-bold tracking-wider block">Monto Respaldado:</span>
              <span class="text-[#15803d] font-bold text-sm font-mono">$${pea.monto_liberado.toFixed(2)} USD</span>
            </div>
            <div>
              <span class="text-[#777777] text-[10px] uppercase font-bold tracking-wider block">Horas Validadas:</span>
              <span class="text-[#111111] font-bold text-sm font-mono">${pea.horas_validadas} h (Motor ON)</span>
            </div>
            <div>
              <span class="text-[#777777] text-[10px] uppercase font-bold tracking-wider block">Código PEA:</span>
              <span class="text-[#bf9410] font-bold text-sm font-mono">${pea.pea_id} (ID: ${pea.id || 7})</span>
            </div>
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <span class="text-[10px] uppercase font-bold text-[#777777] tracking-wider block">Firma Criptográfica SHA-256 (Inmutable):</span>
              <span class="gl-badge gl-badge-success text-[9px]">API Backend 200 OK</span>
            </div>
            <div class="p-3 rounded border border-[#bbf7d0] bg-[#f0fdf4] text-[11px] font-mono text-[#15803d] break-all select-all font-semibold">
              ${pea.hash_sha256}
            </div>
          </div>
        </div>

        <!-- Botones Adaptados a Teléfono (Columna en móvil, Fila en desktop) -->
        <div class="flex flex-col-reverse sm:flex-row items-stretch sm:items-center justify-end gap-2.5 pt-3 border-t border-[#e8e6e1]">
          <button 
            onclick="document.getElementById('modal-root').innerHTML=''" 
            class="gl-btn-outline w-full sm:w-auto active:scale-95"
          >
            Cerrar
          </button>
          ${pea.id ? `
            <button 
              onclick="window.verifyPeaAction(${pea.id})" 
              class="gl-btn-outline w-full sm:w-auto text-emerald-800 border-emerald-300 hover:bg-emerald-50 active:scale-95"
            >
              <i data-lucide="shield-check" class="w-4 h-4 text-emerald-700"></i>
              <span>Verificar en Vivo</span>
            </button>
          ` : ''}
          <button 
            onclick="document.getElementById('modal-root').innerHTML=''; window.switchPlatform('hub'); window.switchTab('reconciliation');" 
            class="gl-btn-black w-full sm:w-auto active:scale-95"
          >
            <i data-lucide="scale" class="w-4 h-4 text-[#bf9410]"></i>
            <span>Ver en Hub ECON</span>
          </button>
        </div>

      </div>
    </div>
  `;
  if (window.lucide) window.lucide.createIcons({ root: modalRoot });
};

// Inicialización de la Aplicación
document.addEventListener('DOMContentLoaded', async () => {
  console.log('[ECON] Inicializando Frontend Hub de Operaciones & Mocks...');

  // Barra Superior Global de Plataformas
  const globalBarEl = document.getElementById('global-portal-bar');
  if (globalBarEl && window.renderGlobalPortalBar) {
    window.renderGlobalPortalBar(globalBarEl);
  }

  // Header del Hub
  const headerContainer = document.getElementById('header-root');
  if (headerContainer && window.renderHeader) {
    window.renderHeader(headerContainer);
  }

  // Suscribirse a cambios del Store
  window.appStore.subscribe((event, state, payload) => {
    // Si cambió la plataforma o los requisitos, actualizar la barra global
    if (globalBarEl && window.renderGlobalPortalBar) {
      window.renderGlobalPortalBar(globalBarEl);
    }

    // Modal de celebración al liberarse la PEA
    if (event === 'pea_liberada' && payload.pea) {
      window.showPeaLiberadaModal(payload.pea);
      if (window.showToast) {
        window.showToast('¡PEA LIBERADA CON ÉXITO! Sello SHA-256 generado.', 'success');
      }
    }

    // Si cambió el header
    if (headerContainer && window.renderHeader && (event === 'refresh_completed' || event === 'refresh_started')) {
      window.renderHeader(headerContainer);
    }

    // Actualizar la pestaña activa del Hub si cambió data relevante
    const currentTab = state.activeTab || 'dashboard';
    const activeEl = document.getElementById(`tab-${currentTab}`);

    if (activeEl && !activeEl.classList.contains('hidden')) {
      if (event === 'refresh_completed' || event === 'cargas_tick') {
        if (currentTab === 'materials' && event === 'cargas_tick') {
          window.renderMaterials(activeEl);
        } else if (event === 'refresh_completed') {
          renderActiveTab(currentTab, activeEl);
        }
      }
    }
  });

  // Inicializar en el Hub con dashboard
  window.switchPlatform('hub');
  window.switchTab('dashboard');

  // Carga inicial de datos desde la API backend
  await window.appStore.refreshAll();
  window.appStore.setAutoRefresh(15); // Auto-refresco cada 15 segundos
});
