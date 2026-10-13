"""All SQL for users. Routes never touch the users table directly."""
import sqlite3

from .db import to_iso, utcnow

PUBLIC = "id, name, email, role, is_active, created_at"


def public(row) -> dict:
    return {"id": row["id"], "name": row["name"], "email": row["email"], "role": row["role"],
            "is_active": bool(row["is_active"]), "created_at": row["created_at"],
            "is_main_admin": row["id"] == 1}


def by_email(conn: sqlite3.Connection, email: str):
    return conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()


def by_id(conn: sqlite3.Connection, user_id: int):
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def email_taken(conn: sqlite3.Connection, email: str, except_id: int | None = None) -> bool:
    row = by_email(conn, email)
    return row is not None and row["id"] != except_id


def create(conn: sqlite3.Connection, name: str, email: str, password_hash: str, role: str = "student") -> int:
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, role, is_active, created_at) VALUES (?, ?, ?, ?, 1, ?)",
        (name, email.strip().lower(), password_hash, role, to_iso(utcnow())))
    return cur.lastrowid


def set_email(conn, user_id: int, email: str) -> None:
    conn.execute("UPDATE users SET email = ? WHERE id = ?", (email.strip().lower(), user_id))


def set_password(conn, user_id: int, password_hash: str) -> None:
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))


def set_active(conn, user_id: int, active: bool) -> None:
    conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if active else 0, user_id))


def set_role(conn, user_id: int, role: str) -> None:
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))


def all_users(conn) -> list:
    return conn.execute(f"SELECT {PUBLIC} FROM users ORDER BY id").fetchall()
