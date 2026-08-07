"""Enforce the per-cell provenance artifact (passports v2, R4-PROV-01).

The provenance artifact is a lineage record only: it states where each cell of
``modeling_dataset_public_2020_2025.csv`` was copied or computed from and how
strong that evidence is. It certifies nothing about point-in-time correctness,
source accuracy, data-rights clearance, or predictive value, and these tests
assert that no such claim leaked in.

Pure helpers take their inputs explicitly so the negative tests exercise the
fail-closed paths without mutating the working tree.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
from pathlib import Path

import pytest

from scripts.data_collection import build_cell_provenance as bcp


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPO_ROOT / bcp.DATASET_REL
CSV_PATH = REPO_ROOT / bcp.OUT_CSV_REL
JSON_PATH = REPO_ROOT / bcp.OUT_JSON_REL
MD_PATH = REPO_ROOT / bcp.OUT_MD_REL
REGISTRY_PATH = REPO_ROOT / "artifact_registry.json"
MAKEFILE_PATH = REPO_ROOT / "Makefile"
PASSPORTS_V1_PATH = REPO_ROOT / bcp.PASSPORTS_V1_REL

PASSPORT_V1_FIELDS = {
    "name",
    "registry_role",
    "source_class",
    "transform_chain",
    "leakage_risk",
    "acceptance_status",
    "caveats",
    "evidence_files",
}

VALUE_PRESERVATION_ROOTS = ("data/trusted_clean", "experiments")
PROTECTED_FILES = (
    "data/trusted_clean/modeling_dataset_public_2020_2025.csv",
    "data/trusted_clean/modeling_dataset_2020_2025.csv",
    "data/trusted_clean/modeling_dataset_training_2020_2025.csv",
    "data/trusted_clean/feature_passports.json",
    "data/trusted_clean/data_dictionary.md",
    "model_confidence_contract.json",
    "docs/limitations_register.md",
)


# --------------------------------------------------------------------------- #
# Loading helpers
# --------------------------------------------------------------------------- #
def load_records() -> list[dict[str, str]]:
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_report() -> dict:
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def load_dataset() -> tuple[list[str], list[dict[str, str]]]:
    text = DATASET_PATH.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader.fieldnames or []), [dict(row) for row in reader]


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_tree(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    return {
        str(p.relative_to(REPO_ROOT).as_posix()): sha256_of(p)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


@pytest.fixture(scope="module")
def records() -> list[dict[str, str]]:
    return load_records()


@pytest.fixture(scope="module")
def report() -> dict:
    return load_report()


@pytest.fixture(scope="module")
def dataset() -> tuple[list[str], list[dict[str, str]]]:
    return load_dataset()


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> Path:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    path.write_text(buffer.getvalue(), encoding="utf-8", newline="")
    return path


# --------------------------------------------------------------------------- #
# Cell-key semantics
# --------------------------------------------------------------------------- #
def test_record_count_equals_rows_times_columns(records, dataset):
    columns, rows = dataset
    assert len(records) == len(rows) * len(columns)
    assert len(records) == 14640


def test_cell_ids_are_the_full_cartesian_product(records, dataset):
    columns, rows = dataset
    expected = {
        bcp.make_cell_id(r["ticker"], bcp.normalize_year(r["year"]), column)
        for r in rows
        for column in columns
    }
    actual = [r["cell_id"] for r in records]
    assert len(actual) == len(set(actual)), "duplicate cell_id in the artifact"
    assert set(actual) == expected


def test_cell_id_parses_back_to_its_parts(records):
    for record in records:
        ticker, year, column = record["cell_id"].split(bcp.CELL_KEY_SEPARATOR)
        assert ticker == record["ticker"]
        assert year == f"{int(record['year']):04d}"
        assert column == record["column"]
        assert bcp.CELL_KEY_SEPARATOR not in ticker + year + column
        assert ticker.isascii()


def test_every_column_and_every_row_key_is_complete(records, dataset):
    columns, rows = dataset
    per_column: dict[str, int] = {}
    per_key: dict[tuple[str, str], int] = {}
    for record in records:
        per_column[record["column"]] = per_column.get(record["column"], 0) + 1
        key = (record["ticker"], record["year"])
        per_key[key] = per_key.get(key, 0) + 1
    assert set(per_column) == set(columns)
    assert set(per_column.values()) == {len(rows)}
    assert len(per_key) == len(rows)
    assert set(per_key.values()) == {len(columns)}


# --------------------------------------------------------------------------- #
# Raw-source provenance
# --------------------------------------------------------------------------- #
def index_by_cell(records: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {r["cell_id"]: r for r in records}


def test_corrected_yearly_cell_carries_its_frozen_source(records):
    record = index_by_cell(records)["AEFES|2020|revenue"]
    assert record["evidence_level"] == "cell_verified"
    assert record["source_artifact"] == bcp.CORRECTED_YEARLY_REL
    assert record["source_field"] == "revenue"
    assert record["source_class"] == "corrected_yearly_csv"
    assert record["transform_id"] == "T_COPY"
    assert record["source_effective_year"] == "2020"

    margin = index_by_cell(records)["AEFES|2020|gross_margin"]
    assert margin["source_field"] == "gross_profit_margin"
    assert margin["source_artifact"] == bcp.CORRECTED_YEARLY_REL


def test_2024_override_cells_are_labelled_and_counted(records, report):
    record = index_by_cell(records)["AEFES|2024|total_assets"]
    assert record["source_class"] == "corrected_balance_2024"
    assert record["transform_id"] == "T_OVERRIDE_2024"
    assert record["source_artifact"] == bcp.BALANCE_2024_REL
    assert record["evidence_level"] == "cell_verified"

    override_cells = [r for r in records if r["source_class"] == "corrected_balance_2024"]
    assert report["counts_by_source_class"]["corrected_balance_2024"] == len(override_cells)
    assert {r["year"] for r in override_cells} == {"2024"}
    assert all(r["evidence_level"] == "cell_verified" for r in override_cells)


def test_non_2024_balance_cell_resolves_to_the_vendor_snapshot(records):
    index = index_by_cell(records)
    record = index["AEFES|2021|total_assets"]
    assert record["source_artifact"] == bcp.VENDOR_SNAPSHOT_REL
    assert record["source_class"] == "vendor_xlsx"
    assert record["transform_id"] == "T_COPY"

    equity = index["AEFES|2021|equity"]
    assert equity["source_artifact"] == bcp.VENDOR_SNAPSHOT_REL
    assert equity["source_field"] == "total_equity"


def test_price_and_benchmark_cells_resolve_to_their_frozen_yahoo_sources(records):
    index = index_by_cell(records)
    price = index["AEFES|2021|price_adjclose_t"]
    assert price["source_artifact"] == bcp.PRICES_REL
    assert price["source_field"] == "year_end_close"
    assert price["source_class"] == "yahoo_fetch"

    bench = index["AEFES|2021|benchmark_same_year_return_pct"]
    assert bench["source_artifact"] == bcp.BENCHMARK_REL
    assert bench["source_field"] == "bist100_return_pct"
    assert bench["source_class"] == "yahoo_fetch"
    assert bench["source_effective_year"] == "2021"


# --------------------------------------------------------------------------- #
# Derived-value lineage
# --------------------------------------------------------------------------- #
def test_excess_return_names_exactly_its_two_same_row_inputs(records):
    index = index_by_cell(records)
    record = index["AEFES|2020|next_year_excess_return_vs_bist100"]
    assert record["evidence_level"] == "derived_chain"
    assert record["upstream_cells"].split(bcp.UPSTREAM_SEPARATOR) == [
        "AEFES|2020|next_year_return_pct",
        "AEFES|2020|next_year_bist100_return_pct",
    ]
    for cell_id in record["upstream_cells"].split(bcp.UPSTREAM_SEPARATOR):
        assert cell_id in index


def test_flag_columns_name_their_frozen_upstream_cells(records):
    index = index_by_cell(records)
    for column in ("has_target", "is_inference_row"):
        record = index[f"AEFES|2020|{column}"]
        assert record["upstream_cells"] == "AEFES|2020|next_year_return_pct"
        assert record["evidence_level"] == "derived_chain"
    outperform = index["AEFES|2020|next_year_outperform_bist100"]
    assert outperform["upstream_cells"] == "AEFES|2020|next_year_excess_return_vs_bist100"


def test_next_year_benchmark_lineage_never_fabricates_an_absent_cell(records):
    index = index_by_cell(records)
    present = index["AEFES|2024|next_year_bist100_return_pct"]
    assert present["upstream_cells"] == "AEFES|2025|benchmark_same_year_return_pct"
    assert present["transform_id"] == "T_SHIFT_T1"

    # 2026 is outside the dataset, so no upstream cell exists and none is invented.
    terminal = index["AEFES|2025|next_year_bist100_return_pct"]
    assert terminal["upstream_cells"] == ""
    assert terminal["value_state"] == "null"
    assert terminal["evidence_level"] == "derived_chain"
    assert terminal["resolution_note"] == "null_preserved"


def test_price_window_lineage_matches_the_committed_window_semantics(records):
    index = index_by_cell(records)
    mom1 = index["AEFES|2022|price_momentum_1y_pct"]
    assert mom1["upstream_cells"].split(bcp.UPSTREAM_SEPARATOR) == [
        "AEFES|2021|price_adjclose_t",
        "AEFES|2022|price_adjclose_t",
    ]
    mom2 = index["AEFES|2022|price_momentum_2y_pct"]
    assert mom2["upstream_cells"].split(bcp.UPSTREAM_SEPARATOR) == [
        "AEFES|2020|price_adjclose_t",
        "AEFES|2022|price_adjclose_t",
    ]
    drawdown = index["AEFES|2022|price_drawdown_from_3y_high_pct"]
    assert drawdown["upstream_cells"].split(bcp.UPSTREAM_SEPARATOR) == [
        "AEFES|2020|price_adjclose_t",
        "AEFES|2021|price_adjclose_t",
        "AEFES|2022|price_adjclose_t",
    ]
    versus = index["AEFES|2022|price_vs_bist100_1y_pct"]
    assert versus["upstream_cells"].endswith("AEFES|2022|benchmark_same_year_return_pct")
    assert index["AEFES|2020|price_history_years_available"]["upstream_cells"] == (
        "AEFES|2020|price_adjclose_t"
    )


def test_upstream_cells_have_no_self_reference_and_no_cycle(records):
    graph = {
        r["cell_id"]: (
            r["upstream_cells"].split(bcp.UPSTREAM_SEPARATOR) if r["upstream_cells"] else []
        )
        for r in records
    }
    for cell_id, parents in graph.items():
        assert cell_id not in parents
        for parent in parents:
            assert parent in graph, f"dangling upstream cell {parent}"
    bcp._assert_acyclic(graph)  # terminates == acyclic


# --------------------------------------------------------------------------- #
# Multi-source lineage
# --------------------------------------------------------------------------- #
def test_multi_candidate_population_matches_the_report_and_uses_priority(records, report):
    flagged = [
        r for r in records if r["resolution_note"] == "multi_candidate_priority_applied"
    ]
    assert report["multi_candidate_count"] == len(flagged)
    assert sorted(r["cell_id"] for r in flagged) == report["multi_candidate_cells"]
    for record in flagged:
        assert record["evidence_level"] == "cell_verified"
        if record["column"] in bcp.BALANCE_COLUMNS and record["year"] == "2024":
            assert record["source_artifact"] == bcp.BALANCE_2024_REL


def test_priority_one_wins_wherever_the_override_verifies(records):
    """No 2024 balance cell verified by the override may be attributed elsewhere."""
    for record in records:
        if record["year"] != "2024" or record["column"] not in bcp.BALANCE_COLUMNS:
            continue
        if record["source_artifact"] == bcp.VENDOR_SNAPSHOT_REL:
            # priority-2 attribution is only legitimate when priority 1 did not verify
            assert record["source_class"] == "vendor_xlsx"
            assert record["transform_id"] == "T_COPY"


# --------------------------------------------------------------------------- #
# Unknown provenance
# --------------------------------------------------------------------------- #
def test_no_record_has_an_empty_evidence_level_and_no_unknown_is_silent(records):
    for record in records:
        assert record["evidence_level"] in bcp.EVIDENCE_LEVELS
        assert record["source_class"] in bcp.SOURCE_CLASSES
        assert record["transform_id"] in bcp.TRANSFORM_IDS
        assert record["resolution_note"] in bcp.RESOLUTION_NOTES
        if record["evidence_level"] == "unknown":
            assert record["resolution_note"] != ""
        if record["resolution_note"] == "":
            assert record["evidence_level"] == "cell_verified"


def test_report_unknown_cells_is_complete_and_sorted(records, report):
    unknown = sorted(r["cell_id"] for r in records if r["evidence_level"] == "unknown")
    assert report["unknown_cells"] == unknown
    assert report["unknown_cells"] == sorted(report["unknown_cells"])
    assert report["unknown_count"] == len(unknown)


def test_null_cells_are_preserved_nulls_not_unknowns(records, dataset):
    columns, rows = dataset
    dataset_nulls = sum(1 for row in rows for column in columns if row[column] == "")
    null_records = [r for r in records if r["value_state"] == "null"]
    assert len(null_records) == dataset_nulls
    for record in null_records:
        assert record["transform_id"] == "T_NULL_PRESERVED"
        assert record["resolution_note"] == "null_preserved"
        assert record["source_artifact"] == ""
        assert record["source_field"] == ""
        assert record["evidence_level"] in {"derived_chain", "column_asserted"}


def test_value_state_matches_the_dataset_cell_by_cell(records, dataset):
    columns, rows = dataset
    index = index_by_cell(records)
    for row in rows:
        ticker = row["ticker"]
        year = bcp.normalize_year(row["year"])
        for column in columns:
            record = index[bcp.make_cell_id(ticker, year, column)]
            expected = "null" if row[column] == "" else "present"
            assert record["value_state"] == expected


# --------------------------------------------------------------------------- #
# Deterministic ordering
# --------------------------------------------------------------------------- #
def test_records_are_in_ticker_year_column_index_order(records, dataset):
    columns, _ = dataset
    index_of = {column: i for i, column in enumerate(columns)}
    keys = [(r["ticker"], r["year"], index_of[r["column"]]) for r in records]
    assert keys == sorted(keys)
    shuffled = list(reversed(records))
    resorted = sorted(shuffled, key=lambda r: (r["ticker"], r["year"], index_of[r["column"]]))
    assert [r["cell_id"] for r in resorted] == [r["cell_id"] for r in records]


# --------------------------------------------------------------------------- #
# Duplicate / conflict handling (negative)
# --------------------------------------------------------------------------- #
def test_duplicate_normalized_upstream_key_is_a_hard_error(tmp_path):
    path = write_csv(
        tmp_path / "dup.csv",
        ["ticker", "year", "revenue"],
        [["AEFES", "2020", "1"], ["aefes ", "2020.0", "2"]],
    )
    with pytest.raises(bcp.ProvenanceError, match="ambiguous source identity"):
        bcp.load_keyed_table(path, {"revenue"})


def test_duplicate_cell_id_is_rejected_by_the_validator():
    base = bcp.resolve_cell(
        "AEFES", "2020", "ticker", "AEFES", bcp.COLUMN_SPECS["ticker"], {}, {"2020"}
    )
    with pytest.raises(bcp.ProvenanceError, match="duplicate cell_id"):
        bcp.validate_records([dict(base), dict(base)], 1, 2)


def test_missing_mapped_source_field_raises(tmp_path):
    path = write_csv(tmp_path / "thin.csv", ["ticker", "year"], [["AEFES", "2020"]])
    with pytest.raises(bcp.ProvenanceError, match="missing mapped fields"):
        bcp.load_keyed_table(path, {"revenue"})


# --------------------------------------------------------------------------- #
# Malformed provenance (negative)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "field,value",
    [
        ("evidence_level", "probably"),
        ("source_class", "guessed"),
        ("transform_id", "T_MAGIC"),
        ("resolution_note", "seems_fine"),
        ("value_state", "maybe"),
    ],
)
def test_out_of_vocabulary_values_are_rejected(field, value):
    record = bcp.resolve_cell(
        "AEFES", "2020", "ticker", "AEFES", bcp.COLUMN_SPECS["ticker"], {}, {"2020"}
    )
    record[field] = value
    with pytest.raises(bcp.ProvenanceError, match="outside vocabulary"):
        bcp.validate_records([record], 1, 1)


def test_unknown_record_without_a_resolution_note_is_rejected():
    record = bcp.resolve_cell(
        "AEFES", "2020", "ticker", "AEFES", bcp.COLUMN_SPECS["ticker"], {}, {"2020"}
    )
    record["evidence_level"] = "unknown"
    record["resolution_note"] = ""
    with pytest.raises(bcp.ProvenanceError, match="unknown record without a resolution_note"):
        bcp.validate_records([record], 1, 1)


def test_record_count_mismatch_is_rejected():
    record = bcp.resolve_cell(
        "AEFES", "2020", "ticker", "AEFES", bcp.COLUMN_SPECS["ticker"], {}, {"2020"}
    )
    with pytest.raises(bcp.ProvenanceError, match="record count"):
        bcp.validate_records([record], 2, 3)


def test_non_verified_record_may_not_name_a_source_artifact():
    record = bcp.resolve_cell(
        "AEFES", "2020", "ticker", "AEFES", bcp.COLUMN_SPECS["ticker"], {}, {"2020"}
    )
    record["source_artifact"] = bcp.PRICES_REL
    with pytest.raises(bcp.ProvenanceError, match="non-verified record names a source_artifact"):
        bcp.validate_records([record], 1, 1)


def test_unparseable_upstream_value_never_counts_as_a_match():
    assert bcp.compare_values("1.0", "", numeric=True) == bcp.UNPARSEABLE
    assert bcp.compare_values("1.0", "abc", numeric=True) == bcp.UNPARSEABLE
    assert bcp.compare_values("1.0", "1.000001", numeric=True) == bcp.MISMATCH
    assert bcp.compare_values("1.0", "1.0000000000001", numeric=True) == bcp.MATCH
    assert bcp.compare_values("1000.0", "1000.0000005", numeric=True) == bcp.MATCH
    assert bcp.compare_values("1000.0", "1000.5", numeric=True) == bcp.MISMATCH
    assert bcp.compare_values("False", "False", numeric=False) == bcp.MATCH
    assert bcp.compare_values("False", "True", numeric=False) == bcp.MISMATCH


# --------------------------------------------------------------------------- #
# Source hash / staleness
# --------------------------------------------------------------------------- #
def test_recorded_source_artifacts_rehash_to_their_recorded_digests(report):
    assert bcp.stale_source_artifacts(report["source_artifacts"], REPO_ROOT) == []


def test_source_artifacts_path_set_is_exactly_the_frozen_list(report):
    paths = [entry["path"] for entry in report["source_artifacts"]]
    assert paths == list(bcp.SOURCE_ARTIFACT_RELS)
    assert "Makefile" not in paths
    assert "artifact_registry.json" not in paths
    for path in paths:
        assert (REPO_ROOT / path).is_file()


def test_mutated_recorded_digest_is_detected_as_stale(report):
    mutated = [dict(entry) for entry in report["source_artifacts"]]
    mutated[1]["sha256"] = "0" * 64
    problems = bcp.stale_source_artifacts(mutated, REPO_ROOT)
    assert len(problems) == 1
    assert mutated[1]["path"] in problems[0]


# --------------------------------------------------------------------------- #
# Repository containment / symlink escape
# --------------------------------------------------------------------------- #
def test_every_persisted_path_is_repo_relative_and_inside_the_repository(records, report):
    persisted = {r["source_artifact"] for r in records if r["source_artifact"]}
    persisted |= {entry["path"] for entry in report["source_artifacts"]}
    persisted |= {report["dataset"], report["records_csv"]}
    for rel in persisted:
        bcp.assert_relative_clean(rel)
        assert not rel.startswith("/")
        assert "\\" not in rel
        assert ".." not in Path(rel).parts
        assert (REPO_ROOT / rel).resolve().is_relative_to(REPO_ROOT.resolve())


@pytest.mark.parametrize("bad", ["/etc/passwd", "../escape.csv", "a\\b.csv", ""])
def test_bad_relative_paths_are_rejected(bad):
    with pytest.raises(bcp.ProvenanceError):
        bcp.assert_relative_clean(bad)


def test_path_escaping_the_repository_raises(tmp_path):
    outside = tmp_path.parent / "outside.csv"
    with pytest.raises(bcp.ProvenanceError, match="escapes the repository root"):
        bcp.assert_within_repo(outside, tmp_path)


def test_symlinked_input_file_raises(tmp_path):
    real = write_csv(tmp_path / "real.csv", ["ticker", "year"], [["AEFES", "2020"]])
    link = tmp_path / "link.csv"
    link.symlink_to(real)
    with pytest.raises(bcp.ProvenanceError, match="input is a symlink"):
        bcp.open_checked_file(link, tmp_path)


def test_symlinked_ancestor_directory_raises(tmp_path):
    real_dir = tmp_path / "real_dir"
    real_dir.mkdir()
    write_csv(real_dir / "in.csv", ["ticker", "year"], [["AEFES", "2020"]])
    linked_dir = tmp_path / "linked_dir"
    linked_dir.symlink_to(real_dir, target_is_directory=True)
    with pytest.raises(bcp.ProvenanceError, match="symlinked ancestor directory"):
        bcp.open_checked_file(linked_dir / "in.csv", tmp_path)


def test_symlinked_output_directory_raises(tmp_path):
    real_dir = tmp_path / "elsewhere"
    real_dir.mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "provenance").symlink_to(real_dir, target_is_directory=True)
    with pytest.raises(bcp.ProvenanceError, match="output directory is a symlink"):
        bcp.prepare_output_dir(tmp_path)


def test_non_regular_input_raises(tmp_path):
    directory = tmp_path / "notafile"
    directory.mkdir()
    with pytest.raises(bcp.ProvenanceError, match="not a regular file"):
        bcp.open_checked_file(directory, tmp_path)


def test_undeclared_input_path_is_refused():
    with pytest.raises(bcp.ProvenanceError, match="not a frozen declared input"):
        bcp.resolve_input("data/trusted_clean/data_dictionary.md")


def test_no_output_string_leaks_a_path_or_environment_value():
    env = {"HOME": "/Users/qzvx7", "USER": "qzvx7", "PWD": "/Users/qzvx7/repo"}
    for path in (CSV_PATH, JSON_PATH, MD_PATH):
        text = path.read_text(encoding="utf-8")
        for needle in bcp.FORBIDDEN_SUBSTRINGS:
            assert needle not in text, f"{path.name} leaks {needle!r}"
        bcp.assert_no_leakage(text, path.name, env)
        bcp.assert_no_leakage(text, path.name)
    report = load_report()
    bcp.assert_no_leading_slash(bcp._json_strings(report), "json")


# --------------------------------------------------------------------------- #
# Exact serialization
# --------------------------------------------------------------------------- #
def test_csv_header_is_exactly_the_frozen_field_order():
    first_line = CSV_PATH.read_text(encoding="utf-8").split("\n", 1)[0]
    assert first_line == ",".join(bcp.RECORD_FIELDS)
    assert len(bcp.RECORD_FIELDS) == 14


def test_csv_is_utf8_lf_without_bom_or_trailing_blank_line():
    raw = CSV_PATH.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    raw.decode("utf-8")
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")
    assert not raw.endswith(b"\n\n")


def test_json_reserializes_byte_identically(report):
    assert JSON_PATH.read_text(encoding="utf-8") == bcp.render_json(report)


def test_report_has_no_top_level_limitations_key(report):
    """Guards the R3-LIMITS-01 auto-discovery coupling; caveats is the v1-safe key."""
    assert "limitations" not in report
    assert isinstance(report["caveats"], list) and report["caveats"]


def test_copied_year_values_are_not_float_round_tripped(records):
    for record in records:
        if record["source_effective_year"]:
            assert re.fullmatch(r"\d{4}", record["source_effective_year"])
            assert "." not in record["source_effective_year"]
    verified = index_by_cell(records)["AEFES|2020|revenue"]
    assert verified["source_effective_year"] == "2020"


def test_source_retrieved_at_is_only_present_where_the_upstream_carries_it(records):
    """None of the frozen inputs carries a retrieved_at field, so the column is empty."""
    assert {r["source_retrieved_at"] for r in records} == {""}


# --------------------------------------------------------------------------- #
# Run-twice determinism and value preservation
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def regenerated(tmp_path_factory) -> Path:
    """Generate twice into an isolated repo copy; return the second run's directory."""
    sandbox = tmp_path_factory.mktemp("provenance_repo")
    for rel in (
        "scripts/data_collection/build_cell_provenance.py",
        "scripts/data_collection/__init__.py",
        "scripts/__init__.py",
        *bcp.SOURCE_ARTIFACT_RELS,
    ):
        source = REPO_ROOT / rel
        if not source.is_file():
            continue
        target = sandbox / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    first = bcp.generate(sandbox)
    snapshot = {
        name: (sandbox / bcp.OUTPUT_DIR_REL / name).read_bytes()
        for name in sorted(p.name for p in (sandbox / bcp.OUTPUT_DIR_REL).iterdir())
    }
    bcp.generate(sandbox)
    for name, data in snapshot.items():
        assert (sandbox / bcp.OUTPUT_DIR_REL / name).read_bytes() == data, (
            f"{name} is not byte-identical across two runs"
        )
    assert first["totals"]["cells"] == 14640
    return sandbox


