"""US1 — register, sign in, sign out (FR-01..FR-03)."""
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .. import users_repo, validation
from ..db import session
from ..errors import ApiError
from ..security import hash_password, issue_token, require_user, revoke, verify_password
from .common import db_path, json_body

BAD_LOGIN = "Email or password is incorrect."


def _session_payload(request: Request, row) -> dict:
    settings = request.app.state.settings
    return {"token": issue_token(row["id"], settings.secret_key, settings.token_hours),
            "user": users_repo.public(row)}


async def register(request: Request):
    data = validation.registration(await json_body(request))
    password_hash = await run_in_threadpool(hash_password, data["password"])
    with session(db_path(request)) as conn:
        if users_repo.email_taken(conn, data["email"]):
            raise ApiError(409, "An account with this email already exists.",
                           {"email": "An account with this email already exists."})
        user_id = users_repo.create(conn, data["name"], data["email"], password_hash)
        row = users_repo.by_id(conn, user_id)
    return JSONResponse(_session_payload(request, row), status_code=201)


async def login(request: Request):
    data = await json_body(request)
    email = data.get("email") if isinstance(data.get("email"), str) else ""
    password = data.get("password") if isinstance(data.get("password"), str) else ""
    with session(db_path(request)) as conn:
        row = users_repo.by_email(conn, email) if email else None
    # Same message for unknown email and wrong password (no account enumeration).
    if row is None or not await run_in_threadpool(verify_password, password, row["password_hash"]):
        raise ApiError(401, BAD_LOGIN)
    if not row["is_active"]:
        raise ApiError(403, "This account has been deactivated. Please contact an administrator.")
    return JSONResponse(_session_payload(request, row))


async def logout(request: Request):
    user = require_user(request)
    revoke(request, user)
    return Response(status_code=204)


routes = [
    Route("/auth/register", register, methods=["POST"]),
    Route("/auth/login", login, methods=["POST"]),
    Route("/auth/logout", logout, methods=["POST"]),
]
