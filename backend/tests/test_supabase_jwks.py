"""Supabase JWT verification: asymmetric JWKS path + HS256 legacy fallback.

Network is mocked — tests never hit Supabase.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["RESEARCH_LLM_PROVIDER"] = "none"

from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402
from cryptography.hazmat.primitives import serialization  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
import jwt  # noqa: E402
from jwt.algorithms import RSAAlgorithm  # noqa: E402

from app.config import settings  # noqa: E402
from app.core import security as SEC  # noqa: E402
from app.main import app  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402

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
    pub = json.loads(RSAAlgorithm.to_jwk(_PRIV.public_key()))
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
    SUPABASE_EMAIL_CONFIRMATION_ENFORCED=False,
    SUPABASE_IDENTITY_BINDINGS={},
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
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == "User@X.com").first()
            if user is None:
                user = User(email="User@X.com", password_hash=SEC.hash_password("Synthetic1!"),
                            role="investor", is_active=True)
                db.add(user)
                db.commit()
            settings.SUPABASE_IDENTITY_BINDINGS = {"uid-123": user.id}

    # ── unit: verification ──
    def test_jwks_verifies_and_returns_claims(self):
        settings.SUPABASE_URL = _SUPA_URL
        payload = SEC.decode_supabase_token(_rs256_token("user@x.com"))
        self.assertEqual(payload["email"], "user@x.com")

    def test_invalid_signature_raises(self):
        settings.SUPABASE_URL = _SUPA_URL
        tok = _rs256_token("user@x.com")
        tampered = tok[:-3] + ("aaa" if not tok.endswith("aaa") else "bbb")
        with self.assertRaises(jwt.PyJWTError):
            SEC.decode_supabase_token(tampered)

    def test_missing_verifier_fails_closed(self):
        # asymmetric token but no SUPABASE_URL / JWKS / secret configured
        settings.SUPABASE_URL = None
        settings.SUPABASE_JWKS_URL = None
        with self.assertRaises(jwt.PyJWTError):
            SEC.decode_supabase_token(_rs256_token("user@x.com"))

    def test_hs256_signed_with_public_key_is_rejected(self):
        """Algorithm confusion (cf. PYSEC-2026-4298): an HS256 token keyed with the
        published JWKS public key must never verify, configured secret or not."""
        settings.SUPABASE_URL = _SUPA_URL

        def b64(data: bytes) -> bytes:
            return base64.urlsafe_b64encode(data).rstrip(b"=")

        signing_input = b".".join([
            b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()),
            b64(json.dumps({"sub": "u", "email": "attacker@x.com", "aud": "authenticated",
                            "exp": int(time.time()) + 3600}).encode()),
        ])
        sig = b64(hmac.new(_PUB_PEM.encode(), signing_input, hashlib.sha256).digest())
        forged = (signing_input + b"." + sig).decode()
        for secret in (None, "legacy-shared-secret"):
            settings.SUPABASE_JWT_SECRET = secret
            with self.assertRaises(jwt.PyJWTError):
                SEC.decode_supabase_token(forged)

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
        settings.SUPABASE_EMAIL_CONFIRMATION_ENFORCED = True  # deployment attests confirmed emails
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
