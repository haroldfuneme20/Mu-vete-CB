"""T088: variante `query` (lenguaje natural) de POST /api/recommendations."""

from __future__ import annotations

import pytest

from backend.tests.conftest import mock_client_for


@pytest.fixture()
def client(mock_db, tmp_path):
    c, _ = mock_client_for(mock_db, tmp_path)
    with c:
        yield c


def test_scenario_f_phrase(client):
    q = "Necesito ir del barrio Paraíso al Portal Tunal, lo más confiable"
    r = client.post("/api/recommendations", json={"query": q})
    assert r.status_code == 200, r.json()
    d = r.json()
    assert d["request"]["interpreted_from_text"] is True
    assert d["request"]["priority"] == "reliable"
    assert d["request"]["origin"]["display_name"] == "Paraíso"
    assert "Portal Tunal" in d["request"]["destination"]["display_name"]
    assert d["explanation"]


def test_ambiguous_or_unknown_place(client):
    r = client.post("/api/recommendations", json={"query": "quiero ir de Paraíso a Narnia"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "AMBIGUOUS_PLACE"
    assert "candidates" in r.json()["error"]["details"]


def test_off_topic(client):
    r = client.post("/api/recommendations", json={"query": "¿Cuál es la receta del ajiaco?"})
    assert r.status_code == 422
    assert r.json()["error"]["details"]["reason"] == "off_topic"
