from datetime import datetime

from config import SEG_TERM
from edi.icn import generate_icn, next_invoice_suffix, next_st_secuencial


def build_edi510(data, selected_vins, doctype, translation_map):
    gs02, gs03, gs04, gs05, gs06, pid, VON, DIN = \
        data["GS02"], data["GS03"], data["GS04"], data["GS05"], data["GS06"], data["PID"], data["VON"], data["DIN"]
    an03, an04 = \
        data["AN03"], data["AN04"]
    if not gs04 or not gs05:
        now = datetime.now()
        gs04, gs05 = now.strftime("%y%m%d"), now.strftime("%H%M")
    fecha, hora = gs04, gs05
    fechaac = datetime.now().strftime("%y%m%d")
    horaac = datetime.now().strftime("%H%M")
    fechast = gs04  # fecha de almacenamiento esta se utilizará en VI cuando estemos en prod
    horast = gs05  # hora de almacenamiento esta se utilizará en VI cuando estemos en prod
    if not pid:
        pid = datetime.now().strftime("%H%M%S%f")[-7:]
    vt = "44202"
    icn = generate_icn()
    gs06 = f"{icn:09d}"

    # ----- header -----
    ics = f"ICS*+ANSI1.1  VT{vt:<15}VT{gs02:<15}{fechaac}{horaac}{icn:09d}{SEG_TERM}"
    gs = f"GS*VI*AHGP*{gs02}*{fechaac}*{horaac}*{gs06}*T*1{SEG_TERM}"
    stnum5 = gs06[:5]
    stnum = f"{stnum5}0001"
    st = f"ST*510*{stnum}{SEG_TERM}"

    # ----- BV1 -----
    qty = len(selected_vins)
    bv1 = f"BV1*AHGP*{an04}*{qty}{SEG_TERM}"

    # ----- VIs + P1 + P2 -----
    def normalize_vi(vi):
        parts = vi.split("*")

        # Asegura al menos 6 campos
        while len(parts) <= 5:
            parts.append("")

        # VI04 (VON) no se usa en 510, se vacía.
        parts[4] = ""
        # VI05 (Dealer ID) es MANDATORY en 510: se toma del 5º campo (index 5)
        # que viene en la VI generada desde el ASN. Si está vacío se deja vacío
        # (el dato real debe venir del flujo).
        return "*".join(parts[:6])

    # ----- P1 -----
    p1 = f"P1**{fechaac}*A*{horaac}{SEG_TERM}"

    # ----- P2 -----
    p2 = f"P2**{fechaac}*A*{horaac}*INVOICE000{SEG_TERM}"

    # Por cada VIN se emiten 3 segmentos: VI, P1 y P2.
    vi_lines = []
    for v in selected_vins:
        vi_lines.append(normalize_vi(v) + SEG_TERM + p1 + p2)

    # ----- SE -----
    # Estructura: ST + BV1 + N×(VI+P1+P2) + SE = 3*N + 3 segmentos.
    seg_count = 3 * len(selected_vins) + 3
    se = f"SE*{seg_count}*{stnum}{SEG_TERM}"

    # ----- footer -----
    ge = f"GE*1*{gs06}{SEG_TERM}"
    ice = f"ICE*000001*{icn:09d}{SEG_TERM}"

    return "".join([ics, gs, st, bv1] + vi_lines + [se, ge, ice])


