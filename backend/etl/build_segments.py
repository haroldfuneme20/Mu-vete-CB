"""Geometría de cada tramo (par de paradas consecutivas de un patrón) + segments_rtree.

Usa `shapes.txt` si el patrón tiene `shape_id`; si no (o si la proyección de las paradas sobre
el trazado no avanza, p. ej. en recorridos en bucle), una línea recta entre paradas
(research R-01/T019).
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict

from shapely.geometry import LineString, Point
from shapely.ops import substring

from backend.app.geo import haversine_m, to_local_m
from backend.etl.common import rtree_insert


def _shapes(gtfs, wanted: set[str]) -> dict[str, LineString]:
    pts: dict[str, list[tuple[int, float, float]]] = defaultdict(list)
    for r in gtfs.rows("shapes.txt"):
        sid = r["shape_id"]
        if sid in wanted:
            pts[sid].append(
                (int(r["shape_pt_sequence"]), float(r["shape_pt_lon"]), float(r["shape_pt_lat"])))
    return {
        sid: LineString([(x, y) for _, x, y in sorted(p)])
        for sid, p in pts.items() if len(p) >= 2
    }


MAX_STOP_OFFSET_M = 150    # la parada debe estar a ≤ 150 m del trazado para usarlo
MAX_DETOUR_FACTOR = 3.0    # el tramo no puede ser > 3× la distancia en línea recta …
MAX_DETOUR_EXTRA_M = 800   # … salvo 800 m de margen para tramos muy cortos
SEARCH_FACTOR = 4.0        # ventana de búsqueda hacia adelante: 4× la distancia entre paradas
SEARCH_MIN_M = 1500        # … con un mínimo de 1,5 km


def _forward_positions(shape: LineString, pts: list[tuple[float, float]]) -> list[float | None]:
    """Posición de cada parada sobre el trazado buscando SOLO hacia adelante.

    Evita que en recorridos de ida y vuelta o circuitos una parada se proyecte sobre la pasada
    equivocada del trazado (lo que dibujaba casi toda la ruta en un tramo corto).
    """
    out: list[float | None] = []
    prev = 0.0
    last_pt: tuple[float, float] | None = None
    for lng, lat in pts:
        pt = Point(lng, lat)
        if last_pt is None:
            window = shape.length
        else:
            # buscar solo en una ventana acorde a la distancia desde la parada anterior
            gap_m = haversine_m(last_pt[1], last_pt[0], lat, lng)
            window = max(gap_m * SEARCH_FACTOR, SEARCH_MIN_M) / 111_000
        end = min(prev + window, shape.length)
        rest = substring(shape, prev, end) if (prev > 0 or end < shape.length) else shape
        if rest.is_empty or rest.geom_type != "LineString":
            out.append(None)
            continue
        d = prev + rest.project(pt)
        near = shape.interpolate(d)
        if haversine_m(lat, lng, near.y, near.x) > MAX_STOP_OFFSET_M:
            out.append(None)          # la parada no está sobre este trazado: no avanzar
            continue
        out.append(d)
        prev = d
        last_pt = (lng, lat)
    return out


def _plausible(geom: LineString, a: tuple[float, float], b: tuple[float, float]) -> bool:
    straight = haversine_m(a[1], a[0], b[1], b[0])
    length = to_local_m(geom).length
    return length <= max(straight * MAX_DETOUR_FACTOR, straight + MAX_DETOUR_EXTRA_M)


def build(con: sqlite3.Connection, gtfs_info: dict | None) -> int:
    pattern_shape: dict[str, str] = (gtfs_info or {}).get("pattern_shape", {})
    shapes = _shapes(gtfs_info["gtfs"], set(pattern_shape.values())) if gtfs_info else {}

    coords = {sid: (lng, lat) for sid, lat, lng in con.execute("SELECT id, lat, lng FROM stops")}
    by_pattern: dict[str, list[str]] = defaultdict(list)
    for pid, _seq, sid in con.execute(
        "SELECT pattern_id, seq, stop_id FROM pattern_stops ORDER BY pattern_id, seq"
    ):
        by_pattern[pid].append(sid)

    n = 0
    rows = []
    fallback = 0
    for pid in sorted(by_pattern):
        stops = by_pattern[pid]
        shape = shapes.get(pattern_shape.get(pid, ""))
        dists = _forward_positions(shape, [coords[s] for s in stops]) if shape is not None else None
        for i in range(len(stops) - 1):
            a, b = coords[stops[i]], coords[stops[i + 1]]
            geom = None
            if dists is not None and dists[i] is not None and dists[i + 1] is not None \
                    and dists[i + 1] > dists[i]:
                geom = substring(shape, dists[i], dists[i + 1])
                if geom.is_empty or geom.geom_type != "LineString" or not _plausible(geom, a, b):
                    geom = None
            if geom is None:
                geom = LineString([a, b])
                fallback += shape is not None
            rows.append((f"{pid}:{i}", pid, i, geom))
    for sid, pid, i, geom in rows:
        cur = con.execute("INSERT INTO segments(id, pattern_id, seq, geom) VALUES (?,?,?,?)",
                          (sid, pid, i, geom.wkb))
        rtree_insert(con, "segments_rtree", cur.lastrowid, geom)
        n += 1
    if fallback:
        print(f"  segmentos: {fallback} tramos con trazado dudoso → línea recta entre paradas")
    return n
