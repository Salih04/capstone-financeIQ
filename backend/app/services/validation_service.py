"""
Validation Service – V3
========================
Time-consistent rolling-window validation for scoring models.

Strategy
--------
* Sort all ComputedMetric rows by period (ascending).
* Use the earliest N-periods as training set, the rest as test.
* Assign success labels via the active LabelDefinition (or fallback to
  rule_based score >= threshold).
* Evaluate using sklearn metrics + confusion matrix.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.financial import ComputedMetric
from app.models.scoring_model import ScoringModel
from app.models.governance import ModelValidationRun, LabelDefinition
from app.services.scoring_service import run_score, _RULE_WEIGHTS

_FEATURES = list(_RULE_WEIGHTS.keys())


def _get_label(metrics_dict: dict, threshold: float) -> int:
    """Rule-based synthetic label: 1 if score >= threshold * 100."""
    rb = run_score(metrics_dict)
    return 1 if rb["total_score"] >= threshold * 100 else 0


def _build_dataset(db: Session, label_def: LabelDefinition | None = None):
    """Return (periods_sorted, X_dict, y_dict) keyed by (company_id, period)."""
    rows = db.query(ComputedMetric).order_by(ComputedMetric.period.asc()).all()
    threshold = label_def.success_threshold if label_def else 0.55

    dataset = []
    for row in rows:
        feat = {f: getattr(row, f, None) for f in _FEATURES}
        if any(v is None for v in feat.values()):
            continue
        label = _get_label(feat, threshold)
        dataset.append({
            "company_id": row.company_id,
            "period": row.period,
            "features": feat,
            "label": label,
        })

    # Sort by period then company_id
    dataset.sort(key=lambda x: (x["period"], x["company_id"]))
    return dataset


def run_time_split_validation(
    db: Session,
    scoring_model_id: int,
    train_ratio: float = 0.7,
    label_def_id: int | None = None,
) -> dict[str, Any]:
    """
    Perform a time-split validation:
      - sort dataset by period
      - train on first train_ratio of periods
      - test on remaining
    Returns a dict of metrics and persists a ModelValidationRun row.
    """
    try:
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score,
            f1_score, roc_auc_score, confusion_matrix,
        )
    except ImportError:
        return {"error": "scikit-learn not available"}

    label_def = db.get(LabelDefinition, label_def_id) if label_def_id else (
        db.query(LabelDefinition).filter(LabelDefinition.is_active == True).first()
    )

    dataset = _build_dataset(db, label_def)
    if len(dataset) < 6:
        return {"error": "Not enough data for validation (need ≥ 6 complete rows)."}

    # Unique sorted periods
    periods = sorted(set(d["period"] for d in dataset))
    split_idx = max(1, int(len(periods) * train_ratio))
    train_periods = set(periods[:split_idx])
    test_periods = set(periods[split_idx:])

    train_data = [d for d in dataset if d["period"] in train_periods]
    test_data = [d for d in dataset if d["period"] in test_periods]

    if not test_data:
        return {"error": "No test data after time split."}

    y_train = [d["label"] for d in train_data]
    if len(set(y_train)) < 2:
        return {"error": "Training set has only one class – cannot train classifier."}

    X_train = np.array([[d["features"][f] for f in _FEATURES] for d in train_data], dtype=float)
    X_test = np.array([[d["features"][f] for f in _FEATURES] for d in test_data], dtype=float)
    y_train_arr = np.array(y_train, dtype=int)
    y_test_arr = np.array([d["label"] for d in test_data], dtype=int)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    clf = LogisticRegression(max_iter=500, C=1.0, solver="lbfgs", class_weight="balanced")
    clf.fit(X_train_s, y_train_arr)

    y_pred = clf.predict(X_test_s)
    y_prob = clf.predict_proba(X_test_s)[:, 1]

    acc = float(accuracy_score(y_test_arr, y_pred))
    prec = float(precision_score(y_test_arr, y_pred, zero_division=0))
    rec = float(recall_score(y_test_arr, y_pred, zero_division=0))
    f1 = float(f1_score(y_test_arr, y_pred, zero_division=0))
    try:
        auc = float(roc_auc_score(y_test_arr, y_prob))
    except ValueError:
        auc = None

    cm = confusion_matrix(y_test_arr, y_pred).tolist()

    # Feature stability: coefficient sign check
    coefs = clf.coef_[0]
    feature_stability = []
    for i, f in enumerate(_FEATURES):
        feature_stability.append({
            "feature": f,
            "coefficient": round(float(coefs[i]), 4),
            "sign": "positive" if coefs[i] > 0 else "negative",
        })
    feature_stability.sort(key=lambda x: -abs(x["coefficient"]))

    calibration_summary = {
        "mean_predicted_prob": round(float(y_prob.mean()), 4),
        "mean_actual_label": round(float(y_test_arr.mean()), 4),
        "calibration_gap": round(float(abs(y_prob.mean() - y_test_arr.mean())), 4),
    }

    val_run = ModelValidationRun(
        scoring_model_id=scoring_model_id,
        validation_type="time_split",
        train_period_start=min(train_periods),
        train_period_end=max(train_periods),
        test_period_start=min(test_periods),
        test_period_end=max(test_periods),
        accuracy=acc,
        precision=prec,
        recall=rec,
        f1=f1,
        roc_auc=auc,
        support_total=len(y_test_arr),
        support_positive=int(y_test_arr.sum()),
        confusion_matrix_json=json.dumps(cm),
        calibration_summary=json.dumps(calibration_summary),
        notes=f"LR time-split {min(train_periods)}→{max(train_periods)} | test:{min(test_periods)}→{max(test_periods)}",
        created_at=datetime.now(timezone.utc),
    )
    db.add(val_run)

    # Update scoring model validation_summary_json
    model = db.get(ScoringModel, scoring_model_id)
    if model:
        model.validation_summary_json = json.dumps({
            "accuracy": acc, "precision": prec, "recall": rec,
            "f1": f1, "roc_auc": auc,
            "train_n": len(train_data), "test_n": len(test_data),
        })

    db.commit()
    db.refresh(val_run)

    return {
        "validation_run_id": val_run.id,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": auc,
        "support_total": len(y_test_arr),
        "support_positive": int(y_test_arr.sum()),
        "confusion_matrix": cm,
        "calibration_summary": calibration_summary,
        "feature_stability": feature_stability,
        "train_periods": sorted(train_periods),
        "test_periods": sorted(test_periods),
    }


def get_validation_history(db: Session, scoring_model_id: int) -> list[dict]:
    """Return all validation runs for a model, ordered most-recent first."""
    runs = (
        db.query(ModelValidationRun)
        .filter(ModelValidationRun.scoring_model_id == scoring_model_id)
        .order_by(ModelValidationRun.created_at.desc())
        .all()
    )
    out = []
    for r in runs:
        out.append({
            "id": r.id,
            "validation_type": r.validation_type,
            "train_period_start": r.train_period_start,
            "train_period_end": r.train_period_end,
            "test_period_start": r.test_period_start,
            "test_period_end": r.test_period_end,
            "accuracy": r.accuracy,
            "precision": r.precision,
            "recall": r.recall,
            "f1": r.f1,
            "roc_auc": r.roc_auc,
            "support_total": r.support_total,
            "support_positive": r.support_positive,
            "confusion_matrix": json.loads(r.confusion_matrix_json) if r.confusion_matrix_json else None,
            "calibration_summary": json.loads(r.calibration_summary) if r.calibration_summary else None,
            "notes": r.notes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return out
