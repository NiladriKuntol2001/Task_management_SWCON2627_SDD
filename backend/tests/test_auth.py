"""US1 — account (FR-01..FR-03, NFR-03, NFR-04, NFR-10)."""
import sqlite3

from backend.tests.support import ApiTestCase, Client


class Register(ApiTestCase):
    def test_register_creates_account_and_signs_in(self):
        status, body = self.client().post("/api/auth/register",
                                          {"name": "Aino", "email": "aino@b.fi", "password": "secret123"})
        self.assertEqual(status, 201)
        self.assertTrue(body["token"])
        self.assertEqual(body["user"]["email"], "aino@b.fi")
        self.assertEqual(body["user"]["role"], "student")
        self.assertNotIn("password_hash", body["user"])

    def test_duplicate_email_ignores_case_and_spaces(self):
        self.client().post("/api/auth/register", {"name": "A", "email": "dup@b.fi", "password": "secret123"})
        status, body = self.client().post("/api/auth/register",
                                          {"name": "B", "email": "  DUP@B.fi ", "password": "secret123"})
        self.assertEqual(status, 409)
        self.assertEqual(body["error"]["fields"]["email"], "An account with this email already exists.")

    def test_validation_messages(self):
        status, body = self.client().post("/api/auth/register", {"name": " ", "email": "nope", "password": "short"})
        self.assertEqual(status, 422)
        fields = body["error"]["fields"]
        self.assertEqual(fields["name"], "Name can't be empty.")
        self.assertEqual(fields["email"], "Enter a valid email address.")
        self.assertEqual(fields["password"], "Password must be at least 8 characters.")

    def test_password_is_stored_hashed(self):
        self.client().post("/api/auth/register", {"name": "H", "email": "hash@b.fi", "password": "PlainText99"})
        conn = sqlite3.connect(self.live.settings.db_path)
        stored = conn.execute("SELECT password_hash FROM users WHERE email='hash@b.fi'").fetchone()[0]
        conn.close()
        self.assertNotIn("PlainText99", stored)
        self.assertTrue(stored.startswith("scrypt$"))

    def test_bad_json_is_rejected_cleanly(self):
        status, body = self.client().request("POST", "/api/auth/register", raw=b"{not json")
        self.assertEqual(status, 400)
        self.assertIn("JSON", body["error"]["message"])


class Login(ApiTestCase):
    def setUp(self):
        self.client().post("/api/auth/register", {"name": "L", "email": "login@b.fi", "password": "secret123"})

    def test_login_ok(self):
        status, body = self.client().post("/api/auth/login", {"email": "LOGIN@b.fi", "password": "secret123"})
        self.assertEqual(status, 200)
        self.assertTrue(body["token"])

    def test_wrong_password_and_unknown_email_get_same_message(self):
        s1, b1 = self.client().post("/api/auth/login", {"email": "login@b.fi", "password": "wrong-pass"})
        s2, b2 = self.client().post("/api/auth/login", {"email": "ghost@b.fi", "password": "secret123"})
        self.assertEqual((s1, s2), (401, 401))
        self.assertEqual(b1["error"]["message"], "Email or password is incorrect.")
        self.assertEqual(b1["error"]["message"], b2["error"]["message"])


class Sessions(ApiTestCase):
    def test_protected_endpoints_need_a_token(self):
        for path in ("/api/tasks", "/api/dashboard", "/api/me", "/api/admin/overview"):
            status, _ = self.client().get(path)
            self.assertEqual(status, 401, path)
        status, _ = Client(self.live.base, "garbage.token.value").get("/api/tasks")
        self.assertEqual(status, 401)

    def test_logout_revokes_token(self):
        c = self.student()
        self.assertEqual(c.get("/api/me")[0], 200)
        self.assertEqual(c.post("/api/auth/logout")[0], 204)
        status, body = c.get("/api/me")
        self.assertEqual(status, 401)
        self.assertIn("signed out", body["error"]["message"])

    def test_tasks_persist_across_sign_out_and_in(self):
        c = self.student()
        self.make_task(c, title="Persistent")
        c.post("/api/auth/logout")
        _, body = self.client().post("/api/auth/login", {"email": c.email, "password": "Password1"})
        again = self.client(body["token"])
        titles = [t["title"] for t in again.get("/api/tasks")[1]["tasks"]]
        self.assertIn("Persistent", titles)
