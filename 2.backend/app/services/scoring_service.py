"""
Dual-mode Scoring Engine
========================
Mode 1 – rule_based   : weighted rule scoring (0-100) + normalised probability
Mode 2 – logistic     : sklearn LogisticRegression trained on in-DB data

run_score() is the single entry-point for both modes and returns a uniform dict:
    {
        "total_score": float,          # 0-100
        "success_probability": float,  # 0-1
        "label_used": str,
        "explanation_summary": str,
        "details": [
            {
                "metric_name": str,
                "metric_value": float|None,
                "normalized_value": float|None,
                "weight": float,
                "contribution": float,
                "comment": str,
            }
        ]
    }
"""
from __future__ import annotations
from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# Rule-based scoring helpers
# ──────────────────────────────────────────────────────────────────────────────

_RULE_WEIGHTS = {
    "roa": 15,
    "roe": 15,
    "operating_margin": 10,
    "net_margin": 5,
    "current_ratio": 10,
    "quick_ratio": 5,
    "cash_ratio": 5,
    "debt_to_equity": 10,
    "debt_to_assets": 5,
    "ocf_to_debt": 10,
    "ocf_to_assets": 5,
    "cash_flow_margin": 5,
}  # total = 100

_METRIC_LABELS = {
    "roa": "Return on Assets (ROA)",
    "roe": "Return on Equity (ROE)",
    "operating_margin": "Operating Margin",
    "net_margin": "Net Profit Margin",
    "current_ratio": "Current Ratio",
    "quick_ratio": "Quick Ratio",
    "cash_ratio": "Cash Ratio",
    "debt_to_equity": "Debt / Equity",
    "debt_to_assets": "Debt / Assets",
    "ocf_to_debt": "OCF / Total Debt",
    "ocf_to_assets": "OCF / Total Assets",
    "cash_flow_margin": "Cash Flow Margin",
}


def _score_pct_metric(v, prev, ideal_low, ideal_high, label, weight,
                       higher_is_better=True):
    """Generic scorer for percentage-based metrics (ROA, ROE, margins)."""
    if v is None:
        return 0.0, f"{label} data is not found."
    w = float(weight)
    if higher_is_better:
        if v >= ideal_high:
            pts = w
            comment = f"{label} {v:.2%} – very strong."
        elif v >= ideal_low:
            pts = w * 0.65
            comment = f"{label} {v:.2%} – medium level."
        elif v > 0:
            pts = w * 0.30
            comment = f"{label} {v:.2%} – weak but positive."
        else:
            pts = 0.0
            comment = f"{label} {v:.2%} – negative."
    else:
        if v <= ideal_low:
            pts = w
            comment = f"{label} {v:.2f} – very good (low)."
        elif v <= ideal_high:
            pts = w * 0.60
            comment = f"{label} {v:.2f} – medium."
        else:
            pts = 0.0
            comment = f"{label} {v:.2f} – high risk."

    trend_bonus = w * 0.20
    if prev is not None:
        if (higher_is_better and v > prev) or (not higher_is_better and v < prev):
            pts = min(pts + trend_bonus, w)
            comment += " Improving trend ✓"
        elif (higher_is_better and v < prev) or (not higher_is_better and v > prev):
            pts = max(pts - trend_bonus, 0)
            comment += " Deteriorating trend ✗"
    return pts, comment


def _score_current_ratio(v, prev, weight):
    if v is None:
        return 0.0, "Current ratio data not available."
    w = float(weight)
    if 1.5 <= v <= 3.0:
        pts = w
        comment = f"Current ratio {v:.2f} – ideal range."
    elif 1.2 <= v < 1.5 or 3.0 < v <= 4.0:
        pts = w * 0.60
        comment = f"Current ratio {v:.2f} – acceptable."
    elif 1.0 <= v < 1.2:
        pts = w * 0.25
        comment = f"Current ratio {v:.2f} – liquidity pressure."
    elif v > 4.0:
        pts = w * 0.45
        comment = f"Current ratio {v:.2f} – extremely high."
    else:
        pts = 0.0
        comment = f"Current ratio {v:.2f} – below 1, critical."
    if prev is not None:
        if abs(v - 2.0) < abs(prev - 2.0):
            pts = min(pts + w * 0.15, w)
            comment += " Approaching the ideal range ✓"
    return pts, comment


_SCORERS = {
    "roa":            lambda v, p, w: _score_pct_metric(v, p, 0.05, 0.10, "ROA", w),
    "roe":            lambda v, p, w: _score_pct_metric(v, p, 0.08, 0.15, "ROE", w),
    "operating_margin": lambda v, p, w: _score_pct_metric(v, p, 0.10, 0.20, "Operating Margin", w),
    "net_margin":     lambda v, p, w: _score_pct_metric(v, p, 0.05, 0.12, "Net Margin", w),
    "current_ratio":  lambda v, p, w: _score_current_ratio(v, p, w),
    "quick_ratio":    lambda v, p, w: _score_pct_metric(v, p, 0.8, 1.5, "Quick Ratio", w, True),
    "cash_ratio":     lambda v, p, w: _score_pct_metric(v, p, 0.2, 0.5, "Cash Ratio", w, True),
    "debt_to_equity": lambda v, p, w: _score_pct_metric(v, p, 0.5, 1.5, "D/E", w, False),
    "debt_to_assets": lambda v, p, w: _score_pct_metric(v, p, 0.3, 0.6, "D/Assets", w, False),
    "ocf_to_debt":    lambda v, p, w: _score_pct_metric(v, p, 0.15, 0.25, "OCF/Debt", w, True),
    "ocf_to_assets":  lambda v, p, w: _score_pct_metric(v, p, 0.05, 0.15, "OCF/Assets", w, True),
    "cash_flow_margin": lambda v, p, w: _score_pct_metric(v, p, 0.08, 0.18, "CF Margin", w, True),
}


