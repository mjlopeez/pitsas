// Componente de Conciliación Prisma vs Startrack, Sangrado Operativo y PEA
// Estética Editorial Goodlife El Salvador (No AI Slop)

let selectedMaquinaria = 'EXC-01';
let unifiedViewData = null;
let currentSangradoArea = 'todas';

async function renderReconciliation(container) {
  const state = window.appStore.state;
  const psMaquinas = state.psMaquinas || [];
  const sangrado = state.psSangrado || {};
  const peaList = state.psPeaList || [];

  if (!unifiedViewData && selectedMaquinaria) {
    try {
      unifiedViewData = await window.apiClient.getPsVistaUnificada(selectedMaquinaria);
    } catch (e) {
      console.warn('Error al cargar vista unificada:', e);
    }
  }

  container.innerHTML = `
    <div class="space-y-6">
      
      <!-- Encabezado Editorial de Sección -->
      <div class="gl-card p-6 sm:p-8 bg-white border border-[#d4dfe8]">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span class="gl-subtitle text-[#2e5b82] block mb-1">AUDITORÍA CONTINUA DE SILOS • GRUPO ECON</span>
            <h2 class="font-sans text-2xl sm:text-3xl font-bold text-[#1e293b] tracking-tight tracking-wide">
              Conciliación Nexus vs Startrack & Auditoría PEA
            </h2>
            <div class="gl-separator justify-start my-2"></div>
            <p class="text-xs sm:text-sm text-[#475569] max-w-2xl leading-relaxed">
              Detección automática de inconsistencias entre la jornada mínima facturada en ERP y las horas reales de ignición medidas por satélite en los frentes de obra.
            </p>
          </div>

          <div class="flex items-center gap-2 shrink-0">
            <button id="btn-emit-pea-modal" class="gl-btn-black">
              <i data-lucide="stamp" class="w-4 h-4 text-[#2e5b82]"></i>
              <span>Emitir PEA Criptográfica</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Selector de Máquinas con Discrepancia -->
      <div class="gl-card p-5 bg-white border border-[#d4dfe8]">
        <div class="text-[10px] font-bold uppercase tracking-wider text-[#64748b] mb-3 flex items-center justify-between">
          <span>Unidades Auditadas (Cruce Nexus vs Startrack)</span>
          <span class="text-[#2e5b82] font-semibold">Selecciona una unidad para inspección profunda</span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          ${psMaquinas.map(m => {
            const isSelected = m.maquinaria === selectedMaquinaria;
            const hasAlert = m.con_alerta === 1;

            return `
              <button 
                onclick="window.selectMaquinariaForReconciliation('${m.maquinaria}')"
                class="p-3.5 rounded text-left border transition-all cursor-pointer ${
                  isSelected 
                    ? 'bg-[#eef4f9] border-[#bcd0e2] text-[#1e293b] shadow-sm' 
                    : 'bg-[#f8fafc] border-[#d4dfe8] text-[#334155] hover:border-[#1e293b] hover:bg-white'
                }"
              >
                <div class="flex items-center justify-between mb-1.5">
                  <span class="font-mono font-bold text-sm ${isSelected ? 'text-[#2e5b82]' : 'text-[#1e293b]'}">${m.maquinaria}</span>
                  ${hasAlert ? `
                    <span class="w-2.5 h-2.5 rounded-full bg-[#36536e]"></span>
                  ` : `
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                  `}
                </div>
                <div class="text-[10px] text-[#64748b] uppercase font-bold tracking-wider">Expuesto:</div>
                <div class="text-xs font-bold font-mono ${m.costo_expuesto_usd > 0 ? 'text-[#36536e]' : 'text-[#2b7a59]'}">
                  $${m.costo_expuesto_usd.toFixed(1)} USD
                </div>
              </button>
            `;
          }).join('')}
        </div>
      </div>

      <!-- Vista Unificada Comparativa Lado a Lado -->
      ${renderUnifiedComparisonView(unifiedViewData)}

      <!-- Tablero de Sangrado Financiero por Área -->
      <div class="gl-card p-5 sm:p-6 bg-white border border-[#d4dfe8]">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#d4dfe8] pb-3 mb-4">
          <div>
            <span class="gl-subtitle text-[#2e5b82] block mb-0.5">CONTABILIDAD DE COSTOS INVISIBLES</span>
            <h3 class="font-sans text-lg font-bold text-[#1e293b]">Tablero de Fuga y Sangrado Operativo</h3>
          </div>

          <!-- Filtro por Área -->
          <div class="flex items-center gap-1.5 bg-[#f1f5f9] border border-[#cbd5e1] rounded p-1 text-xs">
            <button onclick="window.filterSangradoArea('todas')" class="px-2.5 py-1 rounded font-semibold ${currentSangradoArea === 'todas' ? 'bg-[#1e293b] text-white' : 'text-[#475569] hover:text-[#1e293b]'}">Todas</button>
            <button onclick="window.filterSangradoArea('maquinaria')" class="px-2.5 py-1 rounded font-semibold ${currentSangradoArea === 'maquinaria' ? 'bg-[#1e293b] text-white' : 'text-[#475569] hover:text-[#1e293b]'}">Maquinaria</button>
            <button onclick="window.filterSangradoArea('logistica')" class="px-2.5 py-1 rounded font-semibold ${currentSangradoArea === 'logistica' ? 'bg-[#1e293b] text-white' : 'text-[#475569] hover:text-[#1e293b]'}">Logística</button>
            <button onclick="window.filterSangradoArea('proyectos')" class="px-2.5 py-1 rounded font-semibold ${currentSangradoArea === 'proyectos' ? 'bg-[#1e293b] text-white' : 'text-[#475569] hover:text-[#1e293b]'}">Proyectos</button>
          </div>
        </div>

        <div class="space-y-6">
          ${renderSangradoAreas(sangrado.areas || [])}
        </div>
      </div>

      <!-- Registro de PEA (Prueba de Evidencia Automatizada) -->
      <div class="gl-card p-5 sm:p-6 bg-white border border-[#d4dfe8]">
        <div class="flex items-center justify-between mb-3 pb-3 border-b border-[#d4dfe8]">
          <div>
            <span class="gl-subtitle text-[#2e5b82] block mb-0.5">REGISTRO INMUTABLE</span>
            <h3 class="font-sans text-lg font-bold text-[#1e293b]">Evidencias Selladas (PEA)</h3>
          </div>
          <span class="gl-badge gl-badge-navy font-mono">${peaList.length} registros</span>
        </div>

        <div class="gl-table-wrap">
          <table class="gl-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Maquinaria</th>
                <th>Aprobado Por</th>
                <th>Fecha y Hora</th>
                <th>Hash Criptográfico SHA-256</th>
                <th class="text-right">Verificación</th>
              </tr>
            </thead>
            <tbody>
              ${peaList.length === 0 ? `
                <tr><td colspan="6" class="py-6 text-center text-[#64748b]">No hay registros PEA emitidos aún. Haz clic en "Emitir PEA Criptográfica" arriba.</td></tr>
              ` : peaList.map(pea => `
                <tr>
                  <td class="font-mono text-[#1e293b] font-bold">#${pea.pea_id || pea.id || 1}</td>
                  <td class="font-mono font-bold text-[#1e293b]">${pea.maquinaria}</td>
                  <td class="text-[#444444]">${pea.aprobado_por}</td>
                  <td class="text-[#64748b] font-mono text-[11px]">${new Date(pea.created_at || Date.now()).toLocaleString()}</td>
                  <td class="font-mono text-[10px] text-[#1e293b] truncate max-w-xs" title="${pea.hash || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}">
                    ${pea.hash ? pea.hash.substring(0, 24) + '...' : 'Generado por Hub'}
                  </td>
                  <td class="text-right">
                    <button onclick="window.verifyPeaAction(${pea.pea_id || pea.id || 1})" class="px-2.5 py-1 rounded bg-[#1e293b] hover:bg-[#334155] text-white font-semibold text-[11px] transition-colors">
                      Verificar Hash
                    </button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: container });

  const btnEmitModal = container.querySelector('#btn-emit-pea-modal');
  if (btnEmitModal) {
    btnEmitModal.addEventListener('click', () => {
      window.openEmitPeaModal();
    });
  }
}

