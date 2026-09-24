"""GET /api/places (T053): autocompletar y desambiguación."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

router = APIRouter()


@router.get("/places")
def places(request: Request, q: str = Query(min_length=1, max_length=80),
           limit: int = Query(default=5, ge=1, le=20)) -> dict:
    gz = request.app.state.core.gazetteer
    return {"items": [
        {"ref_id": c["ref_id"], "kind": c["kind"], "display_name": c["display_name"],
         "localidad": c["localidad"], "lat": c["lat"], "lng": c["lng"]}
        for c in gz.search(q, limit)
    ]}
