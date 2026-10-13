"""US2 + US4 — task management, validation, organisation, preview
(FR-04..FR-10, FR-13, FR-15..FR-18, FR-35, NFR-12)."""
from backend.tests.support import ApiTestCase, in_hours


class CreateAndView(ApiTestCase):
    def test_create_returns_task_with_priority(self):
        c = self.student()
        task = self.make_task(c, title="STRIDE", subject="Security", deadline=in_hours(14.5),
                              difficulty="Hard", estimated_hours=8)
        self.assertEqual(task["title"], "STRIDE")
        self.assertFalse(task["completed"])
        self.assertEqual(task["priority"]["score"], 90)
        self.assertEqual(task["priority"]["level"], "Critical")

    def test_view_details_has_breakdown(self):
        c = self.student()
        task = self.make_task(c, deadline=in_hours(40.5), difficulty="Hard", estimated_hours=6)
        status, body = c.get(f"/api/tasks/{task['id']}")
        self.assertEqual(status, 200)
        p = body["priority"]
        self.assertEqual((p["deadline_part"], p["difficulty_part"], p["time_part"], p["score"]), (37.5, 24.0, 12.0, 74))

    def test_decimal_hours_allowed(self):
        c = self.student()
        task = self.make_task(c, estimated_hours=1.5)
        self.assertEqual(task["estimated_hours"], 1.5)
        self.assertEqual(task["priority"]["time_score"], 15)

    def test_past_deadline_allowed_and_overdue(self):
        c = self.student()
        task = self.make_task(c, deadline=in_hours(-3))
        self.assertTrue(task["overdue"])


class Validation(ApiTestCase):
    def post_invalid(self, **overrides):
        c = self.student()
        body = {"title": "T", "subject": "S", "deadline": in_hours(50), "difficulty": "Easy", "estimated_hours": 2}
        body.update(overrides)
        status, resp = c.post("/api/tasks", body)
        self.assertEqual(status, 422)
        self.assertEqual(c.get("/api/tasks?status=all")[1]["tasks"], [], "nothing must be saved (NFR-12)")
        return resp["error"]["fields"]

    def test_empty_title(self):
        self.assertEqual(self.post_invalid(title="   ")["title"], "Title can't be empty.")

    def test_title_too_long(self):
        self.assertIn("200 characters", self.post_invalid(title="x" * 201)["title"])

    def test_empty_subject(self):
        self.assertEqual(self.post_invalid(subject="")["subject"], "Subject can't be empty.")

    def test_bad_deadline(self):
        self.assertEqual(self.post_invalid(deadline="next tuesday")["deadline"], "Enter a valid deadline date and time.")
        self.assertIn("deadline", self.post_invalid(deadline=None))

    def test_hours_zero_negative_text_and_too_big(self):
        self.assertEqual(self.post_invalid(estimated_hours=0)["estimated_hours"], "Estimated hours must be more than 0.")
        self.assertEqual(self.post_invalid(estimated_hours=-2)["estimated_hours"], "Estimated hours must be more than 0.")
        self.assertEqual(self.post_invalid(estimated_hours="lots")["estimated_hours"], "Estimated hours must be a number.")
        self.assertEqual(self.post_invalid(estimated_hours=1001)["estimated_hours"], "Estimated hours must be 1000 or less.")

    def test_bad_difficulty(self):
        self.assertIn("Easy, Medium, Hard or Very Hard", self.post_invalid(difficulty="Impossible")["difficulty"])

    def test_several_errors_reported_together(self):
        fields = self.post_invalid(title="", subject="", estimated_hours=0)
        self.assertEqual(set(fields), {"title", "subject", "estimated_hours"})


class EditCompleteDelete(ApiTestCase):
    def test_edit_recalculates_priority(self):
        c = self.student()
        task = self.make_task(c, deadline=in_hours(500), difficulty="Easy", estimated_hours=1)
        self.assertEqual(task["priority"]["score"], 13)
        body = {"title": "Edited", "subject": "S", "deadline": in_hours(10), "difficulty": "Very Hard", "estimated_hours": 10}
        status, updated = c.put(f"/api/tasks/{task['id']}", body)
        self.assertEqual(status, 200)
        self.assertEqual(updated["title"], "Edited")
        self.assertEqual(updated["priority"]["score"], 100)

    def test_invalid_edit_changes_nothing(self):
        c = self.student()
        task = self.make_task(c, title="Keep me")
        status, _ = c.put(f"/api/tasks/{task['id']}", {"title": "", "subject": "S", "deadline": in_hours(5),
                                                       "difficulty": "Easy", "estimated_hours": 1})
        self.assertEqual(status, 422)
        self.assertEqual(c.get(f"/api/tasks/{task['id']}")[1]["title"], "Keep me")

    def test_complete_and_reopen(self):
        c = self.student()
        task = self.make_task(c)
        status, done = c.patch(f"/api/tasks/{task['id']}/complete", {"completed": True})
        self.assertEqual(status, 200)
        self.assertTrue(done["completed"])
        self.assertIsNone(done["priority"])
        self.assertTrue(done["completed_at"])
        self.assertEqual(c.get("/api/tasks")[1]["tasks"], [])
        _, reopened = c.patch(f"/api/tasks/{task['id']}/complete", {"completed": False})
        self.assertFalse(reopened["completed"])
        self.assertIsNone(reopened["completed_at"])
        self.assertIsNotNone(reopened["priority"])

    def test_complete_needs_boolean(self):
        c = self.student()
        task = self.make_task(c)
        self.assertEqual(c.patch(f"/api/tasks/{task['id']}/complete", {"completed": "yes"})[0], 422)

    def test_delete(self):
        c = self.student()
        task = self.make_task(c)
        self.assertEqual(c.delete(f"/api/tasks/{task['id']}")[0], 204)
        self.assertEqual(c.get(f"/api/tasks/{task['id']}")[0], 404)
        self.assertEqual(c.delete(f"/api/tasks/{task['id']}")[0], 404)