def build_edi530(data, selected_vins, doctype, translation_map):
    gs02, gs03, gs04, gs05, gs06, pid = \
        data["GS02"], data["GS03"], data["GS04"], data["GS05"], data["GS06"], data["PID"]
    an03, an05 = \
        data["AN03"], data["AN05"]
    if not gs04 or not gs05:
        now = datetime.now()
        gs04, gs05 = now.strftime("%y%m%d"), now.strftime("%H%M")
    fecha, hora = gs04, gs05
    fechaac = datetime.now().strftime("%y%m%d")
    horaac = datetime.now().strftime("%H%M")
    fechast = gs04  # fecha de almacenamiento esta se utilizará en VI 
    horast = gs05  # hora de almacenamiento esta se utilizará en VI 
    if not pid:
        pid = datetime.now().strftime("%H%M%S%f")[-7:]
    vt = "44202"
    icn = generate_icn()
    gs06 = f"{icn:09d}"

    # ----- header -----
    ics = f"ICS*+ANSI1.1  VT{vt:<15}VT{gs02:<15}{fechaac}{horaac}{icn:09d}{SEG_TERM}"
    gs = f"GS*VI*AHGP*{gs02}*{fechaac}*{horaac}*{gs06}*T*1{SEG_TERM}"
    stnum5 = gs06[:5]
    stnum = f"{stnum5}0001"
    st = f"ST*530*{stnum}{SEG_TERM}"

    # ----- BV3 -----
    qty = len(selected_vins)
    bv3 = f"BV3*AHGP*922786006*{an05}*INVOICE000*{qty}*{fechaac}*{horaac}{SEG_TERM}"
    #
    # ----- VIs -----
    vi_lines = [v + SEG_TERM for v in selected_vins]

    # ----- SE -----
    # Estructura: ST + BV3 + N×VI + SE = N + 3 segmentos.
    seg_count = len(selected_vins) + 3
    se = f"SE*{seg_count}*{stnum}{SEG_TERM}"

    # ----- footer -----
    ge = f"GE*1*{gs06}{SEG_TERM}"
    ice = f"ICE*000001*{icn:09d}{SEG_TERM}"

    return "".join([ics, gs, st, bv3] + vi_lines + [se, ge, ice])