def test_regeneration_is_byte_identical_to_the_committed_artifacts(regenerated):
    out = regenerated / bcp.OUTPUT_DIR_REL
    for committed in (CSV_PATH, JSON_PATH, MD_PATH):
        assert (out / committed.name).read_bytes() == committed.read_bytes(), (
            f"{committed.name} differs from a fresh regeneration"
        )


def test_output_carries_no_timestamp_hostname_or_seed(report):
    blob = json.dumps(report, ensure_ascii=False) + MD_PATH.read_text(encoding="utf-8")
    assert not re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", blob)
    assert not re.search(r"\bseed\b", blob, re.IGNORECASE)
    assert not re.search(r"\bhostname\b", blob, re.IGNORECASE)
    assert os.uname().nodename not in blob


def test_generation_leaves_governed_scientific_artifacts_byte_identical():
    before_files = {rel: sha256_of(REPO_ROOT / rel) for rel in PROTECTED_FILES}
    before_trees = {root: digest_tree(REPO_ROOT / root) for root in VALUE_PRESERVATION_ROOTS}
    bcp.generate(REPO_ROOT)
    after_files = {rel: sha256_of(REPO_ROOT / rel) for rel in PROTECTED_FILES}
    after_trees = {root: digest_tree(REPO_ROOT / root) for root in VALUE_PRESERVATION_ROOTS}
    assert after_files == before_files
    assert after_trees == before_trees