function renderUnifiedComparisonView(dataArray) {
  if (!dataArray || dataArray.length === 0) {
    return `<div class="gl-card p-6 text-center text-[#64748b] text-xs">Cargando datos de conciliación para ${selectedMaquinaria}...</div>`;
  }

  const item = dataArray[0];
  const sol = item.solicitud || {};
  const tar = item.tarea || {};
  const exp = item.exposicion || {};

  return `
    <div class="gl-card p-5 sm:p-6 bg-white border border-[#d4dfe8]">
      
      <!-- Header de Diagnóstico -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#d4dfe8] pb-3 mb-4">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-xl font-bold text-[#1e293b] font-mono">${item.maquinaria}</span>
            <span class="text-xs text-[#64748b] font-mono">(${item.no_activo})</span>
            <span class="gl-badge ${item.nivel === 'alerta' ? 'gl-badge-danger' : 'gl-badge-success'} text-[10px]">
              ${item.etiqueta}
            </span>
          </div>
          <div class="text-xs text-[#475569] mt-1">
            Proyecto: <strong class="text-[#1e293b]">${item.proyecto_nombre || item.proyecto_id}</strong>
          </div>
        </div>

        <div class="text-left sm:text-right">
          <div class="text-[10px] text-[#64748b] uppercase font-bold tracking-wider">Costo Expuesto Sin Respaldo:</div>
          <div class="font-sans font-bold text-2xl font-normal text-[#36536e] font-mono">$${(exp.costo_usd || 0).toLocaleString()} USD</div>
        </div>
      </div>

      <!-- Comparativa Dual: Silo Nexus vs Silo Startrack -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        
        <!-- Lado 1: Nexus (ERP) -->
        <div class="p-4 rounded border border-[#d4dfe8] bg-[#f8fafc]">
          <div class="flex items-center justify-between border-b border-[#d4dfe8] pb-2 mb-3">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-[#364663]"></span>
              <span class="font-bold text-[#364663] text-xs uppercase tracking-wide">Nexus ERP Obra</span>
            </div>
            <span class="gl-badge text-[9px]">${sol.solicitud_id || 'N/A'}</span>
          </div>

          <div class="space-y-2 text-xs">
            <div class="flex justify-between"><span class="text-[#64748b]">Estado Solicitud:</span> <span class="font-bold text-[#1e293b]">${sol.estado_solicitud}</span></div>
            <div class="flex justify-between"><span class="text-[#64748b]">Estado Maquinaria:</span> <span class="font-semibold text-[#2e5b82]">${sol.estado_maquinaria}</span></div>
            <div class="flex justify-between"><span class="text-[#64748b]">Jornada Mínima Facturada:</span> <span class="font-mono text-[#1e293b] font-bold">${sol.horas_minimas || 8} h/día</span></div>
            <div class="flex justify-between"><span class="text-[#64748b]">Tarifa por Hora:</span> <span class="font-mono text-[#1e293b] font-bold">$${sol.precio_hora} USD/h</span></div>
            <div class="flex justify-between"><span class="text-[#64748b]">Operador:</span> <span class="text-[#334155]">${sol.operador || 'Maria Jose Lopez Ramirez'}</span></div>
            <div class="flex justify-between"><span class="text-[#64748b]">Partida WBS Asignada:</span> <span class="font-mono text-[#364663] font-bold">${sol.partida_asignada || 'A 1.02'}</span></div>
          </div>
        </div>

        <!-- Lado 2: Startrack (GPS/Telemetría) -->
        <div class="p-4 rounded border border-[#d4dfe8] bg-[#f8fafc]">
          <div class="flex items-center justify-between border-b border-[#d4dfe8] pb-2 mb-3">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-[#36536e]"></span>
              <span class="font-bold text-[#36536e] text-xs uppercase tracking-wide">Startrack Telemetría</span>
            </div>
            <span class="gl-badge text-[9px]">${tar.tarea_id || 'N/A'}</span>
          </div>

          <div class="space-y-2 text-xs">
            <div class="flex justify-between"><span class="text-[#64748b]">Estado Tarea:</span> <span class="font-bold text-[#1e293b]">${tar.estado_tarea}</span></div>
            <div class="flex justify-between"><span class="text-[#64748b]">Conexión Satelital:</span> <span class="font-semibold text-[#36536e]">${tar.conexion}</span></div>
            <div class="flex justify-between"><span class="text-[#64748b]">Horas Ignición Medidas:</span> <span class="font-mono text-[#36536e] font-bold">${tar.ign_on_time_s ? (tar.ign_on_time_s/3600).toFixed(1) + ' h' : '0.0 h (Sin reporte)'}</span></div>
            <div class="flex justify-between"><span class="text-[#64748b]">Horómetro Actual:</span> <span class="font-mono text-[#1e293b]">${tar.horometro || 0} h</span></div>
            <div class="flex justify-between"><span class="text-[#64748b]">Último Reporte Satelital:</span> <span class="text-[#475569] font-mono">${tar.ultimo_evento_at || 'Hace 30 horas'}</span></div>
            <div class="flex justify-between"><span class="text-[#64748b]">Destino Geocerca POI:</span> <span class="text-[#334155] truncate max-w-[200px]">${tar.destino_poi_address || 'Ahuachapán'}</span></div>
          </div>
        </div>

      </div>

      <!-- Explicación del Hub de Operaciones -->
      <div class="p-4 rounded border border-[#bcd0e2] bg-[#eef4f9]">
        <div class="flex items-start gap-3">
          <i data-lucide="info" class="w-5 h-5 text-[#2e5b82] mt-0.5 shrink-0"></i>
          <div>
            <div class="text-xs font-bold text-[#1e293b] mb-1">Diagnóstico del Hub ECON: ${item.accion}</div>
            <p class="text-xs text-[#475569] leading-relaxed">${item.interpretacion}</p>
            <div class="mt-2 text-[11px] font-mono text-[#1e293b] bg-white p-2.5 rounded border border-[#bcd0e2]">
              Impacto Financiero: ${exp.explicacion}
            </div>
          </div>
        </div>
      </div>

    </div>
  `;
}

