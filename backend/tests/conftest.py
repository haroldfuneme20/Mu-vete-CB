"""Fixtures: red de juguete (T038) y base mock construida con el ETL (integración)."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from shapely.geometry import Point, box

from backend.app.config import CONFIG_DIR, ROOT, Settings
from backend.app.core import BOGOTA, Core
from backend.app.main import create_app
from backend.etl import build_footpaths, build_gazetteer, build_segments
from backend.etl.common import ETL_DIR, rtree_insert

FIXED_NOW = datetime(2026, 9, 24, 7, 30, tzinfo=BOGOTA)

# --- red de juguete ------------------------------------------------------------------------
TOY_STOPS = [
    # id, nombre, kind, lat, lng
    ("A1", "Estación Alta", "transmicable", 4.5500, -74.1500),
    ("A2", "Paradero Alto", "sitp_zonal", 4.5505, -74.1505),
    ("A3", "Punto Comunitario Alto", "community_point", 4.5480, -74.1480),
    ("B1", "Estación Media (cable)", "transmicable", 4.5600, -74.1400),
    ("B2", "Estación Media", "tm_station", 4.5605, -74.1395),
    ("B3", "Paradero Medio", "sitp_zonal", 4.5595, -74.1380),
    ("C", "Estación Centro Sur", "tm_station", 4.5750, -74.1200),
    ("X", "Paradero Intermedio", "sitp_zonal", 4.5400, -74.1200),
    ("D1", "Estación Destino", "tm_station", 4.5900, -74.1000),
    ("D2", "Paradero Destino", "sitp_zonal", 4.5905, -74.1005),
]
TOY_PATTERNS = [
    # id, name, mode, fare_class, fare, headway_s, reliability, confidence, source, stops, mins
    ("P_CABLE:1", "Cable de juguete", "transmicable", "transmicable", None, 60, 0.95, 0.95,
     "src_toy", ["A1", "B1"], [10]),
    ("P_TRUNK:1", "Troncal de juguete", "troncal", "tm_troncal", None, 240, 0.85, 0.95,
     "src_toy", ["B2", "C", "D1"], [10, 10]),
    ("P_ZONAL:1", "Zonal de juguete", "zonal", "sitp_zonal", None, 600, 0.8, 0.95,
     "src_toy", ["A2", "X", "D2"], [25, 25]),
    ("COM_T:1", "Comunitaria de juguete (simulada)", "community", "community", 2000, 900, 0.6,
     0.55, "src_toy_comm", ["A3", "B3"], [12]),
]


def build_toy_db(path: Path, seed_dir: Path) -> Path:
    cfg = yaml.safe_load((CONFIG_DIR / "engine.yaml").read_text(encoding="utf-8"))
    path.unlink(missing_ok=True)
    con = sqlite3.connect(path)
    con.executescript((ETL_DIR / "schema.sql").read_text(encoding="utf-8"))
    con.executemany("INSERT INTO sources VALUES (?,?,?,?,?,?)", [
        ("src_toy", "Red de juguete", "toy", "institutional", "2026-09-01", "2026-09-24"),
        ("src_toy_comm", "Comunitaria de juguete", "toy", "demo_simulated", None, "2026-09-24"),
        ("src_toy_barrios", "Barrios de juguete", "toy", "territorial", None, "2026-09-24"),
    ])
    for bid, name, loc, cb, geom in [
        ("TB1", "Barrio Alto", "Ciudad Bolívar", 1, box(-74.16, 4.54, -74.13, 4.565)),
        ("TB2", "Barrio Destino", "Santa Fe", 0, box(-74.11, 4.58, -74.09, 4.60)),
    ]:
        pt = geom.representative_point()
        cur = con.execute("INSERT INTO barrios VALUES (?,?,?,?,?,?,?,?)",
                          (bid, name, loc, cb, pt.y, pt.x, geom.wkb, "src_toy_barrios"))
        rtree_insert(con, "barrios_rtree", cur.lastrowid, geom)
    for sid, name, kind, lat, lng in TOY_STOPS:
        bid = "TB1" if lat < 4.565 else ("TB2" if lat >= 4.58 else None)
        src = "src_toy_comm" if kind == "community_point" else "src_toy"
        cur = con.execute(
            "INSERT INTO stops(id, name, kind, lat, lng, barrio_id, source_id, source_ref) "
            "VALUES (?,?,?,?,?,?,?,?)", (sid, name, kind, lat, lng, bid, src, f"toy:{sid}"))
        rtree_insert(con, "stops_rtree", cur.lastrowid, Point(lng, lat))
    for pid, name, mode, fc, fare, head, rel, conf, src, stops, mins in TOY_PATTERNS:
        con.execute(
            "INSERT INTO patterns VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (pid, pid.split(":")[0], name, mode, fc, fare, "04:00", "23:00", head, head, rel,
             conf, "2026-09-01", src))
        t = 0
        for i, sid in enumerate(stops):
            con.execute("INSERT INTO pattern_stops VALUES (?,?,?,?)", (pid, i, sid, t * 60))
            if i < len(mins):
                t += mins[i]
    build_segments.build(con, None)
    build_footpaths.build(con, cfg)
    build_gazetteer.build(con, seed_dir)
    con.executemany("INSERT INTO meta VALUES (?,?)",
                    [("data_version", "toy-1"), ("data_mode", "toy")])
    con.commit()
    con.close()
    return path


def make_settings(db: Path, tmp: Path, seed_dir: Path, **over) -> Settings:
    base = dict(
        db_path=db, work_db_path=tmp / "work.db", llm_provider="mock", gemini_api_key=None,
        groq_api_key=None, photos_dir=tmp / "photos", static_dir=None, seed_dir=seed_dir,
        demo_b_backup=False,
        engine=yaml.safe_load((CONFIG_DIR / "engine.yaml").read_text(encoding="utf-8")),
        fares=yaml.safe_load((CONFIG_DIR / "fares.yaml").read_text(encoding="utf-8")),
    )
    base.update(over)
    return Settings(**base)


@pytest.fixture()
def empty_seed(tmp_path: Path) -> Path:
    d = tmp_path / "seed"
    d.mkdir()
    return d


@pytest.fixture()
def toy_db(tmp_path: Path, empty_seed: Path) -> Path:
    return build_toy_db(tmp_path / "toy.db", empty_seed)


@pytest.fixture()
def toy_core(toy_db: Path, tmp_path: Path, empty_seed: Path) -> Core:
    return Core(make_settings(toy_db, tmp_path, empty_seed), now=lambda: FIXED_NOW)


@pytest.fixture()
def toy_client(toy_core: Core):
    with TestClient(create_app(toy_core.settings, core=toy_core)) as c:
        yield c


# --- base mock completa (ETL) --------------------------------------------------------------
@pytest.fixture(scope="session")
def mock_db(tmp_path_factory) -> Path:
    from backend.etl.build import build

    tmp = tmp_path_factory.mktemp("mockdb")
    db = tmp / "muevete.db"
    build(tmp / "raw", ROOT / "data/seed", db, tmp / "offline", mock=True)
    return db


def mock_client_for(mock_db: Path, tmp_path: Path, **over):
    settings = make_settings(mock_db, tmp_path, ROOT / "data/seed", **over)
    core = Core(settings, now=lambda: FIXED_NOW)
    return TestClient(create_app(settings, core=core)), core
