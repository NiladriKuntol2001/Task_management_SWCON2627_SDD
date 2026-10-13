"""US5 — dashboard and recommendation (FR-19, FR-20)."""
from backend.tests.support import ApiTestCase, in_hours


class Dashboard(ApiTestCase):
    def test_empty_dashboard(self):
        c = self.student()
        body = c.get("/api/dashboard")[1]
        self.assertIsNone(body["recommendation"])
        self.assertEqual(body["counts"]["incomplete"], 0)
        self.assertEqual(body["counts"]["completion_percent"], 0)

    def test_counts_mix_and_recommendation(self):
        c = self.student()
        crit = self.make_task(c, title="Crit", deadline=in_hours(14.5), difficulty="Hard", estimated_hours=8)   # 90
        self.make_task(c, title="High", deadline=in_hours(40), difficulty="Hard", estimated_hours=6)             # 73
        self.make_task(c, title="Late", deadline=in_hours(-5), difficulty="Easy", estimated_hours=1)             # 58
        self.make_task(c, title="Far", deadline=in_hours(500), difficulty="Easy", estimated_hours=1)             # 13
        done = self.make_task(c, title="Done", deadline=in_hours(20))
        c.patch(f"/api/tasks/{done['id']}/complete", {"completed": True})

        body = c.get("/api/dashboard")[1]
        self.assertEqual(body["counts"], {"incomplete": 4, "completed": 1, "high_priority": 2, "critical": 1,
                                          "overdue": 1, "due_this_week": 2, "completion_percent": 20})
        self.assertEqual(body["mix"], {"Critical": 1, "High": 1, "Medium": 1, "Low": 1})
        self.assertEqual(body["recommendation"]["id"], crit["id"])
        self.assertEqual(body["recommendation"]["priority"]["deadline_part"], 50.0)
        self.assertEqual([t["title"] for t in body["upcoming"]], ["Crit", "High"])
        self.assertEqual([t["title"] for t in body["overdue"]], ["Late"])

    def test_recommendation_tie_breaks_on_deadline(self):
        c = self.student()
        self.make_task(c, title="Later", deadline=in_hours(130), difficulty="Very Hard", estimated_hours=12)   # 75
        self.make_task(c, title="Sooner", deadline=in_hours(93.5), difficulty="Very Hard", estimated_hours=10)  # 75
        self.assertEqual(c.get("/api/dashboard")[1]["recommendation"]["title"], "Sooner")

    def test_overdue_task_can_be_recommended(self):
        c = self.student()
        self.make_task(c, title="Overdue hard", deadline=in_hours(-60), difficulty="Hard", estimated_hours=4)  # 82
        self.make_task(c, title="Next week", deadline=in_hours(170), difficulty="Medium", estimated_hours=2)
        self.assertEqual(c.get("/api/dashboard")[1]["recommendation"]["title"], "Overdue hard")
