"""Transbordos a pie entre paradas a ≤ max_transfer_m (research R-01)."""

from __future__ import annotations

import sqlite3

from backend.app.geo import haversine_m
from backend.etl.common import Grid


def build(con: sqlite3.Connection, cfg_engine: dict) -> int:
    max_m = cfg_engine["walk"]["max_transfer_m"]
    speed = cfg_engine["walk"]["speed_kmh"] * 1000 / 3600
    stops = con.execute("SELECT id, lat, lng FROM stops").fetchall()
    grid = Grid(cell_deg=max(max_m / 111_000, 0.001))
    for s in stops:
        grid.add(s[1], s[2], s)
    rows = []
    for sid, lat, lng in stops:
        for oid, olat, olng in grid.near(lat, lng):
            if oid == sid:
                continue
            d = haversine_m(lat, lng, olat, olng)
            if d <= max_m:
                rows.append((sid, oid, int(round(d * 1.25 / speed))))  # factor de desvío 1,25
    con.executemany("INSERT OR IGNORE INTO footpaths VALUES (?,?,?)", rows)
    return len(rows)
