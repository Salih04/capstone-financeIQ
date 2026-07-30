"""Behavioral tests for R3-MISS-01 serving-heuristic missingness sensitivity.

These tests validate underlying behavior (masking mechanics, the service null
path, sign convention, fail-closed guards, determinism) rather than only pinning
prose. The full deterministic generation is exercised once per session through a
temp results directory.
"""

from __future__ import annotations

import csv
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import experiments.missingness_sensitivity as ms

ROOT = ms.ROOT
SERVICE_SHA_AT_HEAD = "7438ab40a47b5a1122ec8079d977bde7b7482a31f90dee0de79fd0f5f0212cb1"


# --------------------------------------------------------------------------- #
# Session-scoped heavy build (one deterministic generation)
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("results_missingness")
    comp = ms.compute()
    report = ms.build_report(comp)
    report["_row_cache"] = comp.all_rows
    checksums = ms.write_outputs(report, results_dir=out)
    # write_outputs mutated report (popped caches); re-read the on-disk JSON.
    report_on_disk = json.loads((out / ms.JSON_OUTPUT.name).read_text(encoding="utf-8"))
    return {
        "comp": comp,
        "dir": out,
        "checksums": checksums,
        "report": report_on_disk,
        "csv_text": (out / ms.CSV_OUTPUT.name).read_text(encoding="utf-8"),
        "md_text": (out / ms.MARKDOWN_OUTPUT.name).read_text(encoding="utf-8"),
        "json_text": (out / ms.JSON_OUTPUT.name).read_text(encoding="utf-8"),
    }


@pytest.fixture(scope="session")
def csv_rows(built):
    return list(csv.DictReader(io.StringIO(built["csv_text"])))


# --------------------------------------------------------------------------- #
# 1 + baseline replay
# --------------------------------------------------------------------------- #
def test_unmasked_replay_matches_service(built):
    comp = built["comp"]
    assert comp.baseline_replay_matches_service is True
    assert built["report"]["baseline_replay_audit"]["unmasked_replay_matches_service_output"] is True
    assert built["report"]["baseline_replay_audit"]["approximation_or_reimplementation_used"] is False


def test_seam_replay_equals_direct_service_output():
    """The temp-seam unmasked replay must equal the direct service output exactly."""
    public = ms.load_public_frame()
    training = pd.read_csv(ms.TRAINING_DATASET)
    training["ticker"] = training["ticker"].astype(str).str.strip().str.upper()
    authority = ms.load_category_authority()
    real = ms.load_service(ROOT)
    input_year = ms.resolve_input_year(real, public)
    selected = ms.selected_weight_set(real, authority)
    direct = ms._normalise_direct(
        real.run_forecast(input_year, selected.weights), input_year, selected.weights
    )
    with ms.ScoringSession(public, training, selected.weights) as session:
        replay = session.score(public, input_year)
    assert replay == direct


# --------------------------------------------------------------------------- #
# 2. Service source read-only + byte-identical
# --------------------------------------------------------------------------- #
def test_service_source_unchanged_and_recorded(built):
    actual = ms._sha256_file(ms.SERVICE_FILE)
    assert actual == SERVICE_SHA_AT_HEAD
    assert built["report"]["analysis_universe"]["service_sha256"] == actual
    # backend tree must be free of working-tree modifications after generation.
    diff = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--stat", "--", "backend"],
        capture_output=True, text=True, check=True,
    )
    assert diff.stdout.strip() == ""


# --------------------------------------------------------------------------- #
# 3. Missingness uses the service null path (not zero / imputation)
# --------------------------------------------------------------------------- #
def test_masking_writes_null_not_zero():
    public = ms.load_public_frame()
    input_year = int(public["year"].max())
    masked = ms._mask_frame(public, input_year, ["net_income"], None)
    year_rows = masked[masked["year"] == input_year]
    assert year_rows["net_income"].isna().all()
    assert not (year_rows["net_income"] == 0).any()
    # off-year rows are untouched
    off = public[public["year"] != input_year]["net_income"].reset_index(drop=True)
    off_masked = masked[masked["year"] != input_year]["net_income"].reset_index(drop=True)
    pd.testing.assert_series_equal(off, off_masked)


def test_missing_value_is_nan():
    assert isinstance(ms.MISSING_VALUE, float)
    assert np.isnan(ms.MISSING_VALUE)


def test_null_path_reduces_confidence_via_service():
    """A masked selected feature must appear as missing and reduce confidence."""
    public = ms.load_public_frame()
    training = pd.read_csv(ms.TRAINING_DATASET)
    training["ticker"] = training["ticker"].astype(str).str.strip().str.upper()
    authority = ms.load_category_authority()
    real = ms.load_service(ROOT)
    input_year = ms.resolve_input_year(real, public)
    selected = ms.selected_weight_set(real, authority)
    feature = selected.ordered_features[0]
    with ms.ScoringSession(public, training, selected.weights) as session:
        base = session.score(public, input_year)
        masked = session.score(ms._mask_frame(public, input_year, [feature], None), input_year)
    # every ticker that had the feature usable now has one more missing feature
    reduced = [t for t in base if masked[t]["missing_count"] > base[t]["missing_count"]]
    assert reduced, "masking a selected feature dataset-wide changed no coverage"
    for t in reduced:
        assert masked[t]["confidence"] <= base[t]["confidence"]


# --------------------------------------------------------------------------- #
# 4. Input year + cohort traced from authority, not hardcoded
# --------------------------------------------------------------------------- #
def test_input_year_traced_from_service_authority():
    public = ms.load_public_frame()
    real = ms.load_service(ROOT)
    resolved = ms.resolve_input_year(real, public)
    assert resolved == int(real.get_options()["default_prediction_year"])
    assert resolved == int(public["year"].max())


def test_input_year_mismatch_fails_closed():
    class FakeService:
        @staticmethod
        def get_options():
            return {"default_prediction_year": 1999}
    public = ms.load_public_frame()
    with pytest.raises(ms.MissingnessError):
        ms.resolve_input_year(FakeService, public)


# --------------------------------------------------------------------------- #
# 5. Dataset-wide category masking masks exactly the intended selected features
# --------------------------------------------------------------------------- #
def test_dataset_wide_category_masks_exact_selected_features():
    public = ms.load_public_frame()
    input_year = int(public["year"].max())
    authority = ms.load_category_authority()
    real = ms.load_service(ROOT)
    selected = ms.selected_weight_set(real, authority)
    category = selected.categories[0]
    features = selected.category_to_features[category]
    masked = ms._mask_frame(public, input_year, features, None)
    year_rows = masked[masked["year"] == input_year]
    for feat in features:
        assert year_rows[feat].isna().all()
    # a selected feature NOT in this category must be untouched for some ticker
    other = [f for f in selected.ordered_features if f not in features]
    if other:
        base_year = public[public["year"] == input_year]
        pd.testing.assert_series_equal(
            base_year[other[0]].reset_index(drop=True),
            year_rows[other[0]].reset_index(drop=True),
        )


# --------------------------------------------------------------------------- #
# 6. Per-ticker category masking masks one ticker only
# --------------------------------------------------------------------------- #
def test_per_ticker_category_masks_single_ticker():
    public = ms.load_public_frame()
    input_year = int(public["year"].max())
    authority = ms.load_category_authority()
    real = ms.load_service(ROOT)
    selected = ms.selected_weight_set(real, authority)
    category = selected.categories[0]
    features = selected.category_to_features[category]
    cohort = sorted(public[public["year"] == input_year]["ticker"])
    target = cohort[0]
    masked = ms._mask_frame(public, input_year, features, [target])
    year_rows = masked[masked["year"] == input_year]
    for feat in features:
        assert pd.isna(year_rows.loc[year_rows["ticker"] == target, feat]).all()
        # every other ticker keeps its raw input for these features
        others = year_rows[year_rows["ticker"] != target]
        base_others = public[(public["year"] == input_year) & (public["ticker"] != target)]
        pd.testing.assert_series_equal(
            base_others[feat].reset_index(drop=True),
            others[feat].reset_index(drop=True),
            check_names=False,
        )


# --------------------------------------------------------------------------- #
# 7 + 8. Single-feature scenarios cover every feature and every ticker-feature
# --------------------------------------------------------------------------- #
def test_single_feature_scenarios_are_exhaustive():
    public = ms.load_public_frame()
    input_year = int(public["year"].max())
    authority = ms.load_category_authority()
    real = ms.load_service(ROOT)
    selected = ms.selected_weight_set(real, authority)
    cohort = sorted(public[public["year"] == input_year]["ticker"])
    scenarios = ms.enumerate_scenarios(selected, cohort)

    c = [s for s in scenarios if s.family == "C"]
    d = [s for s in scenarios if s.family == "D"]
    assert {s.mask_name for s in c} == set(selected.ordered_features)
    assert len(c) == len(selected.ordered_features)
    assert len(d) == len(cohort) * len(selected.ordered_features)
    assert {(s.masked_ticker, s.mask_name) for s in d} == {
        (t, f) for t in cohort for f in selected.ordered_features
    }
    # single-feature scenarios never touch a non-selected feature
    for s in c + d:
        assert s.features == [s.mask_name]
        assert s.mask_name in selected.ordered_features


def test_scenario_families_have_expected_counts(built):
    counts = built["report"]["scenario_definitions"]["counts"]
    comp = built["comp"]
    n_cat = len(comp.selected.categories)
    n_feat = len(comp.selected.ordered_features)
    n_tick = len(comp.cohort)
    assert counts["A_dataset_wide_category"] == n_cat
    assert counts["B_per_ticker_category"] == n_cat * n_tick
    assert counts["C_dataset_wide_feature"] == n_feat
    assert counts["D_per_ticker_feature"] == n_feat * n_tick
    assert counts["total_scenarios"] == n_cat + n_cat * n_tick + n_feat + n_feat * n_tick


# --------------------------------------------------------------------------- #
# 9. Rank-delta sign convention
# --------------------------------------------------------------------------- #
def test_rank_delta_sign_convention(csv_rows):
    for row in csv_rows:
        signed = int(row["signed_rank_delta"])
        assert signed == int(row["masked_rank"]) - int(row["baseline_rank"])
        assert int(row["absolute_rank_delta"]) == abs(signed)


# --------------------------------------------------------------------------- #
# 10. Confidence deltas match service behavior
# --------------------------------------------------------------------------- #
def test_confidence_delta_matches_service(csv_rows):
    for row in csv_rows:
        selected_n = int(row["selected_feature_count"])
        usable = int(row["usable_feature_count"])
        missing = int(row["missing_selected_feature_count"])
        assert usable + missing == selected_n
        # masked confidence equals usable/selected to service rounding
        assert round(usable / selected_n, 4) == float(row["masked_confidence"])
        delta = round(float(row["masked_confidence"]) - float(row["baseline_confidence"]), 6)
        assert abs(delta - float(row["confidence_delta"])) < 1e-9


# --------------------------------------------------------------------------- #
# 11. Per-ticker mask can move OTHER tickers' ranks via relative ordering
# --------------------------------------------------------------------------- #
def test_per_ticker_mask_moves_other_tickers(csv_rows):
    moved_others = [
        r for r in csv_rows
        if r["mask_scope"] == "per_ticker"
        and r["ticker_directly_masked"] == "False"
        and int(r["absolute_rank_delta"]) > 0
    ]
    assert moved_others, "no per-ticker scenario moved a non-masked ticker's rank"
    # and the directly-masked ticker is exactly one per per-ticker scenario
    per_ticker = [r for r in csv_rows if r["mask_scope"] == "per_ticker"]
    by_scenario: dict[tuple, int] = {}
    for r in per_ticker:
        key = (r["scenario_family"], r["mask_name"], r["masked_ticker"])
        by_scenario[key] = by_scenario.get(key, 0) + (1 if r["ticker_directly_masked"] == "True" else 0)
    assert by_scenario and all(v == 1 for v in by_scenario.values())


