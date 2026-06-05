"""Research-agent service: constrained, local-LLM-assisted research support.

The structured ML pipeline stays the primary numeric model. This layer only
READS validated structured evidence and produces cautious, bounded research
support: deterministic summaries + scores always, optional local-LLM commentary
when a provider is configured. It never predicts prices/returns, never gives
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

NOT_ADVICE = ("This is a research-support score, NOT investment advice. The LLM is a "
              "decision-support layer, not the numerical predictor.")

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
    base = os.environ.get("RESEARCH_LLM_BASE_URL") or (
        "http://localhost:1234/v1/chat/completions" if provider == "lmstudio"
        else "http://localhost:11434/api/chat" if provider == "ollama" else "")
    w_ml = _env_float("RESEARCH_SCORE_ML_WEIGHT", 0.65)
    w_conf = _env_float("RESEARCH_SCORE_CONFIDENCE_WEIGHT", 0.20)
    w_llm = _env_float("RESEARCH_SCORE_LLM_WEIGHT", 0.15)
    return {
        "provider": provider, "base_url": base,
        "model": os.environ.get("RESEARCH_LLM_MODEL", "local-model"),
        "timeout": _env_float("RESEARCH_LLM_TIMEOUT_SECONDS", 15.0),
        "weights": {"ml": w_ml, "confidence": w_conf, "llm": w_llm},
    }


SYSTEM_PROMPT = """You are a cautious financial RESEARCH-SUPPORT assistant for a capstone project.

STRICT RULES:
- Use ONLY the structured context provided in the user message. Do not use outside knowledge or external data.
- Do NOT invent or estimate any financial fact, number, price, or return not present in the context.
- Do NOT give investment advice. Never output buy, sell, hold, al, sat, or tut.
- Do NOT output a price target or an exact expected return unless that exact value is in the provided model output.
- The structured ML pipeline is the primary predictor; your llm_research_score is only a bounded support signal in [0,1], distinct from the ML score.
- ALWAYS surface the relevant limitations present in the context: small sample size, missing BIST100 benchmark, frozen valuation/profitability data, missing real historical financials, weak/unstable backtest metrics.
- State that this is a research-support system, not an investment recommendation.

Respond with a single JSON object:
{"llm_research_score": 0.0-1.0, "llm_confidence": "low|medium|high",
 "summary": "...", "reasoning": "...", "positive_signals": ["..."],
 "negative_signals": ["..."], "warnings": ["..."], "limitations": ["..."]}