class Organise(ApiTestCase):
    def setUp(self):
        self.c = self.student()
        mk = lambda **kw: self.make_task(self.c, **kw)
        self.a = mk(title="Alpha essay", subject="Writing", deadline=in_hours(48 + 1), difficulty="Easy", estimated_hours=1)
        self.b = mk(title="Beta lab", subject="Physics", deadline=in_hours(9 * 24), difficulty="Very Hard", estimated_hours=10)
        self.late = mk(title="Late quiz", subject="Physics", deadline=in_hours(-5), difficulty="Easy", estimated_hours=1)
        self.done = mk(title="Done task", subject="Writing", deadline=in_hours(-50))
        self.c.patch(f"/api/tasks/{self.done['id']}/complete", {"completed": True})

    def titles(self, query):
        status, body = self.c.get("/api/tasks" + query)
        self.assertEqual(status, 200, body)
        return [t["title"] for t in body["tasks"]]

    def test_filter_subject_case_insensitive(self):
        self.assertEqual(sorted(self.titles("?subject=physics")), ["Beta lab", "Late quiz"])

    def test_filter_status(self):
        self.assertEqual(self.titles("?status=completed"), ["Done task"])
        self.assertEqual(len(self.titles("?status=all")), 4)
        self.assertNotIn("Done task", self.titles("?status=active"))

    def test_search_title(self):
        self.assertEqual(self.titles("?q=ESSAY"), ["Alpha essay"])

    def test_sort_by_deadline(self):
        self.assertEqual(self.titles("?sort=deadline"), ["Late quiz", "Alpha essay", "Beta lab"])

    def test_sort_by_priority(self):
        # Beta lab: 25*.5 + 100*.3 + 100*.2 = 62.5 -> 63; Late quiz: 50+6+2 = 58; Alpha: 37.5+6+2 = 45.5 -> 46
        self.assertEqual(self.titles("?sort=priority"), ["Beta lab", "Late quiz", "Alpha essay"])

    def test_upcoming_is_next_7_days_not_overdue(self):
        self.assertEqual(self.titles("?view=upcoming"), ["Alpha essay"])

    def test_overdue_excludes_completed(self):
        self.assertEqual(self.titles("?view=overdue"), ["Late quiz"])

    def test_subjects_and_counts_returned(self):
        body = self.c.get("/api/tasks")[1]
        self.assertEqual(body["subjects"], ["Physics", "Writing"])
        self.assertEqual(body["counts"], {"active": 3, "completed": 1, "overdue": 1})

    def test_unknown_filters_rejected(self):
        self.assertEqual(self.c.get("/api/tasks?status=weird")[0], 422)
        self.assertEqual(self.c.get("/api/tasks?sort=weird")[0], 422)
        self.assertEqual(self.c.get("/api/tasks?view=weird")[0], 422)


class Preview(ApiTestCase):
    def test_preview_uses_same_formula(self):
        c = self.student()
        status, p = c.post("/api/priority/preview", {"deadline": in_hours(30), "difficulty": "Very Hard",
                                                     "estimated_hours": 6})
        self.assertEqual(status, 200)
        self.assertEqual((p["exact"], p["score"], p["level"]), (79.5, 80, "Critical"))

    def test_preview_validates(self):
        c = self.student()
        status, body = c.post("/api/priority/preview", {"deadline": "x", "difficulty": "Easy", "estimated_hours": 0})
        self.assertEqual(status, 422)
        self.assertEqual(set(body["error"]["fields"]), {"deadline", "estimated_hours"})

    def test_preview_saves_nothing(self):
        c = self.student()
        c.post("/api/priority/preview", {"deadline": in_hours(30), "difficulty": "Easy", "estimated_hours": 1})
        self.assertEqual(c.get("/api/tasks?status=all")[1]["tasks"], [])