# --------------------------------------------------------------------------- #
# 12. Scenario membership identical to baseline (or fail closed)
# --------------------------------------------------------------------------- #
def test_scenario_membership_unchanged(built):
    baseline_checksum = built["report"]["analysis_universe"]["cohort_membership_checksum"]
    for summary in built["report"]["scenario_summaries"]:
        assert summary["cohort_membership_changed"] is False
        assert summary["baseline_membership_checksum"] == baseline_checksum
        assert summary["masked_membership_checksum"] == baseline_checksum


# --------------------------------------------------------------------------- #
# 13. Malformed inputs / schema faults fail with controlled exceptions
# --------------------------------------------------------------------------- #
def _base_public():
    return ms.load_public_frame()


def test_duplicate_ticker_rows_raise(tmp_path):
    frame = _base_public()
    dupe = frame[frame["year"] == frame["year"].max()].head(1)
    bad = pd.concat([frame, dupe], ignore_index=True)
    path = tmp_path / "dupe.csv"
    bad.to_csv(path, index=False)
    with pytest.raises(ms.MissingnessError):
        ms.load_public_frame(path)


def test_malformed_year_raises(tmp_path):
    frame = _base_public()
    frame["year"] = frame["year"].astype(object)
    frame.loc[0, "year"] = "not-a-year"
    path = tmp_path / "badyear.csv"
    frame.to_csv(path, index=False)
    with pytest.raises(ms.MissingnessError):
        ms.load_public_frame(path)


def test_missing_identifier_raises(tmp_path):
    frame = _base_public().drop(columns=["ticker"])
    path = tmp_path / "noid.csv"
    frame.to_csv(path, index=False)
    with pytest.raises(ms.MissingnessError):
        ms.load_public_frame(path)


def test_non_finite_service_output_raises():
    weights = {"a": 1.0, "b": 1.0}
    helper = ms.ScoringSession.__new__(ms.ScoringSession)
    helper._weights = weights
    result = {
        "year": 2025, "stock_count": 1,
        "items": [{"ticker": "X", "score": float("inf"), "confidence": 1.0,
                   "rank": 1, "missing_parameters": []}],
    }
    with pytest.raises(ms.MissingnessError):
        ms.ScoringSession._normalise(helper, result, 2025)


def test_unexpected_schema_raises():
    weights = {"a": 1.0}
    helper = ms.ScoringSession.__new__(ms.ScoringSession)
    helper._weights = weights
    result = {"year": 2025, "stock_count": 1, "items": [{"ticker": "X", "score": 0.5}]}
    with pytest.raises(ms.MissingnessError):
        ms.ScoringSession._normalise(helper, result, 2025)


def test_empty_feature_set_raises():
    class FakeService:
        TARGET_MODE_FINALIZED = "finalized_only"

        @staticmethod
        def train_parameters(**_kwargs):
            return {"top_parameters": []}
    authority = ms.load_category_authority()
    with pytest.raises(ms.MissingnessError):
        ms.selected_weight_set(FakeService, authority)


def test_missing_category_mapping_raises():
    class FakeService:
        TARGET_MODE_FINALIZED = "finalized_only"

        @staticmethod
        def train_parameters(**_kwargs):
            return {"top_parameters": [{"name": "totally_unmapped_feature", "weight": 1.0, "rank": 1}]}
    authority = ms.load_category_authority()
    with pytest.raises(ms.MissingnessError):
        ms.selected_weight_set(FakeService, authority)


def test_output_path_escape_raises(tmp_path):
    with pytest.raises(ms.MissingnessError):
        ms._assert_within(Path("../escape.csv"), tmp_path)
    with pytest.raises(ms.MissingnessError):
        ms._assert_within(Path("/etc/passwd"), tmp_path)
    # a legitimate name resolves inside base
    ok = ms._assert_within(Path("rank_deltas.csv"), tmp_path)
    assert str(ok).startswith(str(tmp_path.resolve()))


# --------------------------------------------------------------------------- #
# 14. No random sampling / stochastic scenario selection
# --------------------------------------------------------------------------- #
def test_no_random_sampling_in_source():
    source = ms.SERVICE_FILE  # sanity: service unchanged
    text = Path(ms.__file__).read_text(encoding="utf-8")
    for banned in ("random.", "np.random", "sample(", "shuffle(", "choice("):
        assert banned not in text, f"stochastic construct {banned!r} present"
    assert source.is_file()


def test_scenario_enumeration_is_deterministic():
    public = ms.load_public_frame()
    input_year = int(public["year"].max())
    authority = ms.load_category_authority()
    real = ms.load_service(ROOT)
    selected = ms.selected_weight_set(real, authority)
    cohort = sorted(public[public["year"] == input_year]["ticker"])
    a = ms.enumerate_scenarios(selected, cohort)
    b = ms.enumerate_scenarios(selected, cohort)
    assert [(s.family, s.mask_name, s.masked_ticker) for s in a] == [
        (s.family, s.mask_name, s.masked_ticker) for s in b
    ]


# --------------------------------------------------------------------------- #
# 15. No model-selection / best-winner semantics
# --------------------------------------------------------------------------- #
def test_no_best_or_winner_semantic_fields(built):
    blob = json.dumps(built["report"]).lower()
    for banned in ("best_", "winner", "most_robust", "most_reliable", "strongest", "winning"):
        assert banned not in blob, f"forbidden semantic field {banned!r} present"


# --------------------------------------------------------------------------- #
# 16. Mandatory sensitivity label in JSON, Markdown, and CSV
# --------------------------------------------------------------------------- #
def test_mandatory_label_present_everywhere(built, csv_rows):
    label = ms.SENSITIVITY_LABEL
    assert label in built["json_text"]
    assert label in built["md_text"]
    assert built["report"]["mandatory_sensitivity_label"] == label
    assert csv_rows and all(r["sensitivity_label"] == label for r in csv_rows)


# --------------------------------------------------------------------------- #
# 17. Predictive-skill / production interpretations rejected
# --------------------------------------------------------------------------- #
def test_predictive_skill_not_claimed(built):
    report = built["report"]
    assert report["predictive_skill_measured"] is False
    ms._assert_no_forbidden_claims(built["json_text"])
    ms._assert_no_forbidden_claims(built["md_text"])
    # response schema carries no recommendation/verdict-style fields
    blob = json.dumps(report).lower()
    for banned in ("recommendation", "buy_signal", "sell_signal", "price_target", "verdict", "rating"):
        assert banned not in blob


def test_forbidden_claim_guard_actually_trips():
    with pytest.raises(ms.MissingnessError):
        ms._assert_no_forbidden_claims("this establishes a reliable predictive edge")


# --------------------------------------------------------------------------- #
# 18. Artifacts parse and reconstruct coherently
# --------------------------------------------------------------------------- #
def test_artifacts_parse_and_reconstruct(built, csv_rows):
    report = built["report"]
    # CSV columns match the declared schema and key uniqueness holds
    assert list(csv_rows[0].keys()) == ms.CSV_COLUMNS
    keys = {
        (r["scenario_family"], r["mask_scope"], r["mask_kind"], r["mask_name"], r["masked_ticker"], r["ticker"])
        for r in csv_rows
    }
    assert len(keys) == len(csv_rows)
    assert len(csv_rows) == report["row_level_evidence"]["row_count"]
    # recorded csv checksum matches the file
    assert report["row_level_evidence"]["csv_sha256"] == ms._sha256_text(built["csv_text"])


# --------------------------------------------------------------------------- #
# 19. Two same-environment generations are byte-identical
# --------------------------------------------------------------------------- #
def test_two_run_byte_identical(built, tmp_path):
    comp = ms.compute()
    report = ms.build_report(comp)
    report["_row_cache"] = comp.all_rows
    second = ms.write_outputs(report, results_dir=tmp_path)
    assert second == built["checksums"]


# --------------------------------------------------------------------------- #
# 20. Fresh generation cannot pass on stale files
# --------------------------------------------------------------------------- #
def test_generation_is_fresh_not_stale(tmp_path):
    for name in (ms.JSON_OUTPUT.name, ms.MARKDOWN_OUTPUT.name, ms.CSV_OUTPUT.name):
        (tmp_path / name).write_text("STALE SENTINEL", encoding="utf-8")
    comp = ms.compute()
    report = ms.build_report(comp)
    report["_row_cache"] = comp.all_rows
    ms.write_outputs(report, results_dir=tmp_path)
    for name in (ms.JSON_OUTPUT.name, ms.MARKDOWN_OUTPUT.name, ms.CSV_OUTPUT.name):
        text = (tmp_path / name).read_text(encoding="utf-8")
        assert "STALE SENTINEL" not in text
    parsed = json.loads((tmp_path / ms.JSON_OUTPUT.name).read_text(encoding="utf-8"))
    assert parsed["task"] == "R3-MISS-01"


# --------------------------------------------------------------------------- #
# 21. Writes confined to results dir
# --------------------------------------------------------------------------- #
def test_writes_confined_to_results_dir(built):
    files = sorted(p.name for p in built["dir"].iterdir())
    assert files == sorted([ms.JSON_OUTPUT.name, ms.MARKDOWN_OUTPUT.name, ms.CSV_OUTPUT.name])


# --------------------------------------------------------------------------- #
# 22. Category authority is the governed passports source_class covering the set
# --------------------------------------------------------------------------- #
def test_category_authority_covers_selected_set(built):
    report = built["report"]
    authority = report["feature_category_authority"]
    assert authority["authority_path"] == "data/trusted_clean/feature_passports.json"
    mapping = report["feature_category_authority"]["category_to_selected_features"]
    selected = {p["name"] for p in report["selected_weight_set"]}
    covered = {feat for feats in mapping.values() for feat in feats}
    assert covered == selected
    for param in report["selected_weight_set"]:
        assert param["category"] in mapping


# --------------------------------------------------------------------------- #
# 23. Makefile + registry coherence
# --------------------------------------------------------------------------- #
def test_makefile_target_present():
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "research-missingness:" in text
    assert "experiments/missingness_sensitivity.py" in text


def test_registry_entries_present_and_coherent():
    registry = json.loads((ROOT / "artifact_registry.json").read_text(encoding="utf-8"))
    assert "experiments/results_missingness" in registry["governed_roots"]
    owned = {
        e["path_or_glob"]: e
        for e in registry["entries"]
        if e["path_or_glob"].startswith("experiments/results_missingness/")
    }
    expected = {
        "experiments/results_missingness/missingness_report.json",
        "experiments/results_missingness/missingness_report.md",
        "experiments/results_missingness/rank_deltas.csv",
    }
    assert set(owned) == expected
    for entry in owned.values():
        assert entry["generator_command"] == "make research-missingness"
        assert entry["hand_edit_forbidden"] is True


# --------------------------------------------------------------------------- #
# BLOCKER 1 — Output-confinement authority (R3-MISS-01 review repair)
# --------------------------------------------------------------------------- #
@pytest.fixture
def outside_temp_root(tmp_path_factory):
    """An explicit bounded temporary-root authority that lives outside the repo.

    ``tmp_path`` is already outside the repository on this platform, but we use a
    dedicated factory dir so tests can plant symlinks freely under it.
    """
    root = tmp_path_factory.mktemp("miss-temp-root")
    return Path(root)


def test_canonical_output_needs_no_override():
    """Probe 1: canonical execution resolves to the governed namespace only."""
    assert ms.resolve_output_authority(None, None) == ms.CANONICAL_RESULTS_DIR
    # Passing the canonical directory explicitly is also accepted (idempotent).
    assert (
        ms.resolve_output_authority(ms.CANONICAL_RESULTS_DIR, None)
        == ms.CANONICAL_RESULTS_DIR
    )
    assert ms.CANONICAL_RESULTS_DIR == ROOT / "experiments" / "results_missingness"


def test_make_target_uses_canonical_output_only():
    """Probe 2: the make recipe carries no output override, so it writes canonically."""
    recipe = (ROOT / "Makefile").read_text(encoding="utf-8")
    # Find the research-missingness recipe body.
    lines = recipe.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("research-missingness:"))
    body = []
    for line in lines[start + 1 :]:
        if line.startswith("\t"):
            body.append(line)
        elif line.strip() == "":
            continue
        else:
            break
    joined = "\n".join(body)
    assert "experiments/missingness_sensitivity.py" in joined
    assert "--results-dir" not in joined
    assert "--temp-root" not in joined


