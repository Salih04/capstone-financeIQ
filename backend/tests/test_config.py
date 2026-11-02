from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from pydantic import ValidationError

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


@pytest.mark.parametrize("bindings", [{"": 1}, {" subject ": 1}, {"s": 0},
                                      {"s": True}, {"s": "1"}, {"s": -1},
                                      {"a": 1, "b": 1}])
def test_identity_bindings_reject_ambiguous_or_invalid_accounts(bindings):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, SUPABASE_IDENTITY_BINDINGS=bindings)


def test_identity_bindings_parse_explicit_operator_json_without_enabling_autocreate():
    with patch.dict("os.environ", {"SUPABASE_IDENTITY_BINDINGS": '{"subject-1":17}'}, clear=True):
        settings = Settings(_env_file=None)
    assert settings.SUPABASE_IDENTITY_BINDINGS == {"subject-1": 17}
    assert settings.SUPABASE_AUTO_CREATE_USERS is False
