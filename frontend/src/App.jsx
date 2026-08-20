import { useState, useEffect } from 'react'
import './App.css'

const API = '/api'

// Un solo acento en toda la página (Color Consistency Lock): azul profundo.
// Las tarjetas ya no compiten en color; el código EDI es el dato y el azul es la acción.
const ACCENT = '#0f4c81'
const NEUTRAL = '#1f2937'

const TARJETAS = [
  { id: '530', titulo: 'Servicio', codigo: '530', plantilla: 'Archivo excel 530',
    desc: 'Lavado, cera, inspección y almacenamiento', dir: '/Inbox/OBT/EDI' },
  { id: '550', titulo: 'Hold', codigo: '550', plantilla: 'Archivo excel 550',
    desc: 'Retención: E para activar, T para liberar', tipoHold: true, dir: '/Inbox/OBT/EDI' },
  { id: '2v', titulo: 'Entrada', codigo: '2V', plantilla: 'Archivo excel 2V',
    desc: 'El vehículo llegó al patio', dir: '/Inbox/OBT/2V3R' },
  { id: '3r', titulo: 'Salida', codigo: '3R', plantilla: 'Archivo excel 3R',
    desc: 'El vehículo salió del patio', dir: '/Inbox/OBT/2V3R' },
  { id: '928', titulo: 'Daños', codigo: '928', plantilla: 'Archivo excel 928',
    desc: 'Reporte de daños del vehículo', dir: '/Inbox/EDI' },
]

