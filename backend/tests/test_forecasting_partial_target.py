"""Experimental 2025 partial 2026-YTD target mode.

Verifies: default finalized_only excludes 2025; include_partial_2025 reports
metadata; missing 2026 YTD data returns a clear unavailable reason; partial mode
never silently treats 2025 as a finalized annual training year.
"""
from __future__ import annotations

import os
import unittest

import pandas as pd
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["RESEARCH_LLM_PROVIDER"] = "none"

from app.main import app  # noqa: E402
from app.services import forecasting_csv_service as svc  # noqa: E402


class PartialTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.partial_path = svc.PARTIAL_2026_YTD_CSV
        # Ensure clean baseline: no real partial file present.
        if cls.partial_path.exists():
            cls.partial_path.rename(cls.partial_path.with_suffix(".bak"))

    @classmethod
    def tearDownClass(cls):
        bak = cls.partial_path.with_suffix(".bak")
        if bak.exists():
            bak.rename(cls.partial_path)

    def tearDown(self):
        # Remove any fixture a test wrote.
        if self.partial_path.exists():
            self.partial_path.unlink()

    # ── defaults ──
    def test_default_options_exclude_2025(self):
        o = self.client.get("/forecasting/options").json()
        self.assertEqual(o["target_mode"], "finalized_only")
        self.assertNotIn(2025, o["trainable_years"])
        self.assertNotIn(2025, o["training_years"])
        self.assertFalse(o["includes_partial_targets"])

    def test_default_train_caps_at_2024(self):
        t = self.client.post("/forecasting/train",
                             json={"train_year_to": 2025, "target_mode": "finalized_only"}).json()
        self.assertEqual(t["train_year_to"], 2024)
        self.assertFalse(t["includes_partial_targets"])
        self.assertNotIn(2025, t["training_years"])

    # ── partial requested but unavailable ──
    def test_partial_unavailable_reason(self):
        o = self.client.get("/forecasting/options",
                            params={"target_mode": "include_partial_2025"}).json()
        self.assertEqual(o["target_mode"], "include_partial_2025")
        self.assertFalse(o["includes_partial_targets"])
        self.assertNotIn(2025, o["training_years"])
        excl = {e["year"]: e["reason"] for e in o["excluded_years"]}
        self.assertIn(2025, excl)
        self.assertIn("not available", excl[2025].lower())
        self.assertIn("data_requirement", o["partial_target_status"])

    def test_partial_unavailable_train_clamps(self):
        t = self.client.post("/forecasting/train",
                             json={"target_mode": "include_partial_2025", "train_year_to": 2025}).json()
        self.assertFalse(t["includes_partial_targets"])
        self.assertEqual(t["train_year_to"], 2024)
        self.assertNotIn(2025, t["training_years"])

    # ── partial available (real fixture, not fabricated by the app) ──
    def _write_fixture(self):
        df = svc._load_training_df()
        tickers = sorted(df[df["year"] == 2025]["ticker"].unique().tolist())[:20]
        rows = [{"ticker": t, "year": 2025, "target_year": 2026,
                 "partial_ytd_return_pct": (i - 10) * 3.5,  # real spread of values
                 "as_of_date": "2026-03-31", "source": "test_fixture"}
                for i, t in enumerate(tickers)]
        pd.DataFrame(rows).to_csv(self.partial_path, index=False)

    def test_partial_available_includes_2025(self):
        self._write_fixture()
        o = self.client.get("/forecasting/options",
                            params={"target_mode": "include_partial_2025"}).json()
        self.assertTrue(o["includes_partial_targets"])
        self.assertIn(2025, o["training_years"])
        self.assertIsNotNone(o["partial_target_warning"])
        # 2025 still must NOT appear as a finalized trainable year.
        self.assertNotIn(2025, o["trainable_years"])
        pm = o["target_metadata"]["partial_ytd_target"]
        self.assertEqual(pm["target_year"], 2026)
        self.assertEqual(pm["target_status"], "partial_ytd")
        self.assertFalse(pm["comparable_to_full_year"])

    def test_partial_available_train_uses_2025(self):
        self._write_fixture()
        t = self.client.post("/forecasting/train",
                             json={"target_mode": "include_partial_2025", "train_year_to": 2025}).json()
        self.assertTrue(t["includes_partial_targets"])
        self.assertEqual(t["train_year_to"], 2025)
        self.assertIn(2025, t["training_years"])
        self.assertIsNotNone(t["partial_target_warning"])
        self.assertTrue(len(t["top_parameters"]) > 0)


if __name__ == "__main__":
    unittest.main()
