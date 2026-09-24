"""Trazado troncal, rutas provisionales y malla vial → display_lines (visualización)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.etl.common import read_features, register_source, require_file


def load(con: sqlite3.Connection, raw: Path, cfg: dict, mock: bool) -> int:
    n = 0
    ct = cfg["trunk_lines"]
    sid = register_source(con, "src_trunk", ct["source_name"], ct["file"], ct["kind"], mock)
    for props, g in read_features(require_file(raw, ct["file"]),
                                  [ct["id_field"], ct["name_field"]]):
        con.execute("INSERT OR REPLACE INTO display_lines VALUES (?,?,?,?,?)",
                    (f"trunk:{props[ct['id_field']]}", "trunk", str(props[ct["name_field"]]),
                     g.wkb, sid))
        n += 1

    cp = cfg["provisional_routes"]
    sid = register_source(con, "src_provisional", cp["source_name"], cp["file"], cp["kind"], mock)
    for props, g in read_features(require_file(raw, cp["file"]),
                                  [cp["code_field"], cp["name_field"]]):
        con.execute("INSERT OR REPLACE INTO display_lines VALUES (?,?,?,?,?)",
                    (f"prov:{props[cp['code_field']]}", "provisional",
                     str(props[cp["name_field"]]), g.wkb, sid))
        n += 1

    cr = cfg["road_network"]
    sid = register_source(con, "src_roads", cr["source_name"], cr["file"], cr["kind"], mock)
    main_values = {str(v).lower() for v in cr["main_values"]}
    for props, g in read_features(require_file(raw, cr["file"]),
                                  [cr["id_field"], cr["hierarchy_field"]]):
        kind = ("road_main" if str(props[cr["hierarchy_field"]]).lower() in main_values
                else "road_other")
        con.execute("INSERT OR REPLACE INTO display_lines VALUES (?,?,?,?,?)",
                    (f"road:{props[cr['id_field']]}", kind,
                     str(props.get(cr["name_field"], "") or ""), g.wkb, sid))
        n += 1
    return n
