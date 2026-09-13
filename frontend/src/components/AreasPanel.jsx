// Dónde sangra la compañía, por las tres áreas de ECON: Maquinaria,
// Logística y Proyectos. Cada una tiene su pregunta y sus cifras.
//
// Lo que NO es decorativo: la separación entre lo medido y lo supuesto. Los
// conteos salen de la base y se pueden auditar; los costos unitarios son
// supuestos nuestros y se ven como tales. Si eso se mezcla en pantalla, la
// cifra deja de ser defendible frente a alguien que conoce la empresa.
// Duenio: Majo
import { useEffect, useState } from 'react'
import * as api from '../api.js'

const AREAS = [
  ['maquinaria', 'Maquinaria', 'dueña del activo'],
  ['logistica', 'Logística', 'mueve el equipo'],
  ['proyectos', 'Proyectos', 'paga las horas'],
]

const fmt = (v, unidad) => {
  if (v == null) return '—'
  if (unidad === 'USD' || unidad === 'USD/semana') {
    return v.toLocaleString('en-US', { style: 'currency', currency: 'USD',
      maximumFractionDigits: 0 })
  }
  return Number.isInteger(v) ? String(v) : v.toFixed(1)
}

function Base({ base }) {
  // La base medida es la prueba de que la cifra no salió de la nada.
  const partes = Object.entries(base || {}).filter(
    ([, v]) => v != null && !(Array.isArray(v) && v.length === 0))
  if (!partes.length) return null
  return (
    <ul className="ar-base">
      {partes.map(([k, v]) => (
        <li key={k}>
          <i>{k.replace(/_/g, ' ')}</i>
          <span>{Array.isArray(v) ? v.join(', ') : String(v)}</span>
        </li>
      ))}
    </ul>
  )
}

export default function AreasPanel() {
  const [area, setArea] = useState('maquinaria')
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)
  const [verSup, setVerSup] = useState(false)

  useEffect(() => {
    setDatos(null)
    api.getSangrado(area)
      .then((d) => { setDatos(d); setError(null) })
      .catch((e) => { setDatos(null); setError(e.message) })
  }, [area])

  const bloque = datos?.areas?.[0]

  return (
    <div className="ar-panel">
      <p className="ar-intro">
        Tres áreas, tres pérdidas distintas. Un tablero que les muestra lo mismo
        a las tres no le sirve a ninguna.
      </p>

      <nav className="ar-tabs">
        {AREAS.map(([k, nombre, que]) => (
          <button key={k} className={area === k ? 'on' : ''} onClick={() => setArea(k)}>
            <b>{nombre}</b><i>{que}</i>
          </button>
        ))}
      </nav>

      {error && <p className="ps-vacio">No se pudo cargar: {error}</p>}
      {!datos && !error && <p className="ps-vacio">Cargando…</p>}

      {bloque && (
        <>
          <p className="ar-pregunta">«{bloque.pregunta}»</p>

          <div className="ar-cifras">
            {bloque.cifras.map((c) => {
              const supuesta = c.supuesto_aplicado.length > 0
              return (
                <article key={c.titulo} className={`ar-cifra${supuesta ? ' sup' : ''}`}>
                  <header>
                    <span className="ar-val">{fmt(c.valor, c.unidad)}</span>
                    <span className="ar-uni">{c.unidad}</span>
                    <span className={`ar-tag ${supuesta ? 'sup' : 'med'}`}>
                      {supuesta ? 'con supuesto' : 'medido'}
                    </span>
                  </header>
                  <h5>{c.titulo}</h5>
                  <p>{c.detalle}</p>
                  <Base base={c.base_medida} />
                  {supuesta && (
                    <div className="ar-sup">
                      {c.supuesto_aplicado.map((s) => (
                        <p key={s.clave}>
                          <b>{s.valor} {s.unidad}</b> — {s.que_es}.
                          <i> {s.fuente}</i>
                        </p>
                      ))}
                    </div>
                  )}
                </article>
              )
            })}
          </div>

          {bloque.proyectos_afectados?.length > 0 && (
            <p className="ar-proys">
              Proyectos afectados: <b>{bloque.proyectos_afectados.join(' · ')}</b>
            </p>
          )}
        </>
      )}

      {datos?.supuestos && (
        <section className="ar-supuestos">
          <button type="button" onClick={() => setVerSup((v) => !v)}>
            {verSup ? '▾' : '▸'} Los {Object.keys(datos.supuestos).length} supuestos,
            completos — ninguno sale de un documento de ECON
          </button>
          {verSup && (
            <table>
              <thead>
                <tr><th>Supuesto</th><th>Valor</th><th>Qué es</th><th>Fuente</th></tr>
              </thead>
              <tbody>
                {Object.entries(datos.supuestos).map(([k, s]) => (
                  <tr key={k}>
                    <td>{k.replace(/_/g, ' ')}</td>
                    <td className="num">{s.valor} {s.unidad}</td>
                    <td>{s.que_es}</td>
                    <td className="fuente">{s.fuente}</td>
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
