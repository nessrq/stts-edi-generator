# -*- coding: utf-8 -*-
"""Utilidades de ofuscación para las credenciales SFTP.

El objetivo NO es "seguridad criptográfica real" (eso no es posible en un .exe
distribuido, quien lo tenga puede extraer la clave y la passphrase). El objetivo
es evitar que las credenciales aparezcan en TEXTO PLANO legible al inspeccionar
el binario con herramientas simples (p.ej. `strings`).

Método: XOR de cada byte con una clave derivada de una semilla fija, y luego
codificación base64. Es reversible y determinista, pero las credenciales no
saltan a la vista directamente.
"""
import base64

# Semilla fija derivada del nombre del proyecto (no contiene datos sensibles).
_SEED = b"edi-stellantis-obfuscation-2026"
# Se extiende la semilla para igualar la longitud del texto a ofuscar.
_XOR_KEY = _SEED * 32


def ofuscar(texto: str) -> str:
    """Ofusca un string y devuelve su representación base64 (str)."""
    data = texto.encode("utf-8")
    key = (_XOR_KEY[: len(data)])
    xored = bytes(b ^ k for b, k in zip(data, key))
    return base64.b64encode(xored).decode("ascii")


def desofuscar(codificado: str) -> str:
    """Invierte ofuscar(): recibe base64 y devuelve el string original."""
    xored = base64.b64decode(codificado.encode("ascii"))
    key = (_XOR_KEY[: len(xored)])
    data = bytes(b ^ k for b, k in zip(xored, key))
    return data.decode("utf-8")
