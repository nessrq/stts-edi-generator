# -*- coding: utf-8 -*-
"""Registro de actividad de la API EDI.

Cada operación (generar / generar + enviar) queda registrada en
edi_web/logs/logs.json con: fecha, tipo, archivo, ruta remota, resultado
y error si falló. Se conservan las últimas 200 entradas.
"""
import json
import os
from datetime import datetime

import app_paths

LOGS_DIR = os.path.join(app_paths.data_dir(), "logs")
LOGS_DIR = os.path.normpath(LOGS_DIR)
LOGS_FILE = os.path.join(LOGS_DIR, "logs.json")

MAX_LOGS = 200


def _load() -> list:
    if os.path.isfile(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            return []
    return []


def registrar(
    tipo: str,
    operacion: str,
    archivo_original=None,
    nombre=None,
    local=None,
    remoto=None,
    enviado=False,
    ok=True,
    detalle=None,
    error=None,
):
    os.makedirs(LOGS_DIR, exist_ok=True)
    logs = _load()
    logs.append({
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "tipo": tipo,
        "operacion": operacion,
        "archivo_original": archivo_original,
        "nombre": nombre,
        "local": local,
        "remoto": remoto,
        "enviado": enviado,
        "ok": ok,
        "detalle": detalle,
        "error": error,
    })
    logs = logs[-MAX_LOGS:]
    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def listar() -> list:
    logs = _load()
    logs.sort(key=lambda l: l["fecha"], reverse=True)
    return logs