"""AutoResearch iteration builder — one self-improving loop, NO training.

Pipeline:
  1. generate instruction dataset (grounded in real project facts)
  2. validate it
  3. optionally evaluate the local LLM (if a provider is reachable)
  4. collect failure cases -> corrective dataset
  5. write an iteration report + a merged next-iteration dataset

It never trains and never downloads a model. The merged dataset is what you
later feed to autoresearch-mlx for LoRA instruction tuning.

Run: PYTHONPATH=. python research_agent_training/build_autoresearch_iteration.py [--n 1000] [--eval]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TRAIN_DIR = REPO_ROOT / "research_agent_training"
PY = sys.executable


def _run(args: list[str]) -> tuple[int, str]:
    env_note = " ".join(args)
    print(f"[iter] $ {env_note}")
    p = subprocess.run([PY, *args], cwd=str(REPO_ROOT), capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    print(out.strip())
    return p.returncode, out.strip()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--eval", action="store_true", help="run local-LLM eval if a provider is reachable")
    a = ap.parse_args(argv)

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    it_dir = TRAIN_DIR / "iterations" / f"iteration_{stamp}"
    it_dir.mkdir(parents=True, exist_ok=True)
    dataset = it_dir / "instruction_dataset.jsonl"
    sample = it_dir / "sample.jsonl"

    log = {}
    rc, out = _run(["research_agent_training/generate_instruction_dataset.py",
                    "--n", str(a.n), "--out", str(dataset), "--sample-out", str(sample)])
    log["generate"] = {"rc": rc, "out": out}

    rc_v, out_v = _run(["research_agent_training/validate_instruction_dataset.py", "--in", str(dataset)])
    log["validate"] = {"rc": rc_v, "out": out_v}

    if a.eval:
        rc_e, out_e = _run(["research_agent_training/evaluate_local_llm.py", "--in", str(dataset), "--n", "20"])
        log["evaluate"] = {"rc": rc_e, "out": out_e}
        rc_c, out_c = _run(["research_agent_training/collect_failure_cases.py"])
        log["collect"] = {"rc": rc_c, "out": out_c}

    # merge base + failure-augmented into the next-iteration dataset
    merged = it_dir / "next_iteration_dataset.jsonl"
    aug = TRAIN_DIR / "failure_augmented_dataset.jsonl"
    lines = dataset.read_text(encoding="utf-8").splitlines() if dataset.is_file() else []
    if aug.is_file():
        lines += [ln for ln in aug.read_text(encoding="utf-8").splitlines() if ln.strip()]
    merged.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = it_dir / "report.md"
    report.write_text("\n".join([
        f"# AutoResearch iteration {stamp}", "",
        "Prepares the next instruction dataset. **No training is performed here.**", "",
        f"- base dataset: `{dataset.name}` ({len(dataset.read_text().splitlines()) if dataset.is_file() else 0} rows)",
        f"- merged next-iteration dataset: `{merged.name}` ({len(lines)} rows)",
        f"- validation: {log['validate']['out'].splitlines()[-1] if log['validate']['out'] else 'n/a'}",
        f"- evaluation: {'run' if a.eval else 'skipped'}",
        "",
        "## Next step (manual, separate machine/time)",
        "Feed `next_iteration_dataset.jsonl` to autoresearch-mlx LoRA tuning on Qwen2.5-1.5B/3B.",
        "See `mlx_training_plan.md`.",
    ]), encoding="utf-8")
    (it_dir / "log.json").write_text(json.dumps(log, indent=2, ensure_ascii=False))

    print(f"[iter] iteration written -> {it_dir}")
    print(f"[iter] report: {report}")
    return 0 if rc_v == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
