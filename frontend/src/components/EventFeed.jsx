// Feed en vivo. Es lo que le dice al jurado que esto es un sistema corriendo
// y no una captura de pantalla. Duenio: Majo
const FUENTE = {
  oem_cat: 'CAT', oem_komatsu: 'KOMATSU', oem_volvo: 'VOLVO',
  retrofit_j1939: 'J1939', field_whatsapp: 'WHATSAPP', field_pwa: 'PWA',
}

export default function EventFeed({ eventos, alertas, onSeleccionar }) {
  return (
    <div className="feed">
      <div className="feed-col">
        <h4>Eventos normalizados</h4>
        <ul>
          {eventos.length === 0 && <li className="vacio">Esperando telemetría…</li>}
          {eventos.map((e, i) => (
            <li key={`${e.id}-${i}`} onClick={() => onSeleccionar(e.asset_identifier)}>
              <span className={`fuente ${e.source}`}>{FUENTE[e.source] || e.source}</span>
              <b>{e.asset_identifier}</b>
              {e.note && <em>{e.note.slice(0, 70)}…</em>}
            </li>
          ))}
        </ul>
      </div>
      <div className="feed-col">
        <h4>Alertas</h4>
        <ul>
          {alertas.length === 0 && <li className="vacio">Sin alertas abiertas.</li>}
          {alertas.map((a, i) => (
            <li key={`${a.id}-${i}`} onClick={() => onSeleccionar(a.asset_identifier)}>
              <span className={`sev ${a.severity}`}>{a.kind}</span>
              <b>{a.asset_identifier}</b>
              <em>{a.title}</em>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
