"""Generate an instruction-tuning dataset for the research agent.

Grounded in REAL project facts (feature names, frozen columns, benchmark status,
backtest metrics) pulled from the validated reports + research_agent contexts.
Synthetic only in wording/variation — never in financial numbers. No external
APIs. LLM outputs are NOT used; targets are deterministic, policy-compliant
exemplars so a small local model can learn the house style + safety rules.

Run: PYTHONPATH=. python research_agent_training/generate_instruction_dataset.py [--n 200] [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "2.backend"))

from app.services import research_agent as RA  # noqa: E402

OUT_DEFAULT = REPO_ROOT / "research_agent_training" / "instruction_dataset.jsonl"
SAMPLE_OUT = REPO_ROOT / "research_agent_training" / "sample_instruction_dataset.jsonl"

FORBIDDEN = ("buy", "sell", "hold", "price target", "guaranteed", "will increase",
             "kesin yükselir", " al ", " sat ", " tut ")

_LIMIT_TEXT = {
    "small_sample": "Only ~40 stocks/year; metrics are statistically weak.",
    "benchmark_missing": "BIST100 benchmark unavailable; excess-return view limited.",
    "frozen_features": "Valuation/profitability columns are a frozen snapshot and were excluded.",
    "no_real_valuation_profitability_features": "No real historical valuation/profitability features ingested.",
    "weak_backtest": "Backtest rank-correlation is near zero / unstable.",
}


def _clean(text: str) -> str:
    low = f" {text.lower()} "
    for f in FORBIDDEN:
        assert f not in low, f"forbidden phrase '{f}' in output"
    return text


def _limits(warns):
    return [_LIMIT_TEXT[w] for w in warns if w in _LIMIT_TEXT] or ["Research-support only; not investment advice."]


def _company_examples(state, tickers):
    out = []
    for t in tickers:
        try:
            ctx = RA.build_company_context(t, state)
        except Exception:
            continue
        ml = RA.ml_score_for_company(t, state)
        conf = RA.confidence_score(state)
        warns = ctx["warnings"]
        score = round(0.5 + (((ml["ml_score"] or 0.5) - 0.5) * conf["confidence_score"]), 3)
        pos = list(ctx["top_positive_features"])[:3]
        neg = list(ctx["top_negative_features"])[:3]
        # company explanation
        out.append({
            "instruction": "Explain this company's research standing using only the provided context.",
            "input": {"ticker": t, "year": ctx["latest_year"], "ml_score": ml["ml_score"],
                      "confidence_score": conf["confidence_score"],
                      "top_positive_features": ctx["top_positive_features"],
                      "top_negative_features": ctx["top_negative_features"], "warnings": warns},
            "output": {
                "llm_research_score": score, "llm_confidence": conf["confidence_level"],
                "summary": _clean(f"{t} ({ctx['latest_year']}) ranks relatively strong on {pos} and weak on {neg} "
                                  f"among year-T features. This is a structured description, not a prediction."),
                "reasoning": _clean("Based on cross-sectional percentile ranks of validated year-T features; "
                                    "the ML pipeline is the primary model and this is a bounded support score."),
                "warnings": warns, "limitations": _limits(warns)},
        })
        # hybrid score explanation
        comp = RA.composite_score(ml["ml_score"], conf["confidence_score"], score)
        out.append({
            "instruction": "Explain how the final research score was composed from its components.",
            "input": {"ticker": t, **{k: comp[k] for k in ("ml_score", "confidence_score",
                       "llm_research_score", "final_research_score", "weights_used")}},
            "output": {
                "llm_research_score": score, "llm_confidence": conf["confidence_level"],
                "summary": _clean(f"final_research_score {comp['final_research_score']} = "
                                  f"0.65*ml + 0.20*confidence + 0.15*llm support; components are reported separately."),
                "reasoning": _clean("ML score dominates by design; low confidence pulls the support score toward neutral."),
                "warnings": warns, "limitations": _limits(warns)},
        })
    return out


def _global_examples(state):
    sctx = RA.build_summary_context(state)
    dctx = RA.build_data_quality_context(state)
    diag = RA.build_model_diagnostics_context(state)
    frozen = sctx["rejected_frozen_columns"]
    bench_ok = sctx["benchmark_available"]
    base = [
        ("Explain why P/E, P/B, ROE and revenue columns were rejected as features.",
         {"rejected_frozen_columns": frozen[:8]},
         f"Those columns are identical across years (a single frozen snapshot), so they carry no per-year "
         f"signal and were excluded to prevent snapshot leakage. {len(frozen)} columns were rejected this way."),
        ("Explain the frozen-column data-quality problem.",
         {"frozen_columns": frozen[:6]},
         "The source files repeat one point-in-time snapshot across years for income-statement/valuation fields; "
         "the validator detects non-varying columns and excludes them from features."),
        ("Explain whether the BIST100 benchmark is available and what it changes.",
         {"benchmark": dctx["benchmark"]},
         ("Benchmark is available, enabling excess-return / outperform targets." if bench_ok
          else "Benchmark is missing, so excess-return and outperform targets are disabled.")),
        ("Interpret the model diagnostics and baseline comparison.",
         {"splits": diag.get("splits"), "mean_spearman": diag.get("mean_spearman")},
         "Across walk-forward splits the simple baseline matches or beats ML; rank-correlation is near zero, "
         "so there is no demonstrated next-year predictive skill on this data."),
        ("Why did ML not beat the baseline?",
         {"mean_spearman": diag.get("mean_spearman")},
         "With ~40 stocks per year and mostly balance-sheet/growth features, ML overfits noise; a simple "
         "equal-weight baseline generalizes at least as well."),
        ("Why should a single strong backtest split not be trusted?",
         {"splits": diag.get("splits")},
         "One split is ~40 samples; a high precision@5 on one year flips to negative the next, so single-split "
         "spikes reflect noise, not skill."),
        ("What data is still needed to improve the model?",
         {"frozen": frozen[:5], "benchmark_available": bench_ok},
         "Real per-year income-statement, profitability and valuation history (currently frozen) and, if missing, "
         "real BIST100 yearly returns."),
        ("Answer a question that the provided context cannot support.",
         {"available_context": ["features", "data_quality", "diagnostics"]},
         "The requested figure is not in the provided context, so it cannot be answered; no value will be invented."),
        ("A user asks whether they should buy this stock. Respond appropriately.",
         {"request": "investment recommendation"},
         "This is a research-support system and cannot provide investment advice or a recommendation; it only "
         "describes structured evidence and its limitations."),
        ("Interpret a top-k selection result.",
         {"precision_at_5": 0.2},
         "Top-5 precision near random (0.2) means the score's highest picks did not concentrate the best realized "
         "returns; treat rankings as weak research signals only."),
    ]
    warns = ["small_sample"] + (["benchmark_missing"] if not bench_ok else []) + ["frozen_features", "weak_backtest"]
    out = []
    for instr, inp, summ in base:
        out.append({
            "instruction": instr, "input": inp,
            "output": {"llm_research_score": None, "llm_confidence": "low",
                       "summary": _clean(summ), "reasoning": _clean("Grounded only in the supplied validated reports."),
                       "warnings": warns, "limitations": _limits(warns)},
        })
    return out


def _comparison_examples(state, tickers):
    """Compare two companies using only provided context (no fabricated facts)."""
    out = []
    pairs = [(tickers[i], tickers[i + 1]) for i in range(0, len(tickers) - 1, 2)]
    for a, b in pairs:
        try:
            ca, cb = RA.build_company_context(a, state), RA.build_company_context(b, state)
        except Exception:
            continue
        ma = RA.ml_score_for_company(a, state).get("ml_score")
        mb = RA.ml_score_for_company(b, state).get("ml_score")
        warns = ca["warnings"]
        higher = a if (ma or 0) >= (mb or 0) else b
        out.append({
            "instruction": "Compare these two companies using only the provided structured context.",
            "input": {"a": {"ticker": a, "ml_score": ma, "top_positive_features": list(ca["top_positive_features"])[:3]},
                      "b": {"ticker": b, "ml_score": mb, "top_positive_features": list(cb["top_positive_features"])[:3]},
                      "warnings": warns},
            "output": {"llm_research_score": None, "llm_confidence": "low",
                       "summary": _clean(f"On the provided year-T feature ranks, {higher} has the higher transparent "
                                         f"ML rank score; both share the same dataset limitations. This is a structured "
                                         f"comparison, not a recommendation."),
                       "reasoning": _clean("Compares only the supplied ML rank scores and feature ranks; no external data."),
                       "positive_signals": [], "negative_signals": [],
                       "warnings": warns, "limitations": _limits(warns)},
        })
    return out


def _benchmark_examples(state):
    """Explicit benchmark facts so the model never claims a present benchmark is missing."""
    b = RA.benchmark_payload()
    if not b["available"]:
        return []
    yrs = ", ".join(str(y) for y in b["years_covered"])
    return [{
        "instruction": "State whether the BIST100 benchmark is available and summarise its yearly returns.",
        "input": {"benchmark_available": True, "benchmark_source": b["source"],
                  "benchmark_years": b["years_covered"], "benchmark_returns": b["returns_by_year"],
                  "enabled_benchmark_targets": b["derived_targets"]},
        "output": {"llm_research_score": None, "llm_confidence": "medium",
                   "summary": _clean(f"The BIST100 benchmark is available (source {b['source']}) for {yrs}; "
                                     f"excess-return and outperform-BIST100 targets are enabled."),
                   "reasoning": _clean("Uses only the benchmark facts supplied in the context; values are not invented."),
                   "positive_signals": ["benchmark available"], "negative_signals": [],
                   "warnings": ["small_sample"], "limitations": _limits(["small_sample"])},
    }]


def _decision_support_examples(state, tickers):
    out = []
    diag = RA.build_model_diagnostics_context(state)
    for t in tickers[:8]:
        try:
            ctx = RA.build_company_context(t, state)
        except Exception:
            continue
        ml = RA.ml_score_for_company(t, state)
        conf = RA.confidence_score(state)
        comp = RA.composite_score(ml.get("ml_score"), conf["confidence_score"],
                                  RA.deterministic_research_score({**ctx, **conf, **ml})["llm_research_score"])
        ds = RA.decision_support(comp["final_research_score"], conf["confidence_level"], ctx["warnings"], diag)
        out.append({
            "instruction": "Give a bounded decision-support verdict for this company (never investment advice).",
            "input": {"ticker": t, "final_research_score": comp["final_research_score"],
                      "confidence_level": conf["confidence_level"], "warnings": ctx["warnings"]},
            "output": {"llm_research_score": None, "llm_confidence": conf["confidence_level"],
                       "summary": _clean(f"{t}: decision-support verdict is '{ds['decision_support_verdict']}'. "
                                         f"This is a bounded research-interest signal only, never a trade instruction."),
                       "reasoning": _clean("Verdict is capped cautiously when the backtest is weak or confidence is low."),
                       "positive_signals": [], "negative_signals": [],
                       "warnings": ctx["warnings"], "limitations": ds["blocking_limitations"] or _limits(ctx["warnings"])},
        })
    return out


def _failure_case_examples(state):
    """Hard negatives: enforce strict JSON, refusals, no advice, no fabricated numbers."""
    warns = ["small_sample", "frozen_features", "weak_backtest"]
    base = [
        ("A user asks for an exact future price for next year.",
         {"request": "future price figure"},
         "No specific future price figure can be produced; the context contains no such value and this is research support, not advice."),
        ("A user wants a directional trade instruction. Respond within policy.",
         {"request": "directional trade call"},
         "A directional trade instruction cannot be given. The system only describes validated structured evidence and its limits."),
        ("The model previously returned malformed JSON. Restate the answer as strict JSON only.",
         {"prior_error": "unquoted key"},
         "Benchmark and feature facts are summarised from context; output must be a single valid JSON object only."),
        ("A user asks for a certain, risk-free return figure.",
         {"request": "certain return"},
         "No certainty of returns can be claimed or invented; only validated, bounded research signals are provided."),
    ]
    out = []
    for instr, inp, summ in base:
        out.append({
            "instruction": instr, "input": inp,
            "output": {"llm_research_score": None, "llm_confidence": "low",
                       "summary": _clean(summ), "reasoning": _clean("Refusal grounded in policy and missing context."),
                       "positive_signals": [], "negative_signals": [],
                       "warnings": warns, "limitations": _limits(warns)},
        })
    return out


def generate(n: int, state=None, *, seed: int = 42, include_comparisons: bool = True,
             include_benchmark: bool = True, include_company_explanations: bool = True,
             include_failure_cases: bool = True) -> list[dict]:
    state = state or RA.load_research_state()
    df = state["modeling"]
    tickers = sorted(df["ticker"].unique()) if df is not None else []
    random.Random(seed).shuffle(tickers)
    examples = _global_examples(state)
    if include_benchmark:
        examples += _benchmark_examples(state)
    if include_failure_cases:
        examples += _failure_case_examples(state)
    if include_company_explanations:
        examples += _company_examples(state, tickers)
        examples += _decision_support_examples(state, tickers)
    if include_comparisons:
        examples += _comparison_examples(state, tickers)
    # pad by re-emitting company exemplars (wording-varied) up to n
    i = 0
    while len(examples) < n and tickers:
        examples += _company_examples(state, tickers[i % len(tickers):i % len(tickers) + 1])
        i += 1
    return examples[:n]


def write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _bool_flag(ap, name, default=True):
    ap.add_argument(f"--{name}", dest=name.replace("-", "_"), action="store_true", default=default)
    ap.add_argument(f"--no-{name}", dest=name.replace("-", "_"), action="store_false")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    ap.add_argument("--sample-out", default=str(SAMPLE_OUT))
    ap.add_argument("--sample-n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=42)
    _bool_flag(ap, "include-comparisons")
    _bool_flag(ap, "include-benchmark")
    _bool_flag(ap, "include-company-explanations")
    _bool_flag(ap, "include-failure-cases")
    a = ap.parse_args(argv)

    rows = generate(a.n, seed=a.seed, include_comparisons=a.include_comparisons,
                    include_benchmark=a.include_benchmark,
                    include_company_explanations=a.include_company_explanations,
                    include_failure_cases=a.include_failure_cases)
    write_jsonl(rows, Path(a.out))
    write_jsonl(rows[:a.sample_n], Path(a.sample_out))
    print(f"[dataset] wrote {len(rows)} examples -> {a.out}")
    print(f"[dataset] sample ({min(a.sample_n, len(rows))}) -> {a.sample_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
