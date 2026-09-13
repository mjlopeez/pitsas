// Componente Mapa de Flota y Geocercas (Leaflet)
// Estética Editorial Goodlife El Salvador (No AI Slop)

let mapInstance = null;
let assetMarkersLayer = null;
let projectCirclesLayer = null;

function renderFleetMap(container) {
  const state = window.appStore.state;
  const assets = state.assets || [];
  const projects = state.projects || [];

  container.innerHTML = `
    <div class="space-y-4">
      
      <!-- Barra Editorial de Control del Mapa -->
      <div class="gl-card p-4 sm:p-5 bg-white border border-[#e8e6e1] flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded bg-[#faf9f6] border border-[#d6d3cb] flex items-center justify-center text-[#bf9410] shrink-0">
            <i data-lucide="map-pin" class="w-4 h-4"></i>
          </div>
          <div>
            <span class="gl-subtitle text-[#bf9410] block text-[9px]">COBERTURA NACIONAL • 18 PROYECTOS</span>
            <h2 class="font-editorial-serif text-base sm:text-lg font-normal text-[#111111]">Geolocalización Satelital & Geocercas de Obra</h2>
          </div>
        </div>

        <!-- Filtros Rápidos de Capas en Mapa -->
        <div class="flex items-center gap-2 text-xs flex-wrap">
          <span class="text-[#777777] font-semibold">Filtrar:</span>
          <button id="map-filter-all" class="px-3 py-1.5 rounded bg-[#111111] text-white font-semibold text-xs transition-colors">Todos (${assets.length})</button>
          <button id="map-filter-on" class="px-3 py-1.5 rounded bg-white text-[#333333] hover:text-[#111111] border border-[#d6d3cb] text-xs transition-colors">Solo ON</button>
          <button id="map-filter-idle" class="px-3 py-1.5 rounded bg-white text-[#333333] hover:text-[#111111] border border-[#d6d3cb] text-xs transition-colors">Solo Ralentí</button>
          <button id="map-btn-recenter" class="gl-btn-outline py-1 px-3 text-xs">
            <i data-lucide="maximize-2" class="w-3.5 h-3.5"></i> Recentrar
          </button>
        </div>
      </div>

      <!-- Contenedor del Mapa -->
      <div class="gl-card p-2 bg-white border border-[#e8e6e1] relative">
        <div id="fleet-map" class="h-[520px] rounded border border-[#e8e6e1]"></div>

        <!-- Leyenda Flotante -->
        <div class="absolute bottom-5 right-5 z-[400] bg-white/95 backdrop-blur-md p-3.5 rounded border border-[#e8e6e1] text-xs shadow-lg hidden sm:block">
          <div class="font-bold text-[#111111] mb-2 text-[10px] uppercase tracking-wider">Leyenda de Telemetría</div>
          <div class="space-y-1.5">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-emerald-500 shadow-sm"></span>
              <span class="text-[#444444]">Motor Encendido (ON)</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-amber-500 shadow-sm"></span>
              <span class="text-[#444444]">Motor en Ralentí (IDLE)</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-slate-400"></span>
              <span class="text-[#444444]">Motor Apagado (OFF)</span>
            </div>
            <div class="flex items-center gap-2 pt-1 border-t border-[#e8e6e1]">
              <span class="w-3 h-3 rounded-full border-2 border-[#bf9410] bg-[#bf9410]/20"></span>
              <span class="text-[#444444]">Geocerca de Proyecto</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  `;

  if (window.lucide) window.lucide.createIcons({ root: container });

  setTimeout(() => initLeafletMap(assets, projects), 50);

  // Filtros
  const btnAll = container.querySelector('#map-filter-all');
  const btnOn = container.querySelector('#map-filter-on');
  const btnIdle = container.querySelector('#map-filter-idle');
  const btnRecenter = container.querySelector('#map-btn-recenter');

  const updateButtons = (activeBtn) => {
    [btnAll, btnOn, btnIdle].forEach(b => {
      if (b === activeBtn) {
        b.className = 'px-3 py-1.5 rounded bg-[#111111] text-white font-semibold text-xs transition-colors';
      } else {
        b.className = 'px-3 py-1.5 rounded bg-white text-[#333333] hover:text-[#111111] border border-[#d6d3cb] text-xs transition-colors';
      }
    });
  };

  if (btnAll) {
    btnAll.addEventListener('click', () => {
      updateButtons(btnAll);
      plotAssetsOnMap(assets);
    });
  }

  if (btnOn) {
    btnOn.addEventListener('click', () => {
      updateButtons(btnOn);
      plotAssetsOnMap(assets.filter(a => a.engine_state === 'ON'));
    });
  }

  if (btnIdle) {
    btnIdle.addEventListener('click', () => {
      updateButtons(btnIdle);
      plotAssetsOnMap(assets.filter(a => a.engine_state === 'IDLE'));
    });
  }

  if (btnRecenter && mapInstance) {
    btnRecenter.addEventListener('click', () => {
      mapInstance.setView([13.7, -89.25], 10);
    });
  }
}

