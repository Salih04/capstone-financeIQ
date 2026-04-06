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


if __name__ == "__main__":
    unittest.main()