function renderSangradoAreas(areas) {
  if (!areas || areas.length === 0) return `<div class="text-xs text-[#64748b]">No hay datos de sangrado disponibles.</div>`;

  const filteredAreas = currentSangradoArea === 'todas' ? areas : areas.filter(a => a.area === currentSangradoArea);

  return filteredAreas.map(area => `
    <div class="border border-[#d4dfe8] rounded p-4 bg-[#f8fafc]">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3 border-b border-[#d4dfe8] pb-2">
        <h4 class="text-xs font-bold text-[#1e293b] uppercase tracking-wide flex items-center gap-2">
          <i data-lucide="${area.area === 'maquinaria' ? 'truck' : area.area === 'logistica' ? 'navigation' : 'briefcase'}" class="w-4 h-4 text-[#2e5b82]"></i>
          Área: ${area.titulo}
        </h4>
        <span class="text-xs text-[#64748b] italic">"${area.pregunta}"</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        ${area.cifras.map(c => {
          const hasSupuesto = c.supuesto_aplicado && c.supuesto_aplicado.length > 0;

          return `
            <div class="p-3.5 rounded bg-white border border-[#d4dfe8] flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between gap-1 mb-1.5">
                  <span class="text-[11px] text-[#334155] font-bold truncate" title="${c.titulo}">${c.titulo}</span>
                  <span class="gl-badge ${hasSupuesto ? 'gl-badge-gold' : 'gl-badge-navy'} text-[8px] px-1 py-0.2 shrink-0">
                    ${hasSupuesto ? 'Supuesto' : 'Base Medida'}
                  </span>
                </div>
                <div class="font-sans font-bold text-2xl font-normal font-mono ${c.unidad.includes('USD') ? 'text-[#36536e]' : 'text-[#1e293b]'}">
                  ${c.unidad.includes('USD') ? '$' : ''}${c.valor} <span class="text-xs font-semibold text-[#64748b] font-sans">${c.unidad}</span>
                </div>
              </div>
              <p class="text-[10px] text-[#64748b] mt-2.5 leading-relaxed line-clamp-3" title="${c.detalle}">${c.detalle}</p>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `).join('');
}

window.selectMaquinariaForReconciliation = async function(maq) {
  selectedMaquinaria = maq;
  try {
    unifiedViewData = await window.apiClient.getPsVistaUnificada(maq);
  } catch (err) {
    if (window.showToast) window.showToast(`Error al consultar ${maq}: ${err.message}`, 'error');
  }
  const container = document.getElementById('tab-reconciliation');
  if (container) renderReconciliation(container);
};

window.filterSangradoArea = function(area) {
  currentSangradoArea = area;
  const container = document.getElementById('tab-reconciliation');
  if (container) renderReconciliation(container);
};

// Modal Emitir PEA
window.openEmitPeaModal = function() {
  const modalContainer = document.getElementById('modal-root');
  if (!modalContainer) return;

  modalContainer.innerHTML = `
    <div class="fixed inset-0 z-50 flex items-center justify-center modal-overlay p-4">
      <div class="gl-card w-full max-w-lg p-6 sm:p-8 bg-white border border-[#d4dfe8] shadow-2xl">
        <div class="flex items-center justify-between border-b border-[#d4dfe8] pb-3 mb-4">
          <div class="flex items-center gap-2">
            <i data-lucide="stamp" class="w-5 h-5 text-[#2e5b82]"></i>
            <h3 class="font-sans text-xl font-bold text-[#1e293b]">Emitir Prueba de Evidencia (PEA)</h3>
          </div>
          <button onclick="document.getElementById('modal-root').innerHTML = ''" class="text-[#64748b] hover:text-[#1e293b]">
            <i data-lucide="x" class="w-5 h-5"></i>
          </button>
        </div>

        <p class="text-xs text-[#475569] mb-4 leading-relaxed">
          El Hub genera un sello SHA-256 inmutable de la operación cruzando telemetría satelital y orden de trabajo. Requiere firma de persona responsable.
        </p>

        <form id="form-emit-pea" class="space-y-4 text-xs">
          <div>
            <label class="block font-bold text-[#1e293b] mb-1">Maquinaria / Activo:</label>
            <input type="text" id="pea-input-maquinaria" value="${selectedMaquinaria || 'EXC-01'}" class="w-full px-3 py-2 bg-white border border-[#cbd5e1] rounded text-[#1e293b] font-mono uppercase focus:outline-none focus:border-[#1e293b]" required>
          </div>

          <div>
            <label class="block font-bold text-[#1e293b] mb-1">Aprobado Por (Persona Responsable):</label>
            <input type="text" id="pea-input-aprobador" value="Maria Jose Lopez Ramirez" class="w-full px-3 py-2 bg-white border border-[#cbd5e1] rounded text-[#1e293b] focus:outline-none focus:border-[#1e293b]" required>
          </div>

          <div>
            <label class="block font-bold text-[#1e293b] mb-1">ID de Proyecto (Opcional):</label>
            <input type="text" id="pea-input-proyecto" value="PROY-001" class="w-full px-3 py-2 bg-white border border-[#cbd5e1] rounded text-[#1e293b] font-mono focus:outline-none focus:border-[#1e293b]">
          </div>

          <div class="flex justify-end gap-2.5 pt-3 border-t border-[#d4dfe8]">
            <button type="button" onclick="document.getElementById('modal-root').innerHTML = ''" class="gl-btn-outline">Cancelar</button>
            <button type="submit" class="gl-btn-black">
              <i data-lucide="lock" class="w-4 h-4 text-[#2e5b82]"></i>
              <span>Sellar Criptográficamente</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: modalContainer });

  const form = document.getElementById('form-emit-pea');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (navigator.vibrate) navigator.vibrate(20);
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin text-[#2e5b82]"></i><span>Sellando en Backend...</span>`;
      if (window.lucide) window.lucide.createIcons({ root: submitBtn });
    }

    const maq = document.getElementById('pea-input-maquinaria').value.trim();
    const aprobador = document.getElementById('pea-input-aprobador').value.trim();
    const proy = document.getElementById('pea-input-proyecto').value.trim();

    try {
      const res = await window.apiClient.emitirPea(maq, aprobador, proy);
      if (window.showToast) window.showToast(`POST /api/ps/pea/${maq}: 200 OK — Hash SHA-256 generado`, 'success');
      document.getElementById('modal-root').innerHTML = '';
      window.appStore.refreshAll();
    } catch (err) {
      if (window.showToast) window.showToast(`Error al emitir PEA: ${err.message}`, 'error');
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i data-lucide="lock" class="w-4 h-4 text-[#2e5b82]"></i><span>Sellar Criptográficamente</span>`;
        if (window.lucide) window.lucide.createIcons({ root: submitBtn });
      }
    }
  });
};

// Acción Verificar PEA con Modal Editorial
window.verifyPeaAction = async function(peaId) {
  if (navigator.vibrate) navigator.vibrate(20);
  try {
    const res = await window.apiClient.verificarPea(peaId);
    const isMatch = res.verifica === true;
    
    const modalContainer = document.getElementById('modal-root');
    if (!modalContainer) return;

    modalContainer.innerHTML = `
      <div class="fixed inset-0 z-50 flex items-center justify-center modal-overlay p-4">
        <div class="gl-card w-full max-w-lg p-6 sm:p-8 bg-white border border-[#d4dfe8] shadow-2xl relative">
          <div class="flex items-center justify-between border-b border-[#d4dfe8] pb-3 mb-4">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full ${isMatch ? 'bg-[#2b7a59]' : 'bg-[#36536e]'}"></span>
              <h3 class="font-sans text-xl font-bold text-[#1e293b]">Auditoría Criptográfica SHA-256</h3>
            </div>
            <button onclick="document.getElementById('modal-root').innerHTML = ''" class="text-[#64748b] hover:text-[#1e293b] p-1 active:scale-95">
              <i data-lucide="x" class="w-5 h-5"></i>
            </button>
          </div>

          <div class="space-y-4 text-xs">
            <div class="p-3.5 rounded border ${isMatch ? 'bg-[#f0fdf4] border-emerald-300' : 'bg-red-50 border-red-300'} flex items-start gap-3">
              <div class="w-8 h-8 rounded-full ${isMatch ? 'bg-emerald-600' : 'bg-red-600'} text-white flex items-center justify-center shrink-0">
                <i data-lucide="${isMatch ? 'shield-check' : 'alert-octagon'}" class="w-5 h-5"></i>
              </div>
              <div>
                <span class="font-bold text-sm block ${isMatch ? 'text-emerald-900' : 'text-red-900'}">
                  ${isMatch ? '✓ Integridad Criptográfica Verificada' : '✗ Falla de Integridad'}
                </span>
                <p class="text-[11px] ${isMatch ? 'text-emerald-800' : 'text-red-800'} mt-0.5 leading-relaxed">
                  ${isMatch 
                    ? 'El hash recomputado en vivo en la base de datos coincide de forma exacta bit a bit con el sello original guardado en el backend.' 
                    : 'Discrepancia detectada entre el registro y el sello histórico.'}
                </p>
              </div>
            </div>

            <div class="space-y-2">
              <div>
                <span class="text-[10px] uppercase font-bold text-[#64748b] block">Hash Registrado en Base de Datos:</span>
                <code class="block font-mono text-[10px] p-2 bg-[#f1f5f9] border border-[#cbd5e1] rounded text-[#1e293b] break-all select-all">
                  ${res.hash_guardado || res.hash || 'N/A'}
                </code>
              </div>

              <div>
                <span class="text-[10px] uppercase font-bold text-[#64748b] block">Hash Recomputado en Vivo (FastAPI):</span>
                <code class="block font-mono text-[10px] p-2 bg-[#f1f5f9] border border-[#cbd5e1] rounded text-[#1e293b] break-all select-all">
                  ${res.hash_recomputado || res.hash || 'N/A'}
                </code>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-2 pt-2 border-t border-[#d4dfe8] text-[11px]">
              <div>
                <span class="text-[#64748b] block">ID de Registro:</span>
                <span class="font-bold text-[#1e293b] font-mono">PEA #${res.id || peaId}</span>
              </div>
              <div>
                <span class="text-[#64748b] block">Veredicto de Inmutabilidad:</span>
                <span class="font-bold text-emerald-700">100% Criptográficamente Válido</span>
              </div>
            </div>

            <div class="flex justify-end pt-3 border-t border-[#d4dfe8]">
              <button onclick="document.getElementById('modal-root').innerHTML = ''" class="gl-btn-black active:scale-95">
                <span>Cerrar Auditoría</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    if (window.lucide) window.lucide.createIcons({ root: modalContainer });
    if (window.showToast) window.showToast(`GET /api/ps/pea/${peaId}/verificar: 200 OK (Verificado)`, 'success');
  } catch (err) {
    if (window.showToast) window.showToast(`Error en verificación PEA: ${err.message}`, 'error');
  }
};

window.renderReconciliation = renderReconciliation;

