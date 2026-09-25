"""Contenedor de servicios del proceso (base, grafo, motor, agente)."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from shapely import wkb

from agent.deps import AgentDeps
from agent.graph import build_graph
from agent.providers import build_provider
from backend.app.config import Settings
from backend.app.db import Database
from backend.app.services.gazetteer import Gazetteer
from backend.app.services.photos import PhotoStore
from backend.app.services.reports import ReportsRepo
from backend.app.services.route_engine.engine import RouteEngine
from backend.app.services.route_engine.graph import Graph
from backend.app.services.seed import load_seed_reports

BOGOTA = timezone(timedelta(hours=-5), "America/Bogota")
SIMPLIFY_DEG = 0.00003   # ~3 m: suficiente para dibujar sin inflar la respuesta


def bogota_now() -> datetime:
    return datetime.now(BOGOTA).replace(microsecond=0)


class Core:
    def __init__(self, settings: Settings, now=bogota_now):
        self.settings = settings
        self.started = time.time()
        self.now = now
        self.db = Database(settings.db_path, settings.work_db_path)
        with self.db.read() as con:
            self.graph = Graph.load(con)
            self.gazetteer = Gazetteer(con)
        self.engine = RouteEngine(self.graph, settings.engine, settings.fares,
                                  geom_lookup=self.segment_coords)
        self.reports = ReportsRepo(self.db, settings.engine, now)
        self.photos = PhotoStore(settings.photos_dir)
        self.llm = build_provider(settings.llm_provider, settings.gemini_api_key,
                                  settings.groq_api_key)
        self.agent = build_graph(AgentDeps(
            engine=self.engine, gazetteer=self.gazetteer, active_reports=self.reports.active,
            llm=self.llm, now=now))
        self.seeded = load_seed_reports(self.reports, settings.seed_dir, settings.demo_b_backup)

    def segment_coords(self, pattern_id: str, board_seq: int, alight_seq: int) -> list | None:
        """Trazado real (shapes del GTFS) de un tramo de viaje, simplificado para el mapa."""
        with self.db.read() as con:
            rows = con.execute(
                "SELECT geom FROM segments WHERE pattern_id = ? AND seq >= ? AND seq < ? "
                "ORDER BY seq", (pattern_id, board_seq, alight_seq)).fetchall()
        if not rows:
            return None
        coords: list[list[float]] = []
        for (g,) in rows:
            line = wkb.loads(g).simplify(SIMPLIFY_DEG)
            pts = [[round(x, 6), round(y, 6)] for x, y in line.coords]
            coords.extend(pts[1:] if coords else pts)
        return coords
