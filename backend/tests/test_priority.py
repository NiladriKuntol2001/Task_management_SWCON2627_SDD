"""US3 — priority engine (FR-11..FR-14). Written from spec.md before priority.py."""
import unittest
from datetime import datetime, timedelta, timezone

from backend.app import priority

NOW = datetime(2026, 10, 12, 16, 30, tzinfo=timezone.utc)


def at(hours: float) -> datetime:
    return NOW + timedelta(hours=hours)


class DeadlineBands(unittest.TestCase):
    def check(self, hours, expected):
        self.assertEqual(priority.score(at(hours), "Easy", 1, NOW)["deadline_score"], expected,
                         f"{hours} h before deadline")

    def test_overdue_is_100(self):
        self.check(-0.01, 100)
        self.check(-300, 100)

    def test_less_than_24_hours_is_100(self):
        self.check(0, 100)
        self.check(23.99, 100)

    def test_one_to_two_whole_days_is_75(self):
        self.check(24, 75)          # clarified: exactly 24 h = 1 whole day
        self.check(47.9, 75)
        self.check(60, 75)          # clarified: 2.5 days -> 2 whole days
        self.check(71.99, 75)

    def test_three_to_six_whole_days_is_50(self):
        self.check(72, 50)
        self.check(156, 50)         # clarified: 6.5 days -> 6
        self.check(167.99, 50)

    def test_seven_to_fourteen_whole_days_is_25(self):
        self.check(168, 25)
        self.check(336, 25)         # clarified: exactly 14 days -> 25
        self.check(359.99, 25)

    def test_fifteen_days_or_more_is_10(self):
        self.check(360, 10)
        self.check(5000, 10)


class Components(unittest.TestCase):
    def test_difficulty_scores(self):
        for level, expected in {"Easy": 20, "Medium": 50, "Hard": 80, "Very Hard": 100}.items():
            self.assertEqual(priority.score(at(500), level, 1, NOW)["difficulty_score"], expected)

    def test_time_score_is_hours_times_ten_capped_at_100(self):
        for hours, expected in [(1, 10), (3, 30), (5, 50), (8, 80), (10, 100), (12, 100), (1.5, 15)]:
            self.assertEqual(priority.score(at(500), "Easy", hours, NOW)["time_score"], expected)

    def test_weights_are_50_30_20(self):
        p = priority.score(at(14.5), "Hard", 8, NOW)
        self.assertEqual((p["deadline_part"], p["difficulty_part"], p["time_part"]), (50.0, 24.0, 16.0))
        self.assertEqual(p["exact"], 90.0)
        self.assertEqual(p["score"], 90)
        self.assertEqual(p["level"], "Critical")


class RoundingAndLevels(unittest.TestCase):
    def test_spec_example_stride(self):
        p = priority.score(at(14.5), "Hard", 8, NOW)
        self.assertEqual((p["score"], p["level"]), (90, "Critical"))

    def test_half_rounds_up(self):
        p = priority.score(at(40.5), "Hard", 6, NOW)       # 37.5 + 24 + 12 = 73.5
        self.assertEqual(p["exact"], 73.5)
        self.assertEqual(p["score"], 74)

    def test_level_follows_shown_score_at_79_5(self):
        # 75*0.5 + 100*0.3 + 60*0.2 ... = 37.5 + 30 + 12 = 79.5 -> shown 80 -> Critical
        p = priority.score(at(30), "Very Hard", 6, NOW)
        self.assertEqual(p["exact"], 79.5)
        self.assertEqual((p["score"], p["level"]), (80, "Critical"))

    def test_level_boundaries(self):
        cases = [(at(500), "Easy", 1, 13, "Low"),          # 5 + 6 + 2
                 (at(100), "Medium", 5, 50, "Medium"),     # 25 + 15 + 10
                 (at(10), "Easy", 2, 60, "High"),          # 50 + 6 + 4 = 60 exactly
                 (at(40), "Very Hard", 9, 86, "Critical")] # 37.5 + 30 + 18 = 85.5 -> 86
        for deadline, diff, hours, shown, level in cases:
            p = priority.score(deadline, diff, hours, NOW)
            self.assertEqual((p["score"], p["level"]), (shown, level), (diff, hours))

    def test_classify_table(self):
        for value, level in [(100, "Critical"), (80, "Critical"), (79, "High"), (60, "High"),
                             (59, "Medium"), (40, "Medium"), (39, "Low"), (0, "Low")]:
            self.assertEqual(priority.classify(value), level)

    def test_days_left_and_overdue_flag(self):
        self.assertEqual(priority.score(at(60), "Easy", 1, NOW)["days_left"], 2)
        p = priority.score(at(-43.5), "Easy", 1, NOW)
        self.assertTrue(p["overdue"])
        self.assertEqual(p["score"], 58)


class Ordering(unittest.TestCase):
    def test_tie_on_shown_score_earlier_deadline_first(self):
        a = {"id": 1, "deadline": at(130), "created_at": at(-10), "priority": {"score": 75}}
        b = {"id": 2, "deadline": at(93.5), "created_at": at(-5), "priority": {"score": 75}}
        c = {"id": 3, "deadline": at(10), "created_at": at(-1), "priority": {"score": 60}}
        ordered = sorted([a, c, b], key=priority.sort_key)
        self.assertEqual([t["id"] for t in ordered], [2, 1, 3])

    def test_full_tie_earlier_created_first(self):
        a = {"id": 1, "deadline": at(50), "created_at": at(-1), "priority": {"score": 70}}
        b = {"id": 2, "deadline": at(50), "created_at": at(-9), "priority": {"score": 70}}
        self.assertEqual([t["id"] for t in sorted([a, b], key=priority.sort_key)], [2, 1])

    def test_completed_tasks_sort_after_open_tasks(self):
        done = {"id": 1, "deadline": at(1), "created_at": at(-1), "priority": None}
        open_ = {"id": 2, "deadline": at(500), "created_at": at(-1), "priority": {"score": 5}}
        self.assertEqual([t["id"] for t in sorted([done, open_], key=priority.sort_key)], [2, 1])


if __name__ == "__main__":
    unittest.main()
