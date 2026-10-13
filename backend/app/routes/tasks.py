"""US2 / US4 — task management, organisation and live preview
(FR-04..FR-10, FR-15..FR-18, FR-21, FR-35)."""
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .. import priority, recommendation, tasks_repo, validation
from ..db import session, utcnow
from ..errors import ApiError, not_found
from ..security import require_user
from .common import db_path, json_body

STATUSES = ("active", "completed", "all")


def _owned(conn, owner_id: int, task_id: int):
    row = tasks_repo.get_for_owner(conn, owner_id, task_id)
    if row is None:
        raise not_found()          # FR-21: someone else's task looks exactly like a missing one
    return row


async def list_tasks(request: Request):
    user = require_user(request)
    q = request.query_params
    status = q.get("status", "active")
    if status not in STATUSES:
        raise ApiError(422, "Unknown status filter.", {"status": "Use active, completed or all."})
    sort = q.get("sort", "priority")
    if sort not in ("priority", "deadline"):
        raise ApiError(422, "Unknown sort order.", {"sort": "Use priority or deadline."})
    view = q.get("view")
    subject = (q.get("subject") or "").strip().lower()
    search = (q.get("q") or "").strip().lower()

    now = utcnow()
    with session(db_path(request)) as conn:
        everything = [tasks_repo.to_dict(r, now) for r in tasks_repo.list_for_owner(conn, user["id"])]

    subjects = sorted({t["subject"] for t in everything}, key=str.lower)
    counts = {"active": sum(not t["completed"] for t in everything),
              "completed": sum(t["completed"] for t in everything),
              "overdue": sum(t["overdue"] for t in everything)}

    if view == "upcoming":
        tasks = recommendation.upcoming(everything, now)
    elif view == "overdue":
        tasks = recommendation.overdue(everything)
    elif view:
        raise ApiError(422, "Unknown view.", {"view": "Use upcoming or overdue."})
    else:
        tasks = [t for t in everything
                 if status == "all" or (status == "completed") == t["completed"]]
    if subject:
        tasks = [t for t in tasks if t["subject"].lower() == subject]
    if search:
        tasks = [t for t in tasks if search in t["title"].lower()]
    if not view:
        tasks = tasks_repo.sort_by_priority(tasks) if sort == "priority" else tasks_repo.sort_by_deadline(tasks)
    return JSONResponse({"tasks": tasks, "subjects": subjects, "counts": counts})


async def create_task(request: Request):
    user = require_user(request)
    data = validation.task(await json_body(request))
    with session(db_path(request)) as conn:
        task_id = tasks_repo.create(conn, user["id"], data)
        row = tasks_repo.get_for_owner(conn, user["id"], task_id)
    return JSONResponse(tasks_repo.to_dict(row, utcnow()), status_code=201)


async def get_task(request: Request):
    user = require_user(request)
    with session(db_path(request)) as conn:
        row = _owned(conn, user["id"], request.path_params["task_id"])
    return JSONResponse(tasks_repo.to_dict(row, utcnow()))


async def update_task(request: Request):
    user = require_user(request)
    task_id = request.path_params["task_id"]
    body = await json_body(request)
    with session(db_path(request)) as conn:
        _owned(conn, user["id"], task_id)
        data = validation.task(body)
        tasks_repo.update_for_owner(conn, user["id"], task_id, data)
        row = tasks_repo.get_for_owner(conn, user["id"], task_id)
    return JSONResponse(tasks_repo.to_dict(row, utcnow()))   # FR-13: re-scored on the way out


async def complete_task(request: Request):
    user = require_user(request)
    task_id = request.path_params["task_id"]
    body = await json_body(request)
    if not isinstance(body.get("completed"), bool):
        raise ApiError(422, "Say whether the task is completed.", {"completed": "Must be true or false."})
    with session(db_path(request)) as conn:
        _owned(conn, user["id"], task_id)
        tasks_repo.set_completed_for_owner(conn, user["id"], task_id, body["completed"])
        row = tasks_repo.get_for_owner(conn, user["id"], task_id)
    return JSONResponse(tasks_repo.to_dict(row, utcnow()))


async def delete_task(request: Request):
    user = require_user(request)
    with session(db_path(request)) as conn:
        if not tasks_repo.delete_for_owner(conn, user["id"], request.path_params["task_id"]):
            raise not_found()
    return Response(status_code=204)


async def preview(request: Request):
    require_user(request)
    errors: dict[str, str] = {}
    data = validation.priority_inputs(await json_body(request), errors)
    validation.fail(errors)
    return JSONResponse(priority.score(data["deadline"], data["difficulty"], data["estimated_hours"], utcnow()))


routes = [
    Route("/tasks", list_tasks, methods=["GET"]),
    Route("/tasks", create_task, methods=["POST"]),
    Route("/tasks/{task_id:int}", get_task, methods=["GET"]),
    Route("/tasks/{task_id:int}", update_task, methods=["PUT"]),
    Route("/tasks/{task_id:int}", delete_task, methods=["DELETE"]),
    Route("/tasks/{task_id:int}/complete", complete_task, methods=["PATCH"]),
    Route("/priority/preview", preview, methods=["POST"]),
]
