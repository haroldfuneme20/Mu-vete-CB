"""T060: Escenario A sobre la base (mock o real) — reproducibilidad y percentil 95."""

from __future__ import annotations

import statistics
import time

import pytest

from backend.tests.conftest import mock_client_for

A = {"origin": {"text": "Mirador del Paraíso"}, "destination": {"text": "Av. Jiménez"},
     "priority": "fast", "depart_at": "2026-09-24T07:30:00-05:00"}
F = {"origin": {"text": "Paraíso"}, "destination": {"text": "Portal Tunal"},
     "priority": "reliable", "depart_at": "2026-09-24T07:30:00-05:00"}


@pytest.fixture()
def client(mock_db, tmp_path):
    c, _ = mock_client_for(mock_db, tmp_path)
    with c:
        yield c


def test_scenario_a_has_alternatives_and_is_reproducible(client):
    runs = [client.post("/api/recommendations", json=A).json() for _ in range(3)]
    for d in runs:
        assert d["recommended"]["rank"] == 1
        assert len(d["alternatives"]) >= 1, "el Escenario B necesita ≥ 2 alternativas viables"
    orders = [[d["recommended"]["id"]] + [a["id"] for a in d["alternatives"]] for d in runs]
    assert orders[0] == orders[1] == orders[2]


def test_p95_under_5_seconds(client):
    times = []
    for i in range(20):
        t0 = time.perf_counter()
        r = client.post("/api/recommendations", json=A if i % 2 == 0 else F)
        times.append(time.perf_counter() - t0)
        assert r.status_code == 200
    p95 = statistics.quantiles(times, n=20)[18]
    assert p95 < 5.0
