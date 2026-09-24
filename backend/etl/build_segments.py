"""Geometría de cada tramo (par de paradas consecutivas de un patrón) + segments_rtree.

Usa `shapes.txt` si el viaje tiene `shape_id`; si no, una línea recta entre paradas
(research R-01/T019).
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict

from shapely.geometry import LineString, Point
from shapely.ops import substring

from backend.etl.common import rtree_insert


def _shapes(gtfs) -> dict[str, LineString]:
    pts: dict[str, list[tuple[int, float, float]]] = defaultdict(list)
    for r in gtfs.rows("shapes.txt"):
        pts[r["shape_id"]].append(
            (int(r["shape_pt_sequence"]), float(r["shape_pt_lon"]), float(r["shape_pt_lat"]))
        )
    return {
        sid: LineString([(x, y) for _, x, y in sorted(p)])
        for sid, p in pts.items() if len(p) >= 2
    }


def build(con: sqlite3.Connection, gtfs_info: dict | None) -> int:
    shapes = _shapes(gtfs_info["gtfs"]) if gtfs_info else {}
    pattern_shape: dict[str, str] = {}
    if gtfs_info:
        for tid, pid in gtfs_info["trip_pattern"].items():
            sh = gtfs_info["trips"].get(tid, {}).get("shape_id")
            if sh and sh in shapes and pid not in pattern_shape:
                pattern_shape[pid] = sh

    coords = {sid: (lng, lat) for sid, lat, lng in con.execute("SELECT id, lat, lng FROM stops")}
    rows = con.execute(
        "SELECT pattern_id, seq, stop_id FROM pattern_stops ORDER BY pattern_id, seq"
    ).fetchall()
    by_pattern: dict[str, list[str]] = defaultdict(list)
    for pid, _seq, sid in rows:
        by_pattern[pid].append(sid)

    n = 0
    for pid in sorted(by_pattern):
        stops = by_pattern[pid]
        shape = shapes.get(pattern_shape.get(pid, ""))
        dists = [shape.project(Point(coords[s])) for s in stops] if shape is not None else None
        for i in range(len(stops) - 1):
            a, b = coords[stops[i]], coords[stops[i + 1]]
            geom = None
            if dists is not None and dists[i + 1] > dists[i]:
                geom = substring(shape, dists[i], dists[i + 1])
                if geom.is_empty or geom.geom_type != "LineString":
                    geom = None
            if geom is None:
                geom = LineString([a, b])
            cur = con.execute(
                "INSERT INTO segments(id, pattern_id, seq, geom) VALUES (?,?,?,?)",
                (f"{pid}:{i}", pid, i, geom.wkb),
            )
            rtree_insert(con, "segments_rtree", cur.lastrowid, geom)
            n += 1
    return n
