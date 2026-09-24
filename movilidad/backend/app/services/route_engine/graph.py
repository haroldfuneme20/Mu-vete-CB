"""Estructuras compactas en memoria para el motor (T024, research R-05)."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field

from backend.app.geo import deg_delta, haversine_m


def hhmm_to_s(t: str) -> int:
    h, m = t.split(":")[:2]
    return int(h) * 3600 + int(m) * 60


@dataclass(slots=True)
class Stop:
    id: str
    name: str
    kind: str
    lat: float
    lng: float
    barrio_id: str | None


@dataclass(slots=True)
class Pattern:
    idx: int
    id: str
    name: str
    mode: str
    fare_class: str
    fare: float | None
    start_s: int
    end_s: int
    headway_peak_s: int
    headway_off_s: int
    reliability: float
    confidence: float
    last_updated: str
    source_id: str
    source_kind: str
    stops: list[str] = field(default_factory=list)
    times: list[int] = field(default_factory=list)


@dataclass(slots=True)
class Source:
    id: str
    name: str
    kind: str
    date: str


class Graph:
    def __init__(self) -> None:
        self.stops: dict[str, Stop] = {}
        self.patterns: list[Pattern] = []
        self.pattern_by_id: dict[str, int] = {}
        self.by_stop: dict[str, list[tuple[int, int]]] = defaultdict(list)
        self.footpaths: dict[str, list[tuple[str, int]]] = defaultdict(list)
        self.sources: dict[str, Source] = {}
        self._grid: dict[tuple[int, int], list[str]] = defaultdict(list)
        self._cell = 0.005
        self.data_version = ""
        self.data_mode = ""

    # --- carga ----------------------------------------------------------------------------
    @classmethod
    def load(cls, con: sqlite3.Connection) -> Graph:
        g = cls()
        meta = dict(con.execute("SELECT key, value FROM meta").fetchall())
        g.data_version = meta.get("data_version", "")
        g.data_mode = meta.get("data_mode", "")
        for sid, name, kind, pub, loaded in con.execute(
            "SELECT id, name, kind, published_at, loaded_at FROM sources"
        ):
            g.sources[sid] = Source(sid, name, kind, (pub or loaded or "")[:10])
        for sid, name, kind, lat, lng, bid in con.execute(
            "SELECT id, name, kind, lat, lng, barrio_id FROM stops"
        ):
            g.stops[sid] = Stop(sid, name, kind, lat, lng, bid)
            g._grid[g._key(lat, lng)].append(sid)
        for row in con.execute(
            "SELECT id, name, mode, fare_class, fare, service_start, service_end, headway_peak_s,"
            " headway_offpeak_s, reliability, confidence, last_updated, source_id FROM patterns "
            "ORDER BY id"
        ):
            idx = len(g.patterns)
            src = g.sources.get(row[12])
            g.patterns.append(Pattern(
                idx=idx, id=row[0], name=row[1], mode=row[2], fare_class=row[3], fare=row[4],
                start_s=hhmm_to_s(row[5]), end_s=hhmm_to_s(row[6]), headway_peak_s=row[7],
                headway_off_s=row[8], reliability=row[9], confidence=row[10],
                last_updated=row[11], source_id=row[12],
                source_kind=src.kind if src else "institutional",
            ))
            g.pattern_by_id[row[0]] = idx
        for pid, seq, sid, t in con.execute(
            "SELECT pattern_id, seq, stop_id, t_from_start_s FROM pattern_stops "
            "ORDER BY pattern_id, seq"
        ):
            p = g.patterns[g.pattern_by_id[pid]]
            p.stops.append(sid)
            p.times.append(t)
            g.by_stop[sid].append((p.idx, seq))
        for a, b, w in con.execute("SELECT from_stop_id, to_stop_id, walk_s FROM footpaths"):
            g.footpaths[a].append((b, w))
        for lst in g.footpaths.values():
            lst.sort()
        return g

    # --- consultas ------------------------------------------------------------------------
    def _key(self, lat: float, lng: float) -> tuple[int, int]:
        return int(lat // self._cell), int(lng // self._cell)

    def stops_near(self, lat: float, lng: float, radius_m: float) -> list[tuple[str, float]]:
        dlat, dlng = deg_delta(radius_m)
        ri, rj = int(dlat // self._cell) + 1, int(dlng // self._cell) + 1
        ki, kj = self._key(lat, lng)
        out = []
        for i in range(ki - ri, ki + ri + 1):
            for j in range(kj - rj, kj + rj + 1):
                for sid in self._grid.get((i, j), []):
                    s = self.stops[sid]
                    d = haversine_m(lat, lng, s.lat, s.lng)
                    if d <= radius_m:
                        out.append((sid, d))
        out.sort(key=lambda x: (x[1], x[0]))
        return out