def test_bounded_temp_destination_is_accepted(outside_temp_root):
    """Probe 3: a destination beneath an explicit bounded temp root succeeds."""
    resolved = ms.resolve_output_authority(Path("run-a/out"), outside_temp_root)
    assert resolved == (outside_temp_root / "run-a" / "out").resolve()
    # An absolute destination under the same authority is also accepted.
    resolved_abs = ms.resolve_output_authority(outside_temp_root / "run-b", outside_temp_root)
    assert resolved_abs == (outside_temp_root / "run-b").resolve()


def test_unrelated_absolute_path_without_authority_is_refused():
    """Probe 4: an arbitrary absolute directory without temp-root authority fails."""
    with pytest.raises(ms.OutputAuthorityError):
        ms.resolve_output_authority(Path("/tmp/financeiq-unauthorized"), None)


@pytest.mark.parametrize(
    "relative",
    [
        "backend/r3-miss-probe",
        "frontend/r3-miss-probe",
        "data/r3-miss-probe",
        "experiments/results_excess/r3-miss-probe",
    ],
)
def test_in_repo_probes_are_refused(relative):
    """Probes 5-8: governed/in-repo destinations without authority all fail closed."""
    with pytest.raises(ms.OutputAuthorityError):
        ms.resolve_output_authority(ROOT / relative, None)
    # Even *with* a temp-root authority, an absolute in-repo path is refused
    # because it is not beneath that authority.
    with tempfile.TemporaryDirectory(prefix="financeiq-miss-authority-") as td:
        with pytest.raises(ms.OutputAuthorityError):
            ms.resolve_output_authority(ROOT / relative, Path(td))


def test_traversal_destination_is_refused(outside_temp_root):
    """Probe 9: a ``..`` traversal escape is refused with and without authority."""
    with pytest.raises(ms.OutputAuthorityError):
        ms.resolve_output_authority(Path("../escape"), None)
    with pytest.raises(ms.OutputAuthorityError):
        ms.resolve_output_authority(Path("a/../../escape"), outside_temp_root)


def test_symlinked_destination_directory_is_refused(outside_temp_root, tmp_path):
    """Probe 10: a symlinked destination directory is refused."""
    external = tmp_path / "external-dest"
    external.mkdir()
    link = outside_temp_root / "link"
    link.symlink_to(external, target_is_directory=True)
    with pytest.raises(ms.OutputAuthorityError):
        ms.resolve_output_authority(Path("link"), outside_temp_root)


def test_symlinked_ancestor_component_is_refused(outside_temp_root, tmp_path):
    """Probe 11: a symlinked ancestor between the temp root and the dest is refused."""
    external = tmp_path / "external-anc"
    external.mkdir()
    (outside_temp_root / "anc").symlink_to(external, target_is_directory=True)
    with pytest.raises(ms.OutputAuthorityError):
        ms.resolve_output_authority(Path("anc/child"), outside_temp_root)


def test_symlink_escape_from_temp_root_is_refused(outside_temp_root, tmp_path):
    """Probe 12: a symlink inside the temp root pointing outside cannot escape it."""
    escape_target = tmp_path / "escape-target"
    escape_target.mkdir()
    (outside_temp_root / "bridge").symlink_to(escape_target, target_is_directory=True)
    with pytest.raises(ms.OutputAuthorityError):
        ms.resolve_output_authority(Path("bridge/out"), outside_temp_root)


def test_temp_root_authority_must_be_a_real_external_directory():
    """A nonexistent, non-directory, or in-repo temp-root authority is refused."""
    with pytest.raises(ms.OutputAuthorityError):
        ms.resolve_output_authority(Path("out"), Path("/no/such/authority/root"))
    with tempfile.NamedTemporaryFile(prefix="financeiq-miss-file-") as handle:
        with pytest.raises(ms.OutputAuthorityError):
            ms.resolve_output_authority(Path("out"), Path(handle.name))
    with pytest.raises(ms.OutputAuthorityError):
        ms.resolve_output_authority(Path("out"), ROOT)


def test_only_the_three_governed_filenames_can_be_written(tmp_path):
    """Probe 13: the safe writer refuses any non-governed basename."""
    with pytest.raises(ms.OutputAuthorityError):
        ms._atomic_write_governed(tmp_path, {"evil.txt": "x"})
    ms._atomic_write_governed(
        tmp_path,
        {
            ms.JSON_OUTPUT.name: "{}",
            ms.MARKDOWN_OUTPUT.name: "# md",
            ms.CSV_OUTPUT.name: "a,b\n",
        },
    )
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
        [ms.JSON_OUTPUT.name, ms.MARKDOWN_OUTPUT.name, ms.CSV_OUTPUT.name]
    )


# --------------------------------------------------------------------------- #
# BLOCKER 2 — Transactional three-artifact publication
# --------------------------------------------------------------------------- #
_G1 = {
    ms.JSON_OUTPUT.name: '{"v":1}\n',
    ms.MARKDOWN_OUTPUT.name: "# md1\n",
    ms.CSV_OUTPUT.name: "a,b\n1,2\n",
}
_G2 = {
    ms.JSON_OUTPUT.name: '{"v":2}\n',
    ms.MARKDOWN_OUTPUT.name: "# md2\n",
    ms.CSV_OUTPUT.name: "a,b\n3,4\n",
}


def _dir_hashes(directory: Path) -> dict[str, str]:
    import hashlib

    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in directory.iterdir()
    }


def _no_residue(directory: Path) -> None:
    residue = [
        p.name
        for p in directory.parent.iterdir()
        if p.name.startswith(f".{directory.name}.")
    ]
    assert residue == [], f"staging/backup residue survived: {residue}"


def test_new_publication_with_no_prior_set_succeeds(tmp_path):
    """1: publishing into a fresh empty directory writes exactly the three files."""
    d = tmp_path / "out"
    d.mkdir()
    ms._atomic_write_governed(d, _G1)
    assert sorted(p.name for p in d.iterdir()) == sorted(_G1)
    for name, text in _G1.items():
        assert (d / name).read_text() == text
    _no_residue(d)


def test_complete_prior_set_is_wholly_replaced(tmp_path):
    """2: a complete prior set is fully replaced, no old bytes survive."""
    d = tmp_path / "out"
    d.mkdir()
    ms._atomic_write_governed(d, _G1)
    ms._atomic_write_governed(d, _G2)
    assert _dir_hashes(d) == _dir_hashes_of(_G2)
    _no_residue(d)


def _dir_hashes_of(contents: dict[str, str]) -> dict[str, str]:
    import hashlib

    return {k: hashlib.sha256(v.encode()).hexdigest() for k, v in contents.items()}


def _inject_rename_failure(monkeypatch, fail_on_call: int):
    """Make the ``fail_on_call``-th os.rename raise, others pass through."""
    real = os.rename
    state = {"n": 0}

    def flaky(src, dst, *, src_dir_fd=None, dst_dir_fd=None):
        state["n"] += 1
        if state["n"] == fail_on_call:
            raise OSError(f"injected failure on rename #{fail_on_call}")
        return real(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)

    monkeypatch.setattr(os, "rename", flaky)
    return state


def test_failure_before_first_rename_preserves_old_set(tmp_path, monkeypatch):
    """3/4: a staging-validation failure leaves the complete prior set intact."""
    d = tmp_path / "out"
    d.mkdir()
    ms._atomic_write_governed(d, _G1)
    before = _dir_hashes(d)
    # Force the staging validation to fail (no rename has happened yet).
    monkeypatch.setattr(
        ms,
        "_validate_dir_contents",
        lambda *a, **k: (_ for _ in ()).throw(ms.OutputAuthorityError("boom")),
    )
    with pytest.raises(ms.OutputAuthorityError):
        ms._atomic_write_governed(d, _G2)
    assert _dir_hashes(d) == before
    _no_residue(d)


def test_failure_between_old_backup_and_new_swap_restores_old_set(tmp_path, monkeypatch):
    """5: failing the staging->child rename restores the complete prior set."""
    d = tmp_path / "out"
    d.mkdir()
    ms._atomic_write_governed(d, _G1)
    before = _dir_hashes(d)
    # rename #1 is child->backup (allowed); rename #2 is staging->child (fails).
    _inject_rename_failure(monkeypatch, fail_on_call=2)
    with pytest.raises(OSError):
        ms._atomic_write_governed(d, _G2)
    assert _dir_hashes(d) == before, "prior set not byte-identical after failure"
    _no_residue(d)


def test_failure_during_post_validation_restores_old_set(tmp_path, monkeypatch):
    """6/7: a post-publication validation failure rolls back to the prior set."""
    d = tmp_path / "out"
    d.mkdir()
    ms._atomic_write_governed(d, _G1)
    before = _dir_hashes(d)
    calls = {"n": 0}
    real = ms._validate_dir_contents

    def validate(dir_fd, contents, *, label):
        calls["n"] += 1
        # First call validates staging (allow); second validates the published
        # directory (fail) to trigger post-publication rollback.
        if label == "published":
            raise ms.OutputAuthorityError("post-publication validation failure")
        return real(dir_fd, contents, label=label)

    monkeypatch.setattr(ms, "_validate_dir_contents", validate)
    with pytest.raises(ms.OutputAuthorityError):
        ms._atomic_write_governed(d, _G2)
    assert _dir_hashes(d) == before
    _no_residue(d)


def test_no_mixed_generation_can_remain_across_injected_failures(tmp_path, monkeypatch):
    """8: after any injected failure the set is wholly old or wholly new."""
    for fail_call in (1, 2):
        d = tmp_path / f"out{fail_call}"
        d.mkdir()
        ms._atomic_write_governed(d, _G1)
        old = _dir_hashes(d)
        _inject_rename_failure(monkeypatch, fail_on_call=fail_call)
        with pytest.raises(OSError):
            ms._atomic_write_governed(d, _G2)
        now = _dir_hashes(d)
        assert now == old or now == _dir_hashes_of(_G2)
        # A mixture of _G1 and _G2 members is never allowed.
        assert not (0 < sum(1 for k in now if now[k] == _dir_hashes_of(_G2)[k]) < 3)
        monkeypatch.undo()
        _no_residue(d)


def test_successful_publication_leaves_no_staging_or_backup_residue(tmp_path):
    """9: a clean replacement leaves only the three governed files."""
    d = tmp_path / "out"
    d.mkdir()
    ms._atomic_write_governed(d, _G1)
    ms._atomic_write_governed(d, _G2)
    assert sorted(p.name for p in d.iterdir()) == sorted(_G2)
    _no_residue(d)


def test_symlinked_prior_output_fails_closed(tmp_path):
    """10: a symlinked prior output directory is refused, never followed."""
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "out"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ms.OutputAuthorityError):
        ms._atomic_write_governed(link, _G1)


def test_incomplete_content_set_is_refused(tmp_path):
    """11: fewer or more than the exact governed set is refused."""
    d = tmp_path / "out"
    d.mkdir()
    with pytest.raises(ms.OutputAuthorityError):
        ms._atomic_write_governed(d, {ms.JSON_OUTPUT.name: "{}"})
    with pytest.raises(ms.OutputAuthorityError):
        ms._atomic_write_governed(
            d, {**_G1, "extra_fourth.json": "x"}
        )


def test_governed_regeneration_remains_deterministic(tmp_path):
    """12: republishing identical content is byte-stable and residue-free."""
    d = tmp_path / "out"
    d.mkdir()
    ms._atomic_write_governed(d, _G1)
    first = _dir_hashes(d)
    ms._atomic_write_governed(d, _G1)
    assert _dir_hashes(d) == first
    _no_residue(d)


def test_deceptive_normalized_path_cannot_bypass_confinement(outside_temp_root):
    """Probe 15: a path that normalizes back inside the repo is still refused."""
    # An absolute destination that lexically dips through the repo is not beneath
    # the temp-root authority once resolved, so it is refused.
    deceptive = ROOT / "backend" / ".." / "backend" / "r3-miss-probe"
    with pytest.raises(ms.OutputAuthorityError):
        ms.resolve_output_authority(deceptive, outside_temp_root)


