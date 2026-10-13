"""US7 — admin panel (FR-26..FR-32). Every handler starts with require_admin (FR-32)."""
from collections import Counter
from datetime import timedelta

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .. import tasks_repo, users_repo, validation
from ..db import from_iso, session, utcnow
from ..errors import ApiError, not_found
from ..security import hash_password, require_admin
from .common import db_path, json_body

ROLES = ("student", "admin")
LEVELS = ("Critical", "High", "Medium", "Low")


def _load(request: Request):
    now = utcnow()
    with session(db_path(request)) as conn:
        users = [users_repo.public(r) for r in users_repo.all_users(conn)]
        tasks = [tasks_repo.to_dict(r, now) for r in tasks_repo.list_all_users(conn)]
    return now, users, tasks


def _per_user(tasks: list[dict]) -> dict[int, dict]:
    stats: dict[int, dict] = {}
    for t in tasks:
        s = stats.setdefault(t["owner_id"], {"open": 0, "completed": 0, "overdue": 0, "top": None})
        if t["completed"]:
            s["completed"] += 1
        else:
            s["open"] += 1
            s["overdue"] += t["overdue"]
            s["top"] = max(s["top"] or 0, t["priority"]["score"])
    return stats


def _with_stats(user: dict, stats: dict) -> dict:
    s = stats.get(user["id"], {"open": 0, "completed": 0, "overdue": 0, "top": None})
    return {**user, **s}


async def overview(request: Request):
    require_admin(request)
    now, users, tasks = _load(request)
    names = {u["id"]: u["name"] for u in users}
    students = [u for u in users if u["role"] == "student"]
    open_tasks = [t for t in tasks if not t["completed"]]
    overdue = [t for t in open_tasks if t["overdue"]]

    days = [(now - timedelta(days=i)).date() for i in range(13, -1, -1)]
    created = Counter(from_iso(t["created_at"]).date() for t in tasks)
    completed = Counter(from_iso(t["completed_at"]).date() for t in tasks if t["completed_at"])

    attention = []
    for owner_id in sorted({t["owner_id"] for t in overdue}):
        mine = tasks_repo.sort_by_priority([t for t in overdue if t["owner_id"] == owner_id])
        worst = mine[0]
        attention.append({
            "id": owner_id, "name": names.get(owner_id, "?"), "overdue": len(mine),
            "open": sum(1 for t in open_tasks if t["owner_id"] == owner_id),
            "task": {"title": worst["title"], "deadline": worst["deadline"],
                     "score": worst["priority"]["score"], "level": worst["priority"]["level"]},
        })
    attention.sort(key=lambda a: (-a["task"]["score"], -a["overdue"], a["id"]))

    return JSONResponse({
        "students": {"total": len(students), "active": sum(u["is_active"] for u in students),
                     "deactivated": sum(not u["is_active"] for u in students)},
        "users_total": len(users),
        "tasks": {"total": len(tasks), "open": len(open_tasks), "completed": len(tasks) - len(open_tasks)},
        "completion_rate": round(100 * (len(tasks) - len(open_tasks)) / len(tasks)) if tasks else 0,
        "critical_open": sum(1 for t in open_tasks if t["priority"]["level"] == "Critical"),
        "overdue": {"tasks": len(overdue), "students": len({t["owner_id"] for t in overdue})},
        "trend": [{"date": d.isoformat(), "created": created.get(d, 0), "completed": completed.get(d, 0)}
                  for d in days],
        "by_level": {lvl: sum(1 for t in open_tasks if t["priority"]["level"] == lvl) for lvl in LEVELS},
        "top_subjects": [{"subject": s, "count": n}
                         for s, n in sorted(Counter(t["subject"] for t in tasks).items(),
                                            key=lambda kv: (-kv[1], kv[0].lower()))[:5]],
        "attention": attention,
    })


async def list_users(request: Request):
    require_admin(request)
    _, users, tasks = _load(request)
    stats = _per_user(tasks)
    q = (request.query_params.get("q") or "").strip().lower()
    if q:
        bare = q.lstrip("#")
        if bare.isdigit():      # a number searches by user ID only
            users = [u for u in users if str(u["id"]) == bare]
        else:
            users = [u for u in users if q in u["name"].lower() or q in u["email"]]
    return JSONResponse({"users": [_with_stats(u, stats) for u in users]})


async def create_user(request: Request):
    require_admin(request)
    body = await json_body(request)
    errors: dict[str, str] = {}
    try:
        data = validation.registration(body)
    except ApiError as err:
        errors.update(err.fields)
        data = {}
    role = body.get("role", "student")
    if role not in ROLES:
        errors["role"] = "Role must be student or admin."
    validation.fail(errors)
    password_hash = await run_in_threadpool(hash_password, data["password"])
    with session(db_path(request)) as conn:
        if users_repo.email_taken(conn, data["email"]):
            raise ApiError(409, "An account with this email already exists.",
                           {"email": "An account with this email already exists."})
        user_id = users_repo.create(conn, data["name"], data["email"], password_hash, role)
        row = users_repo.by_id(conn, user_id)
    return JSONResponse(_with_stats(users_repo.public(row), {}), status_code=201)


async def update_user(request: Request):
    admin = require_admin(request)
    target_id = request.path_params["user_id"]
    body = await json_body(request)
    if target_id == 1:
        raise ApiError(403, "The main admin can't be deactivated or changed.")
    if target_id == admin["id"]:
        raise ApiError(403, "You can't deactivate or change the role of your own account.")
    errors: dict[str, str] = {}
    if "is_active" in body and not isinstance(body["is_active"], bool):
        errors["is_active"] = "Must be true or false."
    if "role" in body and body["role"] not in ROLES:
        errors["role"] = "Role must be student or admin."
    if not ({"is_active", "role"} & body.keys()):
        errors["is_active"] = "Nothing to change."
    validation.fail(errors)
    with session(db_path(request)) as conn:
        if users_repo.by_id(conn, target_id) is None:
            raise not_found("User")
        if "is_active" in body:
            users_repo.set_active(conn, target_id, body["is_active"])
        if "role" in body:
            users_repo.set_role(conn, target_id, body["role"])
        row = users_repo.by_id(conn, target_id)
    _, _, tasks = _load(request)
    return JSONResponse(_with_stats(users_repo.public(row), _per_user(tasks)))


async def all_tasks(request: Request):
    require_admin(request)
    _, users, tasks = _load(request)
    names = {u["id"]: u["name"] for u in users}
    level = request.query_params.get("level")
    if level and level not in LEVELS:
        raise ApiError(422, "Unknown priority level.", {"level": "Use Critical, High, Medium or Low."})
    owner = request.query_params.get("owner_id")
    try:
        owner_id = int(owner) if owner else None
    except ValueError:
        raise ApiError(422, "owner_id must be a number.", {"owner_id": "Must be a number."})
    result = [t for t in tasks if not t["completed"]
              and (not level or t["priority"]["level"] == level)
              and (owner_id is None or t["owner_id"] == owner_id)]
    result = [{**t, "owner_name": names.get(t["owner_id"], "?")} for t in tasks_repo.sort_by_priority(result)]
    return JSONResponse({"tasks": result, "owner_name": names.get(owner_id) if owner_id else None})


routes = [
    Route("/admin/overview", overview, methods=["GET"]),
    Route("/admin/users", list_users, methods=["GET"]),
    Route("/admin/users", create_user, methods=["POST"]),
    Route("/admin/users/{user_id:int}", update_user, methods=["PATCH"]),
    Route("/admin/tasks", all_tasks, methods=["GET"]),
]
