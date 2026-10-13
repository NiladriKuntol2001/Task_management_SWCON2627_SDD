"""FR-21 / NFR-05 — a student can never see or change another user's tasks."""
from backend.tests.support import ApiTestCase, in_hours


class Isolation(ApiTestCase):
    def setUp(self):
        self.owner = self.student("Owner")
        self.other = self.student("Intruder")
        self.task = self.make_task(self.owner, title="Private")

    def test_list_shows_only_own_tasks(self):
        self.make_task(self.other, title="Mine")
        self.assertEqual([t["title"] for t in self.other.get("/api/tasks?status=all")[1]["tasks"]], ["Mine"])

    def test_foreign_task_looks_missing_on_every_operation(self):
        tid = self.task["id"]
        body = {"title": "Hacked", "subject": "S", "deadline": in_hours(5), "difficulty": "Easy", "estimated_hours": 1}
        missing = self.other.get("/api/tasks/999999")
        for status, resp in (self.other.get(f"/api/tasks/{tid}"),
                             self.other.put(f"/api/tasks/{tid}", body),
                             self.other.patch(f"/api/tasks/{tid}/complete", {"completed": True}),
                             self.other.delete(f"/api/tasks/{tid}")):
            self.assertEqual(status, 404)
            self.assertEqual(resp, missing[1], "foreign task must be indistinguishable from a missing one")
        status, still = self.owner.get(f"/api/tasks/{tid}")
        self.assertEqual(status, 200)
        self.assertEqual(still["title"], "Private")
        self.assertFalse(still["completed"])

    def test_dashboard_counts_only_own_tasks(self):
        self.assertEqual(self.other.get("/api/dashboard")[1]["counts"]["incomplete"], 0)
        self.assertEqual(self.owner.get("/api/dashboard")[1]["counts"]["incomplete"], 1)
