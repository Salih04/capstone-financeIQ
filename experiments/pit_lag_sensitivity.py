"""Publication-lag (look-ahead) sensitivity for the T -> T+1 walk-forward.

Finding (docs/audit/PUBLICATION_LAG_AUDIT.md): year-T fundamentals are full
fiscal-year-T statements, published on KAP up to 60/70 days after 31 Dec T
(SPK II-14.1, art. 10), while the target return window starts on the first
trading day of T+1. Statement-derived features are therefore used up to ~10
weeks before an investor could have seen them.

This script re-runs the published walk-forward (same panel construction,
splits, models and metrics, imported from run_experiments.py) under three
feature specifications and writes results to experiments/pit_audit/. It never
touches experiments/results/ or the published leaderboard.

  original        all 40 features as published (must reproduce the leaderboard)
  pit_price_only  only features knowable on the first day of the target window
  pit_lagged_fund statement-derived features taken from fiscal year T-1
                  (published by ~10 March T, >= 9 months before the window)
                  plus the year-T price features
  diag_fy_t_statements  diagnostic, NOT point-in-time: only the unlagged
                  fiscal-year-T statement features, to locate the source of the
                  published baseline IC
  pit_strict      pit_price_only without market_cap and price_adjclose_t,
                  whose levels depend on corporate actions after year T
                  (Yahoo adjclose is back-adjusted; share counts are as-of T)

Run: PYTHONPATH=. python experiments/pit_lag_sensitivity.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
import run_experiments as rx  # noqa: E402

OUT = ROOT / "experiments" / "pit_audit"
SEED = 20261004
N_PERM = 10_000

# Known at the close of year T: prices up to 31 Dec T, the benchmark's year-T
# return, and market capitalisation (year-end price x dated share count).
PIT_SAFE = [
    "price_adjclose_t",
    "price_data_available",
    "price_drawdown_from_3y_high_pct",
    "price_history_years_available",
    "price_momentum_1y_pct",
    "price_momentum_2y_pct",
    "price_vs_bist100_1y_pct",
    "benchmark_same_year_return_pct",
    "market_cap",
]
# Levels built from Yahoo's back-adjusted close: the adjustment factor is set by
# splits, bonus issues and dividends AFTER year T (AEFES 2024: ~10x).
ADJUSTMENT_DEPENDENT = ["price_adjclose_t", "market_cap"]
# Every other feature is computed from fiscal-year-T statements, alone or
# combined with a year-end price (pe_ratio, pb_ratio, ev_ebitda,
# enterprise_value).


PRICES = ROOT / "data" / "trusted_raw" / "prices" / "yahoo_year_end_prices.csv"


def _listed_rows(m: pd.DataFrame) -> pd.Series:
    """True where the ticker has a Yahoo year-end price in or before the feature year.

    Rows before a ticker's first quote carry vendor placeholder returns (e.g.
    five unlisted tickers share 56.947991 as their 2021 'return'), not market
    returns. The published dataset keeps them.
    """
    first = pd.read_csv(PRICES).groupby("ticker")["year"].min()
    return m["year"] >= m["ticker"].map(first)


def _panel(spec: str, exclude_prelisting: bool = False) -> tuple[pd.DataFrame, list[str]]:
    m = pd.read_csv(rx._modeling_csv())
    if exclude_prelisting:
        m = m[_listed_rows(m).fillna(False)].reset_index(drop=True)
    feats = rx._feature_cols(m)
    statement = [c for c in feats if c not in PIT_SAFE]
    if spec == "original":
        cols = feats
        frame = m
    elif spec == "pit_price_only":
        cols = [c for c in feats if c in PIT_SAFE]
        frame = m
    elif spec == "diag_fy_t_statements":
        cols = statement
        frame = m
    elif spec == "pit_strict":
        cols = [c for c in feats if c in PIT_SAFE and c not in ADJUSTMENT_DEPENDENT]
        frame = m
    elif spec == "pit_lagged_fund":
        prev = m[["ticker", "year", *statement]].copy()
        prev["year"] = prev["year"] + 1  # FY T-1 statements attached to feature year T
        frame = m.drop(columns=statement).merge(prev, on=["ticker", "year"], how="left")
        cols = feats
    else:
        raise ValueError(spec)
    out = frame[["ticker", "year", *cols]].copy().rename(columns={"year": "feature_year"})
    for c in cols:
        out[c] = out.groupby("feature_year")[c].rank(pct=True)
    out["target_return"] = pd.to_numeric(frame["next_year_return_pct"], errors="coerce").values
    return out.dropna(subset=["target_return"]).reset_index(drop=True), cols


def _walk_forward(panel: pd.DataFrame, cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, preds = [], []
    for split in rx.SPLITS:
        tr = panel[(panel["feature_year"] + 1).isin(split["train_target_years"])]
        te = panel[panel["feature_year"] == split["test_feature_year"]]
        Xtr, ytr = tr[cols].to_numpy(float), tr["target_return"].to_numpy(float)
        Xte, yte = te[cols].to_numpy(float), te["target_return"].to_numpy(float)
        keep = ~np.isnan(ytr)
        Xtr, ytr = Xtr[keep], ytr[keep]
        for name, (kind, fn) in rx.MODELS.items():
            yp = np.asarray(fn(Xtr, ytr, Xte), dtype=float)
            met = rx._metrics(yte, yp)
            rows.append({"split": split["name"], "model": name, "kind": kind,
                         **{k: v for k, v in met.items() if k != "n"}})
            ok = ~np.isnan(yte) & ~np.isnan(yp)
            preds.append(pd.DataFrame({"split": split["name"], "model": name,
                                       "y_true": yte[ok], "y_pred": yp[ok]}))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True)


def _pooled_ic_test(pred: pd.DataFrame, rng: np.random.Generator) -> dict:
    """Equal-weighted mean of within-year Spearman ICs; within-year permutation."""
    groups = [g for _, g in pred.groupby("split")]
    ranks = [(g["y_pred"].rank().to_numpy(), g["y_true"].rank().to_numpy()) for g in groups]

    def ic(a, b):
        return float(np.corrcoef(a, b)[0, 1])

    observed = float(np.mean([ic(p, t) for p, t in ranks]))
    null = np.empty(N_PERM)
    for i in range(N_PERM):
        null[i] = np.mean([ic(p, rng.permutation(t)) for p, t in ranks])
    p_two = float((np.sum(np.abs(null) >= abs(observed)) + 1) / (N_PERM + 1))
    return {"pooled_ic": round(observed, 3), "perm_p_two_sided": round(p_two, 4)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    published = pd.read_csv(ROOT / "experiments" / "results" / "leaderboard.csv")
    summary = {"seed": SEED, "n_permutations": N_PERM, "pit_safe_features": PIT_SAFE, "specs": {}}
    runs = [(s, False) for s in ("original", "pit_price_only", "pit_strict",
                                  "pit_lagged_fund", "diag_fy_t_statements")]
    runs += [(s, True) for s in ("original", "pit_strict", "pit_lagged_fund",
                                 "diag_fy_t_statements")]
    for spec_name, exclude in runs:
        spec = spec_name
        rng = np.random.default_rng(SEED)
        panel, cols = _panel(spec, exclude_prelisting=exclude)
        if exclude:
            spec = f"{spec_name}__listed_only"
        lb, pred = _walk_forward(panel, cols)
        lb.to_csv(OUT / f"leaderboard_{spec}.csv", index=False)
        if spec == "original":  # the published configuration only
            # Exact for every model except OLS: the rank features are collinear,
            # so the unregularised least-squares solution depends on the BLAS
            # build (observed |delta IC| <= 0.003 with the pinned
            # numpy 1.26.4 / scikit-learn 1.5.1 on macOS).
            merged = lb.merge(published, on=["split", "model"], suffixes=("", "_pub"))
            delta = (merged["spearman"] - merged["spearman_pub"]).abs()
            tol = np.where(merged["model"] == "linear_regression", 0.005, 1e-9)
            if len(merged) != len(published) or (delta > tol).any():
                raise SystemExit("original spec does not reproduce the published leaderboard")
            summary["reproduction_max_abs_delta_ic"] = {
                "linear_regression": round(float(delta[merged["model"] == "linear_regression"].max()), 4),
                "all_other_models": round(float(delta[merged["model"] != "linear_regression"].max()), 4),
            }
        tests = {m: _pooled_ic_test(pred[pred["model"] == m], rng) for m in rx.MODELS}
        summary["specs"][spec] = {"n_features": len(cols), "features": cols, "pooled": tests}
        print(f"\n== {spec} ({len(cols)} features)")
        for m, t in tests.items():
            print(f"  {m:26s} IC={t['pooled_ic']:+.3f}  p={t['perm_p_two_sided']:.4f}")
    (OUT / "pit_lag_sensitivity.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
