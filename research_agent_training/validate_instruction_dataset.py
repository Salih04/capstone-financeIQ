"""Validate a research-agent instruction dataset (JSONL).

Checks structure, score/confidence ranges, forbidden-advice words, and that
required limitations surface when the input context implies them. Exits non-zero
on any hard failure so it can gate `make`.

Run: PYTHONPATH=. python research_agent_training/validate_instruction_dataset.py [--in FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IN = REPO_ROOT / "research_agent_training" / "instruction_dataset.jsonl"

REQUIRED_TOP = ("instruction", "input", "output")
REQUIRED_OUT = ("llm_research_score", "llm_confidence", "summary")
VALID_CONF = ("low", "medium", "high")
FORBIDDEN = ("buy", "sell", "hold", "price target", "guaranteed", "kesin yükselir")
# token-boundary forbidden (avoid matching 'wall', 'salt'): checked with spaces
FORBIDDEN_TOKENS = (" al ", " sat ", " tut ")

# If the input context contains these signals, the output must mention the matching limitation theme.
REQUIRED_WHEN = {
    "small_sample": ("small sample", "~40", "40 stock"),
    "frozen": ("frozen", "snapshot"),
    "weak_backtest": ("weak", "near zero", "unstable", "no demonstrated"),
    "benchmark_missing": ("benchmark", "missing", "unavailable"),
}


def _text_of(output: dict) -> str:
    parts = [str(output.get("summary", "")), str(output.get("reasoning", ""))]
    for k in ("warnings", "limitations", "positive_signals", "negative_signals"):
        v = output.get(k)
        if isinstance(v, list):
            parts.extend(str(x) for x in v)
    return " ".join(parts).lower()


def _input_blob(inp) -> str:
    try:
        return json.dumps(inp, ensure_ascii=False).lower()
    except Exception:
        return str(inp).lower()


def validate_row(row: dict) -> list[str]:
    errs = []
    for k in REQUIRED_TOP:
        if k not in row:
            errs.append(f"missing top key '{k}'")
    out = row.get("output", {})
    if not isinstance(out, dict):
        return errs + ["output is not an object"]
    for k in REQUIRED_OUT:
        if k not in out:
            errs.append(f"missing output key '{k}'")

    score = out.get("llm_research_score")
    if score is not None and not (isinstance(score, (int, float)) and 0.0 <= float(score) <= 1.0):
        errs.append(f"llm_research_score out of [0,1]: {score!r}")
    if out.get("llm_confidence") not in VALID_CONF:
        errs.append(f"invalid llm_confidence: {out.get('llm_confidence')!r}")

    text = _text_of(out)
    spaced = f" {text} "
    for w in FORBIDDEN:
        if w in text:
            errs.append(f"forbidden advice phrase: '{w}'")
    for w in FORBIDDEN_TOKENS:
        if w in spaced:
            errs.append(f"forbidden advice token: '{w.strip()}'")

    if len(str(out.get("summary", ""))) > 600:
        errs.append("summary too long (>600 chars)")

    blob = _input_blob(row.get("input", {}))
    for key, needles in REQUIRED_WHEN.items():
        present = key in blob or (key == "benchmark_missing" and ("benchmark_available\": false" in blob or "missing" in blob))
        if present and not any(n in text for n in needles):
            # benchmark present-and-available is fine; only require when truly missing/flagged
            if key == "benchmark_missing" and ("benchmark_available\": true" in blob or "returns" in blob):
                continue
            errs.append(f"required limitation theme '{key}' not surfaced in output")
    return errs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="inp", default=str(DEFAULT_IN))
    ap.add_argument("--max-report", type=int, default=20)
    a = ap.parse_args(argv)

    path = Path(a.inp)
    if not path.is_file():
        print(f"[validate] FAIL: file not found: {path}")
        return 2

    total, bad = 0, 0
    reported = 0
    for ln, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        total += 1
        try:
            row = json.loads(line)
        except Exception as exc:
            bad += 1
            if reported < a.max_report:
                print(f"[validate] line {ln}: JSON parse error: {exc}")
                reported += 1
            continue
        errs = validate_row(row)
        if errs:
            bad += 1
            if reported < a.max_report:
                print(f"[validate] line {ln}: " + "; ".join(errs))
                reported += 1

    ok = total - bad
    print(f"[validate] {ok}/{total} rows valid; {bad} failed.")
    if total == 0:
        print("[validate] FAIL: empty dataset")
        return 2
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
