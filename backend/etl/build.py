"""Construye data/build/muevete.db y el paquete offline desde data/raw + data/seed.

Uso:
  python -m backend.etl.build --raw data/raw --seed data/seed \
      --db data/build/muevete.db --offline frontend/public/offline
  python -m backend.etl.build --mock ...   # genera y usa datos MOCK en data/raw/mock
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

import yaml

from backend.etl import (
    build_footpaths,
    build_gazetteer,
    build_segments,
    export_offline,
    load_barrios,
    load_community,
    load_gtfs,
    load_stops,
    load_tm_lines,
)
from backend.etl.common import ETL_DIR, ETLError, load_sources_config, now_iso

ROOT = ETL_DIR.parent.parent


def build(raw: Path, seed: Path, db: Path, offline: Path | None, mock: bool,
          sources_cfg: Path | None = None) -> dict:
    if mock:
        from backend.etl.mock_raw import generate

        raw = raw / "mock" if raw.name != "mock" else raw
        generate(raw)
    cfg = load_sources_config(sources_cfg)
    engine_cfg = yaml.safe_load((ROOT / "backend/config/engine.yaml").read_text(encoding="utf-8"))

    db.parent.mkdir(parents=True, exist_ok=True)
    tmp = db.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript((ETL_DIR / "schema.sql").read_text(encoding="utf-8"))
    loaded_at = now_iso()
    t0 = time.time()
    stats: dict[str, int | str] = {}
    stats["barrios"] = load_barrios.load(con, raw, cfg, mock)
    stats["barrios_ciudad_bolivar"] = con.execute(
        "SELECT count(*) FROM barrios WHERE is_ciudad_bolivar = 1").fetchone()[0]
    stats["stops"] = load_stops.load(con, raw, cfg, mock)
    gtfs_info = load_gtfs.load(con, raw, cfg, engine_cfg, loaded_at)
    stats["patterns_gtfs"] = gtfs_info["patterns"]
    stats["patterns_community"] = load_community.load(con, seed)
    stats["display_lines"] = load_tm_lines.load(con, raw, cfg, mock)
    stats["segments"] = build_segments.build(con, gtfs_info)
    stats["footpaths"] = build_footpaths.build(con, engine_cfg)
    stats["gazetteer"] = build_gazetteer.build(con, seed)
    data_version = loaded_at
    con.executemany("INSERT OR REPLACE INTO meta VALUES (?,?)", [
        ("data_version", data_version), ("data_mode", "mock" if mock else "real"),
        ("raw_dir", str(raw)),
    ])
    con.commit()

    entries = export_offline.export_levels_ab(con, offline) if offline is not None else []
    con.close()
    tmp.replace(db)
    if offline is not None:
        if (seed / "demo_scenarios.json").exists():
            entries += export_offline.export_level_c(db, offline, seed)
        manifest = export_offline.write_manifest(offline, entries, data_version)
        stats["offline_gzip_bytes"] = manifest["total_gzip_bytes"]
        stats["offline_precomputed"] = len(json.loads(
            (offline / "demo_scenarios.json").read_text(encoding="utf-8"))["results"]) \
            if (offline / "demo_scenarios.json").exists() else 0
    stats["seconds"] = round(time.time() - t0, 2)
    stats["data_version"] = data_version
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description="ETL Muévete CB")
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--seed", default="data/seed")
    ap.add_argument("--db", default="data/build/muevete.db")
    ap.add_argument("--offline", default=None, help="carpeta de salida del paquete offline")
    ap.add_argument("--mock", action="store_true", help="generar y usar datos MOCK")
    ap.add_argument("--sources", default=None, help="sources.yaml alternativo")
    a = ap.parse_args()
    try:
        stats = build(Path(a.raw), Path(a.seed), Path(a.db),
                      Path(a.offline) if a.offline else None, a.mock,
                      Path(a.sources) if a.sources else None)
    except ETLError as exc:
        print(f"ERROR ETL: {exc}", file=sys.stderr)
        return 2
    for k, v in stats.items():
        print(f"{k:>24}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
