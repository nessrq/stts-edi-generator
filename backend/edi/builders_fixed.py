from datetime import datetime

from edi.icn import generate_icn


def build_isa(transaction_type, sender_id, receiver_id, icn):
    now = datetime.now()
    yymmdd = now.strftime("%y%m%d")
    hhmm = now.strftime("%H%M")

    isa = (
        "ISA*03*"
        f"{transaction_type:<10}*"
        "00*          *"
        "ZZ*"
        f"{sender_id:<15}*"
        "ZZ*"
        f"{receiver_id:<15}*"
        f"{yymmdd}*{hhmm}*"
        "U*00300*"
        f"{icn:09d}*0*P*<"
    )
    return isa


def build_iea(icn):
    return f"IEA*01*{icn:09d}"


def build_ra2ve_excel(registros):
    icn = generate_icn()
    now = datetime.now()

    yymmdd = now.strftime("%y%m%d")
    hhmm = now.strftime("%H%M")

    lines = []

    # ISA
    lines.append(
        "ISA*03*RA2VE     *00*          *ZZ*44202          *ZZ*VISTA          *"
        f"{yymmdd}*{hhmm}*U*00300*{icn:09d}*0*P*<"
    )

    for r in registros:
        if len(r["vin"]) != 17:
            print(f"VIN inválido ignorado: {r['vin']}")
            continue

        lines.append(
            build_2v(
                vin=r["vin"],
                ramp_code=r["ramp_code"],
                haulaway_scac=r["haulaway"][:4],
                action_date_mmddyy=str(r["action_date"]).zfill(6),
                bay_location=r["bay"],
                ship_to=r["ship_to"],
                action_time_hhmm=str(r["hora"]).zfill(4),
            )
        )

    lines.append(f"IEA*01*{icn:09d}")

    return "\n".join(lines)


def build_2v(
    vin,
    ramp_code,
    haulaway_scac,
    action_date_mmddyy,
    bay_location="E1",
    ship_to="RSTVY",
    action_time_hhmm=None,
    shipper_code="C",
    yard_scac="AHGP",
    yard_splc="922786006",
):
    if action_time_hhmm is None:
        action_time_hhmm = datetime.now().strftime("%H%M")

    linea = "".join([
        "2V",                                    # 1–2
        f"{ramp_code:<2}",                       # 3–4
        f"{action_date_mmddyy:>6}",              # 5–10
        f"{vin:<17}",                            # 11–27
        f"{bay_location:<5}",                    # 28–32
        f"{ship_to:<6}",                         # 33–38
        "Y",                                     # 39
        "  ",                                    # 40–41
        "  ",                                    # 42–43
        " " * 10,                                # 44–53
        " " * 6,                                 # 54–59
        "A",                                     # 60
        " " * 6,                                 # 61–66
        " " * 3,                                 # 67–69
        " " * 2,                                 # 70–71
        " " * 2,                                 # 72–73
        " ",                                     # 74
        f"{action_time_hhmm:>4}",                # 75–78
        " ",                                     # 79
        f"{shipper_code}",                       # 80
        " " * 5,                                 # 81–85
        f"{yard_scac:<4}",                       # 86–89
        f"{yard_splc:<9}",                       # 90–98
        f"{haulaway_scac:<4}",                   # 99–102
    ])

    # 🔥 VALIDACIÓN CRÍTICA
    if len(linea) != 102:
        raise ValueError(f"❌ ERROR 2V longitud {len(linea)} (debe ser 102)\n{repr(linea)}")

    return linea


# FORMATO 3R - SALIDA
def build_3r_excel(reg):
    # 🔥 FECHA: tomarla tal cual viene (string) y asegurar 6 chars
    fecha_mmddyy = str(reg["action_date"]).strip().zfill(6)

    # 🔥 HORA: tomar tal cual y asegurar 4 chars
    hora_24 = str(reg["hora"]).strip().zfill(4)

    # Convertir a formato 12h SIN perder ceros
    dt = datetime.strptime(hora_24, "%H%M")
    hora_12 = dt.strftime("%I%M")
    am_pm = "A" if dt.hour < 12 else "P"

    linea = (
        "3R" +
        f"{str(reg['ramp_code']).strip():<2}" +
        f"{fecha_mmddyy:>6}" +
        f"{str(reg['vin']).strip().upper():<17}" +
        f"{str(reg['bay']).strip():<5}" +
        f"{str(reg['ship_to']).strip():<6}" +
        " " +
        " " * 10 +
        f"{hora_12:>4}" +
        am_pm +
        " " * 6 +
        " " * 19 +
        "C" +
        "AHGP" +
        "922786006" +
        f"{str(reg['haulaway']).strip().upper()[:4]:<4}"
    )

    # VALIDACIÓN CRÍTICA
    if len(linea) != 97:
        raise ValueError(f"❌ ERROR 3R longitud {len(linea)}:\n{repr(linea)}")

    return linea


def build_ra3r_excel(registros):
    now = datetime.now()
    yymmdd = now.strftime("%y%m%d")
    hhmm = now.strftime("%H%M")

    icn = generate_icn()

    lines = []

    lines.append(
        f"ISA*03*RA3R      *00*          *ZZ*44202          *ZZ*VISTA          *"
        f"{yymmdd}*{hhmm}*U*00300*{icn:09d}*0*P*<"
    )

    valid_count = 0

    for r in registros:
        vin = str(r["vin"]).strip().upper()

        if len(vin) == 17 and vin.isalnum():
            lines.append(build_3r_excel(r))
            valid_count += 1
        else:
            print(f"VIN inválido ignorado: {vin}")

    lines.append(f"IEA*01*{icn:09d}")

    return "\n".join(lines)
