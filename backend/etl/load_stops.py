"""Carga paradas: estaciones TM/TransMiCable, paraderos SITP y stops.txt del GTFS.

Las paradas del GTFS se fusionan con la estación o paradero más cercano a ≤ 15 m; se
conserva la referencia a ambas fuentes en `source_ref` (constitución IV).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from shapely import wkb
from shapely.geometry import Point

from backend.app.geo import haversine_m
from backend.etl.common import (
    Grid,
    read_features,
    register_source,
    require_file,
    rtree_insert,
)
from backend.etl.gtfs_io import GTFS

MERGE_M = 15.0


def _barrio_for(con: sqlite3.Connection, lat: float, lng: float) -> str | None:
    rows = con.execute(
        "SELECT b.id, b.geom FROM barrios_rtree r JOIN barrios b ON b.rowid = r.rid "
        "WHERE r.min_lng <= ? AND r.max_lng >= ? AND r.min_lat <= ? AND r.max_lat >= ?",
        (lng, lng, lat, lat),
    ).fetchall()
    pt = Point(lng, lat)
    for bid, g in rows:
        if wkb.loads(g).covers(pt):
            return bid
    return None


def _insert_stop(con, sid, name, kind, lat, lng, source_id, source_ref):
    cur = con.execute(
        "INSERT INTO stops(id, name, kind, lat, lng, barrio_id, source_id, source_ref) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (sid, name, kind, lat, lng, _barrio_for(con, lat, lng), source_id, source_ref),
    )
    rtree_insert(con, "stops_rtree", cur.lastrowid, Point(lng, lat))


def load(con: sqlite3.Connection, raw: Path, cfg: dict, mock: bool) -> int:
    ct, cs, cg = cfg["tm_stations"], cfg["sitp_stops"], cfg["gtfs"]
    src_tm = register_source(con, "src_tm_stations", ct["source_name"], ct["file"], ct["kind"],
                             mock)
    src_sitp = register_source(con, "src_sitp_stops", cs["source_name"], cs["file"], cs["kind"],
                               mock)
    src_gtfs = register_source(con, "src_gtfs", cg["source_name"], cg["file"], cg["kind"], mock)

    candidates = []  # (lat, lng, kind, name, source_id, ref)
    for props, g in read_features(require_file(raw, ct["file"]),
                                  [ct["id_field"], ct["name_field"]]):
        tipo = str(props.get(ct.get("cable_field", ""), "") or "").lower()
        kind = "transmicable" if "cable" in tipo else "tm_station"
        candidates.append((g.y, g.x, kind, str(props[ct["name_field"]]), src_tm,
                           f"{ct['file']}:{props[ct['id_field']]}"))
    for props, g in read_features(require_file(raw, cs["file"]),
                                  [cs["id_field"], cs["name_field"]]):
        candidates.append((g.y, g.x, "sitp_zonal", str(props[cs["name_field"]]), src_sitp,
                           f"{cs['file']}:{props[cs['id_field']]}"))

    grid = Grid()
    for i, c in enumerate(candidates):
        grid.add(c[0], c[1], i)
    used: set[int] = set()

    gtfs = GTFS(require_file(raw, cg["file"]))
    n = 0
    for row in gtfs.rows("stops.txt"):
        if row.get("location_type") not in (None, "", "0"):
            continue  # estaciones padre / accesos
        lat, lng = float(row["stop_lat"]), float(row["stop_lon"])
        best, best_d = None, MERGE_M
        for i in grid.near(lat, lng):
            d = haversine_m(lat, lng, candidates[i][0], candidates[i][1])
            if d <= best_d:
                best, best_d = i, d
        if best is not None:
            used.add(best)
            c = candidates[best]
            kind, ref = c[2], f"{cg['file']}:{row['stop_id']}|{c[5]}"
        else:
            kind, ref = "sitp_zonal", f"{cg['file']}:{row['stop_id']}"
        _insert_stop(con, row["stop_id"], row.get("stop_name") or row["stop_id"], kind, lat, lng,
                     src_gtfs, ref)
        n += 1

    for i, c in enumerate(candidates):
        if i in used:
            continue
        prefix = "tm" if c[4] == src_tm else "sitp"
        _insert_stop(con, f"{prefix}:{c[5].split(':', 1)[1]}", c[3], c[2], c[0], c[1], c[4], c[5])
        n += 1
    return n
