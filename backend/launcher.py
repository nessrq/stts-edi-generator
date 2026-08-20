# -*- coding: utf-8 -*-
"""Punto de entrada del .exe empaquetado con PyInstaller.

Arranca el backend FastAPI (que también sirve el frontend compilado) y abre
automáticamente el navegador en http://127.0.0.1:8005. Así el usuario final
solo hace doble clic y ve la app, sin configurar nada.
"""
import os
import sys
import threading
import traceback
import webbrowser


def _preparar_rutas():
    # En el .exe, el código vive en sys._MEIPASS; lo agregamos al path para
    # que funcionen los imports relativos (api, edi, io_excel, transport...).
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    if base not in sys.path:
        sys.path.insert(0, base)


def _abrir_navegador(host, port):
    url = f"http://{host}:{port}"
    try:
        webbrowser.open(url)
    except Exception:
        pass


def _ruta_log():
    # Junto al ejecutable (escribible) para capturar errores de arranque.
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "error.log")


def main():
    try:
        _preparar_rutas()

        import uvicorn
        from api import app

        host = "127.0.0.1"
        port = 8005

        # Abre el navegador unos instantes después de arrancar el servidor.
        threading.Timer(1.2, _abrir_navegador, args=(host, port)).start()

        uvicorn.run(app, host=host, port=port, log_level="warning")
    except Exception:
        tb = traceback.format_exc()
        print(tb)
        try:
            with open(_ruta_log(), "w", encoding="utf-8") as f:
                f.write(tb)
            print(f"\nSe escribió el detalle del error en: {_ruta_log()}")
        except Exception:
            pass
        input("\nOcurrió un error. Presiona Enter para cerrar...")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