def build_edi530_excel(registros):
    now = datetime.now()

    fechaac = now.strftime("%y%m%d")
    horaac = now.strftime("%H%M")

    icn = generate_icn()

    gs06 = f"{icn:09d}"

    vt = "44202"

    # ST02 = GS06 en las primeras posiciones + un secuencial que avanza por
    # archivo (se reinicia por día). Así es único aunque el GS06 sea bajo
    # (con ICNs de pocos dígitos, GS06[:5] sería "00000" para todos).
    stnum5 = gs06[:5]
    stnum = f"{stnum5}{next_st_secuencial()}"

    qty = len(registros)

    lines = []

    # =========================================================
    # ICS
    # =========================================================
    lines.append(
        f"ICS*+ANSI1.1  VT{vt:<15}VTVISTA          "
        f"{fechaac}{horaac}{icn:09d}{SEG_TERM}"
    )

    # =========================================================
    # GS
    # =========================================================
    lines.append(
        f"GS*VI*AHGP*VISTA*{fechaac}*{horaac}*{gs06}*T*1{SEG_TERM}"
    )

    # =========================================================
    # ST
    # =========================================================
    lines.append(
        f"ST*530*{stnum}{SEG_TERM}"
    )

    # =========================================================
    # BV3 + VI
    # =========================================================
    # Estructura que confirma Chrysler: UN SOLO BV3 por lote (BV305 = cantidad
    # de VI que le siguen) seguido de hasta 100 VI. Este es el formato que
    # ellos requieren para que los VINs se reflejen.
    valid_vins = 0
    vi_lines = []

    for r in registros:
        vin = str(r["vin"]).strip().upper()

        if len(vin) != 17:
            print(f"VIN inválido ignorado: {vin}")
            continue

        route_origin = str(r["route_origin"]).strip().upper()
        route_dest = str(r["route_dest"]).strip().upper()
        storage_start_date = str(r["storage_start_date"]).strip().upper()
        storage_end_date = str(r["storage_end_date"]).strip().upper()

        # Relleno a la izquierda de fechas/horas numéricas (NZ 6/6 y 4/4).
        storage_start_date = storage_start_date.zfill(6) if storage_start_date else ""
        storage_end_date = storage_end_date.zfill(6) if storage_end_date else ""

        # Según el manual OBT (530), el VI: VI01 VIN, VI02 ruta origen,
        # VI03 ruta destino, VI04 VON, VI05 Dealer ID, VI06 storage start,
        # VI07 storage end. VI04/VI05 no se usan en servicios y van vacíos.
        vi_lines.append(
            f"VI*{vin}*{route_origin}*{route_dest}***{storage_start_date}*{storage_end_date}{SEG_TERM}"
        )

        valid_vins += 1

    # ----- Un solo BV3 (datos del primer VIN válido) -----
    if valid_vins > 0:
        # El manual limita a 100 VI por BV3/transacción. Se advierte si se
        # supera el límite (cada archivo debería venir segmentado en lotes).
        if valid_vins > 100:
            print(
                f"ADVERTENCIA: {valid_vins} VINs superan el límite de 100 VI "
                "por transacción 530. Partir el archivo en lotes de 100."
            )

        r0 = None
        for r in registros:
            if len(str(r["vin"]).strip().upper()) == 17:
                r0 = r
                break

        service_code = str(r0["service_code"]).strip().upper()
        invoice_number = str(r0["invoice_number"]).strip().upper()
        pickup_date = str(r0["pickup_date"]).strip().upper()
        pickup_time = str(r0["pickup_time"]).strip().upper()

        # Invoice único por lote. El manual exige que BV304 (invoice) sea
        # único por transaction set, sin caracteres especiales (el guion bajo
        # no se acepta). Se genera con un odómetro base-36 infinito:
        # AHGPABRR -> AHGPABRS -> ... -> AHGPABRZ -> AHGPABSA0 -> ...
        # El contador es permanente (nunca se reinicia), así que los invoices
        # nunca se repiten a lo largo del tiempo.
        base = (invoice_number or "INV").rstrip()
        if not base:
            base = "INV"
        # El prefijo del invoice: se quita el último carácter del base y se le
        # anexa el sufijo base-36 generado.
        prefijo = base[:-1]
        sufijo = next_invoice_suffix()
        # Límite de 16 chars del campo invoice (manual): se trunca si excede.
        invoice_number = (prefijo + sufijo)[:16]

        ocean_bill_of_lading = str(r0.get("bill_of_lading", "")).strip().upper()
        voyage_number = str(r0.get("voyage_number", "")).strip().upper()
        vessel_name = str(r0.get("vessel_name", "")).strip().upper()

        pickup_date = pickup_date.zfill(6) if pickup_date else ""
        pickup_time = pickup_time.zfill(4) if pickup_time else ""

        scac = str(r0.get("scac", "")).strip().upper() or "AHGP"
        splc_origin = str(r0.get("splc_origin", "")).strip() or "922786006"

        # BV3: SCAC*SPLC origen*Special Service Code*Invoice*Qty*Date*Time
        bv3 = (
            f"BV3*{scac}*{splc_origin}*{service_code}*{invoice_number}*"
            f"{valid_vins}*{pickup_date}*{pickup_time}"
        )

        # Campos CL obligatorios (BV309 Ocean B/L, BV310 Voyage, BV311 Vessel).
        if service_code == "CL":
            bv3 += f"*{ocean_bill_of_lading}*{voyage_number}*{vessel_name}"
        else:
            bv3 += "***"

        lines.append(bv3 + SEG_TERM)
        lines.extend(vi_lines)

    # =========================================================
    # SE
    # =========================================================
    # Estructura: ST + 1 BV3 + N VI + SE = N + 3 segmentos.
    segment_count = valid_vins + 3

    lines.append(
        f"SE*{segment_count}*{stnum}{SEG_TERM}"
    )

    # =========================================================
    # GE
    # =========================================================
    lines.append(
        f"GE*1*{gs06}{SEG_TERM}"
    )

    # =========================================================
    # ICE
    # =========================================================
    lines.append(
        f"ICE*000001*{icn:09d}{SEG_TERM}"
    )

    return "".join(lines)