def test_cli_reviewer_backend_escape_is_refused_without_writing():
    """The reviewer's exact escape (``--results-dir backend/...``) fails and writes nothing."""
    probe = ROOT / "backend" / "r3-miss-probe"
    assert not probe.exists()
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    result = subprocess.run(
        [
            sys.executable,
            "experiments/missingness_sensitivity.py",
            "--results-dir",
            "backend/r3-miss-probe",
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode != 0
    assert not probe.exists()


def test_cli_temp_output_without_authority_is_refused_without_writing(tmp_path):
    """A bare ``--results-dir`` under /tmp (no ``--temp-root``) is refused, writes nothing."""
    dest = tmp_path / "unauthorized-out"
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    result = subprocess.run(
        [
            sys.executable,
            "experiments/missingness_sensitivity.py",
            "--results-dir",
            str(dest),
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode != 0
    assert not dest.exists()


# --------------------------------------------------------------------------- #
# BLOCKER 4 — Fractional / malformed year validation (never truncated)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "value",
    [2025.5, float("inf"), float("-inf"), float("nan"), True, None, "2025.5", "2025x", "", "  ", "inf", "nan"],
)
def test_to_integral_year_rejects_non_integral_values(value):
    with pytest.raises(ms.MissingnessError):
        ms._to_integral_year(value, position=0)


@pytest.mark.parametrize("value,expected", [(2025, 2025), (2025.0, 2025), ("2025", 2025), (np.int64(2024), 2024)])
def test_to_integral_year_accepts_finite_integers(value, expected):
    assert ms._to_integral_year(value, position=0) == expected


def _public_with_year(tmp_path, year_value):
    frame = ms.load_public_frame()
    frame = frame.copy()
    frame["year"] = frame["year"].astype(object)
    frame.loc[frame.index[0], "year"] = year_value
    path = tmp_path / "year.csv"
    frame.to_csv(path, index=False)
    return path


def test_load_public_frame_rejects_fractional_year(tmp_path):
    """A 2025.5 year must be refused, never silently truncated to 2025."""
    path = _public_with_year(tmp_path, "2025.5")
    with pytest.raises(ms.MissingnessError):
        ms.load_public_frame(path)


@pytest.mark.parametrize("bad", ["inf", "-inf", "nan", "", "2025x"])
def test_load_public_frame_rejects_malformed_years(tmp_path, bad):
    path = _public_with_year(tmp_path, bad)
    with pytest.raises(ms.MissingnessError):
        ms.load_public_frame(path)


def test_load_public_frame_accepts_the_real_dataset():
    """The current valid dataset still loads with integer years unchanged."""
    frame = ms.load_public_frame()
    assert str(frame["year"].dtype) in {"int64", "int32"}
    assert frame["year"].min() >= 2000


# --------------------------------------------------------------------------- #
# BLOCKER 1 — Descriptor-anchored canonical output authority (fake repos)
# --------------------------------------------------------------------------- #
def _fake_repo_canonical(root: Path) -> Path:
    (root / "experiments" / ms.CANONICAL_CHILD_NAME).mkdir(parents=True)
    return root


def test_genuine_canonical_directory_is_anchored(tmp_path):
    """1: a genuine repo/experiments/results_missingness chain anchors cleanly."""
    r = _fake_repo_canonical(tmp_path / "repo")
    fd, child = ms._open_canonical_parent(r)
    try:
        assert child == ms.CANONICAL_CHILD_NAME
    finally:
        os.close(fd)


def test_canonical_directory_replaced_by_external_symlink_fails(tmp_path):
    """2: the canonical directory swapped for an external symlink is refused."""
    r = tmp_path / "repo"
    (r / "experiments").mkdir(parents=True)
    external = tmp_path / "external"
    external.mkdir()
    (r / "experiments" / ms.CANONICAL_CHILD_NAME).symlink_to(
        external, target_is_directory=True
    )
    with pytest.raises(ms.OutputAuthorityError):
        ms._open_canonical_parent(r)


def test_canonical_directory_replaced_by_internal_symlink_fails(tmp_path):
    """3: the canonical directory swapped for an in-repo symlink is refused."""
    r = tmp_path / "repo"
    (r / "experiments").mkdir(parents=True)
    inside = r / "experiments" / "real_inside"
    inside.mkdir()
    (r / "experiments" / ms.CANONICAL_CHILD_NAME).symlink_to(
        inside, target_is_directory=True
    )
    with pytest.raises(ms.OutputAuthorityError):
        ms._open_canonical_parent(r)


def test_symlinked_canonical_ancestor_fails(tmp_path):
    """4: a symlinked 'experiments' ancestor is refused."""
    r = tmp_path / "repo"
    r.mkdir()
    real_exp = tmp_path / "real_experiments"
    (real_exp / ms.CANONICAL_CHILD_NAME).mkdir(parents=True)
    (r / "experiments").symlink_to(real_exp, target_is_directory=True)
    with pytest.raises(ms.OutputAuthorityError):
        ms._open_canonical_parent(r)


def test_symlinked_repository_root_fails(tmp_path):
    """A symlinked repository root is refused before anchoring."""
    real_repo = tmp_path / "real_repo"
    (real_repo / "experiments" / ms.CANONICAL_CHILD_NAME).mkdir(parents=True)
    link = tmp_path / "repo"
    link.symlink_to(real_repo, target_is_directory=True)
    with pytest.raises(ms.OutputAuthorityError):
        ms._open_canonical_parent(link)


def test_missing_canonical_child_is_tolerated_and_created_by_publish(tmp_path):
    """A not-yet-existing canonical directory is anchored (publish creates it)."""
    r = tmp_path / "repo"
    (r / "experiments").mkdir(parents=True)
    fd, child = ms._open_canonical_parent(r)
    os.close(fd)
    assert child == ms.CANONICAL_CHILD_NAME


def test_symlinked_temp_root_authority_is_refused(tmp_path):
    """5: a symlinked temporary-root authority is refused."""
    real = tmp_path / "real_root"
    real.mkdir()
    link = tmp_path / "link_root"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ms.OutputAuthorityError):
        ms.resolve_output_authority(Path("out"), link)


def test_real_repository_canonical_chain_is_clean():
    """The live repository canonical chain validates without raising."""
    ms._assert_canonical_chain_safe()
    assert ms.resolve_output_authority(None, None) == ms.CANONICAL_RESULTS_DIR


# --------------------------------------------------------------------------- #
# Second mandatory repair — BLOCKER 1: continuous descriptor-anchored authority
# --------------------------------------------------------------------------- #
#
# A bounded temporary path was authorized while an intermediate child did not
# exist; after authorization but before publication that child was installed as
# a symlink to an external directory, and publication followed the swapped
# ancestor, writing all three artifacts outside the authorized root.  The
# authority now retains the temporary-root and re-walks the whole chain with
# per-component O_NOFOLLOW at publication time, so no post-authorization
# component swap can redirect where the artifacts land.


def _tmp_authority(tmp_path_factory) -> Path:
    """An existing temporary-root authority outside the repository."""
    return Path(tmp_path_factory.mktemp("authority")).resolve()


def test_genuine_bounded_temporary_destination_publishes(tmp_path_factory):
    """2: a legitimate bounded destination still publishes the complete set."""
    root = _tmp_authority(tmp_path_factory)
    authorized = ms.resolve_output_authority(root / "mid" / "out", root)
    ms._atomic_write_governed(authorized, _G1, temp_root=root)
    assert sorted(os.listdir(authorized)) == sorted(ms.GOVERNED_OUTPUT_NAMES)


def test_post_authorization_external_symlink_ancestor_is_refused(tmp_path_factory):
    """6/15: the reviewed race — a grandparent swapped to an external symlink."""
    root = _tmp_authority(tmp_path_factory)
    external = Path(tempfile.mkdtemp()).resolve()
    (external / "sub").mkdir()
    authorized = ms.resolve_output_authority(root / "mid" / "sub" / "out", root)
    # The swap happens strictly after authorization and above the publish parent.
    (root / "mid").symlink_to(external, target_is_directory=True)
    with pytest.raises(ms.OutputAuthorityError):
        ms._atomic_write_governed(authorized, _G1, temp_root=root)
    # A failed attack must leave no artifact outside the authorized root.
    assert list((external / "sub").rglob("*")) == []


def test_post_authorization_internal_symlink_ancestor_is_refused(tmp_path_factory):
    """7: an internal symlink target is refused just as an external one is."""
    root = _tmp_authority(tmp_path_factory)
    (root / "elsewhere" / "sub").mkdir(parents=True)
    authorized = ms.resolve_output_authority(root / "mid" / "sub" / "out", root)
    (root / "mid").symlink_to(root / "elsewhere", target_is_directory=True)
    with pytest.raises(ms.OutputAuthorityError):
        ms._atomic_write_governed(authorized, _G1, temp_root=root)
    assert list((root / "elsewhere" / "sub").rglob("*")) == []


def test_existing_intermediate_replaced_by_symlink_after_authorization(tmp_path_factory):
    """8: an existing intermediate directory swapped for a symlink is refused."""
    root = _tmp_authority(tmp_path_factory)
    external = Path(tempfile.mkdtemp()).resolve()
    (external / "sub").mkdir()
    (root / "mid" / "sub").mkdir(parents=True)
    authorized = ms.resolve_output_authority(root / "mid" / "sub" / "out", root)
    import shutil

    shutil.rmtree(root / "mid")
    (root / "mid").symlink_to(external, target_is_directory=True)
    with pytest.raises(ms.OutputAuthorityError):
        ms._atomic_write_governed(authorized, _G1, temp_root=root)
    assert list((external / "sub").rglob("*")) == []


def test_intermediate_renamed_and_replaced_by_a_real_directory(tmp_path_factory):
    """9: a *genuine* replacement directory is refused, not silently followed.

    This is the third-review blocker: the replacement is a real directory, so an
    ``O_NOFOLLOW`` walk accepts it.  The retained device/inode chain does not.
    """
    root = _tmp_authority(tmp_path_factory)
    (root / "mid" / "sub").mkdir(parents=True)
    authorized = ms.resolve_output_authority(root / "mid" / "sub" / "out", root)
    os.rename(root / "mid", root / "mid-old")
    (root / "mid" / "sub").mkdir(parents=True)
    with pytest.raises(ms.OutputAuthorityError):
        ms._atomic_write_governed(authorized, _G1, temp_root=root)
    # Publication must not have followed the replacement directory.
    assert list((root / "mid" / "sub").iterdir()) == []
    assert list((root / "mid-old" / "sub").iterdir()) == []


def test_ancestor_deleted_after_authorization_is_refused(tmp_path_factory):
    """11: a deleted ancestor fails closed rather than being recreated blindly."""
    root = _tmp_authority(tmp_path_factory)
    (root / "mid" / "sub").mkdir(parents=True)
    authorized = ms.resolve_output_authority(root / "mid" / "sub" / "out", root)
    import shutil

    shutil.rmtree(root / "mid")
    with pytest.raises(ms.OutputAuthorityError):
        ms._atomic_write_governed(authorized, _G1, temp_root=root)
    assert not (root / "mid").exists()


def test_symlinked_temporary_root_authority_is_refused(tmp_path_factory):
    """5: a symlinked temporary-root authority can redirect the whole tree.

    The legacy-repair pass removed the back-to-back ``_open_temp_publish_parent``
    fallback (a ``temp_root`` publication now *requires* its live retained
    authority), so the refusal is asserted on the surviving surfaces: both
    authorization APIs reject the symlinked root before any chain is established.
    """
    root = _tmp_authority(tmp_path_factory)
    link_parent = Path(tempfile.mkdtemp()).resolve()
    link = link_parent / "rootlink"
    link.symlink_to(root, target_is_directory=True)
    assert not hasattr(ms, "_open_temp_publish_parent"), (
        "the path-only temporary fallback must stay removed"
    )
    with pytest.raises(ms.OutputAuthorityError):
        ms.authorize_publication(root / "out", link)
    with pytest.raises(ms.OutputAuthorityError):
        ms.resolve_output_authority(root / "out", link)


def test_canonical_publication_retains_its_chain_anchoring():
    """1: canonical output still validates the repo -> experiments -> child chain."""
    exp_fd, child = ms._open_canonical_parent(ROOT)
    try:
        assert child == ms.CANONICAL_CHILD_NAME
    finally:
        os.close(exp_fd)


# --------------------------------------------------------------------------- #
# Second mandatory repair — BLOCKER 2: explicit transaction commit point
# --------------------------------------------------------------------------- #
#
# The complete new generation had already been installed and validated when
# backup cleanup deleted one old artifact and raised; the handler then removed
# the new directory and restored the partially deleted backup, leaving only two
# old files.  Cleanup now happens strictly after an explicit commit point and
# never rolls back.


def _publish(directory: Path, contents: dict) -> None:
    ms._atomic_write_governed(directory, contents)


def test_post_commit_cleanup_failure_preserves_the_complete_new_set(tmp_path, monkeypatch):
    """9/11/12: a partial backup cleanup must never corrupt the committed output."""
    d = tmp_path / "results_missingness"
    _publish(d, _G1)
    before_new = {n: _G2[n] for n in _G2}

    original = ms._rmtree_at
    names = sorted(ms.GOVERNED_OUTPUT_NAMES)

    def partial_then_fail(dir_fd, name):
        if name.startswith(f".{d.name}.backup."):
            # Delete the first old member, then fail — the exact reviewed defect.
            sub = os.open(name, os.O_RDONLY | os.O_DIRECTORY, dir_fd=dir_fd)
            try:
                os.unlink(names[0], dir_fd=sub)
            finally:
                os.close(sub)
            raise OSError("simulated post-commit cleanup failure")
        return original(dir_fd, name)

    monkeypatch.setattr(ms, "_rmtree_at", partial_then_fail)
    # Post-commit cleanup failure is non-fatal and must not roll back.
    _publish(d, _G2)
    monkeypatch.undo()

    published = _dir_hashes(d)
    assert sorted(published) == names, "the complete new set must remain visible"
    import hashlib

    for name, text in before_new.items():
        assert published[name] == hashlib.sha256(text.encode()).hexdigest()


def test_post_commit_cleanup_residue_is_swept_by_a_later_invocation(tmp_path, monkeypatch):
    """18: a later invocation cleans the clearly-identified residue safely."""
    d = tmp_path / "results_missingness"
    _publish(d, _G1)
    original = ms._rmtree_at

    def refuse_backup(dir_fd, name):
        if name.startswith(f".{d.name}.backup."):
            raise OSError("simulated cleanup failure")
        return original(dir_fd, name)

    monkeypatch.setattr(ms, "_rmtree_at", refuse_backup)
    _publish(d, _G2)
    monkeypatch.undo()
    residue = [e for e in os.listdir(d.parent) if e != d.name]
    assert residue, "a cleanup failure must leave identified residue, truthfully"

    _publish(d, _G1)
    assert [e for e in os.listdir(d.parent) if e != d.name] == []
    assert sorted(os.listdir(d)) == sorted(ms.GOVERNED_OUTPUT_NAMES)


def test_pre_commit_failure_restores_the_complete_old_generation(tmp_path, monkeypatch):
    """3-8: any pre-commit failure leaves the complete prior set byte-identical."""
    d = tmp_path / "results_missingness"
    _publish(d, _G1)
    before = _dir_hashes(d)

    def fail_validation(dir_fd, contents, *, label):
        if label == "published":
            raise ms.OutputAuthorityError("simulated pre-commit validation failure")
        return None

    monkeypatch.setattr(ms, "_validate_dir_contents", fail_validation)
    with pytest.raises(ms.OutputAuthorityError):
        _publish(d, _G2)
    monkeypatch.undo()

    after = _dir_hashes(d)
    assert after == before, "the complete old generation must be byte-identical"
    assert sorted(after) == sorted(ms.GOVERNED_OUTPUT_NAMES)


def test_no_prior_output_publishes_the_complete_new_set(tmp_path):
    """1: with no prior generation the complete new set is published."""
    d = tmp_path / "results_missingness"
    _publish(d, _G1)
    assert sorted(os.listdir(d)) == sorted(ms.GOVERNED_OUTPUT_NAMES)


def test_a_two_file_or_mixed_generation_is_never_visible(tmp_path, monkeypatch):
    """No accepted state is a two-file or mixed-generation set."""
    d = tmp_path / "results_missingness"
    _publish(d, _G1)
    original = ms._rmtree_at

    def wipe_backup_then_fail(dir_fd, name):
        if name.startswith(f".{d.name}.backup."):
            original(dir_fd, name)
            raise OSError("cleanup reported failure after removing the backup")
        return original(dir_fd, name)

    monkeypatch.setattr(ms, "_rmtree_at", wipe_backup_then_fail)
    _publish(d, _G2)
    monkeypatch.undo()
    assert sorted(os.listdir(d)) == sorted(ms.GOVERNED_OUTPUT_NAMES)


# --------------------------------------------------------------------------- #
# Second mandatory repair — BLOCKER 5: complete service-response replay guard
# --------------------------------------------------------------------------- #
#
# The durable internal baseline guard normalised away complete top-parameter
# detail, warnings, contributions, and inference-related fields, so mutating an
# omitted field did not fail the internal equality guard while the generated
# provenance language claimed a byte comparison of the service output.  The
# guard now compares the complete response as canonical serialized bytes.


def _baseline_response() -> dict:
    """A minimal but structurally complete service response for mutation tests."""
    return {
        "year": 2025,
        "user_type": "individual",
        "risk_level": "medium",
        "stock_count": 1,
        "disclaimer": "research support, not investment advice",
        "items": [
            {
                "ticker": "AAA",
                "score": 0.5,
                "confidence": 0.75,
                "confidence_label": "medium",
                "rank": 1,
                "missing_parameters": ["feat_x"],
                "is_inference_row": True,
                "warnings": ["research support, not investment advice"],
                "top_parameters": [
                    {
                        "name": "feat_a",
                        "weight": 0.25,
                        "value": 12.5,
                        "percentile_in_year": 88.8,
                        "contribution": 0.2,
                    },
                    {
                        "name": "feat_b",
                        "weight": 0.15,
                        "value": 3.5,
                        "percentile_in_year": 40.0,
                        "contribution": 0.06,
                    },
                ],
            }
        ],
    }


def _mutate(fn) -> dict:
    payload = _baseline_response()
    fn(payload)
    return payload


@pytest.mark.parametrize(
    "label, mutator",
    [
        ("ticker", lambda p: p["items"][0].__setitem__("ticker", "BBB")),
        ("score", lambda p: p["items"][0].__setitem__("score", 0.6)),
        ("confidence", lambda p: p["items"][0].__setitem__("confidence", 0.5)),
        ("rank", lambda p: p["items"][0].__setitem__("rank", 2)),
        ("missing_parameters", lambda p: p["items"][0].__setitem__("missing_parameters", [])),
        ("top_parameter_removed", lambda p: p["items"][0]["top_parameters"].pop()),
        (
            "top_parameter_reordered",
            lambda p: p["items"][0]["top_parameters"].reverse(),
        ),
        (
            "top_parameter_value",
            lambda p: p["items"][0]["top_parameters"][0].__setitem__("value", 99.9),
        ),
        (
            "weight",
            lambda p: p["items"][0]["top_parameters"][0].__setitem__("weight", 0.99),
        ),
        (
            "percentile",
            lambda p: p["items"][0]["top_parameters"][0].__setitem__(
                "percentile_in_year", 1.0
            ),
        ),
        (
            "contribution",
            lambda p: p["items"][0]["top_parameters"][0].__setitem__("contribution", 0.9),
        ),
        ("warning_removed", lambda p: p["items"][0]["warnings"].clear()),
        ("warning_added", lambda p: p["items"][0]["warnings"].append("extra")),
        ("warning_text", lambda p: p["items"][0]["warnings"].__setitem__(0, "changed")),
        ("confidence_label", lambda p: p["items"][0].__setitem__("confidence_label", "low")),
        ("inference_flag", lambda p: p["items"][0].__setitem__("is_inference_row", False)),
        ("top_level_year", lambda p: p.__setitem__("year", 2024)),
        ("top_level_disclaimer", lambda p: p.__setitem__("disclaimer", "other")),
        ("stock_count", lambda p: p.__setitem__("stock_count", 2)),
        ("new_nested_field", lambda p: p["items"][0].__setitem__("brand_new", 1)),
    ],
)
def test_every_public_field_mutation_is_detected(label, mutator):
    """2-19: mutating any public field breaks the canonical comparison."""
    baseline = ms.canonical_service_response(_baseline_response())
    mutated = ms.canonical_service_response(_mutate(mutator))
    assert baseline != mutated, f"{label} mutation must be detected"


def test_complete_unmasked_replay_matches_itself():
    """1: an unmutated response compares equal to itself."""
    assert ms.canonical_service_response(
        _baseline_response()
    ) == ms.canonical_service_response(_baseline_response())


def test_canonicalization_is_deterministic_and_key_order_independent():
    """20: canonicalization is stable and independent of dictionary insertion order."""
    payload = _baseline_response()
    reordered = json.loads(json.dumps(payload))
    reordered["items"][0] = dict(
        reversed(list(reordered["items"][0].items()))
    )
    assert ms.canonical_service_response(payload) == ms.canonical_service_response(
        reordered
    )


def test_a_future_field_of_an_unsupported_type_fails_closed():
    """19: an unforeseen value type causes a controlled schema-mismatch failure."""
    payload = _baseline_response()
    payload["items"][0]["exotic"] = {1, 2, 3}  # a set is not a supported JSON type
    with pytest.raises(ms.MissingnessError):
        ms.canonical_service_response(payload)


def test_nonfinite_and_special_scalars_are_deterministic():
    """NaN/infinity and numpy scalars map to explicit deterministic tokens."""
    assert ms._canonicalize_for_comparison(float("nan")) == "__nan__"
    assert ms._canonicalize_for_comparison(float("inf")) == "__+inf__"
    assert ms._canonicalize_for_comparison(float("-inf")) == "__-inf__"
    assert ms._canonicalize_for_comparison(np.float64(1.5)) == 1.5
    assert ms._canonicalize_for_comparison(np.int64(3)) == 3
    assert ms._canonicalize_for_comparison(np.bool_(True)) is True


def test_provenance_claim_matches_the_enforced_comparison(built):
    """21: the generated wording must describe exactly what is enforced."""
    audit = built["report"]["baseline_replay_audit"]
    compared = audit["compared_fields"]
    # Every field the mutation tests prove is enforced must be named.
    for expected in (
        "items[].warnings",
        "items[].is_inference_row",
        "items[].confidence_label",
        "items[].top_parameters[].contribution",
        "items[].top_parameters[].percentile_in_year",
        "items[].top_parameters[].weight",
        "items[].top_parameters[].value",
        "items[].missing_parameters",
    ):
        assert expected in compared, f"{expected} must be declared as compared"
    assert "complete service response" in audit["comparison_method"]
    assert audit["unmasked_replay_matches_service_output"] is True


# --------------------------------------------------------------------------- #
# Third mandatory repair — BLOCKER 1: authorized real-directory replacement
# --------------------------------------------------------------------------- #
#
# The bounded temporary output authority rejected a symlink replacement but
# accepted replacement of an already-authorized intermediate directory with a
# *different genuine directory*: an O_NOFOLLOW walk cannot tell the replacement
# apart from the original, so publication followed the replacement inode.  The
# authority now retains an open descriptor and the (st_dev, st_ino) identity of
# the root and of every authorized component, and revalidates the complete chain
# immediately before publication; a symlink replacement, a real-directory
# replacement, a rename-away, a deletion, or any identity mismatch at any
# component fails closed, and publication proceeds on the retained descriptors so
# a replacement is never followed.


def _mk_authority(tmp_path_factory) -> Path:
    return Path(tmp_path_factory.mktemp("retained-authority")).resolve()


def _publish_with_authority(authority) -> None:
    ms._atomic_write_governed(authority.destination, _G1, authority=authority)


def test_retained_authority_publishes_the_complete_set(tmp_path_factory):
    """Control: an untouched authorized chain still publishes all three artifacts."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid" / "sub").mkdir(parents=True)
    authority = ms.authorize_publication(root / "mid" / "sub" / "out", root)
    try:
        _publish_with_authority(authority)
    finally:
        authority.close()
    assert sorted(os.listdir(root / "mid" / "sub" / "out")) == sorted(
        ms.GOVERNED_OUTPUT_NAMES
    )


def test_immediate_ancestor_replaced_by_a_real_directory_is_refused(tmp_path_factory):
    """The blocker itself: the destination's own parent swapped for a real directory."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid" / "sub").mkdir(parents=True)
    authority = ms.authorize_publication(root / "mid" / "sub" / "out", root)
    try:
        os.rename(root / "mid" / "sub", root / "mid" / "sub-old")
        (root / "mid" / "sub").mkdir()
        with pytest.raises(ms.OutputAuthorityError) as excinfo:
            _publish_with_authority(authority)
    finally:
        authority.close()
    assert "device/inode" in str(excinfo.value)
    # Nothing was written into the replacement directory or the moved-away one.
    assert list((root / "mid" / "sub").iterdir()) == []
    assert list((root / "mid" / "sub-old").iterdir()) == []


def test_higher_ancestor_replaced_by_a_real_directory_is_refused(tmp_path_factory):
    """A replacement two levels up is caught just as the immediate parent is."""
    root = _mk_authority(tmp_path_factory)
    (root / "a" / "b" / "c").mkdir(parents=True)
    authority = ms.authorize_publication(root / "a" / "b" / "c" / "out", root)
    try:
        os.rename(root / "a", root / "a-old")
        (root / "a" / "b" / "c").mkdir(parents=True)
        with pytest.raises(ms.OutputAuthorityError):
            _publish_with_authority(authority)
    finally:
        authority.close()
    assert list((root / "a").rglob("*.json")) == []
    assert list((root / "a-old").rglob("*.json")) == []


def test_rename_away_plus_genuine_replacement_is_refused(tmp_path_factory):
    """Rename-away followed by an identically named genuine directory fails closed."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid" / "sub").mkdir(parents=True)
    decoy = root / "decoy"
    decoy.mkdir()
    (decoy / "sub").mkdir()
    authority = ms.authorize_publication(root / "mid" / "sub" / "out", root)
    try:
        os.rename(root / "mid", root / "mid-parked")
        os.rename(decoy, root / "mid")  # a real directory, never a symlink
        with pytest.raises(ms.OutputAuthorityError):
            _publish_with_authority(authority)
    finally:
        authority.close()
    assert list((root / "mid" / "sub").iterdir()) == []
    assert list((root / "mid-parked" / "sub").iterdir()) == []


def test_authorized_component_deleted_is_refused(tmp_path_factory):
    """A deleted authorized component fails closed instead of being recreated."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid" / "sub").mkdir(parents=True)
    authority = ms.authorize_publication(root / "mid" / "sub" / "out", root)
    import shutil

    try:
        shutil.rmtree(root / "mid")
        with pytest.raises(ms.OutputAuthorityError):
            _publish_with_authority(authority)
    finally:
        authority.close()
    assert not (root / "mid").exists()


def test_authorized_component_replaced_by_symlink_is_refused(tmp_path_factory):
    """The previously repaired symlink replacement still fails closed."""
    root = _mk_authority(tmp_path_factory)
    external = Path(tempfile.mkdtemp()).resolve()
    (external / "sub").mkdir()
    (root / "mid" / "sub").mkdir(parents=True)
    authority = ms.authorize_publication(root / "mid" / "sub" / "out", root)
    import shutil

    try:
        shutil.rmtree(root / "mid")
        (root / "mid").symlink_to(external, target_is_directory=True)
        with pytest.raises(ms.OutputAuthorityError):
            _publish_with_authority(authority)
    finally:
        authority.close()
    assert list((external / "sub").rglob("*")) == []


def test_authority_root_renamed_away_is_refused(tmp_path_factory):
    """The authority root itself must still identify the authorized inode."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid").mkdir()
    authority = ms.authorize_publication(root / "mid" / "out", root)
    try:
        os.rename(root, root.parent / (root.name + "-moved"))
        (root).mkdir()
        (root / "mid").mkdir()
        with pytest.raises(ms.OutputAuthorityError):
            _publish_with_authority(authority)
    finally:
        authority.close()
    assert list((root / "mid").iterdir()) == []


def test_absent_component_created_after_authorization_is_refused(tmp_path_factory):
    """A component that appears after authorization is foreign and is refused."""
    root = _mk_authority(tmp_path_factory)
    authority = ms.authorize_publication(root / "mid" / "out", root)
    try:
        (root / "mid").mkdir()  # created by someone else after authorization
        with pytest.raises(ms.OutputAuthorityError):
            _publish_with_authority(authority)
    finally:
        authority.close()
    assert list((root / "mid").iterdir()) == []


def test_absent_component_is_created_through_the_retained_descriptor(tmp_path_factory):
    """An untouched absent component is created through the authorized parent fd."""
    root = _mk_authority(tmp_path_factory)
    authority = ms.authorize_publication(root / "mid" / "deep" / "out", root)
    try:
        _publish_with_authority(authority)
    finally:
        authority.close()
    assert sorted(os.listdir(root / "mid" / "deep" / "out")) == sorted(
        ms.GOVERNED_OUTPUT_NAMES
    )


def test_legacy_path_plus_temp_root_call_is_protected_by_the_retained_chain(
    tmp_path_factory,
):
    """resolve_output_authority retains the chain, so the path-only call is safe too."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid" / "sub").mkdir(parents=True)
    authorized = ms.resolve_output_authority(root / "mid" / "sub" / "out", root)
    os.rename(root / "mid" / "sub", root / "mid" / "sub-old")
    (root / "mid" / "sub").mkdir()
    with pytest.raises(ms.OutputAuthorityError):
        ms._atomic_write_governed(authorized, _G1, temp_root=root)
    assert list((root / "mid" / "sub").iterdir()) == []


