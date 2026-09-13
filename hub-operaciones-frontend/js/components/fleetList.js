// Componente Directorio de Flota & Ficha de Telemetría
// Estética Editorial Goodlife El Salvador (No AI Slop)

let currentViewMode = 'cards'; // 'cards' | 'table'
let currentPage = 1;
const ITEMS_PER_PAGE = 24;

function renderFleetList(container) {
  const state = window.appStore.state;
  const assets = state.assets || [];
  const projects = state.projects || [];

  // Filtrado de activos
  const search = (state.filterSearch || '').toLowerCase().trim();
  const selectedProj = state.selectedProjectFilter || 'TODOS';
  const selectedEngine = state.filterEngineState || 'TODOS';
  const selectedKind = state.filterKind || 'TODOS';

  const filteredAssets = assets.filter(a => {
    if (search) {
      const matchId = (a.asset_identifier || '').toLowerCase().includes(search);
      const matchMake = (a.make || '').toLowerCase().includes(search);
      const matchModel = (a.model || '').toLowerCase().includes(search);
      const matchKind = (a.kind || '').toLowerCase().includes(search);
      if (!matchId && !matchMake && !matchModel && !matchKind) return false;
    }

    if (selectedProj !== 'TODOS' && a.assigned_project !== selectedProj) return false;
    if (selectedEngine !== 'TODOS' && a.engine_state !== selectedEngine) return false;
    if (selectedKind !== 'TODOS' && a.kind !== selectedKind) return false;

    return true;
  });

  const totalPages = Math.ceil(filteredAssets.length / ITEMS_PER_PAGE) || 1;
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const currentAssets = filteredAssets.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  const allKinds = [...new Set(assets.map(a => a.kind).filter(Boolean))].sort();

  container.innerHTML = `
    <div class="space-y-4">
      
      <!-- Encabezado Editorial Goodlife -->
      <div class="gl-card p-6 sm:p-8 bg-white border border-[#e8e6e1]">
        <span class="gl-subtitle text-[#bf9410] block mb-1">TELEMETRÍA DE CAMPO ISO 15143-3 • GRUPO ECON</span>
        <h2 class="font-editorial-serif text-2xl sm:text-3xl font-normal text-[#111111] tracking-wide">
          Directorio de Maquinaria Pesada & Activos
        </h2>
        <div class="gl-separator justify-start my-2">
          <svg width="65" height="12" viewBox="0 0 65 12" fill="none">
            <path stroke="#bf9410" stroke-width="1.2" stroke-miterlimit="3" d="M1 10 L9 2 L17 10 L24 2 L32 10 L39 2 L47 10 L54 2 L64 10"/>
          </svg>
        </div>
        <p class="text-xs sm:text-sm text-[#555555] max-w-2xl leading-relaxed">
          152 unidades monitoreadas por bus CAN J1939 y enlace satelital en las 18 obras de El Salvador. Auditoría de horómetros, consumos y órdenes de taller.
        </p>
      </div>

      <!-- Barra de Filtros y Búsqueda Adaptada para Móvil -->
      <div class="gl-card p-4 bg-white border border-[#e8e6e1] flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
        
        <!-- Input de Búsqueda -->
        <div class="relative w-full lg:w-72">
          <i data-lucide="search" class="w-4 h-4 text-[#777777] absolute left-3 top-1/2 -translate-y-1/2"></i>
          <input 
            type="text" 
            id="fleet-search-input" 
            placeholder="Buscar CAT-320, Komatsu, Excavadora..." 
            value="${state.filterSearch || ''}"
            class="w-full pl-9 pr-3 py-2 text-xs bg-white border border-[#d6d3cb] rounded text-[#111111] placeholder-[#888888] focus:outline-none focus:border-[#111111]"
          >
        </div>

        <!-- Filtros Desplegables -->
        <div class="flex flex-wrap items-center gap-2 w-full lg:w-auto">
          
          <!-- Filtro Obra -->
          <select id="fleet-filter-project" class="px-3 py-2 text-xs bg-white border border-[#d6d3cb] rounded text-[#333333] focus:outline-none focus:border-[#111111] cursor-pointer">
            <option value="TODOS">Todas las Obras (${projects.length})</option>
            ${projects.map(p => `
              <option value="${p.project_id}" ${selectedProj === p.project_id ? 'selected' : ''}>
                ${p.project_id} - ${p.name.substring(0, 24)}
              </option>
            `).join('')}
          </select>

          <!-- Filtro Motor -->
          <select id="fleet-filter-engine" class="px-3 py-2 text-xs bg-white border border-[#d6d3cb] rounded text-[#333333] focus:outline-none focus:border-[#111111] cursor-pointer">
            <option value="TODOS" ${selectedEngine === 'TODOS' ? 'selected' : ''}>Motor (Todos)</option>
            <option value="ON" ${selectedEngine === 'ON' ? 'selected' : ''}>Encendido (ON)</option>
            <option value="IDLE" ${selectedEngine === 'IDLE' ? 'selected' : ''}>Ralentí (IDLE)</option>
            <option value="OFF" ${selectedEngine === 'OFF' ? 'selected' : ''}>Apagado (OFF)</option>
          </select>

          <!-- Filtro Tipo de Maquinaria -->
          <select id="fleet-filter-kind" class="px-3 py-2 text-xs bg-white border border-[#d6d3cb] rounded text-[#333333] focus:outline-none focus:border-[#111111] cursor-pointer">
            <option value="TODOS" ${selectedKind === 'TODOS' ? 'selected' : ''}>Categoría (Todas)</option>
            ${allKinds.map(k => `
              <option value="${k}" ${selectedKind === k ? 'selected' : ''}>${k.toUpperCase()}</option>
            `).join('')}
          </select>

          <!-- Alternar Vista Tarjetas / Tabla -->
          <div class="flex items-center bg-[#f4f3f0] border border-[#d6d3cb] rounded p-0.5 ml-auto">
            <button id="btn-view-cards" title="Vista Cuadrícula" class="p-1.5 rounded ${currentViewMode === 'cards' ? 'bg-[#111111] text-white' : 'text-[#777777] hover:text-[#111111]'}">
              <i data-lucide="layout-grid" class="w-4 h-4"></i>
            </button>
            <button id="btn-view-table" title="Vista Tabla" class="p-1.5 rounded ${currentViewMode === 'table' ? 'bg-[#111111] text-white' : 'text-[#777777] hover:text-[#111111]'}">
              <i data-lucide="list" class="w-4 h-4"></i>
            </button>
          </div>

        </div>

      </div>

      <!-- Resumen de Resultados -->
      <div class="flex items-center justify-between text-xs text-[#666666] px-1">
        <div>
          Mostrando <strong class="text-[#111111]">${filteredAssets.length}</strong> equipos filtrados de <strong class="text-[#111111]">${assets.length}</strong> totales
        </div>
        <div class="flex items-center gap-2">
          <span>Pág. ${currentPage} de ${totalPages}</span>
          <button id="btn-prev-page" class="px-2 py-1 bg-white border border-[#d6d3cb] rounded text-[#333333] disabled:opacity-40" ${currentPage <= 1 ? 'disabled' : ''}>Ant</button>
          <button id="btn-next-page" class="px-2 py-1 bg-white border border-[#d6d3cb] rounded text-[#333333] disabled:opacity-40" ${currentPage >= totalPages ? 'disabled' : ''}>Sig</button>
        </div>
      </div>

      <!-- Listado de Equipos -->
      ${currentViewMode === 'cards' ? renderAssetCards(currentAssets) : renderAssetTable(currentAssets)}

    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: container });

  // Event Listeners
  const searchInput = container.querySelector('#fleet-search-input');
  const projSelect = container.querySelector('#fleet-filter-project');
  const engineSelect = container.querySelector('#fleet-filter-engine');
  const kindSelect = container.querySelector('#fleet-filter-kind');
  const btnCards = container.querySelector('#btn-view-cards');
  const btnTable = container.querySelector('#btn-view-table');
  const btnPrev = container.querySelector('#btn-prev-page');
  const btnNext = container.querySelector('#btn-next-page');

  let debounceTimer;
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        window.appStore.setState({ filterSearch: e.target.value });
        currentPage = 1;
        renderFleetList(container);
      }, 250);
    });
  }

  if (projSelect) {
    projSelect.addEventListener('change', (e) => {
      window.appStore.setState({ selectedProjectFilter: e.target.value });
      currentPage = 1;
      renderFleetList(container);
    });
  }

  if (engineSelect) {
    engineSelect.addEventListener('change', (e) => {
      window.appStore.setState({ filterEngineState: e.target.value });
      currentPage = 1;
      renderFleetList(container);
    });
  }

  if (kindSelect) {
    kindSelect.addEventListener('change', (e) => {
      window.appStore.setState({ filterKind: e.target.value });
      currentPage = 1;
      renderFleetList(container);
    });
  }

  if (btnCards) {
    btnCards.addEventListener('click', () => {
      currentViewMode = 'cards';
      renderFleetList(container);
    });
  }

  if (btnTable) {
    btnTable.addEventListener('click', () => {
      currentViewMode = 'table';
      renderFleetList(container);
    });
  }

  if (btnPrev) {
    btnPrev.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        renderFleetList(container);
      }
    });
  }

  if (btnNext) {
    btnNext.addEventListener('click', () => {
      if (currentPage < totalPages) {
        currentPage++;
        renderFleetList(container);
      }
    });
  }
}

function renderAssetCards(assets) {
  if (assets.length === 0) {
    return `
      <div class="gl-card p-12 text-center bg-white border border-[#e8e6e1]">
        <i data-lucide="search-x" class="w-10 h-10 text-[#bf9410] mx-auto mb-3 opacity-60"></i>
        <h4 class="font-editorial-serif text-lg font-normal text-[#111111]">No se encontraron equipos</h4>
        <p class="text-xs text-[#777777] mt-1">Prueba ajustando los filtros de búsqueda u obra.</p>
      </div>
    `;
  }

  return `
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      ${assets.map(asset => {
        const pctServicio = Math.min(100, Math.max(0, Math.round(asset.pct_servicio || 0)));
        const serviceWarning = pctServicio >= 90;
        const serviceBarColor = serviceWarning ? 'bg-[#c62828]' : pctServicio > 70 ? 'bg-amber-500' : 'bg-[#0e2439]';

        return `
          <div class="gl-card p-4 sm:p-5 bg-white border border-[#e8e6e1] hover:border-[#111111] flex flex-col justify-between transition-all">
            <div>
              <!-- Header Tarjeta -->
              <div class="flex items-start justify-between gap-2 mb-2 pb-2 border-b border-[#e8e6e1]">
                <div>
                  <div class="flex items-center gap-1.5">
                    <span class="font-bold text-[#111111] font-mono text-sm tracking-tight">${asset.asset_identifier}</span>
                    <span class="gl-badge text-[9px] uppercase">
                      ${asset.telemetry}
                    </span>
                  </div>
                  <div class="text-xs text-[#555555] font-medium">${asset.make} ${asset.model}</div>
                </div>

                <span class="gl-badge ${asset.engine_state === 'ON' ? 'gl-badge-success' : asset.engine_state === 'IDLE' ? 'gl-badge-gold' : 'gl-badge-navy'} text-[9px]">
                  ${asset.engine_state}
                </span>
              </div>

              <!-- Tipo y Obra -->
              <div class="text-xs text-[#666666] mb-3 space-y-1">
                <div class="flex items-center justify-between">
                  <span>Categoría:</span>
                  <span class="font-semibold text-[#111111] capitalize">${asset.kind}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span>Obra Asignada:</span>
                  <span class="font-semibold text-[#0e2439] truncate max-w-[160px]">${asset.assigned_project || 'Sin Asignar'}</span>
                </div>
              </div>

              <!-- Métricas Rápidas -->
              <div class="grid grid-cols-2 gap-2 p-2.5 rounded bg-[#faf9f6] border border-[#e8e6e1] text-xs mb-3 font-mono">
                <div>
                  <span class="text-[9px] text-[#777777] uppercase tracking-wider block font-sans">Horómetro</span>
                  <span class="font-bold text-[#111111] text-sm">${asset.operating_hours?.toFixed(1) || 0} h</span>
                </div>
                <div>
                  <span class="text-[9px] text-[#777777] uppercase tracking-wider block font-sans">Combustible</span>
                  <span class="font-bold text-[#111111] text-sm">${asset.cumulative_fuel?.toFixed(1) || 0} gal</span>
                </div>
              </div>

              <!-- Barra de Mantenimiento Preventivo -->
              <div class="mb-4">
                <div class="flex items-center justify-between text-[11px] mb-1">
                  <span class="text-[#777777]">Ciclo Taller (250h)</span>
                  <span class="font-mono font-bold ${serviceWarning ? 'text-[#c62828]' : 'text-[#111111]'}">${pctServicio}%</span>
                </div>
                <div class="service-progress-bg">
                  <div class="service-progress-bar ${serviceBarColor}" style="width: ${pctServicio}%"></div>
                </div>
                ${serviceWarning ? `
                  <div class="text-[10px] text-[#c62828] font-semibold mt-1 flex items-center gap-1">
                    <i data-lucide="alert-circle" class="w-3 h-3"></i> Mantenimiento Requerido
                  </div>
                ` : ''}
              </div>

            </div>

            <!-- Botones de Acción -->
            <div class="pt-2 border-t border-[#e8e6e1] flex items-center gap-2">
              <button onclick="window.openAssetModal('${asset.asset_identifier}')" class="gl-btn-black flex-1 text-center justify-center text-xs">
                Ficha Técnica
              </button>
              ${serviceWarning ? `
                <button onclick="window.closeAssetServiceAction('${asset.asset_identifier}')" title="Cerrar servicio en taller" class="p-2 rounded bg-[#c62828] hover:bg-[#b71c1c] text-white text-xs min-h-[38px] flex items-center justify-center">
                  <i data-lucide="wrench" class="w-4 h-4"></i>
                </button>
              ` : ''}
            </div>

          </div>
        `;
      }).join('')}
    </div>
  `;
}

function renderAssetTable(assets) {
  if (assets.length === 0) {
    return `<div class="gl-card p-8 text-center text-[#777777] text-xs">No hay datos que coincidan.</div>`;
  }

  return `
    <div class="gl-table-wrap">
      <table class="gl-table">
        <thead>
          <tr>
            <th>Identificador</th>
            <th>Marca / Modelo</th>
            <th>Categoría</th>
            <th>Obra</th>
            <th>Motor</th>
            <th>Horas Totales</th>
            <th>Combustible</th>
            <th>Próx. Servicio (250h)</th>
            <th class="text-right">Acción</th>
          </tr>
        </thead>
        <tbody>
          ${assets.map(asset => {
            const pctServicio = Math.min(100, Math.max(0, Math.round(asset.pct_servicio || 0)));
            const serviceWarning = pctServicio >= 90;

            return `
              <tr>
                <td class="font-mono font-bold text-[#111111]">
                  ${asset.asset_identifier}
                </td>
                <td class="text-[#333333]">${asset.make} ${asset.model}</td>
                <td class="text-[#666666] capitalize">${asset.kind}</td>
                <td class="font-semibold text-[#0e2439]">${asset.assigned_project || 'Sin Asignar'}</td>
                <td>
                  <span class="gl-badge ${asset.engine_state === 'ON' ? 'gl-badge-success' : asset.engine_state === 'IDLE' ? 'gl-badge-gold' : 'gl-badge-navy'} text-[9px]">
                    ${asset.engine_state}
                  </span>
                </td>
                <td class="font-mono font-bold text-[#111111]">${asset.operating_hours?.toFixed(1) || 0} h</td>
                <td class="font-mono text-[#555555]">${asset.cumulative_fuel?.toFixed(1) || 0} gal</td>
                <td>
                  <div class="flex items-center gap-2">
                    <span class="font-mono text-xs ${serviceWarning ? 'text-[#c62828] font-bold' : 'text-[#555555]'}">${pctServicio}%</span>
                    <div class="service-progress-bg w-16">
                      <div class="service-progress-bar ${serviceWarning ? 'bg-[#c62828]' : 'bg-[#0e2439]'}" style="width: ${pctServicio}%"></div>
                    </div>
                  </div>
                </td>
                <td class="text-right">
                  <button onclick="window.openAssetModal('${asset.asset_identifier}')" class="px-2.5 py-1 rounded bg-[#111111] hover:bg-[#333333] text-white font-semibold text-[11px] transition-colors">
                    Ver Ficha
                  </button>
                </td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    </div>
  `;
}

// Modal Ficha Técnica de Activo
window.openAssetModal = async function(assetId) {
  const modalContainer = document.getElementById('modal-root');
  if (!modalContainer) return;

  let asset = window.appStore.state.assets.find(a => a.asset_identifier === assetId);
  if (!asset) return;

  modalContainer.innerHTML = `
    <div class="fixed inset-0 z-50 flex items-center justify-center modal-overlay p-4">
      <div class="gl-card w-full max-w-2xl p-6 sm:p-8 bg-white border border-[#e8e6e1] shadow-2xl max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b border-[#e8e6e1] pb-3 mb-4">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded bg-[#faf9f6] border border-[#d6d3cb] flex items-center justify-center text-[#111111] font-mono font-bold">
              ${asset.asset_identifier.split('-')[0]}
            </div>
            <div>
              <h3 class="font-editorial-serif text-xl font-normal text-[#111111]">${asset.asset_identifier}</h3>
              <p class="text-xs text-[#666666]">${asset.make} ${asset.model} • ${asset.kind}</p>
            </div>
          </div>
          <button onclick="document.getElementById('modal-root').innerHTML = ''" class="text-[#777777] hover:text-[#111111] p-1">
            <i data-lucide="x" class="w-6 h-6"></i>
          </button>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4 text-xs">
          <div class="p-4 rounded border border-[#e8e6e1] bg-[#faf9f6] space-y-2">
            <div class="text-[10px] font-bold text-[#bf9410] uppercase tracking-wider">Telemetría ISO 15143-3</div>
            <div class="flex justify-between"><span class="text-[#777777]">Estado Motor:</span> <span class="font-bold text-[#111111]">${asset.engine_state}</span></div>
            <div class="flex justify-between"><span class="text-[#777777]">Horómetro Total:</span> <span class="font-mono text-[#111111] font-bold">${asset.operating_hours?.toFixed(1) || 0} h</span></div>
            <div class="flex justify-between"><span class="text-[#777777]">Combustible:</span> <span class="font-mono text-[#111111] font-bold">${asset.cumulative_fuel?.toFixed(1) || 0} gal</span></div>
            <div class="flex justify-between"><span class="text-[#777777]">Enlace:</span> <span class="uppercase text-[#111111] font-semibold">${asset.telemetry}</span></div>
          </div>

          <div class="p-4 rounded border border-[#e8e6e1] bg-[#faf9f6] space-y-2">
            <div class="text-[10px] font-bold text-[#bf9410] uppercase tracking-wider">Gestión de Obra & Asignación</div>
            <div class="flex justify-between"><span class="text-[#777777]">Obra Asignada:</span> <span class="font-bold text-[#111111]">${asset.assigned_project || 'Sin Asignar'}</span></div>
            <div class="flex justify-between"><span class="text-[#777777]">Alquilado a:</span> <span class="text-[#333333]">${asset.alquilado_a || 'Flota Propia'}</span></div>
            <div class="flex justify-between"><span class="text-[#777777]">Coordenadas GPS:</span> <span class="font-mono text-[#555555]">${asset.lat?.toFixed(4)}, ${asset.lon?.toFixed(4)}</span></div>
            <div class="flex justify-between"><span class="text-[#777777]">Último Reporte:</span> <span class="font-mono text-[#777777]">${new Date(asset.updated_at).toLocaleTimeString()}</span></div>
          </div>
        </div>

        <div class="p-4 rounded border border-[#e8e6e1] bg-[#faf9f6] mb-6">
          <div class="flex justify-between text-xs mb-1">
            <span class="text-[#111111] font-bold">Estado de Servicio en Taller</span>
            <span class="font-mono font-bold text-[#0e2439]">${asset.horas_desde_servicio?.toFixed(1) || 0} h desde último servicio (Cada ${asset.service_every_h}h)</span>
          </div>
          <div class="service-progress-bg h-2 mb-2">
            <div class="service-progress-bar ${asset.pct_servicio > 90 ? 'bg-[#c62828]' : 'bg-[#0e2439]'}" style="width: ${Math.min(100, Math.max(0, asset.pct_servicio || 0))}%"></div>
          </div>
          <p class="text-[11px] text-[#666666]">
            Al cerrar el servicio en taller, se restablece el contador de horas hacia el horómetro actual y se reanuda la operación regular de la máquina.
          </p>
        </div>

        <div class="flex justify-end gap-3 pt-3 border-t border-[#e8e6e1]">
          <button onclick="document.getElementById('modal-root').innerHTML = ''" class="gl-btn-outline">
            Cerrar
          </button>
          <button onclick="window.closeAssetServiceAction('${asset.asset_identifier}')" class="gl-btn-black">
            <i data-lucide="wrench" class="w-4 h-4 text-[#bf9410]"></i>
            <span>Cerrar Servicio de Taller</span>
          </button>
        </div>
      </div>
    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: modalContainer });
};

// Acción Cerrar Servicio
window.closeAssetServiceAction = async function(assetId) {
  if (navigator.vibrate) navigator.vibrate(20);
  try {
    const res = await window.apiClient.closeAssetService(assetId);
    if (window.showToast) {
      window.showToast(`POST /api/assets/${assetId}/servicio: 200 OK — Servicio cerrado en taller. Horómetro actualizado.`, 'success');
    }
    const modalContainer = document.getElementById('modal-root');
    if (modalContainer) modalContainer.innerHTML = '';
    window.appStore.refreshAll();
  } catch (err) {
    if (window.showToast) window.showToast(`Error al cerrar servicio en ${assetId}: ${err.message}`, 'error');
  }
};

window.renderFleetList = renderFleetList;
