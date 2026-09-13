// Command Center del Hub de Operaciones.
// Duenio: Majo. Wilbert no edita este archivo; si necesita un dato nuevo,
// lo expone en la API y lo avisa.
import { useCallback, useEffect, useMemo, useState } from 'react'
import * as api from './api.js'
import FleetMap from './components/FleetMap.jsx'
import AssetCard from './components/AssetCard.jsx'
import EventFeed from './components/EventFeed.jsx'
import ConnectorHealth from './components/ConnectorHealth.jsx'
import DispatchPanel from './components/DispatchPanel.jsx'
import RoiPanel from './components/RoiPanel.jsx'
import PrismaStartrackPanel from './components/PrismaStartrackPanel.jsx'
import AreasPanel from './components/AreasPanel.jsx'

// "Captura de campo" (WhatsApp/FieldSim) se saco del Command Center — decision
// del equipo, no un bug. El backend (ingest/whatsapp.py) sigue intacto por si
// se retoma; solo la pestaña visible se quito. Ver FieldSim.jsx si se reactiva.
const TABS = [
  ['prisma', 'Prisma + Startrack'],
  ['areas', 'Por área'],
  ['despacho', 'Despacho'],
  ['conectores', 'Integración'],
  ['roi', 'Costos'],
]

export default function App() {
  const [assets, setAssets] = useState([])
  const [projects, setProjects] = useState([])
  const [alertas, setAlertas] = useState([])
  const [eventos, setEventos] = useState([])
  const [conectores, setConectores] = useState([])
  const [contrato, setContrato] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [corredores, setCorredores] = useState([])
  const [sel, setSel] = useState(null)
  const [detalle, setDetalle] = useState(null)
  const [despacho, setDespacho] = useState(null)
  const [tab, setTab] = useState('prisma')
  const [conexion, setConexion] = useState('conectando')

  // --- carga inicial
  useEffect(() => {
    Promise.all([
      api.getAssets(), api.getProjects(), api.getAlerts(),
      api.getConnectors(), api.getContract(), api.getAnalytics(), api.getCorridors(),
    ])
      .then(([a, p, al, c, ct, an, co]) => {
        setAssets(a); setProjects(p); setAlertas(al)
        setConectores(c); setContrato(ct); setAnalytics(an); setCorredores(co)
      })
      .catch((e) => console.error('carga inicial', e))
  }, [])

  // --- stream en vivo
  useEffect(() => {
    return api.conectarStream((kind, data) => {
      if (kind === 'asset') {
        setAssets((prev) => {
          const i = prev.findIndex((x) => x.asset_identifier === data.asset_identifier)
          if (i === -1) return [...prev, data]
          const copia = [...prev]
          copia[i] = { ...copia[i], ...data }
          return copia
        })
      } else if (kind === 'event') {
        setEventos((prev) => [data, ...prev].slice(0, 40))
      } else if (kind === 'alert') {
        setAlertas((prev) => [data, ...prev].slice(0, 40))
      } else if (kind === 'dispatch') {
        setDespacho(data)
        setTab('despacho')
      }
    }, setConexion)
  }, [])

  // --- refresco periodico de lo agregado (conectores y costos)
  useEffect(() => {
    const t = setInterval(() => {
      api.getConnectors().then(setConectores).catch(() => {})
      api.getAnalytics().then(setAnalytics).catch(() => {})
      api.getContract().then(setContrato).catch(() => {})
    }, 5000)
    return () => clearInterval(t)
  }, [])

  // --- detalle del activo seleccionado
  useEffect(() => {
    if (!sel) return setDetalle(null)
    api.getAsset(sel).then(setDetalle).catch(() => setDetalle(null))
  }, [sel, assets])

  const resumen = useMemo(() => {
    const c = {}
    for (const a of assets) c[a.state] = (c[a.state] || 0) + 1
    return c
  }, [assets])

  const solicitar = useCallback(async (asset, dest) => {
    try {
      setDespacho(await api.crearDespacho({ asset_identifier: asset, dest_project: dest }))
      setTab('despacho')
    } catch (e) { alert(`No se pudo crear el traslado: ${e.message}`) }
  }, [])

  return (
    <div className="app">
      <header className="top">
        <div className="marca">
          <b>Hub de Operaciones</b>
          <span>Grupo ECON · CCV Logistics</span>
        </div>
        <div className="resumen">
          {['OPERANDO', 'RALENTI', 'FALLA', 'EN_TRASLADO', 'DISPONIBLE'].map((k) => (
            <span key={k} className={k}>
              <b>{resumen[k] || 0}</b>{k.replace('_', ' ').toLowerCase()}
            </span>
          ))}
        </div>
        <span className={`conexion ${conexion}`}>{conexion}</span>
      </header>

      <main>
        <section className="izq">
          <FleetMap assets={assets} projects={projects} seleccionado={sel} onSeleccionar={setSel} />
          <EventFeed eventos={eventos} alertas={alertas} onSeleccionar={setSel} />
        </section>

        <aside className="der">
          <AssetCard asset={detalle} onDespachar={(a) => { setSel(a); setTab('despacho') }} />

          <nav className="tabs">
            {TABS.map(([k, l]) => (
              <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</button>
            ))}
          </nav>

          <div className="panel">
            {tab === 'prisma' && <PrismaStartrackPanel />}
            {tab === 'areas' && <AreasPanel />}
            {tab === 'despacho' && (
              <DispatchPanel despacho={despacho} corredores={corredores} proyectos={projects}
                             assetSel={sel} onSolicitar={solicitar} />
            )}
            {tab === 'conectores' && <ConnectorHealth conectores={conectores} contrato={contrato} />}
            {tab === 'roi' && <RoiPanel analytics={analytics} />}
          </div>
        </aside>
      </main>
    </div>
  )
}
