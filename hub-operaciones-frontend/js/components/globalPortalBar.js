// Barra Global de Navegación entre las 3 Plataformas y Estado de la PEA
// Estilo Editorial Goodlife El Salvador (No AI Slop • Diseñado para Smartphones y Pantallas Grandes)

function renderGlobalPortalBar(container) {
  const state = window.appStore.state;
  const activePlatform = state.activePlatform || 'hub';

  const st = state.startrackRequirements || {};
  const nx = state.nexusRequirements || {};

  const stCount = Object.values(st).filter(Boolean).length;
  const nxCount = Object.values(nx).filter(Boolean).length;
  const isLiberada = state.peaLiberada;

  container.innerHTML = `
    <div class="px-3 sm:px-6 py-2.5 text-xs border-b border-[#e8e6e1] bg-white shadow-[0_1px_4px_rgba(0,0,0,0.03)]">
      <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        
        <!-- Izquierda: Selector de Plataformas con scroll táctil para teléfonos -->
        <div class="flex items-center gap-2 overflow-x-auto no-scrollbar py-0.5 -mx-1 px-1 shrink-0">
          <span class="gl-subtitle text-[10px] hidden lg:inline-block mr-1">
            PLATAFORMAS:
          </span>

          <!-- Botón 1: Hub ECON -->
          <button 
            onclick="if (navigator.vibrate) navigator.vibrate(12); window.switchPlatform('hub');" 
            class="px-3.5 py-1.5 rounded text-xs font-semibold flex items-center gap-2 transition-all min-h-[38px] cursor-pointer active:scale-95 ${
              activePlatform === 'hub' 
                ? 'bg-[#0e2439] text-white shadow-sm' 
                : 'bg-[#f4f3f0] hover:bg-[#eae8e3] text-[#333333]'
            }"
          >
            <i data-lucide="layers" class="w-3.5 h-3.5 ${activePlatform === 'hub' ? 'text-[#bf9410]' : 'text-[#777777]'}"></i>
            <span>1. Hub ECON</span>
          </button>

          <!-- Botón 2: Startrack Mock -->
          <button 
            onclick="if (navigator.vibrate) navigator.vibrate(12); window.switchPlatform('startrack');" 
            class="px-3.5 py-1.5 rounded text-xs font-semibold flex items-center gap-2 transition-all min-h-[38px] cursor-pointer active:scale-95 ${
              activePlatform === 'startrack' 
                ? 'bg-[#c62828] text-white shadow-sm' 
                : 'bg-[#f4f3f0] hover:bg-[#eae8e3] text-[#333333]'
            }"
          >
            <i data-lucide="satellite" class="w-3.5 h-3.5 ${activePlatform === 'startrack' ? 'text-white' : 'text-[#c62828]'}"></i>
            <span>2. Startrack</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded font-mono font-bold ${
              stCount === 4 ? 'bg-emerald-600 text-white' : 'bg-white text-[#c62828] border border-[#c62828]/30'
            }">
              ${stCount}/4
            </span>
          </button>

          <!-- Botón 3: Nexus Mock -->
          <button 
            onclick="if (navigator.vibrate) navigator.vibrate(12); window.switchPlatform('nexus');" 
            class="px-3.5 py-1.5 rounded text-xs font-semibold flex items-center gap-2 transition-all min-h-[38px] cursor-pointer active:scale-95 ${
              activePlatform === 'nexus' 
                ? 'bg-[#423d90] text-white shadow-sm' 
                : 'bg-[#f4f3f0] hover:bg-[#eae8e3] text-[#333333]'
            }"
          >
            <i data-lucide="building" class="w-3.5 h-3.5 ${activePlatform === 'nexus' ? 'text-white' : 'text-[#423d90]'}"></i>
            <span>3. Nexus ERP</span>
            <span class="text-[10px] px-1.5 py-0.2 rounded font-mono font-bold ${
              nxCount === 4 ? 'bg-emerald-600 text-white' : 'bg-white text-[#423d90] border border-[#423d90]/30'
            }">
              ${nxCount}/4
            </span>
          </button>
        </div>

        <!-- Derecha: Estado de la PEA y Acciones Rápidas -->
        <div class="flex items-center justify-between md:justify-end gap-2.5 flex-wrap sm:flex-nowrap pt-1 md:pt-0 border-t md:border-t-0 border-[#e8e6e1]">
          
          <!-- Badge Editorial de Estado PEA -->
          <div class="flex items-center gap-1.5 px-3 py-1 rounded text-[11px] font-semibold border ${
            isLiberada 
              ? 'bg-emerald-50 border-emerald-300 text-emerald-800' 
              : 'bg-amber-50 border-amber-300 text-amber-900'
          }">
            <i data-lucide="${isLiberada ? 'shield-check' : 'clock'}" class="w-3.5 h-3.5 shrink-0"></i>
            <span class="truncate">${isLiberada ? 'PEA LIBERADA (SHA-256)' : 'PEA EN ESPERA (Faltan Requisitos)'}</span>
          </div>

          <div class="flex items-center gap-1.5 shrink-0">
            <!-- Botón Reiniciar Escenario -->
            <button 
              onclick="window.resetDemoScenario()" 
              title="Reiniciar requisitos de Startrack y Nexus" 
              class="px-2.5 py-1 text-[11px] bg-white hover:bg-[#f4f3f0] text-[#333333] border border-[#d6d3cb] rounded transition-all flex items-center gap-1 min-h-[34px]"
            >
              <i data-lucide="rotate-ccw" class="w-3.5 h-3.5 text-[#bf9410]"></i>
              <span class="hidden sm:inline font-medium">Reiniciar</span>
            </button>

            <!-- Botón Nota de Arquitectura -->
            <button 
              onclick="window.openArchitectureModal()" 
              title="Ver nota sobre la arquitectura de backend" 
              class="px-2.5 py-1 text-[11px] bg-white hover:bg-[#f4f3f0] text-[#bf9410] border border-[#ecd99a] rounded transition-all flex items-center gap-1 min-h-[34px] font-semibold"
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

// Modal de Arquitectura Backend (Estilo Editorial Goodlife)
window.openArchitectureModal = function() {
  const modalRoot = document.getElementById('modal-root');
  if (!modalRoot) return;

  modalRoot.innerHTML = `
    <div class="fixed inset-0 modal-overlay z-50 flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
      <div class="gl-card max-w-xl w-full p-6 sm:p-8 bg-white border border-[#e8e6e1] shadow-2xl my-auto text-[#222222]">
        
        <!-- Header Editorial Goodlife -->
        <div class="text-center pb-3 mb-4 border-b border-[#e8e6e1]">
          <span class="gl-subtitle block">ARQUITECTURA DE INTEGRACIÓN</span>
          <h2 class="gl-title text-2xl sm:text-3xl mt-1 text-[#111111]">Demostración de Enlace Visual</h2>
          <div class="gl-separator">
            <svg width="65" height="12" viewBox="0 0 65 12" fill="none">
              <path stroke="#bf9410" stroke-width="1.2" stroke-miterlimit="3" d="M1 10 L9 2 L17 10 L24 2 L32 10 L39 2 L47 10 L54 2 L64 10"/>
            </svg>
          </div>
          <p class="text-xs text-[#666666] max-w-md mx-auto">
            Por qué visualizamos una conexión que en el entorno productivo opera de forma desatendida.
          </p>
        </div>

        <div class="space-y-4 text-xs sm:text-sm text-[#444444] leading-relaxed mb-6">
          <div class="p-4 rounded bg-[#fdfaf0] border border-[#ecd99a] text-xs leading-relaxed text-[#5c4404]">
            <strong class="font-bold text-[#8c6a05] block mb-1">Aclaratoria de Diseño:</strong>
            Estamos mostrando una interfaz visual interactiva de este enlace entre las dos compañías. En el entorno productivo real, este intercambio de datos es un <strong>proceso 100% de backend desatendido</strong> (APIs, webhooks y colas de mensajes).
          </div>

          <div>
            <h4 class="font-bold text-[#111111] text-xs uppercase tracking-wider mb-1">Objetivo del Simulador:</h4>
            <p class="text-xs text-[#555555]">
              Permitir a los operadores, auditores y directores de <strong>Grupo ECON</strong> comprender visualmente las 4 condiciones satelitales que Startrack debe emitir y las 4 condiciones administrativas que Nexus debe autorizar para que la <strong>Prueba de Evidencia Automatizada (PEA)</strong> se libere y liquide la jornada.
            </p>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
            <div class="p-3 rounded border border-[#e8e6e1] bg-[#faf9f6]">
              <span class="font-bold text-[#c62828] block mb-1">Startrack (Satelital):</span>
              <ul class="list-disc list-inside space-y-1 text-[11px] text-[#555555]">
                <li>Latido GPS reciente (&lt; 2h)</li>
                <li>8.0h motor medidas por sensor</li>
                <li>Geocerca de obra Los Chorros</li>
                <li>Integridad CAN bus sin fallas</li>
              </ul>
            </div>
            <div class="p-3 rounded border border-[#e8e6e1] bg-[#faf9f6]">
              <span class="font-bold text-[#423d90] block mb-1">Nexus ERP (Administrativo):</span>
              <ul class="list-disc list-inside space-y-1 text-[11px] text-[#555555]">
                <li>Requisición de equipo aprobada</li>
                <li>Unidad EXC-01 asignada formalmente</li>
                <li>Partida WBS vinculada a $150/h</li>
                <li>Firma digital del Residente</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Botón de Cierre Editorial -->
        <div class="flex items-center justify-end pt-3 border-t border-[#e8e6e1]">
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
