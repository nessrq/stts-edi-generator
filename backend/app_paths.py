# -*- coding: utf-8 -*-
"""Resolución de rutas de la aplicación, compatible con PyInstaller.

Cuando la app se ejecuta como .exe (PyInstaller), el código vive en un
directorio temporal de solo lectura (sys._MEIPASS). Las carpetas de DATOS del
usuario (salidas/, logs/, contadores) NO deben ir ahí: se crean junto al .exe
(o en %LOCALAPPDATA%) para que sean escribibles y persistan entre ejecuciones.

El frontend compilado (dist/) se empaqueta DENTRO del .exe como recurso, por
lo que sí se lee desde sys._MEIPASS (solo lectura).
"""
import os
import sys


def _frozen():
    """True si la app corre empaquetada con PyInstaller (.exe)."""
    return getattr(sys, "frozen", False)


def base_path():
    """Directorio base de la aplicación (donde vive el código o el .exe)."""
    if _frozen():
        # En .exe, sys.executable apunta al ejecutable real.
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def recurso_path(*parts):
    """Ruta a un recurso empaquetado dentro del .exe (solo lectura)."""
    if _frozen():
        return os.path.join(getattr(sys, "_MEIPASS", ""), *parts)
    # En desarrollo, los recursos están en la raíz del proyecto edi_web.
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", *parts)


def data_dir():
    """Carpeta escribible del usuario para datos (salidas, logs, contadores)."""
    if _frozen():
        # Junto al .exe: simple y portable para el usuario final.
        return os.path.join(base_path(), "datos")
    # En desarrollo, se mantiene la estructura actual del proyecto.
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def frontend_dist():
    """Ruta a los estáticos compilados del frontend (dist/)."""
    if _frozen():
        return recurso_path("frontend")
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
    )


def asegurar_data():
    """Crea (si no existe) la carpeta de datos del usuario."""
    carpeta = data_dir()
    os.makedirs(carpeta, exist_ok=True)
    return carpeta
