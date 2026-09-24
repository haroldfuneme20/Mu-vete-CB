"""Paquete offline por niveles (contracts/offline-package.md).

- Nivel a (T022b): Ciudad Bolívar — barrios, paradas, vías principales, rutas comunitarias,
  índice de lugares.
- Nivel b (T022b): toda Bogotá — trazado troncal y estaciones TM/TransMiCable.
- Nivel c (T079): recomendaciones precalculadas de los escenarios de demo.
"""

from __future__ import annotations

import gzip
import json
import sqlite3
from pathlib import Path

from shapely import wkb
from shapely.geometry import LineString, box, mapping

BUDGET_BYTES = 5 * 1024 * 1024
TOL_A = 0.00005   # ~5 m
TOL_B = 0.00015   # ~15 m


def _feature(geom, props):
    return {"type": "Feature", "properties": props, "geometry": mapping(geom)}


def _write(out: Path, name: str, obj) -> None:
    (out / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")),
                            encoding="utf-8")


def _source_kinds(con) -> dict[str, str]:
    return dict(con.execute("SELECT id, kind FROM sources"))


def export_levels_ab(con: sqlite3.Connection, out: Path) -> list[dict]:
    out.mkdir(parents=True, exist_ok=True)
    kinds = _source_kinds(con)
    cb = con.execute(
        "SELECT min(r.min_lng), min(r.min_lat), max(r.max_lng), max(r.max_lat) "
        "FROM barrios b JOIN barrios_rtree r ON r.rid = b.rowid WHERE b.is_ciudad_bolivar = 1"
    ).fetchone()
    if cb[0] is None:
        raise RuntimeError("No hay barrios con localidad Ciudad Bolívar (revisa sources.yaml)")
    area = box(cb[0] - 0.01, cb[1] - 0.01, cb[2] + 0.01, cb[3] + 0.01)

    files: list[tuple[str, str, object]] = []

    feats = [
        _feature(wkb.loads(g).simplify(TOL_A), {"id": bid, "name": name, "kind": "barrio",
                                                 "localidad": loc, "source_kind": kinds[src]})
        for bid, name, loc, g, src in con.execute(
            "SELECT id, name, localidad, geom, source_id FROM barrios WHERE is_ciudad_bolivar=1")
    ]
    files.append(("cb_barrios.geojson", "a", {"type": "FeatureCollection", "features": feats}))

    feats = []
    for sid, name, kind, lat, lng, src in con.execute(
        "SELECT id, name, kind, lat, lng, source_id FROM stops WHERE lng BETWEEN ? AND ? AND "
        "lat BETWEEN ? AND ?", (area.bounds[0], area.bounds[2], area.bounds[1], area.bounds[3])
    ):
        feats.append({"type": "Feature",
                      "properties": {"id": sid, "name": name, "kind": kind,
                                     "source_kind": kinds[src]},
                      "geometry": {"type": "Point", "coordinates": [lng, lat]}})
    files.append(("cb_stops.geojson", "a", {"type": "FeatureCollection", "features": feats}))

    feats = []
    for lid, name, g, src in con.execute(
        "SELECT id, name, geom, source_id FROM display_lines WHERE kind = 'road_main'"
    ):
        geom = wkb.loads(g)
        if geom.intersects(area):
            feats.append(_feature(geom.intersection(area).simplify(TOL_A),
                                  {"id": lid, "name": name, "kind": "road_main",
                                   "source_kind": kinds[src]}))
    files.append(("cb_roads_main.geojson", "a", {"type": "FeatureCollection", "features": feats}))

    feats = []
    coords = {sid: (lng, lat) for sid, lat, lng in con.execute("SELECT id, lat, lng FROM stops")}
    for pid, name, src in con.execute(
        "SELECT id, name, source_id FROM patterns WHERE mode = 'community' AND id LIKE '%:1'"
    ):
        pts = [coords[s] for (s,) in con.execute(
            "SELECT stop_id FROM pattern_stops WHERE pattern_id = ? ORDER BY seq", (pid,))]
        feats.append(_feature(LineString(pts), {"id": pid, "name": name, "kind": "community",
                                                "source_kind": kinds[src]}))
    files.append(("community_routes.geojson", "a",
                  {"type": "FeatureCollection", "features": feats}))

    places = []
    for disp, kind, ref, lat, lng, loc in con.execute(
        "SELECT DISTINCT display_name, kind, ref_id, lat, lng, localidad FROM gazetteer "
        "WHERE kind IN ('barrio','station','landmark') OR (lng BETWEEN ? AND ? AND "
        "lat BETWEEN ? AND ?) ORDER BY display_name",
        (area.bounds[0], area.bounds[2], area.bounds[1], area.bounds[3]),
    ):
        places.append({"n": disp, "k": kind, "r": ref, "lat": round(lat, 6),
                       "lng": round(lng, 6), "l": loc})
    files.append(("places_index.json", "a", places))

    feats = [
        _feature(wkb.loads(g).simplify(TOL_B), {"id": lid, "name": name, "kind": kind,
                                                 "source_kind": kinds[src]})
        for lid, name, kind, g, src in con.execute(
            "SELECT id, name, kind, geom, source_id FROM display_lines "
            "WHERE kind IN ('trunk','provisional')")
    ]
    files.append(("tm_trunk.geojson", "b", {"type": "FeatureCollection", "features": feats}))

    feats = []
    for sid, name, kind, lat, lng, src in con.execute(
        "SELECT id, name, kind, lat, lng, source_id FROM stops "
        "WHERE kind IN ('tm_station','transmicable')"
    ):
        feats.append({"type": "Feature",
                      "properties": {"id": sid, "name": name, "kind": kind,
                                     "source_kind": kinds[src]},
                      "geometry": {"type": "Point", "coordinates": [lng, lat]}})
    files.append(("tm_stations.geojson", "b", {"type": "FeatureCollection", "features": feats}))

    for name, _lvl, obj in files:
        _write(out, name, obj)
    return [{"path": name, "level": lvl} for name, lvl, _ in files]


