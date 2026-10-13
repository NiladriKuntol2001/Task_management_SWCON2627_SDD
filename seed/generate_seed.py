"""Generate seed/seed-data.json — sample data AND an independent test oracle.

The expected priority for every open task is computed here from spec.md with its own
code (integer tenths, written separately from backend/app/priority.py), so the API's
answers can be checked against it (task T037, success criterion SC-001).

Run:  python seed/generate_seed.py
"""
import json
from pathlib import Path

OUT = Path(__file__).with_name("seed-data.json")

DIFFICULTY = {"Easy": 20, "Medium": 50, "Hard": 80, "Very Hard": 100}


def deadline_points(hours_left: float) -> int:
    """spec.md table + clarification: whole days = floor(hours / 24)."""
    if hours_left < 0:
        return 100
    days = int(hours_left // 24)
    if days == 0:
        return 100
    if days <= 2:
        return 75
    if days <= 6:
        return 50
    if days <= 14:
        return 25
    return 10


def expected(hours_left: float, difficulty: str, est_hours: float) -> dict:
    d = deadline_points(hours_left)
    f = DIFFICULTY[difficulty]
    t10 = min(round(est_hours * 100), 1000)          # time score x10, as an integer
    tenths = d * 5 + f * 3 + t10 * 2 // 10            # exact score x10 (inputs keep this whole)
    assert (t10 * 2) % 10 == 0, "seed hours must give a whole number of tenths"
    shown = (tenths + 5) // 10                        # round half up
    level = "Critical" if shown >= 80 else "High" if shown >= 60 else "Medium" if shown >= 40 else "Low"
    return {"deadline_score": d, "difficulty_score": f, "time_score": t10 / 10,
            "priority_score": tenths / 10, "display_score": shown, "level": level,
            "overdue": hours_left < 0}


USERS = [
    {"id": 1, "name": "Main Admin", "email": "admin123@gmail.com", "password": "admin@123", "role": "admin", "is_active": True, "joined_days_ago": 30},
    {"id": 2, "name": "Niladri Saha", "email": "niladri@student.test", "password": "Student@123", "role": "student", "is_active": True, "joined_days_ago": 21},
    {"id": 3, "name": "Zahra", "email": "zahra@student.test", "password": "Student@123", "role": "student", "is_active": True, "joined_days_ago": 21},
    {"id": 4, "name": "Khadija", "email": "khadija@student.test", "password": "Student@123", "role": "student", "is_active": True, "joined_days_ago": 20},
    {"id": 5, "name": "Aino Virtanen", "email": "aino@student.test", "password": "Student@123", "role": "student", "is_active": True, "joined_days_ago": 18},
    {"id": 6, "name": "Mikael Lindqvist", "email": "mikael@student.test", "password": "Student@123", "role": "student", "is_active": True, "joined_days_ago": 16},
    {"id": 7, "name": "Sara Ahmed", "email": "sara@student.test", "password": "Student@123", "role": "student", "is_active": False, "joined_days_ago": 15},
]

# owner, title, subject, deadline offset (hours from load), difficulty, hours, completed
TASKS = [
    (2, "Security lab: STRIDE threat model", "Software Security", 14.5, "Hard", 8, False),
    (2, "Finnish 1 oral exam", "Finnish 1", 13.5, "Medium", 3, False),
    (2, "Algorithms problem set 4", "Algorithms", 37.5, "Very Hard", 5, False),
    (2, "SDD comparison report draft", "Software Design", 40.5, "Hard", 6, False),
    (2, "Finnish listening exercise", "Finnish 1", 85.5, "Easy", 1, False),
    (2, "Thesis chapter 2 draft", "Thesis", 93.5, "Very Hard", 10, False),
    (2, "Group presentation slides", "Software Design", 112.5, "Medium", 4, False),
    (2, "Cloud computing lab 3", "Cloud Computing", 184.5, "Hard", 6, False),
    (2, "Database normalization exercises", "Databases", 236.5, "Medium", 2, False),
    (2, "Software Security midterm prep", "Software Security", 326.5, "Very Hard", 12, False),
    (2, "Thesis literature review notes", "Thesis", 448.5, "Hard", 9, False),
    (2, "Parnas paper summary", "Software Design", 496.5, "Easy", 2, False),
    (2, "Scalability quiz reflection", "Software Design", -43.5, "Easy", 1, False),
    (2, "Design for Change quiz", "Software Design", -79.5, "Medium", 2, True),
    (2, "Finnish vocabulary set 3", "Finnish 1", -106.5, "Easy", 1, True),
    (2, "Cloud computing reading week 6", "Cloud Computing", -30.0, "Easy", 2, True),
    (2, "SDLC lecture notes", "Software Design", -150.0, "Medium", 3, True),
    (3, "Write acceptance criteria for FR-01 to FR-10", "Software Design", 20.0, "Hard", 5, False),
    (3, "Statistics assignment 2", "Statistics", 44.0, "Medium", 4, False),
    (3, "UX research interview notes", "Human-Computer Interaction", 100.0, "Medium", 3, False),
    (3, "Machine learning project proposal", "Machine Learning", 200.0, "Very Hard", 10, False),
    (3, "Statistics weekly quiz", "Statistics", -5.0, "Easy", 1, True),
    (3, "Finnish 1 homework 5", "Finnish 1", 400.0, "Easy", 2, False),
    (4, "Write pytest cases for priority module", "Software Design", 30.0, "Hard", 6, False),
    (4, "Computer networks lab report", "Computer Networks", 6.0, "Medium", 4, False),
    (4, "Networks exam revision", "Computer Networks", 130.0, "Very Hard", 12, False),
    (4, "Operating systems reading", "Operating Systems", 250.0, "Easy", 2, False),
    (4, "Security lab: password hashing", "Software Security", -20.0, "Medium", 3, True),
    (4, "Peer review of Zahra's spec", "Software Design", -2.0, "Easy", 1, False),
    (5, "Data visualisation poster", "Data Visualisation", 90.0, "Medium", 5, False),
    (5, "Research methods essay", "Research Methods", 300.0, "Hard", 8, False),
    (5, "Python exercises week 7", "Programming", 10.0, "Easy", 2, False),
    (5, "Python exercises week 6", "Programming", -150.0, "Easy", 2, True),
    (6, "Embedded systems project demo", "Embedded Systems", 40.0, "Very Hard", 9, False),
    (6, "Signal processing homework", "Signal Processing", -60.0, "Hard", 4, False),
    (6, "Signal processing exam", "Signal Processing", 500.0, "Very Hard", 15, False),
    (6, "Lab safety quiz", "Embedded Systems", -200.0, "Easy", 1, True),
    (7, "Intro to databases quiz", "Databases", 120.0, "Easy", 1, False),
    (7, "SQL practice set", "Databases", -100.0, "Medium", 2, True),
]

# Activity over the last 14 days for the admin trend chart (index 13 = today).
CREATED_PER_DAY = [1, 3, 2, 4, 2, 1, 3, 5, 2, 3, 4, 2, 3, 4]
COMPLETED_PER_DAY = [0, 1, 0, 1, 0, 0, 1, 2, 0, 1, 1, 0, 1, 1]

# Resolved edge cases from the 2026-10-13 clarifications (used by tests).
EDGE_CASES = [
    {"case": "exactly 24 h left", "deadline_offset_hours": 24.0, "difficulty": "Easy", "estimated_hours": 1},
    {"case": "60 h left (2.5 days)", "deadline_offset_hours": 60.0, "difficulty": "Easy", "estimated_hours": 1},
    {"case": "156 h left (6.5 days)", "deadline_offset_hours": 156.0, "difficulty": "Easy", "estimated_hours": 1},
    {"case": "exactly 14 days left", "deadline_offset_hours": 336.0, "difficulty": "Easy", "estimated_hours": 1},
    {"case": "exactly 15 days left", "deadline_offset_hours": 360.0, "difficulty": "Easy", "estimated_hours": 1},
    {"case": "exact score 79.5 shows 80", "deadline_offset_hours": 30.0, "difficulty": "Very Hard", "estimated_hours": 6},
]


def day_list(per_day):
    return [d for d, n in enumerate(per_day) for _ in range(n)]


def build() -> dict:
    assert sum(CREATED_PER_DAY) == len(TASKS)
    done_ids = [i for i, t in enumerate(TASKS, start=1) if t[6]]
    assert sum(COMPLETED_PER_DAY) == len(done_ids)

    created_days = day_list(CREATED_PER_DAY)          # ascending
    completed_days = day_list(COMPLETED_PER_DAY)
    # Completed tasks take the earliest creation days so creation never follows completion.
    order = done_ids + [i for i in range(1, len(TASKS) + 1) if i not in done_ids]
    created_for = {task_id: created_days[k] for k, task_id in enumerate(order)}
    completed_for = dict(zip(done_ids, completed_days))

    tasks = []
    for i, (owner, title, subject, off, diff, hrs, done) in enumerate(TASKS, start=1):
        created = -(13 - created_for[i]) * 24 - 0.5
        entry = {"id": i, "owner_id": owner, "title": title, "subject": subject,
                 "deadline_offset_hours": off, "difficulty": diff, "estimated_hours": hrs,
                 "completed": done, "created_offset_hours": created}
        if done:
            entry["completed_offset_hours"] = -(13 - completed_for[i]) * 24 - 0.25
            assert entry["completed_offset_hours"] > created
        entry["expected"] = None if done else expected(off, diff, hrs)
        tasks.append(entry)

    for case in EDGE_CASES:
        case["expected"] = expected(case["deadline_offset_hours"], case["difficulty"], case["estimated_hours"])

    open_tasks = [t for t in tasks if not t["completed"]]
    by_level = {lvl: sum(t["expected"]["level"] == lvl for t in open_tasks)
                for lvl in ("Critical", "High", "Medium", "Low")}
    return {
        "about": ("Sample data for StudyFlow SDD v1. Times are hour offsets from the moment the data is "
                  "loaded. 'expected' is the priority spec.md requires, computed independently; use it "
                  "as a test oracle."),
        "formula": "score = deadline*0.50 + difficulty*0.30 + min(hours*10,100)*0.20; "
                   "deadline band from floor(hours_left/24); level from the score rounded half up",
        "users": USERS,
        "tasks": tasks,
        "edge_cases": EDGE_CASES,
        "summary": {"users": len(USERS), "tasks": len(tasks), "open": len(open_tasks),
                    "completed": len(tasks) - len(open_tasks),
                    "overdue": sum(t["expected"]["overdue"] for t in open_tasks),
                    "open_by_level": by_level},
    }


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(data["summary"], indent=2))
