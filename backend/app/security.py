"""Passwords, session tokens and access guards (NFR-03, NFR-04, FR-03, FR-30, FR-32)."""
import base64
import hashlib
import hmac
import secrets
import uuid
from datetime import timedelta

import jwt
from starlette.requests import Request

from .db import from_iso, session, to_iso, utcnow
from .errors import ApiError

# scrypt parameters (research.md R3). Stored with each hash so they can be raised later.
_N, _R, _P, _DKLEN = 2 ** 14, 8, 1, 64


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN)
    return f"scrypt${_N}${_R}${_P}${_b64(salt)}${_b64(key)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt, key = stored.split("$")
        if algo != "scrypt":
            return False
        expected = base64.b64decode(key)
        actual = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt),
                                n=int(n), r=int(r), p=int(p), dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def issue_token(user_id: int, secret: str, hours: int) -> str:
    now = utcnow()
    payload = {"sub": str(user_id), "jti": uuid.uuid4().hex, "iat": int(now.timestamp()),
               "exp": int((now + timedelta(hours=hours)).timestamp())}
    return jwt.encode(payload, secret, algorithm="HS256")


def _decode(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["sub", "jti", "exp"]})
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "Your session has expired. Please sign in again.")
    except jwt.InvalidTokenError:
        raise ApiError(401, "Please sign in to continue.")


def _bearer(request: Request) -> str:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ApiError(401, "Please sign in to continue.")
    return token


def require_user(request: Request) -> dict:
    """Return the signed-in, active user (as a dict) or raise 401."""
    settings = request.app.state.settings
    claims = _decode(_bearer(request), settings.secret_key)
    with session(settings.db_path) as conn:
        if conn.execute("SELECT 1 FROM revoked_tokens WHERE jti = ?", (claims["jti"],)).fetchone():
            raise ApiError(401, "You have signed out. Please sign in again.")
        row = conn.execute("SELECT * FROM users WHERE id = ?", (int(claims["sub"]),)).fetchone()
    if row is None or not row["is_active"]:
        raise ApiError(401, "This account is not active. Please contact an administrator.")
    user = dict(row)
    user["_jti"], user["_exp"] = claims["jti"], claims["exp"]
    return user


def require_admin(request: Request) -> dict:
    user = require_user(request)
    if user["role"] != "admin":
        raise ApiError(403, "Admins only.")
    return user


def revoke(request: Request, user: dict) -> None:
    settings = request.app.state.settings
    expires = to_iso(from_iso("1970-01-01T00:00:00Z") + timedelta(seconds=user["_exp"]))
    with session(settings.db_path) as conn:
        conn.execute("INSERT OR IGNORE INTO revoked_tokens (jti, expires_at) VALUES (?, ?)", (user["_jti"], expires))
