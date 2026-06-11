"""Forward 2026 forecast / inference endpoint (2025 rows → 2026 ranking)."""
from __future__ import annotations

import os
import unittest

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["RESEARCH_LLM_PROVIDER"] = "none"

from app.main import app  # noqa: E402


class InferenceForecastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_options_expose_inference_metadata(self):
        o = self.client.get("/forecasting/options").json()
        self.assertEqual(o["inference_years"], [2025])
        self.assertEqual(o["default_prediction_year"], 2025)
        self.assertEqual(o["default_target_year"], 2026)
        self.assertNotIn(2025, o["trainable_years"])

    def test_inference_public_no_token(self):
        r = self.client.get("/forecasting/inference", params={"year": 2025})  # no auth header
        self.assertEqual(r.status_code, 200)
        b = r.json()
        self.assertTrue(b["available"])
        self.assertEqual(b["mode"], "inference")
        self.assertEqual(b["input_year"], 2025)
        self.assertEqual(b["target_year"], 2026)
        self.assertEqual(b["count"], 40)
        self.assertEqual(len(b["rankings"]), 40)

    def test_inference_rows_are_forward_only(self):
        b = self.client.get("/forecasting/inference", params={"year": 2025}).json()
        for row in b["rankings"]:
            self.assertEqual(row["input_year"], 2025)
            self.assertEqual(row["target_year"], 2026)
            self.assertTrue(row["is_inference"])
            self.assertFalse(row["realized_return_available"])
        ranks = [r["rank"] for r in b["rankings"]]
        self.assertEqual(ranks, sorted(ranks))

    def test_inference_not_a_backtest(self):
        b = self.client.get("/forecasting/inference", params={"year": 2025}).json()
        self.assertEqual(b["prediction_status"], "unevaluated_forward_forecast")
        self.assertIn("not a backtest", b["methodology_note"].lower())
        blob = str(b).lower()
        for bad in (" buy ", " sell ", "evaluated result", "backtested"):
            self.assertNotIn(bad, blob)

    def test_inference_unavailable_reason(self):
        b = self.client.get("/forecasting/inference", params={"year": 2099}).json()
        self.assertFalse(b["available"])
        self.assertIn("not available", b["reason"].lower())
        self.assertEqual(b["count"], 0)


if __name__ == "__main__":
    unittest.main()
