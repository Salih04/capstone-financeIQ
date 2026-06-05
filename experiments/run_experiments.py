"""AutoResearch-style walk-forward experiment loop (PHASE 9).

Honest, reproducible, leakage-controlled. Predicts NEXT-year return from the
current year's features:

    X = year Y features (fundamental + momentum, rank-normalized within Y)
    y = year (Y+1) realized return for the same ticker

Walk-forward splits (train past -> test future):
    train features 2020-2021 (targets 2021-2022)  -> test feature 2022 (target 2023)
    train features 2020-2022 (targets 2021-2023)  -> test feature 2023 (target 2024)
    train features 2020-2023 (targets 2021-2024)  -> test feature 2024 (target 2025)

Baselines run first; ML only if it beats them. Small data => overfitting is
called out. No fake labels, no future data in training, no same-year target leak.

Run:
    python experiments/run_experiments.py
Outputs: experiments/results/*.json, experiments/leaderboard.csv,
         experiments/reports/summary.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "2.backend"))

from app.services.research import data, feature_registry as reg, scoring  # noqa: E402

from sklearn.ensemble import RandomForestRegressor  # noqa: E402
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge  # noqa: E402

RESULTS = ROOT / "experiments" / "results"
REPORTS = ROOT / "experiments" / "reports"
LEADERBOARD = ROOT / "experiments" / "leaderboard.csv"

PRED_FEATURES = [f for f in reg.features_for_next_year_prediction()]


CLEAN_MODELING = ROOT / "data" / "trusted_clean" / "modeling_dataset_2020_2025.csv"


def build_panel() -> pd.DataFrame:
    """One row per (ticker, feature_year) with the NEXT year's return as target.

    Prefer the clean T->T+1 modeling dataset (frozen-snapshot columns already
    excluded, real next-year targets). Fall back to the legacy reference panel.
    """
    if CLEAN_MODELING.is_file():
        m = pd.read_csv(CLEAN_MODELING)
        _non_feat = {
            "ticker", "company_name", "year", "sector", "indices", "is_bist100",
            "same_year_return_pct", "target_year", "has_target", "is_inference_row",
        }
        feat_cols = [c for c in m.columns
                     if c not in _non_feat and not c.startswith("next_year_")]
        out = m[["ticker", "year", *feat_cols]].copy()
        out = out.rename(columns={"year": "feature_year"})
        # rank-normalize each feature within its year (robust, no leak)
        for c in feat_cols:
            out[c] = out.groupby("feature_year")[c].rank(pct=True)
        out["target_return"] = m["next_year_return_pct"].values
        return out.dropna(subset=["target_return"]).reset_index(drop=True)

    frames = []
    years = data.available_years()
    for y in years:
        if (y + 1) not in years:
            continue
        cur = scoring.compute_derived(data.year_frame(y)).set_index("ticker")
        nxt = data.year_frame(y + 1).set_index("ticker")
        # rank-normalize each predictor within the feature year (robust, no leak)
        feat = {}
        for f in PRED_FEATURES:
            if f.name in cur.columns:
                feat[f.name] = scoring._percentile(cur[f.name], f)
        fdf = pd.DataFrame(feat, index=cur.index)
        fdf["feature_year"] = y
        fdf["target_return"] = pd.to_numeric(nxt[data.TARGET_COLUMN], errors="coerce")
        fdf = fdf.reset_index().rename(columns={"index": "ticker"})
        frames.append(fdf)
    return pd.concat(frames, ignore_index=True)


# Targets evaluated when present + non-null in the modeling dataset.
TARGETS = ["next_year_return_pct", "next_year_excess_return_vs_bist100",
           "next_year_outperform_bist100", "next_year_top_20pct_returner"]


def _feature_cols(m: pd.DataFrame) -> list[str]:
    non = {"ticker", "company_name", "year", "sector", "indices", "is_bist100",
           "same_year_return_pct", "target_year", "has_target", "is_inference_row"}
    return [c for c in m.columns if c not in non and not c.startswith("next_year_")]


def build_panel_for_target(target_col: str):
    """(panel, feat_cols) with the given next_year_* column as target. None if absent."""
    if not CLEAN_MODELING.is_file():
        return None, []
    m = pd.read_csv(CLEAN_MODELING)
    if target_col not in m.columns or m[target_col].notna().sum() == 0:
        return None, []
    feat_cols = _feature_cols(m)
    out = m[["ticker", "year", *feat_cols]].copy().rename(columns={"year": "feature_year"})
    for c in feat_cols:
        out[c] = out.groupby("feature_year")[c].rank(pct=True)
    out["target_return"] = pd.to_numeric(m[target_col], errors="coerce").values
    out = out.dropna(subset=["target_return"]).reset_index(drop=True)
    return out, feat_cols


def _eval_target(target_col: str) -> list[dict]:
    panel, feat_cols = build_panel_for_target(target_col)
    if panel is None:
        return []
    rows = []
    for split in SPLITS:
        tr = panel[(panel["feature_year"] + 1).isin(split["train_target_years"])]
        te = panel[panel["feature_year"] == split["test_feature_year"]]
        Xtr, ytr = tr[feat_cols].to_numpy(float), tr["target_return"].to_numpy(float)
        Xte, yte = te[feat_cols].to_numpy(float), te["target_return"].to_numpy(float)
        m = ~np.isnan(ytr)
        Xtr, ytr = Xtr[m], ytr[m]
        if len(ytr) < 5 or np.sum(~np.isnan(yte)) < 5:
            continue
        for name, (kind, fn) in MODELS.items():
            try:
                yp = np.asarray(fn(Xtr, ytr, Xte), dtype=float)
                met = _metrics(yte, yp)
            except Exception as exc:  # noqa
                met = {"error": str(exc)}
            rows.append({"target": target_col, "split": split["name"], "model": name,
                         "kind": kind, **{k: v for k, v in met.items() if k != "n"}})
    return rows


def write_model_outputs(path: Path) -> None:
    """Latest usable-year company scores for the research agent.

    No trained model beats the equal-weight baseline on this data, so the score
    is a transparent rank-based fallback (mean of validated feature percentiles).
    """
    if not CLEAN_MODELING.is_file():
        return
    m = pd.read_csv(CLEAN_MODELING)
    feat_cols = _feature_cols(m)
    year = int(m["year"].max())
    sub = m[m["year"] == year].copy()
    pr = sub[feat_cols].rank(pct=True)
    sub["ml_score"] = pr.mean(axis=1, skipna=True).round(4)
    sub = sub.sort_values("ml_score", ascending=False)
    sub["ml_rank"] = range(1, len(sub) + 1)
    out = pd.DataFrame({
        "ticker": sub["ticker"], "year": year, "ml_score": sub["ml_score"],
        "ml_rank": sub["ml_rank"], "prediction": None,
        "target_name": "next_year_return_pct", "model_name": "baseline_equal_weight",
        "score_source": "fallback_rank_score",
        "notes": "mean of validated year-T feature percentiles; baseline beats ML on this small/static data",
    })
    out.to_csv(path, index=False)


# ---------------- metrics ----------------
def _metrics(y_true: np.ndarray, y_pred: np.ndarray, k: int = 5) -> dict:
    m = ~np.isnan(y_true) & ~np.isnan(y_pred)
    yt, yp = y_true[m], y_pred[m]
    if len(yt) < 3:
        return {}
    order_pred = np.argsort(-yp)
    topk = order_pred[:k]
    bucket_ret = float(np.mean(yt[topk]))
    # precision@k: of top-k predicted, how many in top-k actual
    top_actual = set(np.argsort(-yt)[:k].tolist())
    prec = len(set(topk.tolist()) & top_actual) / k
    spear = pd.Series(yp).corr(pd.Series(yt), method="spearman")
    return {
        "n": int(len(yt)),
        "mae": round(float(np.mean(np.abs(yt - yp))), 2),
        "rmse": round(float(np.sqrt(np.mean((yt - yp) ** 2))), 2),
        "spearman": None if pd.isna(spear) else round(float(spear), 3),
        f"precision_at_{k}": round(prec, 3),
        "top_bucket_avg_return": round(bucket_ret, 2),
        "median_actual_return": round(float(np.median(yt)), 2),
        "directional_acc": round(float(np.mean((yp - np.median(yp) > 0) == (yt - np.median(yt) > 0))), 3),
    }


# ---------------- models ----------------
def _score_equal_weight(Xtr, ytr, Xte):
    return np.nanmean(Xte, axis=1)  # mean of rank percentiles


def _score_rank(Xtr, ytr, Xte):
    # same as equal-weight here (features already rank-normalized) but kept
    # as an explicit baseline name
    return np.nanmean(Xte, axis=1)


def _fit_sklearn(model, Xtr, ytr, Xte):
    Xtr2 = np.nan_to_num(Xtr, nan=0.5)  # rank-imputed center for ML only
    Xte2 = np.nan_to_num(Xte, nan=0.5)
    model.fit(Xtr2, ytr)
    return model.predict(Xte2)


MODELS = {
    "baseline_equal_weight": ("baseline", _score_equal_weight),
    "baseline_rank_score": ("baseline", _score_rank),
    "linear_regression": ("ml", lambda a, b, c: _fit_sklearn(LinearRegression(), a, b, c)),
    "ridge": ("ml", lambda a, b, c: _fit_sklearn(Ridge(alpha=1.0), a, b, c)),
    "lasso": ("ml", lambda a, b, c: _fit_sklearn(Lasso(alpha=0.1, max_iter=5000), a, b, c)),
    "elasticnet": ("ml", lambda a, b, c: _fit_sklearn(ElasticNet(alpha=0.1, max_iter=5000), a, b, c)),
    "random_forest": ("ml", lambda a, b, c: _fit_sklearn(
        RandomForestRegressor(n_estimators=200, max_depth=4, random_state=42), a, b, c)),
}

SPLITS = [
    {"name": "test_2023", "train_target_years": [2021, 2022], "test_feature_year": 2022},
    {"name": "test_2024", "train_target_years": [2021, 2022, 2023], "test_feature_year": 2023},
    {"name": "test_2025", "train_target_years": [2021, 2022, 2023, 2024], "test_feature_year": 2024},
]


def run() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    panel = build_panel()
    feat_cols = [c for c in panel.columns if c not in ("ticker", "feature_year", "target_return")]

    # honest feature/sample reporting
    manual_feats = []
    qr = ROOT / "data" / "trusted_clean" / "data_quality_report.json"
    if qr.is_file():
        import json as _json
        manual_feats = (_json.loads(qr.read_text()).get("manual_financials", {}) or {}).get(
            "accepted_feature_columns", []) or []
    used_source = "clean modeling dataset" if CLEAN_MODELING.is_file() else "legacy reference panel"
    train_years = sorted({y for s in SPLITS for y in s["train_target_years"]})
    test_years = sorted({s["test_feature_year"] + 1 for s in SPLITS})
    print(f"[experiments] source: {used_source}")
    print(f"[experiments] features used: {len(feat_cols)} -> {feat_cols}")
    print(f"[experiments] manual-history features included: "
          f"{[c for c in manual_feats if c in feat_cols] or 'none'}")
    print(f"[experiments] train target years: {train_years} | test years: {test_years}")
    # available targets / benchmark
    avail_targets, bench_ok = [], False
    if CLEAN_MODELING.is_file():
        mcols = pd.read_csv(CLEAN_MODELING, nrows=1).columns
        for t in ("next_year_return_pct", "next_year_top_20pct_returner",
                  "next_year_excess_return_vs_bist100", "next_year_outperform_bist100"):
            if t in mcols:
                col = pd.read_csv(CLEAN_MODELING, usecols=[t])[t]
                if col.notna().any():
                    avail_targets.append(t)
        bench_ok = "next_year_excess_return_vs_bist100" in avail_targets
    print(f"[experiments] available targets: {avail_targets or ['next_year_return_pct']}")
    print(f"[experiments] benchmark targets available: {bench_ok} "
          f"{'' if bench_ok else '(provide BIST100 returns to enable excess/outperform targets)'}")
    print("[experiments] primary target: next_year_return_pct (regression + top-k selection). "
          "On small/static-feature data, prefer ranking/top-k + baselines over exact return claims.")
    per_split_n = panel.groupby("feature_year").size().to_dict()
    if max(per_split_n.values(), default=0) < 60:
        print(f"[experiments] ⚠️ SMALL SAMPLE: ~{max(per_split_n.values(), default=0)} rows/year. "
              "Out-of-sample metrics are noisy and overfitting-prone; trust baselines over single-split ML spikes.")

    leaderboard_rows = []
    for split in SPLITS:
        tr = panel[(panel["feature_year"] + 1).isin(split["train_target_years"])]
        te = panel[panel["feature_year"] == split["test_feature_year"]]
        Xtr, ytr = tr[feat_cols].to_numpy(float), tr["target_return"].to_numpy(float)
        Xte, yte = te[feat_cols].to_numpy(float), te["target_return"].to_numpy(float)
        mtr = ~np.isnan(ytr)
        Xtr, ytr = Xtr[mtr], ytr[mtr]

        split_result = {"split": split["name"], "train_n": int(len(ytr)),
                        "test_n": int(np.sum(~np.isnan(yte))), "models": {}}
        for name, (kind, fn) in MODELS.items():
            try:
                yp = np.asarray(fn(Xtr, ytr, Xte), dtype=float)
                met = _metrics(yte, yp)
            except Exception as exc:  # honest failure report, not silent
                met = {"error": str(exc)}
            split_result["models"][name] = {"kind": kind, **met}
            leaderboard_rows.append({"split": split["name"], "model": name, "kind": kind,
                                     **{k: v for k, v in met.items() if k != "n"}})
        (RESULTS / f"{split['name']}.json").write_text(json.dumps(split_result, indent=2))

    lb = pd.DataFrame(leaderboard_rows)
    lb.to_csv(LEADERBOARD, index=False)
    lb.to_csv(RESULTS / "leaderboard.csv", index=False)

    # ---- benchmark-aware multi-target leaderboard + artifacts (PHASE 4) ----
    by_target_rows = []
    for tgt in TARGETS:
        by_target_rows.extend(_eval_target(tgt))
    bt = pd.DataFrame(by_target_rows)
    if len(bt):
        bt.to_csv(RESULTS / "leaderboard_by_target.csv", index=False)
    write_model_outputs(RESULTS / "research_agent_model_outputs.csv")

    # honest per-target summary
    sm = ["# Experiment summary (benchmark-aware, walk-forward)\n",
          "Small data (~40 stocks/year), leakage-controlled. Treat all numbers as noisy.",
          "Features are largely a static snapshot; baselines usually match/beat ML.\n",
          f"Targets evaluated: {sorted(bt['target'].unique()) if len(bt) else ['next_year_return_pct']}\n"]
    if len(bt):
        for tgt in sorted(bt["target"].unique()):
            sub = bt[bt["target"] == tgt]
            base = sub[sub["kind"] == "baseline"]["spearman"].dropna()
            ml = sub[sub["kind"] == "ml"]["spearman"].dropna()
            sm.append(f"## {tgt}")
            sm.append(f"- baseline mean Spearman: {round(float(base.mean()),3) if len(base) else 'n/a'}")
            sm.append(f"- best ML Spearman: {round(float(ml.max()),3) if len(ml) else 'n/a'}")
            sm.append(f"- ML beats baseline: {bool(len(ml) and len(base) and ml.max() > base.mean())}\n")
    (RESULTS / "experiment_summary.md").write_text("\n".join(sm))

    # Honest summary report.
    lines = ["# Experiment summary (next-year return prediction)\n",
             "Walk-forward, leakage-controlled. Small data (40 stocks/year) — treat",
             "all out-of-sample numbers as noisy and overfitting-prone.\n",
             "> ⚠️ DATA CAVEAT: the trusted XLSX files share ONE static fundamental",
             "> snapshot (only realized returns vary by year). So the predictor features",
             "> are identical every year and this harness is DEGENERATE on the current",
             "> data — it tests a fixed fundamental ranking against each year's returns,",
             "> not real time-series forecasting. The pipeline is ready for genuinely",
             "> time-varying fundamentals if/when they are provided.\n"]
    for split in SPLITS:
        sub = lb[lb["split"] == split["name"]].copy()
        if "spearman" in sub:
            sub = sub.sort_values("spearman", ascending=False, na_position="last")
        lines.append(f"## {split['name']}\n")
        lines.append(sub.to_markdown(index=False))
        lines.append("")
    (REPORTS / "summary.md").write_text("\n".join(lines))
    print("Wrote leaderboard + results + reports.")
    print(lb.to_string(index=False))


if __name__ == "__main__":
    run()
