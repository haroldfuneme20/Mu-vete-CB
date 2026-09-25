"""GTFS → patterns + pattern_stops (research R-01).

Un patrón es (route_id, secuencia ordenada de paradas). Los tiempos entre paradas son la
mediana de hasta `max_trips_per_pattern` viajes; los intervalos (headways) salen de
`frequencies.txt` o, si no existe para el viaje, de las salidas observadas.

El GTFS real de Bogotá trae ~9,5 M filas en stop_times.txt (no ordenadas por viaje): se
filtran los viajes de un día hábil (`service_day`) y se ordenan en una base SQLite temporal
en disco, para no cargar todo en memoria.
"""

from __future__ import annotations

import sqlite3
import statistics
import tempfile
from collections import defaultdict
from pathlib import Path

from backend.etl.common import read_features, require_file
from backend.etl.gtfs_io import GTFS, hms_to_s

FARE_CLASS = {
    "troncal": "tm_troncal",
    "provisional": "provisional",
    "zonal": "sitp_zonal",
    "alimentador": "alimentador",
    "transmicable": "transmicable",
}
DAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}


def _windows(cfg_engine: dict) -> list[tuple[int, int]]:
    out = []
    for w in cfg_engine["service"]["peak_windows"]:
        a, b = w.split("-")
        out.append((hms_to_s(a + ":00"), hms_to_s(b + ":00")))
    return out


def _overlaps(a0, a1, windows) -> bool:
    return any(a0 < w1 and a1 > w0 for w0, w1 in windows)


def _fmt(s: int) -> str:
    s = min(max(0, s), 24 * 3600 - 60)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}"


def _services(gtfs: GTFS, day: str | None) -> set[str] | None:
    if not day or not gtfs.has("calendar.txt"):
        return None
    if day not in DAYS:
        raise ValueError(f"service_day inválido: {day}")
    return {r["service_id"] for r in gtfs.rows("calendar.txt") if r.get(day) == "1"}


class _Acc:
    __slots__ = ("trips", "samples", "starts", "shape")

    def __init__(self) -> None:
        self.trips: list[str] = []
        self.samples: list[list[int]] = []
        self.starts: list[int] = []
        self.shape: str | None = None


def _mode(route: dict, stops: tuple[str, ...], cfg_g: dict, prov_codes: set[str],
          stop_kind: dict[str, str]) -> str:
    short = (route.get("route_short_name") or "").strip().lower()
    if short and short in prov_codes:
        return "provisional"
    agency_mode = (cfg_g.get("agency_modes") or {}).get(str(route.get("agency_id", "")))
    if agency_mode:
        return agency_mode
    rtype = int(route.get("route_type") or 3)
    if rtype in cfg_g["cable_route_types"] or "cable" in (route.get("route_desc") or "").lower():
        return "transmicable"
    if sum(stop_kind.get(s) == "tm_station" for s in stops) > len(stops) / 2:
        return "troncal"
    return "zonal"


