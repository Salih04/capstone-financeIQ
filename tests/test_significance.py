from __future__ import annotations

import numpy as np
import pandas as pd

from experiments import significance


def _prediction_frame(y_true: list[np.ndarray], y_pred: list[np.ndarray]) -> pd.DataFrame:
    frames = []
    for offset, (actual, predicted) in enumerate(zip(y_true, y_pred)):
        year = 2023 + offset
        frames.append(
            pd.DataFrame(
                {
                    "ticker": [f"T{index:02d}" for index in range(len(actual))],
                    "year": year,
                    "model": "test_model",
                    "y_true": actual,
                    "y_pred": predicted,
                    "split": f"test_{year}",
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def test_planted_signal_has_small_permutation_p_value() -> None:
    rng = np.random.default_rng(11)
    actual = [rng.normal(size=32) for _ in range(3)]
    predicted = [values + rng.normal(scale=0.15, size=len(values)) for values in actual]

    result = significance.analyze_model(
        _prediction_frame(actual, predicted),
        permutations=1_000,
        bootstraps=500,
        seed=7,
    )["pooled"]

    assert result["observed_ic"] > 0.9
    assert result["permutation_p_value_two_sided"] <= 0.01
    assert result["bootstrap_ci_95"][0] > 0.8


def test_seeded_shuffled_data_has_non_extreme_p_value_and_is_deterministic() -> None:
    rng = np.random.default_rng(29)
    actual = [rng.normal(size=36) for _ in range(3)]
    predicted = [rng.normal(size=36) for _ in range(3)]
    frame = _prediction_frame(actual, predicted)

    first = significance.analyze_model(
        frame, permutations=1_000, bootstraps=400, seed=17
    )
    second = significance.analyze_model(
        frame, permutations=1_000, bootstraps=400, seed=17
    )

    p_value = first["pooled"]["permutation_p_value_two_sided"]
    assert 0.1 < p_value < 0.9
    assert first == second
