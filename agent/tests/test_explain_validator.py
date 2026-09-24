"""T041: el validador rechaza cifras que no están en los hechos."""

from __future__ import annotations

from agent.providers.mock import explain_template
from agent.validators import parse_json_output, validate_explanation

FACTS = {
    "priority": "fast",
    "is_fastest": True,
    "recommended": {
        "total_time_min": 44, "cost": 3200, "transfers": 1, "confidence": 0.95,
        "reliability": 0.85,
        "legs": [
            {"mode": "transmicable", "route_name": "TransMiCable", "from_stop": "Mirador",
             "to_stop": "Portal Tunal", "stops": ["a", "b", "c", "d"], "duration_min": 13,
             "wait_min": 1, "cost": 3200, "source_kind": "institutional", "confidence": 0.95,
             "reports": []},
        ],
    },
    "alternatives": [],
    "blocked": [],
}


def test_accepts_numbers_present():
    assert validate_explanation("Toma el TransMiCable: 44 minutos y $3.200, confianza 95%.",
                                FACTS)


def test_rejects_invented_numbers():
    assert not validate_explanation("Llegas en 25 minutos por $1.500.", FACTS)


def test_template_always_valid():
    assert validate_explanation(explain_template(FACTS), FACTS)


def test_parse_json_output():
    assert parse_json_output('texto {"on_topic": true, "origin_text": "x"} fin')["on_topic"]
    assert parse_json_output("sin json") is None
    assert parse_json_output('{"otra": 1}') is None
