"""Independent verification of the priority rules (FR-11, FR-12, FR-13, FR-18) on the SDD build.

Every expected value was calculated BY HAND from the team specification (Section 3)
and the team decisions D1-D4. None was obtained by running the code. Same cases and
IDs as on the Vibe Coding build.

This build exposes one function, priority.score(), which returns the exact score
("exact"), a whole-number score for display ("score") and the level. The oracle checks
the exact score, so hand values such as 77.5 are compared without rounding.

Former deviation SDD-01 (days left rounded down, GitHub issue #1) was fixed on 26 Oct 2026:
the build now rounds up as team decision D1 says, so its strict-xfail markers were removed.
"""
from datetime import datetime, timedelta, timezone

import pytest

from backend.app import priority

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


def deadline_score(deadline, now=NOW):
    return priority.deadline_score((deadline - now).total_seconds() / 3600)


def compute(deadline, difficulty, hours, now=NOW):
    p = priority.score(deadline, difficulty, hours, now)
    return p["exact"], p["level"]


# --- TC-PRI-01: one value inside each deadline band -------------------------
@pytest.mark.parametrize(
    "delta, expected",
    [(timedelta(days=30), 10), (timedelta(days=10), 25), (timedelta(days=4), 50),
     (timedelta(hours=36), 75), (timedelta(hours=12), 100), (timedelta(hours=-1), 100)],
)
def test_TC_PRI_01_deadline_score_inside_each_band(delta, expected):
    assert deadline_score(NOW + delta) == expected


# --- TC-PRI-02: band edges ---------------------------------------------------
@pytest.mark.parametrize(
    "delta, expected",
    [
        (timedelta(seconds=-1), 100),             # just overdue
        (timedelta(0), 100),                      # due right now: < 24 hours
        (timedelta(hours=23, minutes=59), 100),   # "Less than 24 hours"
        (timedelta(hours=24), 75),                # exactly 1 day
        (timedelta(hours=48), 75),                # exactly 2 days
        (timedelta(hours=72), 50),                # exactly 3 days
        (timedelta(hours=144), 50),               # exactly 6 days
        (timedelta(hours=168), 25),               # exactly 7 days
        (timedelta(hours=336), 25),               # exactly 14 days
        (timedelta(hours=336, minutes=1), 10),  # "More than 14 days"
    ],
)
def test_TC_PRI_02_deadline_band_edges(delta, expected):
    assert deadline_score(NOW + delta) == expected


# --- TC-PRI-02g: times between the spec's bands (team decision D1) -----------
@pytest.mark.parametrize(
    "delta, expected",
    [(timedelta(hours=49), 50), (timedelta(hours=60), 50), (timedelta(hours=71), 50),
     (timedelta(hours=145), 25), (timedelta(hours=156), 25), (timedelta(hours=167), 25),
     (timedelta(hours=337), 10)],
)
def test_TC_PRI_02g_remaining_time_is_rounded_up_to_whole_days(delta, expected):
    assert deadline_score(NOW + delta) == expected


# --- TC-PRI-03 / 04: difficulty and time scores -----------------------------
@pytest.mark.parametrize("difficulty, expected",
                         [("Easy", 20), ("Medium", 50), ("Hard", 80), ("Very Hard", 100)])
def test_TC_PRI_03_difficulty_scores(difficulty, expected):
    assert priority.score(NOW + timedelta(days=30), difficulty, 1, NOW)["difficulty_score"] == expected


@pytest.mark.parametrize("hours, expected",
                         [(0.1, 1), (0.5, 5), (1, 10), (3, 30), (5, 50), (8, 80), (9.9, 99), (10, 100), (25, 100)])
def test_TC_PRI_04_time_score_is_min_of_hours_times_10_and_100(hours, expected):
    assert float(priority.time_score(hours)) == pytest.approx(expected)


