// Integración oficial del sandbox: Prisma / Nexus (solicitudes y estado del
// recurso) + Startrack (tareas de traslado). Solo lectura y correlación — el
// reto pide consultar, relacionar, interpretar sin asumir inconsistencia, y
// alertar cuando la combinación de estados SÍ es un riesgo real.
//
// Anclado al manual de Nexus ECON: el estado del recurso sale del catálogo
// cerrado de Módulo 8 y la exposición se valoriza con la tarifa horaria real.
// Duenio: Majo
import { useEffect, useState } from 'react'
import * as api from '../api.js'

const MAQUINA_DEMO = 'EXC-01'

// El PEA lo aprueba una PERSONA. El campo existe para que eso se vea en
// pantalla: el Hub automatiza la evidencia, no la decision.
function SelloPEA({ maquinaria }) {
  const [quien, setQuien] = useState('')
  const [pea, setPea] = useState(null)
  const [verif, setVerif] = useState(null)
  const [error, setError] = useState(null)
  const [ocupado, setOcupado] = useState(false)

  const sellar = () => {
    if (!quien.trim()) { setError('Escribí quién aprueba. Es una persona.'); return }
    setOcupado(true); setError(null); setVerif(null)
    api.sellarPEA(maquinaria, quien.trim())
      .then((d) => setPea(d))
      .catch((e) => setError(e.message))
      .finally(() => setOcupado(false))
  }

  const verificar = () => {
    if (!pea) return
    api.verificarPEA(pea.id).then(setVerif).catch((e) => setError(e.message))
  }

  return (
    <div className="pea">
      <h5>Evidencia sellada — PEA</h5>
      {!pea && (
        <div className="pea-form">
          <input
            value={quien}
            placeholder="¿Quién aprueba? (nombre y cargo)"
            onChange={(e) => setQuien(e.target.value)}
          />
          <button type="button" onClick={sellar} disabled={ocupado}>
            {ocupado ? 'Sellando…' : 'Sellar evidencia'}
          </button>
        </div>
      )}

      {error && <p className="pea-error">{error}</p>}

      {pea && (
        <>
          <div className="pea-montos">
            <span>
              <i>Nexus factura</i>
              {usd(pea.monto_facturable)}
            </span>
            <span className={pea.exposicion_usd ? 'exp' : ''}>
              <i>De eso, sin respaldo medido</i>
              {usd(pea.exposicion_usd)}
            </span>
          </div>
          {pea.medicion === 'sin datos' && (
            <p className="pea-aviso">
              Sin horas medidas: los dos montos coinciden porque no hay nada
              que descontar. <b>No es que midiera cero</b> — es que no hay medición.
            </p>
          )}

          <dl className="pea-meta">
            <div><dt>Aprobado por</dt><dd>{pea.aprobado_por}</dd></div>
            <div><dt>Esquema</dt><dd>{pea.esquema}</dd></div>
          </dl>

          <code className="pea-hash">{pea.hash}</code>

          <button type="button" className="pea-verif" onClick={verificar}>
            Verificar recomputando
          </button>

          {verif && (
            <div className={`pea-resultado ${verif.verifica ? 'ok' : 'mal'}`}>
              <b>{verif.verifica ? 'Verifica' : 'NO verifica'}</b>
              <p>
                El hash se recalculó desde el contenido y dio
                {verif.verifica ? ' idéntico' : ' distinto'}. Cualquiera con
                lectura en Nexus y Startrack puede repetir esto:
                <b> no hay que confiar en el Hub.</b>
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}

const usd = (n) =>
  n == null ? '—' : n.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

function Fila({ dt, children }) {
  return <div><dt>{dt}</dt><dd>{children}</dd></div>
}

// Catálogo de Startrack (O: Default Vehicle Status). El 3 es el rastreador
// averiado, no la máquina: por eso no se pinta como crítico.
const ESTADO_VEHICULO = {
  0: ['Normal', 'ok'],
  1: ['En Mantenimiento', 'critico'],
  2: ['Fuera de Servicio', 'critico'],
  3: ['Rastreador en reparación', 'alerta'],
  4: ['Uso ocasional', 'info'],
}

const haceCuanto = (s) => {
  if (s == null) return null
  const h = Math.round(s / 3600)
  if (h < 1) return 'hace menos de 1 h'
  return h < 48 ? `hace ${h} h` : `hace ${Math.round(h / 24)} días`
}

export default function PrismaStartrackPanel() {
  const [maquinas, setMaquinas] = useState([])
  const [sel, setSel] = useState(MAQUINA_DEMO)
  const [ops, setOps] = useState(null)
  const [error, setError] = useState(null)
  const [mapeo, setMapeo] = useState(null)
  const [verMapeo, setVerMapeo] = useState(false)

  useEffect(() => {
    api.getMaquinasPS().then((m) => {
      setMaquinas(m)
      // EXC-01 es el caso de la demo: si está, manda, sin importar el orden.
      if (m.length && !m.find((x) => x.maquinaria === MAQUINA_DEMO)) setSel(m[0].maquinaria)
    }).catch(() => {})
    api.getMapeoPS().then(setMapeo).catch(() => {})
  }, [])

  useEffect(() => {
    if (!sel) return
    api.getVistaUnificada(sel)
      .then((o) => { setOps(o); setError(null) })
      .catch((e) => { setOps([]); setError(e.message) })
  }, [sel])

  const expuesto = (ops || []).reduce((a, o) => a + ((o.exposicion || {}).costo_usd || 0), 0)
  const conAlerta = (ops || []).filter((o) => o.nivel === 'alerta' || o.nivel === 'critico').length

  return (
    <div className="ps-panel">
      <p className="ps-intro">
        Prisma / Nexus tiene la <b>solicitud</b> y el estado del recurso. Startrack
        tiene la <b>tarea de traslado</b>, la ubicación y la conexión. Son dos
        sistemas de registro distintos: aquí se consultan juntos, se interpretan
        sin asumir que un desfase es un error, y se alerta solo cuando de verdad
        hay riesgo.
      </p>

      {mapeo && (
        <p className={`ps-origen ${mapeo.origen}`}>
          {mapeo.origen === 'startrack'
            ? 'Conectado a Startrack — datos en vivo'
            : 'Datos simulados con los casos reales de Nexus y Startrack'}
        </p>
      )}

      <div className="ps-kpis">
        <div className="ps-kpi">
          <span className="ps-kpi-num">{usd(expuesto)}</span>
          <span className="ps-kpi-lbl">Costo Real sin Valor Ganado</span>
        </div>
        <div className={`ps-kpi${conAlerta ? ' alerta' : ''}`}>
          <span className="ps-kpi-num">{conAlerta}</span>
          <span className="ps-kpi-lbl">operaciones que requieren acción</span>
        </div>
      </div>

      <label htmlFor="ps-maquina">Maquinaria</label>
      <select id="ps-maquina" value={sel} onChange={(e) => setSel(e.target.value)}>
        {maquinas.map((m) => (
          <option key={m.maquinaria} value={m.maquinaria}>
            {m.maquinaria} · {m.operaciones} operación{m.operaciones === 1 ? '' : 'es'}
            {m.con_alerta > 0 ? ` · ${m.con_alerta} con alerta` : ''}
            {m.costo_expuesto_usd > 0 ? ` · ${usd(m.costo_expuesto_usd)}` : ''}
          </option>
        ))}
      </select>

      {error && <p className="ps-vacio">Sin datos para {sel}: {error}</p>}
      {ops === null && !error && <p className="ps-vacio">Cargando…</p>}

      <div className="ps-ops">
        {(ops || []).map((o) => (
          <article key={o.solicitud.solicitud_id} className={`ps-op n-${o.nivel}`}>
            <header>
              <div>
                <h4>{o.proyecto_nombre}</h4>
                <span className="ps-proj">
                  {o.proyecto_id}{o.no_activo ? ` · ${o.no_activo}` : ''}
                </span>
              </div>
              <span className={`ps-estado n-${o.nivel}`}>{o.etiqueta}</span>
            </header>

            <div className="ps-cols">
              <section className="ps-col prisma">
                <h5>Prisma / Nexus</h5>
                <dl>
                  <Fila dt="Solicitud">{o.solicitud.solicitud_id}</Fila>
                  <Fila dt="Estado sol.">{o.solicitud.estado_solicitud || '—'}</Fila>
                  <Fila dt="No. activo">{o.solicitud.no_activo || 'Sin asignar'}</Fila>
                  {o.solicitud.clave && <Fila dt="Clave">{o.solicitud.clave}</Fila>}
                  <Fila dt="Clase">{o.solicitud.clase_equipo || o.solicitud.tipo_solicitado || '—'}</Fila>
                  <Fila dt="Estado maq.">
                    <span className={`ps-chip n-${o.nivel}`}>
                      {o.solicitud.estado_maquinaria || 'Sin unidad'}
                    </span>
                  </Fila>
                  {o.solicitud.operador && <Fila dt="Operador">{o.solicitud.operador}</Fila>}
                  {o.solicitud.partida_asignada && (
                    <Fila dt="Partida">{o.solicitud.partida_asignada}</Fila>
                  )}
                  {o.solicitud.precio_hora != null && (
                    <Fila dt="Tarifa">
                      {usd(o.solicitud.precio_hora)}/h · mín. {o.solicitud.horas_minimas} h/jornada
                    </Fila>
                  )}
                  {(o.solicitud.fecha_inicio || o.solicitud.fecha_fin) && (
                    <Fila dt="Vigencia">{o.solicitud.fecha_inicio} → {o.solicitud.fecha_fin}</Fila>
                  )}
                </dl>
              </section>

              <section className="ps-col startrack">
                <h5>Startrack</h5>
                {o.tarea ? (
                  <dl>
                    <Fila dt="Tarea">{o.tarea.tarea_id}</Fila>
                    <Fila dt="Estado tarea">
                      <span className={`ps-chip n-${o.nivel}`}>{o.tarea.estado_tarea}</span>
                    </Fila>
                    <Fila dt="remote_id">{o.tarea.remote_id || o.tarea.identificador_raw || '—'}</Fila>
                    <Fila dt="Programada">{o.tarea.fecha_programada || '—'}</Fila>
                    <Fila dt="Destino">{o.tarea.destino_proyecto_nombre}</Fila>
                    <Fila dt="Motorista">{o.tarea.motorista_nombre}</Fila>
                    <Fila dt="Conexión">
                      <span className={`ps-chip n-${o.nivel}`}>{o.tarea.conexion || '—'}</span>
                      {o.tarea.coms_age_s != null && (
                        <span className="ps-sub"> reportó {haceCuanto(o.tarea.coms_age_s)}</span>
                      )}
                    </Fila>
                    {o.tarea.estado_vehiculo != null && (
                      <Fila dt="Estado veh.">
                        <span className={`ps-chip n-${(ESTADO_VEHICULO[o.tarea.estado_vehiculo] || [])[1] || 'info'}`}>
                          {(ESTADO_VEHICULO[o.tarea.estado_vehiculo] || ['—'])[0]}
                        </span>
                      </Fila>
                    )}
                    <Fila dt="Último evento">
                      {o.tarea.ultimo_evento || '—'}
                      {o.tarea.ultimo_evento_at ? ` · ${o.tarea.ultimo_evento_at.slice(0, 16).replace('T', ' ')}` : ''}
                    </Fila>
                  </dl>
                ) : <p className="ps-vacio">Sin tarea de traslado relacionada.</p>}
              </section>
            </div>

            <p className="ps-interpretacion">{o.interpretacion}</p>

            {o.exposicion && o.exposicion.horas_facturadas > 0 && (
              <div className={`ps-exposicion${o.exposicion.costo_usd < 100 ? ' menor' : ''}`}>
                <b>{usd(o.exposicion.costo_usd)} de exposición</b>
                <div className="ps-horas">
                  <span><i>Nexus facturó</i>{o.exposicion.horas_facturadas} h</span>
                  <span><i>Startrack midió</i>
                    {o.exposicion.horas_medidas != null
                      ? `${o.exposicion.horas_medidas} h`
                      : 'sin datos'}
                  </span>
                  <span className="fuerte"><i>Sin respaldo</i>{o.exposicion.horas_sin_respaldo} h</span>
                </div>
                <p>{o.exposicion.explicacion}</p>
              </div>
            )}

            <p className={`ps-accion n-${o.nivel}`}>
              <b>{o.accion}</b> → {o.responsable}
            </p>

            {o.tarea && <SelloPEA maquinaria={o.maquinaria} />}
          </article>
        ))}
      </div>

      {mapeo && (
        <section className="ps-mapeo">
          <button type="button" onClick={() => setVerMapeo((v) => !v)}>
            {verMapeo ? '▾' : '▸'} Mapeo de campos entre plataformas ({mapeo.campos.length})
          </button>
          {verMapeo && (
            <table>
              <thead>
                <tr><th>Concepto</th><th>Prisma / Nexus</th><th>Startrack</th><th>Decisión</th></tr>
              </thead>
              <tbody>
                {mapeo.campos.map((c) => (
                  <tr key={c.concepto}>
                    <td>{c.concepto}</td>
                    <td>{c.nexus}</td>
                    <td>{c.startrack}</td>
                    <td>{c.decision}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  )
}
