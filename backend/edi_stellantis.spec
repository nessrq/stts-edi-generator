# -*- mode: python ; coding: utf-8 -*-
# Spec de PyInstaller para empaquetar la app EDI Stellantis en un solo .exe.
#
# Requisitos previos al build:
#   1. Frontend compilado en  ../frontend/dist  (npm run build)
#   2. backend/config_secretos.py generado por build_secrets.py (credenciales
#      ofuscadas desde las variables de entorno SFTP_PEM/SFTP_PASSPHRASE).
#
# El frontend se sirve desde el mismo proceso (api.py monta los estáticos),
# por lo que el .exe es una sola aplicación web en http://127.0.0.1:8005.

import os

from PyInstaller.utils.hooks import collect_all

# SPECPATH es la ruta del directorio del .spec (lo provee PyInstaller).
backend_dir = os.path.abspath(SPECPATH)
frontend_dist = os.path.normpath(
    os.path.join(backend_dir, "..", "frontend", "dist")
)

# hidden imports de librerías que PyInstaller no detecta automáticamente.
hiddenimports = [
    "keyring.backends.Windows",
    "keyring.backends.SecretService",
    "keyring.backends.macOS",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
]

datas = []
binaries = []

# numpy 2.x divide sus extensiones C en numpy._core; PyInstaller no las detecta
# todas por sí solo (p.ej. numpy._core._exceptions). collect_all recoge todos
# los submódulos, binarios y datos de estas librerías para evitar el error
# "No module named 'numpy._core._exceptions'" al arrancar el .exe.
for _pkg in ("numpy", "pandas", "openpyxl"):
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    hiddenimports += _h

if os.path.isdir(frontend_dist):
    # El frontend compilado se incluye como carpeta "frontend" dentro del bundle.
    datas.append((frontend_dist, "frontend"))

a = Analysis(
    [os.path.join(backend_dir, "launcher.py")],
    pathex=[backend_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="EDI-Stellantis",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # ventana de consola para ver errores de arranque
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