# --- TC-PRI-05: hand-calculated worked examples -----------------------------
@pytest.mark.parametrize(
    "delta, difficulty, hours, expected_score, expected_level",
    [
        (timedelta(hours=12), "Very Hard", 10, 100, "Critical"),  # E1: 50+30+20
        (timedelta(days=30), "Easy", 1, 13, "Low"),               # E2: 5+6+2
        (timedelta(days=4), "Medium", 5, 50, "Medium"),           # E3: 25+15+10
        (timedelta(hours=36), "Hard", 8, 77.5, "High"),           # E4: 37.5+24+16
        (timedelta(days=10), "Very Hard", 10, 62.5, "High"),      # E5: 12.5+30+20
        (timedelta(days=-1), "Easy", 1, 58, "Medium"),            # E6: 50+6+2 (overdue)
    ],
    ids=["E1", "E2", "E3", "E4", "E5", "E6"],
)
def test_TC_PRI_05_worked_examples(delta, difficulty, hours, expected_score, expected_level):
    s, lvl = compute(NOW + delta, difficulty, hours)
    assert s == pytest.approx(expected_score)
    assert lvl == expected_level


# --- TC-PRI-06: score always within 0-100 -----------------------------------
def test_TC_PRI_06_score_range_and_extremes():
    assert compute(NOW + timedelta(days=30), "Easy", 0.1)[0] == pytest.approx(11.2)
    assert compute(NOW + timedelta(hours=12), "Very Hard", 10)[0] == pytest.approx(100)
    for offset in (timedelta(days=-9), timedelta(hours=1), timedelta(days=3), timedelta(days=400)):
        for diff in ("Easy", "Medium", "Hard", "Very Hard"):
            for hours in (0.01, 1, 10, 1000):
                assert 0 <= compute(NOW + offset, diff, hours)[0] <= 100


# --- TC-PRI-07 / 08 / 09: classification boundaries (one input flips level) --
@pytest.mark.parametrize(
    "case, below, above",
    [
        ((timedelta(hours=12), "Medium", 7, 7.5), (79, "High"), (80, "Critical")),  # B1
        ((timedelta(days=4), "Hard", 5, 5.5), (59, "Medium"), (60, "High")),        # B2
        ((timedelta(days=4), "Easy", 4, 4.5), (39, "Low"), (40, "Medium")),         # B3
    ],
    ids=["TC-PRI-07", "TC-PRI-08", "TC-PRI-09"],
)
def test_TC_PRI_07_08_09_classification_boundaries(case, below, above):
    delta, diff, hours_below, hours_above = case
    s1, l1 = compute(NOW + delta, diff, hours_below)
    s2, l2 = compute(NOW + delta, diff, hours_above)
    assert s1 == pytest.approx(below[0]) and l1 == below[1]
    assert s2 == pytest.approx(above[0]) and l2 == above[1]


@pytest.mark.parametrize("value, lvl", [(0, "Low"), (39, "Low"), (40, "Medium"), (59, "Medium"),
                                        (60, "High"), (79, "High"), (80, "Critical"), (100, "Critical")])
def test_TC_PRI_07_classify_whole_number_scores(value, lvl):
    assert priority.classify(value) == lvl


def test_TC_PRI_10_spec_gap_decimal_score_between_79_and_80():
    """SPEC-GAP-2: 79.8 is in neither '60-79' nor '80-100'. Both readings accepted;
    this build rounds to 80 first, so it says Critical (recorded for the comparison)."""
    s, lvl = compute(NOW + timedelta(hours=12), "Medium", 7.4)  # 50 + 15 + 14.8
    assert s == pytest.approx(79.8)
    assert lvl in {"High", "Critical"}


# --- TC-PRI-14: urgency rises as time passes --------------------------------
def test_TC_PRI_14_score_changes_as_the_deadline_approaches():
    deadline = NOW + timedelta(days=4)
    assert compute(deadline, "Medium", 5)[0] == pytest.approx(50)                                     # 25+15+10
    assert compute(deadline, "Medium", 5, NOW + timedelta(days=3, hours=12))[0] == pytest.approx(75)  # 50+15+10
