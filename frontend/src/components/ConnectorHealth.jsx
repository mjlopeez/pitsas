// Salud de conectores + contrato canonico.
// Es el unico lugar donde la INTEGRACION se ve. El documento original muestra
// los resultados de integrar pero nunca el acto de integrar.
// Duenio: Majo
export default function ConnectorHealth({ conectores, contrato }) {
  return (
    <div className="conectores">
      <h4>Conectores · {contrato?.eventos_normalizados ?? 0} eventos normalizados</h4>
      <ul>
        {conectores.map((c) => (
          <li key={c.source} className={c.estado}>
            <span className="punto" />
            <div>
              <b>{c.nombre}</b>
              <em>{c.protocolo}</em>
            </div>
            <div className="cuenta">
              <span className="ok">{c.aceptados}</span>
              {c.rechazados > 0 && <span className="rej">{c.rechazados} rechazados</span>}
            </div>
          </li>
        ))}
      </ul>

      {contrato?.precedencia && (
        <>
          <h4>Precedencia por campo · quién es dueño del dato</h4>
          <table className="precedencia">
            <tbody>
              {Object.entries(contrato.precedencia).map(([campo, orden]) => (
                <tr key={campo}>
                  <th>{campo}</th>
                  <td>{orden.slice(0, 4).map((s) => s.replace('oem_', '').replace('field_', '')).join(' → ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="nota">
            Cuando una fuente de menor autoridad contradice a una mayor fuera de
            tolerancia, el Hub no elige en silencio: abre un ticket de conciliación.
          </p>
        </>
      )}
    </div>
  )
}
