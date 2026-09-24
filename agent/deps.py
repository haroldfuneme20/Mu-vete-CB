"""Dependencias que el grafo recibe del backend (inyección simple, sin globals)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from agent.providers.fallback import FallbackProvider


@dataclass
class AgentDeps:
    engine: Any                       # backend.app.services.route_engine.engine.RouteEngine
    gazetteer: Any                    # backend.app.services.gazetteer.Gazetteer
    active_reports: Callable[[], list]
    llm: FallbackProvider
    now: Callable[[], datetime]
