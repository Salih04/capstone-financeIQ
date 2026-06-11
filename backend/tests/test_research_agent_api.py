from __future__ import annotations

import os
import unittest

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["RESEARCH_LLM_PROVIDER"] = "none"  # deterministic fallback only

from app.main import app  # noqa: E402

FORBIDDEN = (" buy ", " sell ", " hold ", "price target", " al ", " sat ", " tut ")


def _login(client: TestClient) -> dict:
    client.post("/auth/register", json={"email": "ra@test.com", "password": "Passw0rd!", "role": "analyst"})
    tok = client.post("/auth/login", json={"email": "ra@test.com", "password": "Passw0rd!"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


class ResearchAgentApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.h = _login(cls.client)

    def test_summary(self):
        r = self.client.get("/research/summary", headers=self.h)
        self.assertEqual(r.status_code, 200)
        self.assertIn("context", r.json())

    def test_data_quality(self):
        r = self.client.get("/research/data-quality", headers=self.h)
        self.assertEqual(r.status_code, 200)
        self.assertIn("data_quality", r.json())

    def test_ai_status_not_configured_is_structured(self):
        r = self.client.get("/research/ai-status", headers=self.h)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body["available"])
        self.assertFalse(body["configured"])
        self.assertEqual(body["provider"], "none")
        self.assertIn("AI not configured", body["reason"])
        self.assertTrue(body["fallback_available"])

    def test_model_diagnostics(self):
        r = self.client.get("/research/model-diagnostics", headers=self.h)
        self.assertEqual(r.status_code, 200)
        self.assertIn("diagnostics", r.json())

    def test_company(self):
        r = self.client.get("/research/company/ASELS", headers=self.h)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["context"]["ticker"], "ASELS")

    def test_company_score_components(self):
        r = self.client.get("/research/company/ASELS/score", headers=self.h)
        self.assertEqual(r.status_code, 200)
        s = r.json()["score"]
        for k in ("ml_score", "confidence_score", "llm_research_score",
                  "final_research_score", "score_source", "not_investment_advice"):
            self.assertIn(k, s)
        self.assertTrue(s["not_investment_advice"])

    def test_ask_fallback(self):
        r = self.client.post("/research/ask", headers=self.h,
                             json={"question": "Is the benchmark available?"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["fallback_used"])
        self.assertEqual(body["provider_used"], "none")

    def test_unknown_ticker(self):
        r = self.client.get("/research/company/ZZZZ/score", headers=self.h)
        self.assertEqual(r.status_code, 404)

    def test_no_advice_language(self):
        r = self.client.get("/research/company/ASELS/score", headers=self.h)
        blob = f" {r.text.lower()} "
        for bad in FORBIDDEN:
            self.assertNotIn(bad, blob)

    # ── public-demo access: research endpoints must work WITHOUT a token ──
    def test_summary_public_no_token(self):
        r = self.client.get("/research/summary")  # no Authorization header
        self.assertEqual(r.status_code, 200)
        self.assertIn("context", r.json())

    def test_ask_public_no_token(self):
        r = self.client.post("/research/ask", json={"question": "Top ranked companies"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("answer", r.json())

    def test_company_public_no_token(self):
        r = self.client.get("/research/company/THYAO")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["context"]["ticker"], "THYAO")

    def test_invalid_token_still_public(self):
        bad = {"Authorization": "Bearer not.a.real.token"}
        r = self.client.get("/research/summary", headers=bad)
        self.assertEqual(r.status_code, 200)

    def test_runtime_status_shape(self):
        r = self.client.get("/research/runtime-status")
        self.assertEqual(r.status_code, 200)
        b = r.json()
        for k in ("repo_root", "public_dataset_exists", "public_rows",
                  "training_rows", "company_contexts_count", "missing_required_files",
                  "ai_provider_configured", "llm_fallback_available"):
            self.assertIn(k, b)
        self.assertTrue(b["llm_fallback_available"])

    def test_ai_status_masks_secrets(self):
        # configure a provider+key, confirm the key value is never echoed back
        os.environ["RESEARCH_LLM_PROVIDER"] = "openrouter"
        os.environ["OPENROUTER_API_KEY"] = "sk-should-not-leak-xyz"
        try:
            r = self.client.get("/research/ai-status")
            self.assertEqual(r.status_code, 200)
            self.assertNotIn("sk-should-not-leak-xyz", r.text)
        finally:
            os.environ["RESEARCH_LLM_PROVIDER"] = "none"
            os.environ.pop("OPENROUTER_API_KEY", None)


if __name__ == "__main__":
    unittest.main()
