# -*- coding: utf-8 -*-
"""Arranca el backend de la API EDI.

Uso (desde CUALQUIER carpeta):
    python run_backend.py

No requiere PYTHONPATH: este script se agrega a sí mismo al sys.path.
"""
import os
import sys

# Asegura que este directorio esté en el path para que funcionen los imports
# relativos de api.py (from edi.*, io_excel.*, transport.*, config).
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import uvicorn

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8005, reload=False)