def build_edi540(data, selected_vins, doctype, translation_map):
    gs02, gs03, gs04, gs05, gs06, pid = \
        data["GS02"], data["GS03"], data["GS04"], data["GS05"], data["GS06"], data["PID"]
    an03, an04, an05 = \
        data["AN03"], data["AN04"], data["AN05"]
    if not gs04 or not gs05:
        now = datetime.now()
        gs04, gs05 = now.strftime("%y%m%d"), now.strftime("%H%M")
    fecha, hora = gs04, gs05
    fechaac = datetime.now().strftime("%y%m%d")
    horaac = datetime.now().strftime("%H%M")
    fechast = gs04  # fecha de almacenamiento esta se utilizará en VI cuando estemos en prod
    horast = gs05  # hora de almacenamiento esta se utilizará en VI cuando estemos en prod
    if not pid:
        pid = datetime.now().strftime("%H%M%S%f")[-7:]
    vt = "44202"
    icn = generate_icn()
    gs06 = f"{icn:09d}"

    # ----- header -----
    ics = f"ICS*+ANSI1.1  VT{vt:<15}VT{gs02:<15}{fechaac}{horaac}{icn:09d}{SEG_TERM}"
    gs = f"GS*VI*AHGP*{gs02}*{fechaac}*{horaac}*{gs06}*T*1{SEG_TERM}"
    stnum5 = gs06[:5]
    stnum = f"{stnum5}0001"
    st = f"ST*540*{stnum}{SEG_TERM}"

    # ----- BV4 -----
    qty = len(selected_vins)
    bv4 = f"BV4*A*AHGP*922786006*{an04}*{qty}*{fechaac}*{horaac}{SEG_TERM}"
    p1 = f"P1**{fechast}*A*{horast}*{SEG_TERM}"  # fecha de cuando se recibio el vehículo
    #
    # ----- VIs -----
    vi_lines = [v + SEG_TERM for v in selected_vins]
    # ----- SE -----
    # Estructura: ST + BV4 + P1 + N×VI + SE = N + 4 segmentos.
    seg_count = len(selected_vins) + 4
    se = f"SE*{seg_count}*{stnum}{SEG_TERM}"

    # ----- footer -----
    ge = f"GE*1*{gs06}{SEG_TERM}"
    ice = f"ICE*000001*{icn:09d}{SEG_TERM}"

    return "".join([ics, gs, st, bv4, p1] + vi_lines + [se, ge, ice])

# Registros recibe una lista de diccionarios (vin, hold_code, route origin, route_dest)
def build_edi550_excel(registros, seg_et):

    # guarda fecha y hora actuales en variable now
    now = datetime.now()

    # timestamps en formato año/mes/dia
    fechaac = now.strftime("%y%m%d")

    # hora actual en hora/minutos
    horaac = now.strftime("%H%M")

    # Llama a la funcion generate_icn alojada en edi/icn.py
    icn = generate_icn()

    
    gs06 = f"{icn:09d}"

    vt = "44202"

    stnum5 = gs06[:5]
    stnum = f"{stnum5}0001"

    qty = len(registros)

    lines = []

    # =========================================================
    # ICS
    # =========================================================
    lines.append(
        f"ICS*+ANSI1.1  VT{vt:<15}VTVISTA          "
        f"{fechaac}{horaac}{icn:09d}{SEG_TERM}"
    )

    # =========================================================
    # GS
    # =========================================================
    lines.append(
        f"GS*VI*AHGP*VISTA*{fechaac}*{horaac}*{gs06}*T*1{SEG_TERM}"
    )

    # =========================================================
    # ST
    # =========================================================
    lines.append(
        f"ST*550*{stnum}{SEG_TERM}"
    )

    # =========================================================
    # BV5
    # =========================================================
    # Según el manual OBT (550): BV501 tipo, BV502 SCAC, BV503 SPLC origen,
    # BV504 cantidad, BV505 delay code, BV506 fecha, BV507 SPLC destino (cond),
    # BV508 servicio (cond), BV509 hora. La hora va en la posición 9.
    hold_code = ""
    if registros:
        hold_code = str(registros[0]["hold_code"]).strip().upper()
    lines.append(
        f"BV5*{seg_et}*AHGP*922786006*{qty}*{hold_code}"
        f"*{fechaac}***{horaac}{SEG_TERM}"
    )

    # =========================================================
    # VI
    # =========================================================

    # Contador de vins validos
    valid_vins = 0

    for r in registros:

        vin = str(r["vin"]).strip().upper()
        route_origin = str(r["route_origin"]).strip().upper()
        route_dest = str(r["route_dest"]).strip().upper()
        if len(vin) != 17:
            print(f"VIN inválido ignorado: {vin}")
            continue

        # Según el manual OBT (550), el VI solo requiere VIN, ruta origen y
        # ruta destino (VI01-VI03). VI04-VI10 son condicionales y no se usan
        # para delay effective/terminated, por lo que no se envían.
        lines.append(
            f"VI*{vin}*{route_origin}*{route_dest}{SEG_TERM}"
        )

        valid_vins += 1

    # =========================================================
    # SE
    # =========================================================
    segment_count = 2 + valid_vins + 1

    lines.append(
        f"SE*{segment_count}*{stnum}{SEG_TERM}"
    )

    # =========================================================
    # GE
    # =========================================================
    lines.append(
        f"GE*1*{gs06}{SEG_TERM}"
    )

    # =========================================================
    # ICE
    # =========================================================
    lines.append(
        f"ICE*000001*{icn:09d}{SEG_TERM}"
    )

    return "".join(lines)


