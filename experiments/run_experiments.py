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

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.research import data, feature_registry as reg, scoring  # noqa: E402

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor  # noqa: E402
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge  # noqa: E402

DEFAULT_OUTPUT_ROOT = ROOT / "experiments"
OUTPUT_ROOT = DEFAULT_OUTPUT_ROOT
RESULTS = OUTPUT_ROOT / "results"
REPORTS = OUTPUT_ROOT / "reports"
LEADERBOARD = OUTPUT_ROOT / "leaderboard.csv"

PRED_FEATURES = [f for f in reg.features_for_next_year_prediction()]


CLEAN_MODELING = ROOT / "data" / "trusted_clean" / "modeling_dataset_2020_2025.csv"
TRAINING_MODELING = ROOT / "data" / "trusted_clean" / "modeling_dataset_training_2020_2025.csv"
PUBLIC_MODELING = ROOT / "data" / "trusted_clean" / "modeling_dataset_public_2020_2025.csv"

MODEL_CONFIGS = {
    "baseline_equal_weight": {"kind": "baseline", "parameters": {}, "seed": None},
    "baseline_rank_score": {"kind": "baseline", "parameters": {}, "seed": None},
    "robust_rank_aggregation": {"kind": "baseline", "parameters": {}, "seed": None},
    "linear_regression": {"kind": "ml", "parameters": {}, "seed": None},
    "ridge": {"kind": "ml", "parameters": {"alpha": 1.0}, "seed": None},
    "lasso": {"kind": "ml", "parameters": {"alpha": 0.1, "max_iter": 5000}, "seed": None},
    "elasticnet": {"kind": "ml", "parameters": {"alpha": 0.1, "max_iter": 5000}, "seed": None},
    "random_forest": {
        "kind": "ml",
        "parameters": {"n_estimators": 200, "max_depth": 4},
        "seed": 42,
    },
    "gradient_boosting": {
        "kind": "ml",
        "parameters": {"max_depth": 2, "n_estimators": 120},
        "seed": 42,
    },
}


def _configure_output_root(output_root: Path | None) -> None:
    """Point generated artifacts at the default tree or an isolated rerun tree."""
    global OUTPUT_ROOT, RESULTS, REPORTS, LEADERBOARD
    OUTPUT_ROOT = (output_root or DEFAULT_OUTPUT_ROOT).resolve()
    RESULTS = OUTPUT_ROOT / "results"
    REPORTS = OUTPUT_ROOT / "reports"
    LEADERBOARD = OUTPUT_ROOT / "leaderboard.csv"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_record(path: Path, *, base: Path = ROOT, role: str | None = None) -> dict:
    record = {
        "path": path.resolve().relative_to(base.resolve()).as_posix(),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }
    if role is not None:
        record["role"] = role
    return record


def _git_metadata() -> dict:
    def _git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
        )
        return result.stdout.strip()

    try:
        sha = _git("rev-parse", "HEAD")
        dirty = bool(_git("status", "--porcelain", "--untracked-files=normal"))
    except (OSError, subprocess.CalledProcessError):
        return {"sha": None, "short_sha": "nogit", "dirty": None}
    return {"sha": sha, "short_sha": sha[:8], "dirty": dirty}


def _package_versions() -> dict[str, str]:
    return {
        package: importlib.metadata.version(package)
        for package in ("numpy", "pandas", "scikit-learn")
    }


def _generated_artifacts() -> list[Path]:
    candidates = [
        LEADERBOARD,
        REPORTS / "summary.md",
        RESULTS / "coverage_impact.csv",
        RESULTS / "experiment_summary.md",
        RESULTS / "feature_coverage.csv",
        RESULTS / "feature_stability_by_split.csv",
        RESULTS / "feature_stability_summary.csv",
        RESULTS / "leaderboard.csv",
        RESULTS / "leaderboard_by_target.csv",
        RESULTS / "research_agent_model_outputs.csv",
        *(RESULTS / f"predictions_{split['name']}.csv" for split in SPLITS),
        *(RESULTS / f"{split['name']}.json" for split in SPLITS),
    ]
    return [path for path in candidates if path.is_file()]


