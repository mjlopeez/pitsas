// Barra Global de Navegación entre las 3 Plataformas y Estado de la PEA
// Estética: Azul Frío Pizarra & Acero (Amigable, Humana, Sin AI Slop)

function renderGlobalPortalBar(container) {
  const state = window.appStore.state;
  const activePlatform = state.activePlatform || 'hub';

  const st = state.startrackRequirements || {};
  const nx = state.nexusRequirements || {};

  const stCount = Object.values(st).filter(Boolean).length;
  const nxCount = Object.values(nx).filter(Boolean).length;
  const isLiberada = state.peaLiberada;

  container.innerHTML = `
    <div class="px-3 sm:px-6 py-2.5 text-xs border-b border-[#d4dfe8] bg-white shadow-[0_1px_3px_rgba(15,23,42,0.04)]">
      <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        
        <!-- Izquierda: Selector de Plataformas con scroll táctil para teléfonos -->
        <div class="flex items-center gap-2 overflow-x-auto no-scrollbar py-0.5 -mx-1 px-1 shrink-0">
          <span class="gl-subtitle text-[10px] hidden lg:inline-block mr-1 text-[#2e5b82]">
            PLATAFORMAS:
          </span>

          <!-- Botón 1: Hub ECON -->
          <button 
            onclick="if (navigator.vibrate) navigator.vibrate(12); window.switchPlatform('hub');" 
            class="px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all min-h-[38px] cursor-pointer active:scale-95 ${
              activePlatform === 'hub' 
                ? 'bg-[#1e293b] text-white shadow-sm' 
                : 'bg-[#f1f5f9] hover:bg-[#e2e8f0] text-[#334155] border border-[#d4dfe8]'
            }"
          >
            <i data-lucide="layers" class="w-3.5 h-3.5 ${activePlatform === 'hub' ? 'text-[#9ec1dc]' : 'text-[#64748b]'}"></i>
            <span>1. Hub ECON</span>
          </button>

          <!-- Botón 2: Startrack Mock -->
          <button 
            onclick="if (navigator.vibrate) navigator.vibrate(12); window.switchPlatform('startrack');" 
            class="px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all min-h-[38px] cursor-pointer active:scale-95 ${
              activePlatform === 'startrack' 
                ? 'bg-[#36536e] text-white shadow-sm' 
                : 'bg-[#f1f5f9] hover:bg-[#e2e8f0] text-[#334155] border border-[#d4dfe8]'
            }"
          >
            <i data-lucide="satellite" class="w-3.5 h-3.5 ${activePlatform === 'startrack' ? 'text-white' : 'text-[#36536e]'}"></i>
            <span>2. Startrack</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded font-mono font-bold ${
              stCount === 4 ? 'bg-emerald-600 text-white' : 'bg-[#e2ebf4] text-[#1c344a] border border-[#9ec1dc]'
            }">
              ${stCount}/4
            </span>
          </button>

          <!-- Botón 3: Nexus Mock -->
          <button 
            onclick="if (navigator.vibrate) navigator.vibrate(12); window.switchPlatform('nexus');" 
            class="px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all min-h-[38px] cursor-pointer active:scale-95 ${
              activePlatform === 'nexus' 
                ? 'bg-[#364663] text-white shadow-sm' 
                : 'bg-[#f1f5f9] hover:bg-[#e2e8f0] text-[#334155] border border-[#d4dfe8]'
            }"
          >
            <i data-lucide="building" class="w-3.5 h-3.5 ${activePlatform === 'nexus' ? 'text-white' : 'text-[#364663]'}"></i>
            <span>3. Nexus ERP</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded font-mono font-bold ${
              nxCount === 4 ? 'bg-emerald-600 text-white' : 'bg-[#e2ebf4] text-[#1c344a] border border-[#9ec1dc]'
            }">
              ${nxCount}/4
            </span>
          </button>
        </div>

        <!-- Derecha: Estado de la PEA y Acciones Rápidas -->
        <div class="flex items-center justify-between md:justify-end gap-2.5 flex-wrap sm:flex-nowrap pt-1 md:pt-0 border-t md:border-t-0 border-[#d4dfe8]">
          
          <!-- Badge de Estado PEA -->
          <div class="flex items-center gap-1.5 px-3 py-1 rounded-lg text-[11px] font-semibold border ${
            isLiberada 
              ? 'bg-[#edf7f2] border-[#bfe5d3] text-[#2b7a59]' 
              : 'bg-[#f1f5f9] border-[#cbd5e1] text-[#475569]'
          }">
            <i data-lucide="${isLiberada ? 'shield-check' : 'clock'}" class="w-3.5 h-3.5 shrink-0"></i>
            <span class="truncate">${isLiberada ? 'PEA LIBERADA (SHA-256)' : 'PEA EN ESPERA (Faltan Requisitos)'}</span>
          </div>

          <div class="flex items-center gap-1.5 shrink-0">
            <!-- Botón Reiniciar Escenario -->
            <button 
              onclick="window.resetDemoScenario()" 
              title="Reiniciar requisitos de Startrack y Nexus" 
              class="px-2.5 py-1 text-[11px] bg-white hover:bg-[#f1f5f9] text-[#334155] border border-[#cbd5e1] rounded-lg transition-all flex items-center gap-1 min-h-[34px]"
            >
              <i data-lucide="rotate-ccw" class="w-3.5 h-3.5 text-[#2e5b82]"></i>
              <span class="hidden sm:inline font-medium">Reiniciar</span>
            </button>

            <!-- Botón Nota de Arquitectura -->
            <button 
              onclick="window.openArchitectureModal()" 
              title="Ver nota sobre la arquitectura de backend" 
              class="px-2.5 py-1 text-[11px] bg-white hover:bg-[#f1f5f9] text-[#2e5b82] border border-[#bcd0e2] rounded-lg transition-all flex items-center gap-1 min-h-[34px] font-semibold"
            >
              <i data-lucide="info" class="w-3.5 h-3.5"></i>
              <span class="hidden sm:inline">Arquitectura</span>
            </button>
          </div>

        </div>

      </div>
    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: container });
}

// Modal de Arquitectura Backend (Estética Azul Frío Limpia)
window.openArchitectureModal = function() {
  const modalRoot = document.getElementById('modal-root');
  if (!modalRoot) return;

  modalRoot.innerHTML = `
    <div class="fixed inset-0 modal-overlay z-50 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
      <div class="gl-card max-w-xl w-full p-6 sm:p-8 bg-white border border-[#d4dfe8] shadow-xl my-auto text-[#1e293b] rounded-xl">
        
        <!-- Header del Modal -->
        <div class="text-left pb-3 mb-4 border-b border-[#d4dfe8]">
          <span class="gl-subtitle block text-[#2e5b82]">ARQUITECTURA DE INTEGRACIÓN</span>
          <h2 class="gl-title text-2xl mt-1 text-[#1e293b]">Demostración de Enlace Visual</h2>
          <div class="gl-separator my-2"></div>
          <p class="text-xs text-[#64748b] max-w-md">
            Por qué visualizamos una conexión que en el entorno productivo opera de forma desatendida.
          </p>
        </div>

        <div class="space-y-4 text-xs sm:text-sm text-[#334155] leading-relaxed mb-6">
          <div class="p-4 rounded-lg bg-[#eef4f9] border border-[#bcd0e2] text-xs leading-relaxed text-[#1c344a]">
            <strong class="font-bold text-[#2e5b82] block mb-1">Aclaratoria de Diseño:</strong>
            Estamos mostrando una interfaz visual interactiva de este enlace entre las dos compañías. En el entorno productivo real, este intercambio de datos es un <strong>proceso 100% de backend desatendido</strong> (APIs, webhooks y colas de mensajes).
          </div>

          <div>
            <h4 class="font-bold text-[#1e293b] text-xs uppercase tracking-wider mb-1">Objetivo del Simulador:</h4>
            <p class="text-xs text-[#64748b]">
              Permitir a los operadores, auditores y directores de <strong>Grupo ECON</strong> comprender visualmente las 4 condiciones satelitales que Startrack debe emitir y las 4 condiciones administrativas que Nexus debe autorizar para que la <strong>Prueba de Evidencia Automatizada (PEA)</strong> se libere y liquide la jornada.
            </p>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
            <div class="p-3.5 rounded-lg border border-[#d4dfe8] bg-[#f8fafc]">
              <span class="font-bold text-[#36536e] block mb-1">Startrack (Satelital):</span>
              <ul class="list-disc list-inside space-y-1 text-[11px] text-[#64748b]">
                <li>Latido GPS reciente (&lt; 2h)</li>
                <li>8.0h motor medidas por sensor</li>
                <li>Geocerca de obra Los Chorros</li>
                <li>Integridad CAN bus sin fallas</li>
              </ul>
            </div>
            <div class="p-3.5 rounded-lg border border-[#d4dfe8] bg-[#f8fafc]">
              <span class="font-bold text-[#364663] block mb-1">Nexus ERP (Administrativo):</span>
              <ul class="list-disc list-inside space-y-1 text-[11px] text-[#64748b]">
                <li>Requisición de equipo aprobada</li>
                <li>Unidad EXC-01 asignada formalmente</li>
                <li>Partida WBS vinculada a $150/h</li>
                <li>Firma digital del Residente</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Botón de Cierre -->
        <div class="flex items-center justify-end pt-3 border-t border-[#d4dfe8]">
          <button 
            onclick="document.getElementById('modal-root').innerHTML=''" 
            class="gl-btn-black w-full sm:w-auto"
          >
            Entendido, Continuar
          </button>
        </div>

      </div>
    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: modalRoot });
};

window.renderGlobalPortalBar = renderGlobalPortalBar;
