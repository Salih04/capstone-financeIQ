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


if __name__ == "__main__":
    unittest.main()
