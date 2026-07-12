from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.config import Settings


def test_settings_ignore_unknown_dotenv_keys_without_changing_known_values():
    with TemporaryDirectory() as directory:
        env_file = Path(directory) / ".env"
        env_file.write_text(
            "DATABASE_URL=sqlite:///settings-test.sqlite\n"
            "RESEARCH_LLM_TIMEOUT_SECONDS=9.5\n"
            "OPENROUTER_API_KEY=x\n"
            "OPENROUTER_HTTP_REFERER=https://example.test\n"
            "OPENROUTER_APP_TITLE=FinanceIQ Test\n"
        )

        with patch.dict("os.environ", {}, clear=True):
            settings = Settings(_env_file=env_file)

    assert settings.DATABASE_URL == "sqlite:///settings-test.sqlite"
    assert settings.research_llm_timeout_seconds == 9.5
