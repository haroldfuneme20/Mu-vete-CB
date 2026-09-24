"""T087: interpretación de lenguaje natural con MockProvider (SC-008: ≥ 18/20)."""

from __future__ import annotations

import json
from pathlib import Path

from agent.providers.mock import parse_rules
from backend.app.geo import normalize_name

PHRASES = json.loads((Path(__file__).parent / "fixtures" / "nl_phrases.json").read_text(
    encoding="utf-8"))


def _match(got: str | None, expected: str) -> bool:
    return bool(got) and normalize_name(expected) in normalize_name(got)


def test_at_least_18_of_20_phrases():
    ok, failures = 0, []
    for item in PHRASES:
        r = parse_rules(item["q"])
        good = (r["on_topic"] and _match(r["origin_text"], item["o"])
                and _match(r["destination_text"], item["d"])
                and r["priority"] == item["p"])
        ok += good
        if not good:
            failures.append((item["q"], r))
    assert ok >= 18, f"{ok}/20 correctas; fallas: {failures}"


def test_off_topic():
    r = parse_rules("¿Cuál es la receta del ajiaco?")
    assert r["on_topic"] is False


def test_destination_only_is_on_topic():
    r = parse_rules("quiero ir al Portal Tunal")
    assert r["on_topic"] and r["origin_text"] is None
    assert _match(r["destination_text"], "portal tunal")


def test_time_extraction():
    r = parse_rules("de Paraíso a Restrepo a las 5 de la tarde")
    assert r["time"] == "17:00"
