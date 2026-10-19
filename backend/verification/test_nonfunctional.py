"""Non-functional checks that run without a browser (NFR-01, NFR-06, NFR-07) on the SDD build."""
import importlib
import time
from pathlib import Path

import pytest

from helpers import future_deadline, make_task


def test_TC_NFR_01_api_responds_within_2_seconds_with_100_tasks(client, auth_headers):
    for i in range(100):
        assert make_task(client, auth_headers, title=f"t{i}", subject=f"s{i % 5}",
                         deadline=future_deadline(days=1 + i % 20)).status_code == 201
    slowest = 0.0
    for url in ("/api/tasks", "/api/tasks?sort=deadline", "/api/tasks?view=upcoming",
                "/api/dashboard", "/api/tasks?subject=s1"):
        for _ in range(10):
            start = time.perf_counter()
            assert client.get(url, headers=auth_headers).status_code == 200
            slowest = max(slowest, time.perf_counter() - start)
    print(f"slowest response: {slowest * 1000:.0f} ms")
    assert slowest < 2.0


def test_TC_NFR_06_malformed_requests_get_a_clear_error_and_server_survives(client, auth_headers):
    r = client.post("/api/tasks", content="{ this is not json",
                    headers={**auth_headers, "Content-Type": "application/json"})
    assert r.status_code in (400, 422) and r.json()["error"]["message"]  # Vibe build answered 422
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/tasks/does-not-exist", headers=auth_headers).status_code == 404


@pytest.mark.parametrize(
    "module",
    ["backend.app.routes.auth", "backend.app.routes.tasks", "backend.app.routes.dashboard",
     "backend.app.priority", "backend.app.security"],
)
def test_TC_NFR_07_major_components_are_separate_modules(module):
    assert importlib.import_module(module)


def test_TC_NFR_07b_priority_module_does_not_depend_on_the_web_layer():
    import backend.app.priority as priority
    source = Path(priority.__file__).read_text()
    assert "starlette" not in source and "sqlite3" not in source and "import db" not in source
