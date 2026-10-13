"""SQLite connection, schema and main-admin bootstrap (data-model.md, FR-25, FR-26)."""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('student', 'admin')),
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    subject         TEXT NOT NULL,
    deadline        TEXT NOT NULL,
    difficulty      TEXT NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard', 'Very Hard')),
    estimated_hours REAL NOT NULL CHECK (estimated_hours > 0 AND estimated_hours <= 1000),
    completed       INTEGER NOT NULL DEFAULT 0,
    completed_at    TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_owner_completed ON tasks(owner_id, completed);
CREATE INDEX IF NOT EXISTS idx_tasks_owner_deadline ON tasks(owner_id, deadline);
CREATE TABLE IF NOT EXISTS revoked_tokens (
    jti        TEXT PRIMARY KEY,
    expires_at TEXT NOT NULL
);
"""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def from_iso(text: str) -> datetime:
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def session(db_path: str):
    """One connection per unit of work; commits on success, rolls back on error."""
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def reset_db(db_path: str) -> None:
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(db_path + suffix)
        except FileNotFoundError:
            pass


def init_db(db_path: str, admin_email: str = "admin123@gmail.com", admin_password: str = "admin@123") -> None:
    from .security import hash_password  # local import: security depends on db helpers

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with session(db_path) as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)
        conn.execute("DELETE FROM revoked_tokens WHERE expires_at < ?", (to_iso(utcnow()),))
        if conn.execute("SELECT 1 FROM users WHERE id = 1").fetchone() is None:
            # FR-26: main admin is always user 1. Created once; never overwritten on restart.
            conn.execute(
                "INSERT INTO users (id, name, email, password_hash, role, is_active, created_at)"
                " VALUES (1, 'Main Admin', ?, ?, 'admin', 1, ?)",
                (admin_email.strip().lower(), hash_password(admin_password), to_iso(utcnow())),
            )
