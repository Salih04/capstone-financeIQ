"""Group eval failure cases and emit a corrective (failure-augmented) dataset.

Reads failure_cases.jsonl (from evaluate_local_llm.py), buckets failures by
type, and writes corrective instruction examples that demonstrate the correct,
policy-compliant output for exactly those failure modes. These are GROUNDED
exemplars (no fabricated financial facts) intended for the next LoRA iteration.

Run: PYTHONPATH=. python research_agent_training/collect_failure_cases.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "2.backend"))

from app.services import research_agent as RA  # noqa: E402

OUT_DIR = REPO_ROOT / "research_agent_training"
FAILURE_CASES = OUT_DIR / "failure_cases.jsonl"
AUGMENTED = OUT_DIR / "failure_augmented_dataset.jsonl"

_LIMITS = ["Only ~40 stocks/year; metrics are statistically weak.",
           "Valuation/profitability columns are a frozen snapshot and were excluded.",
           "Backtest rank-correlation is near zero / unstable."]
_WARN = ["small_sample", "frozen_features", "weak_backtest"]


def _benchmark_exemplar():
    b = RA.benchmark_payload()
    yrs = ", ".join(str(y) for y in b["years_covered"]) or "n/a"
    avail = "available" if b["available"] else "missing"
    return {
        "instruction": "State whether the BIST100 benchmark is available; do not claim it is missing if it is present.",
        "input": {"benchmark_available": b["available"], "benchmark_years": b["years_covered"],
                  "benchmark_returns": b["returns_by_year"]},
        "output": {"llm_research_score": None, "llm_confidence": "medium",
                   "summary": f"The BIST100 benchmark is {avail} for {yrs}; values come only from the provided context.",
                   "reasoning": "Uses supplied benchmark facts; no years or values are invented.",
                   "positive_signals": [], "negative_signals": [],
                   "warnings": ["small_sample"], "limitations": _LIMITS[:1]},
    }


def _strict_json_exemplar():
    return {
        "instruction": "Return your answer as a single valid JSON object only, with every key double-quoted.",
        "input": {"prior_error": "unquoted key / trailing comma / prose around JSON"},
        "output": {"llm_research_score": None, "llm_confidence": "low",
                   "summary": "Output is a single JSON object; no markdown, no prose, all keys double-quoted.",
                   "reasoning": "Strict JSON is required so the backend can parse the response deterministically.",
                   "positive_signals": [], "negative_signals": [],
                   "warnings": _WARN, "limitations": _LIMITS},
    }


def _refusal_exemplar():
    return {
        "instruction": "A user demands a directional trade instruction or a certain return. Respond within policy.",
        "input": {"request": "investment advice"},
        "output": {"llm_research_score": None, "llm_confidence": "low",
                   "summary": "This is a research-support system and cannot provide investment advice, a "
                              "directional trade instruction, a specific future price, or any certainty of returns.",
                   "reasoning": "Only validated structured evidence and its limitations are described.",
                   "positive_signals": [], "negative_signals": [],
                   "warnings": _WARN, "limitations": _LIMITS},
    }


def _warning_exemplar():
    return {
        "instruction": "Explain what data is still needed; always surface the dataset limitations.",
        "input": {"frozen": True, "small_sample": True, "weak_backtest": True},
        "output": {"llm_research_score": None, "llm_confidence": "low",
                   "summary": "Real per-year valuation/profitability history is needed; current columns are a "
                              "frozen snapshot, the sample is small (~40/year) and the backtest is weak.",
                   "reasoning": "Names the concrete blocking limitations from the context.",
                   "positive_signals": [], "negative_signals": [],
                   "warnings": _WARN, "limitations": _LIMITS},
    }


FIXERS = {
    "hallucinated_benchmark": _benchmark_exemplar,
    "parse_error": _strict_json_exemplar,
    "score_out_of_range": _strict_json_exemplar,
    "confidence_invalid": _strict_json_exemplar,
    "forbidden_advice_found": _refusal_exemplar,
    "missing_required_warning": _warning_exemplar,
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="inp", default=str(FAILURE_CASES))
    ap.add_argument("--per-type", type=int, default=8)
    a = ap.parse_args(argv)

    path = Path(a.inp)
    if not path.is_file():
        print(f"[collect] no failure cases file at {path}; nothing to augment.")
        AUGMENTED.write_text("")
        return 0

    counts = Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            fc = json.loads(line)
        except Exception:
            continue
        flags = fc.get("flags", {})
        for k, v in flags.items():
            if v and k in FIXERS:
                counts[k] += 1
        if fc.get("error"):
            counts["parse_error"] += 1

    rows = []
    if not counts:
        # no targeted failures — emit the strict-JSON + refusal baseline anyway
        counts.update({"parse_error": 1, "forbidden_advice_found": 1})
    for ftype, c in counts.items():
        maker = FIXERS.get(ftype)
        if not maker:
            continue
        for _ in range(min(a.per_type, max(1, c))):
            rows.append(maker())

    with AUGMENTED.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[collect] failure types: {dict(counts)}")
    print(f"[collect] wrote {len(rows)} corrective examples -> {AUGMENTED.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
