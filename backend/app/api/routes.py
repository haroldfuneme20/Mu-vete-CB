"""GET /api/routes y GET /api/routes/{id} (T099)."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from backend.app.api.errors import ApiError
from backend.app.services.route_engine.metrics import fare_for

router = APIRouter()
PAGE = 50


def _summary(core, p) -> dict:
    return {
        "id": p.id, "name": p.name, "mode": p.mode,
        "service_start": f"{p.start_s // 3600:02d}:{(p.start_s % 3600) // 60:02d}",
        "service_end": f"{p.end_s // 3600:02d}:{(p.end_s % 3600) // 60:02d}",
        "headway_min": round(p.headway_peak_s / 60, 1),
        "fare": fare_for(p, core.settings.fares),
        "source_kind": p.source_kind, "confidence": p.confidence,
        "last_updated": p.last_updated,
    }


@router.get("/routes")
def list_routes(request: Request, mode: str | None = None,
                page: int = Query(default=1, ge=1)) -> dict:
    core = request.app.state.core
    pats = [p for p in core.graph.patterns if not mode or p.mode == mode]
    start = (page - 1) * PAGE
    return {"items": [_summary(core, p) for p in pats[start:start + PAGE]],
            "page": page, "total": len(pats)}


@router.get("/routes/{route_id:path}")
def route_detail(route_id: str, request: Request) -> dict:
    core = request.app.state.core
    idx = core.graph.pattern_by_id.get(route_id)
    if idx is None:
        raise ApiError("NOT_FOUND", "No existe esa ruta.")
    p = core.graph.patterns[idx]
    stops = [core.graph.stops[s] for s in p.stops]
    return {**_summary(core, p),
            "stops": [s.name for s in stops],
            "geometry": {"type": "LineString", "coordinates": [[s.lng, s.lat] for s in stops]}}
