"""T077: contrato de POST /api/sync (lote idempotente)."""

from __future__ import annotations

import json
import uuid


def rep(**over):
    base = {"id": str(uuid.uuid4()), "anon_id": str(uuid.uuid4()), "category": "delay",
            "location": {"lat": 4.5550, "lng": -74.1450}}
    base.update(over)
    return base


def sync(client, reports, files=None):
    return client.post("/api/sync", data={"reports": json.dumps(reports)}, files=files)


def test_batch_statuses_and_idempotency(toy_client):
    good, bad = rep(), rep(category="nope")
    photo_id = good["id"]
    files = {f"photo_{photo_id}": ("f.jpg", b"\xff\xd8\xff" + b"1" * 50, "image/jpeg")}
    r = sync(toy_client, [good, bad], files)
    assert r.status_code == 200
    res = {x["id"]: x for x in r.json()["results"]}
    assert res[good["id"]]["status"] == "accepted"
    assert res[bad["id"]]["status"] == "rejected"
    assert r.json()["recalculate"] is True
    again = sync(toy_client, [good])
    assert again.json()["results"][0]["status"] == "duplicate"
    assert again.json()["recalculate"] is False
    assert len(toy_client.get("/api/reports").json()["items"]) == 1
    assert toy_client.get(f"/api/reports/{photo_id}/photo").status_code == 200


def test_batch_limit(toy_client):
    r = sync(toy_client, [rep() for _ in range(21)])
    assert r.status_code == 422


def test_requires_list(toy_client):
    r = toy_client.post("/api/sync", data={"reports": "{}"})
    assert r.status_code == 422