function App() {
  const [resultado, setResultado] = useState('')
  const [info, setInfo] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [modoPrueba, setModoPrueba] = useState(true)
  const [salidas, setSalidas] = useState([])
  const [logs, setLogs] = useState([])

  async function cargarSalidas() {
    try {
      const res = await fetch(`${API}/salidas`)
      if (res.ok) {
        const data = await res.json()
        setSalidas(data.salidas || [])
      }
    } catch (e) { console.error(e) }
  }

  async function cargarLogs() {
    try {
      const res = await fetch(`${API}/logs`)
      if (res.ok) {
        const data = await res.json()
        setLogs(data.logs || [])
      }
    } catch (e) { console.error(e) }
  }

  async function buscarLogPrevio(nombreArchivo) {
    try {
      const res = await fetch(`${API}/logs`)
      if (!res.ok) return null
      const data = await res.json()
      const nombre = nombreArchivo.trim().toLowerCase()
      const previos = (data.logs || []).filter(
        (l) => l.archivo_original && l.archivo_original.trim().toLowerCase() === nombre
      )
      return previos[0] || null
    } catch (e) {
      console.error(e)
      return null
    }
  }

  function mensajePrevio(l) {
    const fecha = new Date(l.fecha).toLocaleString()
    if (l.error) return `el ${fecha} y FALLÓ: ${l.error}`
    if (l.enviado) return `el ${fecha} y fue ENVIADO al buzón de Chrysler.`
    return `el ${fecha} (se generó, sin envío).`
  }

  async function validarArchivo(archivo) {
    const previo = await buscarLogPrevio(archivo.name)
    if (!previo) return true
    const continuar = window.confirm(
      `ATENCIÓN: el archivo "${archivo.name}" ya fue procesado ${mensajePrevio(previo)}\n\n` +
      '¿Deseas generarlo/enviarlo de todos modos?'
    )
    return continuar
  }

  async function generar(tarjeta, archivo, tipo) {
    if (!archivo) { alert('Selecciona un archivo Excel primero.'); return }
    if (!(await validarArchivo(archivo))) return
    setCargando(true); setResultado(''); setInfo(null)
    try {
      const form = new FormData()
      form.append('archivo', archivo)
      if (tipo) form.append('tipo', tipo)
      form.append('enviar', String(!modoPrueba))
      const res = await fetch(`${API}/generar-y-enviar/${tarjeta.id}`, { method: 'POST', body: form })
      if (!res.ok) throw new Error((await res.text()) || `Error ${res.status}`)
      const data = await res.json()
      setResultado(data.edi)
      if (data.enviado) {
        const tamano = data.detalle?.tamano
        setInfo({
          tipo: 'ok',
          texto: `Confirmado en el buzón de Chrysler: ${data.remoto} (${tamano ?? '?'} bytes verificados)`,
        })
      } else if (data.error) {
        setInfo({
          tipo: 'error',
          texto: `El archivo NO fue alcanzado por el buzón de Chrysler: ${data.error}`,
        })
      } else {
        setInfo({
          tipo: 'warn',
          texto: `Modo prueba: no se envió. Se habría subido a ${data.remoto}`,
        })
      }
      cargarSalidas()
    } catch (e) {
      setResultado(`Error: ${e.message}`)
      setInfo({ tipo: 'error', texto: `El archivo NO fue alcanzado por el buzón de Chrysler: ${e.message}` })
      console.error(e)
    } finally { setCargando(false); cargarLogs() }
  }

  async function generarAsn(tipo, archivo, vins) {
    if (!archivo) { alert('Selecciona el archivo ASN (660) primero.'); return }
    if (!vins.trim()) { alert('Ingresa al menos un VIN.'); return }
    if (!(await validarArchivo(archivo))) return
    setCargando(true); setResultado(''); setInfo(null)
    try {
      const form = new FormData()
      form.append('archivo', archivo)
      form.append('vins', vins)
      const res = await fetch(`${API}/generar/${tipo}`, { method: 'POST', body: form })
      if (!res.ok) throw new Error((await res.text()) || `Error ${res.status}`)
      const data = await res.json()
      setResultado(data.edi)
      setInfo({ tipo: 'warn', texto: `${data.vins} VIN(s) procesados (generación local, sin envío)` })
      cargarSalidas()
    } catch (e) {
      setResultado(`Error: ${e.message}`)
      setInfo({ tipo: 'error', texto: `Error al generar: ${e.message}` })
      console.error(e)
    } finally { setCargando(false); cargarLogs() }
  }

  useEffect(() => { cargarSalidas(); cargarLogs() }, [])

  return (
    <div className="app">
      <header className="cabecera">
        <p className="eyebrow">Stellantis</p>
        <h1>Generador EDI</h1>
        <p className="sub">
          Elige una transacción, selecciona su respectivo Excel y genera el mensaje EDI.
        </p>
      </header>

      <section className="modo">
        <label className="modo-label">
          <input type="checkbox" checked={modoPrueba} onChange={(e) => setModoPrueba(e.target.checked)} />
          <strong>Modo prueba</strong>
        </label>
        <span className="modo-estado" data-activo={modoPrueba}>
          {modoPrueba
            ? 'Activo: no se sube nada al sistema'
            : 'Desactivado: se enviará por SFTP'}
        </span>
      </section>

      <section className="bloque">
        <h2 className="bloque-titulo">ASN (660)</h2>
        <ASNTarjeta generar={generarAsn} deshabilitado={cargando} />
      </section>

      <main className="tarjetas">
        {TARJETAS.map((t) => (
          <Tarjeta key={t.id} tarjeta={t} generar={generar} deshabilitado={cargando} />
        ))}
      </main>

      <section className="bloque resultado">
        <h2 className="bloque-titulo">Vista previa del mensaje EDI</h2>
        {info && <p className="info" data-tipo={info.tipo}>{info.texto}</p>}
        <textarea
          readOnly
          value={cargando ? 'Generando...' : resultado || 'Aquí verás el EDI generado.'}
          spellCheck={false}
        />
      </section>

      <section className="bloque">
        <h2 className="bloque-titulo">Archivos generados</h2>
        <p className="bloque-sub">Haz clic para descargar.</p>
        {salidas.length === 0 ? (
          <p className="vacias">Aún no hay archivos generados.</p>
        ) : (
          <ul className="lista-salidas">
            {salidas.map((s) => (
              <li key={s.nombre}>
                <a className="enlace-descarga" href={`${API}/descargar/${encodeURIComponent(s.nombre)}`} download>
                  {s.nombre}
                </a>
                <span className="meta-salida">{new Date(s.fecha).toLocaleString()} · {s.tamano} bytes</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="bloque">
        <div className="bloque-cab">
          <h2 className="bloque-titulo">Registros de actividad</h2>
          <button className="boton ghost boton-chico" onClick={cargarLogs} disabled={cargando}>
            Actualizar
          </button>
        </div>
        <p className="bloque-sub">Registro de cada generación: cuál archivo, a qué hora y si llegó al buzón o qué falló.</p>
        {logs.length === 0 ? (
          <p className="vacias">Aún no hay registros.</p>
        ) : (
          <ul className="lista-logs">
            {logs.map((l, i) => (
              <li key={`${l.fecha}-${i}`} data-estado={l.error ? 'error' : l.enviado ? 'ok' : 'warn'}>
                <div className="log-fila">
                  <span className="log-fecha">{new Date(l.fecha).toLocaleString()}</span>
                  <span className="log-tipo">{l.tipo}</span>
                  <span className="log-archivo" title={l.nombre || l.archivo_original || ''}>
                    {l.nombre || l.archivo_original || '—'}
                  </span>
                  <span className="log-estado">
                    {l.error ? 'Falló' : l.enviado ? 'Enviado' : 'Generado (sin envío)'}
                  </span>
                </div>
                {l.remoto && <div className="log-detalle">→ {l.remoto}</div>}
                {l.error && <div className="log-error">✕ {l.error}</div>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

function Tarjeta({ tarjeta, generar, deshabilitado }) {
  const [archivo, setArchivo] = useState(null)
  const [tipo, setTipo] = useState('E')

  return (
    <div className="tarjeta">
      <div className="tarjeta-cab">
        <span className="codigo">{tarjeta.codigo}</span>
        <h3>{tarjeta.titulo}</h3>
      </div>
      <p className="sub">{tarjeta.desc}</p>

      <label className="campo">
        <span>Archivo excel</span>
        <input
          type="file"
          accept=".xlsx,.xls"
          onChange={(e) => setArchivo(e.target.files[0] || null)}
          disabled={deshabilitado}
        />
        {archivo && <span className="archivo-elegido">{archivo.name}</span>}
      </label>

      {tarjeta.tipoHold && (
        <label className="campo">
          <span>Tipo de hold</span>
          <select value={tipo} onChange={(e) => setTipo(e.target.value)}>
            <option value="E">E: activar retención</option>
            <option value="T">T: liberar retención</option>
          </select>
        </label>
      )}

      <button
        className="boton"
        onClick={() => generar(tarjeta, archivo, tarjeta.tipoHold ? tipo : null)}
        disabled={deshabilitado}
      >
        Generar {tarjeta.titulo}
      </button>
      <p className="nota">{tarjeta.plantilla} → {tarjeta.dir}</p>
    </div>
  )
}

function ASNTarjeta({ generar, deshabilitado }) {
  const [archivo, setArchivo] = useState(null)
  const [vins, setVins] = useState('')

  return (
    <div className="asn-card">
      <div className="asn-grid">
        <label className="campo">
          <span>Archivo ASN (660)</span>
          <input type="file" accept=".txt,.edi" onChange={(e) => setArchivo(e.target.files[0] || null)} disabled={deshabilitado} />
          {archivo && <span className="archivo-elegido">{archivo.name}</span>}
        </label>
        <label className="campo">
          <span>VINs (separados por coma)</span>
          <input
            type="text"
            placeholder="1C4JJXP66MW737372, 1C4JJXP66MW737373"
            value={vins}
            onChange={(e) => setVins(e.target.value)}
            disabled={deshabilitado}
          />
        </label>
      </div>
      <div className="asn-botones">
        <button className="boton ghost" onClick={() => generar('510', archivo, vins)} disabled={deshabilitado}>
          Generar 510 Dealer
        </button>
        <button className="boton ghost" onClick={() => generar('540', archivo, vins)} disabled={deshabilitado}>
          Generar 540 Shuttle
        </button>
      </div>
    </div>
  )
}

export default App