def test_released_authority_cannot_publish(tmp_path_factory):
    """A closed authority refuses publication instead of re-walking the pathname."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid").mkdir()
    authority = ms.authorize_publication(root / "mid" / "out", root)
    authority.close()
    with pytest.raises(ms.OutputAuthorityError):
        _publish_with_authority(authority)


def test_canonical_authority_retains_and_revalidates_its_chain():
    """The canonical destination is authorized through the same retained chain."""
    authority = ms.authorize_publication(None, None)
    try:
        assert authority.destination == ms.CANONICAL_RESULTS_DIR
        assert authority.child == ms.CANONICAL_CHILD_NAME
        parent_fd, child, revalidate_final = authority.open_publication_parent()
        try:
            assert child == ms.CANONICAL_CHILD_NAME
            assert ms.CANONICAL_CHILD_NAME in os.listdir(parent_fd)
            # The canonical final output directory exists, so its identity is
            # bound and revalidates cleanly against the untouched repository.
            assert authority.final_identity.existed is True
            revalidate_final()
        finally:
            os.close(parent_fd)
    finally:
        authority.close()


def test_retention_ledger_does_not_leak_descriptors(tmp_path_factory):
    """Retained authorities are bounded, so repeated authorization cannot leak fds."""
    root = _mk_authority(tmp_path_factory)
    for index in range(ms._RETENTION_LIMIT * 2):
        ms.resolve_output_authority(root / f"run-{index}" / "out", root)
    assert len(ms._RETAINED_AUTHORITIES) <= ms._RETENTION_LIMIT


# --------------------------------------------------------------------------- #
# FINAL REPAIR — BLOCKER 1: final authorized directory identity
# --------------------------------------------------------------------------- #
#
# The retained chain pinned every *intermediate* component but left the final
# output directory itself to a pathname check at publication time, so an existing
# authorized final directory could be replaced, renamed away, or deleted between
# authorization and publication and publication continued through whatever then
# occupied the name.  Both publication APIs — the structured
# ``authorize_publication`` object and the legacy ``resolve_output_authority`` +
# retained-ledger path — now bind the final directory's device/inode identity at
# authorization and revalidate it from the retained authority root before staging
# and again immediately before the swap.
#
# Each test below drives BOTH APIs through the same attack.


def _final_dest(root: Path) -> Path:
    """A destination whose parent exists and whose final directory pre-exists."""
    (root / "mid").mkdir(parents=True, exist_ok=True)
    out = root / "mid" / "out"
    out.mkdir(exist_ok=True)
    return out


def _structured_publish(root: Path, dest: Path, attack) -> None:
    """Authorize via the structured API, run ``attack``, then publish."""
    authority = ms.authorize_publication(dest, root)
    try:
        attack()
        with pytest.raises(ms.OutputAuthorityError) as excinfo:
            ms._atomic_write_governed(authority.destination, _G1, authority=authority)
    finally:
        authority.close()
    assert "failing closed" in str(excinfo.value)


def _legacy_publish(root: Path, dest: Path, attack) -> None:
    """Authorize via the legacy path-only API, run ``attack``, then publish."""
    authorized = ms.resolve_output_authority(dest, root)
    attack()
    with pytest.raises(ms.OutputAuthorityError) as excinfo:
        ms._atomic_write_governed(authorized, _G1, temp_root=root)
    assert "failing closed" in str(excinfo.value)


_PUBLISH_APIS = pytest.mark.parametrize(
    "publish",
    [
        pytest.param(_structured_publish, id="structured"),
        pytest.param(_legacy_publish, id="legacy"),
    ],
)


@_PUBLISH_APIS
def test_existing_final_directory_publishes_when_untouched(
    publish, tmp_path_factory
):
    """Control: an untouched pre-existing final directory still publishes."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    if publish is _structured_publish:
        authority = ms.authorize_publication(dest, root)
        try:
            ms._atomic_write_governed(authority.destination, _G1, authority=authority)
        finally:
            authority.close()
    else:
        authorized = ms.resolve_output_authority(dest, root)
        ms._atomic_write_governed(authorized, _G1, temp_root=root)
    assert sorted(os.listdir(dest)) == sorted(ms.GOVERNED_OUTPUT_NAMES)


