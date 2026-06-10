from __future__ import annotations

import os
from pathlib import Path

DB_PATH = Path("/tmp/financeiq_backend_tests.sqlite")
if DB_PATH.exists():
    DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("RESEARCH_LLM_PROVIDER", "none")
