"""Settings, read from environment variables with safe local defaults."""
import os
import secrets
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    db_path: str
    secret_key: str
    token_hours: int
    frontend_dir: str
    main_admin_email: str
    main_admin_password: str


def _secret(db_path: str) -> str:
    """Use STUDYFLOW_SECRET if set; otherwise a random key kept next to the database,
    so tokens survive restarts but the key is never committed."""
    env = os.environ.get("STUDYFLOW_SECRET")
    if env:
        return env
    key_file = Path(db_path).with_suffix(".key")
    if key_file.exists():
        return key_file.read_text().strip()
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_urlsafe(48)
    key_file.write_text(key)
    return key


def get_settings(db_path: str | None = None) -> Settings:
    path = db_path or os.environ.get("STUDYFLOW_DB", str(ROOT / "data" / "studyflow.db"))
    return Settings(
        db_path=path,
        secret_key=_secret(path),
        token_hours=int(os.environ.get("STUDYFLOW_TOKEN_HOURS", "8")),
        frontend_dir=str(ROOT / "frontend"),
        main_admin_email=os.environ.get("STUDYFLOW_ADMIN_EMAIL", "admin123@gmail.com"),
        main_admin_password=os.environ.get("STUDYFLOW_ADMIN_PASSWORD", "admin@123"),
    )
