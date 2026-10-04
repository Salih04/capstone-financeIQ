"""Stage PIT-v2: availability-aware point-in-time re-evaluation (post-hoc, registered).

Protocol: docs/PIT_PROTOCOL.md. Registration and the boundary between
pre-registered and post-hoc work: docs/PREREGISTRATION_AMENDMENT_2026-10-04.md.

Same nine models, metrics and walk-forward structure as the published harness
(imported from run_experiments.py), applied to the PIT panel built by
experiments/pit/panel.py. Inference uses the canonical within-split
permutation / bootstrap of experiments/significance.py. Writes only to
experiments/results_pit_v2/; the published results are never touched.

Run: PYTHONPATH=. python experiments/pit_v2_evaluation.py
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))
import run_experiments as rx  # noqa: E402
import significance as sig  # noqa: E402

from experiments.pit import config as cfg  # noqa: E402
from experiments.pit.guard import assert_labels_realized  # noqa: E402
from experiments.pit.panel import build_panel, ranked  # noqa: E402

TEST_FISCAL_YEARS = (2022, 2023, 2024)  # same three test cross-sections as the published splits


def walk_forward(panel) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = ranked(panel)
    feats = panel.features
    rows, preds = [], []
    for test_fy in TEST_FISCAL_YEARS:
        tr = data[data["fiscal_year"] < test_fy]
        te = data[data["fiscal_year"] == test_fy]
        assert_labels_realized(tr["label_end"], te["prediction_time"])
        Xtr, ytr = tr[feats].to_numpy(float), tr["target_return"].to_numpy(float)
        Xte, yte = te[feats].to_numpy(float), te["target_return"].to_numpy(float)
        split = f"test_fy{test_fy}"
        for name, (kind, fn) in rx.MODELS.items():
            yp = np.asarray(fn(Xtr, ytr, Xte), dtype=float)
            met = rx._metrics(yte, yp)
            rows.append({"split": split, "model": name, "kind": kind, "train_n": len(ytr),
                         **{k: v for k, v in met.items()}})
            ok = ~np.isnan(yp)
            preds.append(pd.DataFrame({"split": split, "year": test_fy + 1, "model": name,
                                       "ticker": te["ticker"].to_numpy()[ok],
                                       "y_true": yte[ok], "y_pred": yp[ok]}))
    return pd.DataFrame(rows), pd.concat(preds, ignore_index=True)


def infer(pred: pd.DataFrame) -> dict:
    out = {}
    for model in rx.MODELS:
        res = sig.analyze_model(pred[pred["model"] == model], permutations=cfg.N_PERMUTATIONS,
                                bootstraps=cfg.N_BOOTSTRAPS, seed=cfg.SEED)
        pooled = res["pooled"]
        out[model] = {
            "kind": rx.MODELS[model][0],
            "pooled_ic": pooled["observed_ic"],
            "permutation_p_two_sided": pooled["permutation_p_value_two_sided"],
            "bootstrap_ci_95": pooled["bootstrap_ci_95"],
            "n": pooled["n"],
            "by_split": {s["split"]: {"ic": s["observed_ic"], "n": s["n"],
                                      "p": s["permutation_p_value_two_sided"]}
                         for s in res["exploratory_by_split"]},
        }
        if model in cfg.ML_MODELS:
            out[model]["bonferroni_p"] = min(1.0, pooled["permutation_p_value_two_sided"] * len(cfg.ML_MODELS))
    return out


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git() -> dict:
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                                    capture_output=True, text=True, check=True).stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return {"sha": None, "dirty": None}
    return {"sha": sha, "dirty": dirty}


def run_spec(name: str, spec: dict, out: Path) -> dict:
    feature_set = spec["features"]
    panel = build_panel(spec["cutoff"], cfg.STANDARDIZED_CUTOFF_MODE, feature_set,
                        spec["exclude_quarantined"])
    lb, pred = walk_forward(panel)
    lb.to_csv(out / f"leaderboard_{name}.csv", index=False)
    pred.to_csv(out / f"predictions_{name}.csv", index=False, float_format="%.12g")
    n_by_split = pred[pred["model"] == cfg.PRIMARY_MODEL].groupby("split").size()
    mde = sig.minimum_detectable_ic(n_per_split=int(n_by_split.min()),
                                    split_count=int(len(n_by_split)))
    return {"specification": spec, "mode": cfg.STANDARDIZED_CUTOFF_MODE,
            "n_features": len(panel.features), "features": panel.features,
            "panel": panel.report,
            "test_rows_by_split": {k: int(v) for k, v in n_by_split.items()},
            "minimum_detectable_abs_ic_80pct_power": round(mde, 3),
            "models": infer(pred)}


def main() -> None:
    out = cfg.RESULTS_DIR
    out.mkdir(parents=True, exist_ok=True)
    report = {"stage": "PIT-v2", "status": "post-hoc, registered before outcomes were computed",
              "registration": "docs/PREREGISTRATION_AMENDMENT_2026-10-04.md",
              "protocol": "docs/PIT_PROTOCOL.md",
              "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "git": _git(), "python": platform.python_version(),
              "packages": {p: importlib.metadata.version(p)
                           for p in ("numpy", "pandas", "scikit-learn", "scipy")},
              "seed": cfg.SEED, "n_permutations": cfg.N_PERMUTATIONS,
              "n_bootstraps": cfg.N_BOOTSTRAPS,
              "inputs": {str(p.relative_to(ROOT)): _sha(p) for p in [
                  cfg.MODELING_PATH, cfg.REGISTRY_PATH, cfg.DEADLINES_PATH,
                  cfg.FILING_SAMPLE_PATH, cfg.SHARES_PATH,
                  *sorted(cfg.DERIVED.glob("*.csv"))]},
              "specifications": {}}
    specs = {"PRIMARY": cfg.PRIMARY, **cfg.SENSITIVITIES}
    for name, spec in specs.items():
        report["specifications"][name] = run_spec(name, spec, out)
        r = report["specifications"][name]
        print(f"\n== {name} ({r['n_features']} features, test n {r['test_rows_by_split']}, "
              f"MDE {r['minimum_detectable_abs_ic_80pct_power']})")
        for model, s in r["models"].items():
            extra = f" bonf={s['bonferroni_p']:.3f}" if "bonferroni_p" in s else ""
            print(f"  {model:26s} IC={s['pooled_ic']:+.3f} p={s['permutation_p_two_sided']:.4f}"
                  f" CI=[{s['bootstrap_ci_95'][0]:+.3f},{s['bootstrap_ci_95'][1]:+.3f}]{extra}")
    (out / "report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")


if __name__ == "__main__":
    main()
