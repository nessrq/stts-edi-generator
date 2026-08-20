import io
import os

import paramiko
import keyring

# Trae las constantes desde config para que no esten hardcodeadas  
 
from config import (
    SFTP_HOST,
    SFTP_PORT,
    SFTP_USERNAME,
    SFTP_KEY_PATH,
    SFTP_PASSPHRASE,
    SFTP_PEM,
    CREDENTIAL_SERVICE,
    CREDENTIAL_USER,
)


def _obtener_clave_y_passphrase():
    """Devuelve (clave_rsa, passphrase).

    - Modo .exe (credenciales embebidas): la clave RSA se construye desde la
      cadena PEM incrustada (SFTP_PEM) usando la passphrase embebida (SFTP_PASSPHRASE).
    - Modo desarrollo: la clave se lee del archivo .pem local y la passphrase
      se obtiene del Credential Manager de Windows.
    """
    if SFTP_PEM and SFTP_PASSPHRASE:
        key = paramiko.RSAKey.from_private_key(
            io.StringIO(SFTP_PEM),
            password=SFTP_PASSPHRASE,
        )
        return key, SFTP_PASSPHRASE

    # Flujo local: archivo .pem + passphrase del Credential Manager.
    if not SFTP_KEY_PATH or not os.path.isfile(SFTP_KEY_PATH):
        raise Exception(
            f"No se encontró la llave SFTP en: {SFTP_KEY_PATH}. "
            "Usa un .exe empaquetado con credenciales o configura la ruta."
        )
    passphrase = keyring.get_password(CREDENTIAL_SERVICE, CREDENTIAL_USER)
    if not passphrase:
        raise Exception("No se encontró el passphrase en Windows Credential Manager")
    key = paramiko.RSAKey.from_private_key_file(
        SFTP_KEY_PATH,
        password=passphrase,
    )
    return key, passphrase


def upload_sftp_simple(file_path, remote_path):
    """Sube un archivo por SFTP sin diálogos de GUI (apto para la API web).

    Después de subir verifica contra el servidor que el archivo quedó escrito
    completo (mismo tamaño que el local) y devuelve un dict:
        {"remoto": ruta final, "tamano": bytes verificados en el remoto}
    Si la verificación falla, lanza una excepción.
    """
    host = SFTP_HOST
    port = SFTP_PORT
    username = SFTP_USERNAME

    # Obtiene la clave RSA y el passphrase según el modo (embebido o local).
    key, _passphrase = _obtener_clave_y_passphrase()

    transport = None
    sftp = None

    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=username, pkey=key)

        # abre el canal SFTP
        sftp = paramiko.SFTPClient.from_transport(transport)

        # sube el archivo temporal para evitar que este se suba a medias
        tmp_path = remote_path + ".tmp"

        # Swap del temporal x el final
        sftp.put(file_path, tmp_path)
        sftp.rename(tmp_path, remote_path)

        # Verificación REAL contra el buzón: el archivo existe en el remoto
        # y su tamaño coincide con el archivo local.
        stat = sftp.stat(remote_path)
        tamano_local = os.path.getsize(file_path)

        if stat.st_size != tamano_local:
            raise Exception(
                f"Verificación SFTP: el remoto quedó con {stat.st_size} bytes "
                f"y el local tiene {tamano_local} bytes"
            )

        return {"remoto": remote_path, "tamano": stat.st_size}

    except Exception as e:
        print("Error SFTP:", str(e))
        raise
    finally:
        if sftp is not None:
            try:
                sftp.close()
            except Exception:
                pass
        if transport is not None:
            try:
                transport.close()
            except Exception:
                pass
