"""Grafo LangGraph de 4 nodos, un solo agente (constitución II, contracts/agent.md).

START → parse_request → (clarification ? END : retrieve_mobility_data) → evaluate_routes →
(error ? END : explain_result) → END
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.deps import AgentDeps
from agent.nodes import evaluate_routes, explain_result, parse_request, retrieve_mobility_data
from agent.state import AgentState


def build_graph(deps: AgentDeps):
    g = StateGraph(AgentState)
    g.add_node("parse_request", parse_request.make_node(deps))
    g.add_node("retrieve_mobility_data", retrieve_mobility_data.make_node(deps))
    g.add_node("evaluate_routes", evaluate_routes.make_node(deps))
    g.add_node("explain_result", explain_result.make_node(deps))
    g.add_edge(START, "parse_request")
    g.add_conditional_edges(
        "parse_request",
        lambda s: "end" if s.get("clarification") else "next",
        {"end": END, "next": "retrieve_mobility_data"},
    )
    g.add_edge("retrieve_mobility_data", "evaluate_routes")
    g.add_conditional_edges(
        "evaluate_routes",
        lambda s: "end" if s.get("error") else "next",
        {"end": END, "next": "explain_result"},
    )
    g.add_edge("explain_result", END)
    return g.compile()


def run(graph, request: dict) -> dict:
    """Ejecuta el grafo y devuelve el estado final."""
    return graph.invoke(request)