def _write_manifest(
    outputs: list[Path],
    feat_cols: list[str],
    leaderboard: pd.DataFrame,
    started_at: datetime,
    elapsed_seconds: float,
) -> Path:
    """Register exact run inputs and outputs without certifying methodology."""
    git = _git_metadata()
    completed_at = datetime.now(timezone.utc)
    timestamp = completed_at.strftime("%Y%m%dT%H%M%S.%fZ")
    run_id = f"{timestamp}_{git['short_sha']}"
    manifest_path = RESULTS / "runs" / run_id / "manifest.json"

    input_candidates = [
        (CLEAN_MODELING, "canonical modeling dataset required by the project contract"),
        (_modeling_csv(), "actual experiment dataset"),
        (PUBLIC_MODELING, "public-universe model-output input"),
        (ROOT / "data" / "trusted_clean" / "data_quality_report.json", "data-quality report input"),
    ]
    seen_inputs: set[Path] = set()
    inputs = []
    for path, role in input_candidates:
        resolved = path.resolve()
        if path.is_file() and resolved not in seen_inputs:
            inputs.append(_file_record(path, role=role))
            seen_inputs.add(resolved)

    config_files = [
        ROOT / "experiments" / "run_experiments.py",
        ROOT / "backend" / "app" / "services" / "research" / "feature_registry.py",
        ROOT / "Makefile",
    ]
    artifact_records = [
        _file_record(path, base=OUTPUT_ROOT) for path in sorted(outputs)
    ]
    relative_manifest = manifest_path.relative_to(ROOT) if manifest_path.is_relative_to(ROOT) else manifest_path
    semantic_leaderboard = json.loads(leaderboard.to_json(orient="split"))
    manifest = {
        "schema_version": 1,
        "statement": "Records inputs and artifacts; does not certify methodology or predictive validity.",
        "run": {
            "id": run_id,
            "started_at_utc": started_at.isoformat(),
            "completed_at_utc": completed_at.isoformat(),
            "wall_clock_seconds": round(elapsed_seconds, 6),
            "command": "PYTHONPATH=. python experiments/run_experiments.py",
            "reproduce_command": f"python scripts/verify_run.py {relative_manifest}",
        },
        "git": git,
        "python": {
            "version": platform.python_version(),
            "full_version": sys.version,
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "description": platform.platform(),
        },
        "packages": _package_versions(),
        "inputs": inputs,
        "features": feat_cols,
        "configuration": {
            "targets": TARGETS,
            "splits": SPLITS,
            "models": MODEL_CONFIGS,
            "seeds": {
                name: config["seed"]
                for name, config in MODEL_CONFIGS.items()
                if config["seed"] is not None
            },
            "files": [_file_record(path) for path in config_files],
        },
        "artifacts": artifact_records,
        "semantic_outputs": {"leaderboard": semantic_leaderboard},
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=False)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest_path


def _modeling_csv() -> Path:
    """Return training dataset path if available, else fall back to standard path."""
    return TRAINING_MODELING if TRAINING_MODELING.is_file() else CLEAN_MODELING


def build_panel() -> pd.DataFrame:
    """One row per (ticker, feature_year) with the NEXT year's return as target.

    Prefer the training dataset (may have a larger universe) when available,
    then fall back to the standard modeling dataset, then the legacy panel.
    Training dataset is used so experiments can benefit from a broader universe;
    inference/frontend endpoints use the public-only dataset separately.
    """
    modeling_path = _modeling_csv()
    if modeling_path.is_file():
        m = pd.read_csv(modeling_path)
        _non_feat = {
            "ticker", "company_name", "year", "sector", "indices", "is_bist100",
            "same_year_return_pct", "target_year", "has_target", "is_inference_row",
            "is_public_universe", "is_training_universe", "universe_source",
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
           "same_year_return_pct", "target_year", "has_target", "is_inference_row",
           "is_public_universe", "is_training_universe", "universe_source"}
    return [c for c in m.columns if c not in non and not c.startswith("next_year_")]


def build_panel_for_target(target_col: str):
    """(panel, feat_cols) with the given next_year_* column as target. None if absent."""
    modeling_path = _modeling_csv()
    if not modeling_path.is_file():
        return None, []
    m = pd.read_csv(modeling_path)
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
    modeling_path = PUBLIC_MODELING if PUBLIC_MODELING.is_file() else CLEAN_MODELING
    if not modeling_path.is_file():
        return
    m = pd.read_csv(modeling_path)
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


def _score_robust_rank_aggregation(Xtr, ytr, Xte):
    return np.nanmedian(Xte, axis=1)


def _fit_sklearn(model, Xtr, ytr, Xte):
    Xtr2 = np.nan_to_num(Xtr, nan=0.5)  # rank-imputed center for ML only
    Xte2 = np.nan_to_num(Xte, nan=0.5)
    model.fit(Xtr2, ytr)
    return model.predict(Xte2)


MODELS = {
    "baseline_equal_weight": ("baseline", _score_equal_weight),
    "baseline_rank_score": ("baseline", _score_rank),
    "robust_rank_aggregation": ("baseline", _score_robust_rank_aggregation),
    "linear_regression": ("ml", lambda a, b, c: _fit_sklearn(LinearRegression(), a, b, c)),
    "ridge": ("ml", lambda a, b, c: _fit_sklearn(Ridge(alpha=1.0), a, b, c)),
    "lasso": ("ml", lambda a, b, c: _fit_sklearn(Lasso(alpha=0.1, max_iter=5000), a, b, c)),
    "elasticnet": ("ml", lambda a, b, c: _fit_sklearn(ElasticNet(alpha=0.1, max_iter=5000), a, b, c)),
    "random_forest": ("ml", lambda a, b, c: _fit_sklearn(
        RandomForestRegressor(n_estimators=200, max_depth=4, random_state=42), a, b, c)),
    "gradient_boosting": ("ml", lambda a, b, c: _fit_sklearn(
        GradientBoostingRegressor(random_state=42, max_depth=2, n_estimators=120), a, b, c)),
}

