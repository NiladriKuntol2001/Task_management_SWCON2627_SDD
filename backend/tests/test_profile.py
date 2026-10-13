"""US6 — profile (FR-22..FR-25)."""
from backend.tests.support import ApiTestCase


class Profile(ApiTestCase):
    def test_view_profile(self):
        c = self.student("Niladri")
        self.make_task(c)
        done = self.make_task(c)
        c.patch(f"/api/tasks/{done['id']}/complete", {"completed": True})
        status, me = c.get("/api/me")
        self.assertEqual(status, 200)
        self.assertEqual(me["name"], "Niladri")
        self.assertIsInstance(me["id"], int)
        self.assertEqual((me["role"], me["task_count"], me["completed_count"]), ("student", 2, 1))
        self.assertTrue(me["created_at"])
        self.assertNotIn("password_hash", me)

    def test_user_ids_are_unique_increasing_numbers(self):
        a, b = self.student(), self.student()
        self.assertGreater(b.user["id"], a.user["id"])
        self.assertGreater(a.user["id"], 1)


class ChangeEmail(ApiTestCase):
    def test_change_email_ok(self):
        c = self.student()
        status, me = c.patch("/api/me/email", {"new_email": "New.Address@b.fi", "current_password": "Password1"})
        self.assertEqual(status, 200)
        self.assertEqual(me["email"], "new.address@b.fi")
        self.assertEqual(self.client().post("/api/auth/login", {"email": "new.address@b.fi", "password": "Password1"})[0], 200)

    def test_rules(self):
        c = self.student()
        other = self.student()
        cases = [({"new_email": "bad", "current_password": "Password1"}, 422, "new_email", "Enter a valid email address."),
                 ({"new_email": c.email, "current_password": "Password1"}, 422, "new_email", "This is already your email."),
                 ({"new_email": other.email, "current_password": "Password1"}, 409, "new_email", "Another account already uses this email."),
                 ({"new_email": "fresh@b.fi", "current_password": "wrong"}, 422, "current_password", "Current password is incorrect.")]
        for body, status, field, message in cases:
            got_status, resp = c.patch("/api/me/email", body)
            self.assertEqual(got_status, status, body)
            self.assertEqual(resp["error"]["fields"][field], message)

    def test_main_admin_email_is_fixed(self):
        status, _ = self.admin().patch("/api/me/email", {"new_email": "x@b.fi", "current_password": "admin@123"})
        self.assertEqual(status, 403)


class ChangePassword(ApiTestCase):
    def body(self, **kw):
        b = {"current_password": "Password1", "new_password": "BrandNew99", "confirm_password": "BrandNew99"}
        b.update(kw)
        return b

    def test_change_password_and_old_one_stops_working(self):
        c = self.student()
        self.assertEqual(c.patch("/api/me/password", self.body())[0], 204)
        login = lambda pw: self.client().post("/api/auth/login", {"email": c.email, "password": pw})[0]
        self.assertEqual(login("Password1"), 401)
        self.assertEqual(login("BrandNew99"), 200)

    def test_rules(self):
        c = self.student()
        cases = [(self.body(current_password="nope"), "current_password", "Current password is incorrect."),
                 (self.body(new_password="short", confirm_password="short"), "new_password", "Password must be at least 8 characters."),
                 (self.body(new_password="Password1", confirm_password="Password1"), "new_password",
                  "New password must be different from your current password."),
                 (self.body(confirm_password="Different99"), "confirm_password", "The two new passwords don't match.")]
        for body, field, message in cases:
            status, resp = c.patch("/api/me/password", body)
            self.assertEqual(status, 422, body)
            self.assertEqual(resp["error"]["fields"][field], message)
        self.assertEqual(self.client().post("/api/auth/login", {"email": c.email, "password": "Password1"})[0], 200)
