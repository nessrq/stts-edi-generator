HOLD_CODES = {
    "AA": "E/T",
    "AF": "E",
    "BB": "E/T",
    "BV": "E/T",
    "CA": "E/T",
    "CB": "E/T",
    "CD": "E/T",
    "CE": "E/T",
    "CH": "E/T",
    "CT": "E/T",
    "DA": "E/T",
    "EB": "E/T",
    "FB": "E",
    "FF": "E/T",
    "FM": "E",
    "GC": "E",
    "GD": "E/T",
    "GE": "E",
    "GG": "E/T",
    "GK": "E/T",
    "GM": "E/T",
    "GP": "E/T",
    "GS": "E/T",
    "HH": "E/T",
    "H1": "E",
    "H2": "E",
    "H3": "E",
    "H4": "E",
    "H5": "E",
    "H6": "E",
    "IA": "E/T",
    "IN": "E",
    "MA": "E",
    "MB": "E/T",
    "ME": "E",
    "MS": "E",
    "NR": "E/T",
    "PB": "E/T",
    "PC": "E/T",
    "PD": "E/T",
    "PS": "E",
    "QA": "E",
    "RR": "E/T",
    "SA": "E",
    "SB": "E",
    "SC": "E",
    "SD": "E",
    "SH": "E/T",
    "SO": "E/T",
    "ST": "E/T",
    "TA": "E/T",
    "TH": "E/T",
    "UA": "E/T",
    "VG": "E/T",
    "VS": "E",
    "WA": "E/T",
    "WB": "E/T",
    "WC": "E/T",
    "Y5": "E/T",
    "BK": "E",
    "X0": "E",
    "X1": "E",
    "X2": "E",
    "X3": "E",
    "X4": "E",
    "X5": "E",
    "X6": "E",
    "X7": "E",
    "X8": "E",
    "X9": "E",
    "XA": "E",
    "XB": "E",
    "XC": "E",
    "XD": "E",
    "XE": "E",
    "XF": "E",
    "XG": "E",
    "XH": "E",
    "XI": "E",
    "XJ": "E",  
    "XK": "E",
    "XL": "E",
    "XM": "E",
    "XN": "E",
    "XO": "E",
    "XP": "E",
    "XW": "E",
}

SEG_TERM = "\x1c"

ingresos_vin = "1C4JJXP66MW737372"

# ============================================================
# Constantes de conexión SFTP
# ============================================================
# En el .exe empaquetado, las credenciales provienen de config_secretos.py
# (generado por build_secrets.py en CI con valores OFUSCADOS vía XOR+base64).
# Si ese módulo existe (build), se usa; si no (ejecución local desde el repo),
# se cae al flujo anterior: host/usuario hardcodeados, clave en ruta local y
# passphrase desde el Credential Manager de Windows.

SFTP_PORT = 22

try:
    from config_secretos import (
        SFTP_HOST as _SFTP_HOST_SECRETO,
        SFTP_USERNAME as _SFTP_USERNAME_SECRETO,
        SFTP_PASSPHRASE as _SFTP_PASSPHRASE_SECRETO,
        SFTP_PEM as _SFTP_PEM_SECRETO,
    )
    # Modo .exe: las credenciales vienen ofuscadas del módulo generado.
    SFTP_HOST = _SFTP_HOST_SECRETO
    SFTP_USERNAME = _SFTP_USERNAME_SECRETO
    SFTP_PASSPHRASE = _SFTP_PASSPHRASE_SECRETO
    SFTP_PEM = _SFTP_PEM_SECRETO
    SFTP_KEY_PATH = None  # la clave viene embebida en SFTP_PEM
    CREDENTIAL_SERVICE = None
    CREDENTIAL_USER = None
    _SECRETOS_EMBEBIDOS = True
except ImportError:
    # Modo desarrollo: credenciales locales.
    SFTP_HOST = "emts.extra.chrysler.com"
    SFTP_USERNAME = "AUTOTECHMX"
    SFTP_KEY_PATH = r"C:\Users\Nestor David\Documents\edi_web\ACG_RSA.pem"
    SFTP_PASSPHRASE = None
    SFTP_PEM = None
    CREDENTIAL_SERVICE = "SFTP_KEY_PASSPHRASE"
    CREDENTIAL_USER = "AUTOTECHMX"
    _SECRETOS_EMBEBIDOS = False

# Interruptor maestro de envío SFTP.
# True  = se puede enviar a Chrysler (si el modo prueba de la GUI está desmarcado).
# False = ningún envío se hace, aunque la GUI esté en modo real.
SFTP_ENABLED = True
