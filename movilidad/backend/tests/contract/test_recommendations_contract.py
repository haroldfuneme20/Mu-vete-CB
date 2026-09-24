"""T042: contrato de POST /api/recommendations (formulario) y GET /api/places."""

from __future__ import annotations

AT = "2026-09-24T07:30:00-05:00"
FORM = {"origin": {"lat": 4.5500, "lng": -74.1500}, "destination": {"lat": 4.5900, "lng": -74.1000},
        "priority": "fast", "depart_at": AT}


def test_shape(toy_client):
    r = toy_client.post("/api/recommendations", json=FORM)
    assert r.status_code == 200
    d = r.json()
    for k in ("request", "recommended", "alternatives", "explanation", "explanation_provider",
              "warning", "confidence", "evidence", "computed_at", "data_version"):
        assert k in d
    rec = d["recommended"]
    for k in ("id", "rank", "total_time_min", "cost", "transfers", "availability",
              "reliability", "confidence", "score", "legs", "text_description", "evidence"):
        assert k in rec
    for leg in rec["legs"]:
        assert leg["source_kind"]
        assert leg["geometry"]["type"] == "LineString"
    assert d["explanation_provider"] == "mock"
    assert d["request"]["interpreted_from_text"] is False


def test_out_of_coverage(toy_client):
    body = {**FORM, "origin": {"lat": 4.5900, "lng": -74.1000},
            "destination": {"lat": 4.5750, "lng": -74.1200}}
    r = toy_client.post("/api/recommendations", json=body)
    assert r.status_code == 422 and r.json()["error"]["code"] == "OUT_OF_COVERAGE"


def test_same_origin_destination(toy_client):
    body = {**FORM, "destination": FORM["origin"]}
    r = toy_client.post("/api/recommendations", json=body)
    assert r.status_code == 422 and r.json()["error"]["code"] == "SAME_ORIGIN_DESTINATION"


def test_no_route(toy_client):
    body = {**FORM, "depart_at": "2026-09-24T23:50:00-05:00"}
    r = toy_client.post("/api/recommendations", json=body)
    assert r.status_code == 404 and r.json()["error"]["code"] == "NO_ROUTE"


def test_requires_exactly_one_form(toy_client):
    r = toy_client.post("/api/recommendations", json={**FORM, "query": "de a a b"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_places(toy_client):
    r = toy_client.get("/api/places", params={"q": "Estación Alta"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert items and {"ref_id", "kind", "display_name", "localidad", "lat", "lng"} <= set(items[0])
