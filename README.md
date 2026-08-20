# EDI Stellantis — Versión Web (React + FastAPI)

Versión web de la app EDI. El backend Python (FastAPI) es autocontenido (contiene
toda la lógica EDI: builders, lectores Excel, SFTP) y el frontend React le envía
los Excel para generar los mensajes.

## Estructura

```
edi_web/
├── iniciar.bat          → arranca backend + frontend (doble clic)
├── salidas/             → .txt EDI generados (se guardan aquí)
├── backend/             → backend FastAPI autocontenido
│   ├── run_backend.py   → arranca el backend (sin PYTHONPATH)
│   ├── api.py           → endpoints de la API
│   ├── config.py        → HOLD_CODES, SEG_TERM, constantes SFTP
│   ├── edi/             → builders_x12, builders_fixed, icn, parser
│   ├── io_excel/        → lectores Excel
│   └── transport/       → cliente SFTP
└── frontend/            → app React (Vite)
    └── src/App.jsx      → interfaz de tarjetas por transacción
```

## Arquitectura

```
React (navegador) ──HTTP/JSON──► FastAPI (Python, edi_web/backend)
                                    ├── edi/builders_x12.py   (530, 550, 928)
                                    ├── edi/builders_fixed.py (2V, 3R)
                                    ├── io_excel/readers.py   (lee los Excel)
                                    └── transport/sftp_client.py
```

## Cómo correrla

Opción rápida: doble clic en `iniciar.bat`.

O manualmente (dos terminales):

1. Backend (puerto 8005), desde `edi_web/backend`:
```
cd C:\Users\Nestor David\Documents\proyecto_stellantis\edi_web\backend
C:\Users\Nestor David\AppData\Local\Programs\Python\Python312\python.exe run_backend.py
```
No hace falta PYTHONPATH: `run_backend.py` se agrega a sí mismo al path.
2. Frontend (puerto 5173):
```
cd C:\Users\Nestor David\Documents\proyecto_stellantis\edi_web\frontend
npm install   (solo la primera vez)
npm run dev
```
Abre http://localhost:5173

## Endpoints de la API

### Generar (solo texto)
| Método | Ruta | Sube | Devuelve |
|---|---|---|---|
| POST | /api/generar/530 | Excel 530 | EDI 530 |
| POST | /api/generar/550 | Excel 550 + tipo E/T | EDI 550 |
| POST | /api/generar/928 | Excel 928 | EDI 928 |
| POST | /api/generar/2v | Excel 2V | RA2VE |
| POST | /api/generar/3r | Excel 3R | RA3R |
| POST | /api/generar/510 | ASN 660 + vins | EDI 510 |
| POST | /api/generar/540 | ASN 660 + vins | EDI 540 |
| GET | /api/health | — | status ok |

### Generar + enviar por SFTP (con modo prueba)
Cada uno recibe `enviar` (true/false). Si `enviar=false` (o SFTP_ENABLED=false),
solo genera y reporta `enviado:false` con la ruta remota que se habría usado.

| Método | Ruta | Sube | Destino |
|---|---|---|---|
| POST | /api/generar-y-enviar/530 | Excel 530 + enviar | /Inbox/OBT/EDI |
| POST | /api/generar-y-enviar/550 | Excel 550 + tipo + enviar | /Inbox/OBT/EDI |
| POST | /api/generar-y-enviar/2v | Excel 2V + enviar | /Inbox/OBT/2V3R |
| POST | /api/generar-y-enviar/3r | Excel 3R + enviar | /Inbox/OBT/2V3R |

El check "Modo prueba" del frontend controla el campo `enviar`: activo = no sube,
desactivado = sube de verdad a Chrysler.

### Archivos generados (salidas)

Cada `.txt` generado se guarda en la carpeta `edi_web/salidas/` y queda disponible
para descargar desde el frontend (sección "Archivos generados").

| Método | Ruta | Qué hace |
|---|---|---|
| GET | /api/salidas | Lista los .txt generados (más recientes primero) |
| GET | /api/descargar/{nombre} | Descarga un .txt generado |

Nota: el archivo se guarda en `salidas/` incluso en modo prueba; el envío SFTP
es independiente del guardado local.

## Notas

- El backend usa los mismos nombres de columnas que los lectores `leer_excel_*`.
- El envío SFTP usa `upload_sftp_simple` (sin Tkinter, apto para la API web).
- 510/540 requieren un archivo ASN (660) y una lista de VINs separados por coma.
- 928 se genera pero su endpoint de envío aún no está expuesto (solo /api/generar/928).
