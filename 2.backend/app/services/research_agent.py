"""Research-agent service: constrained, LLM-assisted research support.

The structured ML pipeline stays the primary numeric model. This layer only
READS validated structured evidence and produces cautious, bounded research
support: deterministic summaries + scores always, optional LLM commentary when
a provider is configured. It never predicts prices/returns, never gives
buy/sell/hold, never fabricates facts, and never writes back into any dataset.

Composite (weights configurable via env):
    final_research_score = w_ml*ml_score + w_conf*confidence_score + w_llm*llm_research_score
Components are always returned separately and never hidden.
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd

def _resolve_repo_root() -> Path:
    """Find the dir that actually holds data/trusted_clean.

    Works in the repo (parents[3]) and in Docker (WORKDIR /app with data mounted),
    and honours an explicit RESEARCH_REPO_ROOT override.
    """
    candidates = []
    env = os.environ.get("RESEARCH_REPO_ROOT")
    if env:
        candidates.append(Path(env))
    candidates += [Path(__file__).resolve().parents[3], Path("/app"), Path.cwd()]
    for c in candidates:
        if (c / "data" / "trusted_clean").is_dir():
            return c
    return Path(__file__).resolve().parents[3]


REPO_ROOT = _resolve_repo_root()
CLEAN = REPO_ROOT / "data" / "trusted_clean"
MODELING_CSV = CLEAN / "modeling_dataset_2020_2025.csv"
PUBLIC_MODELING_CSV = CLEAN / "modeling_dataset_public_2020_2025.csv"
COMPANY_CONTEXTS_DIR = CLEAN / "company_contexts"
QUALITY_JSON = CLEAN / "data_quality_report.json"
MIGRATION_JSON = CLEAN / "yearly_snapshot_migration_report.json"
LEADERBOARD = REPO_ROOT / "experiments" / "leaderboard.csv"
RESULTS_DIR = REPO_ROOT / "experiments" / "results"
MODEL_OUTPUTS = RESULTS_DIR / "research_agent_model_outputs.csv"
LEADERBOARD_BY_TARGET = RESULTS_DIR / "leaderboard_by_target.csv"
BENCHMARK_CSV = REPO_ROOT / "data" / "trusted_raw" / "bist100_benchmark_returns.csv"
BENCHMARK_CSV_ALT = CLEAN / "bist100_benchmark_returns.csv"
BENCHMARK_REPORT = CLEAN / "bist100_benchmark_report.json"
FROZEN_EVIDENCE = CLEAN / "frozen_column_evidence.json"
QUARTERLY_INSPECTION = CLEAN / "quarterly_snapshot_inspection.json"
CORRECTED_YEARLY_REPORT = CLEAN / "corrected_yearly_ingestion_report.json"
FREE_VALUATION_REPORT = CLEAN / "free_valuation_history_report.json"


def _public_modeling_csv() -> Path:
    """Return the public-universe modeling dataset path, falling back to the standard one."""
    return PUBLIC_MODELING_CSV if PUBLIC_MODELING_CSV.is_file() else MODELING_CSV


def load_company_context_json(ticker: str, year: int | None = None) -> dict | None:
    """Load pre-built structured context JSON for a ticker/year from company_contexts/.

    Returns None if not found. Callers should fall back to build_company_context().
    year=None → use the latest available year for the ticker.
    """
    if not COMPANY_CONTEXTS_DIR.is_dir():
        return None
    t = str(ticker).strip().upper()
    if year is not None:
        p = COMPANY_CONTEXTS_DIR / f"{t}_{year}.json"
        try:
            return json.loads(p.read_text()) if p.is_file() else None
        except Exception:
            return None
    # Find latest year
    candidates = sorted(COMPANY_CONTEXTS_DIR.glob(f"{t}_*.json"))
    if not candidates:
        return None
    try:
        return json.loads(candidates[-1].read_text())
    except Exception:
        return None

NOT_ADVICE = ("This is a research-support score, NOT investment advice. The LLM is a "
              "decision-support layer, not the numerical predictor.")

# Source distinction (corrected yearly files vs old frozen snapshot) — PHASE 5/7.
FEATURE_COUNT_BEFORE_CORRECTED = 17
ACCEPTED_CORRECTED_YEARLY = ["revenue", "gross_profit", "operating_income", "ebitda", "net_income",
                             "gross_margin", "ebitda_margin", "net_margin", "roe", "roa"]
STILL_MISSING_VALUATION = ["pe", "pb", "ev_ebitda", "market_capitalization",
                           "enterprise_value", "ev_sales", "peg_ratio"]
OLD_SNAPSHOT_REJECTED_NOW_CORRECTED = ["revenue", "ebitda", "net_income", "roe", "roa"]
LEAKAGE_FIELDS_REJECTED = ["price", "period_return", "day_return", "volume", "return_1w", "return_1m",
                           "return_3m", "return_6m", "return_ytd", "return_1y", "return_3y", "return_5y"]

# --------------------------------------------------------------------------- #
# config
# --------------------------------------------------------------------------- #
def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def get_config() -> dict:
    provider = os.environ.get("RESEARCH_LLM_PROVIDER", "none").lower()
    if provider in {"openrouter", "openai"}:
        default_base = "https://openrouter.ai/api/v1/chat/completions"
    elif provider == "lmstudio":
        default_base = "http://localhost:1234/v1/chat/completions"
    elif provider == "ollama":
        default_base = "http://localhost:11434/api/chat"
    else:
        default_base = ""
    base = os.environ.get("RESEARCH_LLM_BASE_URL") or default_base
    w_ml = _env_float("RESEARCH_SCORE_ML_WEIGHT", 0.65)
    w_conf = _env_float("RESEARCH_SCORE_CONFIDENCE_WEIGHT", 0.20)
    w_llm = _env_float("RESEARCH_SCORE_LLM_WEIGHT", 0.15)
    default_model = (
        "openai/gpt-oss-120b:free"
        if provider in {"openrouter", "openai"}
        else "local-model"
    )
    return {
        "provider": provider, "base_url": base,
        "model": os.environ.get("RESEARCH_LLM_MODEL", default_model),
        "timeout": _env_float("RESEARCH_LLM_TIMEOUT_SECONDS", 15.0),
        "max_tokens": int(_env_float("RESEARCH_LLM_MAX_TOKENS", 700)),
        "api_key": os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY"),
        "http_referer": os.environ.get("OPENROUTER_HTTP_REFERER", "http://localhost:3000"),
        "app_title": os.environ.get("OPENROUTER_APP_TITLE", "FinanceIQ"),
        "weights": {"ml": w_ml, "confidence": w_conf, "llm": w_llm},
    }


SYSTEM_PROMPT = """You are a financial research assistant for an academic BIST (Borsa Istanbul) research project.

You explain structured company data produced by a quantitative pipeline. You are a decision-support layer only.

OUTPUT FORMAT (MANDATORY):
- Return ONLY a single valid JSON object. No markdown, no code fences, no prose before or after.
- Every key MUST be wrapped in double quotes. Every string value MUST be wrapped in double quotes.
- No trailing commas. No comments. No extra keys.
- The object MUST have exactly these keys:
  {"llm_research_score": 0.0, "llm_confidence": "low",
   "summary": "...", "reasoning": "...", "positive_signals": [],
   "negative_signals": [], "warnings": [], "limitations": []}
- llm_research_score is a number in [0,1]. llm_confidence is exactly one of "low", "medium", "high".

STRICT CONTENT RULES:
- Use ONLY the structured JSON context provided in the user message. Do not use outside knowledge.
- Do NOT invent, estimate, or fill in any financial number, price, ratio, year, or return that is null or absent in the context.
  If a field is null or missing, say it is missing — do not guess or average.
- Do NOT provide investment advice. Never output the words: buy, sell, hold, al, sat, tut, target price, expected return.
- Do NOT guarantee any future price movement or return.
- The structured ML pipeline is the primary numerical predictor. Your llm_research_score is ONLY a bounded
  research-support signal in [0,1] reflecting how well the supplied evidence supports the company/answer.
  Use 0 only when the context gives you nothing to assess.

STRUCTURED CONTEXT INTERPRETATION:
- "model.ml_score": quantitative rank-based score from the ML pipeline. Explain its relative rank if ml_rank is available.
- "financials.*": real per-year income/balance-sheet data. If null, state it is missing.
- "valuation.*": market_cap/P-E/P-B/EV/EV-EBITDA reconstructed from Yahoo year-end price × shares. If null, state it is missing.
- "benchmarks.training_universe_percentiles": where this company ranks on each metric within its peer group for the year.
  Use these percentiles to explain relative strength or weakness.
