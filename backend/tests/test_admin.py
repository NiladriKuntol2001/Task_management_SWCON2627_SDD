"""US7 — admin panel (FR-26..FR-32)."""
from backend.tests.support import ApiTestCase, in_hours

ADMIN_ENDPOINTS = [("GET", "/api/admin/overview"), ("GET", "/api/admin/users"), ("GET", "/api/admin/tasks"),
                   ("POST", "/api/admin/users"), ("PATCH", "/api/admin/users/2")]


class Access(ApiTestCase):
    def test_main_admin_bootstrapped_as_user_1(self):
        admin = self.admin()
        self.assertEqual((admin.user["id"], admin.user["role"], admin.user["email"]), (1, "admin", "admin123@gmail.com"))
        self.assertTrue(admin.user["is_main_admin"])

    def test_students_get_403_everywhere(self):
        s = self.student()
        for method, path in ADMIN_ENDPOINTS:
            status, body = s.request(method, path, {} if method != "GET" else None)
            self.assertEqual(status, 403, path)
            self.assertEqual(body["error"]["message"], "Admins only.")


class Users(ApiTestCase):
    def test_list_and_search(self):
        admin = self.admin()
        s = self.student("Searchable Person")
        self.make_task(s)
        users = admin.get("/api/admin/users")[1]["users"]
        self.assertEqual(users[0]["id"], 1)
        mine = [u for u in users if u["id"] == s.user["id"]][0]
        self.assertEqual((mine["open"], mine["completed"], mine["overdue"]), (1, 0, 0))
        for q in ("searchable", s.email.upper(), str(s.user["id"]), f"#{s.user['id']}"):
            found = admin.get(f"/api/admin/users?q={q.replace('#', '%23')}")[1]["users"]
            self.assertEqual([u["id"] for u in found], [s.user["id"]], q)

    def test_create_user(self):
        admin = self.admin()
        status, u = admin.post("/api/admin/users", {"name": "New Admin", "email": "na@b.fi",
                                                   "password": "Password1", "role": "admin"})
        self.assertEqual(status, 201)
        self.assertEqual(u["role"], "admin")
        self.assertEqual(admin.post("/api/admin/users", {"name": "Dup", "email": "NA@b.fi", "password": "Password1"})[0], 409)
        status, body = admin.post("/api/admin/users", {"name": "", "email": "x", "password": "1", "role": "boss"})
        self.assertEqual(status, 422)
        self.assertEqual(set(body["error"]["fields"]), {"name", "email", "password", "role"})

    def test_deactivate_blocks_login_and_live_sessions_but_keeps_data(self):
        admin = self.admin()
        s = self.student()
        self.make_task(s, title="Kept")
        status, u = admin.patch(f"/api/admin/users/{s.user['id']}", {"is_active": False})
        self.assertEqual(status, 200)
        self.assertFalse(u["is_active"])
        self.assertEqual(u["open"], 1)
        self.assertEqual(s.get("/api/tasks")[0], 401)
        status, body = self.client().post("/api/auth/login", {"email": s.email, "password": "Password1"})
        self.assertEqual(status, 403)
        self.assertIn("deactivated", body["error"]["message"])
        admin.patch(f"/api/admin/users/{s.user['id']}", {"is_active": True})
        status, body = self.client().post("/api/auth/login", {"email": s.email, "password": "Password1"})
        self.assertEqual(status, 200)
        self.assertEqual([t["title"] for t in self.client(body["token"]).get("/api/tasks")[1]["tasks"]], ["Kept"])

    def test_main_admin_and_self_are_protected(self):
        admin = self.admin()
        self.assertEqual(admin.patch("/api/admin/users/1", {"is_active": False})[0], 403)
        self.assertEqual(admin.patch("/api/admin/users/1", {"role": "student"})[0], 403)
        _, second = admin.post("/api/admin/users", {"name": "Second", "email": "second@b.fi",
                                                   "password": "Password1", "role": "admin"})
        _, body = self.client().post("/api/auth/login", {"email": "second@b.fi", "password": "Password1"})
        second_admin = self.client(body["token"])
        self.assertEqual(second_admin.patch(f"/api/admin/users/{second['id']}", {"is_active": False})[0], 403)
        self.assertEqual(second_admin.patch("/api/admin/users/1", {"is_active": False})[0], 403)

    def test_change_role(self):
        admin = self.admin()
        s = self.student()
        status, u = admin.patch(f"/api/admin/users/{s.user['id']}", {"role": "admin"})
        self.assertEqual((status, u["role"]), (200, "admin"))
        self.assertEqual(s.get("/api/admin/overview")[0], 200)
        self.assertEqual(admin.patch("/api/admin/users/999999", {"is_active": False})[0], 404)
        self.assertEqual(admin.patch(f"/api/admin/users/{s.user['id']}", {"role": "boss"})[0], 422)


class Tasks(ApiTestCase):
    def test_all_tasks_filters_and_order(self):
        admin = self.admin()
        a, b = self.student("A"), self.student("B")
        self.make_task(a, title="A crit", deadline=in_hours(14.5), difficulty="Hard", estimated_hours=8)    # 90
        self.make_task(b, title="B low", deadline=in_hours(500), difficulty="Easy", estimated_hours=1)     # 13
        done = self.make_task(b, title="B done")
        b.patch(f"/api/tasks/{done['id']}/complete", {"completed": True})
        body = admin.get("/api/admin/tasks")[1]
        self.assertEqual([t["title"] for t in body["tasks"]], ["A crit", "B low"])
        self.assertEqual(body["tasks"][0]["owner_name"], "A")
        self.assertEqual([t["title"] for t in admin.get("/api/admin/tasks?level=Low")[1]["tasks"]], ["B low"])
        body = admin.get(f"/api/admin/tasks?owner_id={b.user['id']}")[1]
        self.assertEqual(([t["title"] for t in body["tasks"]], body["owner_name"]), (["B low"], "B"))
        self.assertEqual(admin.get("/api/admin/tasks?level=Huge")[0], 422)


class Overview(ApiTestCase):
    """Own class = own empty database, so the totals are exact."""

    def test_overview_numbers(self):
        admin = self.admin()
        s = self.student("Late Student")
        self.make_task(s, title="Late", deadline=in_hours(-60), difficulty="Hard", estimated_hours=4)      # 82 overdue
        self.make_task(s, title="Fine", deadline=in_hours(500), difficulty="Easy", estimated_hours=1)
        done = self.make_task(s, title="Done")
        s.patch(f"/api/tasks/{done['id']}/complete", {"completed": True})
        o = admin.get("/api/admin/overview")[1]
        self.assertEqual(o["tasks"], {"total": 3, "open": 2, "completed": 1})
        self.assertEqual(o["completion_rate"], 33)
        self.assertEqual(o["critical_open"], 1)
        self.assertEqual(o["overdue"], {"tasks": 1, "students": 1})
        self.assertEqual(len(o["trend"]), 14)
        self.assertEqual(o["trend"][-1]["created"], 3)
        self.assertEqual(o["trend"][-1]["completed"], 1)
        self.assertEqual(o["by_level"], {"Critical": 1, "High": 0, "Medium": 0, "Low": 1})
        self.assertEqual(o["attention"][0]["name"], "Late Student")
        self.assertEqual(o["attention"][0]["task"]["score"], 82)
