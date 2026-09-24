"""Rutas comunitarias (simuladas en el MVP) → patterns `community` en ambos sentidos.

Cada parada se asocia a una parada existente a ≤ 50 m; si no hay, se crea un
`community_point`. Tiempos = distancia / velocidad declarada (T055).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from shapely.geometry import Point

from backend.app.geo import haversine_m
from backend.etl.common import register_source, rtree_insert
from backend.etl.load_stops import _barrio_for

SNAP_M = 50.0


def _snap_or_create(con, route_id, i, st, source_id) -> str:
    rows = con.execute("SELECT id, lat, lng FROM stops").fetchall()
    best, best_d = None, SNAP_M
    for sid, lat, lng in rows:
        d = haversine_m(st["lat"], st["lng"], lat, lng)
        if d <= best_d:
            best, best_d = sid, d
    if best:
        return best
    sid = f"com:{route_id}:{i}"
    cur = con.execute(
        "INSERT INTO stops(id, name, kind, lat, lng, barrio_id, source_id, source_ref) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (sid, st["name"], "community_point", st["lat"], st["lng"],
         _barrio_for(con, st["lat"], st["lng"]), source_id,
         f"community_routes.geojson:{route_id}:{i}"),
    )
    rtree_insert(con, "stops_rtree", cur.lastrowid, Point(st["lng"], st["lat"]))
    return sid


def load(con: sqlite3.Connection, seed: Path) -> int:
    path = seed / "community_routes.geojson"
    if not path.exists():
        return 0
    fc = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for feat in fc["features"]:
        p = feat["properties"]
        kind = p.get("source_kind", "demo_simulated")
        sid = register_source(con, f"src_community_{p['id']}", p["name"],
                              "data/seed/community_routes.geojson", kind, mock=False)
        stop_ids = [_snap_or_create(con, p["id"], i, st, sid) for i, st in enumerate(p["stops"])]
        speed = p.get("speed_kmh", 15) * 1000 / 3600
        for direction, (ids, pts) in enumerate(
            [(stop_ids, p["stops"]), (stop_ids[::-1], p["stops"][::-1])]
        ):
            cum, t = [0], 0.0
            for a, b in zip(pts, pts[1:], strict=False):
                t += haversine_m(a["lat"], a["lng"], b["lat"], b["lng"]) * 1.3 / speed
                cum.append(int(round(t)))
            pid = f"COM_{p['id']}:{direction + 1}"
            head = int(p["headway_min"] * 60)
            con.execute(
                "INSERT INTO patterns(id, route_ref, name, mode, fare_class, fare, service_start,"
                " service_end, headway_peak_s, headway_offpeak_s, reliability, confidence, "
                "last_updated, source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (pid, p["id"], p["name"], "community", "community", p.get("fare"),
                 p["service_start"], p["service_end"], head, int(head * 1.5),
                 p.get("reliability", 0.6), p.get("confidence", 0.55), p["last_updated"], sid),
            )
            con.executemany(
                "INSERT INTO pattern_stops VALUES (?,?,?,?)",
                [(pid, i, s, cum[i]) for i, s in enumerate(ids)],
            )
            n += 1
    return n
