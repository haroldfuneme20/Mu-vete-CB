"""Gazetteer: nombres resolubles de barrios, estaciones, paradas e hitos (research R-06)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from backend.app.geo import normalize_name


def build(con: sqlite3.Connection, seed: Path) -> int:
    rows = []
    loc_of_barrio = dict(con.execute("SELECT id, localidad FROM barrios"))
    for bid, name, loc, lat, lng in con.execute(
        "SELECT id, name, localidad, centroid_lat, centroid_lng FROM barrios"
    ):
        rows.append((normalize_name(name), name, "barrio", bid, lat, lng, loc))

    seen_station: set[str] = set()
    for sid, name, kind, lat, lng, bid, parent in con.execute(
        "SELECT id, name, kind, lat, lng, barrio_id, parent_id FROM stops "
        "ORDER BY parent_id IS NOT NULL, id"
    ):
        loc = loc_of_barrio.get(bid)
        if kind in ("tm_station", "transmicable"):
            if parent:            # plataforma/vagón: la estación padre ya representa el lugar
                continue
            label = f"{name} (TransMiCable)" if kind == "transmicable" else name
            key = normalize_name(label)
            if key in seen_station:
                continue
            seen_station.add(key)
            rows.append((key, label, "station", sid, lat, lng, loc))
        else:
            rows.append((normalize_name(name), name, "stop", sid, lat, lng, loc))

    lm = seed / "landmarks.json"
    if lm.exists():
        for item in json.loads(lm.read_text(encoding="utf-8")):
            for alias in [item["name"], *item.get("aliases", [])]:
                rows.append((normalize_name(alias), item["name"], "landmark", item["id"],
                             item["lat"], item["lng"], item.get("localidad")))
    con.executemany("INSERT INTO gazetteer VALUES (?,?,?,?,?,?,?)", rows)
    return len(rows)