def test_generator_writes_nothing_outside_the_provenance_namespace():
    """data/provenance is the only namespace the generator may create or touch."""
    before = digest_tree(REPO_ROOT / "data" / "trusted_raw")
    bcp.generate(REPO_ROOT)
    assert digest_tree(REPO_ROOT / "data" / "trusted_raw") == before
    assert bcp.OUTPUT_DIR_REL.startswith("data/provenance")
    assert not bcp.OUTPUT_DIR_REL.startswith("data/trusted_clean")


# --------------------------------------------------------------------------- #
# Backward compatibility with passports v1
# --------------------------------------------------------------------------- #
def test_passports_v1_is_untouched():
    v1 = json.loads(PASSPORTS_V1_PATH.read_text(encoding="utf-8"))
    assert v1["schema_version"] == "1.0.0"
    assert len(v1["passports"]) == 61
    for passport in v1["passports"]:
        assert set(passport.keys()) == PASSPORT_V1_FIELDS
    assert "limitations" not in v1


def test_v2_declares_its_own_schema_version(report):
    assert report["provenance_schema_version"] == "2.0.0"
    assert report["provenance_schema_version"] != "1.0.0"
    assert report["record_schema"] == list(bcp.RECORD_FIELDS)


def test_column_asserted_classes_agree_with_passports_v1(records):
    v1 = json.loads(PASSPORTS_V1_PATH.read_text(encoding="utf-8"))
    v1_classes = {p["name"]: p["source_class"] for p in v1["passports"]}
    for record in records:
        if record["evidence_level"] != "column_asserted" or record["value_state"] == "null":
            continue
        assert record["source_class"] == v1_classes[record["column"]]


