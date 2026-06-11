"""Compatibility wrapper for the backend trusted-data validator.

Keeps `python -m scripts.validate_trusted_data` working from the repo root while
the implementation lives with backend code.
"""

from __future__ import annotations

import runpy
from pathlib import Path

BACKEND_VALIDATOR = Path(__file__).resolve().parents[1] / "backend" / "scripts" / "validate_trusted_data.py"

runpy.run_path(str(BACKEND_VALIDATOR), run_name="__main__")
