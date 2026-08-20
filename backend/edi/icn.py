from datetime import datetime

# Contador secuencial por día para el número de control de intercambio.
# El manual OBT exige: "THE NUMBER STARTS AT 1, RUNS TO 99999 AND THEN
# RESETS TO 1" — un contador secuencial que se reinicia cada día.
# Se persiste en un archivo temporal para sobrevivir a reinicios del proceso
# (evita colisiones si se generan dos archivos en el mismo segundo o tras
# reiniciar el backend el mismo día).

import os
import tempfile

_STATE_FILE = os.path.join(tempfile.gettempdir(), "edi_icn_counter.txt")

_last_day = None
_last_counter = 0


def _read_state():
    """Devuelve (dia_yyyymmdd, contador) persistidos, o (None, 0)."""
    try:
        with open(_STATE_FILE, "r", encoding="ascii") as f:
            linea = f.read().strip()
        dia, contador = linea.split(":", 1)
        return int(dia), int(contador)
    except Exception:
        return None, 0


def _write_state(dia, contador):
    try:
        with open(_STATE_FILE, "w", encoding="ascii") as f:
            f.write(f"{dia}:{contador}")
    except Exception:
        pass


def generate_icn():
    """Devuelve el número de control de intercambio (contador por día).

    Máx. 5 dígitos (1-99999), se reinicia al cambiar de día. No puede ser 0.
    """
    global _last_day, _last_counter

    hoy = int(datetime.now().strftime("%Y%m%d"))

    # Cargar estado persistido la primera vez.
    if _last_day is None:
        _last_day, _last_counter = _read_state()

    # Si cambió el día (o no hay estado), reinicia el contador.
    if _last_day != hoy:
        _last_day = hoy
        _last_counter = 0

    # Avanza y da la vuelta en 99999.
    _last_counter += 1
    if _last_counter > 99999:
        _last_counter = 1

    _write_state(_last_day, _last_counter)
    return _last_counter


# ============================================================
# Contador de Invoice Number (odómetro)
# ============================================================
# Genera invoices únicos e infinitos sin caracteres especiales, usando un
# odómetro: el dígito de la derecha cambia primero; cuando se agota, el
# de la izquierda avanza y el de la derecha vuelve a empezar.
#
# El primer dígito (más significativo) arranca en "R"; los dígitos siguientes
# arrancan en "A". Cada dígito recorre A-Z luego 0-9 (36 símbolos).
#
# Secuencia:
#   R, S, T, ..., Z, 0, ..., 9,
#   RA, RB, ..., RZ, R0, ..., R9,
#   SA, SB, ..., SZ, S0, ..., S9,
#   TA, ...
#
# El contador es permanente (NO se reinicia por día), así los invoices nunca
# se repiten a lo largo del tiempo.

_INVOICE_STATE_FILE = os.path.join(tempfile.gettempdir(), "edi_invoice_counter.txt")
_invoice_counter = None

# Alfabeto del dígito: A-Z luego 0-9 (36 símbolos), en orden de avance.
_INV_ALFABETO = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
# Índice de "R" (arranque del primer dígito).
_PRIMERO_START = 17


def _read_invoice_state():
    try:
        with open(_INVOICE_STATE_FILE, "r", encoding="ascii") as f:
            return int(f.read().strip())
    except Exception:
        return 0


def _write_invoice_state(valor):
    try:
        with open(_INVOICE_STATE_FILE, "w", encoding="ascii") as f:
            f.write(str(valor))
    except Exception:
        pass


def reset_invoice_counter(valor=0):
    """Avanza el contador de invoices SOLO si el valor es mayor que el actual.

    El odómetro de invoices es monotónico: nunca retrocede, garantizando que
    cada invoice sea único en el tiempo (Chrysler rechaza invoices repetidos).
    """
    global _invoice_counter
    if _invoice_counter is None:
        _invoice_counter = _read_invoice_state()
    if valor > _invoice_counter:
        _invoice_counter = valor
        _write_invoice_state(valor)


def _contador_a_sufijo(contador):
    """Convierte un contador (>=1) al sufijo en base 36.

    Todos los dígitos usan el alfabeto A-Z luego 0-9. El contador interno
    arranca en el índice de "R" (17), de modo que el primer sufijo es "R",
    después "S", ..., "Z", "0", ..., "9", luego "BA", "BB", ...
    Esto garantiza unicidad infinita y sin caracteres especiales.
    """
    if contador <= 0:
        contador = 1
    base = len(_INV_ALFABETO)  # 36
    n = _PRIMERO_START + contador - 1  # arranca en "R" (índice 17)
    chars = []
    while n > 0:
        n, rem = divmod(n, base)
        chars.append(_INV_ALFABETO[rem])
    # chars quedó en orden invertido (unidades primero); lo invertimos.
    return "".join(reversed(chars)) if chars else _INV_ALFABETO[0]


def next_invoice_suffix():
    """Devuelve el siguiente sufijo de invoice y avanza el contador.

    El contador es permanente y NO se reinicia por día, garantizando
    unicidad infinita.
    """
    global _invoice_counter
    if _invoice_counter is None:
        _invoice_counter = _read_invoice_state()
    _invoice_counter += 1
    _write_invoice_state(_invoice_counter)
    return _contador_a_sufijo(_invoice_counter)


# ============================================================
# Secuencial del Transaction Set Control Number (ST02/SE02)
# ============================================================
# El manual exige que el ST02 sea "GS06 en las primeras posiciones
# concatenado a un secuencial incrementado por cada transacción". Como cada
# archivo 530 es un grupo funcional con una sola transacción, el secuencial
# debe avanzar entre archivos del mismo día para que el ST02 sea único
# (de lo contrario todos quedarían igual a "000000001" con ICNs bajos).
# Se reinicia por día, al igual que el ICN.

_ST_STATE_FILE = os.path.join(tempfile.gettempdir(), "edi_st_secuencial.txt")
_st_day = None
_st_counter = 0


def _read_st_state():
    try:
        with open(_ST_STATE_FILE, "r", encoding="ascii") as f:
            dia, contador = f.read().strip().split(":", 1)
            return int(dia), int(contador)
    except Exception:
        return None, 0


def _write_st_state(dia, contador):
    try:
        with open(_ST_STATE_FILE, "w", encoding="ascii") as f:
            f.write(f"{dia}:{contador}")
    except Exception:
        pass


def next_st_secuencial():
    """Devuelve el siguiente número secuencial (0-padded a 4 dígitos) para
    el ST02. Avanza por cada llamada y se reinicia por día."""
    global _st_day, _st_counter
    hoy = int(datetime.now().strftime("%Y%m%d"))
    if _st_day is None:
        _st_day, _st_counter = _read_st_state()
    if _st_day != hoy:
        _st_day = hoy
        _st_counter = 0
    _st_counter += 1
    _write_st_state(_st_day, _st_counter)
    return f"{_st_counter:04d}"