def test_v2_source_class_vocabulary_extends_v1_by_exactly_one_value():
    v1 = json.loads(PASSPORTS_V1_PATH.read_text(encoding="utf-8"))
    v1_classes = set(v1["source_class_definitions"])
    assert v1_classes <= set(bcp.SOURCE_CLASSES)
    assert set(bcp.SOURCE_CLASSES) - v1_classes == {"corrected_balance_2024"}


# --------------------------------------------------------------------------- #
# Bounded artifact size / count
# --------------------------------------------------------------------------- #
def test_csv_is_bounded_and_has_one_line_per_record():
    raw = CSV_PATH.read_bytes()
    assert len(raw) <= 4 * 1024 * 1024, "CSV exceeded 4 MB — the schema drifted"
    assert raw.count(b"\n") == 14641  # header + 14,640 records


def test_provenance_directory_contains_exactly_three_files():
    entries = sorted(p.name for p in (REPO_ROOT / bcp.OUTPUT_DIR_REL).iterdir())
    assert entries == [
        "cell_provenance_public_2020_2025.csv",
        "cell_provenance_report.json",
        "cell_provenance_report.md",
    ]


# --------------------------------------------------------------------------- #
# No claim drift
# --------------------------------------------------------------------------- #
FORBIDDEN_MARKET_TERMS = ("brazil", "b3", "bovespa", "ibov")

