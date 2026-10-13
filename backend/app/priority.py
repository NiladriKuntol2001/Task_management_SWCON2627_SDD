"""The priority formula (spec.md "Priority Calculation", FR-11..FR-14).

LOCKED by the constitution (principle II): weights, bands and thresholds are copied
from the team's official requirements and the 2026-10-13 clarifications. This is the
only place in the system that knows them; everything else calls score() / sort_key().
"""
import math
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

# Weights in percent: deadline 50, difficulty 30, time 20.
_WEIGHTS = (50, 30, 20)
_DIFFICULTY = {"Easy": 20, "Medium": 50, "Hard": 80, "Very Hard": 100}
# (max whole days left, score); checked in order. Overdue handled separately.
_DEADLINE_BANDS = ((0, 100), (2, 75), (6, 50), (14, 25))
_FAR_AWAY = 10
_LEVELS = ((80, "Critical"), (60, "High"), (40, "Medium"), (0, "Low"))


def deadline_score(hours_left: float) -> int:
    if hours_left < 0:
        return 100                          # overdue
    days = math.floor(hours_left / 24)      # clarified: whole days left
    for max_days, value in _DEADLINE_BANDS:
        if days <= max_days:
            return value
    return _FAR_AWAY


def time_score(estimated_hours: float) -> Decimal:
    return min(Decimal(str(estimated_hours)) * 10, Decimal(100))


def classify(shown_score: int) -> str:
    for minimum, level in _LEVELS:
        if shown_score >= minimum:
            return level
    return "Low"


def _num(d: Decimal) -> float | int:
    return int(d) if d == d.to_integral_value() else float(d)


def score(deadline: datetime, difficulty: str, estimated_hours: float, now: datetime) -> dict:
    """Full breakdown for one incomplete task at time `now`."""
    hours_left = (deadline - now).total_seconds() / 3600
    d = Decimal(deadline_score(hours_left))
    f = Decimal(_DIFFICULTY[difficulty])
    t = time_score(estimated_hours)
    wd, wf, wt = (Decimal(w) / 100 for w in _WEIGHTS)
    parts = (d * wd, f * wf, t * wt)
    exact = sum(parts)
    shown = int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP))   # clarified: half up
    return {
        "score": shown,
        "exact": _num(exact),
        "level": classify(shown),                                       # clarified: from shown score
        "days_left": math.floor(hours_left / 24),
        "overdue": hours_left < 0,
        "deadline_score": int(d),
        "difficulty_score": int(f),
        "time_score": _num(t),
        "deadline_part": float(parts[0]),
        "difficulty_part": float(parts[1]),
        "time_part": float(parts[2]),
    }


def sort_key(task: dict):
    """FR-14: shown score high→low, then earlier deadline, then earlier creation.
    Completed tasks (priority None) come after all open tasks."""
    p = task.get("priority")
    if p is None:
        return (1, 0, task["deadline"], task["created_at"], task["id"])
    return (0, -p["score"], task["deadline"], task["created_at"], task["id"])
