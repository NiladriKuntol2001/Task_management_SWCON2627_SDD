"""Independent API tests derived from the acceptance criteria (Spec sections 6.1-6.18),
run on the SDD build (StudyFlow). Same test IDs as on the Vibe Coding build, so the
two builds can be compared case by case in the traceability matrix.

Adaptations to this build's interface (the intent of each case is unchanged):
API under /api; token in "token"; tasks listed as {"tasks": [...]}; editing is a full
PUT; completing is PATCH /tasks/{id}/complete with {"completed": true|false};
upcoming and overdue lists are ?view=upcoming / ?view=overdue; status filter is
?status=active|completed|all; errors are {"error": {"message", "fields"}}.
"""
import jwt
import pytest

from helpers import (
    complete, dashboard, edit_task, fields, future_deadline, level, make_task,
    past_deadline, score, task_body, tasks, titles,
)

PROTECTED = [
    ("GET", "/api/tasks"), ("POST", "/api/tasks"), ("GET", "/api/tasks?view=upcoming"),
    ("GET", "/api/tasks/1"), ("PUT", "/api/tasks/1"), ("DELETE", "/api/tasks/1"),
    ("PATCH", "/api/tasks/1/complete"), ("GET", "/api/dashboard"),
    ("GET", "/api/me"), ("POST", "/api/auth/logout"), ("POST", "/api/priority/preview"),
]


# ============================ Authentication ================================
def test_TC_AUTH_01_register_valid_returns_token_and_hides_password(client):
    r = client.post("/api/auth/register", json={"name": "Ann", "email": "ann@example.com", "password": "abcd1234"})
    assert r.status_code == 201
    body = r.json()
    assert body["token"] and body["user"]["email"] == "ann@example.com"
    assert "password" not in r.text.lower()


@pytest.mark.parametrize(
    "payload",
    [{"name": "", "email": "a@example.com", "password": "abcd1234"},
     {"name": "   ", "email": "a@example.com", "password": "abcd1234"}],
    ids=["empty-name", "blank-name"],
)
def test_TC_AUTH_02_registration_rejects_empty_name(client, payload):
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 422 and fields(r) == {"name"}


@pytest.mark.parametrize(
    "payload",
    [{"name": "A", "password": "abcd1234"},
     {"name": "A", "email": "a@example.com"},
     {"name": "A", "email": "not-an-email", "password": "abcd1234"},
     {"name": "A", "email": "a@example.com", "password": "short"}],
    ids=["no-email", "no-password", "bad-email", "short-password"],
)
def test_TC_AUTH_03_registration_rejects_missing_or_invalid_fields(client, payload):
    assert client.post("/api/auth/register", json=payload).status_code == 422


def test_TC_AUTH_04_duplicate_email_rejected(client, make_user):
    make_user(email="dup@example.com")
    r = client.post("/api/auth/register", json={"name": "B", "email": "dup@example.com", "password": "abcd1234"})
    assert r.status_code == 409


def test_TC_AUTH_04b_duplicate_email_is_case_insensitive(client, make_user):
    """Team decision D4 (was DEF-02 on the Vibe build)."""
    make_user(email="dup@example.com")
    r = client.post("/api/auth/register", json={"name": "B", "email": "DUP@example.com", "password": "abcd1234"})
    assert r.status_code == 409


def test_TC_AUTH_05_login_with_correct_credentials(client, make_user):
    make_user(email="l@example.com", password="abcd1234")
    r = client.post("/api/auth/login", json={"email": "l@example.com", "password": "abcd1234"})
    assert r.status_code == 200 and r.json()["token"]


def test_TC_AUTH_06_wrong_password_and_unknown_email_give_the_same_error(client, make_user):
    make_user(email="l@example.com", password="abcd1234")
    wrong = client.post("/api/auth/login", json={"email": "l@example.com", "password": "nope-nope"})
    unknown = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "abcd1234"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


@pytest.mark.parametrize("method, path", PROTECTED)
def test_TC_AUTH_07_protected_routes_need_a_token(client, method, path):
    assert client.request(method, path).status_code == 401


