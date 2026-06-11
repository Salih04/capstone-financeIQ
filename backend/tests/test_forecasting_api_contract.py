from __future__ import annotations

import io
import os
import unittest

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app.main import app  # noqa: E402


def _register_and_login(client: TestClient) -> str:
    email = "contract@test.com"
    password = "Passw0rd!"
    client.post("/auth/register", json={"email": email, "password": password, "role": "analyst"})
    r = client.post("/auth/login", json={"email": email, "password": password})
    data = r.json()
    return data["access_token"]


class ForecastingApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        token = _register_and_login(cls.client)
        cls.headers = {"Authorization": f"Bearer {token}"}

    def test_catalog_contract(self):
        r = self.client.get("/parameters/catalog", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("items", body)
        self.assertTrue(isinstance(body["items"], list))
        self.assertGreater(len(body["items"]), 0)
        self.assertIn("ratio", body["items"][0])

    def test_fundamentals_upload_validation_contract(self):
        bad_csv = b"stock_code,sector,period\nASELS,Savunma,2023Q1\n"
        files = {"file": ("bad.csv", io.BytesIO(bad_csv), "text/csv")}
        r = self.client.post("/fundamentals/upload-csv", headers=self.headers, files=files)
        self.assertEqual(r.status_code, 422)
        detail = r.json().get("detail")
        self.assertTrue("Missing required columns" in str(detail))

    def test_predict_history_contract(self):
        r = self.client.get("/predict/history", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("items", body)
        self.assertTrue(isinstance(body["items"], list))

    def test_filters_populate_after_fundamentals_upload(self):
        # Uploading quarterly fundamentals (with a sector) must make Year/Sector
        # dropdowns populate via /forecasting/filters (union of cohort + fundamentals).
        cols = ("ticker,sector,period,revenue,net_income,total_assets,total_equity,"
                "total_liabilities,current_assets,current_liabilities,cash,"
                "operating_cash_flow,operating_income,gross_profit,inventory")
        row = "ASELS,Savunma,2025Q4,100,10,500,200,300,150,80,30,40,25,15,20"
        csv = (cols + "\n" + row + "\n").encode()
        up = self.client.post("/fundamentals/upload-csv", headers=self.headers,
                              files={"file": ("quarterly_fundamentals_2025.csv", io.BytesIO(csv), "text/csv")})
        self.assertNotEqual(up.status_code, 500)
        self.assertEqual(up.status_code, 200)
        r = self.client.get("/forecasting/filters", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn(2025, body["years"])
        self.assertIn("Savunma", body["sectors"])


if __name__ == "__main__":
    unittest.main()
