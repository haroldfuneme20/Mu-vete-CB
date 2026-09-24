"""POST /api/recommendations (T053, T095): formulario o texto libre → agente."""

from __future__ import annotations

from fastapi import APIRouter, Request

from backend.app.api.errors import ApiError
from backend.app.models.recommendation import RecommendationRequest

router = APIRouter()


@router.post("/recommendations")
def recommendations(req: RecommendationRequest, request: Request) -> dict:
    core = request.app.state.core
    state_in = {
        "query": req.query.strip() if req.query else None,
        "origin": req.origin.model_dump() if req.origin else None,
        "destination": req.destination.model_dump() if req.destination else None,
        "priority": req.priority,
        "depart_at": req.depart_at,
    }
    out = core.agent.invoke(state_in)

    clar = out.get("clarification")
    if clar:
        if clar["code"] == "OFF_TOPIC":
            raise ApiError("VALIDATION_ERROR", clar["message"], {"reason": "off_topic"})
        raise ApiError(clar["code"], clar["message"],
                       {"field": clar.get("field"), "candidates": clar.get("candidates", []),
                        "interpreted": out.get("parsed")})
    if out.get("error"):
        e = out["error"]
        raise ApiError(e["code"], e["message"], e.get("details"))

    result = out["result"]
    return {
        "request": {**result["request"], "interpreted_from_text": out.get(
            "interpreted_from_text", False)},
        "recommended": result["recommended"],
        "alternatives": result["alternatives"],
        "explanation": out["explanation"],
        "explanation_provider": out["explanation_provider"],
        "warning": result["warning"],
        "confidence": result["confidence"],
        "evidence": result["evidence"],
        "blocked": result.get("blocked", []),
        "computed_at": core.now().isoformat(),
        "data_version": result["data_version"],
        "data_mode": result["data_mode"],
    }
