// Componente de Conectores, Contrato Canónico ISO 15143-3 y Simulación
// Estética Editorial Goodlife El Salvador (No AI Slop)

function renderConnectors(container) {
  const state = window.appStore.state;
  const connectors = state.connectors || [];

  container.innerHTML = `
    <div class="space-y-6">
      
      <!-- Encabezado Editorial de Conectores -->
      <div class="gl-card p-6 sm:p-8 bg-white border border-[#d4dfe8]">
        <span class="gl-subtitle text-[#2e5b82] block mb-1">ARQUITECTURA DE INGESTA CANÓNICA • ISO 15143-3</span>
        <h2 class="font-sans text-2xl sm:text-3xl font-bold text-[#1e293b] tracking-tight tracking-wide">
          Panel de Conectores & Normalización de Telemetría
        </h2>
        <div class="gl-separator justify-start my-2"></div>
        <p class="text-xs sm:text-sm text-[#475569] max-w-3xl leading-relaxed">
          El Hub normaliza múltiples formatos telemáticos propietarios hacia el contrato estándar ISO 15143-3 (AEMP 2.0). Si un payload no cumple las reglas, se rechaza visiblemente para garantizar la integridad de auditoría de Grupo ECON.
        </p>
      </div>

      <!-- Tabla de Salud de Conectores -->
      <div class="gl-card p-5 sm:p-6 bg-white border border-[#d4dfe8]">
        <div class="flex items-center justify-between pb-3 mb-3 border-b border-[#d4dfe8]">
          <div>
            <span class="gl-subtitle text-[#2e5b82] block mb-0.5">CANALES DE INGESTA</span>
            <h3 class="font-sans text-lg font-bold text-[#1e293b]">Protocolos Técnicos y Fabricantes Homologados</h3>
          </div>
          <span class="gl-badge gl-badge-navy font-mono">${connectors.length} conectores</span>
        </div>

        <div class="gl-table-wrap">
          <table class="gl-table">
            <thead>
              <tr>
                <th>Canal / Fabricante</th>
                <th>Protocolo Técnico</th>
                <th>Estado</th>
                <th>Aceptados</th>
                <th>Rechazados</th>
                <th>Último Evento</th>
              </tr>
            </thead>
            <tbody>
              ${connectors.length === 0 ? `
                <tr><td colspan="6" class="py-6 text-center text-[#64748b]">Cargando conectores telemáticos...</td></tr>
              ` : connectors.map(c => `
                <tr>
                  <td class="font-bold text-[#1e293b] flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full ${c.estado === 'activo' ? 'bg-emerald-500' : 'bg-slate-400'}"></span>
                    ${c.nombre}
                  </td>
                  <td class="font-mono text-[#1e293b]">${c.protocolo}</td>
                  <td>
                    <span class="gl-badge ${c.estado === 'activo' ? 'gl-badge-success' : 'gl-badge-gold'} text-[9px]">
                      ${c.estado.replace('_', ' ')}
                    </span>
                  </td>
                  <td class="font-mono text-[#2b7a59] font-bold">${c.aceptados || 0}</td>
                  <td class="font-mono text-[#36536e] font-bold">${c.rechazados || 0}</td>
                  <td class="font-mono text-[#64748b] text-[11px]">${c.ultimo_evento ? new Date(c.ultimo_evento).toLocaleTimeString() : 'En espera'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Simulador de Pruebas & Datos Sintéticos -->
      <div class="gl-card p-6 sm:p-8 bg-white border border-[#d4dfe8]">
        <div class="flex items-center justify-between pb-3 mb-4 border-b border-[#d4dfe8]">
          <div>
            <span class="gl-subtitle text-[#2e5b82] block mb-0.5">ENTORNO DE PRUEBAS DE CARGA</span>
            <h3 class="font-sans text-lg font-bold text-[#1e293b]">Generador de Escenarios & Pruebas Sintéticas</h3>
            <p class="text-xs text-[#475569] mt-0.5">
              Genera inventarios reproducibles con seed determinista según la distribución de Nexus para pruebas de estrés.
            </p>
          </div>
          <i data-lucide="cpu" class="w-6 h-6 text-[#2e5b82]"></i>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          
          <div class="p-4 rounded border border-[#d4dfe8] bg-[#f8fafc] flex flex-col justify-between">
            <div>
              <strong class="text-[#1e293b] block mb-1">Generar Dataset Sintético</strong>
              <p class="text-[#64748b] text-[11px] mb-3">Inyecta 120 equipos respetando proporciones reales para pruebas.</p>
              <div class="flex items-center gap-2 mb-3">
                <span class="text-[#64748b]">Seed:</span>
                <input type="number" id="synthetic-seed" value="42" class="w-20 px-2 py-1 bg-white border border-[#cbd5e1] rounded text-center text-[#1e293b] font-mono">
                <span class="text-[#64748b] ml-2">Equipos:</span>
                <input type="number" id="synthetic-count" value="120" class="w-20 px-2 py-1 bg-white border border-[#cbd5e1] rounded text-center text-[#1e293b] font-mono">
              </div>
            </div>
            <button id="btn-generate-synthetic" class="gl-btn-black w-full justify-center">
              <i data-lucide="play" class="w-4 h-4 text-[#2e5b82]"></i>
              <span>Generar Inventario</span>
            </button>
          </div>

          <div class="p-4 rounded border border-[#d4dfe8] bg-[#f8fafc] flex flex-col justify-between">
            <div>
              <strong class="text-[#1e293b] block mb-1">Limpieza de Datos Sintéticos</strong>
              <p class="text-[#64748b] text-[11px] mb-3">Elimina únicamente los datos generados de prueba, conservando la flota real de la demo intacta.</p>
            </div>
            <button id="btn-clean-synthetic" class="gl-btn-outline w-full justify-center text-[#36536e] border-[#fca5a5] hover:bg-rose-50">
              <i data-lucide="trash-2" class="w-4 h-4 text-[#36536e]"></i>
              <span>Limpiar Solo Sintéticos</span>
            </button>
          </div>

        </div>
      </div>

    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: container });

  const btnGen = container.querySelector('#btn-generate-synthetic');
  const btnClean = container.querySelector('#btn-clean-synthetic');

  if (btnGen) {
    btnGen.addEventListener('click', async () => {
      if (navigator.vibrate) navigator.vibrate(20);
      btnGen.disabled = true;
      btnGen.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin text-[#2e5b82]"></i><span>Generando...</span>`;
      if (window.lucide) window.lucide.createIcons({ root: btnGen });

      const seed = parseInt(document.getElementById('synthetic-seed').value) || 42;
      const count = parseInt(document.getElementById('synthetic-count').value) || 120;
      try {
        const res = await window.apiClient.generarSintetico(count, seed);
        if (window.showToast) {
          window.showToast(`POST /api/sintetico/generar: 200 OK — ${count} equipos inyectados (Seed: ${seed})`, 'success');
        }
        window.appStore.refreshAll();
      } catch (err) {
        if (window.showToast) window.showToast(`Error al generar: ${err.message}`, 'error');
      } finally {
        btnGen.disabled = false;
        btnGen.innerHTML = `<i data-lucide="play" class="w-4 h-4 text-[#2e5b82]"></i><span>Generar Inventario</span>`;
        if (window.lucide) window.lucide.createIcons({ root: btnGen });
      }
    });
  }

  if (btnClean) {
    btnClean.addEventListener('click', async () => {
      if (navigator.vibrate) navigator.vibrate(20);
      btnClean.disabled = true;
      btnClean.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin text-[#36536e]"></i><span>Limpiando...</span>`;
      if (window.lucide) window.lucide.createIcons({ root: btnClean });

      try {
        const res = await window.apiClient.limpiarSintetico();
        if (window.showToast) {
          window.showToast('POST /api/sintetico/limpiar: 200 OK — Base sintética purgada. Flota restablecida.', 'success');
        }
        window.appStore.refreshAll();
      } catch (err) {
        if (window.showToast) window.showToast(`Error al limpiar: ${err.message}`, 'error');
      } finally {
        btnClean.disabled = false;
        btnClean.innerHTML = `<i data-lucide="trash-2" class="w-4 h-4 text-[#36536e]"></i><span>Limpiar Solo Sintéticos</span>`;
        if (window.lucide) window.lucide.createIcons({ root: btnClean });
      }
    });
  }
}

window.renderConnectors = renderConnectors;
