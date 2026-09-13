// Chip de procedencia: de donde salio cada valor y con que confianza.
// Responde la pregunta del jurado ("y si la IA se equivoca?") antes de que
// la hagan, y convierte la incertidumbre en una funcion del producto.
// Duenio: Majo
const ETIQUETA = {
  oem_cat: 'CAT',
  oem_komatsu: 'KOMATSU',
  oem_volvo: 'VOLVO',
  retrofit_j1939: 'J1939',
  field_ocr: 'OCR',
  field_whatsapp: 'OPERADOR',
  field_pwa: 'PWA',
}

const CLASE = {
  oem_cat: 'oem', oem_komatsu: 'oem', oem_volvo: 'oem',
  retrofit_j1939: 'retro', field_ocr: 'ocr',
  field_whatsapp: 'humano', field_pwa: 'humano',
}

export default function ProvenanceChip({ prov }) {
  if (!prov) return null
  const conf = prov.confidence ?? 1
  const baja = conf < 0.75
  return (
    <span className={`chip ${CLASE[prov.source] || 'humano'}${baja ? ' baja' : ''}`}
          title={prov.confirmed_by ? `confirmado por ${prov.confirmed_by}` : 'sin confirmar'}>
      {ETIQUETA[prov.source] || prov.source}
      {conf < 1 && <em>{conf.toFixed(2)}</em>}
      {prov.confirmed_by === 'audio+foto' && <b>✓</b>}
    </span>
  )
}
