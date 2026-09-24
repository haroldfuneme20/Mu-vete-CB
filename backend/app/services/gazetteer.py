"""Resolución de lugares (T044, research R-06). La IA nunca resuelve lugares: lo hace esto."""

from __future__ import annotations

import re
import sqlite3
from difflib import SequenceMatcher

from shapely import wkb
from shapely.geometry import Point

from backend.app.geo import haversine_m, normalize_name
from backend.app.services.route_engine.engine import Place

KIND_PRIORITY = {"landmark": 0, "station": 1, "barrio": 2, "stop": 3}
MATCH_THRESHOLD = 0.78
SAME_PLACE_M = 400


class Gazetteer:
    def __init__(self, con: sqlite3.Connection):
        cols = ("name_norm", "display_name", "kind", "ref_id", "lat", "lng", "localidad")
        self.rows = [dict(zip(cols, tuple(r), strict=True)) for r in con.execute(
            f"SELECT {', '.join(cols)} FROM gazetteer")]
        self.barrios = [
            (bid, name, loc, bool(cb), wkb.loads(g))
            for bid, name, loc, cb, g in con.execute(
                "SELECT id, name, localidad, is_ciudad_bolivar, geom FROM barrios")
        ]
        self.cb_localidades = {loc for _, _, loc, cb, _ in self.barrios if cb}

    # --- punto → barrio -------------------------------------------------------------------
    def barrio_at(self, lat: float, lng: float) -> tuple[str, str, str, bool] | None:
        pt = Point(lng, lat)
        for bid, name, loc, cb, geom in self.barrios:
            if geom.covers(pt):
                return bid, name, loc, cb
        return None

    def place_from_point(self, lat: float, lng: float, label: str | None = None,
                         kind: str = "point", ref_id: str | None = None,
                         localidad: str | None = None) -> Place:
        b = self.barrio_at(lat, lng)
        return Place(
            display_name=label or (b[1] if b else f"{lat:.5f}, {lng:.5f}"),
            lat=lat, lng=lng, kind=kind, ref_id=ref_id,
            localidad=(b[2] if b else localidad),
            is_ciudad_bolivar=bool(b and b[3]) or (localidad in self.cb_localidades),
        )

    # --- nombre → candidatos --------------------------------------------------------------
    def search(self, text: str, limit: int = 5) -> list[dict]:
        q = normalize_name(text)
        if not q:
            return []
        scored = []
        for r in self.rows:
            n = r["name_norm"]
            if n == q:
                s = 1.0
            elif n.startswith(q) or q in n.split():
                s = 0.9
            elif q in n:
                s = 0.85
            else:
                s = SequenceMatcher(None, q, n).ratio()
            if s >= 0.6:
                scored.append((s, r))
        scored.sort(key=lambda x: (-x[0], KIND_PRIORITY[x[1]["kind"]], x[1]["display_name"]))
        out: list[dict] = []
        for s, r in scored:
            dup = any(
                normalize_name(o["display_name"]) == normalize_name(r["display_name"])
                and haversine_m(o["lat"], o["lng"], r["lat"], r["lng"]) < SAME_PLACE_M
                for o in out
            )
            if not dup:
                out.append({**r, "score": round(s, 3)})
            if len(out) >= limit:
                break
        return out

    def resolve_text(self, text: str) -> tuple[Place | None, list[dict]]:
        """Devuelve (lugar, candidatos). Lugar = None si no hay coincidencia clara."""
        place, cands = self._resolve_once(text)
        stripped = re.sub(r"^(el|la|los|las)\s+", "", normalize_name(text))
        if place is None and stripped != normalize_name(text):
            place2, cands2 = self._resolve_once(stripped)
            if place2 is not None:
                return place2, cands2
        return place, cands

    def _resolve_once(self, text: str) -> tuple[Place | None, list[dict]]:
        cands = self.search(text, limit=5)
        if not cands:
            return None, []
        top = cands[0]
        strong = [c for c in cands if c["score"] >= MATCH_THRESHOLD]
        exact = [c for c in strong if c["score"] >= 0.999]
        if len(exact) == 1 or (len(strong) == 1 and top["score"] >= MATCH_THRESHOLD):
            c = exact[0] if exact else top
            return self.place_for(c), cands
        if len(exact) > 1 and len({(c["kind"], c["localidad"]) for c in exact}) == 1:
            return self.place_for(exact[0]), cands
        return None, cands

    def place_for(self, c: dict) -> Place:
        return self.place_from_point(c["lat"], c["lng"], label=c["display_name"], kind=c["kind"],
                                     ref_id=c["ref_id"], localidad=c["localidad"])

    def resolve_ref(self, ref_id: str) -> Place | None:
        for r in self.rows:
            if r["ref_id"] == ref_id:
                return self.place_for(r)
        return None
