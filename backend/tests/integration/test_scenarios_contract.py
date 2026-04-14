"""Integration tests for /api/scenarios CRUD.

Real HTTP, real SQLite (per-session temp file). Asserts the response
shape consumed by the React `useScenarios` hook and verifies that data
written by POST is visible via GET (round-trip).
"""

import time
from copy import deepcopy

VALID_STATE_PAYLOAD = {
    "players": {
        "my_left":  {"x": 5.0,  "y": 37.0},
        "my_right": {"x": 15.0, "y": 37.0},
        "opp_left": {"x": 5.0,  "y": 7.0},
        "opp_right": {"x": 15.0, "y": 7.0},
    },
    "ball": {"x": 10.0, "y": 26.0, "height": "low", "speed": "slow", "spin": None},
    "mySide": "left",
    "result": None,
}


def _payload(name: str, state: dict | None = None) -> dict:
    return {"name": name, "state": state or deepcopy(VALID_STATE_PAYLOAD)}


class TestList:
    def test_list_starts_empty(self, client):
        r = client.get("/api/scenarios")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_returns_most_recent_first(self, client):
        for name in ("first", "second", "third"):
            r = client.post("/api/scenarios", json=_payload(name))
            assert r.status_code == 201
            # Ensure created_at differs even on fast machines.
            time.sleep(0.005)

        listed = client.get("/api/scenarios").json()
        assert [s["name"] for s in listed] == ["third", "second", "first"]


class TestCreate:
    def test_create_returns_201_with_assigned_fields(self, client):
        r = client.post("/api/scenarios", json=_payload("kitchen low"))
        assert r.status_code == 201
        data = r.json()
        assert isinstance(data["id"], int) and data["id"] > 0
        assert data["name"] == "kitchen low"
        assert "timestamp" in data and isinstance(data["timestamp"], str)

    def test_create_response_state_matches_input(self, client):
        r = client.post("/api/scenarios", json=_payload("round trip"))
        data = r.json()
        assert data["state"] == VALID_STATE_PAYLOAD

    def test_response_uses_frontend_field_names(self, client):
        r = client.post("/api/scenarios", json=_payload("naming"))
        data = r.json()
        # Frontend hook reads sc.state, sc.timestamp, sc.state.mySide
        assert "state" in data
        assert "timestamp" in data
        assert "mySide" in data["state"]
        # Backend internals must not leak into the wire format
        assert "game_state" not in data
        assert "created_at" not in data
        assert "state_json" not in data

    def test_create_with_result_field_round_trips(self, client):
        analysis = client.post(
            "/api/analyze",
            json={
                "my_side": VALID_STATE_PAYLOAD["mySide"],
                "players": VALID_STATE_PAYLOAD["players"],
                "ball": VALID_STATE_PAYLOAD["ball"],
            },
        ).json()

        state = deepcopy(VALID_STATE_PAYLOAD)
        state["result"] = analysis

        r = client.post("/api/scenarios", json=_payload("with result", state))
        assert r.status_code == 201
        data = r.json()
        assert data["state"]["result"] == analysis

    def test_empty_name_rejected(self, client):
        r = client.post("/api/scenarios", json=_payload(""))
        assert r.status_code == 422

    def test_name_too_long_rejected(self, client):
        r = client.post("/api/scenarios", json=_payload("x" * 201))
        assert r.status_code == 422

    def test_invalid_state_rejected(self, client):
        bad = deepcopy(VALID_STATE_PAYLOAD)
        bad["ball"]["y"] = 5.0  # opponent side — Ball validator should reject
        r = client.post("/api/scenarios", json={"name": "bad", "state": bad})
        assert r.status_code == 422

    def test_missing_state_rejected(self, client):
        r = client.post("/api/scenarios", json={"name": "no state"})
        assert r.status_code == 422


class TestRoundTrip:
    """Data written via POST must be visible via GET, byte-for-byte."""

    def test_get_after_post_returns_same_record(self, client):
        posted = client.post("/api/scenarios", json=_payload("alpha")).json()
        listed = client.get("/api/scenarios").json()

        assert len(listed) == 1
        record = listed[0]
        assert record["id"] == posted["id"]
        assert record["name"] == posted["name"]
        assert record["state"] == posted["state"]
        assert record["timestamp"] == posted["timestamp"]

    def test_multiple_round_trip(self, client):
        names = ["alpha", "beta", "gamma"]
        ids = []
        for n in names:
            posted = client.post("/api/scenarios", json=_payload(n)).json()
            ids.append(posted["id"])
            time.sleep(0.005)

        listed = client.get("/api/scenarios").json()
        assert sorted(s["id"] for s in listed) == sorted(ids)
        assert sorted(s["name"] for s in listed) == sorted(names)


class TestDelete:
    def test_delete_removes_scenario(self, client):
        sid = client.post("/api/scenarios", json=_payload("doomed")).json()["id"]
        r = client.delete(f"/api/scenarios/{sid}")
        assert r.status_code == 204
        assert client.get("/api/scenarios").json() == []

    def test_delete_unknown_returns_404(self, client):
        r = client.delete("/api/scenarios/999999")
        assert r.status_code == 404

    def test_delete_then_recreate_returns_new_record(self, client):
        first = client.post("/api/scenarios", json=_payload("v1")).json()
        client.delete(f"/api/scenarios/{first['id']}")
        second = client.post("/api/scenarios", json=_payload("v2")).json()

        # SQLite INTEGER PRIMARY KEY recycles rowids, so the id may match;
        # what we *do* require is that the live record reflects the new
        # content, not the deleted one.
        listed = client.get("/api/scenarios").json()
        assert len(listed) == 1
        assert listed[0]["name"] == "v2"
        assert listed[0]["id"] == second["id"]

    def test_delete_is_idempotent_for_already_deleted(self, client):
        sid = client.post("/api/scenarios", json=_payload("once")).json()["id"]
        first = client.delete(f"/api/scenarios/{sid}")
        assert first.status_code == 204
        second = client.delete(f"/api/scenarios/{sid}")
        assert second.status_code == 404