def _rule_based_score(
    current: dict[str, float | None],
    previous: dict[str, float | None] | None = None,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    prev = previous or {}
    w_map = weights or _RULE_WEIGHTS
    details = []
    total = 0.0

    for metric, weight in w_map.items():
        scorer = _SCORERS.get(metric)
        if scorer is None:
            continue
        curr_val = current.get(metric)
        prev_val = prev.get(metric)
        pts, comment = scorer(curr_val, prev_val, weight)
        details.append({
            "metric_name": _METRIC_LABELS.get(metric, metric),
            "metric_value": curr_val,
            "normalized_value": None,
            "weight": float(weight),
            "contribution": round(pts, 2),
            "comment": comment,
        })
        total += pts

    total_score = round(total, 2)
    prob = round(total_score / 100, 4)

    top_pos = sorted([d for d in details if d["contribution"] >= d["weight"] * 0.6],
                     key=lambda x: -x["contribution"])
    top_neg = sorted([d for d in details if d["contribution"] < d["weight"] * 0.3],
                     key=lambda x: x["contribution"])
    summary = (
        f"Strongest drivers: {', '.join(d['metric_name'] for d in top_pos[:3])}. "
        f"Weak Spots: {', '.join(d['metric_name'] for d in top_neg[:2])}."
        if top_pos or top_neg else "Scoring Calculated."
    )

    return {
        "total_score": total_score,
        "success_probability": prob,
        "label_used": "rule_based",
        "explanation_summary": summary,
        "details": details,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Logistic Regression mode
# ──────────────────────────────────────────────────────────────────────────────

def _logistic_score(
    current: dict[str, float | None],
    previous: dict[str, float | None] | None = None,
    db=None,
) -> dict[str, Any]:
    """
    Train a LogisticRegression on all in-DB computed metrics,
    using rule-based score ≥ 60 as synthetic success label,
    then predict probability for the given company.
    Falls back to rule-based if not enough data.
    """
    try:
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.exceptions import NotFittedError
    except ImportError:
        return _rule_based_score(current, previous)

    FEATURES = list(_RULE_WEIGHTS.keys())

    if db is None:
        return _rule_based_score(current, previous)

    # Gather training samples from DB
    from app.models.financial import ComputedMetric
    rows = db.query(ComputedMetric).all()
    X_rows, y_rows = [], []
    for row in rows:
        feat = [getattr(row, f, None) for f in FEATURES]
        if any(v is None for v in feat):
            continue
        # Synthetic label from rule-based score
        metrics_dict = {f: getattr(row, f, None) for f in FEATURES}
        rb = _rule_based_score(metrics_dict)
        label = 1 if rb["total_score"] >= 55 else 0
        X_rows.append(feat)
        y_rows.append(label)

    if len(X_rows) < 4 or len(set(y_rows)) < 2:
        # Not enough diverse training data – fall back
        return _rule_based_score(current, previous)

    X = np.array(X_rows, dtype=float)
    y = np.array(y_rows, dtype=int)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    clf = LogisticRegression(max_iter=500, C=1.0, solver="lbfgs")
    clf.fit(X_scaled, y)

    # Predict for the input company
    curr_feat = [current.get(f) for f in FEATURES]
    has_null = any(v is None for v in curr_feat)
    if has_null:
        return _rule_based_score(current, previous)

    X_pred = scaler.transform([curr_feat])
    prob = float(clf.predict_proba(X_pred)[0][1])
    total_score = round(prob * 100, 2)

    # Build breakdown using coefficients as weights
    coefs = clf.coef_[0]
    details = []
    for i, metric in enumerate(FEATURES):
        val = current.get(metric)
        coef = float(coefs[i])
        # Normalised contribution = coef * scaled_feature_value
        scaled_val = float(X_pred[0][i])
        contribution = round(coef * scaled_val, 4)
        details.append({
            "metric_name": _METRIC_LABELS.get(metric, metric),
            "metric_value": val,
            "normalized_value": round(scaled_val, 4),
            "weight": round(abs(coef), 4),
            "contribution": contribution,
            "comment": (
                f"Coefficient: {coef:+.3f}. "
                + ("Positive contribution" if contribution > 0 else "Negative contribution.")
            ),
        })

    top_pos = sorted([d for d in details if d["contribution"] > 0], key=lambda x: -x["contribution"])
    top_neg = sorted([d for d in details if d["contribution"] < 0], key=lambda x: x["contribution"])
    summary = (
        f"LR model. Strong: {', '.join(d['metric_name'] for d in top_pos[:3])}. "
        f"Weak: {', '.join(d['metric_name'] for d in top_neg[:2])}."
    )

    return {
        "total_score": total_score,
        "success_probability": round(prob, 4),
        "label_used": "logistic",
        "explanation_summary": summary,
        "details": details,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Public entry-point
# ──────────────────────────────────────────────────────────────────────────────

def run_score(
    current_metrics: dict[str, float | None],
    previous_metrics: dict[str, float | None] | None = None,
    mode: str = "rule_based",        # "rule_based" | "logistic"
    custom_weights: dict | None = None,
    db=None,
) -> dict[str, Any]:
    if mode == "logistic":
        return _logistic_score(current_metrics, previous_metrics, db=db)
    return _rule_based_score(current_metrics, previous_metrics, weights=custom_weights)


