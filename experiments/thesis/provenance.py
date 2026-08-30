"""Shared provenance primitives for MSc-thesis experiments.

Three things every thesis experiment needs, and nothing else:

1. an **isolated output directory** that cannot collide with, or be mistaken
   for, a pre-existing governed results root (``output_dir``);
2. **explicit, declared seeds** — no experiment may invent a seed at runtime
   or read one from the clock (``SEEDS`` / ``seed_for``);
3. a **SHA256 manifest** of what was written and what it was written from
   (``write_manifest``), in the same shape the existing labs already emit.

This module deliberately holds no statistics, no models, and no experiment
logic. It is provenance plumbing only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]

#: Every thesis experiment writes under this root and nowhere else.
THESIS_RESULTS_ROOT = ROOT / "experiments" / "results_thesis"

#: The experiment slugs this namespace is prepared for. An experiment must be
#: declared here before it may claim an output directory, so a typo cannot
#: silently create an unregistered results tree.
EXPERIMENT_SLUGS: tuple[str, ...] = (
    "positive_control",
    # Stage 1b — prospective calibration/diagnostic. Registered in
    # docs/thesis/STAGE_1B_REGISTRATION.md; NOT yet implemented or run.
    "positive_control_calibration",
    "negative_control",
    "defect_injection",
    "informativeness",
    "monthly_panel",
)

#: Explicit per-experiment seeds. Declared here, in version control, *before*
#: the experiments run. An experiment must call ``seed_for`` rather than
#: hardcoding or generating a seed, so that the seed is auditable and cannot be
#: re-chosen after seeing a result.
#:
#: 42 is reused for continuity with ``experiments/run_experiments.py`` and
#: ``experiments/significance.py``, which already fix ``random_state=42`` and
#: ``seed=42``; the thesis experiments differ from each other by slug, not by a
#: seed chosen for effect.
SEEDS: dict[str, int] = {
    "positive_control": 42,
    "positive_control_calibration": 42,
    "negative_control": 42,
    "defect_injection": 42,
    "informativeness": 42,
    "monthly_panel": 42,
}

#: Results roots that already exist and are owned by shipped work. Writing into
#: any of these from a thesis experiment is a governance error.
PROTECTED_RESULTS_ROOTS: tuple[str, ...] = (
    "experiments/results",
    "experiments/results_contamination",
    "experiments/results_dimensionality",
    "experiments/results_disagreement",
    "experiments/results_excess",
    "experiments/results_forward_2026",
    "experiments/results_influence",
    "experiments/results_missingness",
    "experiments/results_placebo",
    "experiments/results_rank_stability",
    "experiments/results_real_terms",
    "experiments/results_regime",
    "experiments/results_serving_eval",
)


class ThesisProvenanceError(RuntimeError):
    """Raised when an experiment would violate the namespace's isolation rules."""


def sha256_path(path: Path) -> str:
    """SHA256 of a file's bytes."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seed_for(slug: str) -> int:
    """The declared seed for ``slug``.

    Fails loudly for an undeclared experiment rather than defaulting, so a new
    experiment cannot run with an undocumented seed.
    """
    if slug not in SEEDS:
        raise ThesisProvenanceError(
            f"no declared seed for experiment {slug!r}; add it to SEEDS in "
            f"experiments/thesis/provenance.py before running the experiment"
        )
    return SEEDS[slug]


def output_dir(slug: str, *, create: bool = True) -> Path:
    """Return the isolated output directory for ``slug``.

    Guarantees the path sits under ``experiments/results_thesis/`` and never
    inside a pre-existing governed results root.
    """
    if slug not in EXPERIMENT_SLUGS:
        raise ThesisProvenanceError(
            f"unknown experiment slug {slug!r}; declare it in EXPERIMENT_SLUGS in "
            f"experiments/thesis/provenance.py first"
        )
    target = (THESIS_RESULTS_ROOT / slug).resolve()
    thesis_root = THESIS_RESULTS_ROOT.resolve()
    if thesis_root != target and thesis_root not in target.parents:
        raise ThesisProvenanceError(f"{target} escapes the thesis results root")
    relative = target.relative_to(ROOT).as_posix()
    for protected in PROTECTED_RESULTS_ROOTS:
        if relative == protected or relative.startswith(protected + "/"):
            raise ThesisProvenanceError(
                f"refusing to write thesis output into protected results root {protected!r}"
            )
    if create:
        target.mkdir(parents=True, exist_ok=True)
    return target


def describe(path: Path, role: str | None = None) -> dict[str, Any]:
    """A ``{path, sha256, size_bytes}`` descriptor, optionally with a role."""
    entry: dict[str, Any] = {
        "path": path.resolve().relative_to(ROOT).as_posix(),
        "sha256": sha256_path(path),
        "size_bytes": path.stat().st_size,
    }
    if role is not None:
        entry["role"] = role
    return entry


def write_manifest(
    slug: str,
    *,
    artifacts: Iterable[Path],
    source_artifacts: Iterable[tuple[Path, str]],
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write ``artifact_manifest.json`` for one thesis experiment.

    ``artifacts`` are the files the experiment produced; ``source_artifacts``
    are ``(path, role)`` pairs for the inputs it read. The emitted
    ``source_artifacts`` key is the same shape the artifact-registry staleness
    test auto-discovers, so a drifting input fails the suite by name once the
    experiment's output root is added to ``governed_roots``.
    """
    target = output_dir(slug)
    manifest = {
        "experiment": slug,
        "seed": seed_for(slug),
        "claim_safety": {
            "descriptive_research_evidence_only": True,
            "reliable_predictive_edge_established": False,
            "investment_value_established": False,
        },
        "artifacts": sorted(
            (describe(path) for path in artifacts), key=lambda item: item["path"]
        ),
        "source_artifacts": sorted(
            (describe(path, role) for path, role in source_artifacts),
            key=lambda item: item["path"],
        ),
    }
    if extra:
        manifest.update(extra)
    manifest_path = target / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest_path
