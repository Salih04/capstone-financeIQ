"""Missing-to-null coercion for stored financial values.

A stored financial fact is either a finite float or null. NaN, +/-Infinity and
overflowed values are missing: they are never stored, never turned into 0.0 and
never replaced by an imputed value.
"""
from __future__ import annotations

import math
from typing import Any


def finite_or_none(value: Any) -> float | None:
    """Return ``value`` as a finite float, or None when it is missing/non-finite.

    Non-numeric input (e.g. ``"abc"``) still raises ``ValueError``/``TypeError``
    so each caller keeps its own error handling for malformed cells.
    """
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None
