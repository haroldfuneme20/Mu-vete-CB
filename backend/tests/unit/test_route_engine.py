"""T039: motor sobre la red de juguete."""

from __future__ import annotations

from datetime import datetime

import pytest

from backend.app.core import BOGOTA
from backend.app.services.route_engine.engine import EngineError, Place

AT = datetime(2026, 9, 24, 7, 30, tzinfo=BOGOTA)
ORIGIN = Place("Estación Alta", 4.5500, -74.1500, is_ciudad_bolivar=True)
DEST = Place("Estación Destino", 4.5900, -74.1000)


def rides(alt):
    return [leg["pattern_id"] for leg in alt["legs"] if leg["mode"] != "walk"]


def test_best_route_is_cable_plus_trunk(toy_core):
    r = toy_core.engine.recommend(ORIGIN, DEST, "fast", AT, [])
    assert rides(r["recommended"]) == ["P_CABLE:1", "P_TRUNK:1"]
    # 30 s espera + 10 min cable + caminata + 2 min espera + 5 min transbordo + 20 min troncal
    assert 38 <= r["recommended"]["total_time_min"] <= 42
    assert r["recommended"]["transfers"] == 1


def test_wait_is_half_headway(toy_core):
    r = toy_core.engine.recommend(ORIGIN, DEST, "fast", AT, [])
    legs = [x for x in r["recommended"]["legs"] if x["mode"] != "walk"]
    assert legs[0]["wait_min"] == 1          # 60 s × 0,5 = 30 s → redondea a 1 min
    assert legs[1]["wait_min"] == 7          # 240 s × 0,5 + 300 s de transbordo = 7 min


def test_returns_distinct_alternatives_up_to_three(toy_core):
    r = toy_core.engine.recommend(ORIGIN, DEST, "fast", AT, [])
    alts = [r["recommended"], *r["alternatives"]]
    assert 2 <= len(alts) <= 3
    assert len({a["id"] for a in alts}) == len(alts)
    assert any(rides(a) == ["P_ZONAL:1"] for a in alts)


def test_max_two_transfers(toy_core):
    r = toy_core.engine.recommend(ORIGIN, DEST, "balanced", AT, [])
    for a in [r["recommended"], *r["alternatives"]]:
        assert a["transfers"] <= toy_core.settings.engine["transfers"]["max"]


def test_walk_access_limit(toy_core):
    far = Place("Lejos", 4.5300, -74.1700, is_ciudad_bolivar=True)
    with pytest.raises(EngineError) as e:
        toy_core.engine.recommend(far, DEST, "fast", AT, [])
    assert e.value.code == "NO_ROUTE"


def test_out_of_service_hours(toy_core):
    night = datetime(2026, 9, 24, 23, 45, tzinfo=BOGOTA)
    with pytest.raises(EngineError) as e:
        toy_core.engine.recommend(ORIGIN, DEST, "fast", night, [])
    assert e.value.code == "NO_ROUTE"


def test_out_of_coverage(toy_core):
    a = Place("Fuera 1", 4.5900, -74.1000)
    b = Place("Fuera 2", 4.5750, -74.1200)
    with pytest.raises(EngineError) as e:
        toy_core.engine.recommend(a, b, "fast", AT, [])
    assert e.value.code == "OUT_OF_COVERAGE"


def test_same_origin_destination(toy_core):
    with pytest.raises(EngineError) as e:
        toy_core.engine.recommend(ORIGIN, ORIGIN, "fast", AT, [])
    assert e.value.code == "SAME_ORIGIN_DESTINATION"


def test_deterministic(toy_core):
    runs = [toy_core.engine.recommend(ORIGIN, DEST, "balanced", AT, []) for _ in range(3)]
    ids = [[a["id"] for a in [r["recommended"], *r["alternatives"]]] for r in runs]
    assert ids[0] == ids[1] == ids[2]


def test_every_leg_has_source_kind_and_community_is_marked(toy_core):
    r = toy_core.engine.recommend(ORIGIN, DEST, "cheap", AT, [])
    for a in [r["recommended"], *r["alternatives"]]:
        for leg in a["legs"]:
            assert leg["source_kind"] in {"institutional", "community", "territorial",
                                          "demo_simulated"}
            if leg["mode"] == "community":
                assert leg["source_kind"] == "demo_simulated"
                assert "simulada para la demo" in a["text_description"]
