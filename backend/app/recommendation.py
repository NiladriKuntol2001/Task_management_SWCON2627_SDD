"""'What should I work on today?' (FR-20) and dashboard figures (FR-19)."""
from datetime import timedelta

from .db import from_iso
from .tasks_repo import sort_by_deadline, sort_by_priority

UPCOMING_DAYS = 7   # clarified 2026-10-13


def recommend(tasks: list[dict]) -> dict | None:
    """First incomplete task in priority order (overdue tasks included), or None."""
    open_tasks = [t for t in tasks if not t["completed"]]
    return sort_by_priority(open_tasks)[0] if open_tasks else None


def upcoming(tasks: list[dict], now) -> list[dict]:
    """FR-17: incomplete, not overdue, due within the next 7 days, earliest first."""
    limit = now + timedelta(days=UPCOMING_DAYS)
    return sort_by_deadline([t for t in tasks if not t["completed"] and not t["overdue"]
                             and from_iso(t["deadline"]) <= limit])


def overdue(tasks: list[dict]) -> list[dict]:
    return sort_by_deadline([t for t in tasks if t["overdue"]])


def summary(tasks: list[dict], now) -> dict:
    open_tasks = [t for t in tasks if not t["completed"]]
    done = len(tasks) - len(open_tasks)
    mix = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for t in open_tasks:
        mix[t["priority"]["level"]] += 1
    soon = upcoming(tasks, now)
    return {
        "counts": {
            "incomplete": len(open_tasks),
            "completed": done,
            "high_priority": mix["Critical"] + mix["High"],
            "critical": mix["Critical"],
            "overdue": sum(1 for t in open_tasks if t["overdue"]),
            "due_this_week": len(soon),
            "completion_percent": round(100 * done / len(tasks)) if tasks else 0,
        },
        "mix": mix,
        "recommendation": recommend(tasks),
        "upcoming": soon,
        "overdue": overdue(tasks),
    }