def test_TC_AUTH_08_invalid_expired_and_forged_tokens_rejected(client, settings, make_user):
    headers, user = make_user()
    real = headers["Authorization"].split()[1]
    key = settings.secret_key
    expired = jwt.encode({"sub": str(user["id"]), "jti": "x1", "exp": 1}, key, algorithm="HS256")
    unknown_user = jwt.encode({"sub": "99999", "jti": "x2", "exp": 4102444800}, key, algorithm="HS256")
    wrong_key = jwt.encode({"sub": str(user["id"]), "jti": "x3", "exp": 4102444800}, "not-the-key", algorithm="HS256")
    tampered = real[:-3] + ("AAA" if not real.endswith("AAA") else "BBB")
    unsigned = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0." + real.split(".")[1] + "."
    for token in (expired, unknown_user, wrong_key, tampered, unsigned, "garbage"):
        r = client.get("/api/tasks", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401, token


def test_TC_AUTH_09_logout_endpoint_accepts_an_authenticated_user(client, auth_headers):
    assert client.post("/api/auth/logout", headers=auth_headers).status_code == 204


def test_TC_AUTH_09b_token_no_longer_works_after_logout(client, auth_headers):
    """Extra case for this build: it revokes the token on logout (FR-03)."""
    client.post("/api/auth/logout", headers=auth_headers)
    assert client.get("/api/tasks", headers=auth_headers).status_code == 401


def test_TC_AUTH_10_long_password_does_not_crash(client):
    pw = "x" * 100 + "1"
    r = client.post("/api/auth/register", json={"name": "L", "email": "long@example.com", "password": pw})
    assert r.status_code == 201
    assert client.post("/api/auth/login", json={"email": "long@example.com", "password": pw}).status_code == 200


# ========================= Task management / validation =====================
def test_TC_TASK_01_create_task_stores_all_fields_and_a_priority(client, auth_headers):
    r = make_task(client, auth_headers, title="Essay", subject="History", difficulty="Hard", hours=3)
    assert r.status_code == 201
    t = r.json()
    assert (t["title"], t["subject"], t["difficulty"], t["estimated_hours"]) == ("Essay", "History", "Hard", 3)
    assert t["completed"] is False and 0 <= score(t) <= 100 and level(t)
    assert tasks(client, auth_headers)[0]["id"] == t["id"]


@pytest.mark.parametrize("title", ["", "   ", "x" * 201], ids=["empty", "blank", "201-chars"])
def test_TC_TASK_02_invalid_title_rejected_and_not_stored(client, auth_headers, title):
    assert make_task(client, auth_headers, title=title).status_code == 422
    assert tasks(client, auth_headers, "?status=all") == []


@pytest.mark.parametrize("subject", ["", "   "])
def test_TC_TASK_03_empty_subject_rejected(client, auth_headers, subject):
    assert make_task(client, auth_headers, subject=subject).status_code == 422
    assert tasks(client, auth_headers, "?status=all") == []


@pytest.mark.parametrize("deadline", ["not-a-date", "", None, "2026-13-45"])
def test_TC_TASK_04_invalid_or_missing_deadline_rejected(client, auth_headers, deadline):
    body = {"title": "T", "subject": "S", "difficulty": "Easy", "estimated_hours": 1}
    if deadline is not None:
        body["deadline"] = deadline
    assert client.post("/api/tasks", json=body, headers=auth_headers).status_code == 422


@pytest.mark.parametrize("hours", [0, -1, -0.5, "abc", None])
def test_TC_TASK_05_estimated_hours_must_be_positive(client, auth_headers, hours):
    assert make_task(client, auth_headers, hours=hours).status_code == 422


def test_TC_TASK_05b_smallest_positive_hours_accepted(client, auth_headers):
    assert make_task(client, auth_headers, hours=0.1).status_code == 201


@pytest.mark.parametrize("difficulty", ["Extreme", "", "easy", 3, None])
def test_TC_TASK_06_invalid_difficulty_rejected(client, auth_headers, difficulty):
    assert make_task(client, auth_headers, difficulty=difficulty).status_code == 422


@pytest.mark.parametrize("difficulty", ["Easy", "Medium", "Hard", "Very Hard"])
def test_TC_TASK_06b_all_predefined_difficulties_accepted(client, auth_headers, difficulty):
    assert make_task(client, auth_headers, difficulty=difficulty).status_code == 201


def test_TC_TASK_07_edit_own_task_is_saved(client, auth_headers):
    t = make_task(client, auth_headers, title="Old").json()
    r = edit_task(client, auth_headers, t, title="New")
    assert r.status_code == 200 and r.json()["title"] == "New"
    assert client.get(f"/api/tasks/{t['id']}", headers=auth_headers).json()["title"] == "New"


@pytest.mark.parametrize(
    "change",
    [{"title": ""}, {"subject": " "}, {"deadline": "bad"}, {"estimated_hours": 0}, {"difficulty": "Extreme"}],
)
def test_TC_TASK_08_invalid_edit_rejected_and_task_unchanged(client, auth_headers, change):
    t = make_task(client, auth_headers, title="Keep").json()
    assert edit_task(client, auth_headers, t, **change).status_code == 422
    assert client.get(f"/api/tasks/{t['id']}", headers=auth_headers).json()["title"] == "Keep"


@pytest.mark.parametrize("field", ["title", "subject", "deadline", "difficulty", "estimated_hours"])
def test_TC_TASK_08b_explicit_null_must_not_crash_the_server(safe_client, auth_headers, field):
    """A required field sent as null must be rejected (4xx), never a 500 (was DEF-01 on the Vibe build)."""
    t = make_task(safe_client, auth_headers).json()
    r = edit_task(safe_client, auth_headers, t, **{field: None})
    assert r.status_code == 422, f"PUT {field}=null -> {r.status_code}"
    assert safe_client.get(f"/api/tasks/{t['id']}", headers=auth_headers).status_code == 200


def test_TC_TASK_09_delete_removes_the_task_everywhere(client, auth_headers):
    tid = make_task(client, auth_headers).json()["id"]
    assert client.delete(f"/api/tasks/{tid}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/tasks/{tid}", headers=auth_headers).status_code == 404
    assert tasks(client, auth_headers, "?status=all") == []
    assert tasks(client, auth_headers, "?view=upcoming") == []
    assert dashboard(client, auth_headers)["recommendation"] is None


def test_TC_TASK_10_complete_keeps_the_task_and_can_be_reopened(client, auth_headers):
    tid = make_task(client, auth_headers).json()["id"]
    done = complete(client, auth_headers, tid).json()
    assert done["completed"] is True
    assert [t["id"] for t in tasks(client, auth_headers, "?status=completed")] == [tid]
    reopened = complete(client, auth_headers, tid, done=False).json()
    assert reopened["completed"] is False


def test_TC_TASK_11_task_details_contain_every_field(client, auth_headers):
    tid = make_task(client, auth_headers).json()["id"]
    t = client.get(f"/api/tasks/{tid}", headers=auth_headers).json()
    for key in ("title", "subject", "deadline", "difficulty", "estimated_hours", "completed", "priority"):
        assert key in t
    assert {"score", "level"} <= set(t["priority"])


def test_TC_TASK_12_tasks_persist_across_logout_and_login(client, make_user):
    headers, _ = make_user(email="p@example.com", password="abcd1234")
    tid = make_task(client, headers, title="Persist").json()["id"]
    client.post("/api/auth/logout", headers=headers)
    token = client.post("/api/auth/login", json={"email": "p@example.com", "password": "abcd1234"}).json()["token"]
    listed = tasks(client, {"Authorization": f"Bearer {token}"})
    assert [t["id"] for t in listed] == [tid] and listed[0]["title"] == "Persist"


def test_TC_TASK_13_validation_errors_name_the_field_and_explain(client, auth_headers):
    r = make_task(client, auth_headers, title="", hours=0)
    errs = r.json()["error"]["fields"]
    assert set(errs) >= {"title", "estimated_hours"}
    assert all(errs.values())


# ============================ Priority via the API ==========================
def test_TC_PRI_11_changing_the_deadline_recalculates_priority(client, auth_headers):
    t = make_task(client, auth_headers, deadline=future_deadline(days=10), difficulty="Very Hard", hours=10).json()
    assert score(t) == pytest.approx(62.5)  # E5
    t2 = edit_task(client, auth_headers, t, deadline=future_deadline(hours=12)).json()
    assert score(t2) == pytest.approx(100) and level(t2) == "Critical"


def test_TC_PRI_12_changing_the_difficulty_recalculates_priority(client, auth_headers):
    t = make_task(client, auth_headers, deadline=future_deadline(days=30), difficulty="Easy", hours=1).json()
    assert score(t) == pytest.approx(13)  # E2
    t2 = edit_task(client, auth_headers, t, difficulty="Very Hard").json()
    assert score(t2) == pytest.approx(37)  # 5 + 30 + 2


def test_TC_PRI_13_changing_the_hours_recalculates_priority(client, auth_headers):
    t = make_task(client, auth_headers, deadline=future_deadline(days=30), difficulty="Easy", hours=1).json()
    t2 = edit_task(client, auth_headers, t, estimated_hours=10).json()
    assert score(t2) == pytest.approx(31)  # 5 + 6 + 20


def test_TC_PRI_15_overdue_task_gets_deadline_score_100(client, auth_headers):
    t = make_task(client, auth_headers, deadline=past_deadline(days=1), difficulty="Easy", hours=1).json()
    assert score(t) == pytest.approx(58) and level(t) == "Medium"  # E6


# ======================= Filtering / sorting / tie-break ====================
def _seed_five(client, h):
    spec = {  # E1..E5 from the oracle
        "E1": (dict(hours=12), "Very Hard", 10, "Physics"),
        "E2": (dict(days=30), "Easy", 1, "Math"),
        "E3": (dict(days=4), "Medium", 5, "Math"),
        "E4": (dict(hours=36), "Hard", 8, "Physics"),
        "E5": (dict(days=10), "Very Hard", 10, "Art"),
    }
    ids = {}
    for name, (delta, diff, hours, subject) in spec.items():
        ids[name] = make_task(client, h, title=name, subject=subject, difficulty=diff, hours=hours,
                              deadline=future_deadline(**delta)).json()["id"]
    return ids


def test_TC_FLT_01_filter_by_subject(client, auth_headers):
    _seed_five(client, auth_headers)
    assert set(titles(tasks(client, auth_headers, "?subject=Math"))) == {"E2", "E3"}


def test_TC_FLT_02_filter_by_completion_status(client, auth_headers):
    ids = _seed_five(client, auth_headers)
    complete(client, auth_headers, ids["E1"])
    assert set(titles(tasks(client, auth_headers, "?status=completed"))) == {"E1"}
    assert set(titles(tasks(client, auth_headers, "?status=active"))) == {"E2", "E3", "E4", "E5"}


def test_TC_FLT_03_filter_with_no_match_and_combined_filters(client, auth_headers):
    ids = _seed_five(client, auth_headers)
    assert tasks(client, auth_headers, "?subject=Chemistry&status=all") == []
    complete(client, auth_headers, ids["E2"])
    assert titles(tasks(client, auth_headers, "?subject=Math&status=active")) == ["E3"]


def test_TC_SORT_01_sort_by_priority_highest_first(client, auth_headers):
    _seed_five(client, auth_headers)
    listed = tasks(client, auth_headers, "?sort=priority")
    assert titles(listed) == ["E1", "E4", "E5", "E3", "E2"]
    assert [score(t) for t in listed] == pytest.approx([100, 77.5, 62.5, 50, 13])


def test_TC_SORT_02_sort_by_deadline_earliest_first(client, auth_headers):
    _seed_five(client, auth_headers)
    assert titles(tasks(client, auth_headers, "?sort=deadline")) == ["E1", "E4", "E3", "E5", "E2"]


def test_TC_SORT_03_equal_scores_earlier_deadline_first(client, auth_headers):
    later = make_task(client, auth_headers, title="later", deadline=future_deadline(days=5)).json()
    sooner = make_task(client, auth_headers, title="sooner", deadline=future_deadline(days=4)).json()
    assert score(later) == score(sooner) == 50
    assert titles(tasks(client, auth_headers, "?sort=priority")) == ["sooner", "later"]


def test_TC_SORT_04_equal_score_and_deadline_oldest_task_first(client, auth_headers):
    """Team decision D2: same score AND same deadline -> the task created earlier comes first."""
    d = future_deadline(days=4)
    for name in ("first", "second", "third"):
        make_task(client, auth_headers, title=name, deadline=d)
    for _ in range(3):
        assert titles(tasks(client, auth_headers)) == ["first", "second", "third"]


# ====================== Upcoming / overdue / dashboard ======================
def test_TC_UPC_01_upcoming_shows_next_7_days_earliest_first(client, auth_headers):
    a = make_task(client, auth_headers, title="2d", deadline=future_deadline(days=2)).json()["id"]
    b = make_task(client, auth_headers, title="6d", deadline=future_deadline(days=6)).json()["id"]
    make_task(client, auth_headers, title="10d", deadline=future_deadline(days=10))
    listed = tasks(client, auth_headers, "?view=upcoming")
    ids = [t["id"] for t in listed]
    assert a in ids and b in ids and ids.index(a) < ids.index(b)
    assert "10d" not in titles(listed)


def test_TC_UPC_02_completed_tasks_not_upcoming(client, auth_headers):
    tid = make_task(client, auth_headers, deadline=future_deadline(days=2)).json()["id"]
    complete(client, auth_headers, tid)
    assert tasks(client, auth_headers, "?view=upcoming") == []


def test_TC_UPC_03_overdue_tasks_not_listed_as_upcoming(client, auth_headers):
    """Team decision D3 (was DEF-03 on the Vibe build)."""
    make_task(client, auth_headers, title="late", deadline=past_deadline(days=1))
    make_task(client, auth_headers, title="soon", deadline=future_deadline(days=2))
    assert titles(tasks(client, auth_headers, "?view=upcoming")) == ["soon"]
    dash = dashboard(client, auth_headers)
    assert titles(dash["upcoming"]) == ["soon"]
    assert dash["counts"]["due_this_week"] == 1
    assert titles(dash["overdue"]) == ["late"]


def test_TC_OVD_01_incomplete_task_past_deadline_is_overdue(client, auth_headers):
    make_task(client, auth_headers, title="late", deadline=past_deadline(hours=2))
    make_task(client, auth_headers, title="fine", deadline=future_deadline(days=2))
    by_title = {t["title"]: t for t in tasks(client, auth_headers)}
    assert by_title["late"]["overdue"] is True and by_title["fine"]["overdue"] is False
    assert titles(tasks(client, auth_headers, "?view=overdue")) == ["late"]


def test_TC_OVD_02_completed_task_is_never_overdue(client, auth_headers):
    tid = make_task(client, auth_headers, deadline=past_deadline(days=3)).json()["id"]
    done = complete(client, auth_headers, tid).json()
    assert done["overdue"] is False
    assert tasks(client, auth_headers, "?view=overdue") == []


def test_TC_DASH_01_dashboard_summarises_the_task_mix(client, auth_headers):
    make_task(client, auth_headers, title="crit", deadline=future_deadline(hours=12), difficulty="Very Hard", hours=10)
    make_task(client, auth_headers, title="med", deadline=future_deadline(days=4))
    make_task(client, auth_headers, title="late", deadline=past_deadline(days=1), difficulty="Easy", hours=1)
    tid = make_task(client, auth_headers, title="done").json()["id"]
    complete(client, auth_headers, tid)
    d = dashboard(client, auth_headers)
    c = d["counts"]
    assert c["incomplete"] == 3 and c["completed"] == 1
    assert c["high_priority"] == 1  # only "crit" is High/Critical
    assert c["overdue"] == 1
    assert set(titles(d["upcoming"])) >= {"crit", "med"}
    assert d["recommendation"]["title"] == "crit"


# =========================== Daily recommendation ===========================
def test_TC_REC_01_recommends_the_highest_priority_incomplete_task(client, auth_headers):
    _seed_five(client, auth_headers)
    assert dashboard(client, auth_headers)["recommendation"]["title"] == "E1"


def test_TC_REC_02_completed_tasks_are_excluded_from_the_recommendation(client, auth_headers):
    ids = _seed_five(client, auth_headers)
    complete(client, auth_headers, ids["E1"])
    assert dashboard(client, auth_headers)["recommendation"]["title"] == "E4"
    complete(client, auth_headers, ids["E1"], done=False)
    assert dashboard(client, auth_headers)["recommendation"]["title"] == "E1"


def test_TC_REC_03_equal_scores_recommend_the_earlier_deadline(client, auth_headers):
    make_task(client, auth_headers, title="later", deadline=future_deadline(days=5))
    sooner = make_task(client, auth_headers, title="sooner", deadline=future_deadline(days=4)).json()
    assert dashboard(client, auth_headers)["recommendation"]["id"] == sooner["id"]


def test_TC_REC_04_no_incomplete_tasks_gives_no_recommendation(client, auth_headers):
    assert dashboard(client, auth_headers)["recommendation"] is None
    tid = make_task(client, auth_headers).json()["id"]
    complete(client, auth_headers, tid)
    assert dashboard(client, auth_headers)["recommendation"] is None


def test_TC_REC_05_overdue_tasks_can_be_recommended(client, auth_headers):
    make_task(client, auth_headers, title="late", deadline=past_deadline(days=2), difficulty="Very Hard", hours=10)
    make_task(client, auth_headers, title="easy", deadline=future_deadline(days=30), difficulty="Easy", hours=1)
    assert dashboard(client, auth_headers)["recommendation"]["title"] == "late"


def test_TC_SORT_05_higher_exact_score_ranks_first_even_when_rounded_scores_match(client, auth_headers):
    """Added after reading this build's tie rule (FR-14, D2). Hand-calculated:
    X: 36 h, Hard, 8 h    -> 37.5 + 24 + 16   = 77.5 (shown 78)
    Y: 47 h, Hard, 8.45 h -> 37.5 + 24 + 16.9 = 78.4 (shown 78)
    Y has the higher score, so it must come first and be recommended, even though X is due sooner."""
    make_task(client, auth_headers, title="X", deadline=future_deadline(hours=36), difficulty="Hard", hours=8)
    make_task(client, auth_headers, title="Y", deadline=future_deadline(hours=47), difficulty="Hard", hours=8.45)
    listed = tasks(client, auth_headers, "?sort=priority")
    assert [score(t) for t in listed] == pytest.approx([78.4, 77.5])
    assert titles(listed) == ["Y", "X"]
    assert dashboard(client, auth_headers)["recommendation"]["title"] == "Y"
