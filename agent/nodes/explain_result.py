"""Nodo 4: explicación en lenguaje sencillo, validada contra los hechos (T052, T069)."""

from __future__ import annotations

import json
from pathlib import Path

from agent.deps import AgentDeps
from agent.providers.mock import explain_template
from agent.state import AgentState
from agent.validators import validate_explanation

PROMPT = (Path(__file__).resolve().parents[1] / "prompts" / "explain.txt").read_text(
    encoding="utf-8")


def _slim_leg(leg: dict) -> dict:
    return {k: leg[k] for k in ("mode", "route_name", "from_stop", "to_stop", "stops",
                                "duration_min", "wait_min", "cost", "source_kind",
                                "confidence", "reports")}


def build_facts(result: dict, priority: str) -> dict:
    rec = result["recommended"]
    alts = [rec, *result["alternatives"]]
    slim = lambda a: {  # noqa: E731
        "total_time_min": a["total_time_min"], "cost": a["cost"], "transfers": a["transfers"],
        "confidence": a["confidence"], "reliability": a["reliability"],
        "legs": [_slim_leg(x) for x in a["legs"]],
    }
    return {
        "priority": priority,
        "recommended": slim(rec),
        "alternatives": [slim(a) for a in result["alternatives"]],
        "is_fastest": rec["total_time_min"] <= min(a["total_time_min"] for a in alts),
        "is_cheapest": rec["cost"] <= min(a["cost"] for a in alts),
        "is_most_reliable": rec["reliability"] >= max(a["reliability"] for a in alts),
        "blocked": [{"route_name": b["route_name"], "n_confirm": b["n_confirm"]}
                    for b in result.get("blocked", [])],
    }


def make_node(deps: AgentDeps):
    def explain_result(state: AgentState) -> AgentState:
        result = state["result"]
        facts = build_facts(result, state.get("priority", "balanced"))
        prompt = PROMPT + json.dumps(facts, ensure_ascii=False)
        text, provider = deps.llm.generate_checked(
            prompt, lambda s: validate_explanation(s, facts))
        if not validate_explanation(text, facts):   # defensa final: plantilla determinística
            text, provider = explain_template(facts), "mock"
        return {"explanation": text, "explanation_provider": provider}

    return explain_result
