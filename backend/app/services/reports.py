"""Reportes ciudadanos (T065): upsert idempotente, asociación a tramos y confirmaciones."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from shapely import wkb
from shapely.geometry import Point

from backend.app.db import Database
from backend.app.geo import deg_delta, to_local_m
from backend.app.models.report import ReportIn
from backend.app.services.route_engine.incidents import ActiveReport


class ReportsRepo:
    def __init__(self, db: Database, cfg: dict, now: Callable[[], datetime]):
        self.db, self.cfg, self.now = db, cfg, now

    # --- escritura ------------------------------------------------------------------------
    def upsert(self, r: ReportIn, photo_path: str | None = None,
               source: str = "citizen") -> tuple[str, dict]:
        with self.db.write() as con:
            row = con.execute("SELECT * FROM reports WHERE id = ?", (r.id,)).fetchone()
            if row is not None:
                if photo_path and not row["photo_path"]:
                    con.execute("UPDATE reports SET photo_path = ? WHERE id = ?",
                                (photo_path, r.id))
                return "duplicate", self._out(con, r.id)
            received = self.now()
            expires = received + timedelta(hours=self.cfg["reports"]["validity_h"])
            con.execute(
                "INSERT INTO reports(id, anon_id, category, lat, lng, description, photo_path, "
                "created_at, received_at, expires_at, source) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (r.id, r.anon_id, r.category, r.location.lat, r.location.lng, r.description,
                 photo_path, r.created_at, received.isoformat(), expires.isoformat(), source),
            )
            for seg_id, dist in self._nearby_segments(con, r.location.lat, r.location.lng):
                con.execute("INSERT OR IGNORE INTO report_segments VALUES (?,?,?)",
                            (r.id, seg_id, round(dist, 1)))
            return "accepted", self._out(con, r.id)

    def _nearby_segments(self, con, lat: float, lng: float) -> list[tuple[str, float]]:
        radius = self.cfg["reports"]["radius_m"]
        dlat, dlng = deg_delta(radius)
        rows = con.execute(
            "SELECT s.id, s.geom FROM segments_rtree r JOIN segments s ON s.rid = r.rid "
            "WHERE r.max_lng >= ? AND r.min_lng <= ? AND r.max_lat >= ? AND r.min_lat <= ?",
            (lng - dlng, lng + dlng, lat - dlat, lat + dlat),
        ).fetchall()
        pt = to_local_m(Point(lng, lat))
        out = []
        for sid, g in rows:
            d = to_local_m(wkb.loads(g)).distance(pt)
            if d <= radius:
                out.append((sid, d))
        return sorted(out)

    # --- lectura --------------------------------------------------------------------------
    def _confirmations(self, con, report_id: str) -> int:
        row = con.execute(
            "SELECT max(n) FROM (SELECT count(DISTINCT r2.anon_id) AS n FROM report_segments rs "
            "JOIN report_segments rs2 ON rs2.segment_id = rs.segment_id "
            "JOIN reports r ON r.id = rs.report_id JOIN reports r2 ON r2.id = rs2.report_id "
            "WHERE rs.report_id = ? AND r2.category = r.category AND r2.expires_at > ? "
            "GROUP BY rs.segment_id)",
            (report_id, self.now().isoformat()),
        ).fetchone()
        return int(row[0] or 1)

    def _out(self, con, report_id: str) -> dict:
        r = con.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        n_seg = con.execute("SELECT count(*) FROM report_segments WHERE report_id = ?",
                            (report_id,)).fetchone()[0]
        return {"id": r["id"], "received_at": r["received_at"], "expires_at": r["expires_at"],
                "affected_segments": n_seg, "confirmations": self._confirmations(con, r["id"])}

    def active(self) -> list[ActiveReport]:
        now = self.now().isoformat()
        with self.db.read() as con:
            rows = con.execute(
                "SELECT r.id, r.anon_id, r.category, group_concat(rs.segment_id) AS segs "
                "FROM reports r LEFT JOIN report_segments rs ON rs.report_id = r.id "
                "WHERE r.expires_at > ? GROUP BY r.id ORDER BY r.id", (now,)).fetchall()
        return [ActiveReport(r["id"], r["anon_id"], r["category"],
                             sorted((r["segs"] or "").split(",")) if r["segs"] else [])
                for r in rows]

    def count_active(self) -> int:
        with self.db.read() as con:
            return con.execute("SELECT count(*) FROM reports WHERE expires_at > ?",
                               (self.now().isoformat(),)).fetchone()[0]

    def list_public(self, active_only: bool = True,
                    bbox: tuple[float, float, float, float] | None = None) -> list[dict]:
        q = "SELECT * FROM reports WHERE 1=1"
        args: list = []
        if active_only:
            q += " AND expires_at > ?"
            args.append(self.now().isoformat())
        if bbox:
            q += " AND lng BETWEEN ? AND ? AND lat BETWEEN ? AND ?"
            args += [bbox[0], bbox[2], bbox[1], bbox[3]]
        q += " ORDER BY received_at DESC LIMIT 500"
        with self.db.read() as con:
            return [
                {"id": r["id"], "category": r["category"], "lat": r["lat"], "lng": r["lng"],
                 "description": r["description"], "received_at": r["received_at"],
                 "expires_at": r["expires_at"], "has_photo": bool(r["photo_path"]),
                 "source": r["source"], "confirmations": self._confirmations(con, r["id"])}
                for r in con.execute(q, args).fetchall()
            ]
