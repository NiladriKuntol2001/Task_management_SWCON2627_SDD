"""Small helpers so each test reads like its test case (Member 3 verification suite)."""
from datetime import datetime, timedelta, timezone


def future_deadline(**kw) -> str:
    return (datetime.now(timezone.utc) + timedelta(**kw)).isoformat()


def past_deadline(**kw) -> str:
    return (datetime.now(timezone.utc) - timedelta(**kw)).isoformat()


def task_body(title="Task", subject="Math", deadline=None, difficulty="Medium", hours=5, **extra):
    """Default task: 4 days, Medium, 5 h -> hand-calculated score 50 (E3)."""
    body = {"title": title, "subject": subject, "deadline": deadline or future_deadline(days=4),
            "difficulty": difficulty, "estimated_hours": hours}
    body.update(extra)
    return body


def make_task(client, headers, **kw):
    return client.post("/api/tasks", json=task_body(**kw), headers=headers)


def edit_task(client, headers, task, **changes):
    """PUT is a full replacement in this build: send the current task with some fields changed."""
    body = {k: task[k] for k in ("title", "subject", "deadline", "difficulty", "estimated_hours")}
    body.update(changes)
    return client.put(f"/api/tasks/{task['id']}", json=body, headers=headers)


def tasks(client, headers, query=""):
    """List of tasks from GET /api/tasks (the response wraps them in {"tasks": [...]})."""
    r = client.get(f"/api/tasks{query}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["tasks"]


def titles(task_list):
    return [t["title"] for t in task_list]


def score(task):
    """Exact (unrounded) score; the build also shows a whole-number score in priority['score']."""
    return task["priority"]["exact"]


def level(task):
    return task["priority"]["level"]


def complete(client, headers, task_id, done=True):
    return client.patch(f"/api/tasks/{task_id}/complete", json={"completed": done}, headers=headers)


def dashboard(client, headers):
    r = client.get("/api/dashboard", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def fields(response):
    """Field names that the error body says are wrong."""
    return set(response.json()["error"]["fields"])
