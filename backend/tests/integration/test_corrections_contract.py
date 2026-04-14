"""Integration tests for POST /api/correct.

The corrections endpoint stores human-in-the-loop overrides for later
RAG fine-tuning. Keep these focused on the contract — the analyze
recommendations themselves are covered by `test_analyze_contract.py`.
"""

from copy import deepcopy

GAME_STATE = {
    "my_side": "left",
    "players": {
        "my_left":  {"x": 5.0,  "y": 37.0},
        "my_right": {"x": 15.0, "y": 37.0},
        "opp_left": {"x": 5.0,  "y": 7.0},
        "opp_right": {"x": 15.0, "y": 7.0},
    },
    "ball": {"x": 10.0, "y": 26.0, "height": "low", "speed": "slow", "spin": None},
}

CORRECTED = [
    {
        "name": "Manual Cross-Court Dink",
        "why": "Operator preferred this over the model's choice.",
        "rally": [
            {"shot": 1, "who": "You",      "action": "Dink crosscourt",     "result": "Lands at sideline"},
            {"shot": 2, "who": "Opponent", "action": "Stretches and dinks", "result": "Pop-up"},
            {"shot": 3, "who": "Partner",  "action": "Attack the floater",  "result": "Winner"},
        ],
    }
]


def test_create_correction_returns_201(client):
    payload = {
        "game_state": GAME_STATE,
        "corrected_response": CORRECTED,
        "note": "manual override for kitchen-low scenario",
    }
    r = client.post("/api/correct", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert isinstance(data["id"], int) and data["id"] > 0
    assert data["note"] == "manual override for kitchen-low scenario"
    assert data["game_state"] == GAME_STATE
    assert data["corrected_response"] == CORRECTED
    assert "created_at" in data


def test_create_correction_without_note(client):
    payload = {"game_state": GAME_STATE, "corrected_response": CORRECTED}
    r = client.post("/api/correct", json=payload)
    assert r.status_code == 201
    assert r.json()["note"] is None


def test_invalid_game_state_rejected(client):
    bad_state = deepcopy(GAME_STATE)
    bad_state["ball"]["y"] = 5.0  # opponent side
    r = client.post(
        "/api/correct",
        json={"game_state": bad_state, "corrected_response": CORRECTED},
    )
    assert r.status_code == 422


def test_corrected_response_must_have_rally(client):
    bad_correction = [{"name": "no rally", "why": "missing rally field"}]
    r = client.post(
        "/api/correct",
        json={"game_state": GAME_STATE, "corrected_response": bad_correction},
    )
    assert r.status_code == 422
