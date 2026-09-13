// Simulador de WhatsApp: la red de seguridad de la demo.
// Misma tuberia aguas abajo que el webhook real (voz -> NER -> OCR -> evento).
// Si el alta en Meta no sale, esto ES la demo y el jurado ve lo mismo.
// Duenio: Wilbert (tuberia) / Majo (vista)
import { useState } from 'react'

const AUDIOS = [
  { ref: 'demo_hidraulica', label: 'Falla hidráulica · CAT 320 en San Diego' },
  { ref: 'demo_diesel', label: 'Vale de diésel · 120 gal en La Cantera' },
  { ref: 'demo_arribo', label: 'Arribo de cama baja · Planta San Diego' },
]

export default function FieldSim({ onEnviar, resultado }) {
  const [audio, setAudio] = useState(AUDIOS[0].ref)
  const [texto, setTexto] = useState('')
  const [conFoto, setConFoto] = useState(true)
  const [enviando, setEnviando] = useState(false)

  const enviar = async () => {
    setEnviando(true)
    try {
      await onEnviar({
        de: '+503-7777-1234',
        audio_ref: texto ? null : audio,
        texto: texto || null,
        // Placeholder: el pipeline real recibe la foto del tablero.
        // Majo: cambiar por un <input type="file"> que lea como base64.
        foto_b64: conFoto ? btoa('foto-tablero-demo') : null,
        lat: 13.4871,
        lon: -89.2961,
      })
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="sim">
      <div className="wa-chat">
        <div className="wa-head">Hub de Operaciones ECON · WhatsApp</div>
        <div className="wa-body">
          {resultado?.pipeline?.map((p, i) => (
            <div key={i} className={`wa-msg ${p.paso}`}>
              <span className="paso">{p.paso.replace('_', ' ')}</span>
              {p.texto && <p>{p.texto}</p>}
              {p.datos && (
                <ul>
                  {Object.entries(p.datos)
                    .filter(([, v]) => v !== null && v !== '' && (!Array.isArray(v) || v.length))
                    .map(([k, v]) => (
                      <li key={k}><b>{k}</b> {String(Array.isArray(v) ? v.join(', ') : v).slice(0, 90)}</li>
                    ))}
                </ul>
              )}
              {p.asset && <p className="res">→ {p.asset} {p.obra ? `(obra ${p.obra})` : ''}</p>}
              {p.concuerdan !== undefined && (
                <p className={p.concuerdan ? 'ok' : 'warn'}>
                  audio {p.audio_h} h vs foto {p.foto_h} h · {p.concuerdan ? 'se confirman' : 'discrepan'}
                </p>
              )}
              {p.confianza !== undefined && <em>confianza {p.confianza}</em>}
            </div>
          ))}
          {!resultado && <p className="vacio">Manda una nota de voz desde el campo.</p>}
        </div>
      </div>

      <div className="sim-ctrl">
        <label htmlFor="sim-audio">Nota de voz sembrada</label>
        <select id="sim-audio" value={audio} onChange={(e) => setAudio(e.target.value)}>
          {AUDIOS.map((a) => <option key={a.ref} value={a.ref}>{a.label}</option>)}
        </select>

        <label htmlFor="sim-texto">…o escribe el mensaje</label>
        <input id="sim-texto" value={texto} placeholder="se reventó la manguera de la 320…"
               onChange={(e) => setTexto(e.target.value)} />

        <label className="check" htmlFor="sim-foto">
          <input id="sim-foto" type="checkbox" checked={conFoto}
                 onChange={(e) => setConFoto(e.target.checked)} />
          adjuntar foto del horómetro (activa OCR y validación cruzada)
        </label>

        <button className="btn" onClick={enviar} disabled={enviando}>
          {enviando ? 'procesando…' : 'Enviar por WhatsApp'}
        </button>
      </div>
    </div>
  )
}