@_PUBLISH_APIS
def test_final_directory_replaced_by_another_real_directory_fails_closed(
    publish, tmp_path_factory
):
    """The blocker itself: the final directory swapped for a different real directory."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    decoy = root / "decoy"
    decoy.mkdir()

    def attack():
        os.rename(dest, root / "mid" / "out-parked")
        os.rename(decoy, dest)  # a genuine directory, never a symlink

    publish(root, dest, attack)
    # Neither the replacement nor the parked original received any artifact.
    assert list(dest.iterdir()) == []
    assert list((root / "mid" / "out-parked").iterdir()) == []


@_PUBLISH_APIS
def test_final_directory_renamed_away_fails_closed(publish, tmp_path_factory):
    """A final directory renamed away (and nothing put back) fails closed."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)

    def attack():
        os.rename(dest, root / "mid" / "moved-elsewhere")

    publish(root, dest, attack)
    assert not dest.exists()
    assert list((root / "mid" / "moved-elsewhere").iterdir()) == []


@_PUBLISH_APIS
def test_final_directory_deleted_fails_closed(publish, tmp_path_factory):
    """A deleted final directory is never silently recreated and published into."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)

    def attack():
        dest.rmdir()

    publish(root, dest, attack)
    assert not dest.exists()


@_PUBLISH_APIS
def test_final_directory_replaced_by_symlink_fails_closed(publish, tmp_path_factory):
    """A symlink substituted for the authorized final directory is never followed."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    external = Path(tempfile.mkdtemp()).resolve()

    def attack():
        dest.rmdir()
        dest.symlink_to(external, target_is_directory=True)

    publish(root, dest, attack)
    assert list(external.iterdir()) == [], "the symlink target was written through"


