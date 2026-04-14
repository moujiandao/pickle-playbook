"""Integration test fixtures.

These tests spin up a *real* uvicorn subprocess with an isolated SQLite
database and hit the live HTTP endpoints. No mocks. The server runs for
the whole test session and is torn down on exit.

The strategy engine falls back to its deterministic heuristic when
ANTHROPIC_API_KEY is not set, so the fixture explicitly clears the key
to keep the analyze contract reproducible across machines.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterator

import httpx
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]
STARTUP_TIMEOUT_SECONDS = 20


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_health(base_url: str, proc: subprocess.Popen) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            output = ""
            if proc.stdout is not None:
                output = proc.stdout.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"uvicorn exited with code {proc.returncode} during startup\n"
                f"--- server output ---\n{output}"
            )
        try:
            r = httpx.get(f"{base_url}/api/health", timeout=1.0)
            if r.status_code == 200:
                return
        except httpx.HTTPError as exc:
            last_err = exc
        time.sleep(0.15)
    proc.terminate()
    raise RuntimeError(
        f"server at {base_url} did not become healthy within "
        f"{STARTUP_TIMEOUT_SECONDS}s (last error: {last_err})"
    )


@pytest.fixture(scope="session")
def live_server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Spawn a real uvicorn subprocess; yield its base URL."""
    port = _free_port()
    db_path = tmp_path_factory.mktemp("integration_db") / "pickle.db"

    env = os.environ.copy()
    env["PICKLE_DATABASE_URL"] = f"sqlite:///{db_path}"
    # Force the deterministic heuristic path — the analyze contract tests
    # assert response *shape*, and we don't want them to depend on a live
    # Claude key (or burn one when CI runs).
    env.pop("ANTHROPIC_API_KEY", None)
    # Make sure the backend's app module is importable by uvicorn.
    env["PYTHONPATH"] = str(BACKEND_DIR)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_health(base_url, proc)
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


@pytest.fixture
def client(live_server: str) -> Iterator[httpx.Client]:
    """Per-test httpx client pointed at the live server."""
    with httpx.Client(base_url=live_server, timeout=10.0) as c:
        yield c


@pytest.fixture(autouse=True)
def _isolate_scenarios(client: httpx.Client) -> Iterator[None]:
    """Wipe the scenarios table before each test for isolation.

    The session-scoped server shares a single SQLite file across the
    whole run, so individual tests must not see each other's writes.
    """
    existing = client.get("/api/scenarios")
    if existing.status_code == 200:
        for row in existing.json():
            client.delete(f"/api/scenarios/{row['id']}")
    yield
