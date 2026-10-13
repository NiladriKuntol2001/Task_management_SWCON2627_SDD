"""US5 — dashboard and recommendation (FR-19, FR-20)."""
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .. import recommendation, tasks_repo
from ..db import session, utcnow
from ..security import require_user
from .common import db_path


async def dashboard(request: Request):
    user = require_user(request)
    now = utcnow()
    with session(db_path(request)) as conn:
        tasks = [tasks_repo.to_dict(r, now) for r in tasks_repo.list_for_owner(conn, user["id"])]
    return JSONResponse(recommendation.summary(tasks, now))


routes = [Route("/dashboard", dashboard, methods=["GET"])]
