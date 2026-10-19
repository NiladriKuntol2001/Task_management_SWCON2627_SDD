"""Security and data-isolation tests (FR-21, NFR-03..NFR-06) on the SDD build.
User A owns tasks; user B (another student) tries to reach them. Same IDs as on the
Vibe Coding build. TC-SEC-10 (static scan with bandit and pip-audit) runs in CI.
"""
import re
from pathlib import Path

import pytest

from helpers import complete, dashboard, edit_task, future_deadline, make_task, tasks, titles

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"


@pytest.fixture
def two_users(make_user):
    a_headers, a = make_user(name="Alice", email="alice@example.com")
    b_headers, b = make_user(name="Bob", email="bob@example.com")
    return a_headers, a, b_headers, b


def _a_task(client, a_headers):
    return make_task(client, a_headers, title="A-secret", subject="A-subject").json()


# ------------------ Data isolation: user B against A's task -----------------
def test_TC_SEC_01_other_user_cannot_read_a_task(client, two_users):
    a_h, _, b_h, _ = two_users
    t = _a_task(client, a_h)
    assert client.get(f"/api/tasks/{t['id']}", headers=b_h).status_code == 404


def test_TC_SEC_02_other_user_cannot_edit_a_task(client, two_users):
    a_h, _, b_h, _ = two_users
    t = _a_task(client, a_h)
    assert edit_task(client, b_h, t, title="hacked").status_code == 404
    assert client.get(f"/api/tasks/{t['id']}", headers=a_h).json()["title"] == "A-secret"


def test_TC_SEC_03_other_user_cannot_delete_a_task(client, two_users):
    a_h, _, b_h, _ = two_users
    t = _a_task(client, a_h)
    assert client.delete(f"/api/tasks/{t['id']}", headers=b_h).status_code == 404
    assert client.get(f"/api/tasks/{t['id']}", headers=a_h).status_code == 200


def test_TC_SEC_04_other_user_cannot_complete_a_task(client, two_users):
    a_h, _, b_h, _ = two_users
    t = _a_task(client, a_h)
    assert complete(client, b_h, t["id"]).status_code == 404
    assert client.get(f"/api/tasks/{t['id']}", headers=a_h).json()["completed"] is False


def test_TC_SEC_04b_foreign_and_nonexistent_tasks_look_identical(client, two_users):
    a_h, _, b_h, _ = two_users
    t = _a_task(client, a_h)
    foreign = client.get(f"/api/tasks/{t['id']}", headers=b_h)
    missing = client.get("/api/tasks/999999", headers=b_h)
    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json()


def test_TC_SEC_05_no_listing_ever_contains_another_users_tasks(client, two_users):
    a_h, _, b_h, _ = two_users
    make_task(client, a_h, title="A-secret", subject="A-subject", deadline=future_deadline(hours=5))
    make_task(client, b_h, title="B-own", subject="B-subject")
    for query in ("", "?subject=A-subject", "?status=all", "?status=completed",
                  "?view=overdue", "?view=upcoming", "?sort=deadline"):
        text = client.get(f"/api/tasks{query}", headers=b_h).text  # also contains the subject list
        assert "A-secret" not in text and "A-subject" not in text, query
    dash = dashboard(client, b_h)
    assert dash["recommendation"]["title"] == "B-own"  # not A's more urgent task
    assert "A-secret" not in str(dash)


def test_TC_SEC_06_owner_cannot_be_forged_in_the_request_body(client, two_users):
    a_h, a, b_h, b = two_users
    created = make_task(client, b_h, owner_id=a["id"], userId=a["id"]).json()
    assert created["owner_id"] == b["id"]
    t = _a_task(client, a_h)
    edit_task(client, a_h, t, owner_id=b["id"])
    assert client.get(f"/api/tasks/{t['id']}", headers=a_h).json()["owner_id"] == a["id"]


# --------------------------- Injection and XSS -------------------------------
def test_TC_SEC_07_sql_injection_in_login_is_rejected(client, make_user):
    make_user(email="victim@example.com", password="abcd1234")
    for email in ("' OR 1=1 --", "victim@example.com' --"):
        r = client.post("/api/auth/login", json={"email": email, "password": "x"})
        assert r.status_code in (401, 422) and "token" not in r.json()
    r = client.post("/api/auth/login", json={"email": {"$ne": None}, "password": {"$ne": None}})
    assert r.status_code in (401, 422) and "token" not in r.json()  # Vibe build answered 422