@_PUBLISH_APIS
def test_final_directory_recreated_with_a_different_identity_fails_closed(
    publish, tmp_path_factory
):
    """Delete-then-recreate under the same name is a different inode and is refused."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    original = os.stat(dest)

    def attack():
        dest.rmdir()
        dest.mkdir()
        assert os.stat(dest).st_ino != original.st_ino, "fixture did not recycle"

    publish(root, dest, attack)
    assert list(dest.iterdir()) == []


@_PUBLISH_APIS
def test_absent_final_directory_replaced_by_a_foreign_directory_fails_closed(
    publish, tmp_path_factory
):
    """A directory appearing where none was authorized is foreign and is refused."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid").mkdir()
    dest = root / "mid" / "out"  # deliberately absent at authorization

    def attack():
        dest.mkdir()
        (dest / "foreign.txt").write_text("planted\n")

    publish(root, dest, attack)
    assert sorted(p.name for p in dest.iterdir()) == ["foreign.txt"]


@_PUBLISH_APIS
def test_absent_final_directory_replaced_by_a_symlink_fails_closed(
    publish, tmp_path_factory
):
    """A symlink appearing before governed creation fails closed, unfollowed."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid").mkdir()
    dest = root / "mid" / "out"
    external = Path(tempfile.mkdtemp()).resolve()

    def attack():
        dest.symlink_to(external, target_is_directory=True)

    publish(root, dest, attack)
    assert list(external.iterdir()) == []


@_PUBLISH_APIS
def test_absent_final_directory_replaced_by_a_regular_file_fails_closed(
    publish, tmp_path_factory
):
    """A plain file appearing under the governed name is refused, not overwritten."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid").mkdir()
    dest = root / "mid" / "out"

    def attack():
        dest.write_text("not a directory\n")

    publish(root, dest, attack)
    assert dest.read_text() == "not a directory\n"


def test_the_pre_repair_check_would_have_accepted_the_replacement(tmp_path_factory):
    """Evidence these tests are adversarial: the old pathname check still passes.

    Before the repair the publisher revalidated only the *intermediate* chain and
    then asked whether the child was a genuine directory.  Both conditions still
    hold after a real-directory replacement, so the old code published into the
    replacement; only the bound device/inode identity distinguishes them.
    """
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    authority = ms.authorize_publication(dest, root)
    try:
        os.rename(dest, root / "mid" / "parked")
        dest.mkdir()
        parent_fd = ms._open_dir_path(root / "mid")
        try:
            # The pre-repair predicate: exists, and is a genuine directory.
            assert ms._lstat_kind(parent_fd, "out") == (True, True)
        finally:
            os.close(parent_fd)
        with pytest.raises(ms.OutputAuthorityError) as excinfo:
            ms._atomic_write_governed(authority.destination, _G1, authority=authority)
    finally:
        authority.close()
    assert "device/inode" in str(excinfo.value)
    assert list(dest.iterdir()) == []


def test_existing_final_directory_identity_is_bound_at_authorization(
    tmp_path_factory,
):
    """Authorization records the exact inode of an existing final directory."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    info = os.stat(dest)
    authority = ms.authorize_publication(dest, root)
    try:
        identity = authority.final_identity
        assert identity.existed is True
        assert (identity.dev, identity.ino) == (info.st_dev, info.st_ino)
    finally:
        authority.close()


def test_absent_final_directory_is_recorded_as_absent_at_authorization(
    tmp_path_factory,
):
    """A destination that does not exist yet is authorized as absent, not pinned."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid").mkdir()
    authority = ms.authorize_publication(root / "mid" / "out", root)
    try:
        identity = authority.final_identity
        assert identity.existed is False
        assert identity.dev is None and identity.ino is None
    finally:
        authority.close()


def test_final_directory_binding_refuses_a_symlink_at_authorization(
    tmp_path_factory,
):
    """A destination that is already a symlink is refused before any work starts."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid").mkdir()
    external = Path(tempfile.mkdtemp()).resolve()
    (root / "mid" / "out").symlink_to(external, target_is_directory=True)
    with pytest.raises(ms.OutputAuthorityError):
        ms.authorize_publication(root / "mid" / "out", root)


def test_final_directory_replacement_is_caught_after_staging_too(
    tmp_path_factory, monkeypatch
):
    """A replacement that lands *during* staging is caught before the visible swap."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    (dest / "prior.txt").write_text("prior\n")
    authority = ms.authorize_publication(dest, root)

    real_validate = ms._validate_dir_contents
    swapped = {"done": False}

    def validate(dir_fd, contents, *, label):
        # The staging set has just been validated; swap the final directory for a
        # different genuine directory before the publisher reaches the rename.
        result = real_validate(dir_fd, contents, label=label)
        if label == "staging" and not swapped["done"]:
            swapped["done"] = True
            os.rename(dest, root / "mid" / "parked")
            dest.mkdir()
        return result

    monkeypatch.setattr(ms, "_validate_dir_contents", validate)
    try:
        with pytest.raises(ms.OutputAuthorityError) as excinfo:
            ms._atomic_write_governed(authority.destination, _G1, authority=authority)
    finally:
        authority.close()
    assert swapped["done"], "the fixture never performed the swap"
    assert "device/inode" in str(excinfo.value)
    assert list(dest.iterdir()) == []
    # The original generation was moved aside intact and was never disturbed.
    assert (root / "mid" / "parked" / "prior.txt").read_text() == "prior\n"


def test_canonical_final_directory_identity_is_bound_and_revalidated(tmp_path):
    """The canonical namespace is bound the same way (checked on a fake repo root)."""
    fake = tmp_path / "repo"
    (fake / ms.CANONICAL_PARENT_NAME / ms.CANONICAL_CHILD_NAME).mkdir(parents=True)
    exp_fd, child = ms._open_canonical_parent(fake)
    try:
        identity = ms._snapshot_final_directory(
            exp_fd, child, label="canonical final output directory"
        )
        assert identity.existed is True
        ms._revalidate_final_directory(exp_fd, child, identity)
        # Replace the canonical output directory with a different real directory.
        os.rename(
            fake / ms.CANONICAL_PARENT_NAME / child,
            fake / ms.CANONICAL_PARENT_NAME / "parked",
        )
        (fake / ms.CANONICAL_PARENT_NAME / child).mkdir()
        with pytest.raises(ms.OutputAuthorityError) as excinfo:
            ms._revalidate_final_directory(exp_fd, child, identity)
    finally:
        os.close(exp_fd)
    assert "replacement identity" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# FINAL LEGACY REPAIR — legacy final-directory identity/absence contract
# --------------------------------------------------------------------------- #
#
# The structured ``authorize_publication`` API bound and revalidated the final
# governed directory correctly, but the legacy ``resolve_output_authority`` +
# retained-ledger flow accepted **in-root symlink substitution** of that
# directory: the publisher fully resolved the destination pathname, so a symlink
# planted at the governed final component silently retargeted publication at the
# link's target *and* changed the destination string, which made the retained
# authority unfindable.  The flow then fell back to path-only validation and
# re-authorized the attacker's target (legitimately inside the authorized root),
# writing all three artifacts into the replacement.  Both an existing authorized
# directory and an unexpected symlink appearing where the directory was absent
# published into the replacement.
#
# The repair keeps the governed final component as a *name* when a destination is
# canonicalized (``_normalize_publication_path``), so a substitution can no longer
# change which authority applies, and it removes the silent path-only fallback:
# a destination the legacy API authorized may only be published through its live
# retained authority, and a temporary-root publication requires one.
#
# Every test below drives the attack through all three publication surfaces.


def _in_root_hijack(root: Path) -> Path:
    """A genuine directory inside the authorized root — the in-root symlink target."""
    hijack = root / "hijack"
    hijack.mkdir()
    return hijack


def _external_hijack() -> Path:
    """A genuine directory outside the authorized root."""
    return Path(tempfile.mkdtemp(prefix="miss-external-hijack-")).resolve()


def _legacy_preresolved_publish(root: Path, dest: Path, attack) -> None:
    """Legacy authorize, attack, then publish the path a caller resolved itself.

    Strictly harder than :func:`_legacy_publish`: it reproduces exactly what the
    pre-repair ``write_outputs`` did to its ``results_dir`` argument, so the
    publisher is handed the attacker's target path rather than the governed one.
    """
    authorized = ms.resolve_output_authority(dest, root)
    attack()
    handed = Path(authorized).resolve()
    with pytest.raises(ms.OutputAuthorityError) as excinfo:
        ms._atomic_write_governed(handed, _G1, temp_root=root)
    assert "failing closed" in str(excinfo.value)


_ALL_PUBLISH_APIS = pytest.mark.parametrize(
    "publish",
    [
        pytest.param(_structured_publish, id="structured"),
        pytest.param(_legacy_publish, id="legacy"),
        pytest.param(_legacy_preresolved_publish, id="legacy-preresolved"),
    ],
)


@_ALL_PUBLISH_APIS
def test_existing_final_directory_replaced_by_in_root_symlink_fails_closed(
    publish, tmp_path_factory
):
    """The reported blocker: in-root symlink substitution of an existing directory."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    hijack = _in_root_hijack(root)

    def attack():
        dest.rmdir()
        dest.symlink_to(hijack, target_is_directory=True)

    publish(root, dest, attack)
    assert list(hijack.iterdir()) == [], "the in-root symlink target was published into"
    assert dest.is_symlink(), "the planted link should be refused, not consumed"


@_ALL_PUBLISH_APIS
def test_absent_final_directory_replaced_by_in_root_symlink_fails_closed(
    publish, tmp_path_factory
):
    """The reported blocker's second half: an in-root symlink appears where absent."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid").mkdir()
    dest = root / "mid" / "out"  # deliberately absent at authorization
    hijack = _in_root_hijack(root)

    def attack():
        dest.symlink_to(hijack, target_is_directory=True)

    publish(root, dest, attack)
    assert list(hijack.iterdir()) == [], "the in-root symlink target was published into"


@_ALL_PUBLISH_APIS
def test_existing_final_directory_replaced_by_external_symlink_fails_closed_all_apis(
    publish, tmp_path_factory
):
    """External symlink variant, including the pre-resolved legacy surface."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    hijack = _external_hijack()

    def attack():
        dest.rmdir()
        dest.symlink_to(hijack, target_is_directory=True)

    publish(root, dest, attack)
    assert list(hijack.iterdir()) == []


@_ALL_PUBLISH_APIS
def test_absent_final_directory_replaced_by_external_symlink_fails_closed_all_apis(
    publish, tmp_path_factory
):
    """External symlink appearing where the final directory was absent."""
    root = _mk_authority(tmp_path_factory)
    (root / "mid").mkdir()
    dest = root / "mid" / "out"
    hijack = _external_hijack()

    def attack():
        dest.symlink_to(hijack, target_is_directory=True)

    publish(root, dest, attack)
    assert list(hijack.iterdir()) == []


@_ALL_PUBLISH_APIS
def test_final_directory_symlinked_to_a_nested_in_root_path_fails_closed(
    publish, tmp_path_factory
):
    """A link deeper inside the authorized root is refused like any other."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    nested = root / "deep" / "nested" / "target"
    nested.mkdir(parents=True)

    def attack():
        dest.rmdir()
        dest.symlink_to(nested, target_is_directory=True)

    publish(root, dest, attack)
    assert list(nested.iterdir()) == []


