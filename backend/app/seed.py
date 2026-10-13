"""Load seed/seed-data.json into an empty database. Deadlines and timestamps are
stored in the file as hour offsets and placed relative to the moment of loading,
so the expected priorities in the file stay correct on any day."""
import json
from datetime import timedelta
from pathlib import Path

from .db import session, to_iso, utcnow
from .security import hash_password

SEED_FILE = Path(__file__).resolve().parents[2] / "seed" / "seed-data.json"


def load_seed(db_path: str, seed_file: Path = SEED_FILE) -> str | None:
    data = json.loads(Path(seed_file).read_text(encoding="utf-8"))
    now = utcnow()

    def at(hours: float) -> str:
        return to_iso(now + timedelta(hours=hours))

    with session(db_path) as conn:
        if conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] > 0:
            return None
        hashes: dict[str, str] = {}
        for u in data["users"]:
            pw_hash = hashes.setdefault(u["password"], hash_password(u["password"]))
            joined = at(-24 * u["joined_days_ago"])
            if u["id"] == 1:
                # The main admin already exists (db.init_db); keep its password, align the rest.
                conn.execute("UPDATE users SET name = ?, created_at = ? WHERE id = 1", (u["name"], joined))
                continue
            conn.execute(
                "INSERT OR REPLACE INTO users (id, name, email, password_hash, role, is_active, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (u["id"], u["name"], u["email"], pw_hash, u["role"], 1 if u["is_active"] else 0, joined))
        for t in data["tasks"]:
            completed_at = at(t["completed_offset_hours"]) if t["completed"] else None
            conn.execute(
                "INSERT INTO tasks (id, owner_id, title, subject, deadline, difficulty, estimated_hours,"
                " completed, completed_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (t["id"], t["owner_id"], t["title"], t["subject"], at(t["deadline_offset_hours"]),
                 t["difficulty"], t["estimated_hours"], 1 if t["completed"] else 0, completed_at,
                 at(t["created_offset_hours"]), at(t["created_offset_hours"])))
    return f"{len(data['users'])} users, {len(data['tasks'])} tasks"