def build_edi928(registros):
    now = datetime.now()

    yymmdd = now.strftime("%y%m%d")
    hhmm = now.strftime("%H%M")

    icn = generate_icn()

    lines = []

    # =========================================================
    # ISA
    # =========================================================
    lines.append(
        f"ISA~00~          ~00~          ~ZZ~44202          ~ZZ~VDICS          ~"
        f"{yymmdd}~{hhmm}~U~00302~{icn:09d}~0~P~<{SEG_TERM}"
    )

    # =========================================================
    # GS
    # =========================================================
    lines.append(
        f"GS~AI~44202~VDICS~{yymmdd}~{hhmm}~{icn}~X~003020{SEG_TERM}"
    )

    # =========================================================
    # ST
    # =========================================================
    st_control = "000000001"

    lines.append(
        f"ST~928~{st_control}{SEG_TERM}"
    )

    # =========================================================
    # BIX
    # =========================================================
    lines.append(
        f"BIX~02~AHGP~{yymmdd}~2~~~~~A~91~44202{SEG_TERM}"
    )

    # =========================================================
    # AGRUPAR DAÑOS POR VIN
    # =========================================================
    vins = {}

    for r in registros:
        vin = str(r["vin"]).strip().upper()

        # VALIDAR VIN
        if len(vin) != 17:
            print(f"VIN inválido ignorado: {vin}")
            continue

        # CREAR VIN
        if vin not in vins:
            vins[vin] = {
                "carrier": str(
                    r.get("carrier", "AHGP")
                ).strip().upper(),
                "damages": []
            }

        # =====================================================
        # MAPEO DAÑOS
        # =====================================================
        area = str(
            r.get("damage_area", "")
        ).strip()

        dtype = str(
            r.get("damage_type", "")
        ).strip()

        severity = str(
            r.get("severity", "")
        ).strip()

        # =====================================================
        # SI NO HAY DAÑOS → NO AGREGAR
        # =====================================================
        
        if not area and not dtype and not severity:
            continue

        vins[vin]["damages"].append({
            "area": area,
            "type": dtype,
            "severity": severity
        })

    # =========================================================
    # CONTEO SEGMENTOS
    # ST + BIX
    # =========================================================
    segment_count = 2

    # =========================================================
    # GENERAR TI / VC / ID
    # =========================================================
    for vin, data in vins.items():
        carrier = data["carrier"]

        # =====================================================
        # TI
        # =====================================================
        lines.append(
            f"TI~{carrier}~~~~{SEG_TERM}"
        )

        segment_count += 1

        # =====================================================
        # VC
        # =====================================================
        lines.append(
            f"VC~{vin}~~~~~~03~~~{SEG_TERM}"
        )

        segment_count += 1

        damages = data["damages"]

        # =====================================================
        # SIN DAÑOS
        # =====================================================
        if not damages:
            lines.append(
                f"ID~99~00~0{SEG_TERM}"
            )

            segment_count += 1

        # =====================================================
        # CON DAÑOS
        # =====================================================
        else:
            for d in damages:
                area = d["area"] or "99"
                dtype = d["type"] or "00"
                severity = d["severity"] or "0"

                lines.append(
                    f"ID~{area}~{dtype}~{severity}{SEG_TERM}"
                )

                segment_count += 1

    # =========================================================
    # SE
    # =========================================================
    lines.append(
        f"SE~{segment_count + 1}~{st_control}{SEG_TERM}"
    )

    # =========================================================
    # GE
    # =========================================================
    lines.append(
        f"GE~1~{icn}{SEG_TERM}"
    )

    # =========================================================
    # IEA
    # =========================================================
    lines.append(
        f"IEA~00001~{icn:09d}{SEG_TERM}"
    )

    # =========================================================
    # OUTPUT FINAL - UNA SOLA LÍNEA
    # =========================================================
    return "".join(lines)
