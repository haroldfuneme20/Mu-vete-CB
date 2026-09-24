"""Validador de cifras de la explicación (FR-007, research R-07).

Toda cifra que aparezca en el texto debe existir en los hechos calculados por el motor.
"""

from __future__ import annotations

import json
import re

NUM_RE = re.compile(r"\d{1,3}(?:\.\d{3})+|\d+(?:,\d+)?")


def _nums_in(text: str) -> set[int]:
    out = set()
    for m in NUM_RE.findall(text):
        v = m.replace(".", "").split(",")[0]
        if v.isdigit():
            out.add(int(v))
    return out


def allowed_numbers(facts: dict) -> set[int]:
    allowed: set[int] = set()

    def walk(x):
        if isinstance(x, bool):
            return
        if isinstance(x, int):
            allowed.add(x)
        elif isinstance(x, float):
            allowed.add(int(round(x)))
            if 0 <= x <= 1:
                allowed.add(int(round(x * 100)))
        elif isinstance(x, str):
            allowed.update(_nums_in(x))
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(facts)
    for leg in facts.get("recommended", {}).get("legs", []):
        allowed.add(max(1, len(leg.get("stops", [])) - 1))
    allowed.update({0, 1, 2})  # "1 persona", "2 personas", conectores
    return allowed


def validate_explanation(text: str, facts: dict) -> bool:
    if not text or len(text) > 900:
        return False
    return _nums_in(text) <= allowed_numbers(facts)


def parse_json_output(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "on_topic" not in data:
        return None
    return data