# Affirmative claim phrasings only. A denial ("certifies nothing about point-in-time
# correctness") must never trip this guard, so every entry is a phrasing that can only
# appear when the artifact is asserting the property rather than disclaiming it.
FORBIDDEN_CLAIM_PHRASES = (
    "is point-in-time correct",
    "point-in-time validated",
    "point-in-time guaranteed",
    "rights are cleared",
    "rights cleared",
    "validated predictive edge",
    "reliable predictive edge exists",
    "certifies predictive",
    "proven signal",
    "generates alpha",
    "guaranteed return",
    "investment recommendation",
    "buy recommendation",
    "sell recommendation",
    "suitable for trading",
    "ready for deployment",
    "sources are accurate",
    "source accuracy is certified",
)

REQUIRED_DENIALS = (
    "point-in-time",
    "data-rights clearance",
    "source accuracy",
    "predictive validity",
    "investment usefulness",
)


def test_no_external_market_reference_leaked_into_any_artifact():
    generator = (REPO_ROOT / bcp.GENERATOR_REL).read_text(encoding="utf-8")
    for text in (
        CSV_PATH.read_text(encoding="utf-8"),
        JSON_PATH.read_text(encoding="utf-8"),
        MD_PATH.read_text(encoding="utf-8"),
        generator,
    ):
        lowered = text.lower()
        for term in FORBIDDEN_MARKET_TERMS:
            assert not re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", lowered), (
                f"external-market term {term!r} leaked into an artifact"
            )


