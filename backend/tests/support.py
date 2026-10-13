"""Test helpers: a real StudyFlow server on a free port with its own temporary
database, and a tiny JSON client. Standard library only (runs without pytest)."""
import json
import os
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import timedelta

import uvicorn

from backend.app.config import get_settings
from backend.app.db import init_db, to_iso, utcnow
from backend.app.main import create_app


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class LiveServer:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["STUDYFLOW_SECRET"] = "test-secret-key-for-unit-tests-only"
        self.settings = get_settings(os.path.join(self.tmp.name, "test.db"))
        init_db(self.settings.db_path, self.settings.main_admin_email, self.settings.main_admin_password)
        self.port = _free_port()
        config = uvicorn.Config(create_app(self.settings), host="127.0.0.1", port=self.port, log_level="error")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    def start(self):
        self.thread.start()
        deadline = time.time() + 10
        while not self.server.started:
            if time.time() > deadline:
                raise RuntimeError("test server did not start")
            time.sleep(0.02)
        return self

    def stop(self):
        self.server.should_exit = True
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.port}"


class Client:
    def __init__(self, base: str, token: str | None = None):
        self.base = base
        self.token = token

    def request(self, method: str, path: str, body=None, raw: bytes | None = None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                text = resp.read().decode()
                return resp.status, (json.loads(text) if text else None)
        except urllib.error.HTTPError as err:
            text = err.read().decode()
            return err.code, (json.loads(text) if text else None)

    def get(self, path): return self.request("GET", path)
    def post(self, path, body=None): return self.request("POST", path, body if body is not None else {})
    def put(self, path, body): return self.request("PUT", path, body)
    def patch(self, path, body): return self.request("PATCH", path, body)
    def delete(self, path): return self.request("DELETE", path)


def in_hours(h: float) -> str:
    return to_iso(utcnow() + timedelta(hours=h))


class ApiTestCase(unittest.TestCase):
    """Starts one server per test class."""

    @classmethod
    def setUpClass(cls):
        cls.live = LiveServer().start()

    @classmethod
    def tearDownClass(cls):
        cls.live.stop()

    _counter = 0

    def client(self, token=None) -> Client:
        return Client(self.live.base, token)

    def student(self, name="Student") -> Client:
        """Register a fresh student and return a signed-in client."""
        ApiTestCase._counter += 1
        email = f"user{ApiTestCase._counter}_{id(self)}@test.fi"
        status, body = self.client().post("/api/auth/register",
                                          {"name": name, "email": email, "password": "Password1"})
        self.assertEqual(status, 201, body)
        c = self.client(body["token"])
        c.user = body["user"]
        c.email = email
        return c

    def admin(self) -> Client:
        status, body = self.client().post("/api/auth/login",
                                          {"email": "admin123@gmail.com", "password": "admin@123"})
        self.assertEqual(status, 200, body)
        c = self.client(body["token"])
        c.user = body["user"]
        return c

    def make_task(self, c: Client, **overrides) -> dict:
        body = {"title": "Essay", "subject": "Software Design", "deadline": in_hours(100),
                "difficulty": "Medium", "estimated_hours": 3}
        body.update(overrides)
        status, task = c.post("/api/tasks", body)
        self.assertEqual(status, 201, task)
        return task
