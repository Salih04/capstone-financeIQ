"""Point-in-time guard: availability is checked from timestamps, never from names.

Three checks, all fail closed:

1. ``assert_registered`` — every model feature exists in the registry and is
   ``admitted``. Unknown or excluded features are refused.
2. ``assert_point_in_time`` — for every (row, feature) with a value, the
   recorded ``available_at`` is not later than the row's ``prediction_time``.
   A value without an ``available_at`` is itself a violation.
3. ``assert_labels_realized`` — every training label was fully realised (its
   window ended) before the prediction time of the rows it is used to score.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from experiments.pit import config as cfg


class PointInTimeViolation(AssertionError):
    """A feature or label would be used before it was publicly available."""


def load_registry(path: Path = cfg.REGISTRY_PATH) -> dict[str, dict]:
    payload = json.loads(Path(path).read_text())
    if payload.get("registry") != "feature_availability_registry":
        raise PointInTimeViolation(f"{path} is not a feature availability registry")
    features = {f["name"]: f for f in payload["features"]}
    if len(features) != len(payload["features"]):
        raise PointInTimeViolation("duplicate feature names in registry")
    return features


def assert_registered(features: list[str], registry: dict[str, dict]) -> None:
    unknown = [f for f in features if f not in registry]
    excluded = [f for f in features if f in registry and registry[f]["status"] != "admitted"]
    if unknown or excluded:
        raise PointInTimeViolation(
            f"features not admitted by the availability registry: unknown={unknown}, "
            f"excluded={excluded}")


def assert_point_in_time(values: pd.DataFrame, availability: pd.DataFrame,
                         features: list[str]) -> None:
    """``values``: one row per observation with ``prediction_time`` and feature columns.
    ``availability``: same index, one ``available_at`` timestamp column per feature.
    """
    if "prediction_time" not in values or values["prediction_time"].isna().any():
        raise PointInTimeViolation("every evaluated row needs a prediction_time")
    problems = []
    for feat in features:
        if feat not in availability:
            raise PointInTimeViolation(f"no availability timestamps recorded for {feat}")
        present = values[feat].notna()
        when = availability.loc[present, feat]
        missing = when.isna()
        late = when > values.loc[present, "prediction_time"]
        for idx in when.index[missing | late]:
            problems.append({
                "row": idx, "feature": feat,
                "ticker": values.at[idx, "ticker"] if "ticker" in values else None,
                "available_at": None if pd.isna(when[idx]) else str(when[idx]),
                "prediction_time": str(values.at[idx, "prediction_time"]),
            })
    if problems:
        head = problems[:10]
        raise PointInTimeViolation(
            f"{len(problems)} feature values are not available at prediction time; first: {head}")


def assert_labels_realized(train_label_end: pd.Series, prediction_time: pd.Series) -> None:
    """Training labels must have ended strictly before the earliest scored prediction."""
    if train_label_end.isna().any():
        raise PointInTimeViolation("training rows without a realised label end date")
    if len(prediction_time) and train_label_end.max() >= prediction_time.min():
        raise PointInTimeViolation(
            f"training label ends {train_label_end.max()} but scoring starts "
            f"{prediction_time.min()}")
