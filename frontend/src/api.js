// Cliente del Hub. Una sola capa: si cambia una ruta, se cambia aqui.
// Duenio: Majo

// Token para los endpoints que MUTAN estado. Solo hace falta si el backend
// tiene HUB_ADMIN_TOKEN puesto (o sea, cuando esta expuesto por ngrok).
// En local, sin token, todo funciona igual y esto queda vacio.
// Las LECTURAS nunca lo necesitan.
let adminToken = ''
export const setAdminToken = (t) => { adminToken = t || '' }

const j = async (url, opts) => {
  const r = await fetch(url, opts)
  if (r.status === 401) {
    throw new Error('401: este endpoint modifica estado y pide token. '
                    + 'Llama setAdminToken(...) con el HUB_ADMIN_TOKEN del backend.')
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
  return r.json()
}

export const getAssets     = () => j('/api/assets')
export const getAsset      = (id) => j(`/api/assets/${encodeURIComponent(id)}`)
export const getProjects   = () => j('/api/projects')
export const getAlerts     = () => j('/api/alerts')
export const getConnectors = () => j('/api/connectors')
export const getContract   = () => j('/api/contract')
export const getAnalytics  = () => j('/api/analytics')
export const getCorridors  = () => j('/api/dispatch/corridors')

const post = (url, body) =>
  j(url, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      ...(adminToken ? { 'X-Hub-Token': adminToken } : {}),
    },
    body: JSON.stringify(body ?? {}),
  })

export const crearDespacho = (payload) => post('/api/dispatch', payload)
export const cerrarAlerta = (id) => post(`/api/alerts/${id}/cerrar`)
export const resetDemo = () => post('/admin/reset')

// SSE: el navegador reconecta solo. onEvent(kind, data)
export function conectarStream(onEvent, onEstado) {
  const es = new EventSource('/api/stream')
  es.addEventListener('open', () => onEstado?.('conectado'))
  es.addEventListener('error', () => onEstado?.('reconectando'))
  for (const kind of ['asset', 'event', 'alert', 'dispatch', 'carga']) {
    es.addEventListener(kind, (m) => {
      try { onEvent(kind, JSON.parse(m.data)) } catch { /* ignorar keep-alive */ }
    })
  }
  return () => es.close()
}

export const getMaquinasPS = () => j('/api/ps/maquinas')
export const getVistaUnificada = (maquinaria) => j(`/api/ps/vista-unificada/${encodeURIComponent(maquinaria)}`)
export const getMapeoPS = () => j('/api/ps/mapeo')
export const getGeocercas = () => j('/api/ps/geocercas')
export const getSangrado = (area) =>
  j(`/api/ps/sangrado${area ? `?area=${encodeURIComponent(area)}` : ''}`)
export const sellarPEA = (maquinaria, aprobadoPor) =>
  j(`/api/ps/pea/${encodeURIComponent(maquinaria)}`
    + `?aprobado_por=${encodeURIComponent(aprobadoPor)}`, { method: 'POST' })
export const listarPEA = () => j('/api/ps/pea')
export const verificarPEA = (id) => j(`/api/ps/pea/${id}/verificar`)
