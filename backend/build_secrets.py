# -*- coding: utf-8 -*-
"""Genera el módulo config_secretos.py con las credenciales SFTP OFUSCADAS.

Este script se ejecuta en el CI (GitHub Actions) ANTES de empaquetar con
PyInstaller. Lee las credenciales desde variables de entorno (que provienen
de GitHub Secrets) y escribe un módulo Python con los valores ofuscados
(vía XOR+base64) para que NO aparezcan en texto plano dentro del .exe.

Variables de entorno esperadas (normalmente GitHub Secrets):
    SFTP_PEM          -> contenido completo del archivo ACG_RSA.pem
    SFTP_PASSPHRASE   -> passphrase de la llave RSA
    SFTP_USERNAME     -> usuario del SFTP (opcional, default AUTOTECHMX)
    SFTP_HOST         -> host del SFTP (opcional, default emts.extra.chrysler.com)

El archivo generado (config_secretos.py) NO se sube al repositorio: está
en .gitignore y solo se crea durante el build.
"""
import os

from crypto_utils import ofuscar

# Rutas relativas a este script.
_AQUI = os.path.dirname(os.path.abspath(__file__))
_DESTINO = os.path.join(_AQUI, "config_secretos.py")


def _leer(variable, default=None):
    valor = os.environ.get(variable)
    if valor is None or valor.strip() == "":
        return default
    # Si viene de un secret multilínea se conserva tal cual.
    return valor


def main():
    pem = _leer("SFTP_PEM")
    passphrase = _leer("SFTP_PASSPHRASE")
    username = _leer("SFTP_USERNAME", "AUTOTECHMX")
    host = _leer("SFTP_HOST", "emts.extra.chrysler.com")

    faltan = []
    if not pem:
        faltan.append("SFTP_PEM")
    if not passphrase:
        faltan.append("SFTP_PASSPHRASE")

    if faltan:
        print("ERROR: faltan variables de entorno obligatorias:", ", ".join(faltan))
        print("Configúralas como GitHub Secrets en el repositorio.")
        raise SystemExit(1)

    # Ofusca cada valor. El .pem se guarda como una sola cadena base64.
    contenido = f"""# -*- coding: utf-8 -*-
# ARCHIVO GENERADO AUTOMÁTICAMENTE por build_secrets.py (no editar).
# No contiene credenciales en texto plano: están ofuscadas con XOR+base64.
# Este archivo NO se sube al repositorio y solo existe en el build.

from crypto_utils import desofuscar

SFTP_HOST = desofuscar({ofuscar(host)!r})
SFTP_USERNAME = desofuscar({ofuscar(username)!r})
SFTP_PASSPHRASE = desofuscar({ofuscar(passphrase)!r})
SFTP_PEM = desofuscar({ofuscar(pem)!r})
"""

    with open(_DESTINO, "w", encoding="utf-8") as f:
        f.write(contenido)

    print(f"OK: se generó {_DESTINO}")
    print("Credenciales incrustadas de forma OFUSCADA (XOR+base64).")
    # Verificación rápida (sin imprimir valores reales).
    import importlib.util
    spec = importlib.util.spec_from_file_location("config_secretos", _DESTINO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print(f"Verificación: host={mod.SFTP_HOST!r} user={mod.SFTP_USERNAME!r} "
          f"pem_len={len(mod.SFTP_PEM)} pass_len={len(mod.SFTP_PASSPHRASE)}")


if __name__ == "__main__":
    main()
