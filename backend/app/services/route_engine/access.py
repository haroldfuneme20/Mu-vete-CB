"""Paso 1 del motor: paradas a distancia caminable del origen/destino (T045)."""

from __future__ import annotations

from backend.app.services.route_engine.graph import Graph

DETOUR = 1.25  # factor de desvío de la caminata respecto a la línea recta


def walk_seconds(distance_m: float, speed_kmh: float) -> int:
    return int(round(distance_m * DETOUR / (speed_kmh * 1000 / 3600)))


def access_stops(graph: Graph, lat: float, lng: float, cfg: dict) -> dict[str, int]:
    """Devuelve {stop_id: segundos a pie} para las paradas usables (con algún patrón)."""
    walk = cfg["walk"]
    out: dict[str, int] = {}
    for sid, d in graph.stops_near(lat, lng, walk["max_access_m"]):
        if graph.by_stop.get(sid):
            out[sid] = walk_seconds(d, walk["speed_kmh"])
    return out
