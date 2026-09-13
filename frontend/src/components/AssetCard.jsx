// Ficha del activo con procedencia por campo. Duenio: Majo
import ProvenanceChip from './ProvenanceChip.jsx'

export default function AssetCard({ asset, onDespachar }) {
  if (!asset) return <div className="ficha vacia">Selecciona un activo en el mapa.</div>
  const p = asset.provenance || {}
  const pct = asset.pct_servicio ?? 0

  return (
    <div className="ficha">
      <header>
        <div>
          <h3>{asset.asset_identifier}</h3>
          <p className="sub">{asset.make} {asset.model} · {asset.kind}</p>
        </div>
        <span className={`estado ${asset.state}`}>{asset.state?.replace('_', ' ')}</span>
      </header>

      <dl>
        <div>
          <dt>Horómetro</dt>
          <dd>{(asset.operating_hours ?? 0).toFixed(1)} h <ProvenanceChip prov={p.operating_hours} /></dd>
        </div>
        <div>
          <dt>Combustible acumulado</dt>
          <dd>{(asset.cumulative_fuel ?? 0).toFixed(0)} gal <ProvenanceChip prov={p.cumulative_fuel} /></dd>
        </div>
        <div>
          <dt>Motor</dt>
          <dd>{asset.engine_state || '—'} <ProvenanceChip prov={p.engine_state} /></dd>
        </div>
        <div>
          <dt>Obra asignada</dt>
          <dd>{asset.assigned_project || '—'} <ProvenanceChip prov={p.assigned_project} /></dd>
        </div>
        <div>
          <dt>Telemetría</dt>
          <dd>{asset.telemetry === 'oem' ? 'nativa de fábrica' : 'retrofit CAN J1939'}</dd>
        </div>
      </dl>

      <div className="servicio">
        <div className="barra"><span style={{ width: `${Math.min(100, pct)}%` }} className={pct >= 96 ? 'urgente' : ''} /></div>
        <p>{asset.horas_desde_servicio} h de {asset.service_every_h} h desde el último servicio</p>
      </div>

      {asset.alertas?.length > 0 && (
        <ul className="alertas-ficha">
          {asset.alertas.slice(0, 5).map((a) => (
            <li key={a.id} className={a.severity}>
              <b>{a.title}</b>
              {a.detail && <span>{a.detail}</span>}
            </li>
          ))}
        </ul>
      )}

      <button className="btn" onClick={() => onDespachar(asset.asset_identifier)}>
        Solicitar traslado
      </button>
    </div>
  )
}
