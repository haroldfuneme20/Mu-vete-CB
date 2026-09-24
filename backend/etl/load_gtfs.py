"""GTFS → patterns + pattern_stops (research R-01).

Un patrón es (route_id, secuencia ordenada de paradas). Los tiempos entre paradas son la
mediana de hasta `max_trips_per_pattern` viajes; los intervalos (headways) salen de
`frequencies.txt` o, si no existe, de las salidas observadas en `stop_times.txt`.
"""

from __future__ import annotations

import sqlite3
import statistics
from collections import defaultdict
from pathlib import Path

from backend.etl.common import read_features, require_file
from backend.etl.gtfs_io import GTFS, hms_to_s

FARE_CLASS = {
    "troncal": "tm_troncal",
    "provisional": "provisional",
    "zonal": "sitp_zonal",
    "transmicable": "transmicable",
}


def _windows(cfg_engine: dict) -> list[tuple[int, int]]:
    out = []
    for w in cfg_engine["service"]["peak_windows"]:
        a, b = w.split("-")
        out.append((hms_to_s(a + ":00"), hms_to_s(b + ":00")))
    return out


def _overlaps(a0, a1, windows) -> bool:
    return any(a0 < w1 and a1 > w0 for w0, w1 in windows)


def _fmt(s: int) -> str:
    s = max(0, s) % (24 * 3600) if s < 48 * 3600 else 0
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}"


def load(con: sqlite3.Connection, raw: Path, cfg: dict, cfg_engine: dict,
         loaded_at: str) -> dict:
    cg = cfg["gtfs"]
    gtfs = GTFS(require_file(raw, cg["file"]))
    peak = _windows(cfg_engine)

    prov_codes: set[str] = set()
    cp = cfg["provisional_routes"]
    for props, _g in read_features(require_file(raw, cp["file"]), [cp["code_field"]]):
        prov_codes.add(str(props[cp["code_field"]]).strip().lower())

    stop_kind = dict(con.execute("SELECT id, kind FROM stops").fetchall())
    routes = {r["route_id"]: r for r in gtfs.rows("routes.txt")}
    trips = {t["trip_id"]: t for t in gtfs.rows("trips.txt")}

    by_trip: dict[str, list[tuple[int, str, int]]] = defaultdict(list)
    for st in gtfs.rows("stop_times.txt"):
        t = st.get("arrival_time") or st.get("departure_time")
        if not t:
            continue
        by_trip[st["trip_id"]].append((int(st["stop_sequence"]), st["stop_id"], hms_to_s(t)))

    freqs: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    for f in gtfs.rows("frequencies.txt"):
        freqs[f["trip_id"]].append(
            (hms_to_s(f["start_time"]), hms_to_s(f["end_time"]), int(f["headway_secs"]))
        )

    groups: dict[tuple[str, tuple[str, ...]], list[str]] = defaultdict(list)
    for trip_id in sorted(by_trip):
        seq = sorted(by_trip[trip_id])
        if len(seq) < 2 or trip_id not in trips:
            continue
        key = (trips[trip_id]["route_id"], tuple(s[1] for s in seq))
        groups[key].append(trip_id)

    max_trips = int(cg.get("max_trips_per_pattern", 50))
    default_start, default_end = cg["default_service"]
    trip_pattern: dict[str, str] = {}
    counters: dict[str, int] = defaultdict(int)
    n = 0
    for (route_id, stops), trip_ids in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[1][0])):
        r = routes.get(route_id, {})
        counters[route_id] += 1
        pid = f"{route_id}:{counters[route_id]}"
        sample = trip_ids[:max_trips]
        offsets = []
        for tid in sample:
            seq = sorted(by_trip[tid])
            t0 = seq[0][2]
            offsets.append([s[2] - t0 for s in seq])
        cum = [int(statistics.median(col)) for col in zip(*offsets, strict=True)]

        # headways
        fw = [w for tid in trip_ids for w in freqs.get(tid, [])]
        if fw:
            hp = [h for a, b, h in fw if _overlaps(a, b, peak)]
            ho = [h for a, b, h in fw if not _overlaps(a, b, peak)]
            head_peak = int(min(hp)) if hp else int(statistics.median(h for _, _, h in fw))
            head_off = int(statistics.median(ho)) if ho else head_peak
            svc_start, svc_end = min(a for a, _, _ in fw), max(b for _, b, _ in fw)
        else:
            all_starts = sorted(sorted(by_trip[t])[0][2] for t in trip_ids)
            in_peak = [s for s in all_starts if _overlaps(s, s + 1, peak)]
            peak_len = sum(w1 - w0 for w0, w1 in peak)
            head_peak = int(peak_len / len(in_peak)) if in_peak else 1800
            off = len(all_starts) - len(in_peak)
            head_off = int((18 * 3600 - peak_len) / off) if off else max(head_peak, 1800)
            svc_start, svc_end = all_starts[0], all_starts[-1] + cum[-1]
        start_s = _fmt(svc_start) if svc_start else default_start
        end_s = _fmt(svc_end) if svc_end else default_end

        # modo
        rtype = int(r.get("route_type") or 3)
        desc = (r.get("route_desc") or "").lower()
        short = (r.get("route_short_name") or "").strip()
        if short.lower() in prov_codes:
            mode = "provisional"
        elif rtype in cg["cable_route_types"] or "cable" in desc:
            mode = "transmicable"
        elif sum(stop_kind.get(s) == "tm_station" for s in stops) > len(stops) / 2:
            mode = "troncal"
        else:
            mode = "zonal"
        long_name = r.get("route_long_name") or ""
        name = long_name if mode == "transmicable" else f"{short} {long_name}".strip()
        reliability = cg["cable_reliability"] if mode == "transmicable" else cg[
            "default_reliability"]

        con.execute(
            "INSERT INTO patterns(id, route_ref, name, mode, fare_class, fare, service_start, "
            "service_end, headway_peak_s, headway_offpeak_s, reliability, confidence, "
            "last_updated, source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (pid, route_id, name or pid, mode, FARE_CLASS[mode], None, start_s, end_s,
             max(head_peak, 30), max(head_off, 30), reliability, cg["default_confidence"],
             loaded_at[:10], "src_gtfs"),
        )
        con.executemany(
            "INSERT INTO pattern_stops(pattern_id, seq, stop_id, t_from_start_s) VALUES (?,?,?,?)",
            [(pid, i, s, cum[i]) for i, s in enumerate(stops)],
        )
        for tid in trip_ids:
            trip_pattern[tid] = pid
        n += 1
    return {"patterns": n, "trip_pattern": trip_pattern, "trips": trips, "gtfs": gtfs}
