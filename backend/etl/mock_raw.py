"""Genera archivos crudos MOCK con el mismo formato que las fuentes reales.

Uso: python -m backend.etl.mock_raw --out data/raw/mock

Sirve para avanzar mientras llegan los archivos reales (P-03). Las coordenadas son
aproximadas y los tiempos, frecuencias y trazados son SIMULADOS: no deben presentarse como
datos oficiales. Todas las fuentes generadas llevan "(MOCK)" en su nombre.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from pathlib import Path

# --- Geografía simulada -------------------------------------------------------------------

BARRIOS = [
    # id, nombre, localidad, (lat_min, lat_max, lng_min, lng_max)
    ("CB001", "Paraíso", "Ciudad Bolívar", (4.550, 4.558, -74.162, -74.150)),
    ("CB002", "Mirador Alto", "Ciudad Bolívar", (4.544, 4.550, -74.166, -74.154)),
    ("CB003", "Manitas", "Ciudad Bolívar", (4.558, 4.564, -74.156, -74.144)),
    ("CB004", "Juan Pablo II", "Ciudad Bolívar", (4.564, 4.572, -74.150, -74.136)),
    ("CB005", "Lucero", "Ciudad Bolívar", (4.556, 4.566, -74.144, -74.130)),
    ("CB006", "Vista Hermosa", "Ciudad Bolívar", (4.540, 4.548, -74.150, -74.136)),
    ("CB007", "Candelaria La Nueva", "Ciudad Bolívar", (4.548, 4.556, -74.150, -74.136)),
    ("TU001", "Tunal", "Tunjuelito", (4.572, 4.582, -74.136, -74.120)),
    ("RU001", "Santa Lucía", "Rafael Uribe Uribe", (4.582, 4.594, -74.112, -74.098)),
    ("AN001", "Restrepo", "Antonio Nariño", (4.588, 4.598, -74.098, -74.084)),
    ("SF001", "Las Cruces", "Santa Fe", (4.596, 4.608, -74.084, -74.068)),
]

# Estaciones (id, nombre, tipo, lat, lng)
CABLE = [
    ("TMC01", "Portal Tunal", "Cable", 4.5766, -74.1306),
    ("TMC02", "Juan Pablo II", "Cable", 4.5680, -74.1420),
    ("TMC03", "Manitas", "Cable", 4.5610, -74.1500),
    ("TMC04", "Mirador del Paraíso", "Cable", 4.5540, -74.1560),
]
TRUNK = [
    ("TM001", "Portal Tunal", "Troncal", 4.5770, -74.1300),
    ("TM002", "Parque", "Troncal", 4.5820, -74.1160),
    ("TM003", "Santa Lucía", "Troncal", 4.5875, -74.1045),
    ("TM004", "Calle 40 Sur", "Troncal", 4.5925, -74.0950),
    ("TM005", "Hortúa", "Troncal", 4.5972, -74.0855),
    ("TM006", "Av. Jiménez", "Troncal", 4.6015, -74.0765),
]

# Paraderos zonales (id, nombre, lat, lng)
SITP = [
    ("SP001", "Paraíso - Cl 71 Sur", 4.5535, -74.1575),
    ("SP002", "Mirador Alto - Kr 27", 4.5470, -74.1600),
    ("SP003", "Manitas - Cl 70", 4.5605, -74.1490),
    ("SP004", "Juan Pablo II - Kr 18", 4.5685, -74.1410),
    ("SP005", "Lucero - Av. Boyacá", 4.5620, -74.1360),
    ("SP006", "Candelaria - Cl 64 Sur", 4.5520, -74.1420),
    ("SP007", "Vista Hermosa - Kr 18", 4.5440, -74.1430),
    ("SP008", "Portal Tunal - Zonal", 4.5760, -74.1295),
    ("SP009", "Tunal - Av. Boyacá", 4.5790, -74.1250),
    ("SP010", "Santa Lucía - Kr 12", 4.5860, -74.1060),
    ("SP011", "Restrepo - Kr 19", 4.5930, -74.0900),
    ("SP012", "Las Cruces - Cl 6", 4.5985, -74.0800),
    ("SP013", "Av. Jiménez - Zonal", 4.6010, -74.0772),
    ("SP014", "Av. Villavicencio - Cl 59 Sur", 4.5700, -74.1300),
    ("SP015", "Av. Caracas - Cl 27 Sur", 4.5900, -74.0990),
]

# Rutas GTFS: (route_id, short_name, long_name, route_type, desc, stops, minutes_between,
#              headway_peak_min, headway_off_min, start, end)
ROUTES = [
    ("R_CABLE", "TMC", "TransMiCable Ciudad Bolívar", 6, "cable",
     ["TMC04", "TMC03", "TMC02", "TMC01"], [4, 4, 5], 1, 1, "05:00", "22:00"),
    ("R_TRUNK_H", "H", "Troncal Caracas Sur - Portal Tunal / Av. Jiménez", 3, "troncal",
     ["TM001", "TM002", "TM003", "TM004", "TM005", "TM006"], [5, 4, 4, 4, 4], 4, 6,
     "04:30", "23:00"),
    ("R_Z174", "17-4", "Zonal Paraíso - Centro", 3, "zonal",
     ["SP001", "SP003", "SP006", "SP014", "SP009", "SP010", "SP015", "SP011", "SP012",
      "SP013"], [7, 8, 9, 8, 8, 7, 8, 6, 5], 12, 20, "04:30", "22:30"),
    ("R_Z182", "18-2", "Zonal Juan Pablo II - Portal Tunal", 3, "zonal",
     ["SP004", "SP005", "SP014", "SP008"], [5, 5, 5], 8, 12, "04:30", "22:30"),
    ("R_Z240", "240", "Zonal Portal Tunal - Las Cruces", 3, "zonal",
     ["SP008", "SP009", "SP010", "SP011", "SP012", "SP013"], [6, 9, 9, 8, 6], 10, 15,
     "04:30", "22:30"),
    ("R_P02", "P-02", "Provisional Portal Tunal - Calle 40 Sur", 3, "provisional",
     ["SP008", "SP009", "SP010", "SP015"], [6, 8, 8], 15, 20, "05:00", "21:00"),
]

ROADS = [
    ("V001", "Av. Boyacá", "arterial",
     [(-74.1600, 4.5470), (-74.1490, 4.5605), (-74.1360, 4.5620), (-74.1250, 4.5790)]),
    ("V002", "Av. Caracas", "arterial",
     [(-74.1300, 4.5770), (-74.1045, 4.5875), (-74.0855, 4.5972), (-74.0765, 4.6015)]),
    ("V003", "Av. Villavicencio", "arterial",
     [(-74.1420, 4.5520), (-74.1300, 4.5700), (-74.1295, 4.5760)]),
    ("V004", "Kr 18 (Ciudad Bolívar)", "intermedia",
     [(-74.1430, 4.5440), (-74.1420, 4.5520), (-74.1410, 4.5685)]),
    ("V005", "Cl 71 Sur", "local", [(-74.1575, 4.5535), (-74.1560, 4.5540)]),
]


def _rect(b):
    lat0, lat1, lng0, lng1 = b
    return [[[lng0, lat0], [lng1, lat0], [lng1, lat1], [lng0, lat1], [lng0, lat0]]]


def _fc(features):
    return {"type": "FeatureCollection", "features": features}


def _point(lng, lat, props):
    return {"type": "Feature", "properties": props,
            "geometry": {"type": "Point", "coordinates": [lng, lat]}}


def _line(coords, props):
    return {"type": "Feature", "properties": props,
            "geometry": {"type": "LineString", "coordinates": coords}}


def _hhmm_to_s(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 3600 + int(m) * 60


def _s_to_hms(s: int) -> str:
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def build_gtfs() -> bytes:
    stops = {s[0]: (s[1], s[3], s[4]) for s in CABLE + TRUNK}
    stops.update({s[0]: (s[1], s[2], s[3]) for s in SITP})

    files: dict[str, list[list]] = {
        "agency.txt": [["agency_id", "agency_name", "agency_url", "agency_timezone"],
                       ["TM", "TransMilenio (MOCK)", "https://example.org", "America/Bogota"]],
        "stops.txt": [["stop_id", "stop_name", "stop_lat", "stop_lon"]],
        "routes.txt": [["route_id", "agency_id", "route_short_name", "route_long_name",
                        "route_type", "route_desc"]],
        "trips.txt": [["route_id", "service_id", "trip_id", "direction_id"]],
        "stop_times.txt": [["trip_id", "arrival_time", "departure_time", "stop_id",
                            "stop_sequence"]],
        "frequencies.txt": [["trip_id", "start_time", "end_time", "headway_secs"]],
    }
    for sid, (name, lat, lng) in sorted(stops.items()):
        files["stops.txt"].append([sid, name, f"{lat:.6f}", f"{lng:.6f}"])

    for (rid, short, long_, rtype, desc, seq, mins, hp, ho, start, end) in ROUTES:
        files["routes.txt"].append([rid, "TM", short, long_, rtype, desc])
        for direction in (0, 1):
            s_seq = seq if direction == 0 else list(reversed(seq))
            m_seq = mins if direction == 0 else list(reversed(mins))
            trip_id = f"{rid}_{direction}"
            files["trips.txt"].append([rid, "WD", trip_id, direction])
            t = _hhmm_to_s(start)
            for i, stop_id in enumerate(s_seq):
                hms = _s_to_hms(t)
                files["stop_times.txt"].append([trip_id, hms, hms, stop_id, i + 1])
                if i < len(m_seq):
                    t += m_seq[i] * 60
            # frecuencias: pico y valle
            files["frequencies.txt"] += [
                [trip_id, _s_to_hms(_hhmm_to_s(start)), "06:00:00", ho * 60],
                [trip_id, "06:00:00", "09:00:00", hp * 60],
                [trip_id, "09:00:00", "16:00:00", ho * 60],
                [trip_id, "16:00:00", "19:30:00", hp * 60],
                [trip_id, "19:30:00", _s_to_hms(_hhmm_to_s(end)), ho * 60],
            ]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, rows in files.items():
            sio = io.StringIO()
            csv.writer(sio, lineterminator="\n").writerows(rows)
            zf.writestr(name, sio.getvalue())
    return buf.getvalue()


def generate(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    w = lambda name, obj: (out / name).write_text(  # noqa: E731
        json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")

    w("BarriosCatastrales.geojson", _fc([
        {"type": "Feature",
         "properties": {"CODIGO_BARRIO": bid, "NOMBRE_BARRIO": name, "LOCALIDAD": loc},
         "geometry": {"type": "Polygon", "coordinates": _rect(b)}}
        for bid, name, loc, b in BARRIOS
    ]))
    w("EstacionesTransmilenio.geojson", _fc([
        _point(lng, lat, {"CODIGO_ESTACION": sid, "NOMBRE_ESTACION": name, "TIPO": tipo})
        for sid, name, tipo, lat, lng in CABLE + TRUNK
    ]))
    w("ParaderosZonalesSITP.geojson", _fc([
        _point(lng, lat, {"CODIGO_PARADERO": sid, "NOMBRE_PARADERO": name})
        for sid, name, lat, lng in SITP
    ]))
    w("TrazadoTroncal.geojson", _fc([
        _line([[s[4], s[3]] for s in TRUNK],
              {"CODIGO_TRONCAL": "H", "NOMBRE_TRONCAL": "Caracas Sur (MOCK)"}),
        _line([[s[4], s[3]] for s in reversed(CABLE)],
              {"CODIGO_TRONCAL": "TMC", "NOMBRE_TRONCAL": "TransMiCable (MOCK)"}),
    ]))
    sitp = {s[0]: s for s in SITP}
    w("RutasProvisionales.geojson", _fc([
        _line([[sitp[x][3], sitp[x][2]] for x in ["SP008", "SP009", "SP010", "SP015"]],
              {"CODIGO_RUTA": "P-02", "NOMBRE_RUTA": "Provisional Portal Tunal - Calle 40 Sur"}),
    ]))
    w("MallaVialIntegrada.geojson", _fc([
        _line([list(c) for c in coords],
              {"CODIGO_VIA": vid, "NOMBRE_VIA": name, "JERARQUIA": h})
        for vid, name, h, coords in ROADS
    ]))
    (out / "gtfs_bogota.zip").write_bytes(build_gtfs())
    (out / "MOCK_README.txt").write_text(
        "Datos SIMULADOS generados por backend/etl/mock_raw.py. No son datos oficiales.\n",
        encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/raw/mock")
    args = ap.parse_args()
    generate(Path(args.out))
    print(f"Datos mock generados en {args.out}")


if __name__ == "__main__":
    main()
