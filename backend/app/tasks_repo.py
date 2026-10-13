"""All SQL for tasks. Every student-facing function takes owner_id and filters by it
(FR-21, constitution IV). Only the *_all_users functions are for the admin module."""
import sqlite3
from datetime import datetime

from . import priority
from .db import from_iso, to_iso, utcnow


def to_dict(row, now: datetime) -> dict:
    """Row -> API task, with priority derived at `now` (FR-13)."""
    deadline = from_iso(row["deadline"])
    completed = bool(row["completed"])
    hours = row["estimated_hours"]
    return {
        "id": row["id"],
        "owner_id": row["owner_id"],
        "title": row["title"],
        "subject": row["subject"],
        "deadline": row["deadline"],
        "difficulty": row["difficulty"],
        "estimated_hours": int(hours) if float(hours).is_integer() else hours,
        "completed": completed,
        "completed_at": row["completed_at"],
        "created_at": row["created_at"],
        "overdue": (not completed) and deadline < now,                      # FR-18
        "priority": None if completed else priority.score(deadline, row["difficulty"], hours, now),
    }


def sort_by_priority(tasks: list[dict]) -> list[dict]:
    return sorted(tasks, key=priority.sort_key)


def sort_by_deadline(tasks: list[dict]) -> list[dict]:
    return sorted(tasks, key=lambda t: (t["deadline"], t["created_at"], t["id"]))


def list_for_owner(conn: sqlite3.Connection, owner_id: int) -> list:
    return conn.execute("SELECT * FROM tasks WHERE owner_id = ?", (owner_id,)).fetchall()


def get_for_owner(conn: sqlite3.Connection, owner_id: int, task_id: int):
    return conn.execute("SELECT * FROM tasks WHERE id = ? AND owner_id = ?", (task_id, owner_id)).fetchone()


def create(conn: sqlite3.Connection, owner_id: int, data: dict) -> int:
    now = to_iso(utcnow())
    cur = conn.execute(
        "INSERT INTO tasks (owner_id, title, subject, deadline, difficulty, estimated_hours, completed,"
        " created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)",
        (owner_id, data["title"], data["subject"], to_iso(data["deadline"]), data["difficulty"],
         data["estimated_hours"], now, now))
    return cur.lastrowid


def update_for_owner(conn, owner_id: int, task_id: int, data: dict) -> bool:
    cur = conn.execute(
        "UPDATE tasks SET title = ?, subject = ?, deadline = ?, difficulty = ?, estimated_hours = ?,"
        " updated_at = ? WHERE id = ? AND owner_id = ?",
        (data["title"], data["subject"], to_iso(data["deadline"]), data["difficulty"],
         data["estimated_hours"], to_iso(utcnow()), task_id, owner_id))
    return cur.rowcount == 1


def set_completed_for_owner(conn, owner_id: int, task_id: int, completed: bool) -> bool:
    now = to_iso(utcnow())
    cur = conn.execute(
        "UPDATE tasks SET completed = ?, completed_at = ?, updated_at = ? WHERE id = ? AND owner_id = ?",
        (1 if completed else 0, now if completed else None, now, task_id, owner_id))
    return cur.rowcount == 1


def delete_for_owner(conn, owner_id: int, task_id: int) -> bool:
    return conn.execute("DELETE FROM tasks WHERE id = ? AND owner_id = ?", (task_id, owner_id)).rowcount == 1


def counts_for_owner(conn, owner_id: int) -> tuple[int, int]:
    row = conn.execute("SELECT COUNT(*) AS n, COALESCE(SUM(completed), 0) AS done FROM tasks WHERE owner_id = ?",
                       (owner_id,)).fetchone()
    return row["n"], row["done"]


# --- admin only (FR-27, FR-31) ---------------------------------------------------

def list_all_users(conn) -> list:
    return conn.execute("SELECT * FROM tasks").fetchall()
