"""Supabase JWT verification: asymmetric JWKS path + HS256 legacy fallback.

Network is mocked — tests never hit Supabase.
"""
from __future__ import annotations

import os
import time
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["RESEARCH_LLM_PROVIDER"] = "none"

from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402
from cryptography.hazmat.primitives import serialization  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from jose import jwk, jwt  # noqa: E402

from app.config import settings  # noqa: E402
from app.core import security as SEC  # noqa: E402
from app.main import app  # noqa: E402

_PRIV = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PRIV_PEM = _PRIV.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()
_PUB_PEM = _PRIV.public_key().public_bytes(
    serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
).decode()
_KID = "test-signing-key-1"
_SUPA_URL = "https://example-ref.supabase.co"
_ISS = f"{_SUPA_URL}/auth/v1"


def _public_jwks() -> dict:
    pub = jwk.construct(_PUB_PEM, "RS256").to_dict()
    pub.update({"kid": _KID, "alg": "RS256", "use": "sig"})
    return {"keys": [pub]}


def _rs256_token(email: str, *, iss: str = _ISS, exp_delta: int = 3600) -> str:
    now = int(time.time())
    claims = {"sub": "uid-123", "email": email, "aud": "authenticated",
              "iss": iss, "iat": now, "exp": now + exp_delta}
    return jwt.encode(claims, _PRIV_PEM, algorithm="RS256", headers={"kid": _KID})


_DEFAULTS = dict(
    PUBLIC_DEMO_MODE=True, REQUIRE_APPROVED_USER=False, APPROVED_EMAILS="",
    SUPABASE_URL=None, SUPABASE_JWKS_URL=None, SUPABASE_JWT_SECRET=None,
)


class SupabaseJwksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        SEC._JWKS_CACHE.clear()
        self._orig_fetch = SEC._http_get_json
        SEC._http_get_json = lambda url: _public_jwks()  # mock network

    def tearDown(self):
        SEC._http_get_json = self._orig_fetch
        SEC._JWKS_CACHE.clear()
        for k, v in _DEFAULTS.items():
            setattr(settings, k, v)

    def _private(self, approved: str = ""):
        settings.PUBLIC_DEMO_MODE = False
        settings.REQUIRE_APPROVED_USER = True
        settings.APPROVED_EMAILS = approved
        settings.SUPABASE_URL = _SUPA_URL

    # ── unit: verification ──
    def test_jwks_verifies_and_returns_claims(self):
        settings.SUPABASE_URL = _SUPA_URL
        payload = SEC.decode_supabase_token(_rs256_token("user@x.com"))
        self.assertEqual(payload["email"], "user@x.com")

    def test_invalid_signature_raises(self):
        settings.SUPABASE_URL = _SUPA_URL
        tok = _rs256_token("user@x.com")
        tampered = tok[:-3] + ("aaa" if not tok.endswith("aaa") else "bbb")
        from jose import JWTError
        with self.assertRaises(JWTError):
            SEC.decode_supabase_token(tampered)

    def test_missing_verifier_fails_closed(self):
        # asymmetric token but no SUPABASE_URL / JWKS / secret configured
        settings.SUPABASE_URL = None
        settings.SUPABASE_JWKS_URL = None
        from jose import JWTError
        with self.assertRaises(JWTError):
            SEC.decode_supabase_token(_rs256_token("user@x.com"))

    def test_hs256_legacy_still_works(self):
        settings.SUPABASE_JWT_SECRET = "legacy-shared-secret"
        tok = jwt.encode(
            {"sub": "u", "email": "legacy@x.com", "aud": "authenticated",
             "exp": int(time.time()) + 3600},
            "legacy-shared-secret", algorithm="HS256",
        )
        payload = SEC.decode_supabase_token(tok)
        self.assertEqual(payload["email"], "legacy@x.com")

    # ── endpoint: private mode + JWKS ──
    def test_private_approved_jwks_user_200(self):
        self._private(approved="user@x.com")
        r = self.client.get("/research/summary",
                            headers={"Authorization": f"Bearer {_rs256_token('User@X.com')}"})
        self.assertEqual(r.status_code, 200)

    def test_private_unapproved_jwks_user_403(self):
        self._private(approved="someone@else.com")
        r = self.client.get("/research/summary",
                            headers={"Authorization": f"Bearer {_rs256_token('user@x.com')}"})
        self.assertEqual(r.status_code, 403)

    def test_private_invalid_jwks_token_401(self):
        self._private(approved="user@x.com")
        r = self.client.get("/research/summary",
                            headers={"Authorization": "Bearer not.a.jwt"})
        self.assertEqual(r.status_code, 401)

    def test_private_anonymous_401(self):
        self._private(approved="user@x.com")
        self.assertEqual(self.client.get("/research/summary").status_code, 401)


if __name__ == "__main__":
    unittest.main()
