"""T099: contrato de /api/stops y /api/routes."""

from __future__ import annotations


def test_stops_bbox(toy_client):
    r = toy_client.get("/api/stops", params={"bbox": "-74.16,4.54,-74.13,4.57"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert items and all({"id", "name", "kind", "lat", "lng", "source_kind"} <= set(i)
                         for i in items)
    assert all(4.54 <= i["lat"] <= 4.57 for i in items)


def test_stops_kind_filter(toy_client):
    r = toy_client.get("/api/stops", params={"bbox": "-75,4,-73,5", "kind": "tm_station"})
    assert {i["kind"] for i in r.json()["items"]} == {"tm_station"}


def test_stops_bad_bbox(toy_client):
    assert toy_client.get("/api/stops", params={"bbox": "x"}).status_code == 422


def test_routes_list_and_detail(toy_client):
    r = toy_client.get("/api/routes", params={"mode": "community"})
    items = r.json()["items"]
    assert items and items[0]["source_kind"] == "demo_simulated"
    d = toy_client.get(f"/api/routes/{items[0]['id']}")
    assert d.status_code == 200
    assert d.json()["geometry"]["type"] == "LineString" and len(d.json()["stops"]) >= 2
    assert toy_client.get("/api/routes/NOPE:1").status_code == 404


def test_health(toy_client):
    h = toy_client.get("/api/health").json()
    assert h["status"] == "ok" and h["llm_provider"] == "mock"