def test_TC_SEC_07b_sql_injection_in_filters_and_text_fields(client, two_users):
    a_h, _, b_h, _ = two_users
    _a_task(client, a_h)
    leaked = client.get("/api/tasks", params={"subject": "x' OR '1'='1", "q": "' OR 1=1 --"}, headers=b_h)
    assert leaked.status_code == 200 and leaked.json()["tasks"] == []
    nasty = "'); DROP TABLE tasks; --"
    assert make_task(client, b_h, title=nasty, subject=nasty).status_code == 201
    assert titles(tasks(client, b_h)) == [nasty]  # table intact, stored as text
    assert titles(tasks(client, a_h)) == ["A-secret"]


def test_TC_SEC_08_script_in_task_text_is_returned_as_inert_json(client, auth_headers):
    payload = "<script>alert(1)</script>"
    assert make_task(client, auth_headers, title=payload, subject="<img src=x onerror=alert(1)>").status_code == 201
    listing = client.get("/api/tasks", headers=auth_headers)
    assert listing.headers["content-type"].startswith("application/json")
    assert listing.json()["tasks"][0]["title"] == payload  # stored verbatim; escaping is the UI's job


# Every innerHTML in the frontend was read by hand (Member 3, 19 Oct 2026): both build SVG
# icons from constants and a server-computed number, never user text. Any new use fails
# this test until it has been reviewed and added here.
REVIEWED_INNER_HTML = {("ui.js", "PATHS[name]"), ("ui.js", "Priority score ${score} out of 100")}


def test_TC_SEC_08b_frontend_never_injects_raw_html():
    js = FRONTEND / "js"
    if not js.exists():
        pytest.skip("frontend sources not present")
    found = set()
    for path in js.rglob("*.js"):
        text = path.read_text()
        for m in re.finditer(r"\.(innerHTML|outerHTML)\s*=|insertAdjacentHTML\(", text):
            snippet = text[m.end(): text.find("\n", text.find("\n", m.end()) + 1)]
            key = next(((path.name, k) for (f, k) in REVIEWED_INNER_HTML if f == path.name and k in snippet),
                       (path.name, snippet.strip()[:60]))
            found.add(key)
    assert found <= REVIEWED_INNER_HTML, f"unreviewed raw-HTML insertion: {found - REVIEWED_INNER_HTML}"


# ----------------------- Passwords and account handling ----------------------
def test_TC_SEC_09_passwords_are_hashed_and_never_returned(client, db, make_user):
    headers, _ = make_user(email="h@example.com", password="Sup3rSecret!")
    stored = db.execute("SELECT password_hash FROM users WHERE email = 'h@example.com'").fetchone()[0]
    assert stored != "Sup3rSecret!" and stored.startswith("scrypt$")  # salted scrypt (research.md R3)
    for url in ("/api/me", "/api/dashboard", "/api/tasks"):
        text = client.get(url, headers=headers).text
        assert "Sup3rSecret!" not in text and "password_hash" not in text and stored not in text


def test_TC_SEC_09b_same_password_gives_different_hashes(client, db, make_user):
    make_user(email="one@example.com", password="samepass1")
    make_user(email="two@example.com", password="samepass1")
    rows = db.execute("SELECT password_hash FROM users WHERE email IN ('one@example.com', 'two@example.com')")
    assert len({r[0] for r in rows}) == 2  # salted


# ------------------------------ Admin role -----------------------------------
@pytest.mark.parametrize("extra", [{"role": "admin"}, {"is_admin": True}])
def test_TC_SEC_11_registration_cannot_create_an_admin(client, extra):
    r = client.post("/api/auth/register", json={"name": "Eve", "email": "eve@example.com",
                                                "password": "abcd1234", **extra})
    assert r.status_code == 201 and r.json()["user"]["role"] == "student"


@pytest.mark.parametrize("path", ["/api/admin/users", "/api/admin/tasks", "/api/admin/overview"])
def test_TC_SEC_12_students_cannot_use_admin_routes(client, auth_headers, path):
    assert client.get(path).status_code == 401
    assert client.get(path, headers=auth_headers).status_code == 403


def test_TC_SEC_13_admin_responses_never_expose_password_hashes(client, admin_headers, make_user):
    make_user(name="S", email="s@example.com")
    for path in ("/api/admin/users", "/api/admin/tasks", "/api/admin/overview"):
        text = client.get(path, headers=admin_headers).text
        assert "password_hash" not in text and "scrypt$" not in text, path


def test_TC_SEC_14_deactivated_user_loses_access(client, make_user, admin_headers):
    headers, user = make_user(email="gone@example.com", password="abcd1234")
    r = client.patch(f"/api/admin/users/{user['id']}", json={"is_active": False}, headers=admin_headers)
    assert r.status_code == 200
    assert client.get("/api/tasks", headers=headers).status_code in (401, 403)  # Vibe build: 403
    assert client.post("/api/auth/login", json={"email": "gone@example.com", "password": "abcd1234"}).status_code == 403
