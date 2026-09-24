"""T061: regla 1 reporte parcial / 2+ confirmados, vigencia, radio y topes."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from backend.app.core import BOGOTA
from backend.app.models.report import ReportIn
from backend.app.services.route_engine.engine import Place

AT = datetime(2026, 9, 24, 7, 30, tzinfo=BOGOTA)
ORIGIN = Place("Estación Alta", 4.5500, -74.1500, is_ciudad_bolivar=True)
DEST = Place("Estación Destino", 4.5900, -74.1000)
ON_CABLE = {"lat": 4.5550, "lng": -74.1450}         # mitad del cable A1 → B1


def report(cat="blockage", anon=None, loc=ON_CABLE):
    return ReportIn(id=str(uuid.uuid4()), anon_id=anon or str(uuid.uuid4()), category=cat,
                    location=loc)


def rec(core):
    return core.engine.recommend(ORIGIN, DEST, "fast", AT, core.reports.active())


def pats(alt):
    return [x["pattern_id"] for x in alt["legs"] if x["mode"] != "walk"]


def test_single_blockage_is_partial(toy_core):
    base = rec(toy_core)["recommended"]["total_time_min"]
    toy_core.reports.upsert(report())
    r = rec(toy_core)
    cable = [a for a in [r["recommended"], *r["alternatives"]] if "P_CABLE:1" in pats(a)]
    assert cable, "con 1 reporte la ruta sigue disponible (penalización parcial)"
    assert cable[0]["total_time_min"] >= base + 15
    assert cable[0]["reliability"] < 0.85
    leg = next(x for x in cable[0]["legs"] if x["pattern_id"] == "P_CABLE:1")
    assert leg["reports"][0]["n_confirm"] == 1 and leg["reports"][0]["effect"] == "parcial"


def test_two_distinct_devices_invalidate(toy_core):
    toy_core.reports.upsert(report())
    toy_core.reports.upsert(report())
    r = rec(toy_core)
    for a in [r["recommended"], *r["alternatives"]]:
        assert "P_CABLE:1" not in pats(a)
    assert r["blocked"] and r["blocked"][0]["n_confirm"] == 2


def test_same_device_counts_once(toy_core):
    anon = str(uuid.uuid4())
    toy_core.reports.upsert(report(anon=anon))
    toy_core.reports.upsert(report(anon=anon))
    r = rec(toy_core)
    assert any("P_CABLE:1" in pats(a) for a in [r["recommended"], *r["alternatives"]])


def test_expired_report_has_no_effect(toy_core):
    toy_core.reports.upsert(report())
    toy_core.reports.upsert(report())
    later = AT + timedelta(hours=2, minutes=1)
    toy_core.reports.now = lambda: later
    assert toy_core.reports.active() == []


def test_far_report_does_not_touch_segments(toy_core):
    status, out = toy_core.reports.upsert(report(loc={"lat": 4.5300, "lng": -74.1700}))
    assert status == "accepted" and out["affected_segments"] == 0


def test_idempotent_upsert(toy_core):
    r = report()
    assert toy_core.reports.upsert(r)[0] == "accepted"
    assert toy_core.reports.upsert(r)[0] == "duplicate"
    assert len(toy_core.reports.active()) == 1


def test_delay_penalty_is_capped(toy_core):
    for _ in range(4):
        toy_core.reports.upsert(report(cat="delay"))
    r = rec(toy_core)
    cfg = toy_core.settings.engine
    for a in [r["recommended"], *r["alternatives"]]:
        assert a["total_time_min"] <= 120 + cfg["reports"]["caps"]["max_add_s"] // 60
