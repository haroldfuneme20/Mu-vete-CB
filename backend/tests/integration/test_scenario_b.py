"""T063: Escenario B — primer bloqueo penaliza, segundo (otro dispositivo) cambia la ruta."""

from __future__ import annotations

import json
import uuid

import pytest

from backend.tests.conftest import mock_client_for
from backend.tests.integration.test_scenario_a import A


@pytest.fixture()
def client(mock_db, tmp_path):
    c, _ = mock_client_for(mock_db, tmp_path)
    with c:
        yield c


def _rides(d):
    return [x["pattern_id"] for x in d["recommended"]["legs"] if x["mode"] != "walk"]


def _block_point(d):
    """Punto medio del primer tramo del primer viaje de la ruta recomendada."""
    leg = next(x for x in d["recommended"]["legs"] if x["mode"] != "walk")
    (x1, y1), (x2, y2) = leg["geometry"]["coordinates"][:2]
    return {"lat": (y1 + y2) / 2, "lng": (x1 + x2) / 2}


def _report(client, loc):
    rep = {"id": str(uuid.uuid4()), "anon_id": str(uuid.uuid4()), "category": "blockage",
           "location": loc}
    return client.post("/api/reports", data={"report": json.dumps(rep)})


def test_first_report_penalizes_second_switches(client):
    before = client.post("/api/recommendations", json=A).json()
    loc = _block_point(before)

    assert _report(client, loc).status_code == 201
    after1 = client.post("/api/recommendations", json=A).json()
    assert _rides(after1) == _rides(before), "P-12: el primer reporte no debe cambiar la ruta"
    assert after1["recommended"]["total_time_min"] > before["recommended"]["total_time_min"]
    assert "1 persona" in after1["explanation"]

    assert _report(client, loc).status_code == 201
    after2 = client.post("/api/recommendations", json=A).json()
    assert _rides(after2) != _rides(before)
    assert "2 personas reportaron" in after2["explanation"]
