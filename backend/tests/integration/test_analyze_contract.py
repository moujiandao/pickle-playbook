"""Integration tests for POST /api/analyze.

Asserts the *contract* advertised in CLAUDE.md: a list of recommendations,
each with name/why/rally, where rally has exactly 3 numbered steps. Exercises
the live FastAPI server end-to-end (real HTTP, real Pydantic validation,
real strategy engine on the heuristic fallback path).
"""

from copy import deepcopy

import pytest

VALID_STATE = {
    "my_side": "left",
    "players": {
        "my_left":  {"x": 5.0,  "y": 37.0},
        "my_right": {"x": 15.0, "y": 37.0},
        "opp_left": {"x": 5.0,  "y": 7.0},
        "opp_right": {"x": 15.0, "y": 7.0},
    },
    "ball": {"x": 10.0, "y": 26.0, "height": "low", "speed": "slow", "spin": None},
    "skill_level": "4.0",
}


def _state(**ball_overrides) -> dict:
    s = deepcopy(VALID_STATE)
    s["ball"].update(ball_overrides)
    return s


class TestResponseShape:
    def test_returns_200_and_list(self, client):
        r = client.post("/api/analyze", json=VALID_STATE)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_at_least_one_recommendation(self, client):
        recs = client.post("/api/analyze", json=VALID_STATE).json()
        assert len(recs) >= 1

    def test_at_most_three_recommendations(self, client):
        recs = client.post("/api/analyze", json=VALID_STATE).json()
        assert len(recs) <= 3

    def test_each_recommendation_has_required_fields(self, client):
        recs = client.post("/api/analyze", json=VALID_STATE).json()
        for rec in recs:
            assert isinstance(rec.get("name"), str) and rec["name"]
            assert isinstance(rec.get("why"), str) and rec["why"]
            assert isinstance(rec.get("rally"), list)

    def test_each_rally_has_exactly_three_steps(self, client):
        recs = client.post("/api/analyze", json=VALID_STATE).json()
        for rec in recs:
            assert len(rec["rally"]) == 3

    def test_rally_steps_are_numbered_1_2_3(self, client):
        recs = client.post("/api/analyze", json=VALID_STATE).json()
        for rec in recs:
            assert [step["shot"] for step in rec["rally"]] == [1, 2, 3]

    def test_each_rally_step_has_required_fields(self, client):
        recs = client.post("/api/analyze", json=VALID_STATE).json()
        for rec in recs:
            for step in rec["rally"]:
                assert isinstance(step.get("who"), str) and step["who"]
                assert isinstance(step.get("action"), str) and step["action"]
                assert isinstance(step.get("result"), str) and step["result"]


class TestZoneCoverage:
    """The endpoint must produce something sensible for every valid ball zone."""

    @pytest.mark.parametrize(
        "ball",
        [
            {"y": 26.0, "height": "low",  "speed": "slow"},   # kitchen low
            {"y": 26.0, "height": "mid",  "speed": "slow"},   # kitchen mid
            {"y": 26.0, "height": "high", "speed": "slow"},   # kitchen high
            {"y": 33.0, "height": "low",  "speed": "slow"},   # transition
            {"y": 40.0, "height": "low",  "speed": "slow"},   # baseline slow
            {"y": 40.0, "height": "low",  "speed": "fast"},   # baseline fast
        ],
    )
    def test_returns_recommendations_for_every_zone(self, client, ball):
        recs = client.post("/api/analyze", json=_state(**ball)).json()
        assert isinstance(recs, list)
        assert len(recs) >= 1
        for rec in recs:
            assert len(rec["rally"]) == 3


class TestValidation:
    """Pydantic validators reject bad payloads with 422."""

    def test_ball_on_opponent_side_rejected(self, client):
        r = client.post("/api/analyze", json=_state(y=10.0))
        assert r.status_code == 422

    def test_left_player_must_be_left_of_right_player(self, client):
        bad = deepcopy(VALID_STATE)
        bad["players"]["my_left"] = {"x": 16.0, "y": 37.0}
        r = client.post("/api/analyze", json=bad)
        assert r.status_code == 422

    def test_my_team_cannot_cross_net(self, client):
        bad = deepcopy(VALID_STATE)
        bad["players"]["my_left"] = {"x": 5.0, "y": 10.0}  # on opponent side
        r = client.post("/api/analyze", json=bad)
        assert r.status_code == 422

    def test_opp_team_cannot_cross_net(self, client):
        bad = deepcopy(VALID_STATE)
        bad["players"]["opp_left"] = {"x": 5.0, "y": 30.0}  # on our side
        r = client.post("/api/analyze", json=bad)
        assert r.status_code == 422

    def test_spin_outside_kitchen_rejected(self, client):
        r = client.post("/api/analyze", json=_state(y=38.0, spin="topspin"))
        assert r.status_code == 422

    def test_spin_inside_kitchen_accepted(self, client):
        r = client.post("/api/analyze", json=_state(y=26.0, spin="topspin"))
        assert r.status_code == 200

    def test_missing_my_side_rejected(self, client):
        bad = {k: v for k, v in VALID_STATE.items() if k != "my_side"}
        r = client.post("/api/analyze", json=bad)
        assert r.status_code == 422

    def test_invalid_height_rejected(self, client):
        r = client.post("/api/analyze", json=_state(height="medium"))
        assert r.status_code == 422

    def test_invalid_speed_rejected(self, client):
        r = client.post("/api/analyze", json=_state(speed="medium"))
        assert r.status_code == 422

    def test_x_out_of_bounds_rejected(self, client):
        bad = _state()
        bad["ball"]["x"] = 25.0
        r = client.post("/api/analyze", json=bad)
        assert r.status_code == 422

    def test_missing_skill_level_rejected(self, client):
        bad = {k: v for k, v in VALID_STATE.items() if k != "skill_level"}
        r = client.post("/api/analyze", json=bad)
        assert r.status_code == 422

    def test_invalid_skill_level_rejected(self, client):
        bad = deepcopy(VALID_STATE)
        bad["skill_level"] = "6.0"
        r = client.post("/api/analyze", json=bad)
        assert r.status_code == 422


class TestCors:
    """The frontend dev server origin must be allowed."""

    def test_dev_origin_allowed(self, client):
        r = client.request(
            "OPTIONS",
            "/api/analyze",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert r.status_code == 200
        assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_unknown_origin_rejected(self, client):
        r = client.request(
            "OPTIONS",
            "/api/analyze",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert r.status_code == 400
