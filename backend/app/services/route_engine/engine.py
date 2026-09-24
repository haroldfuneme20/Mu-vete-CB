"""Motor de rutas determinístico (constitución II, T050).

Pipeline de 6 pasos: resolver ubicaciones → generar candidatos → estimar métricas →
aplicar incidentes → calcular score → devolver con evidencia. Sin LLM ni red.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

from backend.app.geo import haversine_m
from backend.app.services.route_engine import access, metrics, raptor, scoring
from backend.app.services.route_engine.describe import describe, minutes
from backend.app.services.route_engine.graph import Graph
from backend.app.services.route_engine.incidents import ActiveReport, IncidentContext

MIN_TRIP_M = 200


class EngineError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code, self.message, self.details = code, message, details or {}


@dataclass
class Place:
    display_name: str
    lat: float
    lng: float
    kind: str = "point"
    ref_id: str | None = None
    localidad: str | None = None
    is_ciudad_bolivar: bool = False

    def as_dict(self) -> dict:
        return {"display_name": self.display_name, "localidad": self.localidad,
                "kind": self.kind, "ref_id": self.ref_id, "lat": self.lat, "lng": self.lng,
                "is_ciudad_bolivar": self.is_ciudad_bolivar}


class RouteEngine:
    def __init__(self, graph: Graph, cfg: dict, fares: dict):
        self.g, self.cfg, self.fares = graph, cfg, fares

    # ------------------------------------------------------------------------------------
    def recommend(self, origin: Place, destination: Place, priority: str, depart_at: datetime,
                  reports: list[ActiveReport]) -> dict:
        # 1. resolver / validar
        if not (origin.is_ciudad_bolivar or destination.is_ciudad_bolivar):
            raise EngineError(
                "OUT_OF_COVERAGE",
                "Por ahora solo calculamos viajes que empiezan o terminan en Ciudad Bolívar.")
        if haversine_m(origin.lat, origin.lng, destination.lat, destination.lng) < MIN_TRIP_M:
            raise EngineError("SAME_ORIGIN_DESTINATION",
                              "El origen y el destino son el mismo lugar.")
        depart_s = depart_at.hour * 3600 + depart_at.minute * 60
        acc = access.access_stops(self.g, origin.lat, origin.lng, self.cfg)
        egr = access.access_stops(self.g, destination.lat, destination.lng, self.cfg)
        if not acc or not egr:
            raise EngineError("NO_ROUTE", "No hay paradas a distancia caminable del "
                              + ("origen." if not acc else "destino."),
                              {"suggestion": "Prueba con un lugar cercano a una estación."})

        # 4a. incidentes que invalidan tramos (afectan la búsqueda)
        ctx = IncidentContext.build(self.g, reports, self.cfg)

        # 2. candidatos
        journeys = raptor.search(self.g, acc, egr, depart_s, self.cfg, ctx.invalid)
        blocked = self._blocked(acc, egr, depart_s, ctx) if ctx.invalid else []
        if not journeys:
            raise EngineError(
                "NO_ROUTE",
                "No encontramos una ruta disponible a esta hora."
                + (" Hay bloqueos confirmados en las rutas posibles." if blocked else ""),
                {"suggestion": "Prueba otra hora de salida u otra prioridad.",
                 "blocked": blocked})

        # 3 + 4b. métricas con penalizaciones parciales
        items = []
        for j in journeys:
            m = metrics.compute(self.g, j, depart_s, ctx, self.cfg, self.fares)
            items.append((self._alt_id(j), m, j))

        # 5. score
        ranked = scoring.rank(items, priority, self.cfg)

        # 6. devolver
        alts = [self._alternative(s, i + 1, origin, destination) for i, s in enumerate(ranked)]
        warning = "all_affected" if all(s.metrics.penalized for s in ranked) else None
        evidence = self._evidence(alts)
        for b in blocked:
            evidence.append({"kind": "report",
                             "label": f"{b['n_confirm']} personas reportaron un bloqueo en "
                                      f"{b['route_name']}; se descartó esa opción",
                             "report_ids": b["report_ids"], "n_confirm": b["n_confirm"]})
        return {
            "blocked": blocked,
            "request": {"origin": origin.as_dict(), "destination": destination.as_dict(),
                        "priority": priority, "depart_at": depart_at.isoformat()},
            "recommended": alts[0],
            "alternatives": alts[1:],
            "confidence": alts[0]["confidence"],
            "warning": warning,
            "evidence": evidence,
            "data_version": self.g.data_version,
            "data_mode": self.g.data_mode,
        }

    # ------------------------------------------------------------------------------------
    def _blocked(self, acc, egr, depart_s, ctx: IncidentContext) -> list[dict]:
        """Rutas que serían candidatas pero tienen un tramo invalidado por bloqueo confirmado."""
        out: dict[str, dict] = {}
        for j in raptor.search(self.g, acc, egr, depart_s, self.cfg, set()):
            for r in j.rides:
                for seq in range(r.board_seq, r.alight_seq):
                    key = (r.pattern, seq)
                    if key in ctx.invalid:
                        p = self.g.patterns[r.pattern]
                        anons = ctx.by_segment[key]["blockage"]
                        ids = sorted({x for lst in anons.values() for x in lst})
                        cur = out.get(p.name)
                        if cur is None or len(anons) > cur["n_confirm"]:
                            out[p.name] = {"route_name": p.name, "pattern_id": p.id,
                                           "n_confirm": len(anons), "report_ids": ids}
        return [out[k] for k in sorted(out)]

    def _alt_id(self, j: raptor.Journey) -> str:
        key = "|".join(
            f"{self.g.patterns[r.pattern].id}@{r.board_seq}-{r.alight_seq}" for r in j.rides)
        return "alt_" + hashlib.sha1(key.encode()).hexdigest()[:8]

    def _stop_point(self, sid: str) -> list[float]:
        s = self.g.stops[sid]
        return [s.lng, s.lat]

    def _alternative(self, s: scoring.Scored, rank: int, origin: Place, dest: Place) -> dict:
        j: raptor.Journey = s.payload
        m = s.metrics
        g = self.g
        legs = []
        first = g.stops[j.access_stop]
        legs.append(self._walk_leg(origin.display_name, first.name, j.access_s,
                                   [[origin.lng, origin.lat], [first.lng, first.lat]]))
        ride_i = 0
        for part in j.parts:
            if isinstance(part, raptor.Walk):
                a, b = g.stops[part.from_stop], g.stops[part.to_stop]
                legs.append(self._walk_leg(a.name, b.name, part.walk_s,
                                           [[a.lng, a.lat], [b.lng, b.lat]]))
                continue
            p = g.patterns[part.pattern]
            eff = m.ride_effects[ride_i]
            seq_stops = p.stops[part.board_seq: part.alight_seq + 1]
            src = g.sources.get(p.source_id)
            legs.append({
                "mode": p.mode,
                "pattern_id": p.id,
                "route_name": p.name,
                "from_stop": g.stops[seq_stops[0]].name,
                "to_stop": g.stops[seq_stops[-1]].name,
                "stops": [g.stops[x].name for x in seq_stops],
                "duration_min": minutes(part.ride_s + eff.add_s),
                "wait_min": minutes(part.wait_s),
                "cost": m.ride_costs[ride_i],
                "source_kind": p.source_kind,
                "source_id": p.source_id,
                "source_name": src.name if src else p.source_id,
                "confidence": p.confidence,
                "last_updated": p.last_updated,
                "reports": eff.reports,
                "geometry": {"type": "LineString",
                             "coordinates": [self._stop_point(x) for x in seq_stops]},
            })
            ride_i += 1
        last = g.stops[j.egress_stop]
        legs.append(self._walk_leg(last.name, dest.display_name, j.egress_s,
                                   [[last.lng, last.lat], [dest.lng, dest.lat]]))
        alt = {
            "id": s.id, "rank": rank,
            "total_time_min": minutes(m.time_s), "cost": m.cost, "transfers": m.transfers,
            "availability": m.availability, "reliability": m.reliability,
            "confidence": m.confidence, "score": s.score, "penalized": m.penalized,
            "legs": legs,
        }
        alt["text_description"] = describe(alt)
        alt["evidence"] = self._evidence([alt])
        return alt

    def _walk_leg(self, frm: str, to: str, seconds: int, coords: list) -> dict:
        return {"mode": "walk", "pattern_id": None, "route_name": "Caminata", "from_stop": frm,
                "to_stop": to, "stops": [frm, to], "duration_min": minutes(seconds),
                "wait_min": 0, "cost": 0, "source_kind": "territorial", "source_id": None,
                "source_name": "Cálculo de caminata", "confidence": 1.0, "last_updated": None,
                "reports": [], "geometry": {"type": "LineString", "coordinates": coords}}

    def _evidence(self, alts: list[dict]) -> list[dict]:
        ev: dict[str, dict] = {}
        for alt in alts:
            for leg in alt["legs"]:
                sid = leg.get("source_id")
                if sid and sid not in ev:
                    src = self.g.sources.get(sid)
                    ev[sid] = {"kind": "source", "label": src.name if src else sid,
                               "source_id": sid, "source_kind": leg["source_kind"],
                               "date": src.date if src else None}
                for r in leg["reports"]:
                    key = f"report:{r['category']}:{','.join(r['report_ids'])}"
                    if key not in ev:
                        who = "1 persona reportó" if r["n_confirm"] == 1 else \
                            f"{r['n_confirm']} personas reportaron"
                        ev[key] = {"kind": "report",
                                   "label": f"{who} {r['label']} en {leg['route_name']}",
                                   "report_ids": r["report_ids"], "n_confirm": r["n_confirm"]}
        return list(ev.values())
