"""T037 / SC-001 — load the sample data and check every open task's score and level
against the independent oracle in seed/seed-data.json; check dashboard (US5) and
admin overview (FR-27) figures for the sample data; time the API (NFR-01)."""
import json
import time

from backend.app.seed import SEED_FILE, load_seed
from backend.tests.support import ApiTestCase, Client

DATA = json.loads(SEED_FILE.read_text(encoding="utf-8"))


class SeedOracle(ApiTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_seed(cls.live.settings.db_path)

    def login(self, email, password="Student@123") -> Client:
        status, body = self.client().post("/api/auth/login", {"email": email, "password": password})
        self.assertEqual(status, 200, body)
        return self.client(body["token"])

    def test_every_open_task_matches_oracle(self):
        admin = self.login("admin123@gmail.com", "admin@123")
        api = {t["id"]: t for t in admin.get("/api/admin/tasks")[1]["tasks"]}
        oracle = [t for t in DATA["tasks"] if t["expected"]]
        self.assertEqual(len(api), len(oracle))
        mismatches = []
        for t in oracle:
            got, want = api[t["id"]]["priority"], t["expected"]
            if (got["score"], got["level"], got["deadline_score"], got["overdue"]) != \
                    (want["display_score"], want["level"], want["deadline_score"], want["overdue"]):
                mismatches.append((t["title"], got, want))
        self.assertEqual(mismatches, [])

    def test_edge_cases_match_oracle(self):
        s = self.login("niladri@student.test")
        from backend.tests.support import in_hours
        for case in DATA["edge_cases"]:
            # The server reads the clock a moment after we do, so a deadline exactly on a day
            # boundary arrives a fraction early. With time rounded up (D1), k days minus a minute
            # is still k days for k >= 2; only "exactly 24 h" needs a minute added (else < 24 h).
            # Exact boundaries are unit-tested with a fixed clock in test_priority.
            offset = case["deadline_offset_hours"]
            offset += 1 / 60 if offset == 24 else -1 / 60
            _, p = s.post("/api/priority/preview", {"deadline": in_hours(offset),
                                                    "difficulty": case["difficulty"],
                                                    "estimated_hours": case["estimated_hours"]})
            want = case["expected"]
            self.assertEqual((p["deadline_score"], p["score"], p["level"]),
                             (want["deadline_score"], want["display_score"], want["level"]), case["case"])

    def test_niladri_dashboard_matches_spec_us5(self):
        body = self.login("niladri@student.test").get("/api/dashboard")[1]
        c = body["counts"]
        self.assertEqual((c["incomplete"], c["completed"], c["high_priority"], c["critical"], c["overdue"]),
                         (13, 4, 6, 1, 1))
        self.assertEqual(body["recommendation"]["title"], "Security lab: STRIDE threat model")
        self.assertEqual(body["recommendation"]["priority"]["score"], 90)
        self.assertEqual(c["due_this_week"], 7)

    def test_admin_overview_matches_sample(self):
        o = self.login("admin123@gmail.com", "admin@123").get("/api/admin/overview")[1]
        self.assertEqual(o["students"], {"total": 6, "active": 5, "deactivated": 1})
        self.assertEqual(o["tasks"], {"total": 39, "open": 30, "completed": 9})
        self.assertEqual(o["by_level"], DATA["summary"]["open_by_level"])
        self.assertEqual(o["overdue"], {"tasks": 3, "students": 3})
        self.assertEqual(sum(d["created"] for d in o["trend"]), 39)
        self.assertEqual(sum(d["completed"] for d in o["trend"]), 9)
        self.assertEqual(o["attention"][0]["name"], "Mikael Lindqvist")

    def test_deactivated_sample_user_cannot_sign_in(self):
        status, _ = self.client().post("/api/auth/login", {"email": "sara@student.test", "password": "Student@123"})
        self.assertEqual(status, 403)

    def test_api_response_times_under_2_seconds(self):
        s = self.login("niladri@student.test")
        admin = self.login("admin123@gmail.com", "admin@123")
        slowest = 0.0
        for client, path in [(s, "/api/dashboard"), (s, "/api/tasks?status=all"), (s, "/api/me"),
                             (admin, "/api/admin/overview"), (admin, "/api/admin/users"), (admin, "/api/admin/tasks")]:
            start = time.perf_counter()
            self.assertEqual(client.get(path)[0], 200)
            slowest = max(slowest, time.perf_counter() - start)
        self.assertLess(slowest, 2.0)
