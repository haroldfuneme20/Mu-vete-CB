"""Carga BarriosCatastrales → barrios + barrios_rtree."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.app.geo import normalize_name
from backend.etl.common import read_features, register_source, require_file, rtree_insert


def load(con: sqlite3.Connection, raw: Path, cfg: dict, mock: bool) -> int:
    c = cfg["barrios"]
    path = require_file(raw, c["file"])
    sid = register_source(con, "src_barrios", c["source_name"], c["file"], c["kind"], mock)
    target = cfg["localidad_ciudad_bolivar"]
    n = 0
    for props, geom in read_features(path, [c["id_field"], c["name_field"], c["localidad_field"]]):
        loc = str(props[c["localidad_field"]] or "")
        is_cb = 1 if normalize_name(loc, drop_prefix=False) == target else 0
        pt = geom.representative_point()
        cur = con.execute(
            "INSERT INTO barrios(id, name, localidad, is_ciudad_bolivar, centroid_lat, "
            "centroid_lng, geom, source_id) VALUES (?,?,?,?,?,?,?,?)",
            (str(props[c["id_field"]]), str(props[c["name_field"]]), loc, is_cb,
             pt.y, pt.x, geom.wkb, sid),
        )
        rtree_insert(con, "barrios_rtree", cur.lastrowid, geom)
        n += 1
    return n
