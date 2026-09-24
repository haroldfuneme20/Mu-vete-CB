"""T062: contrato de reportes."""

from __future__ import annotations

import json
import uuid

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 100


def rep(**over):
    base = {"id": str(uuid.uuid4()), "anon_id": str(uuid.uuid4()), "category": "blockage",
            "location": {"lat": 4.5550, "lng": -74.1450}, "description": "Vía cerrada"}
    base.update(over)
    return base


def post(client, report, photo=None):
    files = {"photo": ("f.jpg", photo, "image/jpeg")} if photo is not None else None
    return client.post("/api/reports", data={"report": json.dumps(report)}, files=files)


def test_create_then_duplicate(toy_client):
    r = rep()
    a = post(toy_client, r)
    assert a.status_code == 201 and a.json()["status"] == "accepted"
    assert a.json()["affected_segments"] >= 1 and a.json()["confirmations"] == 1
    b = post(toy_client, r)
    assert b.status_code == 200 and b.json()["status"] == "duplicate"


def test_photo_ok_and_served(toy_client):
    r = rep()
    assert post(toy_client, r, JPEG).status_code == 201
    got = toy_client.get(f"/api/reports/{r['id']}/photo")
    assert got.status_code == 200 and got.headers["content-type"] == "image/jpeg"


def test_photo_too_large(toy_client):
    big = b"\xff\xd8" + b"0" * (1024 * 1024 + 10)
    r = post(toy_client, rep(), big)
    assert r.status_code == 413 and r.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_missing_location_or_category(toy_client):
    bad = rep()
    del bad["location"]
    assert post(toy_client, bad).status_code == 422
    bad = rep(category="inventada")
    assert post(toy_client, bad).status_code == 422


def test_description_limit(toy_client):
    assert post(toy_client, rep(description="x" * 281)).status_code == 422


def test_list_never_exposes_anon_id(toy_client):
    post(toy_client, rep())
    items = toy_client.get("/api/reports").json()["items"]
    assert items and all("anon_id" not in i for i in items)
    assert {"id", "category", "lat", "lng", "received_at", "expires_at", "confirmations",
            "has_photo"} <= set(items[0])


def test_photo_404(toy_client):
    assert toy_client.get(f"/api/reports/{uuid.uuid4()}/photo").status_code == 404
