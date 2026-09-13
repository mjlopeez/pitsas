// Componente de Control de Materiales, Dosificación y Laboratorio
// Estética Editorial Goodlife El Salvador (No AI Slop)

function renderMaterials(container) {
  const state = window.appStore.state;
  const cargas = state.cargas || [];

  container.innerHTML = `
    <div class="space-y-6">
      
      <!-- Banner Editorial de Operaciones de Materiales -->
      <div class="gl-card p-6 sm:p-8 bg-white border border-[#e8e6e1]">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span class="gl-subtitle text-[#bf9410] block mb-1">CONTROL DE CALIDAD & TIEMPOS • GRUPO ECON</span>
            <h2 class="font-editorial-serif text-2xl sm:text-3xl font-normal text-[#111111] tracking-wide">
              Logística de Concreto & Asfalto en Tránsito
            </h2>
            <div class="gl-separator justify-start my-2">
              <svg width="65" height="12" viewBox="0 0 65 12" fill="none">
                <path stroke="#bf9410" stroke-width="1.2" stroke-miterlimit="3" d="M1 10 L9 2 L17 10 L24 2 L32 10 L39 2 L47 10 L54 2 L64 10"/>
              </svg>
            </div>
            <p class="text-xs sm:text-sm text-[#555555] max-w-2xl leading-relaxed">
              Desde la dosificación en planta, cada m³ de concreto tiene una hora de muerte operativa ligada a las restricciones del VMT y cuadrillas en obra.
            </p>
          </div>

          <div class="flex flex-wrap items-center gap-2.5 shrink-0">
            <button id="btn-open-dosificar-modal" class="gl-btn-gold">
              <i data-lucide="plus-circle" class="w-4 h-4"></i>
              <span>Dosificar Nueva Carga</span>
            </button>
            <button id="btn-open-lab-modal" class="gl-btn-outline">
              <i data-lucide="flask-conical" class="w-4 h-4 text-[#bf9410]"></i>
              <span>Registrar Ensayo Lab</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Métricas Rápidas de Materiales -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="gl-card p-5 bg-white border border-[#e8e6e1]">
          <span class="text-[10px] text-[#777777] font-bold uppercase tracking-wider">Total Cargas Monitoreadas</span>
          <div class="font-editorial-serif text-3xl font-normal text-[#111111] font-mono mt-1">${cargas.length} lotes</div>
          <p class="text-[11px] text-[#666666] mt-1">Concreto premezclado y mezclas asfálticas</p>
        </div>

        <div class="gl-card p-5 bg-white border border-[#e8e6e1]">
          <span class="text-[10px] text-[#15803d] font-bold uppercase tracking-wider">En Tránsito con Tiempo Válido</span>
          <div class="font-editorial-serif text-3xl font-normal text-[#15803d] font-mono mt-1">
            ${cargas.filter(c => (c.minutos_restantes || 0) > 0 && c.estado !== 'retenida').length} cargas
          </div>
          <p class="text-[11px] text-[#666666] mt-1">Dentro de ventana de manejabilidad</p>
        </div>

        <div class="gl-card p-5 bg-white border border-[#e8e6e1]">
          <span class="text-[10px] text-[#c62828] font-bold uppercase tracking-wider">Retenidas / Vencidas</span>
          <div class="font-editorial-serif text-3xl font-normal text-[#c62828] font-mono mt-1">
            ${cargas.filter(c => c.estado === 'retenida' || (c.minutos_restantes || 0) <= 0).length} cargas
          </div>
          <p class="text-[11px] text-[#666666] mt-1">Bloqueadas antes de vertido en obra</p>
        </div>
      </div>

      <!-- Tarjetas de Cargas Vivas -->
      <div class="space-y-4">
        <div class="flex items-center justify-between pb-2 border-b border-[#e8e6e1]">
          <h3 class="font-editorial-serif text-lg font-normal text-[#111111]">Cargas Activas en Ruta</h3>
          <span class="text-xs text-[#bf9410] font-mono font-bold">Reloj sincronizado en vivo</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          ${cargas.length === 0 ? `
            <div class="col-span-2 gl-card p-8 text-center text-[#777777] text-xs bg-white border border-[#e8e6e1]">
              No hay cargas en tránsito actualmente. Crea una con el botón "Dosificar Nueva Carga".
            </div>
          ` : cargas.map(c => {
            const minRest = typeof c.minutos_restantes === 'number' ? c.minutos_restantes : 0;
            const isVencida = minRest <= 0;
            const isWarning = minRest > 0 && minRest <= 20;
            const isRetenida = c.estado === 'retenida' || c.cumple_especificacion === false;

            return `
              <div class="gl-card p-5 sm:p-6 bg-white border transition-all ${
                isRetenida || isVencida ? 'border-[#fca5a5] bg-[#fff5f5]' : isWarning ? 'border-[#fde68a] bg-[#fffdf5]' : 'border-[#e8e6e1]'
              } flex flex-col justify-between">
                <div>
                  
                  <!-- Header Lote -->
                  <div class="flex items-start justify-between gap-2 border-b border-[#e8e6e1] pb-2.5 mb-3">
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="font-bold text-[#111111] text-sm font-mono">${c.lote}</span>
                        <span class="gl-badge text-[9px] uppercase">
                          ${c.tipo}
                        </span>
                      </div>
                      <div class="text-xs text-[#666666] mt-0.5">Camión: <strong class="text-[#0e2439] font-mono">${c.asset_identifier}</strong></div>
                    </div>

                    <!-- Estado Badge -->
                    <div>
                      ${isRetenida ? `
                        <span class="gl-badge gl-badge-danger font-bold text-[10px]">RETENIDA POR LAB</span>
                      ` : `
                        <span class="gl-badge gl-badge-success font-bold text-[10px]">EN TRÁNSITO</span>
                      `}
                    </div>
                  </div>

                  <!-- Temporizador Dinámico -->
                  <div class="p-3.5 rounded border border-[#e8e6e1] bg-[#faf9f6] mb-3 flex items-center justify-between">
                    <div>
                      <span class="text-[9px] uppercase tracking-wider text-[#777777] block font-bold">Tiempo de Vida Restante</span>
                      <div class="font-editorial-serif text-2xl font-normal font-mono ${isRetenida || isVencida ? 'text-[#c62828]' : isWarning ? 'text-amber-600' : 'text-[#15803d]'}">
                        ${isVencida ? 'VENCIDO / PÉRDIDA' : `${minRest.toFixed(1)} minutos`}
                      </div>
                    </div>
                    <div class="w-10 h-10 rounded flex items-center justify-center ${isRetenida || isVencida ? 'bg-rose-100 text-[#c62828]' : isWarning ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-[#15803d]'}">
                      <i data-lucide="${isRetenida ? 'shield-x' : isVencida ? 'alarm-clock-off' : 'clock'}" class="w-5 h-5"></i>
                    </div>
                  </div>

                  <!-- Detalles de Ruta y Mezcla -->
                  <div class="grid grid-cols-2 gap-2 text-xs mb-3 text-[#555555]">
                    <div><span class="text-[#777777]">Origen:</span> <strong class="text-[#111111]">${c.planta_origen}</strong></div>
                    <div><span class="text-[#777777]">Destino:</span> <strong class="text-[#111111]">${c.obra_destino}</strong></div>
                    <div><span class="text-[#777777]">Volumen:</span> <span class="font-mono text-[#0e2439] font-bold">${c.cantidad ? `${c.cantidad} ${c.unidad || ''}` : 'N/A'}</span></div>
                    <div><span class="text-[#777777]">Diseño:</span> <span class="font-mono text-[#111111]">${c.diseno || (c.temperatura_c ? `${c.temperatura_c}°C` : 'N/A')}</span></div>
                  </div>

                  <!-- Ensayo de Laboratorio -->
                  <div class="text-[11px] p-2.5 rounded border border-[#e8e6e1] bg-[#faf9f6]">
                    <span class="text-[#777777]">Dictamen Laboratorio:</span>
                    ${c.ensayo ? `
                      <span class="font-semibold ${c.cumple_especificacion ? 'text-[#15803d]' : 'text-[#c62828]'} ml-1">
                        ${c.ensayo} (${c.cumple_especificacion ? 'CUMPLE' : 'NO CUMPLE - RETENER'})
                      </span>
                    ` : `
                      <span class="text-[#777777] italic ml-1">Pendiente de ensayo</span>
                    `}
                  </div>

                </div>

                <!-- Botones Acciones -->
                <div class="pt-3 border-t border-[#e8e6e1] mt-3 flex items-center gap-2">
                  <button onclick="window.openQuickLabModal('${c.lote}', '${c.asset_identifier}')" class="gl-btn-black flex-1 text-center justify-center text-xs">
                    Dictaminar Lote
                  </button>
                </div>

              </div>
            `;
          }).join('')}
        </div>
      </div>

    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: container });

  const btnDosificar = container.querySelector('#btn-open-dosificar-modal');
  const btnLab = container.querySelector('#btn-open-lab-modal');

  if (btnDosificar) btnDosificar.addEventListener('click', () => window.openDosificarModal());
  if (btnLab) btnLab.addEventListener('click', () => window.openQuickLabModal());
}

// Modal Dosificar
window.openDosificarModal = function() {
  const modalContainer = document.getElementById('modal-root');
  if (!modalContainer) return;

  modalContainer.innerHTML = `
    <div class="fixed inset-0 z-50 flex items-center justify-center modal-overlay p-4">
      <div class="gl-card w-full max-w-lg p-6 sm:p-8 bg-white border border-[#e8e6e1] shadow-2xl max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b border-[#e8e6e1] pb-3 mb-4">
          <div class="flex items-center gap-2">
            <i data-lucide="plus-circle" class="w-5 h-5 text-[#bf9410]"></i>
            <h3 class="font-editorial-serif text-xl font-normal text-[#111111]">Dosificar Carga de Planta</h3>
          </div>
          <button onclick="document.getElementById('modal-root').innerHTML = ''" class="text-[#777777] hover:text-[#111111]">
            <i data-lucide="x" class="w-5 h-5"></i>
          </button>
        </div>

        <p class="text-xs text-[#555555] mb-4 leading-relaxed">
          La planta dosifica y arranca el reloj de vida útil de la carga. Sincroniza automáticamente la veda del VMT y cuadrilla en destino.
        </p>

        <form id="form-dosificar" class="space-y-3 text-xs">
          <div>
            <label class="block font-bold text-[#111111] mb-1">Tipo de Material:</label>
            <select id="dos-tipo" class="w-full px-3 py-2 bg-white border border-[#d6d3cb] rounded text-[#111111]">
              <option value="CONCRETO">CONCRETO (Reloj máx: 90 min)</option>
              <option value="ASFALTO">ASFALTO (Reloj máx: 120 min)</option>
              <option value="AGREGADO">AGREGADO</option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-bold text-[#111111] mb-1">Planta Origen:</label>
              <select id="dos-origen" class="w-full px-3 py-2 bg-white border border-[#d6d3cb] rounded text-[#111111]">
                <option value="PCSS">PCSS - Planta Concreto San Salvador</option>
                <option value="PCLL">PCLL - Planta Concreto La Libertad</option>
                <option value="PCSO">PCSO - Planta Concreto Sonsonate</option>
                <option value="PCSM">PCSM - Planta Concreto San Miguel</option>
                <option value="PASD">PASD - Planta Asfalto San Diego</option>
                <option value="PASS">PASS - Planta Asfalto San Salvador</option>
              </select>
            </div>
            <div>
              <label class="block font-bold text-[#111111] mb-1">Obra Destino:</label>
              <select id="dos-destino" class="w-full px-3 py-2 bg-white border border-[#d6d3cb] rounded text-[#111111]">
                <option value="PDUT">PDUT - Paso Desnivel Utila</option>
                <option value="PDCL">PDCL - Paso Desnivel Claudia Lars</option>
                <option value="PDEJ">PDEJ - Paso Desnivel El Jaguar</option>
                <option value="PDNU">PDNU - Paso Desnivel Naciones Unidas</option>
                <option value="BSON">BSON - Bypass Sonsonate</option>
                <option value="CHOR">CHOR - Tramo Los Chorros</option>
                <option value="APLL">APLL - Ampliación Pto La Libertad</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block font-bold text-[#111111] mb-1">Camión Hormigonera / Mixer:</label>
            <input type="text" id="dos-asset" value="MACK-GU813-01" class="w-full px-3 py-2 bg-white border border-[#d6d3cb] rounded text-[#111111] font-mono uppercase" required>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-bold text-[#111111] mb-1">Cantidad:</label>
              <input type="number" step="0.1" id="dos-cantidad" value="8.0" class="w-full px-3 py-2 bg-white border border-[#d6d3cb] rounded text-[#111111]" required>
            </div>
            <div>
              <label class="block font-bold text-[#111111] mb-1">Unidad:</label>
              <input type="text" id="dos-unidad" value="m3" class="w-full px-3 py-2 bg-white border border-[#d6d3cb] rounded text-[#111111]">
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-bold text-[#111111] mb-1">Diseño de Mezcla:</label>
              <input type="text" id="dos-diseno" value="fc280" class="w-full px-3 py-2 bg-white border border-[#d6d3cb] rounded text-[#111111] font-mono">
            </div>
            <div>
              <label class="block font-bold text-[#111111] mb-1">Temperatura inicial (°C):</label>
              <input type="number" id="dos-temp" value="28" class="w-full px-3 py-2 bg-white border border-[#d6d3cb] rounded text-[#111111]">
            </div>
          </div>

          <div class="flex justify-end gap-2.5 pt-4 border-t border-[#e8e6e1]">
            <button type="button" onclick="document.getElementById('modal-root').innerHTML = ''" class="gl-btn-outline">Cancelar</button>
            <button type="submit" class="gl-btn-black">
              <i data-lucide="play" class="w-4 h-4 text-[#bf9410]"></i>
              <span>Iniciar Despacho</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: modalContainer });

  const form = document.getElementById('form-dosificar');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      tipo: document.getElementById('dos-tipo').value,
      planta_origen: document.getElementById('dos-origen').value,
      obra_destino: document.getElementById('dos-destino').value,
      asset_identifier: document.getElementById('dos-asset').value.trim(),
      cantidad: parseFloat(document.getElementById('dos-cantidad').value) || 8.0,
      unidad: document.getElementById('dos-unidad').value.trim() || 'm3',
      diseno: document.getElementById('dos-diseno').value.trim() || 'fc280',
      temperatura_c: parseFloat(document.getElementById('dos-temp').value) || null
    };

    if (navigator.vibrate) navigator.vibrate(20);
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin text-[#bf9410]"></i><span>Dosificando en Planta...</span>`;
      if (window.lucide) window.lucide.createIcons({ root: submitBtn });
    }

    try {
      const res = await window.apiClient.dosificarCarga(payload);
      if (window.showToast) {
        window.showToast(`POST /ingest/planta: 200 OK — Lote dosificado con éxito. Reloj de fraguado iniciado.`, 'success');
      }
      document.getElementById('modal-root').innerHTML = '';
      window.appStore.refreshAll();
    } catch (err) {
      if (window.showToast) window.showToast(`Error al dosificar: ${err.message}`, 'error');
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i data-lucide="play" class="w-4 h-4 text-[#bf9410]"></i><span>Iniciar Despacho</span>`;
        if (window.lucide) window.lucide.createIcons({ root: submitBtn });
      }
    }
  });
};

// Modal Dictamen Laboratorio
window.openQuickLabModal = function(lote = '', assetId = '') {
  const modalContainer = document.getElementById('modal-root');
  if (!modalContainer) return;

  modalContainer.innerHTML = `
    <div class="fixed inset-0 z-50 flex items-center justify-center modal-overlay p-4">
      <div class="gl-card w-full max-w-md p-6 sm:p-8 bg-white border border-[#e8e6e1] shadow-2xl">
        <div class="flex items-center justify-between border-b border-[#e8e6e1] pb-3 mb-4">
          <div class="flex items-center gap-2">
            <i data-lucide="flask-conical" class="w-5 h-5 text-[#bf9410]"></i>
            <h3 class="font-editorial-serif text-xl font-normal text-[#111111]">Dictamen de Laboratorio</h3>
          </div>
          <button onclick="document.getElementById('modal-root').innerHTML = ''" class="text-[#777777] hover:text-[#111111]">
            <i data-lucide="x" class="w-5 h-5"></i>
          </button>
        </div>

        <p class="text-xs text-[#555555] mb-4 leading-relaxed">
          El laboratorio es el custodio de la especificación técnica. Si el lote no cumple, el Hub lo retiene automáticamente antes de vertido en obra.
        </p>

        <form id="form-dictamen-lab" class="space-y-4 text-xs">
          <div>
            <label class="block font-bold text-[#111111] mb-1">Código de Lote:</label>
            <input type="text" id="lab-lote" value="${lote}" placeholder="C-SMOKE-..." class="w-full px-3 py-2 bg-white border border-[#d6d3cb] rounded text-[#111111] font-mono" required>
          </div>

          <div>
            <label class="block font-bold text-[#111111] mb-1">Descripción del Ensayo:</label>
            <input type="text" id="lab-ensayo" value="compresión 7 días 280 kg/cm2" class="w-full px-3 py-2 bg-white border border-[#d6d3cb] rounded text-[#111111]" required>
          </div>

          <div class="p-3.5 rounded border border-[#e8e6e1] bg-[#faf9f6] flex items-center justify-between">
            <div>
              <span class="font-bold text-[#111111] block">¿Cumple Especificación?</span>
              <span class="text-[11px] text-[#666666]">Desmarcar para activar retención inmediata</span>
            </div>
            <input type="checkbox" id="lab-cumple" class="w-5 h-5 accent-[#bf9410]" checked>
          </div>

          <div class="flex justify-end gap-2.5 pt-3 border-t border-[#e8e6e1]">
            <button type="button" onclick="document.getElementById('modal-root').innerHTML = ''" class="gl-btn-outline">Cancelar</button>
            <button type="submit" class="gl-btn-black">
              <i data-lucide="check" class="w-4 h-4 text-[#bf9410]"></i>
              <span>Guardar Dictamen</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: modalContainer });

  const form = document.getElementById('form-dictamen-lab');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      lote: document.getElementById('lab-lote').value.trim(),
      ensayo: document.getElementById('lab-ensayo').value.trim(),
      cumple: document.getElementById('lab-cumple').checked,
      asset_identifier: assetId || null
    };

    if (navigator.vibrate) navigator.vibrate(20);
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin text-[#bf9410]"></i><span>Guardando Ensayo...</span>`;
      if (window.lucide) window.lucide.createIcons({ root: submitBtn });
    }

    try {
      const res = await window.apiClient.dictaminarLab(payload);
      const msg = payload.cumple 
        ? `POST /ingest/lab: 200 OK — Lote ${payload.lote} APROBADO por laboratorio.` 
        : `POST /ingest/lab: 200 OK — Lote ${payload.lote} RECHAZADO. Carga RETENIDA en sistema.`;
      if (window.showToast) window.showToast(msg, payload.cumple ? 'success' : 'warning');
      document.getElementById('modal-root').innerHTML = '';
      window.appStore.refreshAll();
    } catch (err) {
      if (window.showToast) window.showToast(`Error al registrar ensayo: ${err.message}`, 'error');
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i data-lucide="check" class="w-4 h-4 text-[#bf9410]"></i><span>Guardar Dictamen</span>`;
        if (window.lucide) window.lucide.createIcons({ root: submitBtn });
      }
    }
  });
};

window.renderMaterials = renderMaterials;
