"""Nodo 2: reportes vigentes y versión de datos (T051, T067). No usa LLM."""

from __future__ import annotations

from agent.deps import AgentDeps
from agent.state import AgentState


def make_node(deps: AgentDeps):
    def retrieve_mobility_data(state: AgentState) -> AgentState:
        return {"active_reports": deps.active_reports(),
                "data_version": deps.engine.g.data_version}

    return retrieve_mobility_data
