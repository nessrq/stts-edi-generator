# === LEE LA 660 Y EXTRAE GS/ICE/AN/VI ===

import re

from config import SEG_TERM


def split_segments(text):
    if SEG_TERM in text:
        return [p.strip() for p in text.split(SEG_TERM) if p.strip()]
    return [p.strip() for p in re.split(r"[~\r\n]+", text) if p.strip()]


def extract_segment(segments, tag):
    return next((s for s in segments if s.startswith(tag + "*")), None)


def extract_fields(seg):
    return seg.split("*")


def parse_asn(path):
    text = open(path, "r", encoding="utf-8").read()
    segs = split_segments(text)
    gs = extract_segment(segs, "GS")
    ice = extract_segment(segs, "ICE")
    an = extract_segment(segs, "AN")
    gs02 = gs03 = gs04 = gs05 = gs06 = ""
    an03 = ""
    an04 = ""
    an05 = ""
    VON = ""
    DIN = ""
    if an:
        d = extract_fields(an)
        if len(d) > 3:
            an03 = d[3]
        if len(d) > 4:
            an04 = d[4]
        if len(d) > 5:
            an05 = d[5]
    if gs:
        p = extract_fields(gs)
        if len(p) > 2:
            gs02 = p[2]
        if len(p) > 3:
            gs03 = p[3]
        if len(p) > 4:
            gs04 = p[4]
        if len(p) > 5:
            gs05 = p[5]
        if len(p) > 6:
            gs06 = p[6]
    pid = ""
    if ice:
        p = extract_fields(ice)
        if len(p) > 2:
            pid = p[2]
    vins_raw = [s for s in segs if s.startswith("VI*")]
    vins = []
    for v in vins_raw:
        parts = v.split("*")
        vin = parts[1].strip() if len(parts) > 1 else ""
        route_origin = parts[2].strip() if len(parts) > 2 else ""
        route_dest = parts[3].strip() if len(parts) > 3 else ""
        VON = parts[4].strip() if len(parts) > 4 else ""
        DIN = parts[5].strip() if len(parts) > 5 else ""

        vi_short_general = f"VI*{vin}*{route_origin}*{route_dest}"
        vins.append(v)
    return {"GS02": gs02, "GS03": gs03, "GS04": gs04,
            "GS05": gs05, "GS06": gs06, "PID": pid, "VINS": vins,
            "AN03": an03, "AN04": an04, "AN05": an05, "VON": VON, "DIN": DIN}
