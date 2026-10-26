"""The priority formula (spec.md "Priority Calculation", FR-11..FR-14).

LOCKED by the constitution (principle II): weights, bands and thresholds are copied
from the team's official requirements and the team decisions D1 (time left rounded UP
to whole days, issue #1) and D2 (ties only on equal exact score, issue #2). This is the
only place in the system that knows them; everything else calls score() / sort_key().
"""
import math
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

# Weights in percent: deadline 50, difficulty 30, time 20.
_WEIGHTS = (50, 30, 20)
_DIFFICULTY = {"Easy": 20, "Medium": 50, "Hard": 80, "Very Hard": 100}
# (max days after rounding up, score); checked in order. Under 24 h / overdue first.
_DEADLINE_BANDS = ((2, 75), (6, 50), (14, 25))
_FAR_AWAY = 10
_LEVELS = ((80, "Critical"), (60, "High"), (40, "Medium"), (0, "Low"))


def days_counted(hours_left: float) -> int:
    """Days used for the band: 0 under 24 h, otherwise ceil(hours / 24) (D1).
    Negative (floor) when the deadline has passed."""
    if hours_left < 0:
        return math.floor(hours_left / 24)
    if hours_left < 24:
        return 0
    return math.ceil(hours_left / 24)


def deadline_score(hours_left: float) -> int:
    if hours_left < 24:                     # overdue (negative) or less than 24 hours
        return 100
    days = math.ceil(hours_left / 24)       # D1: round the time left UP to whole days
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
        "days_left": days_counted(hours_left),
        "overdue": hours_left < 0,
        "deadline_score": int(d),
        "difficulty_score": int(f),
        "time_score": _num(t),
        "deadline_part": float(parts[0]),
        "difficulty_part": float(parts[1]),
        "time_part": float(parts[2]),
    }


def sort_key(task: dict):
    """FR-14 / D2: exact score high→low, then earlier deadline, then earlier creation.
    The shown whole-number score is for display only (issue #2: 78.4 and 77.5 both
    show 78, but 78.4 must come first). Completed tasks (priority None) come last."""
    p = task.get("priority")
    if p is None:
        return (1, 0, task["deadline"], task["created_at"], task["id"])
    return (0, -p["exact"], task["deadline"], task["created_at"], task["id"])
