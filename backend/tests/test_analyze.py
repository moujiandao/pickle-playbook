"""Tests for POST /api/analyze — covers all ball zones, heights, and edge cases."""

import pytest
from fastapi.testclient import TestClient

# Default valid game state — ball low in kitchen, opponents at kitchen
BASE_STATE = {
    "my_side": "left",
    "players": {
        "my_left":  {"x": 5.0,  "y": 37.0},
        "my_right": {"x": 15.0, "y": 37.0},
        "opp_left": {"x": 5.0,  "y": 7.0},
        "opp_right":{"x": 15.0, "y": 7.0},
    },
    "ball": {"x": 10.0, "y": 26.0, "height": "low", "speed": "slow", "spin": None},
}


def _state(**ball_overrides):
    state = {**BASE_STATE, "ball": {**BASE_STATE["ball"], **ball_overrides}}
    return state


def _transition_state():
    return _state(y=33.0, height="low", speed="slow")


def _baseline_state():
    return _state(y=40.0, height="low", speed="slow")


class TestAnalyzeStructure:
    def test_returns_list(self, client: TestClient):
        r = client.post("/api/analyze", json=BASE_STATE)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_at_least_one_recommendation(self, client: TestClient):
        r = client.post("/api/analyze", json=BASE_STATE)
        assert len(r.json()) >= 1

    def test_each_rec_has_required_fields(self, client: TestClient):
        recs = client.post("/api/analyze", json=BASE_STATE).json()
        for rec in recs:
            assert "name" in rec
            assert "why" in rec
            assert "rally" in rec

    def test_each_rally_has_three_steps(self, client: TestClient):
        recs = client.post("/api/analyze", json=BASE_STATE).json()
        for rec in recs:
            assert len(rec["rally"]) == 3

    def test_rally_steps_numbered_1_2_3(self, client: TestClient):
        recs = client.post("/api/analyze", json=BASE_STATE).json()
        for rec in recs:
            shots = [s["shot"] for s in rec["rally"]]
            assert shots == [1, 2, 3]

    def test_at_most_three_recommendations(self, client: TestClient):
        recs = client.post("/api/analyze", json=BASE_STATE).json()
        assert len(recs) <= 3


class TestBallZones:
    def test_kitchen_low_includes_dink(self, client: TestClient):
        recs = client.post("/api/analyze", json=_state(y=25.0, height="low")).json()
        names = [r["name"] for r in recs]
        assert any("Dink" in n for n in names)

    def test_kitchen_mid_includes_speedup(self, client: TestClient):
        # spin is allowed in kitchen zone
        recs = client.post("/api/analyze", json=_state(y=25.0, height="mid", spin=None)).json()
        names = [r["name"] for r in recs]
        assert any("Speed-Up" in n or "Topspin" in n for n in names)

    def test_kitchen_high_includes_attack(self, client: TestClient):
        recs = client.post("/api/analyze", json=_state(y=25.0, height="high")).json()
        names = [r["name"] for r in recs]
        assert any("Speed-Up" in n or "Attack" in n or "Topspin" in n for n in names)

    def test_transition_zone_includes_drop(self, client: TestClient):
        recs = client.post("/api/analyze", json=_transition_state()).json()
        names = [r["name"] for r in recs]
        assert any("Drop" in n for n in names)

    def test_baseline_includes_drop(self, client: TestClient):
        recs = client.post("/api/analyze", json=_baseline_state()).json()
        names = [r["name"] for r in recs]
        assert any("Drop" in n for n in names)

    def test_baseline_fast_adds_drive(self, client: TestClient):
        recs = client.post("/api/analyze", json=_baseline_state() | {"ball": {**_baseline_state()["ball"], "speed": "fast"}}).json()
        names = [r["name"] for r in recs]
        assert any("Drive" in n for n in names)


class TestValidation:
    def test_ball_on_opponent_side_rejected(self, client: TestClient):
        bad = _state(y=10.0)  # opponent side
        r = client.post("/api/analyze", json=bad)
        assert r.status_code == 422

    def test_my_left_x_gte_my_right_x_rejected(self, client: TestClient):
        bad = {**BASE_STATE, "players": {**BASE_STATE["players"], "my_left": {"x": 16.0, "y": 37.0}}}
        r = client.post("/api/analyze", json=bad)
        assert r.status_code == 422

    def test_spin_outside_kitchen_rejected(self, client: TestClient):
        bad = _state(y=38.0, spin="topspin")  # baseline with spin
        r = client.post("/api/analyze", json=bad)
        assert r.status_code == 422

    def test_missing_my_side_rejected(self, client: TestClient):
        bad = {k: v for k, v in BASE_STATE.items() if k != "my_side"}
        r = client.post("/api/analyze", json=bad)
        assert r.status_code == 422
