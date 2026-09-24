"""Nodo 3: llama al motor determinístico. NUNCA usa el LLM (constitución II)."""

from __future__ import annotations

from datetime import datetime

from agent.deps import AgentDeps
from agent.state import AgentState
from backend.app.services.route_engine.engine import EngineError


def _depart(deps: AgentDeps, value: str | None) -> datetime:
    now = deps.now()
    if not value:
        return now
    if len(value) <= 5 and ":" in value:          # "HH:MM" interpretado de texto libre
        h, m = value.split(":")
        return now.replace(hour=int(h) % 24, minute=int(m), second=0, microsecond=0)
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=now.tzinfo)


def make_node(deps: AgentDeps):
    def evaluate_routes(state: AgentState) -> AgentState:
        try:
            result = deps.engine.recommend(
                state["resolved_origin"], state["resolved_destination"],
                state.get("priority", "balanced"), _depart(deps, state.get("depart_at")),
                state.get("active_reports", []),
            )
            return {"result": result, "error": None}
        except EngineError as e:
            return {"result": None,
                    "error": {"code": e.code, "message": e.message, "details": e.details}}

    return evaluate_routes
