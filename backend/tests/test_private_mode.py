"""Private/demo access-control mode, allowlist, rate limiting, docs gating."""
from __future__ import annotations

import os
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["RESEARCH_LLM_PROVIDER"] = "none"

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402

_DEFAULTS = dict(
    PUBLIC_DEMO_MODE=True, REQUIRE_APPROVED_USER=False, APPROVED_EMAILS="",
    RATE_LIMIT_ENABLED=False, RATE_LIMIT_REQUESTS_PER_MINUTE=60,
)


def _reset():
    for k, v in _DEFAULTS.items():
        setattr(settings, k, v)


class PrivateModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # a real, signed legacy token (works without SUPABASE_JWT_SECRET)
        cls.client.post("/auth/register", json={"email": "Owner@Test.com", "password": "Passw0rd!", "role": "admin"})
        cls.token = cls.client.post("/auth/login", json={"email": "Owner@Test.com", "password": "Passw0rd!"}).json()["access_token"]
        cls.auth = {"Authorization": f"Bearer {cls.token}"}

    def tearDown(self):
        _reset()

    # ── demo mode (default) ──
    def test_demo_allows_anonymous(self):
        settings.PUBLIC_DEMO_MODE = True
        r = self.client.get("/research/summary")  # no token
        self.assertEqual(r.status_code, 200)

    # ── private mode ──
    def test_private_denies_anonymous_401(self):
        settings.PUBLIC_DEMO_MODE = False
        r = self.client.get("/research/summary")
        self.assertEqual(r.status_code, 401)

    def test_private_invalid_token_401(self):
        settings.PUBLIC_DEMO_MODE = False
        r = self.client.get("/research/summary", headers={"Authorization": "Bearer not.a.token"})
        self.assertEqual(r.status_code, 401)

    def test_private_valid_token_no_approval_required_ok(self):
        settings.PUBLIC_DEMO_MODE = False
        settings.REQUIRE_APPROVED_USER = False
        r = self.client.get("/research/summary", headers=self.auth)
        self.assertEqual(r.status_code, 200)

    def test_private_empty_allowlist_fails_closed_403(self):
        settings.PUBLIC_DEMO_MODE = False
        settings.REQUIRE_APPROVED_USER = True
        settings.APPROVED_EMAILS = ""
        r = self.client.get("/research/summary", headers=self.auth)
        self.assertEqual(r.status_code, 403)

    def test_private_approved_email_ok_case_insensitive(self):
        settings.PUBLIC_DEMO_MODE = False
        settings.REQUIRE_APPROVED_USER = True
        settings.APPROVED_EMAILS = "owner@test.com"  # token email is Owner@Test.com
        r = self.client.get("/research/summary", headers=self.auth)
        self.assertEqual(r.status_code, 200)

    def test_private_unapproved_email_403(self):
        settings.PUBLIC_DEMO_MODE = False
        settings.REQUIRE_APPROVED_USER = True
        settings.APPROVED_EMAILS = "someone-else@example.com"
        r = self.client.get("/research/summary", headers=self.auth)
        self.assertEqual(r.status_code, 403)
        # must not leak the allowlist or claims
        self.assertNotIn("someone-else@example.com", r.text)
        self.assertNotIn("owner@test.com", r.text.lower())

    def test_health_public_in_private_mode(self):
        settings.PUBLIC_DEMO_MODE = False
        settings.REQUIRE_APPROVED_USER = True
        self.assertEqual(self.client.get("/health").status_code, 200)

    # ── rate limiting ──
    def test_rate_limit_429(self):
        settings.RATE_LIMIT_ENABLED = True
        settings.RATE_LIMIT_REQUESTS_PER_MINUTE = 2
        codes = [self.client.post("/research/ask", json={"question": "top ranked"}).status_code for _ in range(3)]
        self.assertEqual(codes[0], 200)
        self.assertEqual(codes[1], 200)
        self.assertEqual(codes[2], 429)

    # ── docs gating mechanism ──
    def test_docs_disabled_returns_404(self):
        a = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
        c = TestClient(a)
        self.assertEqual(c.get("/openapi.json").status_code, 404)
        self.assertEqual(c.get("/docs").status_code, 404)


if __name__ == "__main__":
    unittest.main()
