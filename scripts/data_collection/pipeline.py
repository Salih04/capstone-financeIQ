"""Shared core for the T -> T+1 modeling-dataset pipeline.

Goal: study whether year-T financial metrics relate to year-(T+1) realized
stock return for BIST companies. Research/educational only, NOT investment
advice.

Honesty rules enforced here:
  * No fabrication, no synthetic data, no fake-zero imputation.
  * The legacy data/trusted/stocks_2020_2025.csv is treated as UNRELIABLE
    reference only. Columns proven to be a frozen snapshot (identical across
    years) are EXCLUDED from features rather than passed off as historical.
  * The only genuinely per-year signal we trust from the reference data is the
    realized annual return (`annual_return_pct`), which drives the targets.
  * Fundamentals that genuinely vary per year are kept as PROVISIONAL features,
    clearly flagged; real historical statements should replace them via the
    manual-ingestion path (data/trusted_raw/).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "trusted_raw"
CLEAN_DIR = REPO_ROOT / "data" / "trusted_clean"
LEGACY_CSV = REPO_ROOT / "data" / "trusted" / "stocks_2020_2025.csv"

FUNDAMENTALS_CSV = CLEAN_DIR / "company_year_fundamentals.csv"
RETURNS_CSV = CLEAN_DIR / "company_year_returns.csv"
BENCHMARK_CSV = CLEAN_DIR / "bist100_benchmark_returns.csv"
BENCHMARK_TEMPLATE = CLEAN_DIR / "bist100_benchmark_returns.template.csv"
MODELING_CSV = CLEAN_DIR / "modeling_dataset_2020_2025.csv"
QUALITY_JSON = CLEAN_DIR / "data_quality_report.json"
QUALITY_MD = CLEAN_DIR / "data_quality_report.md"

# Reference column -> canonical name (subset we may salvage as provisional
# year-T features, plus identity/return). Frozen ones are dropped downstream.
REF_RENAME = {
    "ticker": "ticker",
    "year": "year",
    "indices": "indices",
    "annual_return_pct": "same_year_return_pct",
    # balance sheet / leverage / growth (these genuinely vary per year)
    "total_assets": "total_assets",
    "current_assets": "current_assets",
    "non_current_assets": "non_current_assets",
    "short_term_liabilities": "short_term_liabilities",
    "long_term_liabilities": "long_term_liabilities",
    "equity": "equity",
    "working_capital": "working_capital",
    "net_debt": "net_debt",
    "current_ratio": "current_ratio",
    "leverage_ratio": "leverage_ratio",
    "financial_debt_ratio": "financial_debt_ratio",
    "net_debt_ebitda": "net_debt_to_ebitda",
    "revenue_growth_pct": "revenue_growth_pct",
    "gross_profit_growth_pct": "gross_profit_growth_pct",
    "operating_income_growth_pct": "operating_income_growth_pct",
    "ebitda_growth_pct": "ebitda_growth_pct",
    "net_income_growth_pct": "net_income_growth_pct",
}

IDENTITY_COLS = ("ticker", "company_name", "year", "sector", "indices", "is_bist100")
TARGET_COLS = (
    "next_year_return_pct", "next_year_rank_by_return", "next_year_return_percentile",
    "next_year_top_10pct_returner", "next_year_top_20pct_returner",
    "next_year_bist100_return_pct", "next_year_excess_return_vs_bist100",
    "next_year_outperform_bist100",
)
META_COLS = ("has_target", "target_year", "is_inference_row", "same_year_return_pct")


FINANCIALS_DIR = RAW_DIR / "financials"


@dataclass
class PipelineConfig:
    start_year: int = 2020
    end_year: int = 2025
    tickers: list[str] | None = None
    force_refresh: bool = False
    skip_download: bool = True   # default: no network; manual/reference only
    manual_only: bool = False
    validate_only: bool = False
    manual_financials_dir: Path = FINANCIALS_DIR
    strict_manual_validation: bool = False
    allow_partial_manual_coverage: bool = True
    manual_report: dict = field(default_factory=dict)
    manual_overrides: dict = field(default_factory=dict)
    manual_feature_columns: list = field(default_factory=list)
    log: list[str] = field(default_factory=list)

    def say(self, msg: str) -> None:
        self.log.append(msg)
        print(msg)


# --------------------------------------------------------------------------- #
# Universe + reference ingest
# --------------------------------------------------------------------------- #
def load_reference() -> pd.DataFrame:
    if not LEGACY_CSV.is_file():
        raise FileNotFoundError(
            f"Reference data {LEGACY_CSV} missing. It is the bootstrap source for "
            "the realized-return targets and the company universe."
        )
    df = pd.read_csv(LEGACY_CSV)
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    df["year"] = df["year"].astype(int)
    return df


def classify_variability(df: pd.DataFrame) -> dict[str, list[str]]:
    """Per-ticker: does a column vary across years? (data decides, not a list)."""
    g = df.groupby("ticker")
    varying, frozen = [], []
    skip = {"ticker", "year", "indices", "source_file"}
    for col in df.columns:
        if col in skip:
            continue
        share_varying = float((g[col].nunique(dropna=False) > 1).mean())
        (varying if share_varying >= 0.5 else frozen).append(col)
    return {"varying": sorted(varying), "frozen": sorted(frozen)}


def build_universe(cfg: PipelineConfig) -> pd.DataFrame:
    ref = load_reference()
    uni = ref[["ticker", "indices"]].drop_duplicates("ticker").copy()
    uni["company_name"] = uni["ticker"]      # no real name source; ticker as label
    uni["sector"] = np.nan                    # not reliably present per-year
    uni["is_bist100"] = uni["indices"].fillna("").str.contains("XU100")
    if cfg.tickers:
        wanted = {t.upper() for t in cfg.tickers}
        uni = uni[uni["ticker"].isin(wanted)]
    (RAW_DIR / "company_universe.csv").parent.mkdir(parents=True, exist_ok=True)
    uni.to_csv(RAW_DIR / "company_universe.csv", index=False)
    cfg.say(f"[universe] {len(uni)} tickers (is_bist100={int(uni['is_bist100'].sum())})")
    return uni


# --------------------------------------------------------------------------- #
# Financial features (year T) — provisional, from reference; frozen excluded
# --------------------------------------------------------------------------- #
def build_fundamentals(cfg: PipelineConfig) -> pd.DataFrame:
    ref = load_reference()
    var = classify_variability(ref)
    keep = [c for c in REF_RENAME if c in ref.columns]
    fund = ref[keep].rename(columns=REF_RENAME)

    # Drop reference columns proven frozen (would be snapshot-leakage into past).
    excluded = [REF_RENAME[c] for c in keep
                if c in var["frozen"] and REF_RENAME[c] not in ("ticker", "year", "indices")]
    fund = fund.drop(columns=[c for c in excluded if c in fund.columns], errors="ignore")

    yr = (fund["year"] >= cfg.start_year) & (fund["year"] <= cfg.end_year)
    fund = fund[yr].copy()
    fund.to_csv(FUNDAMENTALS_CSV, index=False)
    feat_cols = [c for c in fund.columns if c not in ("ticker", "year", "indices", "same_year_return_pct")]
    cfg.say(f"[fundamentals] {len(fund)} rows, {len(feat_cols)} provisional features; "
            f"excluded {len(excluded)} frozen-snapshot columns")
    return fund


# --------------------------------------------------------------------------- #
# Returns + T -> T+1 targets (the genuinely real part)
# --------------------------------------------------------------------------- #
def build_returns(cfg: PipelineConfig) -> pd.DataFrame:
    ref = load_reference()
    r = ref[["ticker", "year", "annual_return_pct"]].rename(
        columns={"annual_return_pct": "same_year_return_pct"}
    ).copy()
    r = r.dropna(subset=["same_year_return_pct"])

    # next-year return = this ticker's realized return in (year+1)
    nxt = r.rename(columns={"year": "yp", "same_year_return_pct": "next_year_return_pct"})
    nxt["year"] = nxt["yp"] - 1
    r = r.merge(nxt[["ticker", "year", "next_year_return_pct"]], on=["ticker", "year"], how="left")
    r["target_year"] = r["year"] + 1

    # cross-sectional ranks/percentiles WITHIN the target year (vectorized
    # groupby-transforms; no apply -> no grouping-column FutureWarning).
    grp = r.groupby("target_year")["next_year_return_pct"]
    v = r["next_year_return_pct"]
    r["next_year_rank_by_return"] = grp.rank(ascending=False, method="min")
    r["next_year_return_percentile"] = grp.rank(pct=True) * 100
    r["next_year_top_10pct_returner"] = (r["next_year_return_percentile"] >= 90).where(v.notna())
    r["next_year_top_20pct_returner"] = (r["next_year_return_percentile"] >= 80).where(v.notna())
    r.to_csv(RETURNS_CSV, index=False)
    cov = int(r["next_year_return_pct"].notna().sum())
    cfg.say(f"[returns] {len(r)} rows; next-year target coverage {cov}/{len(r)}")
    return r


# --------------------------------------------------------------------------- #
# BIST100 benchmark — manual CSV only, never fabricated
# --------------------------------------------------------------------------- #
# Benchmark may live in trusted_raw (preferred, user-provided) or trusted_clean.
BENCHMARK_RAW_CSV = RAW_DIR / "bist100_benchmark_returns.csv"
BENCHMARK_RAW_TEMPLATE = RAW_DIR / "bist100_benchmark_returns.template.csv"
_BENCHMARK_TEMPLATE_TEXT = (
    "year,bist100_return_pct\n"
    "# Fill REAL BIST100 yearly total-return % (one row per year). Do not fabricate.\n"
)


def ensure_benchmark_template() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not BENCHMARK_TEMPLATE.exists():
        BENCHMARK_TEMPLATE.write_text(_BENCHMARK_TEMPLATE_TEXT)
    if not BENCHMARK_RAW_TEMPLATE.exists():
        BENCHMARK_RAW_TEMPLATE.write_text(_BENCHMARK_TEMPLATE_TEXT)


def load_benchmark(cfg: PipelineConfig) -> pd.DataFrame | None:
    ensure_benchmark_template()
    path = next((p for p in (BENCHMARK_RAW_CSV, BENCHMARK_CSV) if p.is_file()), None)
    if path is None:
        cfg.say(f"[benchmark] MISSING. Provide {BENCHMARK_RAW_CSV} or {BENCHMARK_CSV} "
                "(year,bist100_return_pct). Excess-return targets skipped.")
        return None
    b = pd.read_csv(path, comment="#")
    b.columns = [c.strip().lower() for c in b.columns]
    if "year" not in b.columns or "bist100_return_pct" not in b.columns:
        cfg.say(f"[benchmark] {path.name}: missing year/bist100_return_pct columns; skipping.")
        return None
    b["bist100_return_pct"] = pd.to_numeric(b["bist100_return_pct"], errors="coerce")
    b = b.dropna(subset=["year", "bist100_return_pct"])
    b["year"] = b["year"].astype(int)
    if b.duplicated("year").any():
        cfg.say(f"[benchmark] {path.name}: duplicate year rows; keeping last.")
        b = b.drop_duplicates("year", keep="last")
    cfg.say(f"[benchmark] loaded {len(b)} years from {path.name}: {sorted(b['year'].tolist())}")
    return b[["year", "bist100_return_pct"]]


# --------------------------------------------------------------------------- #
# Manual real financial-history merge
# --------------------------------------------------------------------------- #
def _manual_col_status(df: pd.DataFrame, col: str,
                       min_nonnull: int = 2, min_varying_frac: float = 0.5) -> str:
    """Sparse-aware acceptance status for an added manual column.

    Returns "varying" (accept), or a rejection reason:
      * all_null              — no non-null values at all
      * insufficient_history  — too few non-null values, or no ticker has >=2
                                non-null years (cannot prove it varies over time)
      * frozen_across_years   — tickers WITH multi-year history repeat one value
    Nulls are ignored throughout, so a legitimately sparse-but-varying column
    (e.g. free-derived valuation) is accepted; a repeated snapshot is rejected.
    """
    s = pd.to_numeric(df[col], errors="coerce")
    nonnull = s.notna()
    if not nonnull.any():
        return "all_null"
    if int(nonnull.sum()) < min_nonnull:
        return "insufficient_history"
    sub = df.loc[nonnull, ["ticker"]].assign(_v=s[nonnull])
    per_ticker_unique = sub.groupby("ticker")["_v"].nunique()
    multi = per_ticker_unique[sub.groupby("ticker")["_v"].size() >= 2]
    if len(multi) == 0:
        # every ticker has at most one non-null year -> cannot show time variation
        return "insufficient_history"
    varying_frac = float((multi > 1).mean())
    return "varying" if varying_frac >= min_varying_frac else "frozen_across_years"


def merge_manual_financials(cfg: PipelineConfig, df: pd.DataFrame, base_features: set[str]) -> pd.DataFrame:
    """Merge real per-year history from data/trusted_raw/financials/ if present.

    Overrides matching base columns where supplied; adds new columns otherwise.
    A manual column becomes a valid feature only if it genuinely varies across
    years and is not all-null. Frozen snapshot values are never used to fill the
    years a user did not supply.
    """
    from scripts.data_collection import manual_ingest as M

    known = set(df["ticker"].unique())
    man, rep = M.load_manual(
        cfg.manual_financials_dir, known_tickers=known,
        strict=cfg.strict_manual_validation, allow_partial=cfg.allow_partial_manual_coverage,
    )
    if cfg.strict_manual_validation and rep.issues:
        for i in rep.issues:
            cfg.say(f"[manual] STRICT issue: {i}")
        raise SystemExit("Strict manual validation failed; aborting.")

    if man is None or not rep.present:
        rep.issues.append("manual financial history missing (data/trusted_raw/financials/ empty)")
        cfg.manual_report = rep.as_dict()
        cfg.say("[manual] no manual financial history found; using reference-only features.")
        return df

    man_cols = [c for c in man.columns if c not in ("ticker", "year")]
    df = df.merge(man, on=["ticker", "year"], how="left", suffixes=("", "_manual"))

    overrides: dict[str, int] = {}
    added: list[str] = []
    for c in man_cols:
        target = M.OVERRIDE_MAP.get(c)
        if target and target in df.columns:
            # When manual col name == base col name, pandas suffixed the manual
            # side to "<c>_manual"; otherwise it is just <c>.
            src = f"{c}_manual" if f"{c}_manual" in df.columns else c
            mask = df[src].notna()
            overrides[target] = int(mask.sum())
            df.loc[mask, target] = df.loc[mask, src]
            if src != target:
                df = df.drop(columns=[src])
        else:
            added.append(c)  # new column, already merged in

    # Accept added manual columns using a SPARSE-AWARE frozen check. A manual
    # column (e.g. free-derived valuation) may be legitimately sparse: only some
    # tickers/years have a value. It must NOT be rejected as "frozen" merely
    # because many ticker-years are missing. Evaluate variation ONLY among tickers
    # that actually have >=2 non-null years; reject only if those genuinely repeat
    # the same value (truly frozen) or there is too little history to validate.
    accepted, rejected = [], {}
    for c in added:
        status = _manual_col_status(df, c)
        if status == "varying":
            accepted.append(c)
        else:
            rejected[c] = status
            df = df.drop(columns=[c])

    cfg.manual_overrides = overrides
    cfg.manual_feature_columns = accepted
    rep.issues = rep.issues  # keep
    d = rep.as_dict()
    d["overrides_from_snapshot"] = overrides
    d["accepted_feature_columns"] = accepted
    d["rejected_feature_columns"] = rejected
    cfg.manual_report = d
    cfg.say(f"[manual] ingested {rep.rows_ingested} rows from {len(rep.files)} file(s); "
            f"overrides={list(overrides)} accepted_features={accepted} rejected={rejected}")
    return df


# --------------------------------------------------------------------------- #
# Assemble modeling dataset
# --------------------------------------------------------------------------- #
def build_modeling_dataset(cfg: PipelineConfig) -> pd.DataFrame:
    uni = build_universe(cfg)
    fund = build_fundamentals(cfg)
    ret = build_returns(cfg)
    bench = load_benchmark(cfg)

    df = fund.merge(ret, on=["ticker", "year"], how="left", suffixes=("", "_ret"))
    if "same_year_return_pct_ret" in df.columns:
        df["same_year_return_pct"] = df["same_year_return_pct"].fillna(df.pop("same_year_return_pct_ret"))
    df = df.merge(uni.drop(columns=["indices"]), on="ticker", how="left")

    # benchmark-relative targets (target year = year+1)
    if bench is not None:
        bn = bench.rename(columns={"year": "target_year", "bist100_return_pct": "next_year_bist100_return_pct"})
        df = df.merge(bn, on="target_year", how="left")
        df["next_year_excess_return_vs_bist100"] = (
            df["next_year_return_pct"] - df["next_year_bist100_return_pct"]
        )
        df["next_year_outperform_bist100"] = (
            df["next_year_excess_return_vs_bist100"] > 0
        ).where(df["next_year_excess_return_vs_bist100"].notna())
    else:
        for c in ("next_year_bist100_return_pct", "next_year_excess_return_vs_bist100",
                  "next_year_outperform_bist100"):
            df[c] = np.nan

    # Merge real manual financial history (if any) and accept varying columns.
    base_features = set(feature_columns(df))
    df = merge_manual_financials(cfg, df, base_features)

    df["has_target"] = df["next_year_return_pct"].notna()
    df["is_inference_row"] = ~df["has_target"]

    # column order: identity, features, targets, meta
    feat_cols = [c for c in df.columns if c not in
                 set(IDENTITY_COLS) | set(TARGET_COLS) | set(META_COLS) | {"indices"}]
    ordered = (
        [c for c in ("ticker", "company_name", "year", "sector", "indices", "is_bist100") if c in df.columns]
        + sorted(feat_cols)
        + [c for c in TARGET_COLS if c in df.columns]
        + [c for c in ("same_year_return_pct", "target_year", "has_target", "is_inference_row") if c in df.columns]
    )
    df = df[ordered].sort_values(["year", "ticker"]).reset_index(drop=True)
    df.to_csv(MODELING_CSV, index=False)
    cfg.say(f"[modeling] {len(df)} rows -> {MODELING_CSV.name} "
            f"(with target: {int(df['has_target'].sum())}, inference-only: {int(df['is_inference_row'].sum())})")
    return df


def feature_columns(df: pd.DataFrame) -> list[str]:
    excl = set(IDENTITY_COLS) | set(TARGET_COLS) | set(META_COLS) | {"indices", "target_year"}
    return [c for c in df.columns if c not in excl]
