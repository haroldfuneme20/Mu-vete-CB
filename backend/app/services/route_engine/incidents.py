"""Paso 4 del motor: efecto de los reportes vigentes sobre los tramos (T067, FR-017/FR-018).

Regla (clarificación Q3):
- 1 reporte (1 anon_id) → penalización parcial según la categoría.
- ≥ 2 reportes coincidentes (mismo tramo, misma categoría, anon_id distintos) → escalada:
  bloqueo invalida el tramo; las demás categorías multiplican la penalización.
- Por viaje y categoría se aplica una sola vez el efecto más fuerte de sus tramos.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from backend.app.services.route_engine.graph import Graph

CATEGORY_LABEL = {
    "blockage": "bloqueo",
    "delay": "retraso",
    "route_change": "cambio de ruta",
    "risk": "riesgo",
    "other": "otro",
}


@dataclass
class ActiveReport:
    id: str
    anon_id: str
    category: str
    segment_ids: list[str]


@dataclass
class IncidentContext:
    # (pattern_idx, seq) → {category: {anon_id: [report_ids]}}
    by_segment: dict[tuple[int, int], dict[str, dict[str, list[str]]]] = field(
        default_factory=dict)
    invalid: set[tuple[int, int]] = field(default_factory=set)

    @classmethod
    def build(cls, graph: Graph, reports: list[ActiveReport], cfg: dict) -> IncidentContext:
        ctx = cls()
        agg: dict[tuple[int, int], dict[str, dict[str, list[str]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list)))
        for r in reports:
            for seg in r.segment_ids:
                pid, _, seq = seg.rpartition(":")
                if pid not in graph.pattern_by_id:
                    continue
                agg[(graph.pattern_by_id[pid], int(seq))][r.category][r.anon_id].append(r.id)
        ctx.by_segment = {k: {c: dict(a) for c, a in v.items()} for k, v in agg.items()}
        if cfg["reports"]["confirmed"].get("blockage", {}).get("invalidate"):
            for key, cats in ctx.by_segment.items():
                if len(cats.get("blockage", {})) >= 2:
                    ctx.invalid.add(key)
        return ctx


@dataclass
class RideEffect:
    add_s: int = 0
    reliability: float = 0.0
    availability: float = 0.0
    reports: list[dict] = field(default_factory=list)


def ride_effect(ctx: IncidentContext, pattern_idx: int, board_seq: int, alight_seq: int,
                cfg: dict) -> RideEffect:
    rc = cfg["reports"]
    strongest: dict[str, tuple[int, list[str]]] = {}
    for seq in range(board_seq, alight_seq):
        for cat, anons in ctx.by_segment.get((pattern_idx, seq), {}).items():
            n = len(anons)
            ids = sorted({rid for lst in anons.values() for rid in lst})
            if cat not in strongest or n > strongest[cat][0]:
                strongest[cat] = (n, ids)
    eff = RideEffect()
    for cat in sorted(strongest):
        n, ids = strongest[cat]
        partial = rc["partial"].get(cat, {}) or {}
        mult = rc["confirmed"].get("multiplier", 2) if n >= 2 else 1
        eff.add_s += int(partial.get("add_s", 0) * mult)
        eff.reliability += partial.get("reliability", 0.0) * mult
        eff.availability += partial.get("availability", 0.0) * mult
        effect = "confirmado" if n >= 2 else "parcial"
        eff.reports.append({"category": cat, "label": CATEGORY_LABEL.get(cat, cat),
                            "n_confirm": n, "effect": effect, "report_ids": ids})
    return eff
