# -*- coding: utf-8 -*-
"""API FastAPI que expone la lógica EDI de Stellantis al frontend React.

Incluye:
- Generación de transacciones (530, 550, 928, 2V, 3R) desde Excel.
- Generación de 510/540 desde un ASN (660) + VINs seleccionados.
- Envío SFTP con modo prueba (no fuerza conexión, permite simulacro).
- Guardado local de los .txt generados en la carpeta "salidas" y su descarga.

Ejecutar desde edi_web/backend/ (o usar run_backend.py).
"""
import os
import tempfile
from datetime import datetime

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import SEG_TERM, SFTP_ENABLED
from edi.parser import parse_asn
from edi.builders_x12 import (
    build_edi530_excel,
    build_edi550_excel,
    build_edi928,
    build_edi510,
    build_edi540,
)
from edi.builders_fixed import build_ra2ve_excel, build_ra3r_excel
from io_excel.readers import (
    leer_excel_530,
    leer_excel_550,
    leer_excel_2v,
    leer_excel_3r,
    leer_excel_928,
)
from transport.sftp_client import upload_sftp_simple
from logs import registrar, listar as listar_logs
import app_paths

app = FastAPI(title="Stellantis EDI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carpeta donde se guardan los .txt generados (carpeta de datos del usuario).
SALIDAS_DIR = os.path.join(app_paths.data_dir(), "salidas")
SALIDAS_DIR = os.path.normpath(SALIDAS_DIR)
os.makedirs(SALIDAS_DIR, exist_ok=True)


def _guardar_temporal(upload: UploadFile) -> str:
    sufijo = os.path.splitext(upload.filename or "")[1] or ".xlsx"
    fd, ruta = tempfile.mkstemp(suffix=sufijo)
    with os.fdopen(fd, "wb") as f:
        f.write(upload.file.read())
    return ruta


def _guardar_txt(
    tipo: str,
    nombre_base: str,
    contenido: str,
    dir_remoto: str,
    enviar: bool,
    archivo_original: str = None,
):
    """Guarda el EDI en la carpeta 'salidas' y, si 'enviar' está activo, lo sube.

    Registra el resultado en el log. Devuelve un dict con 'nombre' (archivo
    local), 'remoto' (ruta remota), 'enviado' (bool) y, si el envío falló,
    'error' con el detalle. El archivo local NO se borra: queda en 'salidas'.
    """
    nombre = f"{nombre_base}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    ruta = os.path.join(SALIDAS_DIR, nombre)

    remoto = f"{dir_remoto}/{nombre}"
    enviado = False
    error = None
    detalle = None

    try:
        with open(ruta, "w", encoding="ascii") as f:
            f.write(contenido)

        if enviar and SFTP_ENABLED:
            try:
                detalle = upload_sftp_simple(ruta, remoto)
                enviado = True
            except Exception as e:
                error = str(e)
    except Exception as e:
        error = str(e)

    registrar(
        tipo=tipo,
        operacion="generar_enviar",
        archivo_original=archivo_original,
        nombre=nombre,
        local=ruta,
        remoto=remoto,
        enviado=enviado,
        ok=(error is None),
        detalle=detalle,
        error=error,
    )

    return {
        "nombre": nombre,
        "archivo": ruta,
        "remoto": remoto,
        "enviado": enviado,
        "error": error,
        "detalle": detalle,
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/salidas")
def listar_salidas():
    """Lista los .txt generados en la carpeta 'salidas' (más recientes primero)."""
    archivos = []
    if os.path.isdir(SALIDAS_DIR):
        for nombre in os.listdir(SALIDAS_DIR):
            ruta = os.path.join(SALIDAS_DIR, nombre)
            if os.path.isfile(ruta) and nombre.endswith(".txt"):
                archivos.append({
                    "nombre": nombre,
                    "fecha": datetime.fromtimestamp(os.path.getmtime(ruta)).isoformat(),
                    "tamano": os.path.getsize(ruta),
                })
    archivos.sort(key=lambda a: a["fecha"], reverse=True)
    return {"salidas": archivos}


@app.get("/api/descargar/{nombre}")
def descargar(nombre: str):
    """Descarga un .txt generado de la carpeta 'salidas'."""
    ruta = os.path.normpath(os.path.join(SALIDAS_DIR, nombre))
    if os.path.dirname(ruta) != os.path.normpath(SALIDAS_DIR) or not os.path.isfile(ruta):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(ruta, filename=nombre, media_type="text/plain")


# ====================== GENERAR (solo texto) ======================

@app.post("/api/generar/530")
async def generar_530(archivo: UploadFile = File(...)):
    ruta = _guardar_temporal(archivo)
    try:
        registros = leer_excel_530(ruta)
        edi = build_edi530_excel(registros)
        return {"edi": edi, "segmentos": len(edi.split(SEG_TERM)) - 1}
    finally:
        os.unlink(ruta)


@app.post("/api/generar/550")
async def generar_550(archivo: UploadFile = File(...), tipo: str = Form("E")):
    ruta = _guardar_temporal(archivo)
    try:
        registros = leer_excel_550(ruta)
        edi = build_edi550_excel(registros, tipo)
        return {"edi": edi, "segmentos": len(edi.split(SEG_TERM)) - 1}
    finally:
        os.unlink(ruta)


@app.post("/api/generar/928")
async def generar_928(archivo: UploadFile = File(...)):
    ruta = _guardar_temporal(archivo)
    try:
        registros = leer_excel_928(ruta)
        edi = build_edi928(registros)
        return {"edi": edi, "segmentos": len(edi.split(SEG_TERM)) - 1}
    finally:
        os.unlink(ruta)


@app.post("/api/generar/2v")
async def generar_2v(archivo: UploadFile = File(...)):
    ruta = _guardar_temporal(archivo)
    try:
        registros = leer_excel_2v(ruta)
        edi = build_ra2ve_excel(registros)
        return {"edi": edi, "lineas": len(edi.splitlines())}
    finally:
        os.unlink(ruta)


@app.post("/api/generar/3r")
async def generar_3r(archivo: UploadFile = File(...)):
    ruta = _guardar_temporal(archivo)
    try:
        registros = leer_excel_3r(ruta)
        edi = build_ra3r_excel(registros)
        return {"edi": edi, "lineas": len(edi.splitlines())}
    finally:
        os.unlink(ruta)


# ====================== GENERAR + ENVIAR (con modo prueba) ======================

@app.post("/api/generar-y-enviar/530")
async def generar_enviar_530(
    archivo: UploadFile = File(...),
    enviar: bool = Form(False),
):
    ruta = _guardar_temporal(archivo)
    try:
        registros = leer_excel_530(ruta)
        edi = build_edi530_excel(registros)
        res = _guardar_txt("530", "EDI_530", edi, "/Inbox/OBT/EDI", enviar, archivo.filename)
        res["edi"] = edi
        res["segmentos"] = len(edi.split(SEG_TERM)) - 1
        return res
    finally:
        os.unlink(ruta)


@app.post("/api/generar-y-enviar/550")
async def generar_enviar_550(
    archivo: UploadFile = File(...),
    tipo: str = Form("E"),
    enviar: bool = Form(False),
):
    ruta = _guardar_temporal(archivo)
    try:
        registros = leer_excel_550(ruta)
        edi = build_edi550_excel(registros, tipo)
        res = _guardar_txt("550", "EDI_550", edi, "/Inbox/OBT/EDI", enviar, archivo.filename)
        res["edi"] = edi
        res["segmentos"] = len(edi.split(SEG_TERM)) - 1
        return res
    finally:
        os.unlink(ruta)


@app.post("/api/generar-y-enviar/2v")
async def generar_enviar_2v(
    archivo: UploadFile = File(...),
    enviar: bool = Form(False),
):
    ruta = _guardar_temporal(archivo)
    try:
        registros = leer_excel_2v(ruta)
        edi = build_ra2ve_excel(registros)
        res = _guardar_txt("2v", "EDI_RA2VE", edi, "/Inbox/OBT/2V3R", enviar, archivo.filename)
        res["edi"] = edi
        res["lineas"] = len(edi.splitlines())
        return res
    finally:
        os.unlink(ruta)


@app.post("/api/generar-y-enviar/3r")
async def generar_enviar_3r(
    archivo: UploadFile = File(...),
    enviar: bool = Form(False),
):
    ruta = _guardar_temporal(archivo)
    try:
        registros = leer_excel_3r(ruta)
        edi = build_ra3r_excel(registros)
        res = _guardar_txt("3r", "RA3R", edi, "/Inbox/OBT/2V3R", enviar, archivo.filename)
        res["edi"] = edi
        res["lineas"] = len(edi.splitlines())
        return res
    finally:
        os.unlink(ruta)


# ====================== 510 / 540 desde ASN ======================

def _registros_a_vins(registros: list) -> list:
    """Convierte una lista de VINs (strings) a segmentos VI* para los builders."""
    return [f"VI*{vin}****" for vin in registros]


@app.post("/api/generar/510")
async def generar_510(
    archivo: UploadFile = File(...),
    vins: str = Form(""),
):
    """Recibe un ASN (660) y una lista de VINs separados por coma."""
    ruta = _guardar_temporal(archivo)
    try:
        data = parse_asn(ruta)
        lista_vins = [v.strip() for v in vins.split(",") if v.strip()]
        vi_vins = _registros_a_vins(lista_vins)
        edi = build_edi510(data, vi_vins, "DCXSAA", "EDIVTV")
        registrar(
            tipo="510",
            operacion="generar",
            archivo_original=archivo.filename,
            ok=True,
            detalle={"vins": len(vi_vins)},
        )
        return {"edi": edi, "vins": len(vi_vins)}
    except Exception as e:
        registrar(
            tipo="510",
            operacion="generar",
            archivo_original=archivo.filename,
            ok=False,
            error=str(e),
        )
        raise
    finally:
        os.unlink(ruta)


@app.post("/api/generar/540")
async def generar_540(
    archivo: UploadFile = File(...),
    vins: str = Form(""),
):
    ruta = _guardar_temporal(archivo)
    try:
        data = parse_asn(ruta)
        lista_vins = [v.strip() for v in vins.split(",") if v.strip()]
        vi_vins = _registros_a_vins(lista_vins)
        edi = build_edi540(data, vi_vins, "DCXSAA", "EDIVTV")
        registrar(
            tipo="540",
            operacion="generar",
            archivo_original=archivo.filename,
            ok=True,
            detalle={"vins": len(vi_vins)},
        )
        return {"edi": edi, "vins": len(vi_vins)}
    except Exception as e:
        registrar(
            tipo="540",
            operacion="generar",
            archivo_original=archivo.filename,
            ok=False,
            error=str(e),
        )
        raise
    finally:
        os.unlink(ruta)


@app.get("/api/logs")
def logs():
    """Lista la actividad registrada (más recientes primero)."""
    return {"logs": listar_logs()}


# ====================== Frontend estático (SPA) ======================
# En el .exe, el frontend compilado (dist/) se sirve desde el mismo puerto,
# de modo que el usuario final usa una sola URL (http://127.0.0.1:8005).

_DIST = app_paths.frontend_dist()


def _servir_index():
    indice = os.path.join(_DIST, "index.html")
    if os.path.isfile(indice):
        return HTMLResponse(open(indice, encoding="utf-8").read())
    return HTMLResponse("<h1>Frontend no encontrado</h1>", status_code=404)


if os.path.isdir(_DIST):
    # Sirve los estáticos (js, css, assets) y deja el index.html para el SPA.
    _assets_dir = os.path.join(_DIST, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")


@app.get("/", include_in_schema=False)
def raiz():
    return _servir_index()


@app.get("/favicon.svg", include_in_schema=False)
def _favicon():
    _ruta = os.path.join(_DIST, "favicon.svg")
    if os.path.isfile(_ruta):
        return FileResponse(_ruta, media_type="image/svg+xml")
    return _servir_index()


@app.get("/icons.svg", include_in_schema=False)
def _icons():
    _ruta = os.path.join(_DIST, "icons.svg")
    if os.path.isfile(_ruta):
        return FileResponse(_ruta, media_type="image/svg+xml")
    return _servir_index()


# Catch-all: cualquier ruta que no sea /api cae al SPA (react-router).
@app.get("/{ruta:path}", include_in_schema=False)
def _spa_fallback(ruta: str):
    if ruta.startswith("api/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    return _servir_index()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8005)
