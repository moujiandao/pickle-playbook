"""Smoke test: the live server is up and the health endpoint responds."""


def test_health_returns_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_openapi_schema_lists_expected_paths(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert "/api/health" in paths
    assert "/api/analyze" in paths
    assert "/api/scenarios" in paths
    assert "/api/scenarios/{scenario_id}" in paths
    assert "/api/correct" in paths
