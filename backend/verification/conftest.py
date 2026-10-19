"""Fixtures for the independent verification suite (Member 3) on the SDD build.

Each test gets its own temporary SQLite database and a fresh app instance, so
tests never share data. Run from the repository root:

    pip install -r backend/requirements.txt pytest httpx
    pytest backend/verification -v
"""
import os
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ["STUDYFLOW_SECRET"] = "verification-suite-secret-not-used-anywhere-else"

from starlette.testclient import TestClient  # noqa: E402

from backend.app.config import get_settings  # noqa: E402
from backend.app.db import init_db  # noqa: E402
from backend.app.main import create_app  # noqa: E402

ADMIN_EMAIL = "admin123@gmail.com"      # main admin seeded by init_db (FR-25)
ADMIN_PASSWORD = "admin@123"


@pytest.fixture
def settings(tmp_path):
    s = get_settings(str(tmp_path / "verification.db"))
    init_db(s.db_path, s.main_admin_email, s.main_admin_password)
    return s


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))


@pytest.fixture
def safe_client(settings):
    """Like client, but a server crash comes back as HTTP 500 instead of a Python error."""
    return TestClient(create_app(settings), raise_server_exceptions=False)


@pytest.fixture
def db(settings):
    """Read-only look at the database (used to check how passwords are stored)."""
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def make_user(client):
    """Registers a student and returns (headers, user_json)."""

    def _make(name="Alice Student", email="alice@example.com", password="hunter2pass"):
        r = client.post("/api/auth/register", json={"name": name, "email": email, "password": password})
        assert r.status_code == 201, r.text
        body = r.json()
        return {"Authorization": f"Bearer {body['token']}"}, body["user"]

    return _make


@pytest.fixture
def auth_headers(make_user):
    headers, _ = make_user()
    return headers


@pytest.fixture
def admin_headers(client):
    r = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}
