"""Paso 5 del motor: score ponderado y orden determinístico (T048)."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.route_engine.metrics import Metrics


@dataclass
class Scored:
    id: str
    metrics: Metrics
    score: float
    payload: object


def _norm_inverse(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [1.0] * len(values)
    return [(hi - v) / (hi - lo) for v in values]


def rank(items: list[tuple[str, Metrics, object]], priority: str, cfg: dict) -> list[Scored]:
    if not items:
        return []
    weights = cfg["weights"].get(priority) or cfg["weights"]["balanced"]
    wt, wa, wr, wc = weights
    t_norm = _norm_inverse([m.time_s for _, m, _ in items])
    c_norm = _norm_inverse([m.cost for _, m, _ in items])
    scored = []
    for (aid, m, payload), tn, cn in zip(items, t_norm, c_norm, strict=True):
        s = wt * tn + wa * m.availability + wr * m.reliability + wc * cn
        scored.append(Scored(aid, m, round(s, 4), payload))
    # score desc, luego desempate fijo (tie_break: menor tiempo, luego id)
    scored.sort(key=lambda x: (-x.score, x.metrics.time_s, x.id))
    return scored[: cfg["candidates"]["k_return"]]
