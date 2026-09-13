// Panel de despacho con la veda del VMT dibujada sobre la linea de tiempo.
// Minuto 3 de la demo. Duenio: Majo
import { useState } from 'react'

// 24 h en pixeles proporcionales; las vedas vienen del backend.
function Linea({ plan, vedas }) {
  if (!plan) return null
  const hora = (iso) => {
    const d = new Date(iso)
    return d.getUTCHours() - 6 + d.getUTCMinutes() / 60
  }
  const salida = ((hora(plan.salida) + 24) % 24)
  const llegada = salida + plan.eta_minutos / 60
  const pct = (h) => `${(h / 24) * 100}%`

  return (
    <div className="linea">
      {vedas.map((v, i) => {
        const [h1, m1] = v.desde.split(':').map(Number)
        const [h2, m2] = v.hasta.split(':').map(Number)
        const a = h1 + m1 / 60, b = h2 + m2 / 60
        return (
          <div key={i} className="veda" title={`veda ${v.etiqueta} ${v.desde}–${v.hasta}`}
               style={{ left: pct(a), width: pct(b - a) }} />
        )
      })}
      <div className="viaje" style={{ left: pct(salida), width: pct(Math.max(0.4, llegada - salida)) }}>
        <span>{plan.salida_local?.slice(11)}</span>
      </div>
      {[0, 6, 12, 18, 24].map((h) => (
        <i key={h} className="tick" style={{ left: pct(h) }}><b>{String(h % 24).padStart(2, '0')}</b></i>
      ))}
    </div>
  )
}

export default function DispatchPanel({ despacho, corredores, proyectos, onSolicitar, assetSel }) {
  const [dest, setDest] = useState('PSD')
  const corredor = corredores.find((c) => c.corredor_id === (despacho?.plan?.corredor))
    || corredores.find((c) => c.corredor_id === 'panamericana_poniente')

  return (
    <div className="despacho">
      <div className="fila">
        <select id="dest-obra" value={dest} onChange={(e) => setDest(e.target.value)}>
          {proyectos.map((p) => <option key={p.project_id} value={p.project_id}>{p.name}</option>)}
        </select>
        <button className="btn" disabled={!assetSel}
                onClick={() => onSolicitar(assetSel, dest)}>
          {assetSel ? `Trasladar ${assetSel}` : 'Selecciona un activo'}
        </button>
      </div>

      {despacho && (
        <>
          <div className={`aptitud ${despacho.aptitud.apto ? 'ok' : 'bloqueado'}`}>
            {despacho.aptitud.apto
              ? 'Aptitud técnica validada: sin códigos de falla ni servicio vencido.'
              : `Bloqueado: ${despacho.aptitud.bloqueos.join(' · ')}`}
          </div>

          <Linea plan={despacho.plan} vedas={corredor?.vedas || []} />

          <div className={`plan ${despacho.plan.reprogramado ? 'reprog' : ''}`}>
            <p className="hora">{despacho.plan.salida_local?.slice(11)} → {despacho.plan.llegada_local?.slice(11)}</p>
            <p className="ruta">{despacho.plan.corredor_nombre} · {despacho.plan.eta_minutos} min · {despacho.km} km</p>
            <p className="razon">{despacho.plan.razon}</p>
            {despacho.plan.reprogramado && (
              <p className="alterna">
                Alternativa sin desvío: salir a las {despacho.alternativa_sin_desvio.salida_local?.slice(11)}
              </p>
            )}
          </div>

          <pre className="wa">{despacho.mensaje_whatsapp}</pre>
        </>
      )}
    </div>
  )
}
