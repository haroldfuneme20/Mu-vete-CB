"""Paso 2 del motor: RAPTOR simplificado basado en frecuencias (T046, research R-01).

- Rondas k = 1..(transbordos.max + 1): cada ronda permite un viaje más en vehículo.
- Espera al abordar = headway × headway_factor (+ penalización de transbordo si k ≥ 2).
- Transbordos a pie precalculados (footpaths) desde paradas alcanzadas en vehículo.
- Los tramos invalidados por reportes confirmados no se pueden recorrer.
- Diversidad: se repite la búsqueda prohibiendo el patrón principal de la mejor alternativa
  nueva, hasta `k_search` ejecuciones. Todo es determinístico (iteraciones ordenadas).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from backend.app.services.route_engine.graph import Graph, Pattern, hhmm_to_s

INF = math.inf


@dataclass(slots=True)
class Label:
    time: float
    kind: str               # access | ride | walk
    data: tuple
    round: int


@dataclass
class Ride:
    pattern: int
    board_seq: int
    alight_seq: int
    wait_s: int
    ride_s: int


@dataclass
class Walk:
    from_stop: str
    to_stop: str
    walk_s: int


@dataclass
class Journey:
    access_stop: str
    access_s: int
    egress_stop: str = ""
    egress_s: int = 0
    parts: list[Ride | Walk] = field(default_factory=list)
    total_s: int = 0

    @property
    def rides(self) -> list[Ride]:
        return [p for p in self.parts if isinstance(p, Ride)]

    def key(self) -> tuple:
        return tuple((r.pattern, r.board_seq, r.alight_seq) for r in self.rides)


def in_peak(t_s: int, cfg: dict) -> bool:
    for w in cfg["service"]["peak_windows"]:
        a, b = w.split("-")
        if hhmm_to_s(a) <= t_s % 86400 < hhmm_to_s(b):
            return True
    return False


def headway_s(p: Pattern, t_s: int, cfg: dict) -> int:
    return p.headway_peak_s if in_peak(t_s, cfg) else p.headway_off_s


def active(p: Pattern, t_s: float) -> bool:
    return p.start_s <= t_s % 86400 <= p.end_s


def _reconstruct(graph: Graph, rounds: list[dict[str, Label]], stop: str, k: int) -> Journey:
    parts: list[Ride | Walk] = []
    sid, r = stop, k
    while True:
        lab = rounds[r][sid]
        if lab.kind == "access":
            parts.reverse()
            return Journey(access_stop=sid, access_s=int(lab.data[0]), parts=parts)
        if lab.kind == "walk":
            frm, w = lab.data
            parts.append(Walk(frm, sid, int(w)))
            sid, r = frm, lab.round
            continue
        pidx, bseq, aseq, wait = lab.data
        pat = graph.patterns[pidx]
        parts.append(Ride(pidx, bseq, aseq, int(wait), pat.times[aseq] - pat.times[bseq]))
        sid, r = pat.stops[bseq], lab.round - 1


def _run(graph: Graph, access: dict[str, int], egress: dict[str, int], depart_s: int,
         cfg: dict, banned: set[int], invalid: set[tuple[int, int]]) -> list[Journey]:
    max_rounds = cfg["transfers"]["max"] + 1
    factor = cfg["wait"]["headway_factor"]
    penalty = cfg["transfers"]["penalty_s"]

    rounds: list[dict[str, Label]] = [{}]
    best: dict[str, float] = {}
    for sid in sorted(access):
        rounds[0][sid] = Label(access[sid], "access", (access[sid],), 0)
        best[sid] = access[sid]
    marked = set(access)
    target_best = INF
    found: list[Journey] = []

    for k in range(1, max_rounds + 1):
        prev = rounds[k - 1]
        cur: dict[str, Label] = dict(prev)
        queue: dict[int, int] = {}
        for sid in sorted(marked):
            for pidx, seq in graph.by_stop.get(sid, ()):
                if pidx not in banned and (pidx not in queue or seq < queue[pidx]):
                    queue[pidx] = seq

        ride_marked: set[str] = set()
        for pidx in sorted(queue):
            p = graph.patterns[pidx]
            boarded: tuple[int, float, int] | None = None   # (seq, salida, espera)
            for seq in range(queue[pidx], len(p.stops)):
                sid = p.stops[seq]
                if boarded is not None:
                    arr = boarded[1] + p.times[seq] - p.times[boarded[0]]
                    if arr < best.get(sid, INF) and arr < target_best:
                        cur[sid] = Label(arr, "ride", (pidx, boarded[0], seq, boarded[2]), k)
                        best[sid] = arr
                        ride_marked.add(sid)
                lab = prev.get(sid)
                if lab is not None and seq < len(p.stops) - 1 and active(p, depart_s + lab.time):
                    wait = int(headway_s(p, int(depart_s + lab.time), cfg) * factor)
                    if k >= 2:
                        wait += penalty
                    dep = lab.time + wait
                    if boarded is None or dep - p.times[seq] < boarded[1] - p.times[boarded[0]]:
                        boarded = (seq, dep, wait)
                if (pidx, seq) in invalid:
                    boarded = None   # no se puede recorrer el tramo seq → seq+1

        walk_marked: set[str] = set()
        for sid in sorted(ride_marked):
            base = cur[sid].time
            for to, w in graph.footpaths.get(sid, ()):
                arr = base + w
                if arr < best.get(to, INF) and arr < target_best:
                    cur[to] = Label(arr, "walk", (sid, w), k)
                    best[to] = arr
                    walk_marked.add(to)
        rounds.append(cur)
        marked = ride_marked | walk_marked

        best_here: tuple[float, str] | None = None
        for sid in sorted(egress):
            lab = cur.get(sid)
            if lab is None or lab.round != k:
                continue
            total = lab.time + egress[sid]
            if best_here is None or total < best_here[0]:
                best_here = (total, sid)
        if best_here is not None:
            target_best = min(target_best, best_here[0])
            j = _reconstruct(graph, rounds, best_here[1], k)
            j.egress_stop, j.egress_s = best_here[1], egress[best_here[1]]
            j.total_s = int(round(best_here[0]))
            found.append(j)
        if not marked:
            break
    return found


def search(graph: Graph, access: dict[str, int], egress: dict[str, int], depart_s: int,
           cfg: dict, invalid: set[tuple[int, int]] | None = None) -> list[Journey]:
    invalid = invalid or set()
    banned: set[int] = set()
    seen: dict[tuple, Journey] = {}
    for _ in range(cfg["candidates"]["k_search"]):
        new = [j for j in _run(graph, access, egress, depart_s, cfg, banned, invalid)
               if j.rides and j.key() not in seen]
        for j in new:
            seen[j.key()] = j
        if not new:
            break
        top = min(new, key=lambda x: (x.total_s, x.key()))
        main = max(top.rides, key=lambda r: (r.ride_s, -r.pattern))
        banned.add(main.pattern)
    return sorted(seen.values(), key=lambda x: (x.total_s, x.key()))
