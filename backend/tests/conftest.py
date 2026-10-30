from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

_TEST_DB_DIR = TemporaryDirectory(prefix="financeiq-backend-tests-")
DB_PATH = Path(_TEST_DB_DIR.name) / "tests.sqlite"

os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("RESEARCH_LLM_PROVIDER", "none")
