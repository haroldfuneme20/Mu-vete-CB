"""T040: normalización, perfiles de pesos y top-3."""

from __future__ import annotations

import yaml

from backend.app.config import CONFIG_DIR
from backend.app.services.route_engine.metrics import Metrics
from backend.app.services.route_engine.scoring import rank

CFG = yaml.safe_load((CONFIG_DIR / "engine.yaml").read_text(encoding="utf-8"))


def m(time_min, cost, avail=0.9, rel=0.85):
    return Metrics(time_s=time_min * 60, cost=cost, availability=avail, reliability=rel,
                   confidence=0.9, transfers=0)


ITEMS = [
    ("alt_fast", m(40, 3200, rel=0.7), None),
    ("alt_cheap", m(60, 2000, rel=0.7), None),
    ("alt_safe", m(55, 3200, rel=0.98), None),
    ("alt_slow", m(90, 3200, rel=0.6), None),
]


def ids(priority):
    return [s.id for s in rank(ITEMS, priority, CFG)]


def test_top3_only():
    assert len(ids("balanced")) == 3


def test_fast_prefers_time():
    assert ids("fast")[0] == "alt_fast"


def test_cheap_prefers_cost():
    assert ids("cheap")[0] == "alt_cheap"


def test_reliable_prefers_reliability():
    assert ids("reliable")[0] == "alt_safe"


def test_equal_values_normalize_to_one_and_tie_break():
    same = [("alt_b", m(40, 3200), None), ("alt_a", m(40, 3200), None)]
    out = rank(same, "balanced", CFG)
    assert [s.id for s in out] == ["alt_a", "alt_b"]      # desempate por id
    assert out[0].score == out[1].score


def test_weights_sum_to_one():
    for w in CFG["weights"].values():
        assert abs(sum(w) - 1) < 1e-9
