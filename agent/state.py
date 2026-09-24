"""Estado del grafo LangGraph (contracts/agent.md)."""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # entrada
    query: str | None
    origin: dict | None            # {ref_id} | {lat, lng}
    destination: dict | None
    priority: str
    depart_at: str | None
    # parse_request
    parsed: dict
    resolved_origin: Any
    resolved_destination: Any
    interpreted_from_text: bool
    clarification: dict | None     # {code, message, candidates}
    # retrieve_mobility_data
    active_reports: list
    data_version: str
    # evaluate_routes
    result: dict | None
    error: dict | None
    # explain_result
    explanation: str
    explanation_provider: str