def load(con: sqlite3.Connection, raw: Path, cfg: dict, cfg_engine: dict,
         loaded_at: str) -> dict:
    cg = cfg["gtfs"]
    gtfs = GTFS(require_file(raw, cg["file"]))
    peak = _windows(cfg_engine)

    prov_codes: set[str] = set()
    cp = cfg["provisional_routes"]
    for props, _g in read_features(require_file(raw, cp["file"]), [cp["code_field"]]):
        prov_codes.add(str(props[cp["code_field"]]).strip().lower())

    known_stops = {r[0] for r in con.execute("SELECT id FROM stops")}
    stop_kind = dict(con.execute("SELECT id, kind FROM stops").fetchall())
    routes = {r["route_id"]: r for r in gtfs.rows("routes.txt")}
    services = _services(gtfs, cg.get("service_day"))
    trips = {t["trip_id"]: t for t in gtfs.rows("trips.txt")
             if services is None or t.get("service_id") in services}

    freqs: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    for f in gtfs.rows("frequencies.txt"):
        if f["trip_id"] in trips:
            freqs[f["trip_id"]].append(
                (hms_to_s(f["start_time"]), hms_to_s(f["end_time"]), int(f["headway_secs"])))

    # --- 1) staging de stop_times en disco --------------------------------------------------
    with tempfile.TemporaryDirectory() as tmpdir:
        stg = sqlite3.connect(Path(tmpdir) / "stage.db")
        stg.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;"
                          "CREATE TABLE st(trip TEXT, seq INTEGER, stop TEXT, t INTEGER);")
        batch = []
        for st in gtfs.rows("stop_times.txt"):
            tid = st["trip_id"]
            if tid not in trips or st["stop_id"] not in known_stops:
                continue
            t = st.get("arrival_time") or st.get("departure_time")
            if not t:
                continue
            batch.append((tid, int(st["stop_sequence"]), st["stop_id"], hms_to_s(t)))
            if len(batch) >= 200_000:
                stg.executemany("INSERT INTO st VALUES (?,?,?,?)", batch)
                batch.clear()
        if batch:
            stg.executemany("INSERT INTO st VALUES (?,?,?,?)", batch)
        stg.execute("CREATE INDEX st_trip ON st(trip, seq)")
        stg.commit()

        # --- 2) agrupar viajes en patrones (streaming por viaje) ----------------------------
        max_trips = int(cg.get("max_trips_per_pattern", 50))
        acc: dict[tuple[str, tuple[str, ...]], _Acc] = {}

        def flush(tid: str, rows: list[tuple[str, int]]) -> None:
            if len(rows) < 2:
                return
            trip = trips[tid]
            key = (trip["route_id"], tuple(r[0] for r in rows))
            a = acc.get(key)
            if a is None:
                a = acc[key] = _Acc()
            t0 = rows[0][1]
            a.trips.append(tid)
            a.starts.append(t0)
            if len(a.samples) < max_trips:
                a.samples.append([r[1] - t0 for r in rows])
            if a.shape is None and trip.get("shape_id"):
                a.shape = trip["shape_id"]

        cur_tid, cur_rows = None, []
        for tid, stop, t in stg.execute("SELECT trip, stop, t FROM st ORDER BY trip, seq"):
            if tid != cur_tid:
                if cur_tid is not None:
                    flush(cur_tid, cur_rows)
                cur_tid, cur_rows = tid, []
            cur_rows.append((stop, t))
        if cur_tid is not None:
            flush(cur_tid, cur_rows)
        stg.close()

    # --- 3) escribir patrones -------------------------------------------------------------
    default_start, default_end = cg["default_service"]
    pattern_shape: dict[str, str] = {}
    counters: dict[str, int] = defaultdict(int)
    mode_of_stop: dict[str, set[str]] = defaultdict(set)
    peak_len = sum(w1 - w0 for w0, w1 in peak)
    n = 0
    for (route_id, stops), a in sorted(acc.items(), key=lambda kv: (kv[0][0], min(kv[1].trips))):
        r = routes.get(route_id, {})
        counters[route_id] += 1
        pid = f"{route_id}:{counters[route_id]}"
        cum = [int(statistics.median(col)) for col in zip(*a.samples, strict=True)]
        cum = [max(0, c) for c in cum]

        fw = [w for tid in a.trips for w in freqs.get(tid, [])]
        if fw:
            hp = [h for s, e, h in fw if _overlaps(s, e, peak)]
            ho = [h for s, e, h in fw if not _overlaps(s, e, peak)]
            head_peak = int(min(hp)) if hp else int(statistics.median(h for _, _, h in fw))
            head_off = int(statistics.median(ho)) if ho else head_peak
            svc_start = min(min(s for s, _, _ in fw), min(a.starts))
            svc_end = max(max(e for _, e, _ in fw), max(a.starts) + cum[-1])
        else:
            starts = sorted(a.starts)
            in_peak = sum(1 for s in starts if _overlaps(s, s + 1, peak))
            head_peak = int(peak_len / in_peak) if in_peak else 1800
            off = len(starts) - in_peak
            head_off = int((18 * 3600 - peak_len) / off) if off else max(head_peak, 1800)
            svc_start, svc_end = starts[0], starts[-1] + cum[-1]

        mode = _mode(r, stops, cg, prov_codes, stop_kind)
        short = (r.get("route_short_name") or "").strip()
        long_name = " ".join((r.get("route_long_name") or "").split())
        name = long_name if mode == "transmicable" else f"{short} {long_name}".strip()
        if mode == "transmicable":
            name = f"TransMiCable {long_name}".strip()
        reliability = cg["cable_reliability"] if mode == "transmicable" else cg[
            "default_reliability"]

        con.execute(
            "INSERT INTO patterns(id, route_ref, name, mode, fare_class, fare, service_start, "
            "service_end, headway_peak_s, headway_offpeak_s, reliability, confidence, "
            "last_updated, source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (pid, route_id, name or pid, mode, FARE_CLASS[mode], None,
             _fmt(svc_start) if svc_start else default_start,
             _fmt(svc_end) if svc_end else default_end,
             min(max(head_peak, 30), 3 * 3600), min(max(head_off, 30), 3 * 3600),
             reliability, cg["default_confidence"], loaded_at[:10], "src_gtfs"),
        )
        con.executemany(
            "INSERT INTO pattern_stops(pattern_id, seq, stop_id, t_from_start_s) VALUES (?,?,?,?)",
            [(pid, i, s, cum[i]) for i, s in enumerate(stops)],
        )
        if a.shape:
            pattern_shape[pid] = a.shape
        for s in stops:
            mode_of_stop[s].add(mode)
        n += 1

    # --- 4) tipo definitivo de cada parada servida ------------------------------------------
    updates = []
    for sid, modes in mode_of_stop.items():
        if stop_kind.get(sid) == "community_point":
            continue
        if "transmicable" in modes:
            kind = "transmicable"
        elif "troncal" in modes:
            kind = "tm_station"
        else:
            kind = "sitp_zonal"
        if kind != stop_kind.get(sid):
            updates.append((kind, sid))
    con.executemany("UPDATE stops SET kind = ? WHERE id = ?", updates)

    return {"patterns": n, "pattern_shape": pattern_shape, "gtfs": gtfs,
            "trips_used": sum(len(a.trips) for a in acc.values())}
