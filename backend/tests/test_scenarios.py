"""Tests for CRUD /api/scenarios."""

STATE = {
    "players": {
        "my_left":  {"x": 5.0,  "y": 37.0},
        "my_right": {"x": 15.0, "y": 37.0},
        "opp_left": {"x": 5.0,  "y": 7.0},
        "opp_right":{"x": 15.0, "y": 7.0},
    },
    "ball": {"x": 10.0, "y": 26.0, "height": "low", "speed": "slow", "spin": None},
    "mySide": "left",
    "result": None,
}


def test_list_empty_initially(client):
    r = client.get("/api/scenarios")
    assert r.status_code == 200
    assert r.json() == []


def test_create_returns_201(client):
    r = client.post("/api/scenarios", json={"name": "Test Setup", "state": STATE})
    assert r.status_code == 201
    data = r.json()
    assert data["id"] is not None
    assert data["name"] == "Test Setup"
    assert data["state"]["ball"]["height"] == "low"
    assert data["state"]["mySide"] == "left"
    assert "timestamp" in data


def test_list_after_create(client):
    client.post("/api/scenarios", json={"name": "S1", "state": STATE})
    client.post("/api/scenarios", json={"name": "S2", "state": STATE})
    r = client.get("/api/scenarios")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_delete_removes_scenario(client):
    r = client.post("/api/scenarios", json={"name": "To Delete", "state": STATE})
    sid = r.json()["id"]
    del_r = client.delete(f"/api/scenarios/{sid}")
    assert del_r.status_code == 204
    assert client.get("/api/scenarios").json() == []


def test_delete_nonexistent_returns_404(client):
    r = client.delete("/api/scenarios/9999")
    assert r.status_code == 404


def test_create_empty_name_rejected(client):
    r = client.post("/api/scenarios", json={"name": "", "state": STATE})
    assert r.status_code == 422
