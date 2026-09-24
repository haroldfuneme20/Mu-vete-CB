"""GET /api/health (T028, FR-032)."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict:
    core = request.app.state.core
    ok = bool(core.graph.patterns) and bool(core.graph.stops)
    return {
        "status": "ok" if ok else "degraded",
        "data_version": core.graph.data_version,
        "data_mode": core.graph.data_mode,
        "llm_provider": core.llm.name,
        "llm_last_provider": core.llm.last_provider,
        "reports_active": core.reports.count_active(),
        "uptime_s": int(time.time() - core.started),
    }