SPLITS = [
    {"name": "test_2023", "train_target_years": [2021, 2022], "test_feature_year": 2022},
    {"name": "test_2024", "train_target_years": [2021, 2022, 2023], "test_feature_year": 2023},
    {"name": "test_2025", "train_target_years": [2021, 2022, 2023, 2024], "test_feature_year": 2024},
]


def _write_feature_reports(panel: pd.DataFrame, feat_cols: list[str]) -> None:
    coverage_rows = []
    for c in feat_cols:
        s = panel[c]
        coverage_rows.append({
            "feature": c,
            "nonnull_rows": int(s.notna().sum()),
            "nonnull_rate": round(float(s.notna().mean()), 4),
            "years_with_data": int(panel.loc[s.notna(), "feature_year"].nunique()),
            "tickers_with_data": int(panel.loc[s.notna(), "ticker"].nunique()),
        })
    pd.DataFrame(coverage_rows).sort_values(
        ["nonnull_rate", "feature"], ascending=[False, True]
    ).to_csv(RESULTS / "feature_coverage.csv", index=False)

    stability_rows = []
    for split in SPLITS:
        tr = panel[(panel["feature_year"] + 1).isin(split["train_target_years"])]
        y = tr["target_return"]
        for c in feat_cols:
            x = tr[c]
            ok = x.notna() & y.notna()
            corr = pd.Series(x[ok]).corr(pd.Series(y[ok]), method="spearman") if int(ok.sum()) >= 5 else np.nan
            stability_rows.append({
                "split": split["name"],
                "feature": c,
                "train_rows": int(ok.sum()),
                "abs_spearman_to_target": None if pd.isna(corr) else round(abs(float(corr)), 4),
                "spearman_to_target": None if pd.isna(corr) else round(float(corr), 4),
            })
    st = pd.DataFrame(stability_rows)
    st.to_csv(RESULTS / "feature_stability_by_split.csv", index=False)
    if len(st):
        agg = (st.dropna(subset=["abs_spearman_to_target"])
                 .groupby("feature", as_index=False)
                 .agg(mean_abs_spearman=("abs_spearman_to_target", "mean"),
                      std_abs_spearman=("abs_spearman_to_target", "std"),
                      splits_observed=("abs_spearman_to_target", "count")))
        agg["mean_abs_spearman"] = agg["mean_abs_spearman"].round(4)
        agg["std_abs_spearman"] = agg["std_abs_spearman"].fillna(0).round(4)
        agg.sort_values(["mean_abs_spearman", "splits_observed"], ascending=[False, False]).to_csv(
            RESULTS / "feature_stability_summary.csv", index=False
        )

    tmp = panel[["target_return", *feat_cols]].copy()
    tmp["coverage_fraction"] = tmp[feat_cols].notna().mean(axis=1)
    tmp["coverage_bucket"] = pd.cut(
        tmp["coverage_fraction"],
        bins=[-0.01, 0.5, 0.8, 1.0],
        labels=["low", "medium", "high"],
    )
    cov = (tmp.dropna(subset=["target_return"])
             .groupby("coverage_bucket", observed=False)["target_return"]
             .agg(["count", "mean", "median"])
             .reset_index())
    cov.rename(columns={"mean": "mean_next_year_return_pct",
                        "median": "median_next_year_return_pct"}, inplace=True)
    cov.to_csv(RESULTS / "coverage_impact.csv", index=False)


def _markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    d = df.copy()
    d = d.where(pd.notna(d), "")
    cols = [str(c) for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |",
             "| " + " | ".join("---" for _ in cols) + " |"]
    for _, row in d.iterrows():
        vals = [str(row[c]).replace("|", "\\|") for c in d.columns]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _data_caveat(feature_data: pd.DataFrame, feat_cols: list[str], frozen_excluded: int) -> list[str]:
    """Build the report caveat from observed within-ticker cross-year variance."""
    varying_features = []
    for c in feat_cols:
        cross_year_variance = feature_data.groupby("ticker")[c].var(ddof=0).dropna()
        if (cross_year_variance > 0).any():
            varying_features.append(c)

    if varying_features:
        return [
            "> ⚠️ DATA CAVEAT: corrected features vary by year: "
            f"{len(varying_features)} of {len(feat_cols)} predictor features show verified",
            "> within-ticker cross-year variance; "
            f"{frozen_excluded} frozen reference columns are excluded. The dataset remains",
            "> small and sparse, so this does not establish reliable predictive signal."
        ]

    return [
        "> ⚠️ DATA CAVEAT: verified current predictor features have no within-ticker",
        "> cross-year variance. This harness is DEGENERATE on the current data — it",
        "> tests a fixed feature ranking against each year's returns, not real time-series",
        "> forecasting. The pipeline requires genuinely time-varying features."
    ]