function initLeafletMap(assets, projects) {
  if (typeof L === 'undefined') return;

  const mapContainer = document.getElementById('fleet-map');
  if (!mapContainer) return;

  if (mapInstance) {
    mapInstance.remove();
    mapInstance = null;
  }

  // Centro en El Salvador
  mapInstance = L.map('fleet-map', {
    center: [13.7, -89.25],
    zoom: 10,
    zoomControl: true
  });

  // Capa de mapa base CartoDB Voyager (limpia, clara, editorial)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(mapInstance);

  projectCirclesLayer = L.layerGroup().addTo(mapInstance);
  assetMarkersLayer = L.layerGroup().addTo(mapInstance);

  plotProjectsOnMap(projects);
  plotAssetsOnMap(assets);
}

function plotProjectsOnMap(projects) {
  if (!projectCirclesLayer) return;
  projectCirclesLayer.clearLayers();

  projects.forEach(proj => {
    if (!proj.lat || !proj.lon) return;

    const color = proj.kind === 'planta_concreto' ? '#0e2439' :
                  proj.kind === 'planta_asfalto' ? '#bf9410' :
                  proj.kind === 'cantera' ? '#423d90' :
                  proj.kind === 'aeropuerto' ? '#c62828' : '#111111';

    const circle = L.circle([proj.lat, proj.lon], {
      color: color,
      fillColor: color,
      fillOpacity: 0.12,
      weight: 1.5,
      radius: proj.radius_m || 1000
    });

    circle.bindPopup(`
      <div class="text-xs p-1 font-sans" style="color: #111111;">
        <div class="font-bold text-sm mb-1">${proj.name}</div>
        <div class="text-[#555555] mb-1"><strong>ID Proyecto:</strong> ${proj.project_id}</div>
        <div class="text-[#555555] mb-1"><strong>Tipo:</strong> <span class="capitalize">${proj.kind.replace('_', ' ')}</span></div>
        <div class="text-[#555555]"><strong>Radio Geocerca:</strong> ${proj.radius_m} m</div>
      </div>
    `);

    projectCirclesLayer.addLayer(circle);
  });
}

function plotAssetsOnMap(assets) {
  if (!assetMarkersLayer) return;
  assetMarkersLayer.clearLayers();

  assets.forEach(asset => {
    if (!asset.lat || !asset.lon) return;

    const stateColor = asset.engine_state === 'ON' ? '#10b981' :
                       asset.engine_state === 'IDLE' ? '#f59e0b' : '#64748b';

    const iconHtml = `
      <div style="background-color: ${stateColor}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid #ffffff; box-shadow: 0 0 6px rgba(0,0,0,0.3); cursor: pointer;"></div>
    `;

    const customIcon = L.divIcon({
      html: iconHtml,
      className: 'custom-asset-pin',
      iconSize: [14, 14],
      iconAnchor: [7, 7]
    });

    const marker = L.marker([asset.lat, asset.lon], { icon: customIcon });

    const pctServicio = Math.min(100, Math.max(0, Math.round(asset.pct_servicio || 0)));
    const serviceBarColor = pctServicio > 90 ? 'bg-[#c62828]' : 'bg-[#0e2439]';

    marker.bindPopup(`
      <div class="text-xs p-1 font-sans" style="min-width: 220px; color: #111111;">
        <div class="flex items-center justify-between border-b border-[#e8e6e1] pb-1.5 mb-2">
          <span class="font-bold text-sm font-mono text-[#111111]">${asset.asset_identifier}</span>
          <span class="gl-badge ${asset.engine_state === 'ON' ? 'gl-badge-success' : asset.engine_state === 'IDLE' ? 'gl-badge-gold' : 'gl-badge-navy'} text-[9px]">
            ${asset.engine_state}
          </span>
        </div>
        <div class="space-y-1 text-[#555555] mb-2">
          <div><strong class="text-[#111111]">Equipo:</strong> ${asset.make} ${asset.model} (${asset.kind})</div>
          <div><strong class="text-[#111111]">Obra:</strong> ${asset.assigned_project || 'Sin Asignar'}</div>
          <div><strong class="text-[#111111]">Horómetro:</strong> <span class="font-mono text-[#111111] font-bold">${asset.operating_hours?.toFixed(1) || 0} h</span></div>
          <div><strong class="text-[#111111]">Combustible:</strong> <span class="font-mono text-[#111111]">${asset.cumulative_fuel?.toFixed(1) || 0} gal</span></div>
        </div>
        <div class="mb-2">
          <div class="flex justify-between text-[10px] text-[#777777] mb-0.5">
            <span>Intervalo Mantenimiento (250h)</span>
            <span class="font-mono font-bold ${pctServicio > 90 ? 'text-[#c62828]' : 'text-[#111111]'}">${pctServicio}%</span>
          </div>
          <div class="service-progress-bg">
            <div class="service-progress-bar ${serviceBarColor}" style="width: ${pctServicio}%"></div>
          </div>
        </div>
        <button onclick="window.openAssetModal('${asset.asset_identifier}')" class="gl-btn-black w-full justify-center text-xs mt-1">
          Ficha Técnica
        </button>
      </div>
    `);

    assetMarkersLayer.addLayer(marker);
  });
}

window.renderFleetMap = renderFleetMap;
window.plotAssetsOnMap = plotAssetsOnMap;
