"""GET /api/stops (T099): paradas en una caja para el mapa."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from backend.app.api.errors import ApiError

router = APIRouter()
MAX_ITEMS = 2000


@router.get("/stops")
def stops(request: Request, bbox: str = Query(...), kind: str | None = None) -> dict:
    try:
        min_lng, min_lat, max_lng, max_lat = (float(x) for x in bbox.split(","))
    except ValueError as exc:
        raise ApiError("VALIDATION_ERROR", "bbox = minLng,minLat,maxLng,maxLat") from exc
    g = request.app.state.core.graph
    items = []
    for s in sorted(g.stops.values(), key=lambda s: s.id):
        if not (min_lng <= s.lng <= max_lng and min_lat <= s.lat <= max_lat):
            continue
        if kind and s.kind != kind:
            continue
        pats = g.by_stop.get(s.id, [])
        src = g.patterns[pats[0][0]].source_kind if pats else "institutional"
        items.append({"id": s.id, "name": s.name, "kind": s.kind, "lat": s.lat, "lng": s.lng,
                      "source_kind": src})
        if len(items) >= MAX_ITEMS:
            break
    return {"items": items, "truncated": len(items) >= MAX_ITEMS}