def test_artifacts_assert_no_validity_or_investment_claim(report):
    blob = (JSON_PATH.read_text(encoding="utf-8") + MD_PATH.read_text(encoding="utf-8")).lower()
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        assert phrase not in blob, f"claim drift: {phrase!r}"
    disclaimer = report["disclaimer"].lower()
    assert "lineage record only" in disclaimer
    assert "certifies nothing" in disclaimer
    assert "not investment advice" in disclaimer
    for denial in REQUIRED_DENIALS:
        assert denial in disclaimer, f"disclaimer must explicitly deny {denial!r}"
    assert "lineage record only" in MD_PATH.read_text(encoding="utf-8").lower()


# --------------------------------------------------------------------------- #
# Artifact-registry ownership
# --------------------------------------------------------------------------- #
def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_provenance_namespace_is_a_governed_root():
    registry = load_registry()
    assert "data/provenance" in registry["governed_roots"]
    assert registry["task"] == "R3-REL-01", "R4-PROV-01 adds entries; it does not take the registry"
    assert registry["schema_version"] == "1.0.0"


def test_each_provenance_artifact_has_exactly_one_registry_entry():
    registry = load_registry()
    for rel in (bcp.OUT_CSV_REL, bcp.OUT_JSON_REL, bcp.OUT_MD_REL):
        owners = [e for e in registry["entries"] if e["path_or_glob"] == rel]
        assert len(owners) == 1, f"{rel} must have exactly one owner, found {len(owners)}"
        entry = owners[0]
        assert entry["artifact_class"] == "generated"
        assert entry["generator_command"] == "make cell-provenance"
        assert entry["hand_edit_forbidden"] is True
        assert entry["notes"].strip()
        assert (REPO_ROOT / rel).is_file()


def test_cell_provenance_is_a_declared_makefile_target():
    text = MAKEFILE_PATH.read_text(encoding="utf-8")
    assert re.search(r"^cell-provenance:", text, re.MULTILINE)
    phony = re.search(r"^\.PHONY:((?:.*\\\n)*.*)", text, re.MULTILINE)
    assert phony and "cell-provenance" in phony.group(1)


def test_registry_inputs_reference_real_files():
    registry = load_registry()
    for entry in registry["entries"]:
        if not entry["path_or_glob"].startswith("data/provenance/"):
            continue
        assert entry["inputs"], "provenance entries must declare their inputs"
        for rel in entry["inputs"]:
            bcp.assert_relative_clean(rel)
            assert (REPO_ROOT / rel).is_file(), f"declared input missing: {rel}"
