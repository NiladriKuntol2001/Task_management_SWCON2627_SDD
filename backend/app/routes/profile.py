"""US6 — profile, change email, change password (FR-22..FR-25)."""
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .. import tasks_repo, users_repo, validation
from ..db import session
from ..errors import ApiError
from ..security import hash_password, require_user, verify_password
from .common import db_path, json_body

WRONG_CURRENT = "Current password is incorrect."


def _profile(conn, user_id: int) -> dict:
    row = users_repo.by_id(conn, user_id)
    total, done = tasks_repo.counts_for_owner(conn, user_id)
    return {**users_repo.public(row), "task_count": total, "completed_count": done}


async def me(request: Request):
    user = require_user(request)
    with session(db_path(request)) as conn:
        return JSONResponse(_profile(conn, user["id"]))


async def _check_current(user: dict, body: dict) -> None:
    current = body.get("current_password")
    if not isinstance(current, str) or not current:
        raise ApiError(422, "Enter your current password.", {"current_password": "Enter your current password."})
    if not await run_in_threadpool(verify_password, current, user["password_hash"]):
        raise ApiError(422, WRONG_CURRENT, {"current_password": WRONG_CURRENT})


async def change_email(request: Request):
    user = require_user(request)
    body = await json_body(request)
    errors: dict[str, str] = {}
    new_email = validation.email(body, "new_email", errors)
    validation.fail(errors)
    if user["id"] == 1:
        raise ApiError(403, "The main admin's email can't be changed.")
    if new_email == user["email"]:
        raise ApiError(422, "This is already your email.", {"new_email": "This is already your email."})
    await _check_current(user, body)
    with session(db_path(request)) as conn:
        if users_repo.email_taken(conn, new_email, except_id=user["id"]):
            raise ApiError(409, "Another account already uses this email.",
                           {"new_email": "Another account already uses this email."})
        users_repo.set_email(conn, user["id"], new_email)
        return JSONResponse(_profile(conn, user["id"]))


async def change_password(request: Request):
    user = require_user(request)
    body = await json_body(request)
    await _check_current(user, body)
    errors: dict[str, str] = {}
    new = validation.new_password(body, "new_password", errors)
    if not errors and new == body.get("current_password"):
        errors["new_password"] = "New password must be different from your current password."
    if body.get("confirm_password") != body.get("new_password"):
        errors["confirm_password"] = "The two new passwords don't match."
    validation.fail(errors)
    new_hash = await run_in_threadpool(hash_password, new)
    with session(db_path(request)) as conn:
        users_repo.set_password(conn, user["id"], new_hash)
    return Response(status_code=204)


routes = [
    Route("/me", me, methods=["GET"]),
    Route("/me/email", change_email, methods=["PATCH"]),
    Route("/me/password", change_password, methods=["PATCH"]),
]