def _feature_variance_caveat(panel: pd.DataFrame, feat_cols: list[str]) -> list[str]:
    """Build the variance caveat from the current raw modeling data."""
    frozen_excluded = 0
    quality_report = ROOT / "data" / "trusted_clean" / "data_quality_report.json"
    if quality_report.is_file():
        quality = json.loads(quality_report.read_text())
        frozen_excluded = len(quality.get("frozen_columns_excluded_from_features", []))
    variation_frame = panel
    if _modeling_csv().is_file():
        variation_frame = pd.read_csv(_modeling_csv(), usecols=["ticker", *feat_cols])
    return _data_caveat(variation_frame, feat_cols, frozen_excluded)


def _write_summary_report(lb: pd.DataFrame, panel: pd.DataFrame, feat_cols: list[str]) -> None:
    """Write the honest summary without changing experiment results."""
    lines = ["# Experiment summary (next-year return prediction)\n",
             "Walk-forward, leakage-controlled. Small data (40 stocks/year) — treat",
             "all out-of-sample numbers as noisy and overfitting-prone.\n",
             *_feature_variance_caveat(panel, feat_cols),
             ""]
    for split in SPLITS:
        sub = lb[lb["split"] == split["name"]].copy()
        if "spearman" in sub:
            sub = sub.sort_values("spearman", ascending=False, na_position="last")
        lines.append(f"## {split['name']}\n")
        lines.append(_markdown_table(sub))
        lines.append("")
    (REPORTS / "summary.md").write_text("\n".join(lines))


def run(output_root: Path | None = None) -> Path:
    _configure_output_root(output_root)
    started_at = datetime.now(timezone.utc)
    started_clock = time.perf_counter()
    RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    panel = build_panel()
    feat_cols = [c for c in panel.columns if c not in ("ticker", "feature_year", "target_return")]
    _write_feature_reports(panel, feat_cols)

    # honest feature/sample reporting
    manual_feats = []
    qr = ROOT / "data" / "trusted_clean" / "data_quality_report.json"
    if qr.is_file():
        import json as _json
        manual_feats = (_json.loads(qr.read_text()).get("manual_financials", {}) or {}).get(
            "accepted_feature_columns", []) or []
    used_source = str(_modeling_csv().relative_to(ROOT)) if _modeling_csv().is_file() else "legacy reference panel"
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
        prediction_rows = []
        for name, (kind, fn) in MODELS.items():
            try:
                yp = np.asarray(fn(Xtr, ytr, Xte), dtype=float)
                met = _metrics(yte, yp)
                evaluated = ~np.isnan(yte) & ~np.isnan(yp)
                prediction_rows.extend(
                    {
                        "ticker": ticker,
                        "year": split["test_feature_year"] + 1,
                        "model": name,
                        "y_true": float(actual),
                        "y_pred": float(prediction),
                    }
                    for ticker, actual, prediction in zip(
                        te.loc[evaluated, "ticker"], yte[evaluated], yp[evaluated]
                    )
                )
            except Exception as exc:  # honest failure report, not silent
                met = {"error": str(exc)}
            split_result["models"][name] = {"kind": kind, **met}
            leaderboard_rows.append({"split": split["name"], "model": name, "kind": kind,
                                     **{k: v for k, v in met.items() if k != "n"}})
        (RESULTS / f"{split['name']}.json").write_text(json.dumps(split_result, indent=2))
        pd.DataFrame(
            prediction_rows,
            columns=["ticker", "year", "model", "y_true", "y_pred"],
        ).to_csv(RESULTS / f"predictions_{split['name']}.csv", index=False, float_format="%.17g")

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
          *_feature_variance_caveat(panel, feat_cols),
          "Baselines usually match/beat ML.\n",
          "Additional reports: `feature_coverage.csv`, `feature_stability_summary.csv`, `coverage_impact.csv`.\n",
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

    _write_summary_report(lb, panel, feat_cols)
    manifest_path = _write_manifest(
        _generated_artifacts(), feat_cols, lb, started_at, time.perf_counter() - started_clock
    )
    print("Wrote leaderboard + results + reports.")
    print(f"Registered run manifest: {manifest_path}")
    print(lb.to_string(index=False))
    return manifest_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        help="isolated output root containing leaderboard.csv, results/, and reports/",
    )
    args = parser.parse_args()
    run(args.out)