def export_level_c(db: Path, out: Path, seed: Path) -> list[dict]:
    """Nivel c (T079): recomendaciones precalculadas de los escenarios A y F por prioridad."""
    from datetime import datetime

    import yaml

    from agent.deps import AgentDeps
    from agent.graph import build_graph
    from agent.providers import build_provider
    from backend.app.config import CONFIG_DIR
    from backend.app.core import BOGOTA
    from backend.app.services.gazetteer import Gazetteer
    from backend.app.services.route_engine.engine import RouteEngine
    from backend.app.services.route_engine.graph import Graph

    spec = json.loads((seed / "demo_scenarios.json").read_text(encoding="utf-8"))
    cfg = yaml.safe_load((CONFIG_DIR / "engine.yaml").read_text(encoding="utf-8"))
    fares = yaml.safe_load((CONFIG_DIR / "fares.yaml").read_text(encoding="utf-8"))
    con = sqlite3.connect(db)
    graph, gz = Graph.load(con), Gazetteer(con)
    con.close()
    agent = build_graph(AgentDeps(engine=RouteEngine(graph, cfg, fares), gazetteer=gz,
                                  active_reports=list, llm=build_provider("mock"),
                                  now=lambda: datetime(2026, 9, 24, 7, 30, tzinfo=BOGOTA)))
    results = []
    for sc in spec["scenarios"]:
        for prio in ("balanced", "fast", "cheap", "reliable"):
            st = agent.invoke({"origin": sc["origin"], "destination": sc["destination"],
                               "priority": prio, "depart_at": sc.get("depart")})
            if st.get("clarification") or st.get("error") or not st.get("result"):
                continue
            r = st["result"]
            results.append({
                "scenario": sc["id"], "priority": prio,
                "query_key": f"{sc['origin']['text']}|{sc['destination']['text']}|{prio}",
                "recommendation": {
                    "request": {**r["request"], "interpreted_from_text": False},
                    "recommended": r["recommended"], "alternatives": r["alternatives"],
                    "explanation": st["explanation"], "explanation_provider": "mock",
                    "warning": r["warning"], "confidence": r["confidence"],
                    "evidence": r["evidence"], "blocked": r.get("blocked", []),
                    "computed_at": f"{r['data_version']}", "data_version": r["data_version"],
                    "data_mode": r["data_mode"], "precomputed": True,
                },
            })
    _write(out, "demo_scenarios.json", {"scenarios": spec["scenarios"], "results": results})
    return [{"path": "demo_scenarios.json", "level": "c"}]


def write_manifest(out: Path, entries: list[dict], version: str) -> dict:
    total_gz = 0
    for e in entries:
        data = (out / e["path"]).read_bytes()
        e["bytes"] = len(data)
        e["gzip_bytes"] = len(gzip.compress(data))
        total_gz += e["gzip_bytes"]
    manifest = {"version": version, "total_gzip_bytes": total_gz, "files": entries}
    _write(out, "manifest.json", manifest)
    if total_gz > BUDGET_BYTES:
        raise RuntimeError(
            f"Paquete offline de {total_gz / 1e6:.1f} MB comprimido supera el presupuesto de 5 MB"
        )
    return manifest


def read_manifest_entries(out: Path) -> list[dict]:
    p = out / "manifest.json"
    if not p.exists():
        return []
    return [{"path": e["path"], "level": e["level"]}
            for e in json.loads(p.read_text(encoding="utf-8"))["files"]]
