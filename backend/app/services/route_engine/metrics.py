"""Paso 3 del motor: métricas por candidato (T047)."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.services.route_engine.graph import Graph
from backend.app.services.route_engine.incidents import IncidentContext, RideEffect, ride_effect
from backend.app.services.route_engine.raptor import Journey, headway_s

INTEGRATED = {"tm_troncal", "transmicable", "sitp_zonal", "provisional"}


@dataclass
class Metrics:
    time_s: int
    cost: int
    availability: float
    reliability: float
    confidence: float
    transfers: int
    ride_effects: list[RideEffect] = field(default_factory=list)
    ride_costs: list[int] = field(default_factory=list)
    penalized: bool = False


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def fare_for(pattern, fares: dict) -> int:
    if pattern.fare_class == "community":
        return int(pattern.fare if pattern.fare is not None else fares["community"]["default"])
    return int(fares.get(pattern.fare_class, 0))


def compute(graph: Graph, j: Journey, depart_s: int, ctx: IncidentContext, cfg: dict,
            fares: dict) -> Metrics:
    floor = cfg["reports"]["caps"]["min_score_component"]
    av = cfg["availability"]
    add_total = 0
    costs: list[int] = []
    effects: list[RideEffect] = []
    avail, rel, conf = 1.0, 1.0, 1.0
    integrated_paid = False
    window_s = fares["integrated_transfer"]["window_min"] * 60
    first_integrated_t: float | None = None
    t = j.access_s
    for part in j.parts:
        if not hasattr(part, "pattern"):
            t += part.walk_s
            continue
        p = graph.patterns[part.pattern]
        t += part.wait_s
        # costo con regla de transbordo integrado
        if p.fare_class in INTEGRATED:
            if integrated_paid and first_integrated_t is not None and \
                    t - first_integrated_t <= window_s:
                c = int(fares["integrated_transfer"]["extra"])
            else:
                c = fare_for(p, fares)
                integrated_paid, first_integrated_t = True, t
        else:
            c = fare_for(p, fares)
        costs.append(c)
        # disponibilidad por frecuencia
        h_min = headway_s(p, int(depart_s + t), cfg) / 60
        span = av["worst_headway_min"] - av["best_headway_min"]
        a = 1 - (h_min - av["best_headway_min"]) / span
        eff = ride_effect(ctx, part.pattern, part.board_seq, part.alight_seq, cfg)
        effects.append(eff)
        avail = min(avail, _clamp(a, floor, 1.0) + eff.availability)
        rel = min(rel, p.reliability + eff.reliability)
        conf = min(conf, p.confidence)
        add_total += eff.add_s
        t += part.ride_s
    add_total = min(add_total, cfg["reports"]["caps"]["max_add_s"])
    return Metrics(
        time_s=j.total_s + add_total,
        cost=sum(costs),
        availability=round(_clamp(avail, floor, 1.0), 3),
        reliability=round(_clamp(rel, floor, 1.0), 3),
        confidence=round(conf, 3),
        transfers=max(0, len(j.rides) - 1),
        ride_effects=effects,
        ride_costs=costs,
        penalized=any(e.reports for e in effects),
    )