@_ALL_PUBLISH_APIS
def test_final_directory_real_replacement_deletion_rename_recreation_all_apis(
    publish, tmp_path_factory
):
    """Real-directory replacement, deletion, rename-away and recreation, all APIs.

    The first two publication surfaces are already covered above; this repeats the
    four non-symlink attacks across all three so the pre-resolved legacy surface is
    held to the identical contract.
    """
    root = _mk_authority(tmp_path_factory)

    # (a) replacement by a different genuine directory
    dest = _final_dest(root)
    decoy = root / "decoy"
    decoy.mkdir()

    def replace():
        os.rename(dest, root / "mid" / "parked")
        os.rename(decoy, dest)

    publish(root, dest, replace)
    assert list(dest.iterdir()) == []
    assert list((root / "mid" / "parked").iterdir()) == []

    # (b) rename-away, (c) deletion, (d) delete-then-recreate
    for index, attack_name in enumerate(("renamed", "deleted", "recreated")):
        sub = _mk_authority(tmp_path_factory)
        target = _final_dest(sub)
        original_ino = os.stat(target).st_ino

        def attack(target=target, sub=sub, attack_name=attack_name, original_ino=original_ino):
            if attack_name == "renamed":
                os.rename(target, sub / "mid" / f"moved-{index}")
            elif attack_name == "deleted":
                target.rmdir()
            else:
                target.rmdir()
                target.mkdir()
                assert os.stat(target).st_ino != original_ino, "fixture recycled the inode"

        publish(sub, target, attack)
        if attack_name == "renamed":
            assert not target.exists()
            assert list((sub / "mid" / f"moved-{index}").iterdir()) == []
        elif attack_name == "deleted":
            assert not target.exists()
        else:
            assert list(target.iterdir()) == []


def test_the_pre_repair_resolution_would_have_retargeted_the_legacy_flow(
    tmp_path_factory,
):
    """Evidence the attack is real: full resolution still lands in the hijack dir.

    The pre-repair publisher did ``results_dir.resolve()``.  That value is shown
    here to be the attacker's in-root target, and the ledger key computed from it
    does not match the key the authorization retained — which is precisely why the
    old code lost its authority and re-derived one from the replacement path.  The
    repaired normalization keeps the governed name, so the key still matches.
    """
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    hijack = _in_root_hijack(root)
    authorized = ms.resolve_output_authority(dest, root)
    retained_key = ms._authority_key(authorized, root)
    assert retained_key in ms._RETAINED_AUTHORITIES

    dest.rmdir()
    dest.symlink_to(hijack, target_is_directory=True)

    # The pre-repair behaviour, reproduced verbatim.
    pre_repair = Path(authorized).resolve()
    assert pre_repair == hijack, "the attack no longer retargets full resolution"
    assert ms._authority_key(pre_repair, root) not in ms._RETAINED_AUTHORITIES

    # The repaired canonicalization is stable under the substitution.
    assert ms._normalize_publication_path(authorized) == Path(authorized)
    assert ms._authority_key(authorized, root) == retained_key

    # And the resolution target itself is refused as a claim alias.
    with pytest.raises(ms.OutputAuthorityError) as excinfo:
        ms._atomic_write_governed(pre_repair, _G1, temp_root=root)
    assert "failing closed" in str(excinfo.value)
    assert list(hijack.iterdir()) == []


def test_normalize_publication_path_never_follows_the_final_component(tmp_path):
    """Unit contract: the parent chain is resolved, the governed name is not."""
    (tmp_path / "real").mkdir()
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "real", target_is_directory=True)
    assert ms._normalize_publication_path(link) == tmp_path / "link"
    assert link.resolve() == tmp_path / "real"
    # An absent destination normalizes to itself, and a symlinked *parent* is
    # resolved (only the final component is protected from resolution).
    assert ms._normalize_publication_path(tmp_path / "absent") == tmp_path / "absent"
    assert ms._normalize_publication_path(link / "child") == tmp_path / "real" / "child"


# --- legacy retained-authority states: missing / released / stale / mismatched --


def test_missing_legacy_retained_authority_fails_closed(tmp_path_factory):
    """An authority evicted from the ledger must not degrade to path-only checks."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    authorized = ms.resolve_output_authority(dest, root)
    evicted = ms._RETAINED_AUTHORITIES.pop(ms._authority_key(authorized, root))
    evicted.close()
    with pytest.raises(ms.OutputAuthorityError) as excinfo:
        ms._atomic_write_governed(authorized, _G1, temp_root=root)
    assert "failing closed" in str(excinfo.value)
    assert list(dest.iterdir()) == []


def test_released_legacy_retained_authority_fails_closed(tmp_path_factory):
    """A retained authority closed behind the ledger's back cannot publish."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    authorized = ms.resolve_output_authority(dest, root)
    ms._RETAINED_AUTHORITIES[ms._authority_key(authorized, root)].close()
    with pytest.raises(ms.OutputAuthorityError) as excinfo:
        ms._atomic_write_governed(authorized, _G1, temp_root=root)
    assert "already released" in str(excinfo.value)
    assert list(dest.iterdir()) == []


def test_consumed_legacy_retained_authority_requires_reauthorization(tmp_path_factory):
    """Publication consumes the authority; a second publication must re-authorize."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    authorized = ms.resolve_output_authority(dest, root)
    ms._atomic_write_governed(authorized, _G1, temp_root=root)
    assert sorted(os.listdir(dest)) == sorted(ms.GOVERNED_OUTPUT_NAMES)
    before = _dir_hashes(dest)
    with pytest.raises(ms.OutputAuthorityError) as excinfo:
        ms._atomic_write_governed(authorized, _G2, temp_root=root)
    assert "re-authorize" in str(excinfo.value)
    # The published generation is untouched by the refused second attempt.
    assert _dir_hashes(dest) == before
    _no_residue(dest.parent)
    # Re-authorizing is the supported way forward, and it still works.
    reauthorized = ms.resolve_output_authority(dest, root)
    ms._atomic_write_governed(reauthorized, _G2, temp_root=root)
    assert _dir_hashes(dest) == _dir_hashes_of(_G2)


def test_stale_legacy_retained_authority_fails_closed(tmp_path_factory):
    """A retained chain whose authority root was renamed away is stale and refused."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    authorized = ms.resolve_output_authority(dest, root)
    os.rename(root, root.parent / (root.name + "-moved"))
    try:
        with pytest.raises(ms.OutputAuthorityError) as excinfo:
            ms._atomic_write_governed(authorized, _G1, temp_root=root)
        assert "failing closed" in str(excinfo.value)
        moved_dest = root.parent / (root.name + "-moved") / "mid" / "out"
        assert list(moved_dest.iterdir()) == []
    finally:
        os.rename(root.parent / (root.name + "-moved"), root)


def test_mismatched_legacy_temp_root_authority_fails_closed(tmp_path_factory):
    """The same destination under a *different* temp-root authority is refused."""
    root = _mk_authority(tmp_path_factory)
    other_root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    authorized = ms.resolve_output_authority(dest, root)
    with pytest.raises(ms.OutputAuthorityError) as excinfo:
        ms._atomic_write_governed(authorized, _G1, temp_root=other_root)
    assert "failing closed" in str(excinfo.value)
    assert list(dest.iterdir()) == []


def test_mismatched_structured_authority_object_fails_closed(tmp_path_factory):
    """An authority for another destination cannot publish this one (or itself)."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    other = root / "mid" / "other"
    other.mkdir()
    authority = ms.authorize_publication(dest, root)
    try:
        with pytest.raises(ms.OutputAuthorityError) as excinfo:
            ms._atomic_write_governed(other, _G1, authority=authority)
    finally:
        authority.close()
    assert "mismatched authority" in str(excinfo.value)
    assert list(other.iterdir()) == []
    assert list(dest.iterdir()) == []


def test_temp_root_publication_without_any_authority_fails_closed(tmp_path_factory):
    """A temp-root publication that never authorized anything is refused outright."""
    root = _mk_authority(tmp_path_factory)
    dest = root / "mid" / "out"
    dest.mkdir(parents=True)
    with pytest.raises(ms.OutputAuthorityError) as excinfo:
        ms._atomic_write_governed(dest, _G1, temp_root=root)
    assert "requires the live retained authority" in str(excinfo.value)
    assert list(dest.iterdir()) == []


def test_retention_limit_eviction_fails_closed_instead_of_falling_back(
    tmp_path_factory,
):
    """An authority evicted by the retention limit demands re-authorization."""
    root = _mk_authority(tmp_path_factory)
    dest = _final_dest(root)
    authorized = ms.resolve_output_authority(dest, root)
    for index in range(ms._RETENTION_LIMIT + 1):
        ms.resolve_output_authority(root / f"filler-{index}" / "out", root)
    assert ms._authority_key(authorized, root) not in ms._RETAINED_AUTHORITIES
    with pytest.raises(ms.OutputAuthorityError) as excinfo:
        ms._atomic_write_governed(authorized, _G1, temp_root=root)
    assert "re-authorize" in str(excinfo.value)
    assert list(dest.iterdir()) == []


def test_legacy_claims_hold_no_descriptors(tmp_path_factory):
    """The claim ledger records key strings only — it can never leak a descriptor."""
    root = _mk_authority(tmp_path_factory)
    for index in range(ms._RETENTION_LIMIT * 2):
        ms.resolve_output_authority(root / f"claim-{index}" / "out", root)
    assert len(ms._RETAINED_AUTHORITIES) <= ms._RETENTION_LIMIT
    assert all(
        isinstance(entry, tuple)
        and len(entry) == 2
        and all(isinstance(part, str) for part in entry)
        for entry in ms._LEGACY_CLAIMS
    )


# --- untouched controls and the zero-unauthorized-write sweep ------------------


@pytest.mark.parametrize("preexisting", [True, False], ids=["existing", "absent"])
def test_untouched_legacy_and_structured_controls_publish(preexisting, tmp_path_factory):
    """Controls: with no attack, both APIs publish exactly the three artifacts."""
    for api in ("legacy", "structured"):
        root = _mk_authority(tmp_path_factory)
        (root / "mid").mkdir()
        dest = root / "mid" / "out"
        if preexisting:
            dest.mkdir()
        if api == "legacy":
            authorized = ms.resolve_output_authority(dest, root)
            ms._atomic_write_governed(authorized, _G1, temp_root=root)
        else:
            authority = ms.authorize_publication(dest, root)
            try:
                ms._atomic_write_governed(authority.destination, _G1, authority=authority)
            finally:
                authority.close()
        assert _dir_hashes(dest) == _dir_hashes_of(_G1)
        _no_residue(dest.parent)


def _governed_files_under(*roots: Path) -> list[str]:
    """Every governed artifact basename found anywhere beneath ``roots``."""
    found: list[str] = []
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.name in ms.GOVERNED_OUTPUT_NAMES and not path.is_symlink():
                found.append(str(path))
    return sorted(found)


def test_no_attack_variant_writes_any_artifact_anywhere(tmp_path_factory):
    """Sweep: after every attack, no governed artifact exists anywhere at all.

    Covers both publication-relevant trees — the authorized root (which holds the
    in-root symlink target, the parked original, the decoy and the nested target)
    and the external symlink target — so a partial or misdirected write cannot
    hide outside the directory a single assertion happens to inspect.
    """
    def in_root_existing(root, dest, hijack):
        dest.mkdir()
        return lambda: (dest.rmdir(), dest.symlink_to(hijack, target_is_directory=True))

    def in_root_absent(root, dest, hijack):
        return lambda: dest.symlink_to(hijack, target_is_directory=True)

    def real_replacement(root, dest, hijack):
        dest.mkdir()

        def attack():
            os.rename(dest, root / "mid" / "parked")
            os.rename(hijack, dest)

        return attack

    def deletion(root, dest, hijack):
        dest.mkdir()
        return dest.rmdir

    def rename_away(root, dest, hijack):
        dest.mkdir()
        return lambda: os.rename(dest, root / "mid" / "parked")

    def recreation(root, dest, hijack):
        dest.mkdir()

        def attack():
            dest.rmdir()
            dest.mkdir()

        return attack

    setups = [in_root_existing, in_root_absent, real_replacement, deletion,
              rename_away, recreation]
    publishers = [_structured_publish, _legacy_publish, _legacy_preresolved_publish]

    for setup in setups:
        for publish in publishers:
            for external in (False, True):
                root = _mk_authority(tmp_path_factory)
                (root / "mid").mkdir()
                dest = root / "mid" / "out"
                hijack = _external_hijack() if external else (root / "hijack")
                if not external:
                    hijack.mkdir()
                attack = setup(root, dest, hijack)
                publish(root, dest, attack)
                leaked = _governed_files_under(root, hijack)
                assert leaked == [], (
                    f"{setup.__name__}/{publish.__name__}"
                    f"/{'external' if external else 'in-root'} wrote {leaked}"
                )
