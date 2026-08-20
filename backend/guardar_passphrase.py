# -*- coding: utf-8 -*-
"""Guarda el passphrase de la llave SFTP en el Credential Manager de Windows.

Uso:
    python guardar_passphrase.py

Te pedirá el passphrase SIN mostrarlo en pantalla y lo guarda en el
Credential Manager con el servicio y usuario que espera la app.
"""
import getpass
import keyring

SERVICE = "SFTP_KEY_PASSPHRASE"
USER = "AUTOTECHMX"

actual = keyring.get_password(SERVICE, USER)
if actual:
    print(f"Ya existe una credencial guardada para {SERVICE}\\{USER}.")
    respuesta = input("¿Reemplazarla? (s/N): ").strip().lower()
    if respuesta != "s":
        print("Sin cambios.")
        raise SystemExit(0)

passphrase = getpass.getpass("Passphrase de la llave RSA (no se muestra): ")

if not passphrase:
    print("El passphrase no puede estar vacío.")
    raise SystemExit(1)

keyring.set_password(SERVICE, USER, passphrase)

# Verificar
verif = keyring.get_password(SERVICE, USER)
if verif == passphrase:
    print("Passphrase guardado correctamente en el Credential Manager.")
else:
    print("ERROR: la verificación falló.")
