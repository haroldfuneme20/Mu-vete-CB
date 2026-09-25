"""Carga paradas: estaciones TM/TransMiCable, paraderos SITP y stops.txt del GTFS.

- Las paradas del GTFS (plataformas y estaciones padre) se fusionan con la estación o paradero
  más cercano dentro del radio de cada fuente; se conserva la referencia a ambas fuentes en
  `source_ref` (constitución IV).
- El tipo definitivo de cada parada servida lo fija después load_gtfs según los modos de las
  rutas que pasan por ella.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from shapely import STRtree, wkb
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

SITP_MERGE_M = 15.0


class BarrioIndex:
    """Punto → barrio con un STRtree en memoria (evita consultas por parada)."""

    def __init__(self, con: sqlite3.Connection):
        rows = con.execute("SELECT id, geom FROM barrios").fetchall()
        self.ids = [r[0] for r in rows]
        self.geoms = [wkb.loads(r[1]) for r in rows]
        self.tree = STRtree(self.geoms) if self.geoms else None

    def at(self, lat: float, lng: float) -> str | None:
        if self.tree is None:
            return None
        pt = Point(lng, lat)
        for i in sorted(self.tree.query(pt)):
            if self.geoms[i].covers(pt):
                return self.ids[i]
        return None


def _barrio_for(con: sqlite3.Connection, lat: float, lng: float) -> str | None:
    return BarrioIndex(con).at(lat, lng)


def _insert_stop(con, idx: BarrioIndex, sid, name, kind, lat, lng, source_id, source_ref,
                 parent_id=None):
    cur = con.execute(
        "INSERT INTO stops(id, name, kind, lat, lng, barrio_id, source_id, source_ref, parent_id) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (sid, name, kind, lat, lng, idx.at(lat, lng), source_id, source_ref, parent_id),
    )
    rtree_insert(con, "stops_rtree", cur.lastrowid, Point(lng, lat))


def _station_sources(cfg: dict) -> list[dict]:
    # compatibilidad: `tm_stations` (un archivo) o `stations` (lista)
    if "stations" in cfg:
        return cfg["stations"]
    return [{**cfg["tm_stations"], "source_id": "src_tm_stations"}]


def load(con: sqlite3.Connection, raw: Path, cfg: dict, mock: bool) -> int:
    cs, cg = cfg["sitp_stops"], cfg["gtfs"]
    idx = BarrioIndex(con)

    candidates = []  # (lat, lng, kind, name, source_id, ref, merge_m)
    for st in _station_sources(cfg):
        sid = register_source(con, st.get("source_id", "src_tm_stations"), st["source_name"],
                              st["file"], st["kind"], mock)
        for props, g in read_features(require_file(raw, st["file"]),
                                      [st["id_field"], st["name_field"]]):
            if st.get("fixed_kind"):
                kind = st["fixed_kind"]
            else:
                tipo = str(props.get(st.get("cable_field", ""), "") or "").lower()
                kind = "transmicable" if "cable" in tipo else "tm_station"
            candidates.append((g.y, g.x, kind, str(props[st["name_field"]]).strip(), sid,
                               f"{st['file']}:{props[st['id_field']]}",
                               float(st.get("merge_m", SITP_MERGE_M))))
    src_sitp = register_source(con, "src_sitp_stops", cs["source_name"], cs["file"], cs["kind"],
                               mock)
    for props, g in read_features(require_file(raw, cs["file"]),
                                  [cs["id_field"], cs["name_field"]]):
        candidates.append((g.y, g.x, "sitp_zonal", str(props[cs["name_field"]]).strip(),
                           src_sitp, f"{cs['file']}:{props[cs['id_field']]}", SITP_MERGE_M))
    src_gtfs = register_source(con, "src_gtfs", cg["source_name"], cg["file"], cg["kind"], mock)

    grid = Grid()
    for i, c in enumerate(candidates):
        grid.add(c[0], c[1], i)
    used: set[int] = set()

    gtfs = GTFS(require_file(raw, cg["file"]))
    n = 0
    for row in gtfs.rows("stops.txt"):
        loc_type = row.get("location_type") or "0"
        if loc_type not in ("0", "1"):
            continue  # accesos, nodos genéricos
        lat, lng = float(row["stop_lat"]), float(row["stop_lon"])
        best, best_d = None, None
        for i in grid.near(lat, lng):
            d = haversine_m(lat, lng, candidates[i][0], candidates[i][1])
            if d <= candidates[i][6] and (best_d is None or d < best_d):
                best, best_d = i, d
        if best is not None:
            used.add(best)
            c = candidates[best]
            kind, ref = c[2], f"{cg['file']}:{row['stop_id']}|{c[5]}"
        else:
            kind = "tm_station" if loc_type == "1" else "sitp_zonal"
            ref = f"{cg['file']}:{row['stop_id']}"
        _insert_stop(con, idx, row["stop_id"], (row.get("stop_name") or row["stop_id"]).strip(),
                     kind, lat, lng, src_gtfs, ref, row.get("parent_station") or None)
        n += 1

    for i, c in enumerate(candidates):
        if i in used:
            continue
        prefix = "sitp" if c[4] == src_sitp else "tm"
        _insert_stop(con, idx, f"{prefix}:{c[5].split(':', 1)[1]}", c[3], c[2], c[0], c[1],
                     c[4], c[5])
        n += 1
    return n