Output JSON only, no prose around it."""


# --------------------------------------------------------------------------- #
# state loading
# --------------------------------------------------------------------------- #
def _load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text()) if p.is_file() else {}
    except Exception:
        return {}


def load_research_state() -> dict:
    state: dict[str, Any] = {
        "modeling_available": MODELING_CSV.is_file(),
        "quality": _load_json(QUALITY_JSON),
        "migration": _load_json(MIGRATION_JSON),
        "leaderboard": None,
        "modeling": None,
        "model_outputs": None,
    }
    if MODELING_CSV.is_file():
        state["modeling"] = pd.read_csv(MODELING_CSV)
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
        "valid_for_modeling": q.get("valid_for_T_to_T1_modeling"),
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
        "manual_rejected": man.get("rejected_feature_columns", {}),
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
def call_local_llm(messages: list[dict], cfg: dict | None = None) -> dict:
    cfg = cfg or get_config()
    if cfg["provider"] == "none" or not cfg["base_url"]:
        return {"ok": False, "provider": "none", "error": "no provider configured"}
    try:
        if cfg["provider"] == "ollama":
            payload = {"model": cfg["model"], "messages": messages, "stream": False,
                       "options": {"temperature": 0.2}}
        else:  # lmstudio / openai-compatible
            payload = {"model": cfg["model"], "messages": messages, "temperature": 0.2}
        req = urllib.request.Request(
            cfg["base_url"], data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=cfg["timeout"]) as r:
            data = json.loads(r.read().decode())
        if cfg["provider"] == "ollama":
            content = data.get("message", {}).get("content", "")
        else:
            content = data["choices"][0]["message"]["content"]
        return {"ok": True, "provider": cfg["provider"], "content": content}
    except Exception as exc:  # noqa - fail safe, never crash the endpoint
        return {"ok": False, "provider": cfg["provider"], "error": str(exc)}


def _parse_llm_json(content: str) -> dict | None:
    try:
        start, end = content.find("{"), content.rfind("}")
        if start < 0 or end < 0:
            return None
        obj = json.loads(content[start:end + 1])
        s = obj.get("llm_research_score")
        if isinstance(s, (int, float)):
            obj["llm_research_score"] = max(0.0, min(1.0, float(s)))
        else:
            obj["llm_research_score"] = None
        if obj.get("llm_confidence") not in ("low", "medium", "high"):
            obj["llm_confidence"] = "low"
        return obj
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# composite (PHASE 7)
# --------------------------------------------------------------------------- #
def composite_score(ml_score, confidence_score_v, llm_research_score, cfg: dict | None = None) -> dict:
    cfg = cfg or get_config()
    w = cfg["weights"]
    notes = []
    comps = {"ml": (ml_score, w["ml"]), "confidence": (confidence_score_v, w["conf"] if "conf" in w else w["confidence"]),
             "llm": (llm_research_score, w["llm"])}
    # redistribute weight of any null component across present ones
    present = {k: (v, wt) for k, (v, wt) in comps.items() if v is not None}
    if ml_score is None:
        notes.append("ml_score null -> weight redistributed; result is a partial_score")
    total_w = sum(wt for _, wt in present.values()) or 1.0
    final = round(sum(v * wt for v, wt in present.values()) / total_w, 3) if present else None
    return {
        "ml_score": ml_score,
        "confidence_score": confidence_score_v,
        "llm_research_score": llm_research_score,
        "final_research_score": final,
        "partial_score": ml_score is None,
        "weights_used": {"ml": w["ml"], "confidence": w["confidence"], "llm": w["llm"]},
        "scoring_notes": notes or ["all components present"],
        "disclaimer": NOT_ADVICE,
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

    cfg = get_config()
    llm_out, fallback = None, True
    if cfg["provider"] != "none":
        msg = [{"role": "system", "content": SYSTEM_PROMPT},
               {"role": "user", "content": json.dumps({"task": "company_insight", "context": ctx_for_score})}]
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
    # Flat, explicit score block (PHASE 5 contract) — components never hidden.
    score = {
        "ticker": ctx["ticker"], "year": ctx["latest_year"],
        "score_source": ml.get("score_source"), "target_name": ml.get("target_name"),
        "model_name": ml.get("model_name"), "ml_rank": ml.get("ml_rank"),
        "ml_score": comp["ml_score"], "confidence_score": comp["confidence_score"],
        "llm_research_score": comp["llm_research_score"],
        "final_research_score": comp["final_research_score"],
        "partial_score": comp["partial_score"], "weights_used": comp["weights_used"],
        "confidence_level": conf["confidence_level"], "confidence_reasons": conf["confidence_reasons"],
        "reasoning": llm_out.get("reasoning"), "warnings": ctx["warnings"],
        "limitations": llm_out.get("limitations"), "scoring_notes": comp["scoring_notes"],
        "not_investment_advice": True,
    }
    return {
        "ticker": ctx["ticker"], "context": ctx, "ml": ml, "confidence": conf,
        "llm": llm_out, "score": score, "provider_used": cfg["provider"],
        "fallback_used": fallback, "disclaimer": NOT_ADVICE, "not_investment_advice": True,
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
    summary, fallback = None, True
    if cfg["provider"] != "none":
        msg = [{"role": "system", "content": SYSTEM_PROMPT},
               {"role": "user", "content": json.dumps({"task": "summary", "context": {**ctx, **conf, "diagnostics": diag}})}]
        res = call_local_llm(msg, cfg)
        if res.get("ok"):
            parsed = _parse_llm_json(res["content"])
            if parsed:
                summary, fallback = parsed, False
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
            "provider_used": cfg["provider"], "fallback_used": fallback, "disclaimer": NOT_ADVICE}


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


def answer_research_question(question: str, ticker: str | None = None,
                            max_context_tokens: int | None = None, state: dict | None = None) -> dict:
    state = state or load_research_state()
    cfg = get_config()
    ctx: dict[str, Any] = {"summary": build_summary_context(state),
                           "data_quality": build_data_quality_context(state),
                           "diagnostics": build_model_diagnostics_context(state)}
    if ticker:
        try:
            ctx["company"] = build_company_context(ticker, state)
        except (KeyError, ValueError) as exc:
            ctx["company_error"] = str(exc)

    answer, fallback = None, True
    if cfg["provider"] != "none":
        msg = [{"role": "system", "content": SYSTEM_PROMPT},
               {"role": "user", "content": json.dumps({"question": question, "context": ctx})}]
        res = call_local_llm(msg, cfg)
        if res.get("ok"):
            answer, fallback = res["content"], False
    if answer is None:
        answer = ("[deterministic fallback — no LLM configured] Based only on validated reports: "
                  f"{ctx['summary']['feature_count']} year-T features, benchmark "
                  f"{'available' if ctx['summary']['benchmark_available'] else 'missing'}, "
                  f"{len(ctx['summary']['rejected_frozen_columns'])} frozen columns excluded, small sample. "
                  "No price/return prediction and no investment advice can be given.")
    return {
        "answer": answer,
        "context_used_summary": {k: (list(v) if isinstance(v, dict) else v) for k, v in ctx.items()},
        "warnings": _company_warnings(state),
        "provider_used": cfg["provider"], "fallback_used": fallback,
        "disclaimer": NOT_ADVICE,
    }