- "benchmarks.year_medians": median values for the peer group. Use for comparison.
- "data_quality.missing_fields": list these explicitly in your limitations.
- "data_quality.warnings": always surface these.
- "guardrails": always respected — research support only, not investment advice.

ALWAYS SURFACE THESE LIMITATIONS:
- Small sample size (~40 BIST stocks/year).
- Walk-forward Spearman near zero — no reliable predictive edge has been found.
- Valuation features may be from a frozen snapshot for some years.
- Any null/missing fields from data_quality.missing_fields.
- If benchmark_available=false, note benchmark data is unavailable.
- If benchmark_available=true, use the exact years and values given; never say benchmark is missing.
- If context includes "grounded_answer", treat it as the verified factual baseline — keep its facts and expand.

RESPONSE GUIDANCE:
- "summary": 2-4 plain-English sentences covering score drivers, key financial/valuation highlights, and data quality.
- "reasoning": cite specific metrics and years from the context. Mention percentile rankings if available.
- "positive_signals": list of factual strengths from the context data (no advice).
- "negative_signals": list of factual weaknesses or missing data points.
- "warnings": data quality issues, model limitations, missing fields.
- "limitations": always include the small-sample and weak-backtest disclaimers.
- This output is research support, NOT investment advice.
Output JSON only."""


# --------------------------------------------------------------------------- #
# state loading
# --------------------------------------------------------------------------- #
def _load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text()) if p.is_file() else {}
    except Exception:
        return {}


def load_research_state() -> dict:
    pub_csv = _public_modeling_csv()
    state: dict[str, Any] = {
        "modeling_available": pub_csv.is_file(),
        "quality": _load_json(QUALITY_JSON),
        "migration": _load_json(MIGRATION_JSON),
        "leaderboard": None,
        "modeling": None,
        "model_outputs": None,
    }
    if pub_csv.is_file():
        state["modeling"] = pd.read_csv(pub_csv)
    if LEADERBOARD.is_file():
        try:
            state["leaderboard"] = pd.read_csv(LEADERBOARD)
        except Exception:
            state["leaderboard"] = None
    if MODEL_OUTPUTS.is_file():
        try:
            mo = pd.read_csv(MODEL_OUTPUTS)
            mo["ticker"] = mo["ticker"].astype(str).str.upper()
            state["model_outputs"] = mo
        except Exception:
            state["model_outputs"] = None
    return state


def _feature_groups(quality: dict) -> dict:
    feats = quality.get("feature_columns", [])
    groups = {"balance_sheet": [], "growth": [], "other": []}
    for f in feats:
        if f.endswith("growth_pct"):
            groups["growth"].append(f)
        elif any(k in f for k in ("asset", "liabilit", "equity", "debt", "ratio", "working_capital")):
            groups["balance_sheet"].append(f)
        else:
            groups["other"].append(f)
    return groups


# --------------------------------------------------------------------------- #
# contexts (compact — never the raw dataset)
# --------------------------------------------------------------------------- #
def build_summary_context(state: dict | None = None) -> dict:
    state = state or load_research_state()
    q = state["quality"]
    man = q.get("manual_financials", {}) or {}
    # Use the LIVE benchmark file as truth (the quality report can be stale if it
    # was generated before the benchmark was collected).
    live_bench = benchmark_payload()
    return {
        "dataset_available": state["modeling_available"],
        "rows": q.get("rows"),
        "rows_with_target": q.get("rows_with_target"),
        "inference_only_rows": q.get("inference_only_rows"),
        "feature_count": q.get("n_features"),
        "feature_groups": _feature_groups(q),
        "rejected_frozen_columns": q.get("frozen_columns_excluded_from_features", []),
        "manual_accepted_features": man.get("accepted_feature_columns", []),
        "benchmark_available": live_bench["available"],
        "benchmark_source": live_bench["source"],
        "benchmark_years": live_bench["years_covered"],
        "benchmark_returns": live_bench["returns_by_year"],
        "enabled_benchmark_targets": (live_bench["derived_targets"] if live_bench["available"] else []),
        "corrected_yearly_financials": corrected_yearly_payload(),
        "feature_count_before_corrected_yearly": FEATURE_COUNT_BEFORE_CORRECTED,
        "feature_count_after_corrected_yearly": q.get("n_features"),
        "accepted_corrected_yearly_features": ACCEPTED_CORRECTED_YEARLY,
        "still_missing_valuation_features": STILL_MISSING_VALUATION,
        "old_snapshot_rejected_but_corrected_accepted": OLD_SNAPSHOT_REJECTED_NOW_CORRECTED,
        "model_signal_after_corrected_yearly": "still weak/unstable",
        "free_valuation": free_valuation_payload(),
        "valid_for_modeling": q.get("valid_for_T_to_T1_modeling"),
    }


def corrected_yearly_payload() -> dict:
    """Status of the corrected-yearly income/profitability ingestion (if present)."""
    if not CORRECTED_YEARLY_REPORT.is_file():
        return {"available": False}
    j = _load_json(CORRECTED_YEARLY_REPORT)
    return {
        "available": bool(j),
        "accepted_columns": sorted((j.get("accepted_columns") or {}).keys()),
        "frozen_valuation_columns": sorted((j.get("frozen_valuation_columns") or {}).keys()),
        "misalignment_2024_columns": sorted((j.get("misalignment_2024_evidence") or {}).keys()),
        "rows_written": j.get("rows_written"),
        "note": j.get("note", ""),
    }


def free_valuation_payload() -> dict:
    """Status of the free-data valuation builder (Yahoo prices + manual shares)."""
    if not FREE_VALUATION_REPORT.is_file():
        return {"available": False, "attempted": False}
    j = _load_json(FREE_VALUATION_REPORT)
    pc = j.get("price_coverage", {}) or {}
    return {
        "available": True,
        "attempted": True,
        "shares_status": j.get("shares_status"),
        "price_rows": pc.get("rows_with_price"),
        "total_rows": pc.get("total_rows"),
        "target_column_status": j.get("target_column_status", {}),
        "columns_entering_candidate": j.get("columns_entering_candidate", []),
        "shares_template_path": j.get("shares_template_path"),
        "limitations": j.get("limitations", ""),
    }


def build_data_quality_context(state: dict | None = None) -> dict:
    state = state or load_research_state()
    q, mig = state["quality"], state["migration"]
    man = q.get("manual_financials", {}) or {}
    return {
        "frozen_columns": q.get("frozen_columns_excluded_from_features", []),
        "leakage_controls": "next_year_* / same_year_return_pct / target_year never used as features",
        "misaligned_columns": mig.get("columns_rejected_misaligned", []),
        "manual_financials_present": man.get("present", False),
        "manual_accepted_features": man.get("accepted_feature_columns", []),
        "manual_source_note": man.get("source_note", ""),
        "manual_rejected": man.get("rejected_feature_columns", {}),
        "corrected_yearly": corrected_yearly_payload(),
        "free_valuation": free_valuation_payload(),
        "source_distinction": q.get("source_distinction", {}),
        "benchmark": q.get("benchmark", {}),
        "extreme_growth_counts": q.get("extreme_growth_counts", {}),
    }


def build_model_diagnostics_context(state: dict | None = None) -> dict:
    state = state or load_research_state()
    lb = state["leaderboard"]
    out: dict[str, Any] = {
        "small_sample": True,
        "interpretation": ("~40 stocks/year; out-of-sample metrics are noisy and overfitting-prone. "
                           "Prefer baselines and ranking/top-k over exact-return claims."),
        "splits": [],
    }
    if lb is not None and len(lb):
        for split in sorted(lb["split"].unique()):
            sub = lb[lb["split"] == split]
            base = sub[sub["kind"] == "baseline"]["spearman"].dropna()
            ml = sub[sub["kind"] == "ml"]["spearman"].dropna()
            out["splits"].append({
                "split": split,
                "baseline_spearman": round(float(base.mean()), 3) if len(base) else None,
                "best_ml_spearman": round(float(ml.max()), 3) if len(ml) else None,
                "ml_beats_baseline": bool(len(ml) and len(base) and ml.max() > base.mean()),
            })
        spears = lb["spearman"].dropna()
        out["mean_spearman"] = round(float(spears.mean()), 3) if len(spears) else None
        out["weak_backtest"] = bool(out.get("mean_spearman") is None or abs(out["mean_spearman"]) < 0.1)
        out["ml_beats_baseline_consistently"] = all(s["ml_beats_baseline"] for s in out["splits"]) if out["splits"] else False
    else:
        out["weak_backtest"] = True
        out["ml_beats_baseline_consistently"] = False
    after = (state["quality"] or {}).get("n_features", FEATURE_COUNT_BEFORE_CORRECTED)
    out["feature_count_before_corrected_yearly"] = FEATURE_COUNT_BEFORE_CORRECTED
    out["feature_count_after_corrected_yearly"] = after
    out["interpretation_business"] = (
        f"The dataset improved from {FEATURE_COUNT_BEFORE_CORRECTED} to {after} validated features after adding "
        "corrected yearly income and profitability data. Despite this structural improvement, the out-of-sample "
        "signal remains weak/unstable — the pipeline is better but the current data still does not demonstrate a "
        "reliable predictive edge. The missing block is historical valuation: P/E, P/B, EV/EBITDA, market cap and "
        "enterprise value, which are still repeated snapshots.")
    return out


def build_company_context(ticker: str, state: dict | None = None) -> dict:
    state = state or load_research_state()
    if state["modeling"] is None:
        raise ValueError("modeling dataset not available; run `make data` first.")
    df = state["modeling"]
    t = str(ticker).strip().upper()
    sub = df[df["ticker"].astype(str).str.upper() == t]
    if sub.empty:
        raise KeyError(f"ticker {t} not in modeling dataset")
    q = state["quality"]
    feats = [c for c in q.get("feature_columns", []) if c in df.columns]
    latest = sub.sort_values("year").iloc[-1]
    # percentile of each feature within the latest year's cross-section
    year_df = df[df["year"] == latest["year"]]
    pos, neg = {}, {}
    for f in feats:
        s = pd.to_numeric(year_df[f], errors="coerce")
        v = pd.to_numeric(pd.Series([latest[f]]), errors="coerce").iloc[0]
        if pd.isna(v):
            continue
        pct = round(float((s < v).mean() * 100), 1)
        (pos if pct >= 60 else neg if pct <= 40 else pos)[f] = pct
    top_pos = dict(sorted(pos.items(), key=lambda kv: -kv[1])[:5])
    top_neg = dict(sorted(neg.items(), key=lambda kv: kv[1])[:5])
    return {
        "ticker": t,
        "latest_year": int(latest["year"]),
        "has_target": bool(latest.get("has_target", False)),
        "is_inference_row": bool(latest.get("is_inference_row", False)),
        "same_year_return_pct": _num(latest.get("same_year_return_pct")),
        "feature_count": len(feats),
        "top_positive_features": top_pos,
        "top_negative_features": top_neg,
        "warnings": _company_warnings(state),
    }


def _num(v):
    try:
        return None if pd.isna(v) else round(float(v), 3)
    except (TypeError, ValueError):
        return None


def _fmt(v) -> str:
    """Human string for an answer fragment (None/NaN -> 'n/a')."""
    if v is None:
        return "n/a"
    try:
        if isinstance(v, float) and pd.isna(v):
            return "n/a"
    except (TypeError, ValueError):
        pass
    return str(v)


def _company_warnings(state: dict) -> list[str]:
    q = state["quality"]
    w = ["small_sample"]
    bench = q.get("benchmark", {}) or {}
    if not bench.get("excess_outperform_targets_enabled", q.get("benchmark_available", False)):
        w.append("benchmark_missing")
    if q.get("frozen_columns_excluded_from_features"):
        w.append("frozen_features")
    man = q.get("manual_financials", {}) or {}
    if not man.get("accepted_feature_columns"):
        w.append("no_real_valuation_profitability_features")
    return w


# --------------------------------------------------------------------------- #
# confidence layer (PHASE 5)
# --------------------------------------------------------------------------- #
def confidence_score(state: dict | None = None) -> dict:
    state = state or load_research_state()
    q = state["quality"]
    diag = build_model_diagnostics_context(state)
    man = q.get("manual_financials", {}) or {}
    bench = q.get("benchmark", {}) or {}
    score, reasons = 1.0, []

    if diag.get("small_sample"):
        score -= 0.25; reasons.append("small_sample (-0.25)")
    if not bench.get("excess_outperform_targets_enabled", q.get("benchmark_available", False)):
        score -= 0.15; reasons.append("benchmark_missing (-0.15)")
    if not man.get("accepted_feature_columns"):
        score -= 0.20; reasons.append("no_manual_valuation_profitability_features (-0.20)")
    if diag.get("weak_backtest"):
        score -= 0.20; reasons.append("weak_backtest_spearman_near_zero (-0.20)")
    if q.get("frozen_columns_excluded_from_features"):
        score -= 0.10; reasons.append("frozen_columns_present (-0.10)")

    score = max(0.0, min(1.0, round(score, 3)))
    level = "high" if score >= 0.66 else "medium" if score >= 0.33 else "low"
    return {"confidence_score": score, "confidence_level": level, "confidence_reasons": reasons}


# --------------------------------------------------------------------------- #
# ML score (PHASE 6) — never fabricated
# --------------------------------------------------------------------------- #
def ml_score_for_company(ticker: str, state: dict | None = None) -> dict:
    """ML score in [0,1]. Prefer the experiments artifact, else a feature-rank proxy.

    There is no trained per-company model that beats the baseline on this data, so
    even the artifact score is a transparent rank-based fallback. score_source,
    target_name and model_name are always exposed.
    """
    state = state or load_research_state()
    t = str(ticker).strip().upper()

    mo = state.get("model_outputs")
    if mo is not None and "ticker" in mo.columns:
        row = mo[mo["ticker"] == t]
        if not row.empty:
            r = row.sort_values("year").iloc[-1]
            return {"ml_score": _num(r.get("ml_score")), "ml_rank": int(r["ml_rank"]) if pd.notna(r.get("ml_rank")) else None,
                    "score_source": str(r.get("score_source", "fallback_rank_score")),
                    "target_name": str(r.get("target_name", "next_year_return_pct")),
                    "model_name": str(r.get("model_name", "baseline_equal_weight")),
                    "ml_score_note": str(r.get("notes", ""))}

    try:
        ctx = build_company_context(ticker, state)
    except (KeyError, ValueError) as exc:
        return {"ml_score": None, "score_source": "unavailable", "target_name": None,
                "model_name": None, "ml_score_note": str(exc)}
    pcts = list(ctx["top_positive_features"].values()) + list(ctx["top_negative_features"].values())
    if not pcts:
        return {"ml_score": None, "score_source": "unavailable", "target_name": None,
                "model_name": None, "ml_score_note": "no usable features for this company-year"}
    score = round(sum(pcts) / len(pcts) / 100.0, 3)
    return {"ml_score": score, "ml_rank": None, "score_source": "deterministic_feature_rank",
            "target_name": "next_year_return_pct", "model_name": "feature_rank_proxy",
            "ml_score_note": "rank-based proxy from validated year-T features (no trained model beats baseline)"}


# --------------------------------------------------------------------------- #
# deterministic fallbacks (PHASE 2)
# --------------------------------------------------------------------------- #
def deterministic_research_score(context: dict) -> dict:
    """LLM-free research score: midpoint of available evidence, conservative."""
    ml = context.get("ml_score")
    conf = context.get("confidence_score", 0.0)
    base = (ml if ml is not None else 0.5)
    # pull toward 0.5 by (1-confidence): low confidence => closer to neutral
    llm_like = round(0.5 + (base - 0.5) * conf, 3)
    return {"llm_research_score": max(0.0, min(1.0, llm_like)),
            "llm_confidence": context.get("confidence_level", "low"),
            "source": "deterministic_fallback"}


def deterministic_company_summary(context: dict) -> dict:
    t = context.get("ticker", "?")
    yr = context.get("latest_year")
    pos = ", ".join(context.get("top_positive_features", {})) or "none stand out"
    neg = ", ".join(context.get("top_negative_features", {})) or "none stand out"
    warns = context.get("warnings", [])
    summary = (f"{t} ({yr}): year-T features rank relatively strong on [{pos}] and weak on [{neg}]. "
               f"This is a structured-evidence description, not a prediction.")
    return {
        "summary": summary,
        "reasoning": "Percentile ranks of validated year-T features within the cross-section.",
        "positive_signals": list(context.get("top_positive_features", {})),
        "negative_signals": list(context.get("top_negative_features", {})),
        "warnings": warns,
        "limitations": _limitations(warns),
        "source": "deterministic_fallback",
    }


def _limitations(warns: list[str]) -> list[str]:
    M = {
        "small_sample": "Only ~40 stocks/year — metrics are statistically weak.",
        "benchmark_missing": "BIST100 benchmark may be absent — excess-return view limited.",
        "frozen_features": "Valuation/profitability columns are a frozen snapshot and were excluded.",
        "no_real_valuation_profitability_features": "No real historical valuation/profitability features ingested.",
        "weak_backtest": "Backtest correlation is near zero/unstable.",
    }
    return [M[w] for w in warns if w in M] or ["Research-support only; not investment advice."]


# --------------------------------------------------------------------------- #
# LLM provider abstraction (PHASE 3) — fails safe
# --------------------------------------------------------------------------- #
def _strip_think(text: str) -> str:
    """Remove <think>...</think> reasoning blocks some models emit."""
    if not text:
        return text
    import re
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()


def _http_post_json(url: str, payload: dict, timeout: float, headers: dict | None = None) -> dict:
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers=req_headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _openrouter_headers(cfg: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "HTTP-Referer": cfg.get("http_referer") or "http://localhost:3000",
        "X-Title": cfg.get("app_title") or "FinanceIQ",
    }
    return {k: v for k, v in headers.items() if v}


def call_local_llm(messages: list[dict], cfg: dict | None = None) -> dict:
    cfg = cfg or get_config()
    if cfg["provider"] == "none" or not cfg["base_url"]:
        return {"ok": False, "provider": "none", "error": "no provider configured"}
    timeout = cfg["timeout"]
    # ---- Ollama -----------------------------------------------------------
    if cfg["provider"] == "ollama":
        try:
            payload = {"model": cfg["model"], "messages": messages, "stream": False,
                       "options": {"temperature": 0.2}}
            data = _http_post_json(cfg["base_url"], payload, timeout)
            return {"ok": True, "provider": "ollama",
                    "content": _strip_think(data.get("message", {}).get("content", ""))}
        except Exception as exc:  # noqa
            return {"ok": False, "provider": "ollama", "error": str(exc)}
    # ---- OpenRouter / OpenAI-compatible -----------------------------------
    if cfg["provider"] in {"openrouter", "openai"}:
        if not cfg.get("api_key"):
            return {"ok": False, "provider": cfg["provider"], "error": "missing OPENROUTER_API_KEY or OPENAI_API_KEY"}
        try:
            payload = {"model": cfg["model"], "messages": messages, "temperature": 0.2,
                       "max_tokens": int(cfg.get("max_tokens", 700))}
            data = _http_post_json(cfg["base_url"], payload, timeout, headers=_openrouter_headers(cfg))
            content = _strip_think(data["choices"][0]["message"]["content"])
            return {"ok": True, "provider": "openrouter", "content": content}
        except Exception as exc:  # noqa
            return {"ok": False, "provider": "openrouter", "error": str(exc)}
    # ---- LM Studio / OpenAI-compatible primary ----------------------------
    try:
        payload = {"model": cfg["model"], "messages": messages, "temperature": 0.2,
                   "max_tokens": int(cfg.get("max_tokens", 700))}
        data = _http_post_json(cfg["base_url"], payload, timeout)
        content = _strip_think(data["choices"][0]["message"]["content"])
        return {"ok": True, "provider": cfg["provider"], "content": content}
    except Exception as primary_exc:  # noqa - try LM Studio native endpoint
        try:
            alt = cfg["base_url"].replace("/v1/chat/completions", "/api/v1/chat")
            if alt == cfg["base_url"]:
                raise primary_exc
            sys_txt = "\n".join(m["content"] for m in messages if m["role"] == "system")
            usr_txt = "\n".join(m["content"] for m in messages if m["role"] != "system")
            data = _http_post_json(alt, {"model": cfg["model"], "system_prompt": sys_txt,
                                         "input": usr_txt}, timeout)
            content = data["output"][0]["content"] if isinstance(data.get("output"), list) else data.get("content", "")
            return {"ok": True, "provider": cfg["provider"], "content": _strip_think(content), "endpoint": "native"}
        except Exception as alt_exc:  # noqa
            return {"ok": False, "provider": cfg["provider"], "error": f"{primary_exc} | alt: {alt_exc}"}


LLM_RESULT_SCHEMA: dict[str, Any] = {
    "llm_research_score": None, "llm_confidence": "low", "summary": "", "reasoning": "",
    "positive_signals": [], "negative_signals": [], "warnings": [], "limitations": [],
}


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        # drop leading ```lang and trailing ```
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def _repair_json(blob: str) -> str:
    """Best-effort, SAFE repair of small model JSON mistakes.

    Handles: code fences, trailing commas, and the common
    `"key: value"` / `key: value` mistakes where the model forgot quotes.
    """
    import re
    s = _strip_code_fences(blob)
    start, end = s.find("{"), s.rfind("}")
    if start >= 0 and end > start:
        s = s[start:end + 1]
    # `"llm_confidence: medium"` -> `"llm_confidence": "medium"`  (quote opened before key, value unquoted)
    s = re.sub(r'"(\w+)\s*:\s*([A-Za-z0-9_.\- ]+?)"', r'"\1": "\2"', s)
    # bare-key `key:` (no opening quote) at start of a field -> `"key":`
    s = re.sub(r'([{,]\s*)([A-Za-z_]\w*)(\s*):', r'\1"\2"\3:', s)
    # trailing commas before } or ]
    s = re.sub(r',\s*([}\]])', r'\1', s)
    return s


def _coerce_llm_result(obj: dict) -> dict:
    """Force a parsed dict into the strict schema with safe defaults."""
    out = dict(LLM_RESULT_SCHEMA)
    if isinstance(obj, dict):
        for k in out:
            if k in obj and obj[k] is not None:
                out[k] = obj[k]
    s = out.get("llm_research_score")
    out["llm_research_score"] = max(0.0, min(1.0, float(s))) if isinstance(s, (int, float)) else None
    conf = str(out.get("llm_confidence", "low")).strip().lower()
    out["llm_confidence"] = conf if conf in ("low", "medium", "high") else "low"
    for k in ("summary", "reasoning"):
        out[k] = "" if out[k] is None else str(out[k])
    for k in ("positive_signals", "negative_signals", "warnings", "limitations"):
        v = out[k]
        out[k] = [str(x) for x in v] if isinstance(v, list) else ([str(v)] if v else [])
    return out


def _parse_llm_json(content: str) -> dict | None:
    """Parse model output into the strict schema. Returns None only if no object recoverable."""
    if not content or not str(content).strip():
        return None
    for candidate in (content, _repair_json(content)):
        try:
            start, end = candidate.find("{"), candidate.rfind("}")
            if start < 0 or end < 0:
                continue
            obj = json.loads(candidate[start:end + 1])
            if isinstance(obj, dict):
                return _coerce_llm_result(obj)
        except Exception:
            continue
    return None


def _human_answer(result: dict) -> str:
    """Compact human-readable line from a structured llm_result (no raw JSON)."""
    parts = []
    if result.get("summary"):
        parts.append(str(result["summary"]).strip())
    conf = result.get("llm_confidence")
    score = result.get("llm_research_score")
    meta = []
    if score is not None:
        meta.append(f"LLM support score {score:.2f}")
    if conf:
        meta.append(f"confidence {conf}")
    if meta:
        parts.append("(" + ", ".join(meta) + ")")
    return " ".join(parts) if parts else "No summary produced."


# --------------------------------------------------------------------------- #
# composite (PHASE 7)
# --------------------------------------------------------------------------- #
def composite_score(ml_score, confidence_score_v, llm_research_score, cfg: dict | None = None) -> dict:
    cfg = cfg or get_config()
    w = cfg["weights"]
    notes = []
    # The LLM contributes ONLY when it returns a meaningful score in (0,1]. A null
    # or exactly-0 value means "AI evidence unavailable" (small models often emit 0
    # when unsure) — its weight is redistributed to ML + confidence instead of
    # dragging the final score down. Bounded weight => the LLM can never dominate.
    llm_available = isinstance(llm_research_score, (int, float)) and 0.0 < float(llm_research_score) <= 1.0
    llm_for_calc = float(llm_research_score) if llm_available else None
    if not llm_available:
        notes.append("AI evidence unavailable -> LLM weight redistributed to ML + confidence")

    comps = {"ml": (ml_score, w["ml"]),
             "confidence": (confidence_score_v, w["confidence"]),
             "llm": (llm_for_calc, w["llm"])}
    # redistribute weight of any null component across present ones
    present = {k: (v, wt) for k, (v, wt) in comps.items() if v is not None}
    if ml_score is None:
        notes.append("ml_score null -> weight redistributed; result is a partial_score")
    total_w = sum(wt for _, wt in present.values()) or 1.0
    final = round(sum(v * wt for v, wt in present.values()) / total_w, 3) if present else None
    return {
        "ml_score": ml_score,
        "confidence_score": confidence_score_v,
        "llm_research_score": llm_for_calc,          # null when unavailable (UI shows "unavailable")
        "llm_support_available": llm_available,
        "final_research_score": final,
        "partial_score": ml_score is None,
        "weights_used": {"ml": w["ml"], "confidence": w["confidence"], "llm": w["llm"]},
        "scoring_notes": notes or ["all components present"],
        "disclaimer": NOT_ADVICE,
    }


# --------------------------------------------------------------------------- #
# provider diagnostics (safe, no secrets)
# --------------------------------------------------------------------------- #
def provider_diagnostics(cfg: dict | None = None, provider_used=None,
                         fallback_used=None, llm_error=None) -> dict:
    cfg = cfg or get_config()
    return {
        "configured_provider": cfg["provider"],
        "configured_model": cfg["model"],
        "configured_base_url": cfg["base_url"],
        "provider_used": provider_used,
        "fallback_used": fallback_used,
        "llm_error": llm_error,
    }


# --------------------------------------------------------------------------- #
# decision-support layer (deterministic; LLM never overrides hard warnings)
# --------------------------------------------------------------------------- #
_VERDICT_ORDER = ["insufficient evidence", "low confidence watchlist",
                  "moderate research interest", "high research interest"]


def decision_support(final_score, confidence_level: str, warnings: list[str], diag: dict) -> dict:
    weak = bool(diag.get("weak_backtest", True))
    warnings = warnings or []
    blocking = []
    if "frozen_features" in warnings:
        blocking.append("Valuation/profitability columns are a frozen snapshot (excluded).")
    if "no_real_valuation_profitability_features" in warnings:
        blocking.append("Real historical valuation/profitability data is still missing.")
    if weak:
        blocking.append("Backtest signal is weak/unstable.")
    if "small_sample" in warnings:
        blocking.append("Small sample (~40 stocks/year).")

    if final_score is None:
        verdict = "insufficient evidence"
    elif final_score >= 0.60:
        verdict = "high research interest"
    elif final_score >= 0.45:
        verdict = "moderate research interest"
    else:
        verdict = "low confidence watchlist"

    # Deterministic caution: weak model / low confidence cannot yield a strong verdict.
    cap = "low confidence watchlist" if (weak or confidence_level == "low") else "moderate research interest"
    if _VERDICT_ORDER.index(verdict) > _VERDICT_ORDER.index(cap):
        verdict = cap

    reasoning = (
        "Structured ML score and deterministic confidence are primary; the LLM is bounded support. "
        f"Final research score {('%.2f' % final_score) if final_score is not None else 'n/a'} with "
        f"{confidence_level} confidence" + (" and a weak backtest" if weak else "") +
        " keeps this a research-interest signal only, never a buy/sell/hold recommendation."
    )
    required = [
        "Real per-year valuation history (P/E, P/B, EV/EBITDA).",
        "Real per-year profitability history (ROE, ROA, margins).",
        "Larger cross-section / more history to stabilise the backtest.",
    ]
    return {
        "decision_support_verdict": verdict,
        "decision_support_reasoning": reasoning,
        "blocking_limitations": blocking,
        "required_next_data": required,
        "not_investment_advice": True,
    }


# --------------------------------------------------------------------------- #
# high-level generators (PHASE 2)
# --------------------------------------------------------------------------- #
def generate_company_insight(ticker: str, state: dict | None = None) -> dict:
    state = state or load_research_state()
    ctx = build_company_context(ticker, state)
    conf = confidence_score(state)
    ml = ml_score_for_company(ticker, state)
    ctx_for_score = {**ctx, **conf, **ml}

    # Prefer the pre-built structured RAG context (richer: financials, valuation,
    # benchmarks, data_quality). Fall back to the lighter build_company_context dict.
    rag_ctx = load_company_context_json(ticker)
    if rag_ctx is not None:
        # Merge ml_score/rank into the RAG context model block
        rag_ctx.setdefault("model", {})
        if rag_ctx["model"].get("ml_score") is None:
            rag_ctx["model"]["ml_score"] = ml.get("ml_score")
            rag_ctx["model"]["ml_rank"] = ml.get("ml_rank")
        llm_context = rag_ctx
    else:
        llm_context = ctx_for_score

    cfg = get_config()
    llm_out, fallback = None, True
    if cfg["provider"] != "none":
        msg = [{"role": "system", "content": SYSTEM_PROMPT},
               {"role": "user", "content": json.dumps({"task": "company_insight", "context": llm_context})}]
        res = call_local_llm(msg, cfg)
        if res.get("ok"):
            parsed = _parse_llm_json(res["content"])
            if parsed:
                llm_out, fallback = parsed, False
    if llm_out is None:
        det = deterministic_company_summary(ctx)
        llm_out = {**det, **deterministic_research_score(ctx_for_score)}

    llm_score = llm_out.get("llm_research_score")
    comp = composite_score(ml.get("ml_score"), conf["confidence_score"], llm_score, cfg)
    diag = build_model_diagnostics_context(state)
    ds = decision_support(comp["final_research_score"], conf["confidence_level"], ctx["warnings"], diag)
    # Flat, explicit score block (PHASE 5 contract) — components never hidden.
    score = {
        "ticker": ctx["ticker"], "year": ctx["latest_year"],
        "score_source": ml.get("score_source"), "target_name": ml.get("target_name"),
        "model_name": ml.get("model_name"),
        "ml_score_label": "Fundamental ranking model",
        "confidence_label": "Data confidence",
        "llm_support_label": "AI evidence support",
        "final_label": "Final research score",
        "ml_rank": ml.get("ml_rank"),
        "ml_score": comp["ml_score"], "confidence_score": comp["confidence_score"],
        "llm_research_score": comp["llm_research_score"],
        "llm_support_available": comp["llm_support_available"],
        "final_research_score": comp["final_research_score"],
        "partial_score": comp["partial_score"], "weights_used": comp["weights_used"],
        "confidence_level": conf["confidence_level"], "confidence_reasons": conf["confidence_reasons"],
        "reasoning": llm_out.get("reasoning"), "warnings": ctx["warnings"],
        "limitations": llm_out.get("limitations"), "scoring_notes": comp["scoring_notes"],
        "decision_support_verdict": ds["decision_support_verdict"],
        "decision_support_reasoning": ds["decision_support_reasoning"],
        "blocking_limitations": ds["blocking_limitations"],
        "required_next_data": ds["required_next_data"],
        "not_investment_advice": True,
    }
    llm_err = None if not fallback else "no LLM provider or unparseable output; deterministic fallback used"
    llm_used = not fallback
    return {
        "ticker": ctx["ticker"], "context": ctx, "ml": ml, "confidence": conf,
        "llm": llm_out, "score": score, "decision_support": ds,
        "provider_used": cfg["provider"], "fallback_used": fallback,
        "mode": "llm" if llm_used else "fallback", "llm_used": llm_used,
        "model": cfg["model"] if llm_used else None,
        "diagnostics": provider_diagnostics(cfg, cfg["provider"], fallback, llm_err),
        "disclaimer": NOT_ADVICE, "not_investment_advice": True,
    }


def generate_summary_insight(state: dict | None = None) -> dict:
    state = state or load_research_state()
    ctx = build_summary_context(state)
    conf = confidence_score(state)
    diag = build_model_diagnostics_context(state)
    warns = []
    if not ctx["benchmark_available"]:
        warns.append("benchmark_missing")
    if ctx["rejected_frozen_columns"]:
        warns.append("frozen_features")
    if diag.get("weak_backtest"):
        warns.append("weak_backtest")
    warns.append("small_sample")

    cfg = get_config()
    summary, fallback, llm_error = None, True, None
    if cfg["provider"] != "none":
        msg = [{"role": "system", "content": SYSTEM_PROMPT},
               {"role": "user", "content": json.dumps({"task": "summary", "context": {**ctx, **conf, "diagnostics": diag}})}]
        res = call_local_llm(msg, cfg)
        if res.get("ok"):
            parsed = _parse_llm_json(res["content"])
            if parsed:
                summary, fallback = parsed, False
            else:
                llm_error = "LLM output could not be parsed into valid JSON; deterministic fallback used"
        else:
            llm_error = res.get("error")
    if summary is None:
        summary = {
            "summary": (f"Dataset: {ctx['rows']} rows, {ctx['feature_count']} validated year-T features, "
                        f"{ctx['rows_with_target']} with next-year targets. Benchmark "
                        f"{'available' if ctx['benchmark_available'] else 'MISSING'}. "
                        f"{len(ctx['rejected_frozen_columns'])} frozen columns excluded."),
            "reasoning": "Derived from data_quality_report + leaderboard.",
            "warnings": warns, "limitations": _limitations(warns), "source": "deterministic_fallback",
            "llm_research_score": None, "llm_confidence": conf["confidence_level"],
        }
    return {"context": ctx, "confidence": conf, "diagnostics": diag, "summary": summary,
            "provider_used": cfg["provider"], "fallback_used": fallback, "llm_error": llm_error,
            "provider_diagnostics": provider_diagnostics(cfg, cfg["provider"], fallback, llm_error),
            "disclaimer": NOT_ADVICE}


def _records(df) -> list[dict]:
    """JSON-safe records: NaN/inf -> null (FastAPI cannot serialize NaN floats)."""
    if df is None or len(df) == 0:
        return []
    return json.loads(df.to_json(orient="records"))


def experiments_payload(state: dict | None = None) -> dict:
    state = state or load_research_state()
    diag = build_model_diagnostics_context(state)
    lb = state["leaderboard"]
    by_target = []
    if LEADERBOARD_BY_TARGET.is_file():
        try:
            by_target = _records(pd.read_csv(LEADERBOARD_BY_TARGET))
        except Exception:
            by_target = []
    targets = sorted({r.get("target") for r in by_target if r.get("target")}) or ["next_year_return_pct"]
    return {
        "primary_target": "next_year_return_pct",
        "available_targets": targets,
        "diagnostics": diag,
        "leaderboard": _records(lb),
        "leaderboard_by_target": by_target,
        "verdict": ("No reliable predictive edge demonstrated yet. Single-split spikes should not be "
                    "trusted; more real historical valuation/profitability data is required."),
        "interpretation_business": [
            f"The dataset improved from {FEATURE_COUNT_BEFORE_CORRECTED} to {diag.get('feature_count_after_corrected_yearly', 27)} validated features.",
            "Corrected yearly income and profitability fields are now included.",
            "Despite this improvement, out-of-sample signal remains weak/unstable.",
            "The pipeline improved structurally, but the current data still does not demonstrate a reliable predictive edge.",
            "The missing block is historical valuation: P/E, P/B, EV/EBITDA, market cap, enterprise value.",
        ],
        "small_sample": True,
        "disclaimer": NOT_ADVICE,
    }


def benchmark_payload() -> dict:
    path = next((p for p in (BENCHMARK_CSV, BENCHMARK_CSV_ALT) if p.is_file()), None)
    returns, source = {}, "none"
    if path is not None:
        try:
            b = pd.read_csv(path, comment="#")
            b.columns = [c.strip().lower() for c in b.columns]
            for _, r in b.dropna(subset=["year", "bist100_return_pct"]).iterrows():
                returns[int(r["year"])] = round(float(r["bist100_return_pct"]), 2)
        except Exception:
            returns = {}
    if BENCHMARK_REPORT.is_file():
        try:
            source = json.loads(BENCHMARK_REPORT.read_text()).get("source", "none")
        except Exception:
            source = "unknown"
    return {
        "available": bool(returns),
        "source": source,
        "years_covered": sorted(returns.keys()),
        "returns_by_year": returns,
        "targets_enabled": bool(returns),
        "derived_targets": ["next_year_bist100_return_pct", "next_year_excess_return_vs_bist100",
                            "next_year_outperform_bist100"],
        "explanation": ("Excess return = stock next-year return minus BIST100 next-year return. "
                        "Outperform = excess > 0. Targets are null until benchmark is present."),
        "disclaimer": NOT_ADVICE,
    }


def companies_payload(state: dict | None = None) -> dict:
    state = state or load_research_state()
    df = state["modeling"]
    if df is None:
        return {"companies": [], "year": None, "note": "modeling dataset not available"}
    year = int(df["year"].max())
    sub = df[df["year"] == year]
    mo = state.get("model_outputs")
    score_map, rank_map = {}, {}
    if mo is not None:
        for _, r in mo.iterrows():
            score_map[str(r["ticker"]).upper()] = _num(r.get("ml_score"))
            rank_map[str(r["ticker"]).upper()] = int(r["ml_rank"]) if pd.notna(r.get("ml_rank")) else None
    rows = []
    for t in sorted(sub["ticker"].astype(str).str.upper().unique()):
        rows.append({"ticker": t, "year": year, "ml_score": score_map.get(t),
                     "ml_rank": rank_map.get(t)})
    rows.sort(key=lambda r: (r["ml_rank"] is None, r["ml_rank"] if r["ml_rank"] is not None else 1e9))
    return {"year": year, "count": len(rows), "companies": rows, "disclaimer": NOT_ADVICE}


def frozen_evidence_payload() -> dict:
    out = {"available": False, "columns": {}, "verdict": "frozen evidence report not generated yet",
           "quarterly": None}
    if FROZEN_EVIDENCE.is_file():
        try:
            j = json.loads(FROZEN_EVIDENCE.read_text())
            out = {"available": True, "columns": j.get("columns", {}),
                   "verdict": j.get("verdict", ""), "note": j.get("note", ""), "quarterly": None}
        except Exception:
            pass
    if QUARTERLY_INSPECTION.is_file():
        try:
            out["quarterly"] = json.loads(QUARTERLY_INSPECTION.read_text())
        except Exception:
            pass
    return out


# --------------------------------------------------------------------------- #
# grounded intent helpers (PHASE 3/4) — specific, never-fabricated answers
# --------------------------------------------------------------------------- #
def get_corrected_yearly_status(state: dict | None = None) -> dict:
    state = state or load_research_state()
    cy = corrected_yearly_payload()
    q = state["quality"]
    after = q.get("n_features", FEATURE_COUNT_BEFORE_CORRECTED)
    return {
        "corrected_yearly_data_available": bool(cy.get("available")),
        "feature_count_before_corrected_yearly": FEATURE_COUNT_BEFORE_CORRECTED,
        "feature_count_after_corrected_yearly": after,
        "accepted_corrected_yearly_features": cy.get("accepted_columns") or ACCEPTED_CORRECTED_YEARLY,
        "still_missing_valuation_features": cy.get("frozen_valuation_columns") or STILL_MISSING_VALUATION,
        "old_snapshot_rejected_but_corrected_accepted": OLD_SNAPSHOT_REJECTED_NOW_CORRECTED,
        "misalignment_2024_columns": cy.get("misalignment_2024_columns", []),
        "model_signal_after_corrected_yearly": "still weak/unstable",
    }


def get_missing_data_summary(state: dict | None = None) -> dict:
    return {
        "still_missing_valuation_features": STILL_MISSING_VALUATION,
        "summary": ("Real per-year historical valuation is still missing: P/E, P/B, EV/EBITDA, market cap "
                    "and enterprise value are repeated snapshots. A non-misaligned 2024 export and a larger "
                    "cross-section would also help."),
        "request_from_provider": ("Per-year (or per-quarter) valuation time series that actually change over "
                                  "time, plus a corrected 2024 file with aligned balance-sheet columns."),
    }


def get_benchmark_outperformers(year: int | None = None, limit: int = 10, state: dict | None = None) -> dict:
    """Historical realized outperformers vs BIST100 (reporting on completed target years)."""
    state = state or load_research_state()
    df = state["modeling"]
    need = {"ticker", "target_year", "next_year_outperform_bist100",
            "next_year_excess_return_vs_bist100"}
    if df is None or not need.issubset(df.columns):
        return {"available": False, "reason": "benchmark-relative targets not present in modeling dataset"}
    sub = df[df["next_year_outperform_bist100"].notna()].copy()
    if sub.empty:
        return {"available": False, "reason": "no completed benchmark target years yet"}
    sub["target_year"] = sub["target_year"].astype(int)
    years_avail = sorted(int(y) for y in sub["target_year"].unique())
    use_year = int(year) if (year is not None and int(year) in years_avail) else years_avail[-1]
    yr = sub[sub["target_year"] == use_year].copy()
    out = yr[yr["next_year_outperform_bist100"].astype(bool)].copy()
    out = out.sort_values("next_year_excess_return_vs_bist100", ascending=False)
    rows = [{"ticker": str(r["ticker"]).upper(),
             "excess_return_vs_bist100_pct": _num(r["next_year_excess_return_vs_bist100"]),
             "stock_return_pct": _num(r.get("next_year_return_pct")),
             "bist100_return_pct": _num(r.get("next_year_bist100_return_pct"))}
            for _, r in out.head(limit).iterrows()]
    bench_ret = None
    if "next_year_bist100_return_pct" in yr.columns and len(yr):
        bench_ret = _num(yr["next_year_bist100_return_pct"].dropna().iloc[0]) if yr["next_year_bist100_return_pct"].notna().any() else None
    return {
        "available": True,
        "target_year": use_year,
        "years_available": years_avail,
        "benchmark_return_pct": bench_ret,
        "outperformer_count": int(len(out)),
        "total_in_year": int(len(yr)),
        "truncated": bool(len(out) > limit),
        "outperformers": rows,
        "fields_used": ["ticker", "target_year", "next_year_return_pct",
                        "next_year_bist100_return_pct", "next_year_excess_return_vs_bist100",
                        "next_year_outperform_bist100"],
    }


def get_top_ranked_companies(year: int | None = None, limit: int = 10, state: dict | None = None) -> dict:
    state = state or load_research_state()
    mo = state.get("model_outputs")
    if mo is None or "ml_rank" not in mo.columns:
        return {"available": False, "reason": "model outputs not available"}
    df = mo.copy()
    df["year"] = pd.to_numeric(df.get("year"), errors="coerce")
    years_avail = sorted(int(y) for y in df["year"].dropna().unique())
    use_year = int(year) if year in years_avail else (years_avail[-1] if years_avail else None)
    if use_year is not None:
        df = df[df["year"] == use_year]
    df = df.sort_values("ml_rank")
    rows = [{"ticker": str(r["ticker"]).upper(), "ml_rank": int(r["ml_rank"]) if pd.notna(r.get("ml_rank")) else None,
             "ml_score": _num(r.get("ml_score")), "score_source": str(r.get("score_source", "")),
             "target_name": str(r.get("target_name", ""))}
            for _, r in df.head(limit).iterrows()]
    return {"available": True, "year": use_year, "years_available": years_avail, "top_ranked": rows}


_YEAR_RE = __import__("re").compile(r"\b(20\d{2})\b")


def classify_intent(question: str) -> str:
    q = (question or "").lower()
    if any(k in q for k in ("beat bist", "outperform", "beat the benchmark", "beat the market", "beat index")):
        return "benchmark_outperformers"
    if "bist" in q or "benchmark" in q:
        return "benchmark_status"
    if any(k in q for k in ("top rank", "highest score", "best ranked", "top stocks", "highest rank",
                            "top ranked", "best stocks", "ranked highest")):
        return "top_ranked"
    if any(k in q for k in ("valuation", "p/e", " pe ", "p/b", " pb ", "ev/ebitda", "ev_ebitda",
                            "market cap", "market_cap", "enterprise value", "calculate p", "fintables", "kap",
                            "shares outstanding", "shares", "free float", "free-float", "fiili", "dolas",
                            "issued capital", "paid-in", "paid in capital", "fill shares")):
        return "valuation"
    if any(k in q for k in ("why", "weak", "signal", "reliable", "edge", "backtest", "diagnostic")):
        return "diagnostics"
    if any(k in q for k in ("accept", "reject", "feature", "column", "frozen", "valuation",
                            "missing", "corrected", "data quality", "snapshot", "leakage")):
        return "data_quality"
    return "general"


def _year_in(question: str):
    m = _YEAR_RE.search(question or "")
    return int(m.group(1)) if m else None


def _intent_answer(intent: str, question: str, state: dict, ticker: str | None) -> dict | None:
    """Deterministic, specific answer for a detected intent. None for 'general'."""
    year = _year_in(question)
    cy = get_corrected_yearly_status(state)
    warns = _company_warnings(state)
    lims = _limitations(warns)

    if intent == "benchmark_outperformers":
        o = get_benchmark_outperformers(year=year, limit=10, state=state)
        if not o.get("available"):
            return {"answer": ("Benchmark-relative results are not available yet: " + o.get("reason", "") +
                               ". 2025 rows are inference-only (no next-year result yet)."),
                    "data_used": {"source": "modeling_dataset", "year": year, "rows_used": 0, "fields_used": []},
                    "warnings": warns, "limitations": lims}
        names = ", ".join(f"{r['ticker']} (+{r['excess_return_vs_bist100_pct']:.1f}% vs BIST100)"
                          for r in o["outperformers"]) or "none"
        trunc = " (top 10 shown)" if o["truncated"] else ""
        bench = f"BIST100 returned {o['benchmark_return_pct']:.1f}% that year; " if o.get("benchmark_return_pct") is not None else ""
        ans = (f"For target year {o['target_year']}, {bench}{o['outperformer_count']} of {o['total_in_year']} "
               f"stocks beat BIST100{trunc}: {names}. Completed target years available: "
               f"{o['years_available'][0]}–{o['years_available'][-1]}. This is historical evaluation of realized "
               "returns, not a future recommendation.")
        return {"answer": ans, "intent_data": o,
                "data_used": {"source": "modeling_dataset (realized benchmark targets)",
                              "year": o["target_year"], "target_year": o["target_year"],
                              "rows_used": o["total_in_year"], "fields_used": o["fields_used"]},
                "warnings": warns, "limitations": lims}

    if intent == "benchmark_status":
        b = benchmark_payload()
        if b["available"]:
            yrs = ", ".join(str(y) for y in b["years_covered"])
            ans = (f"The BIST100 benchmark is available (source {b['source']}) for {yrs}. It lets the system "
                   "compare each stock's next-year return against the market, enabling excess-return and "
                   "outperform-BIST100 targets.")
        else:
            ans = "The BIST100 benchmark is currently missing, so market-comparison targets are disabled."
        return {"answer": ans,
                "data_used": {"source": "bist100_benchmark", "year": None,
                              "rows_used": len(b["years_covered"]), "fields_used": ["year", "bist100_return_pct"]},
                "warnings": warns, "limitations": lims}

    if intent == "top_ranked":
        t = get_top_ranked_companies(year=year, limit=10, state=state)
        if not t.get("available"):
            return {"answer": "Model-ranked companies are not available: " + t.get("reason", ""),
                    "data_used": {"source": "research_agent_model_outputs", "year": year, "rows_used": 0, "fields_used": []},
                    "warnings": warns, "limitations": lims}
        names = ", ".join(f"{r['ticker']} (#{r['ml_rank']})" for r in t["top_ranked"]) or "none"
        src = t["top_ranked"][0]["score_source"] if t["top_ranked"] else "rank score"
        ans = (f"Highest model-ranked companies for {t['year']} (by transparent ML rank score, source: {src}): "
               f"{names}. Note the backtest signal is still weak, so treat these as research candidates, not advice.")
        return {"answer": ans, "intent_data": t,
                "data_used": {"source": "research_agent_model_outputs.csv", "year": t["year"],
                              "rows_used": len(t["top_ranked"]),
                              "fields_used": ["ticker", "ml_rank", "ml_score", "score_source", "target_name"]},
                "warnings": warns, "limitations": lims}

    if intent == "diagnostics":
        diag = build_model_diagnostics_context(state)
        ans = (f"The dataset improved from {cy['feature_count_before_corrected_yearly']} to "
               f"{cy['feature_count_after_corrected_yearly']} validated features after adding corrected yearly "
               "income and profitability data. Despite this, the out-of-sample signal is still weak/unstable "
               f"(mean rank-correlation {_fmt(diag.get('mean_spearman'))}, ML does not consistently beat a "
               "simple baseline). The dataset is small (~40 stocks/year) and historical valuation (P/E, P/B, "
               "EV/EBITDA, market cap, enterprise value) is still a repeated snapshot — so no reliable "
               "predictive edge is demonstrated yet.")
        return {"answer": ans,
                "data_used": {"source": "experiments + data_quality", "year": None,
                              "rows_used": 0, "fields_used": ["mean_spearman", "weak_backtest", "feature_count"]},
                "warnings": warns, "limitations": lims}

    if intent == "data_quality":
        acc = ", ".join(cy["accepted_corrected_yearly_features"])
        miss = ", ".join(cy["still_missing_valuation_features"])
        ans = (f"Corrected yearly files added {len(cy['accepted_corrected_yearly_features'])} real per-year "
               f"income/profitability features now used by the model: {acc}. These same names were rejected in "
               "the OLD snapshot source (repeated values), but the corrected source genuinely changes year by "
               f"year. Still missing/rejected as a frozen snapshot: {miss}. The 2024 export also had columns "
               "shifted into the wrong place, so those cells were rejected rather than guessed.")
        return {"answer": ans, "intent_data": cy,
                "data_used": {"source": "corrected_yearly_ingestion_report + data_quality_report", "year": None,
                              "rows_used": cy["feature_count_after_corrected_yearly"],
                              "fields_used": cy["accepted_corrected_yearly_features"]},
                "warnings": warns, "limitations": lims}

    if intent == "valuation":
        fv = free_valuation_payload()
        attempted = fv.get("attempted")
        entered = fv.get("columns_entering_candidate") or []
        shares = fv.get("shares_status", "missing")
        ql = (question or "").lower()
        # free-float / how-to-fill sub-questions get a specific, correct answer
        if any(k in ql for k in ("free float", "free-float", "fiili", "dolas")):
            ans = ("No — 'Fiili Dolasimdaki Pay Tutari' (free float) is only the publicly-traded portion and "
                   "understates total shares, so it must NOT be used for market cap. Market cap needs TOTAL "
                   "issued / paid-in shares (or total share count). Free-float rows are tagged "
                   "capital_basis=free_float_only and rejected by the builder.")
            return {"answer": ans, "data_used": {"source": "shares workflow", "year": None, "rows_used": 0,
                    "fields_used": ["capital_basis", "shares_outstanding"]}, "warnings": warns, "limitations": lims}
        if any(k in ql for k in ("how do i fill", "fill shares", "shares outstanding", "issued capital",
                                 "paid-in", "paid in capital", "how to fill")):
            ans = ("Fill shares via the capital-EVENT file, not 240 manual rows: edit "
                   "data/trusted_raw/shares_outstanding_events.csv with ONE row per capital CHANGE "
                   "(ticker, effective_year, total issued/paid-in shares, source, confidence, "
                   "capital_basis=issued_capital, nominal_value=1). Stable capital = a single 2020 row. "
                   "Run `make shares` to carry events forward to every year, then `make valuation`. Use total "
                   "issued/paid-in capital (share count when nominal value is 1 TL) — never free float.")
            return {"answer": ans, "data_used": {"source": "shares workflow", "year": None, "rows_used": 0,
                    "fields_used": ["effective_year", "shares_outstanding", "capital_basis"]},
                    "warnings": warns, "limitations": lims}
        if not attempted:
            ans = ("Valuation columns (P/E, P/B, EV/EBITDA, market cap, enterprise value) are not available "
                   "yet. The old Fintables snapshot repeated one value across years and was rejected. A free "
                   "builder can reconstruct them from year-end price × shares plus validated financials.")
        elif entered:
            ans = (f"Yes — free valuation columns now in the model: {', '.join(entered)}. They are computed "
                   "from Yahoo year-end price × shares outstanding and validated financials (P/E = market cap / "
                   "net income, P/B = market cap / equity, EV/EBITDA = (market cap + net debt) / EBITDA).")
        else:
            ans = ("We can calculate P/E, P/B and EV/EBITDA ourselves WITHOUT buying frozen Fintables data: "
                   f"P/E = market cap / net income, P/B = market cap / equity, EV/EBITDA = (market cap + net "
                   f"debt) / EBITDA, where market cap = year-end price × shares outstanding. Year-end prices were "
                   f"collected free from Yahoo ({fv.get('price_rows')}/{fv.get('total_rows')} rows). The binding "
                   f"gap is shares outstanding ({shares}) — Yahoo gives price but not historical share counts. "
                   "Until real shares are supplied (KAP / company reports), market cap and the ratios stay null "
                   "and cannot enter the model. The old Fintables valuation snapshot remains rejected.")
        return {"answer": ans, "intent_data": fv,
                "data_used": {"source": "free_valuation_history_report", "year": None,
                              "rows_used": fv.get("price_rows", 0),
                              "fields_used": ["year_end_close", "shares_outstanding", "net_income", "equity",
                                              "ebitda", "net_debt"]},
                "warnings": warns, "limitations": lims}

    if intent == "company" and ticker:
        try:
            ins = generate_company_insight(ticker, state)
            sc = ins["score"]
            ans = (f"{ticker.upper()} ({sc.get('year')}): final research score {_fmt(sc.get('final_research_score'))} "
                   f"(ML {_fmt(sc.get('ml_score'))}, confidence {_fmt(sc.get('confidence_level'))}). "
                   f"Decision-support verdict: {sc.get('decision_support_verdict')}. Research support only.")
            return {"answer": ans, "data_used": {"source": "company score", "year": sc.get("year"),
                    "rows_used": 1, "fields_used": ["ml_score", "confidence_score", "final_research_score"]},
                    "warnings": warns, "limitations": lims}
        except Exception:
            return None
    return None


def answer_research_question(question: str, ticker: str | None = None,
                            max_context_tokens: int | None = None, state: dict | None = None) -> dict:
    state = state or load_research_state()
    cfg = get_config()
    intent = classify_intent(question)
    if intent == "general" and ticker:
        intent = "company"

    det = _intent_answer(intent, question, state, ticker)

    # compact context for the LLM: only what the intent needs
    ctx: dict[str, Any] = {"summary": build_summary_context(state),
                           "diagnostics": build_model_diagnostics_context(state),
                           "corrected_yearly_status": get_corrected_yearly_status(state)}
    if det and det.get("intent_data") is not None:
        ctx["intent_data"] = det["intent_data"]
    if det and det.get("answer"):
        ctx["grounded_answer"] = det["answer"]
    if ticker:
        try:
            ctx["company"] = build_company_context(ticker, state)
        except (KeyError, ValueError) as exc:
            ctx["company_error"] = str(exc)

    llm_result, fallback, llm_error = None, True, None
    if cfg["provider"] != "none":
        msg = [{"role": "system", "content": SYSTEM_PROMPT},
               {"role": "user", "content": json.dumps({"question": question, "intent": intent, "context": ctx})}]
        res = call_local_llm(msg, cfg)
        if res.get("ok"):
            parsed = _parse_llm_json(res["content"])
            if parsed:
                llm_result, fallback = parsed, False
            else:
                llm_error = "LLM output could not be parsed into valid JSON; deterministic fallback used"
        else:
            llm_error = res.get("error")

    warns = (det or {}).get("warnings") or _company_warnings(state)
    lims = (det or {}).get("limitations") or _limitations(warns)
    llm_used = (llm_result is not None) and (not fallback)
    if llm_result is None:
        llm_result = _coerce_llm_result({
            "llm_research_score": None, "llm_confidence": confidence_score(state)["confidence_level"],
            "summary": (det or {}).get("answer") or _general_summary(ctx["summary"]),
            "reasoning": "Generated from validated project reports (AI assistant not used for this answer).",
            "warnings": warns, "limitations": lims,
        })

    grounded = (det or {}).get("answer")    # exact facts (tickers/returns) when present
    # Fact-bearing intents keep the exact grounded headline; the AI adds interpretation.
    # Explanatory intents let the AI phrase the headline (richer, still grounded in context).
    FACT_INTENTS = {"benchmark_outperformers", "top_ranked", "benchmark_status"}
    if llm_used and intent not in FACT_INTENTS and (llm_result.get("summary") or "").strip():
        answer = llm_result["summary"]
    else:
        answer = grounded or _human_answer(llm_result)

    return {
        "answer": answer,
        "grounded_answer": grounded,
        "intent": intent,
        "mode": "llm" if llm_used else "fallback",
        "llm_used": llm_used,
        "model": cfg["model"] if llm_used else None,
        "data_used": (det or {}).get("data_used", {"source": "validated reports", "year": None,
                      "rows_used": 0, "fields_used": []}),
        "llm_result": llm_result,
        "context_used_summary": sorted(ctx.keys()),
        "warnings": warns,
        "limitations": lims,
        "provider_used": cfg["provider"], "fallback_used": fallback, "llm_error": llm_error,
        "diagnostics": provider_diagnostics(cfg, cfg["provider"], fallback, llm_error),
        "disclaimer": "This is research support, not investment advice.",
    }


def _general_summary(s: dict) -> str:
    bench = "available" if s["benchmark_available"] else "missing"
    return (f"The validated dataset has {s['feature_count']} year-end features across {s['rows']} company-years, "
            f"with the BIST100 market benchmark {bench}. Ask about benchmark outperformers, top-ranked "
            "companies, accepted/rejected data, or why the model signal is still weak.")
