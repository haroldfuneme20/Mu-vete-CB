"""Nodo 1: interpretar y resolver origen/destino (T051, T090)."""

from __future__ import annotations

from pathlib import Path

from agent.deps import AgentDeps
from agent.state import AgentState
from agent.validators import parse_json_output

PROMPT = (Path(__file__).resolve().parents[1] / "prompts" / "parse.txt").read_text(
    encoding="utf-8")
PRIORITIES = {"balanced", "fast", "cheap", "reliable"}


def _clar(code: str, message: str, candidates=None, field: str | None = None) -> dict:
    return {"code": code, "message": message, "field": field,
            "candidates": [
                {"ref_id": c["ref_id"], "kind": c["kind"], "display_name": c["display_name"],
                 "localidad": c["localidad"], "lat": c["lat"], "lng": c["lng"]}
                for c in (candidates or [])
            ]}


def _resolve_ref(deps: AgentDeps, ref: dict | None, field: str):
    if not ref:
        return None, _clar("VALIDATION_ERROR", f"Falta el {field}.", field=field)
    if ref.get("ref_id"):
        p = deps.gazetteer.resolve_ref(ref["ref_id"])
        if p is None:
            return None, _clar("VALIDATION_ERROR", f"No reconocemos el {field}.", field=field)
        return p, None
    if ref.get("lat") is not None and ref.get("lng") is not None:
        return deps.gazetteer.place_from_point(float(ref["lat"]), float(ref["lng"]),
                                               label=ref.get("label")), None
    if ref.get("text"):
        return _resolve_text(deps, ref["text"], field)
    return None, _clar("VALIDATION_ERROR", f"Falta el {field}.", field=field)


def _resolve_text(deps: AgentDeps, text: str, field: str):
    place, cands = deps.gazetteer.resolve_text(text)
    if place is not None:
        return place, None
    if cands:
        return None, _clar("AMBIGUOUS_PLACE",
                           f"Encontramos varios lugares para «{text}». ¿Cuál es tu {field}?",
                           cands, field)
    return None, _clar("AMBIGUOUS_PLACE",
                       f"No encontramos «{text}». Prueba con el nombre del barrio o de la "
                       "estación, o usa el formulario.", [], field)


def make_node(deps: AgentDeps):
    def parse_request(state: AgentState) -> AgentState:
        out: AgentState = {"interpreted_from_text": False, "clarification": None}
        priority = state.get("priority") or "balanced"
        if state.get("query"):
            text, provider = deps.llm.generate_checked(
                PROMPT + state["query"], lambda s: parse_json_output(s) is not None)
            parsed = parse_json_output(text) or {}
            out["parsed"] = {**parsed, "provider": provider}
            out["interpreted_from_text"] = True
            if not parsed.get("on_topic", False):
                out["clarification"] = _clar(
                    "OFF_TOPIC", "Solo puedo ayudarte con viajes en Bogotá que empiecen o "
                    "terminen en Ciudad Bolívar. ¿A dónde quieres ir?")
                return out
            if parsed.get("priority") in PRIORITIES:
                priority = parsed["priority"]
            if parsed.get("time"):
                out["depart_at"] = parsed["time"]
            o_txt, d_txt = parsed.get("origin_text"), parsed.get("destination_text")
            if not d_txt:
                out["clarification"] = _clar("AMBIGUOUS_PLACE", "¿A dónde quieres ir?",
                                             field="destino")
                return out
            if not o_txt:
                out["clarification"] = _clar("AMBIGUOUS_PLACE", "¿Desde dónde sales?",
                                             field="origen")
                return out
            origin, c1 = _resolve_text(deps, o_txt, "origen")
            dest, c2 = _resolve_text(deps, d_txt, "destino")
        else:
            origin, c1 = _resolve_ref(deps, state.get("origin"), "origen")
            dest, c2 = _resolve_ref(deps, state.get("destination"), "destino")
        out["priority"] = priority if priority in PRIORITIES else "balanced"
        if c1 or c2:
            out["clarification"] = c1 or c2
            return out
        out["resolved_origin"], out["resolved_destination"] = origin, dest
        return out

    return parse_request
