// Mapa de flota. Leaflet directo (sin react-leaflet: una dependencia menos
// que puede fallar a las 08:00). Tiles de OpenStreetMap: sin token, sin cuenta.
// Duenio: Majo
import { useEffect, useRef } from 'react'
import L from 'leaflet'

const COLOR = {
  OPERANDO: '#1f7a52',
  RALENTI: '#b8860b',
  FALLA: '#a2241c',
  EN_MANTENIMIENTO: '#6b4ea8',
  EN_TRASLADO: '#1f5f8b',
  DISPONIBLE: '#6b7a88',
}

function icono(estado) {
  const c = COLOR[estado] || COLOR.DISPONIBLE
  const pulso = estado === 'FALLA' ? ' pulso' : ''
  return L.divIcon({
    className: '',
    html: `<span class="pin${pulso}" style="background:${c}"></span>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  })
}

export default function FleetMap({ assets, projects, seleccionado, onSeleccionar }) {
  const ref = useRef(null)
  const map = useRef(null)
  const marcadores = useRef(new Map())
  const capaObras = useRef(null)

  // --- init
  useEffect(() => {
    if (map.current) return
    map.current = L.map(ref.current, { zoomControl: true }).setView([13.6, -89.35], 10)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© OpenStreetMap',
    }).addTo(map.current)
    capaObras.current = L.layerGroup().addTo(map.current)
  }, [])

  // --- geocercas de obras y planteles
  useEffect(() => {
    if (!capaObras.current) return
    capaObras.current.clearLayers()
    for (const p of projects) {
      L.circle([p.lat, p.lon], {
        radius: p.radius_m,
        color: '#c14d18',
        weight: 1,
        fillOpacity: 0.05,
      })
        .bindTooltip(`${p.name} · geocerca ${p.radius_m} m`)
        .addTo(capaObras.current)
    }
  }, [projects])

  // --- marcadores de activos (se actualizan en sitio, no se recrean:
  //     recrear 151 marcadores en cada evento SSE hace parpadear el mapa)
  useEffect(() => {
    if (!map.current) return
    for (const a of assets) {
      if (a.lat == null || a.lon == null) continue
      const existente = marcadores.current.get(a.asset_identifier)
      if (existente) {
        existente.setLatLng([a.lat, a.lon])
        if (existente.__estado !== a.state) {
          existente.setIcon(icono(a.state))
          existente.__estado = a.state
        }
      } else {
        const m = L.marker([a.lat, a.lon], { icon: icono(a.state) })
          .addTo(map.current)
          .bindTooltip(
            `<b>${a.asset_identifier}</b><br>${a.make || ''} ${a.model || ''} · ${a.state}` +
            `<br>${(a.operating_hours ?? 0).toFixed(1)} h`,
          )
          .on('click', () => onSeleccionar(a.asset_identifier))
        m.__estado = a.state
        marcadores.current.set(a.asset_identifier, m)
      }
    }
  }, [assets, onSeleccionar])

  // --- centrar en el activo seleccionado
  useEffect(() => {
    if (!seleccionado || !map.current) return
    const a = assets.find((x) => x.asset_identifier === seleccionado)
    if (a?.lat != null) map.current.flyTo([a.lat, a.lon], 14, { duration: 0.6 })
  }, [seleccionado, assets])

  return (
    <div className="mapa-wrap">
      <div ref={ref} className="mapa" />
      <div className="leyenda">
        {Object.entries(COLOR).map(([k, c]) => (
          <span key={k}><i style={{ background: c }} />{k.replace('_', ' ').toLowerCase()}</span>
        ))}
      </div>
    </div>
  )
}
