# -*- coding: utf-8 -*-
"""Punto de entrada del .exe empaquetado con PyInstaller (modo windowed).

Arranca el backend FastAPI (que también sirve el frontend compilado) en segundo
plano y abre el navegador en http://127.0.0.1:8005. No muestra consola: el
usuario final solo hace doble clic y ve la app en el navegador.

Para detener la app: finalizar el proceso "EDI-Stellantis" desde el
Administrador de tareas.
"""
import os
import sys
import socket
import threading
import traceback
import webbrowser


def _preparar_rutas():
    # En el .exe, el código vive en sys._MEIPASS; lo agregamos al path para
    # que funcionen los imports relativos (api, edi, io_excel, transport...).
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    if base not in sys.path:
        sys.path.insert(0, base)


def _es_frozen():
    return getattr(sys, "frozen", False)


def _silenciar_salida():
    # En modo windowed (sin consola), sys.stdout/stderr son None. Los
    # redirigimos a devnull para que print/logging no rompan el arranque.
    if _es_frozen() and sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")


def _ruta_log():
    if _es_frozen():
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "error.log")


def _mostrar_error(mensaje):
    # Cuadro de diálogo (funciona sin consola).
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, mensaje, "EDI Stellantis", 0x10)
    except Exception:
        pass
    try:
        print(mensaje)
    except Exception:
        pass


def _puerto_en_uso(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def _abrir_navegador(host, port):
    try:
        webbrowser.open(f"http://{host}:{port}")
    except Exception:
        pass


def _esperar_y_abrir(host, port):
    # Abre el navegador cuando el servidor ya responde (evita "no se pudo
    # conectar" por arranque lento del .exe al importar pandas/numpy).
    import time
    for _ in range(30):
        if _puerto_en_uso(host, port):
            _abrir_navegador(host, port)
            return
        time.sleep(1)


def main():
    host = "127.0.0.1"
    port = 8005

    _silenciar_salida()

    try:
        # Si ya hay una instancia corriendo, solo abrir el navegador y salir.
        if _puerto_en_uso(host, port):
            _abrir_navegador(host, port)
            return

        _preparar_rutas()

        import uvicorn
        from api import app

        threading.Thread(
            target=_esperar_y_abrir, args=(host, port), daemon=True
        ).start()

        uvicorn.run(app, host=host, port=port, log_level="warning")
    except Exception:
        tb = traceback.format_exc()
        try:
            with open(_ruta_log(), "w", encoding="utf-8") as f:
                f.write(tb)
            _mostrar_error(
                "Ocurrió un error al iniciar la aplicación.\n\n"
                + tb
                + "\n\nSe escribió el detalle en: "
                + _ruta_log()
            )
        except Exception:
            _mostrar_error("Ocurrió un error al iniciar la aplicación:\n\n" + tb)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
