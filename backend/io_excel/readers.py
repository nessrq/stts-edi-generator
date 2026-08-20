import pandas as pd

from config import HOLD_CODES


def _txt(valor):
    """Convierte un valor de Excel a texto; los NaN/vacíos devuelven ''."""
    if valor is None:
        return ""
    if isinstance(valor, float) and pd.isna(valor):
        return ""
    texto = str(valor).strip()
    if texto.lower() in ("nan", "none", "nat"):
        return ""
    return texto


def leer_excel_530(path):
    df = pd.read_excel(path)

    registros = []

    for _, row in df.iterrows():
        registros.append({
            "vin": str(row["VIN"]).strip().upper(),
            "scac": _txt(row.get("SCAC *", "")),
            "splc_origin": _txt(row.get("SPLC ORIGIN *", "")),
            "route_origin": _txt(row.get("ROUTE ORIGIN", "")),
            "route_dest": _txt(row.get("ROUTE DESTINATION", "")),
            "service_code": _txt(row.get("SERVICE CODE", "")),
            "invoice_number": _txt(row.get("INVOICE NUMBER", "")),
            "pickup_date": _txt(row.get("PICKUP DATE", "")),
            "pickup_time": _txt(row.get("PICKUP TIME", "")),
            "storage_start_date": _txt(row.get("STORAGE START DATE", "")),
            "storage_end_date": _txt(row.get("STORAGE END DATE", "")),
            "voyage_number": _txt(row.get("VOYAGE NUMBER", "")),
            "vessel_name": _txt(row.get("VESSEL NAME", "")),
            "bill_of_lading": _txt(row.get("BILL OF LADING", "")),
        })

    return registros


def leer_excel_550(path):
    df = pd.read_excel(path)

    registros = []

    hold_codes = set()

    for idx, (_, row) in enumerate(df.iterrows(), start=2):
        vin = str(row["VIN NUMBER"]).strip().upper()
        hold_code = str(row["HOLD CODE"]).strip().upper()
        route_origin = str(row["ROUTE ORIGIN"]).strip().upper()
        route_dest = str(row["ROUTE DESTINATION"]).strip().upper()

        # Validar que exista
        if hold_code not in HOLD_CODES:
            raise ValueError(
                f"HOLD CODE inválido '{hold_code}' en la fila {idx}."
            )

        hold_codes.add(hold_code)

        registros.append({
            "vin": vin,
            "hold_code": hold_code,
            "route_origin": route_origin,
            "route_dest": route_dest,
        })

    # El archivo solo puede contener un HOLD CODE
    if len(hold_codes) > 1:
        raise ValueError(
            "El archivo contiene varios HOLD CODE diferentes. "
            "Solo se permite un HOLD CODE por archivo."
        )

    return registros


# 2V gate in/entrada y 3R gateout/salida
def _leer_fijo(path, col_fecha, col_hora):
    """Lee una plantilla de ancho fijo (2V/3R).

    - La FECHA y la HORA se leen como texto (dtype=str) para conservar los
      ceros a la izquierda, que son parte del formato requerido por Chrysler
      (p.ej. "081526", "1100").
    - El RAMP CODE, en cambio, se genera SIN el cero a la izquierda (p.ej.
      "01" -> "1"), replicando el comportamiento del programa antiguo. Chrysler
      espera el ramp code así ("1 " en el ancho fijo de 2 chars), no con cero.
    """
    df = pd.read_excel(path, dtype=str)
    df.columns = df.columns.str.strip()
    registros = []

    for _, row in df.iterrows():
        ramp = str(row["Ramp Code (2 caracteres)"]).strip()
        # Convierte a int y de vuelta a str para eliminar el cero a la izquierda.
        # Si no es numérico (p.ej. "A1"), se conserva tal cual.
        try:
            ramp = str(int(ramp))
        except ValueError:
            pass
        registros.append({
            "ramp_code": ramp,
            "action_date": str(row[col_fecha]).strip(),
            "vin": str(row["VIN (17 caracteres)"]).strip().upper(),
            "bay": str(row["Bay Location (5 caracteres)"]).strip(),
            "ship_to": str(row["Ship-To Dealer (6 caracteres)"]).strip(),
            "hora": str(row[col_hora]).strip(),
            "haulaway": str(row["Haulaway SCAC (4 caracteres)"]).strip().upper()
        })

    return registros


def leer_excel_2v(path):
    return _leer_fijo(
        path,
        col_fecha="Fecha de recepcion (6 Caracteres  MMDDAA)",
        col_hora="Hora de recepcion (4 caracteres HHMM)",
    )


def leer_excel_3r(path):
    return _leer_fijo(
        path,
        col_fecha="Fecha de salida (6 Caracteres  MMDDAA)",
        col_hora="Hora de recepcion (4 caracteres HHMM)",
    )


def leer_excel_928(path):
    df = pd.read_excel(path)

    registros = []

    for _, row in df.iterrows():
        registros.append({
            "vin": str(row["VIN #"]).strip().upper(),
            "carrier": str(row["Carrier"]).strip().upper(),
            "carrier_ref": str(row["Carrier Ref"]).strip(),
            "damage_area": str(row["Area"]).strip().zfill(2),
            "damage_type": str(row["Type"]).strip().zfill(2),
            "severity": str(row["Severity"]).strip(),
            "damage_desc": str(row["Damage Description"]).strip(),
            "damage_class": str(row["Damage Classification"]).strip(),
            "inspection_date": row["Damage Record Date"],
            "site": str(row["Site"]).strip(),
            "comments": str(row["Comments"]).strip(),
            "vessel": str(row["Vessel"]).strip(),
        })

    return registros


def formatear_fecha(fecha):
    return pd.to_datetime(fecha).strftime("%m%d%y")


def formatear_hora(hora):
    return pd.to_datetime(hora).strftime("%H%M")
