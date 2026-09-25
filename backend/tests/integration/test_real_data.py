"""Escenarios A, B y F sobre la base REAL (data/build/muevete.db con data_mode = real).

Se omiten si la base real no existe (p. ej. en CI, donde el GTFS vive en un Release).
"""

from __future__ import annotations

import json
import sqlite3
import uuid

import pytest

from backend.app.config import ROOT
from backend.tests.conftest import make_settings

REAL_DB = ROOT / "data/build/muevete.db"


def _is_real() -> bool:
    if not REAL_DB.exists():
        return False
    con = sqlite3.connect(REAL_DB)
    try:
        row = con.execute("SELECT value FROM meta WHERE key = 'data_mode'").fetchone()
    finally:
        con.close()
    return bool(row and row[0] == "real")


pytestmark = pytest.mark.skipif(not _is_real(), reason="no hay base real construida")

A = {"origin": {"text": "Mirador del Paraíso"}, "destination": {"text": "Av. Jiménez"},
     "priority": "fast", "depart_at": "2026-09-24T07:30:00-05:00"}


@pytest.fixture()
def client(tmp_path):
    from fastapi.testclient import TestClient

    from backend.app.core import Core
    from backend.app.main import create_app
    from backend.tests.conftest import FIXED_NOW

    settings = make_settings(REAL_DB, tmp_path, ROOT / "data/seed")
    core = Core(settings, now=lambda: FIXED_NOW)
    with TestClient(create_app(settings, core=core)) as c:
        yield c


def _rides(d):
    return [x["pattern_id"] for x in d["recommended"]["legs"] if x["mode"] != "walk"]


def test_scenario_a_real(client):
    r = client.post("/api/recommendations", json=A)
    assert r.status_code == 200, r.json()
    d = r.json()
    assert d["data_mode"] == "real"
    modes = [x["mode"] for x in d["recommended"]["legs"] if x["mode"] != "walk"]
    assert modes[0] == "transmicable"
    assert len(d["alternatives"]) >= 1


def test_scenario_f_real(client):
    q = "Necesito ir del barrio Paraíso al Portal Tunal, lo más confiable"
    r = client.post("/api/recommendations", json={"query": q})
    assert r.status_code == 200, r.json()
    d = r.json()
    assert d["request"]["priority"] == "reliable"
    assert "Paraíso" in d["request"]["origin"]["display_name"]
    assert "Portal Tunal" in d["request"]["destination"]["display_name"]


def test_scenario_b_real(client):
    before = client.post("/api/recommendations", json=A).json()
    cable = next(x for x in before["recommended"]["legs"] if x["mode"] == "transmicable")
    a, b = cable["stop_points"][:2]
    loc = {"lat": (a["lat"] + b["lat"]) / 2, "lng": (a["lng"] + b["lng"]) / 2}

    def report():
        rep = {"id": str(uuid.uuid4()), "anon_id": str(uuid.uuid4()), "category": "blockage",
               "location": loc}
        return client.post("/api/reports", data={"report": json.dumps(rep)})

    assert report().status_code == 201
    after1 = client.post("/api/recommendations", json=A).json()
    assert _rides(after1) == _rides(before), "P-12: el primer reporte no debe cambiar la ruta"
    assert after1["recommended"]["total_time_min"] > before["recommended"]["total_time_min"]

    assert report().status_code == 201
    after2 = client.post("/api/recommendations", json=A).json()
    assert _rides(after2) != _rides(before)
    assert "2 personas reportaron" in after2["explanation"]
