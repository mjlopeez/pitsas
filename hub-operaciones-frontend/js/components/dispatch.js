// Componente de Despacho, Rutas y Restricciones VMT
// Estética Editorial Goodlife El Salvador (No AI Slop)

function renderDispatch(container) {
  const state = window.appStore.state;
  const corridors = state.corridors || [];

  container.innerHTML = `
    <div class="space-y-6">
      
      <!-- Banner Editorial de Despacho & VMT -->
      <div class="gl-card p-6 sm:p-8 bg-white border border-[#d4dfe8]">
        <span class="gl-subtitle text-[#2e5b82] block mb-1">REGULACIÓN VIAL & LOGÍSTICA • EL SALVADOR</span>
        <h2 class="font-sans text-2xl sm:text-3xl font-bold text-[#1e293b] tracking-tight">
          Control de Despacho & Ventanas de Veda VMT
        </h2>
        <div class="gl-separator justify-start my-2"></div>
        <p class="text-xs sm:text-sm text-[#475569] max-w-3xl leading-relaxed">
          El Viceministerio de Transporte (VMT) restringe la circulación de transporte pesado en los accesos al Área Metropolitana de San Salvador durante horas pico. El Hub programa salidas algorítmicamente para evitar retenciones y multas.
        </p>
      </div>

      <!-- Corredores Viales Registrados -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        ${corridors.map(cor => {
          const hasVedas = cor.vedas && cor.vedas.length > 0;

          return `
            <div class="gl-card p-5 sm:p-6 bg-white border border-[#d4dfe8] flex flex-col justify-between">
              <div>
                <div class="flex items-start justify-between gap-2 border-b border-[#d4dfe8] pb-3 mb-3">
                  <div>
                    <h4 class="font-bold text-[#1e293b] text-sm">${cor.nombre}</h4>
                    <span class="font-mono text-[11px] text-[#1e293b]">ID: ${cor.corredor_id}</span>
                  </div>
                  <span class="gl-badge ${hasVedas ? 'gl-badge-gold' : 'gl-badge-success'} text-[10px]">
                    ${hasVedas ? 'Horarios Restringidos' : 'Libre Circulación'}
                  </span>
                </div>

                <div class="space-y-2 text-xs mb-4">
                  <div class="flex justify-between text-[#475569]">
                    <span class="text-[#64748b]">Penalidad de Tiempo:</span>
                    <span class="font-mono text-[#1e293b] font-bold">+${cor.penalidad_min} minutos</span>
                  </div>
                  <div class="flex justify-between text-[#475569]">
                    <span class="text-[#64748b]">Aplicación:</span>
                    <strong class="text-[#1e293b]">Lunes a Viernes</strong>
                  </div>
                </div>

                <!-- Lista de Franjas de Veda -->
                <div class="space-y-1.5">
                  <span class="text-[9px] uppercase font-bold text-[#64748b] tracking-wider">Horarios de Veda Vigentes:</span>
                  ${hasVedas ? cor.vedas.map(v => `
                    <div class="p-2.5 rounded border border-[#bcd0e2] bg-[#eef4f9] flex items-center justify-between text-xs font-mono">
                      <span class="text-[#1b3a57] font-bold">${v.desde} – ${v.hasta}</span>
                      <span class="text-[#475569] capitalize text-[11px] font-sans">${v.etiqueta}</span>
                    </div>
                  `).join('') : `
                    <div class="p-2.5 rounded border border-[#bbf7d0] bg-[#f0fdf4] text-[#2b7a59] text-xs font-semibold">
                      Sin restricción de horario. Permite tránsito continuo.
                    </div>
                  `}
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>

      <!-- Simulador de Despacho Inteligente -->
      <div class="gl-card p-6 sm:p-8 bg-white border border-[#d4dfe8]">
        <div class="flex items-center gap-2 mb-2">
          <i data-lucide="compass" class="w-5 h-5 text-[#2e5b82]"></i>
          <h3 class="font-sans text-xl font-bold text-[#1e293b]">Validador de Salida de Carga (Algoritmo VMT)</h3>
        </div>
        <p class="text-xs text-[#475569] mb-4 max-w-2xl leading-relaxed">
          Evalúa en milisegundos si una carga puede salir inmediatamente, si debe tomar el desvío por Quezaltepeque, o si la planta debe esperar a que culmine la veda.
        </p>

        <form id="form-check-dispatch" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs mb-4">
          <div>
            <label class="block font-bold text-[#1e293b] mb-1">Tipo Material:</label>
            <select id="val-tipo" class="w-full px-3 py-2 bg-white border border-[#cbd5e1] rounded text-[#1e293b]">
              <option value="CONCRETO">CONCRETO</option>
              <option value="ASFALTO">ASFALTO</option>
              <option value="AGREGADO">AGREGADO</option>
            </select>
          </div>

          <div>
            <label class="block font-bold text-[#1e293b] mb-1">Planta Origen:</label>
            <select id="val-origen" class="w-full px-3 py-2 bg-white border border-[#cbd5e1] rounded text-[#1e293b]">
              <option value="PCSS">PCSS - Planta Concreto San Salvador</option>
              <option value="PASD">PASD - Planta Asfalto San Diego</option>
              <option value="PCLL">PCLL - Planta La Libertad Costa</option>
            </select>
          </div>

          <div>
            <label class="block font-bold text-[#1e293b] mb-1">Obra Destino:</label>
            <select id="val-destino" class="w-full px-3 py-2 bg-white border border-[#cbd5e1] rounded text-[#1e293b]">
              <option value="CHOR">CHOR - Tramo Los Chorros</option>
              <option value="PDUT">PDUT - Paso Desnivel Utila</option>
              <option value="BSON">BSON - Bypass Sonsonate</option>
              <option value="QZTP">QZTP - Quezaltepeque</option>
            </select>
          </div>

          <div>
            <label class="block font-bold text-[#1e293b] mb-1">Corredor Propuesto:</label>
            <select id="val-corredor" class="w-full px-3 py-2 bg-white border border-[#cbd5e1] rounded text-[#1e293b]">
              <option value="panamericana_poniente">Panamericana Poniente</option>
              <option value="bulevar_monsenor_romero">Bulevar Monseñor Romero</option>
              <option value="bypass_quezaltepeque">Desvío Quezaltepeque (+40 min)</option>
              <option value="autopista_comalapa">Autopista a Comalapa</option>
            </select>
          </div>

          <div class="sm:col-span-2 lg:col-span-4 flex justify-end pt-2">
            <button type="submit" class="gl-btn-black">
              <i data-lucide="check-circle" class="w-4 h-4 text-[#2e5b82]"></i>
              <span>Evaluar Ruta y Veda VMT</span>
            </button>
          </div>
        </form>

        <!-- Resultado de la Evaluación -->
        <div id="dispatch-eval-result" class="hidden p-4 rounded border text-xs"></div>
      </div>

    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: container });

  const formCheck = container.querySelector('#form-check-dispatch');
  const resultBox = container.querySelector('#dispatch-eval-result');

  if (formCheck && resultBox) {
    formCheck.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        tipo: document.getElementById('val-tipo').value,
        planta_origen: document.getElementById('val-origen').value,
        obra_destino: document.getElementById('val-destino').value,
        corredor: document.getElementById('val-corredor').value,
        dosificado_en: new Date().toISOString()
      };

      if (navigator.vibrate) navigator.vibrate(20);
      const submitBtn = formCheck.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin text-[#2e5b82]"></i><span>Evaluando Veda VMT...</span>`;
        if (window.lucide) window.lucide.createIcons({ root: submitBtn });
      }

      try {
        resultBox.classList.remove('hidden');
        resultBox.innerHTML = `<span class="text-xs text-[#475569]">Consultando algoritmos de despacho del Hub...</span>`;

        const res = await window.apiClient.checkDispatchCarga(payload);
        if (window.showToast) {
          window.showToast(`POST /api/dispatch/carga: 200 OK — Algoritmo VMT evaluado`, 'success');
        }

        const decision = res.decision || (res.autorizado ? 'AUTORIZADO' : 'RERUTAR');
        const isOk = decision === 'AUTORIZADO' || res.autorizado;

        resultBox.className = `p-4 rounded border text-xs ${
          isOk ? 'bg-[#f0fdf4] border-emerald-300 text-emerald-900' : 'bg-[#fffdf5] border-amber-300 text-amber-900'
        }`;

        resultBox.innerHTML = `
          <div class="flex items-center gap-2 font-bold text-sm mb-1">
            <i data-lucide="${isOk ? 'check-check' : 'alert-triangle'}" class="w-5 h-5 ${isOk ? 'text-emerald-700' : 'text-amber-700'}"></i>
            Dictamen de Despacho: ${decision}
          </div>
          <div class="space-y-1 mt-2 text-[#444444]">
            <div><strong class="text-[#1e293b]">Recomendación:</strong> ${res.mensaje || res.explicacion || 'Salida autorizada sin conflicto con vedas del VMT.'}</div>
            ${res.corredor_recomendado ? `<div><strong class="text-[#1e293b]">Corredor Óptimo:</strong> <span class="font-mono text-[#1e293b] font-bold">${res.corredor_recomendado}</span></div>` : ''}
          </div>
        `;
        if (window.lucide) window.lucide.createIcons({ root: resultBox });
      } catch (err) {
        resultBox.classList.remove('hidden');
        resultBox.className = 'p-4 rounded border bg-rose-50 border-rose-300 text-rose-800 text-xs';
        resultBox.innerHTML = `Error al consultar despacho: ${err.message}`;
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = `<i data-lucide="check-circle" class="w-4 h-4 text-[#2e5b82]"></i><span>Evaluar Ruta y Veda VMT</span>`;
          if (window.lucide) window.lucide.createIcons({ root: submitBtn });
        }
      }
    });
  }
}

window.renderDispatch = renderDispatch;
