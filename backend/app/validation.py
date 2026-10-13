"""Server-side input validation with messages that say what to fix
(FR-01, FR-10, FR-23, FR-24, NFR-06, NFR-07, NFR-12)."""
import math
import re

from .db import from_iso
from .errors import ApiError

DIFFICULTIES = ("Easy", "Medium", "Hard", "Very Hard")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
MIN_PASSWORD = 8


def fail(fields: dict[str, str], message: str = "Please fix the highlighted fields.") -> None:
    if fields:
        raise ApiError(422, message, fields)


def text(data: dict, key: str, label: str, max_len: int, errors: dict) -> str:
    value = data.get(key)
    value = value.strip() if isinstance(value, str) else ""
    if not value:
        errors[key] = f"{label} can't be empty."
    elif len(value) > max_len:
        errors[key] = f"{label} must be {max_len} characters or fewer."
    return value


def email(data: dict, key: str, errors: dict) -> str:
    value = data.get(key)
    value = value.strip().lower() if isinstance(value, str) else ""
    if not value:
        errors[key] = "Email can't be empty."
    elif len(value) > 254 or not EMAIL_RE.match(value):
        errors[key] = "Enter a valid email address."
    return value


def new_password(data: dict, key: str, errors: dict) -> str:
    value = data.get(key)
    if not isinstance(value, str) or len(value) < MIN_PASSWORD:
        errors[key] = f"Password must be at least {MIN_PASSWORD} characters."
        return ""
    if len(value) > 200:
        errors[key] = "Password must be 200 characters or fewer."
    return value


def registration(data: dict) -> dict:
    errors: dict[str, str] = {}
    result = {
        "name": text(data, "name", "Name", 100, errors),
        "email": email(data, "email", errors),
        "password": new_password(data, "password", errors),
    }
    fail(errors)
    return result


def priority_inputs(data: dict, errors: dict) -> dict:
    deadline_raw = data.get("deadline")
    deadline = None
    if not isinstance(deadline_raw, str) or not deadline_raw.strip():
        errors["deadline"] = "Enter a valid deadline date and time."
    else:
        try:
            deadline = from_iso(deadline_raw.strip())
        except ValueError:
            errors["deadline"] = "Enter a valid deadline date and time."

    difficulty = data.get("difficulty")
    if difficulty not in DIFFICULTIES:
        errors["difficulty"] = "Choose a difficulty: Easy, Medium, Hard or Very Hard."

    hours_raw = data.get("estimated_hours")
    hours = None
    if isinstance(hours_raw, bool) or hours_raw is None or hours_raw == "":
        errors["estimated_hours"] = "Estimated hours must be a number."
    else:
        try:
            hours = float(hours_raw)
            if not math.isfinite(hours):
                raise ValueError
            if hours <= 0:
                errors["estimated_hours"] = "Estimated hours must be more than 0."
            elif hours > 1000:
                errors["estimated_hours"] = "Estimated hours must be 1000 or less."
        except (TypeError, ValueError):
            errors["estimated_hours"] = "Estimated hours must be a number."
    return {"deadline": deadline, "difficulty": difficulty, "estimated_hours": hours}


def task(data: dict) -> dict:
    errors: dict[str, str] = {}
    result = {
        "title": text(data, "title", "Title", 200, errors),
        "subject": text(data, "subject", "Subject", 100, errors),
        **priority_inputs(data, errors),
    }
    fail(errors)
    return result
