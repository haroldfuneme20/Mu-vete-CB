"""Contenedor de servicios del proceso (base, grafo, motor, agente)."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

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
        self.engine = RouteEngine(self.graph, settings.engine, settings.fares)
        self.reports = ReportsRepo(self.db, settings.engine, now)
        self.photos = PhotoStore(settings.photos_dir)
        self.llm = build_provider(settings.llm_provider, settings.gemini_api_key,
                                  settings.groq_api_key)
        self.agent = build_graph(AgentDeps(
            engine=self.engine, gazetteer=self.gazetteer, active_reports=self.reports.active,
            llm=self.llm, now=now))
        self.seeded = load_seed_reports(self.reports, settings.seed_dir, settings.demo_b_backup)
