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
from sqlalchemy import func
from app.models.financial import ComputedMetric

# New multi-model family identifiers for v1 rollout.
MULTI_MODEL_IDS = (
    "elasticnet",
    "random_forest",
    "xgboost",
    "sarimax",
    "tft",
)

# Initial ensemble defaults; later replaced by validation-learned weights.
ENSEMBLE_WEIGHTS_V1: dict[str, float] = {
    "elasticnet": 0.2,
    "random_forest": 0.2,
    "xgboost": 0.2,
    "sarimax": 0.2,
    "tft": 0.2,
}


class ModelScoringUnavailable(ValueError):
    pass

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
    raw_total = 0.0
    available_weight = 0.0

    for metric, weight in w_map.items():
        scorer = _SCORERS.get(metric)
        if scorer is None:
            continue

        curr_val = current.get(metric)
        prev_val = prev.get(metric)

        # IMPORTANT:
        # Missing data should not be treated as 0 performance.
        # It is excluded from the available weight and does not penalize the company.
        if curr_val is None:
            details.append({
                "metric_name": _METRIC_LABELS.get(metric, metric),
                "metric_value": None,
                "normalized_value": None,
                "weight": float(weight),
                "contribution": None,
                "comment": f"{_METRIC_LABELS.get(metric, metric)} data is not available and was excluded from scoring.",
            })
            continue

        pts, comment = scorer(curr_val, prev_val, weight)

        details.append({
            "metric_name": _METRIC_LABELS.get(metric, metric),
            "metric_value": curr_val,
            "normalized_value": None,
            "weight": float(weight),
            "contribution": round(pts, 2),
            "comment": comment,
        })

        raw_total += pts
        available_weight += float(weight)

    if available_weight <= 0:
        total_score = 0.0
    else:
        total_score = round((raw_total / available_weight) * 100, 2)

    prob = round(total_score / 100, 4)

    valid_details = [d for d in details if d["contribution"] is not None]

    top_pos = sorted(
        [d for d in valid_details if d["contribution"] >= d["weight"] * 0.6],
        key=lambda x: -x["contribution"],
    )

    top_neg = sorted(
        [d for d in valid_details if d["contribution"] < d["weight"] * 0.3],
        key=lambda x: x["contribution"],
    )

    excluded = [d["metric_name"] for d in details if d["contribution"] is None]

    summary_parts = []

    if top_pos:
        summary_parts.append(
            f"Strongest drivers: {', '.join(d['metric_name'] for d in top_pos[:3])}."
        )

    if top_neg:
        summary_parts.append(
            f"Weak spots: {', '.join(d['metric_name'] for d in top_neg[:2])}."
        )

    if excluded:
        summary_parts.append(
            f"Excluded missing metrics: {', '.join(excluded[:3])}."
        )

    summary = " ".join(summary_parts) if summary_parts else "Scoring calculated."

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
    Train a LogisticRegression on historical computed metrics using real labels:
        label = 1  if next_period_net_income > current_period_net_income  (growth > 0)
        label = 0  otherwise

    Uses a time-based split: oldest 80% of periods for training, newest 20% for
    validation. Prints validation metrics (accuracy, precision, recall, F1, AUC)
    so quality is visible in server logs.

    Falls back to rule-based if real labels cannot be derived or data is too sparse.
    """
    try:
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score,
            f1_score, roc_auc_score, confusion_matrix,
        )
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return _rule_based_score(current, previous)

    FEATURES = list(_RULE_WEIGHTS.keys())

    if db is None:
        return _rule_based_score(current, previous)

    from app.models.company import Company
    from app.models.financial import ComputedMetric
    from app.models.forecasting import QuarterlyFundamental

    # Build labelled dataset using next-period net income growth
    rows = (
        db.query(ComputedMetric)
        .order_by(ComputedMetric.company_id, ComputedMetric.period)
        .all()
    )

    # Index QuarterlyFundamental by (stock_code, period) for fast lookup
    qf_index: dict[tuple[str, str], float | None] = {}
    for qf in db.query(QuarterlyFundamental).all():
        qf_index[(qf.stock_code, qf.period)] = qf.net_income

    # Group rows by company so we can find the next period per company
    from collections import defaultdict
    company_rows: dict[int, list[ComputedMetric]] = defaultdict(list)
    for row in rows:
        company_rows[row.company_id].append(row)

    # Build ticker lookup
    ticker_by_id: dict[int, str] = {
        c.id: c.ticker for c in db.query(Company).all()
    }

    X_rows, y_rows, period_tags = [], [], []
    for cid, crows in company_rows.items():
        ticker = ticker_by_id.get(cid)
        if not ticker:
            continue
        for i, row in enumerate(crows):
            feat = [getattr(row, f, None) for f in FEATURES]
            if all(v is None for v in feat):
                continue
            # Real label: did net income grow in the NEXT period?
            if i + 1 >= len(crows):
                continue  # no next period available
            next_row = crows[i + 1]
            curr_ni = qf_index.get((ticker, row.period))
            next_ni = qf_index.get((ticker, next_row.period))
            if curr_ni is None or next_ni is None:
                continue
            label = 1 if next_ni > curr_ni else 0
            X_rows.append(feat)
            y_rows.append(label)
            period_tags.append(row.period)

    if len(X_rows) < 4 or len(set(y_rows)) < 2:
        return _rule_based_score(current, previous)

    # Time-based split: train on oldest 80%, validate on newest 20%
    sorted_periods = sorted(set(period_tags))
    cutoff_idx = max(1, int(len(sorted_periods) * 0.8))
    cutoff_period = sorted_periods[cutoff_idx - 1]

    X_train, y_train, X_test, y_test = [], [], [], []
    for feat, label, period in zip(X_rows, y_rows, period_tags):
        if period <= cutoff_period:
            X_train.append(feat)
            y_train.append(label)
        else:
            X_test.append(feat)
            y_test.append(label)

    if len(X_train) < 4 or len(set(y_train)) < 2:
        return _rule_based_score(current, previous)

    X_tr = np.array(X_train, dtype=float)
    y_tr = np.array(y_train, dtype=int)

    imputer = SimpleImputer(strategy="mean")
    X_tr_imp = imputer.fit_transform(X_tr)

    scaler = StandardScaler()
    X_tr_scaled = scaler.fit_transform(X_tr_imp)

    clf = LogisticRegression(max_iter=500, C=1.0, solver="lbfgs")
    clf.fit(X_tr_scaled, y_tr)

    # Print validation metrics when test set is large enough
    if len(X_test) >= 4 and len(set(y_test)) >= 2:
        X_te_raw = np.array(X_test, dtype=float)
        X_te = scaler.transform(imputer.transform(X_te_raw))
        y_te = np.array(y_test, dtype=int)
        y_pred = clf.predict(X_te)
        y_prob = clf.predict_proba(X_te)[:, 1]
        cm = confusion_matrix(y_te, y_pred)
        print(
            f"[ML] train={len(X_train)} test={len(X_test)} cutoff={cutoff_period} | "
            f"acc={accuracy_score(y_te, y_pred):.3f} "
            f"prec={precision_score(y_te, y_pred, zero_division=0):.3f} "
            f"rec={recall_score(y_te, y_pred, zero_division=0):.3f} "
            f"f1={f1_score(y_te, y_pred, zero_division=0):.3f} "
            f"auc={roc_auc_score(y_te, y_prob):.3f} "
            f"cm={cm.tolist()}"
        )

    # Predict for the input company
    curr_feat = [current.get(f) for f in FEATURES]
    if all(v is None for v in curr_feat):
        return _rule_based_score(current, previous)

    X_pred = scaler.transform(imputer.transform([curr_feat]))
    prob = float(clf.predict_proba(X_pred)[0][1])
    total_score = round(prob * 100, 2)

    coefs = clf.coef_[0]
    details = []
    for i, metric in enumerate(FEATURES):
        val = current.get(metric)
        coef = float(coefs[i])
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
                + ("Positive contribution." if contribution > 0 else "Negative contribution.")
            ),
        })

    top_pos = sorted([d for d in details if d["contribution"] > 0], key=lambda x: -x["contribution"])
    top_neg = sorted([d for d in details if d["contribution"] < 0], key=lambda x: x["contribution"])
    summary = (
        "This probability is generated using a logistic regression model trained on "
        "real next-period net income growth labels. "
        f"Strong: {', '.join(d['metric_name'] for d in top_pos[:3])}. "
        f"Weak: {', '.join(d['metric_name'] for d in top_neg[:2])}."
    )

    return {
        "total_score": total_score,
        "success_probability": round(prob, 4),
        "label_used": "logistic_real_label",
        "explanation_summary": summary,
        "details": details,
    }


def _mean_impute_metrics(
    db,
    period: str | None,
    metrics: dict[str, float | None],
) -> dict[str, float | None]:
    if db is None or not metrics:
        return metrics

    keys = list(_RULE_WEIGHTS.keys())
    avg_cols = [func.avg(getattr(ComputedMetric, k)).label(k) for k in keys]
    query = db.query(*avg_cols)
    if period:
        query = query.filter(ComputedMetric.period == period)
    row = query.first()
    if not row:
        return metrics

    means: dict[str, float | None] = {}
    for k in keys:
        val = getattr(row, k, None)
        means[k] = float(val) if val is not None else None

    return {
        k: (means.get(k) if metrics.get(k) is None else metrics.get(k))
        for k in keys
    }


# ──────────────────────────────────────────────────────────────────────────────
# Multi-model helpers (v1)
# ──────────────────────────────────────────────────────────────────────────────

def _build_success_dataset(db) -> list[dict[str, Any]]:
    from collections import defaultdict
    from app.models.company import Company
    from app.models.financial import ComputedMetric
    from app.models.forecasting import QuarterlyFundamental, WinnerCohortRow

    features = list(_RULE_WEIGHTS.keys())
    rows = (
        db.query(ComputedMetric)
        .order_by(ComputedMetric.company_id, ComputedMetric.period.asc())
        .all()
    )
    ticker_by_id = {c.id: c.ticker for c in db.query(Company).all()}
    qf_index: dict[tuple[str, str], float | None] = {}
    for qf in db.query(QuarterlyFundamental).all():
        qf_index[(qf.stock_code, qf.period)] = qf.net_income

    return_by_year: dict[tuple[str, int], float | None] = {}
    for wr in db.query(WinnerCohortRow).all():
        return_by_year[(wr.stock_code, wr.year)] = wr.period_return

    company_rows: dict[int, list[ComputedMetric]] = defaultdict(list)
    for row in rows:
        company_rows[row.company_id].append(row)

    dataset: list[dict[str, Any]] = []
    for company_id, crows in company_rows.items():
        ticker = ticker_by_id.get(company_id)
        if not ticker:
            continue
        crows = sorted(crows, key=lambda r: r.period)
        for i, row in enumerate(crows):
            if i + 1 >= len(crows):
                continue
            feat = [getattr(row, f, None) for f in features]
            # Keep partially-missing rows; we impute later during training.
            if all(v is None for v in feat):
                continue
            next_row = crows[i + 1]
            curr_ni = qf_index.get((ticker, row.period))
            next_ni = qf_index.get((ticker, next_row.period))
            if curr_ni is None or next_ni is None:
                continue
            growth_success = next_ni > curr_ni
            try:
                year = int(str(row.period)[:4])
            except (TypeError, ValueError):
                year = None
            period_return = return_by_year.get((ticker, year)) if year is not None else None
            return_success = period_return is None or period_return > 0
            label = 1 if (growth_success and return_success) else 0
            dataset.append(
                {
                    "company_id": company_id,
                    "period": row.period,
                    "features": feat,
                    "label": label,
                }
            )
    return dataset


def _fit_family_model(
    mode: str,
    db,
    current_metrics: dict[str, float | None],
    company_id: int | None,
    period: str | None,
) -> dict[str, Any]:
    import numpy as np
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler

    features = list(_RULE_WEIGHTS.keys())
    current_row = [current_metrics.get(f) for f in features]
    if all(v is None for v in current_row):
        raise ModelScoringUnavailable(
            f"{mode} requires at least one available scoring metric for prediction."
        )

    dataset = _build_success_dataset(db)
    if company_id is not None and period is not None:
        dataset = [
            d
            for d in dataset
            if not (d["company_id"] == company_id and d["period"] == period)
        ]
    if len(dataset) < 20:
        raise ModelScoringUnavailable(
            f"{mode} has insufficient labeled history ({len(dataset)} rows)."
        )

    X = np.array([d["features"] for d in dataset], dtype=float)
    y = np.array([d["label"] for d in dataset], dtype=int)
    # Remove fully-empty rows before fitting imputers/models.
    valid_mask = np.isfinite(X).any(axis=1)
    X = X[valid_mask]
    y = y[valid_mask]
    if len(X) < 20:
        raise ModelScoringUnavailable(
            f"{mode} has insufficient usable history after filtering ({len(X)} rows)."
        )
    if len(set(y.tolist())) < 2:
        raise ModelScoringUnavailable(f"{mode} training labels contain only one class.")

    imputer = SimpleImputer(strategy="mean")
    X_imp = imputer.fit_transform(X)
    X_pred_imp = imputer.transform(np.array([current_row], dtype=float))

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X_imp)
    X_pred = scaler.transform(X_pred_imp)

    if mode == "elasticnet":
        from sklearn.linear_model import ElasticNet

        model = ElasticNet(alpha=0.05, l1_ratio=0.5, max_iter=2000, random_state=42)
        model.fit(Xs, y.astype(float))
        prob = float(model.predict(X_pred)[0])
        prob = max(0.0, min(1.0, prob))
        total_score = round(prob * 100, 2)
        details = []
        coefs = model.coef_
        for i, metric in enumerate(features):
            details.append(
                {
                    "metric_name": _METRIC_LABELS.get(metric, metric),
                    "metric_value": current_row[i],
                    "normalized_value": round(float(X_pred[0][i]), 4),
                    "weight": round(abs(float(coefs[i])), 4),
                    "contribution": round(float(coefs[i] * X_pred[0][i]), 4),
                    "comment": "ElasticNet coefficient-based contribution.",
                }
            )
        return {
            "total_score": total_score,
            "success_probability": round(prob, 4),
            "label_used": "elasticnet_success_return",
            "explanation_summary": "ElasticNet trained on success label from growth+returns.",
            "details": details,
        }

    if mode == "random_forest":
        from sklearn.ensemble import RandomForestClassifier

        model = RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            min_samples_leaf=3,
            random_state=42,
            class_weight="balanced",
        )
        model.fit(Xs, y)
        prob = float(model.predict_proba(X_pred)[0][1])
        total_score = round(prob * 100, 2)
        importances = model.feature_importances_
        details = []
        for i, metric in enumerate(features):
            details.append(
                {
                    "metric_name": _METRIC_LABELS.get(metric, metric),
                    "metric_value": current_row[i],
                    "normalized_value": round(float(X_pred[0][i]), 4),
                    "weight": round(float(importances[i]), 4),
                    "contribution": round(float(importances[i] * prob * 100), 4),
                    "comment": "RandomForest feature importance contribution.",
                }
            )
        return {
            "total_score": total_score,
            "success_probability": round(prob, 4),
            "label_used": "random_forest_success_return",
            "explanation_summary": "RandomForest trained on success label from growth+returns.",
            "details": details,
        }

    if mode == "xgboost":
        try:
            from xgboost import XGBClassifier
        except Exception as exc:
            raise ModelScoringUnavailable(
                "xgboost package is not available in the current environment."
            ) from exc
        model = XGBClassifier(
            n_estimators=250,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary:logistic",
            random_state=42,
            eval_metric="logloss",
        )
        model.fit(Xs, y)
        prob = float(model.predict_proba(X_pred)[0][1])
        total_score = round(prob * 100, 2)
        return {
            "total_score": total_score,
            "success_probability": round(prob, 4),
            "label_used": "xgboost_success_return",
            "explanation_summary": "XGBoost trained on success label from growth+returns.",
            "details": _rule_based_score(current_metrics).get("details", []),
        }

    if mode == "sarimax":
        raise ModelScoringUnavailable(
            "sarimax adapter is staged but not yet enabled in this environment."
        )

    if mode == "tft":
        raise ModelScoringUnavailable(
            "tft adapter is staged but not yet enabled in this environment."
        )

    raise ModelScoringUnavailable(f"Unknown model family: {mode}")


def run_multi_model_score(
    current_metrics: dict[str, float | None],
    previous_metrics: dict[str, float | None] | None,
    db,
    company_id: int | None,
    period: str | None,
    selected_models: list[str] | None = None,
) -> dict[str, Any]:
    requested = selected_models or list(MULTI_MODEL_IDS)
    invalid = [m for m in requested if m not in MULTI_MODEL_IDS]
    if invalid:
        raise ModelScoringUnavailable(f"Unsupported model ids: {', '.join(invalid)}")

    per_model: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    for model_id in requested:
        try:
            per_model[model_id] = _fit_family_model(
                model_id, db, current_metrics, company_id, period
            )
        except ModelScoringUnavailable as exc:
            warnings.append(f"{model_id}: {exc}")

    if not per_model:
        raise ModelScoringUnavailable(
            "No model outputs could be generated. " + " | ".join(warnings)
        )

    available_weights = {
        m: ENSEMBLE_WEIGHTS_V1[m] for m in per_model if m in ENSEMBLE_WEIGHTS_V1
    }
    weight_sum = sum(available_weights.values())
    if weight_sum <= 0:
        raise ModelScoringUnavailable("No ensemble weights available for active models.")

    ensemble_prob = sum(
        per_model[m]["success_probability"] * (w / weight_sum)
        for m, w in available_weights.items()
    )
    ensemble_score = round(ensemble_prob * 100, 2)
    imputed_current = _mean_impute_metrics(db, period, current_metrics)
    imputed_previous = _mean_impute_metrics(db, period, previous_metrics or {}) if previous_metrics else None
    details = _rule_based_score(imputed_current, imputed_previous).get("details", [])
    model_notes = ", ".join(sorted(per_model.keys()))
    summary = f"Ensemble_v1 computed from models: {model_notes}."
    if warnings:
        summary += f" Warnings: {' | '.join(warnings)}"

    return {
        "total_score": ensemble_score,
        "success_probability": round(ensemble_prob, 4),
        "label_used": "ensemble_v1",
        "explanation_summary": summary,
        "details": details,
        "per_model": per_model,
        "ensemble_weights": {m: round(w / weight_sum, 4) for m, w in available_weights.items()},
        "warnings": warnings,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Public entry-point
# ──────────────────────────────────────────────────────────────────────────────

def run_score(
    current_metrics: dict[str, float | None],
    previous_metrics: dict[str, float | None] | None = None,
    mode: str = "rule_based",
    custom_weights: dict | None = None,
    db=None,
    company_id: int | None = None,
    period: str | None = None,
) -> dict[str, Any]:
    if mode in MULTI_MODEL_IDS:
        if db is None:
            raise ModelScoringUnavailable(f"{mode} requires database-backed training data.")
        result = _fit_family_model(mode, db, current_metrics, company_id, period)
    else:
        imputed_current = _mean_impute_metrics(db, period, current_metrics) if db else current_metrics
        imputed_previous = (
            _mean_impute_metrics(db, period, previous_metrics) if (db and previous_metrics) else previous_metrics
        )
        result = _logistic_score(imputed_current, imputed_previous, db=db) if mode == "logistic" else _rule_based_score(
            imputed_current,
            imputed_previous,
            weights=custom_weights,
        )

    if db is None or company_id is None or period is None:
        return result

    try:
        from app.models.analytics import SectorNormalizedFeature

        norm_rows = (
            db.query(SectorNormalizedFeature)
            .filter(
                SectorNormalizedFeature.company_id == company_id,
                SectorNormalizedFeature.period == period,
            )
            .all()
        )

        norm_by_metric = {r.feature_name: r for r in norm_rows}

        total = 0.0
        available_weight = 0.0

        for d in result["details"]:
            metric_key = None
            for k, label in _METRIC_LABELS.items():
                if label == d["metric_name"]:
                    metric_key = k
                    break

            if metric_key is None:
                continue

            norm = norm_by_metric.get(metric_key)

            if norm is None or norm.percentile_rank is None or d["contribution"] is None:
                continue

            percentile = float(norm.percentile_rank)

            # Defensive normalization:
            # percentile_rank should be 0–1. If stored as 0–100, convert it.
            if percentile > 1:
                percentile = percentile / 100
            # Clamp to valid range
            percentile = max(0.0, min(1.0, percentile))
            d["normalized_value"] = round(percentile, 4)
            weight = float(d["weight"])
            original_points = float(d["contribution"])
            # Original contribution also must not exceed its own weight
            original_points = max(0.0, min(weight, original_points))
            sector_points = percentile * weight
            blended = (0.70 * original_points) + (0.30 * sector_points)
            # Final contribution must stay inside 0–weight
            blended = max(0.0, min(weight, blended))
            d["contribution"] = round(blended, 2)
            d["comment"] += f" Sector percentile: {percentile:.0%}."

            total += blended
            available_weight += weight

        if available_weight > 0:
            result["total_score"] = round((total / available_weight) * 100, 2)
            result["success_probability"] = round(result["total_score"] / 100, 4)

        result["label_used"] = f"{result['label_used']}_sector_adjusted"
        result["explanation_summary"] += " Sector percentile adjustment applied."

    except Exception as exc:
        result["explanation_summary"] += f" Sector adjustment skipped: {exc}"

    return result
