"""Start StudyFlow (API + frontend) with one command.

    python run.py                 # start, keep existing data
    python run.py --seed          # load sample data if the database has no tasks
    python run.py --reset --seed  # delete the database and start fresh with sample data
"""
import argparse
import os
import sys

import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import config  # noqa: E402
from backend.app.db import init_db, reset_db  # noqa: E402
from backend.app.main import create_app  # noqa: E402
from backend.app.seed import load_seed  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run StudyFlow")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--seed", action="store_true", help="load sample data into an empty database")
    parser.add_argument("--reset", action="store_true", help="delete the database first")
    args = parser.parse_args()

    settings = config.get_settings()
    if args.reset:
        reset_db(settings.db_path)
    init_db(settings.db_path, settings.main_admin_email, settings.main_admin_password)
    if args.seed:
        added = load_seed(settings.db_path)
        print(f"Sample data: {added}" if added else "Sample data: database already has tasks, nothing loaded")

    print(f"StudyFlow running on http://{args.host}:{args.port}  (database: {settings.db_path})")
    uvicorn.run(create_app(settings), host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
