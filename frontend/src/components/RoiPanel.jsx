// Tablero de costos. Cierre de la demo, dirigido a los jueces directivos.
// Duenio: Josue (numeros) / Majo (vista)
const usd = (n) => `$${(n ?? 0).toLocaleString('en-US')}`

export default function RoiPanel({ analytics }) {
  if (!analytics) return null
  const m = analytics.modelo_anual
  const s = analytics.sesion

  return (
    <div className="roi">
      <div className="tiles">
        <div className="tile">
          <p className="k">Beneficio anual proyectado</p>
          <p className="v">{usd(m.beneficio_total)}</p>
          <p className="n">{usd(m.ahorro_diesel)} diésel · {usd(m.ahorro_logistica)} logística · {usd(m.ahorro_taller)} taller</p>
        </div>
        <div className="tile">
          <p className="k">Retorno de inversión</p>
          <p className="v">{m.roi_meses} meses</p>
          <p className="n">{usd(m.capex)} CAPEX + {usd(m.opex_anual)}/año OPEX</p>
        </div>
        <div className="tile">
          <p className="k">Galones de ralentí evitados</p>
          <p className="v">{(m.galones_evitados ?? 0).toLocaleString('en-US')}</p>
          <p className="n">100 equipos · 1 h/día · 300 días · $4.00/gal</p>
        </div>
      </div>

      <h4>Impacto observado en esta sesión</h4>
      <div className="sesion">
        <span><b>{s.eventos_normalizados}</b> eventos normalizados</span>
        <span><b>{s.traslados_reprogramados}</b> traslados reprogramados</span>
        <span><b>{usd(s.detenciones_evitadas_usd)}</b> en detenciones evitadas</span>
        <span><b>{s.galones_ralenti_detectados} gal</b> de ralentí detectado</span>
      </div>

      <h4>Indicadores</h4>
      <table className="kpis">
        <thead><tr><th>KPI</th><th>Línea base</th><th>Con el Hub</th><th>Mecanismo</th></tr></thead>
        <tbody>
          {analytics.kpis.map((k) => (
            <tr key={k.kpi}>
              <th>{k.kpi}</th><td>{k.base}</td><td className="mejor">{k.con_hub}</td><td className="mec">{k.mecanismo}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
