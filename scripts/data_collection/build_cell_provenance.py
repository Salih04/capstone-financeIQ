"""Per-cell provenance (passports v2) for the public modeling dataset — R4-PROV-01.

Materializes, for every cell of ``modeling_dataset_public_2020_2025.csv``, a
deterministic record of where that value came from: which upstream artifact,
which field in it, through which transformation, and with what strength of
evidence.

This is a **lineage record only**. It changes no dataset value, creates no
statistical result, and certifies neither point-in-time validity, source
accuracy, data-rights clearance, nor any predictive or investment property.

Run as::

    make cell-provenance
    PYTHONPATH=. python -m scripts.data_collection.build_cell_provenance

The generator is read-only with respect to every path outside
``data/provenance/``. It builds the whole payload in memory, runs every
integrity assertion, and only then writes; any failure writes nothing.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import stat
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[2]

PROVENANCE_SCHEMA_VERSION = "2.0.0"
TASK_ID = "R4-PROV-01"

# --------------------------------------------------------------------------- #
# Frozen paths (repo-relative POSIX literals; never re-derived from the FS)
# --------------------------------------------------------------------------- #
DATASET_REL = "data/trusted_clean/modeling_dataset_public_2020_2025.csv"
PASSPORTS_V1_REL = "data/trusted_clean/feature_passports.json"
RETURNS_REL = "data/trusted_clean/company_year_returns.csv"
CORRECTED_YEARLY_REL = "data/trusted_raw/financials/corrected_yearly_financials_candidate.csv"
VENDOR_SNAPSHOT_REL = "data/trusted_raw/financials/candidate_from_yearly_snapshots.csv"
BALANCE_2024_REL = "data/trusted_raw/financials/corrected_balance_sheet_2024.csv"
VALUATION_REL = "data/trusted_raw/financials/free_valuation_history_candidate.csv"
PRICES_REL = "data/trusted_raw/prices/yahoo_year_end_prices.csv"
BENCHMARK_REL = "data/trusted_raw/bist100_benchmark_returns.csv"
GENERATOR_REL = "scripts/data_collection/build_cell_provenance.py"

OUTPUT_DIR_REL = "data/provenance"
OUT_CSV_REL = f"{OUTPUT_DIR_REL}/cell_provenance_public_2020_2025.csv"
OUT_JSON_REL = f"{OUTPUT_DIR_REL}/cell_provenance_report.json"
OUT_MD_REL = f"{OUTPUT_DIR_REL}/cell_provenance_report.md"

# §13.5 — frozen source_artifacts list, in this exact order.
SOURCE_ARTIFACT_RELS = (
    GENERATOR_REL,
    DATASET_REL,
    PASSPORTS_V1_REL,
    RETURNS_REL,
    CORRECTED_YEARLY_REL,
    VENDOR_SNAPSHOT_REL,
    BALANCE_2024_REL,
    VALUATION_REL,
    PRICES_REL,
    BENCHMARK_REL,
)

# Every path the generator is permitted to read. No dynamic path input exists.
ALLOWED_INPUT_RELS = frozenset(SOURCE_ARTIFACT_RELS)

# Upstream tables keyed on (ticker, year); the benchmark is keyed on year only.
TICKER_YEAR_SOURCES = (
    RETURNS_REL,
    CORRECTED_YEARLY_REL,
    VENDOR_SNAPSHOT_REL,
    BALANCE_2024_REL,
    VALUATION_REL,
    PRICES_REL,
)

# --------------------------------------------------------------------------- #
# Frozen record schema (§9.1) — exactly these 14 fields, in exactly this order
# --------------------------------------------------------------------------- #
RECORD_FIELDS = (
    "cell_id",
    "ticker",
    "year",
    "column",
    "value_state",
    "source_class",
    "evidence_level",
    "source_artifact",
    "source_field",
    "source_effective_year",
    "source_retrieved_at",
    "transform_id",
    "upstream_cells",
    "resolution_note",
)

CELL_KEY_SEPARATOR = "|"
UPSTREAM_SEPARATOR = ";"

VALUE_STATES = ("present", "null")

# §9.2 — the seven passports-v1 classes verbatim, plus corrected_balance_2024.
SOURCE_CLASSES = (
    "vendor_xlsx",
    "corrected_yearly_csv",
    "yahoo_fetch",
    "manual_shares",
    "derived",
    "metadata",
    "unknown",
    "corrected_balance_2024",
)

SOURCE_CLASS_DEFINITIONS = {
    "vendor_xlsx": "Vendor yearly-snapshot workbook lineage (candidate_from_yearly_snapshots.csv family).",
    "corrected_yearly_csv": "Reviewed corrected yearly financials candidate lineage.",
    "yahoo_fetch": "Cached Yahoo year-end price / benchmark lineage.",
    "manual_shares": "Manually curated shares-outstanding lineage (v1 vocabulary value; not attributed at cell level by this artifact).",
    "derived": "Computed inside the pipeline from other recorded inputs or dataset cells.",
    "metadata": "Identifier, cohort, or row-state assignment.",
    "unknown": "No upstream source could be verified and no chain could be asserted.",
    "corrected_balance_2024": "Reviewed 2024 balance-sheet override input (new in provenance schema 2.0.0; not part of passports v1).",
}

# §9.3 — the honesty axis.
EVIDENCE_LEVELS = ("cell_verified", "derived_chain", "column_asserted", "unknown")

EVIDENCE_LEVEL_DEFINITIONS = {
    "cell_verified": (
        "The dataset value was compared against a specific (source_artifact, source_field, ticker, year) "
        "upstream value and matched under the recorded value-equality rule. Strongest available evidence."
    ),
    "derived_chain": (
        "The value is a deterministic function of the named upstream_cells of this same dataset. "
        "Provenance is the chain, not a copied source value."
    ),
    "column_asserted": (
        "No cell-level upstream source file carries this field; provenance is inherited from the "
        "passports-v1 column assertion. Weaker than cell_verified and labelled as such."
    ),
    "unknown": (
        "No source could be verified and no chain asserted. Always carries a resolution_note."
    ),
}

# §9.4 — stable identifiers, expanded once here rather than per record.
TRANSFORM_IDS = (
    "T_COPY",
    "T_OVERRIDE_2024",
    "T_RATIO",
    "T_SHIFT_T1",
    "T_RANK_WITHIN_YEAR",
    "T_PRICE_WINDOW",
    "T_METADATA",
    "T_NULL_PRESERVED",
    "T_UNRESOLVED",
)

TRANSFORM_DEFINITIONS = {
    "T_COPY": "Value copied unchanged from source_artifact.source_field at the same (ticker, year).",
    "T_OVERRIDE_2024": "Value taken from the reviewed 2024 balance-sheet override in preference to the vendor snapshot.",
    "T_RATIO": "Deterministic arithmetic on named upstream cells (valuation ratios, margins, excess return).",
    "T_SHIFT_T1": "Outcome from year T+1 shifted back onto feature year T.",
    "T_RANK_WITHIN_YEAR": "Rank, percentile, or flag computed within the target year.",
    "T_PRICE_WINDOW": "Price momentum, drawdown, or history count computed over a T-bounded price window.",
    "T_METADATA": "Identifier, cohort, or row-state metadata assignment.",
    "T_NULL_PRESERVED": "The cell is null and was never filled; the pipeline's no-imputation contract is the provenance.",
    "T_UNRESOLVED": "No transformation could be established.",
}

# §10.1 — closed set; the empty string is a member (cell_verified with no note).
RESOLUTION_NOTES = (
    "",
    "null_preserved",
    "column_asserted_no_cell_source",
    "derived_from_dataset_cells",
    "multi_candidate_priority_applied",
    "no_upstream_row",
    "value_mismatch_all_candidates",
    "value_unparseable",
)

RESOLUTION_NOTE_DEFINITIONS = {
    "null_preserved": "Cell is null; no value was ever filled.",
    "column_asserted_no_cell_source": "No upstream file carries this field at cell granularity.",
    "derived_from_dataset_cells": "Value is computed from the named upstream_cells.",
    "multi_candidate_priority_applied": "More than one candidate source verified the value; the frozen source priority chose one.",
    "no_upstream_row": "The candidate upstream file(s) have no row at this (ticker, year).",
    "value_mismatch_all_candidates": "Upstream row(s) exist but no candidate value matched under the value-equality rule.",
    "value_unparseable": "The dataset or upstream value could not be parsed for comparison (includes empty upstream fields).",
}

VALUE_EQUALITY_RULE = (
    "Numeric columns match when abs(a - b) <= 1e-9 * max(1.0, abs(a)); non-numeric columns match on exact "
    "string equality of the verbatim CSV text. A parse failure is never a match."
)

RECORD_ORDERING_RULE = (
    "Records are sorted by (ticker, year, dataset column index) ascending, where the column index is the "
    "positional index of the column in the dataset header, not its lexicographic rank."
)

DISCLAIMER = (
    "Lineage record only. This artifact states where each dataset value was copied or computed from and how "
    "strong that evidence is. It certifies nothing about point-in-time correctness, data-rights clearance, "
    "source accuracy, completeness, predictive validity, causal validity, statistical significance, or "
    "investment usefulness, and it is not investment advice. The project's walk-forward finding (no reliable "
    "predictive edge) is unchanged by this artifact."
)

CAVEATS = (
    "cell_verified means the dataset value equals a specific upstream value under the recorded equality rule; "
    "it does not mean the upstream value is correct.",
    "column_asserted records inherit passports-v1 column-level provenance because no upstream file carries the "
    "field at cell granularity; they are strictly weaker than cell_verified and were never upgraded by inference.",
    "unknown records are reported, never repaired: no dataset value was changed, no tolerance was widened, and "
    "no nearest candidate was substituted.",
    "Null cells are recorded as preserved nulls. The pipeline never imputes; for null cells source_class names "
    "the column's declared source family rather than a verified attribution, and evidence_level plus "
    "resolution_note carry the honesty.",
    "Lineage depth is bounded at the nearest upstream artifact at which a value was verified, plus intra-dataset "
    "upstream_cells. No deeper materialized evidence exists in this repository, and none was invented.",
    "Scope is exactly the 240-row x 61-column public modeling dataset. The full and training datasets, external "
    "markets, and experiment outputs are out of scope.",
    "The manual-shares component of the upstream valuation inputs is not attributed at cell level by this "
    "artifact; valuation cells are recorded against the valuation candidate file they were verified against.",
)


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
class ProvenanceError(RuntimeError):
    """Raised for any fail-closed condition. The generator then writes nothing."""


# --------------------------------------------------------------------------- #
# Path integrity (§13.1–§13.3) — reimplemented locally on purpose.
# experiments/run_excess_basis.py is a protected R3-TGT-01 module and must be
# neither imported nor modified by this task.
# --------------------------------------------------------------------------- #
def assert_relative_clean(rel: str) -> str:
    """Validate a persisted repo-relative POSIX path (§13.2)."""
    if not isinstance(rel, str) or rel == "":
        raise ProvenanceError(f"empty or non-string relative path: {rel!r}")
    if "\\" in rel:
        raise ProvenanceError(f"backslash in persisted path: {rel!r}")
    if rel.startswith("/"):
        raise ProvenanceError(f"absolute persisted path: {rel!r}")
    parts = PurePosixPath(rel).parts
    if not parts:
        raise ProvenanceError(f"empty persisted path: {rel!r}")
    if ".." in parts:
        raise ProvenanceError(f"path traversal in persisted path: {rel!r}")
    if PurePosixPath(rel).is_absolute():
        raise ProvenanceError(f"absolute persisted path: {rel!r}")
    return rel


def assert_within_repo(path: Path, root: Path) -> Path:
    """Every path read or written must resolve inside the repository root."""
    resolved = path.resolve()
    root_resolved = root.resolve()
    if not resolved.is_relative_to(root_resolved):
        raise ProvenanceError(f"path escapes the repository root: {path}")
    return resolved


def assert_no_symlink_ancestors(path: Path, root: Path) -> None:
    """No ancestor of ``path`` up to (and including) ``root`` may be a symlink."""
    root_resolved = root.resolve()
    current = path if path.is_absolute() else (root / path)
    current = current.parent
    seen = 0
    while True:
        seen += 1
        if seen > 64:  # pragma: no cover - defensive
            raise ProvenanceError(f"pathological ancestor chain for {path}")
        if current.exists() or current.is_symlink():
            if current.is_symlink():
                raise ProvenanceError(f"symlinked ancestor directory: {current}")
        if current.resolve() == root_resolved:
            return
        parent = current.parent
        if parent == current:
            raise ProvenanceError(f"ancestor walk left the repository root: {path}")
        current = parent


def resolve_input(rel: str, root: Path = REPO_ROOT) -> Path:
    """Resolve a frozen repo-relative input path, failing closed on anything odd."""
    assert_relative_clean(rel)
    if rel not in ALLOWED_INPUT_RELS:
        raise ProvenanceError(f"path is not a frozen declared input: {rel!r}")
    return open_checked_file(root / rel, root)


def open_checked_file(path: Path, root: Path) -> Path:
    """Assert ``path`` is a real, non-symlinked regular file inside ``root``."""
    assert_within_repo(path, root)
    assert_no_symlink_ancestors(path, root)
    try:
        info = os.lstat(path)
    except FileNotFoundError as exc:
        raise ProvenanceError(f"missing input file: {path}") from exc
    if stat.S_ISLNK(info.st_mode):
        raise ProvenanceError(f"input is a symlink: {path}")
    if not stat.S_ISREG(info.st_mode):
        raise ProvenanceError(f"input is not a regular file: {path}")
    return path


def prepare_output_dir(root: Path = REPO_ROOT, rel: str = OUTPUT_DIR_REL) -> Path:
    """Validate and create the output directory, refusing symlinks (§13.3)."""
    assert_relative_clean(rel)
    out_dir = root / rel
    assert_within_repo(out_dir.parent, root)
    assert_no_symlink_ancestors(out_dir, root)
    if out_dir.is_symlink():
        raise ProvenanceError(f"output directory is a symlink: {out_dir}")
    if out_dir.exists() and not out_dir.is_dir():
        raise ProvenanceError(f"output path exists and is not a directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    if out_dir.is_symlink():  # pragma: no cover - defensive re-check
        raise ProvenanceError(f"output directory is a symlink: {out_dir}")
    return out_dir


# --------------------------------------------------------------------------- #
# Source identity normalization (§13.4)
# --------------------------------------------------------------------------- #
def normalize_ticker(raw: str) -> str:
    return str(raw).strip().upper()


def normalize_year(raw: str) -> str:
    """Parse a year via int(float(...)) and render it as a 4-digit decimal string."""
    try:
        value = int(float(str(raw).strip()))
    except (TypeError, ValueError) as exc:
        raise ProvenanceError(f"unparseable year value: {raw!r}") from exc
    if value < 0 or value > 9999:
        raise ProvenanceError(f"year out of range: {raw!r}")
    return f"{value:04d}"


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    text = path.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(text))
    header = list(reader.fieldnames or [])
    if not header:
        raise ProvenanceError(f"upstream file has no header: {path}")
    return header, [dict(row) for row in reader]


def load_keyed_table(
    path: Path,
    required_fields: set[str],
    key_fields: tuple[str, ...] = ("ticker", "year"),
) -> dict[tuple[str, ...], dict[str, str]]:
    """Load an upstream CSV into a normalized-key table, failing closed on ambiguity."""
    header, rows = read_csv_rows(path)
    missing = sorted(f for f in (set(key_fields) | required_fields) if f not in header)
    if missing:
        raise ProvenanceError(f"upstream header {path.name} is missing mapped fields: {missing}")
    table: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        key_parts: list[str] = []
        for field in key_fields:
            raw = row.get(field, "")
            key_parts.append(normalize_ticker(raw) if field == "ticker" else normalize_year(raw))
        key = tuple(key_parts)
        if key in table:
            raise ProvenanceError(
                f"ambiguous source identity: duplicate normalized key {key} in {path.name}"
            )
        table[key] = row
    return table


# --------------------------------------------------------------------------- #
# Value equality (§9.6)
# --------------------------------------------------------------------------- #
NON_NUMERIC_COLUMNS = frozenset(
    {
        "ticker",
        "company_name",
        "sector",
        "indices",
        "universe_source",
        "is_bist100",
        "is_public_universe",
        "is_training_universe",
        "has_target",
        "is_inference_row",
        "next_year_outperform_bist100",
        "next_year_top_10pct_returner",
        "next_year_top_20pct_returner",
    }
)

MATCH = "match"
MISMATCH = "mismatch"
UNPARSEABLE = "unparseable"
NO_ROW = "no_row"


def _to_float(text: str) -> float | None:
    try:
        value = float(str(text).strip())
    except (TypeError, ValueError):
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value


def compare_values(dataset_text: str, upstream_text: str, numeric: bool) -> str:
    """Return MATCH / MISMATCH / UNPARSEABLE for one candidate comparison."""
    if upstream_text is None or str(upstream_text).strip() == "":
        return UNPARSEABLE
    if not numeric:
        if dataset_text is None or str(dataset_text) == "":
            return UNPARSEABLE
        return MATCH if str(dataset_text) == str(upstream_text) else MISMATCH
    a = _to_float(dataset_text)
    b = _to_float(upstream_text)
    if a is None or b is None:
        return UNPARSEABLE
    return MATCH if abs(a - b) <= 1e-9 * max(1.0, abs(a)) else MISMATCH


# --------------------------------------------------------------------------- #
# Frozen column -> source resolution table (§9.7).
# The implementation does not choose these mappings.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Candidate:
    """One frozen candidate source for a column, in priority order."""

    source_rel: str
    source_field: str
    source_class: str
    transform_id: str
    only_year: str | None = None  # applies only when the dataset year equals this


SOURCED = "sourced"
CHAINED = "chained"
ASSERTED = "asserted"


@dataclass(frozen=True)
class ColumnSpec:
    kind: str
    nominal_source_class: str
    transform_id: str
    candidates: tuple[Candidate, ...] = ()
    chain: str = ""  # lineage rule name for CHAINED columns


CORRECTED_YEARLY_FIELDS = {
    "revenue": "revenue",
    "gross_profit": "gross_profit",
    "operating_income": "operating_income",
    "ebitda": "ebitda",
    "net_income": "net_income",
    "roe": "roe",
    "roa": "roa",
    "gross_margin": "gross_profit_margin",
    "net_margin": "net_profit_margin",
    "ebitda_margin": "ebitda_margin",
}

BALANCE_COLUMNS = (
    "total_assets",
    "current_assets",
    "non_current_assets",
    "short_term_liabilities",
    "long_term_liabilities",
    "working_capital",
    "net_debt",
    "current_ratio",
    "leverage_ratio",
    "financial_debt_ratio",
    "net_debt_to_ebitda",
    "equity",
)

VENDOR_BALANCE_FIELDS = {col: col for col in BALANCE_COLUMNS}
VENDOR_BALANCE_FIELDS["equity"] = "total_equity"

VALUATION_FIELDS = {
    "market_cap": "market_cap",
    "enterprise_value": "enterprise_value",
    "pe_ratio": "pe",
    "pb_ratio": "pb",
    "ev_ebitda": "ev_ebitda",
}

RETURNS_TRANSFORMS = {
    "same_year_return_pct": "T_COPY",
    "next_year_return_pct": "T_SHIFT_T1",
    "target_year": "T_SHIFT_T1",
    "next_year_rank_by_return": "T_RANK_WITHIN_YEAR",
    "next_year_return_percentile": "T_RANK_WITHIN_YEAR",
    "next_year_top_10pct_returner": "T_RANK_WITHIN_YEAR",
    "next_year_top_20pct_returner": "T_RANK_WITHIN_YEAR",
}

GROWTH_COLUMNS = (
    "ebitda_growth_pct",
    "gross_profit_growth_pct",
    "net_income_growth_pct",
    "operating_income_growth_pct",
    "revenue_growth_pct",
)

METADATA_COLUMNS = (
    "ticker",
    "company_name",
    "year",
    "sector",
    "indices",
    "is_bist100",
    "is_public_universe",
    "is_training_universe",
    "universe_source",
)

# Lineage rule names for CHAINED columns (§9.7 / price_features.py window semantics).
CHAIN_PRICE_T = "price_t"
CHAIN_PRICE_HISTORY = "price_history_to_t"
CHAIN_PRICE_MOM1 = "price_t_and_t_minus_1"
CHAIN_PRICE_MOM2 = "price_t_and_t_minus_2"
CHAIN_PRICE_3Y = "price_t_minus_2_to_t"
CHAIN_PRICE_VS_BENCH = "price_t_and_t_minus_1_plus_benchmark_t"
CHAIN_BENCH_T1 = "benchmark_t_plus_1"
CHAIN_EXCESS = "next_year_return_and_next_year_benchmark"
CHAIN_OUTPERFORM = "next_year_excess"
CHAIN_TARGET_FLAG = "next_year_return"


def build_column_specs() -> dict[str, ColumnSpec]:
    specs: dict[str, ColumnSpec] = {}

    for column, field in CORRECTED_YEARLY_FIELDS.items():
        specs[column] = ColumnSpec(
            kind=SOURCED,
            nominal_source_class="corrected_yearly_csv",
            transform_id="T_COPY",
            candidates=(
                Candidate(CORRECTED_YEARLY_REL, field, "corrected_yearly_csv", "T_COPY"),
            ),
        )

    for column in BALANCE_COLUMNS:
        specs[column] = ColumnSpec(
            kind=SOURCED,
            nominal_source_class="vendor_xlsx",
            transform_id="T_COPY",
            candidates=(
                Candidate(
                    BALANCE_2024_REL,
                    column,
                    "corrected_balance_2024",
                    "T_OVERRIDE_2024",
                    only_year="2024",
                ),
                Candidate(
                    VENDOR_SNAPSHOT_REL,
                    VENDOR_BALANCE_FIELDS[column],
                    "vendor_xlsx",
                    "T_COPY",
                ),
            ),
        )

    for column, field in VALUATION_FIELDS.items():
        specs[column] = ColumnSpec(
            kind=SOURCED,
            nominal_source_class="derived",
            transform_id="T_RATIO",
            candidates=(Candidate(VALUATION_REL, field, "derived", "T_RATIO"),),
        )

    specs["price_adjclose_t"] = ColumnSpec(
        kind=SOURCED,
        nominal_source_class="yahoo_fetch",
        transform_id="T_COPY",
        candidates=(Candidate(PRICES_REL, "year_end_close", "yahoo_fetch", "T_COPY"),),
    )
    specs["benchmark_same_year_return_pct"] = ColumnSpec(
        kind=SOURCED,
        nominal_source_class="yahoo_fetch",
        transform_id="T_COPY",
        candidates=(Candidate(BENCHMARK_REL, "bist100_return_pct", "yahoo_fetch", "T_COPY"),),
    )

    for column, transform in RETURNS_TRANSFORMS.items():
        specs[column] = ColumnSpec(
            kind=SOURCED,
            nominal_source_class="derived",
            transform_id=transform,
            candidates=(Candidate(RETURNS_REL, column, "derived", transform),),
        )

    for column in GROWTH_COLUMNS:
        specs[column] = ColumnSpec(
            kind=ASSERTED,
            nominal_source_class="vendor_xlsx",
            transform_id="T_RATIO",
        )

    for column in METADATA_COLUMNS:
        specs[column] = ColumnSpec(
            kind=ASSERTED,
            nominal_source_class="metadata",
            transform_id="T_METADATA",
        )

    chained = {
        "price_data_available": ("T_PRICE_WINDOW", CHAIN_PRICE_T),
        "price_history_years_available": ("T_PRICE_WINDOW", CHAIN_PRICE_HISTORY),
        "price_momentum_1y_pct": ("T_PRICE_WINDOW", CHAIN_PRICE_MOM1),
        "price_momentum_2y_pct": ("T_PRICE_WINDOW", CHAIN_PRICE_MOM2),
        "price_drawdown_from_3y_high_pct": ("T_PRICE_WINDOW", CHAIN_PRICE_3Y),
        "price_vs_bist100_1y_pct": ("T_PRICE_WINDOW", CHAIN_PRICE_VS_BENCH),
        "next_year_bist100_return_pct": ("T_SHIFT_T1", CHAIN_BENCH_T1),
        "next_year_excess_return_vs_bist100": ("T_RATIO", CHAIN_EXCESS),
        "next_year_outperform_bist100": ("T_RATIO", CHAIN_OUTPERFORM),
        "has_target": ("T_RATIO", CHAIN_TARGET_FLAG),
        "is_inference_row": ("T_RATIO", CHAIN_TARGET_FLAG),
    }
    for column, (transform, chain) in chained.items():
        specs[column] = ColumnSpec(
            kind=CHAINED,
            nominal_source_class="derived",
            transform_id=transform,
            chain=chain,
        )

    return specs


COLUMN_SPECS = build_column_specs()

SOURCE_PRIORITY = (
    {
        "columns": list(BALANCE_COLUMNS),
        "order": [
            f"{BALANCE_2024_REL} (year 2024 only)",
            VENDOR_SNAPSHOT_REL,
        ],
        "note": "The reviewed 2024 balance-sheet override outranks the vendor snapshot at year 2024.",
    },
)


# --------------------------------------------------------------------------- #
# Lineage (§9.5) — intra-dataset upstream cells only
# --------------------------------------------------------------------------- #
def make_cell_id(ticker: str, year: str, column: str) -> str:
    return f"{ticker}{CELL_KEY_SEPARATOR}{year}{CELL_KEY_SEPARATOR}{column}"


def upstream_cells_for(
    chain: str,
    ticker: str,
    year: str,
    present_years: set[str],
) -> list[str]:
    """Return the frozen intra-dataset lineage for a chained column.

    Only cells that actually exist in the in-scope dataset are named; a hop whose
    year is absent from the dataset yields no upstream cell rather than a
    fabricated one.
    """
    year_int = int(year)

    def price(offset: int) -> list[str]:
        target = f"{year_int + offset:04d}"
        if target not in present_years:
            return []
        return [make_cell_id(ticker, target, "price_adjclose_t")]

    if chain == CHAIN_PRICE_T:
        return price(0)
    if chain == CHAIN_PRICE_HISTORY:
        years = sorted(y for y in present_years if int(y) <= year_int)
        return [make_cell_id(ticker, y, "price_adjclose_t") for y in years]
    if chain == CHAIN_PRICE_MOM1:
        return price(-1) + price(0)
    if chain == CHAIN_PRICE_MOM2:
        return price(-2) + price(0)
    if chain == CHAIN_PRICE_3Y:
        return price(-2) + price(-1) + price(0)
    if chain == CHAIN_PRICE_VS_BENCH:
        cells = price(-1) + price(0)
        cells.append(make_cell_id(ticker, year, "benchmark_same_year_return_pct"))
        return cells
    if chain == CHAIN_BENCH_T1:
        target = f"{year_int + 1:04d}"
        if target not in present_years:
            return []
        return [make_cell_id(ticker, target, "benchmark_same_year_return_pct")]
    if chain == CHAIN_EXCESS:
        return [
            make_cell_id(ticker, year, "next_year_return_pct"),
            make_cell_id(ticker, year, "next_year_bist100_return_pct"),
        ]
    if chain == CHAIN_OUTPERFORM:
        return [make_cell_id(ticker, year, "next_year_excess_return_vs_bist100")]
    if chain == CHAIN_TARGET_FLAG:
        return [make_cell_id(ticker, year, "next_year_return_pct")]
    raise ProvenanceError(f"unknown lineage chain: {chain!r}")


# --------------------------------------------------------------------------- #
# Record construction
# --------------------------------------------------------------------------- #
def _blank_record(ticker: str, year: str, column: str) -> dict[str, str]:
    return {
        "cell_id": make_cell_id(ticker, year, column),
        "ticker": ticker,
        "year": int(year),
        "column": column,
        "value_state": "",
        "source_class": "",
        "evidence_level": "",
        "source_artifact": "",
        "source_field": "",
        "source_effective_year": "",
        "source_retrieved_at": "",
        "transform_id": "",
        "upstream_cells": "",
        "resolution_note": "",
    }


def resolve_cell(
    ticker: str,
    year: str,
    column: str,
    dataset_text: str,
    spec: ColumnSpec,
    tables: dict[str, dict[tuple[str, ...], dict[str, str]]],
    present_years: set[str],
) -> dict[str, object]:
    """Resolve one cell against the frozen table. Pure with respect to the FS."""
    record = _blank_record(ticker, year, column)
    is_null = dataset_text == ""
    record["value_state"] = "null" if is_null else "present"

    chain_cells: list[str] = []
    if spec.kind == CHAINED:
        chain_cells = upstream_cells_for(spec.chain, ticker, year, present_years)
        record["upstream_cells"] = UPSTREAM_SEPARATOR.join(chain_cells)

    if is_null:
        record["transform_id"] = "T_NULL_PRESERVED"
        record["evidence_level"] = "derived_chain" if spec.kind == CHAINED else "column_asserted"
        record["source_class"] = spec.nominal_source_class
        record["resolution_note"] = "null_preserved"
        return record

    if spec.kind == ASSERTED:
        record["evidence_level"] = "column_asserted"
        record["source_class"] = spec.nominal_source_class
        record["transform_id"] = spec.transform_id
        record["resolution_note"] = "column_asserted_no_cell_source"
        return record

    if spec.kind == CHAINED:
        record["evidence_level"] = "derived_chain"
        record["source_class"] = "derived"
        record["transform_id"] = spec.transform_id
        record["resolution_note"] = "derived_from_dataset_cells"
        return record

    numeric = column not in NON_NUMERIC_COLUMNS
    outcomes: list[str] = []
    matches: list[tuple[Candidate, dict[str, str]]] = []
    for candidate in spec.candidates:
        if candidate.only_year is not None and candidate.only_year != year:
            continue
        table = tables[candidate.source_rel]
        key = (year,) if candidate.source_rel == BENCHMARK_REL else (ticker, year)
        row = table.get(key)
        if row is None:
            outcomes.append(NO_ROW)
            continue
        outcome = compare_values(dataset_text, row.get(candidate.source_field, ""), numeric)
        outcomes.append(outcome)
        if outcome == MATCH:
            matches.append((candidate, row))

    if matches:
        candidate, row = matches[0]
        record["evidence_level"] = "cell_verified"
        record["source_class"] = candidate.source_class
        record["source_artifact"] = candidate.source_rel
        record["source_field"] = candidate.source_field
        record["source_effective_year"] = normalize_year(row.get("year", year))
        record["source_retrieved_at"] = str(row.get("retrieved_at", "") or "")
        record["transform_id"] = candidate.transform_id
        record["resolution_note"] = (
            "multi_candidate_priority_applied" if len(matches) > 1 else ""
        )
        return record

    record["evidence_level"] = "unknown"
    record["source_class"] = "unknown"
    record["transform_id"] = "T_UNRESOLVED"
    if not outcomes or all(outcome == NO_ROW for outcome in outcomes):
        record["resolution_note"] = "no_upstream_row"
    elif UNPARSEABLE in outcomes:
        record["resolution_note"] = "value_unparseable"
    else:
        record["resolution_note"] = "value_mismatch_all_candidates"
    return record


def build_records(
    dataset_columns: list[str],
    dataset_rows: list[dict[str, str]],
    tables: dict[str, dict[tuple[str, ...], dict[str, str]]],
) -> list[dict[str, object]]:
    """Build all cell records in the frozen (ticker, year, column-index) order."""
    missing_specs = sorted(c for c in dataset_columns if c not in COLUMN_SPECS)
    if missing_specs:
        raise ProvenanceError(f"columns absent from the frozen resolution table: {missing_specs}")
    extra_specs = sorted(c for c in COLUMN_SPECS if c not in dataset_columns)
    if extra_specs:
        raise ProvenanceError(f"resolution table names columns absent from the dataset: {extra_specs}")

    keyed: list[tuple[str, str, dict[str, str]]] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in dataset_rows:
        ticker = str(row["ticker"])
        year = normalize_year(row["year"])
        if CELL_KEY_SEPARATOR in ticker or CELL_KEY_SEPARATOR in year:
            raise ProvenanceError(f"cell-key separator present in identity: {ticker!r} {year!r}")
        if not ticker.isascii():
            raise ProvenanceError(f"non-ASCII ticker: {ticker!r}")
        if (ticker, year) in seen_keys:
            raise ProvenanceError(f"duplicate dataset key: {(ticker, year)}")
        seen_keys.add((ticker, year))
        keyed.append((ticker, year, row))

    present_years = {year for _, year, _ in keyed}
    for column in dataset_columns:
        if CELL_KEY_SEPARATOR in column:
            raise ProvenanceError(f"cell-key separator present in column name: {column!r}")

    records: list[dict[str, object]] = []
    for ticker, year, row in sorted(keyed, key=lambda item: (item[0], item[1])):
        for column in dataset_columns:  # dataset header order == column index order
            records.append(
                resolve_cell(
                    ticker,
                    year,
                    column,
                    row[column],
                    COLUMN_SPECS[column],
                    tables,
                    present_years,
                )
            )
    return records


# --------------------------------------------------------------------------- #
# Validation (§13.6)
# --------------------------------------------------------------------------- #
def validate_records(
    records: list[dict[str, object]],
    expected_rows: int,
    expected_columns: int,
    dataset_columns: list[str] | None = None,
) -> None:
    """Fail closed on any schema, vocabulary, ordering, or lineage violation."""
    expected_total = expected_rows * expected_columns
    if len(records) != expected_total:
        raise ProvenanceError(
            f"record count {len(records)} != rows*columns {expected_total}"
        )

    seen: set[str] = set()
    for record in records:
        if tuple(record.keys()) != RECORD_FIELDS:
            raise ProvenanceError(f"record field set/order mismatch for {record.get('cell_id')!r}")
        cell_id = record["cell_id"]
        if cell_id in seen:
            raise ProvenanceError(f"duplicate cell_id: {cell_id}")
        seen.add(cell_id)
        if cell_id != make_cell_id(str(record["ticker"]), f"{int(record['year']):04d}", str(record["column"])):
            raise ProvenanceError(f"cell_id does not reconstruct from its parts: {cell_id}")
        if record["value_state"] not in VALUE_STATES:
            raise ProvenanceError(f"value_state outside vocabulary: {record['value_state']!r}")
        if record["source_class"] not in SOURCE_CLASSES:
            raise ProvenanceError(f"source_class outside vocabulary: {record['source_class']!r}")
        if record["evidence_level"] not in EVIDENCE_LEVELS:
            raise ProvenanceError(f"evidence_level outside vocabulary: {record['evidence_level']!r}")
        if record["transform_id"] not in TRANSFORM_IDS:
            raise ProvenanceError(f"transform_id outside vocabulary: {record['transform_id']!r}")
        if record["resolution_note"] not in RESOLUTION_NOTES:
            raise ProvenanceError(f"resolution_note outside vocabulary: {record['resolution_note']!r}")
        if record["evidence_level"] == "unknown" and not record["resolution_note"]:
            raise ProvenanceError(f"unknown record without a resolution_note: {cell_id}")
        if record["resolution_note"] == "" and record["evidence_level"] != "cell_verified":
            raise ProvenanceError(f"empty resolution_note on a non-verified record: {cell_id}")
        if record["source_artifact"]:
            assert_relative_clean(str(record["source_artifact"]))
            if record["source_artifact"] not in ALLOWED_INPUT_RELS:
                raise ProvenanceError(f"undeclared source_artifact: {record['source_artifact']!r}")
        if record["evidence_level"] != "cell_verified" and record["source_artifact"]:
            raise ProvenanceError(f"non-verified record names a source_artifact: {cell_id}")

    # Lineage closure: every named upstream cell exists, no self-reference, no cycle.
    graph: dict[str, list[str]] = {}
    for record in records:
        upstream = str(record["upstream_cells"])
        graph[str(record["cell_id"])] = upstream.split(UPSTREAM_SEPARATOR) if upstream else []
    for cell_id, parents in graph.items():
        for parent in parents:
            if parent == cell_id:
                raise ProvenanceError(f"self-referencing upstream cell: {cell_id}")
            if parent not in graph:
                raise ProvenanceError(f"upstream cell not present in the artifact: {parent}")
    _assert_acyclic(graph)

    if dataset_columns is not None:
        per_column = Counter(str(record["column"]) for record in records)
        for column in dataset_columns:
            if per_column[column] != expected_rows:
                raise ProvenanceError(
                    f"column {column} has {per_column[column]} records, expected {expected_rows}"
                )
        index_of = {column: i for i, column in enumerate(dataset_columns)}
        keys = [
            (str(r["ticker"]), f"{int(r['year']):04d}", index_of[str(r["column"])])
            for r in records
        ]
        if keys != sorted(keys):
            raise ProvenanceError("records are not in (ticker, year, column-index) order")


def _assert_acyclic(graph: dict[str, list[str]]) -> None:
    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[str, int] = defaultdict(int)
    for start in graph:
        if colour[start] != WHITE:
            continue
        stack: list[tuple[str, int]] = [(start, 0)]
        colour[start] = GREY
        while stack:
            node, index = stack.pop()
            parents = graph.get(node, [])
            if index < len(parents):
                stack.append((node, index + 1))
                parent = parents[index]
                if colour[parent] == GREY:
                    raise ProvenanceError(f"cycle in upstream_cells at {parent}")
                if colour[parent] == WHITE:
                    colour[parent] = GREY
                    stack.append((parent, 0))
            else:
                colour[node] = BLACK


# --------------------------------------------------------------------------- #
# Leak guards (§13.7)
# --------------------------------------------------------------------------- #
FORBIDDEN_SUBSTRINGS = ("/Users/", "/home/", "C:\\")


def environment_markers(env: dict[str, str] | None = None) -> list[str]:
    env = os.environ if env is None else env
    markers = []
    for name in ("HOME", "USER", "PWD"):
        value = str(env.get(name, "") or "").strip()
        if len(value) >= 3:
            markers.append(value)
    return markers


def assert_no_leakage(text: str, label: str, env: dict[str, str] | None = None) -> None:
    for needle in FORBIDDEN_SUBSTRINGS:
        if needle in text:
            raise ProvenanceError(f"{label} contains an absolute-path marker: {needle!r}")
    for marker in environment_markers(env):
        if marker in text:
            raise ProvenanceError(f"{label} contains an environment value")


def assert_no_leading_slash(values: list[str], label: str) -> None:
    for value in values:
        if isinstance(value, str) and value.startswith("/"):
            raise ProvenanceError(f"{label} contains an absolute path: {value!r}")


def _json_strings(node: object) -> list[str]:
    out: list[str] = []
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for key, value in node.items():
            out.append(str(key))
            out.extend(_json_strings(value))
    elif isinstance(node, (list, tuple)):
        for value in node:
            out.extend(_json_strings(value))
    return out


# --------------------------------------------------------------------------- #
# Source digests (§13.5)
# --------------------------------------------------------------------------- #
def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_source_artifacts(root: Path = REPO_ROOT) -> list[dict[str, str]]:
    entries = []
    for rel in SOURCE_ARTIFACT_RELS:
        path = resolve_input(rel, root)
        entries.append({"path": rel, "sha256": sha256_of(path)})
    return entries


def stale_source_artifacts(
    entries: list[dict[str, str]], root: Path = REPO_ROOT
) -> list[str]:
    """Re-hash each recorded source artifact; return human-readable staleness problems."""
    problems: list[str] = []
    for entry in entries:
        rel = str(entry.get("path", ""))
        try:
            assert_relative_clean(rel)
        except ProvenanceError as exc:
            problems.append(f"{rel}: {exc}")
            continue
        path = root / rel
        if not path.is_file():
            problems.append(f"{rel}: recorded source artifact is missing")
            continue
        actual = sha256_of(path)
        if actual != entry.get("sha256"):
            problems.append(
                f"{rel}: recorded sha256 {entry.get('sha256')} != actual {actual}"
            )
    return problems


# --------------------------------------------------------------------------- #
# Aggregates and serialization
# --------------------------------------------------------------------------- #
def _counts(records: list[dict[str, object]], field: str) -> dict[str, int]:
    counter = Counter(str(record[field]) for record in records)
    return {key: counter[key] for key in sorted(counter)}


def build_payload(
    records: list[dict[str, object]],
    dataset_columns: list[str],
    dataset_rows: int,
    source_artifacts: list[dict[str, str]],
) -> dict[str, object]:
    unknown_cells = sorted(
        str(r["cell_id"]) for r in records if r["evidence_level"] == "unknown"
    )
    multi_cells = sorted(
        str(r["cell_id"])
        for r in records
        if r["resolution_note"] == "multi_candidate_priority_applied"
    )
    by_column: dict[str, dict[str, int]] = {}
    for record in records:
        bucket = by_column.setdefault(str(record["column"]), {})
        level = str(record["evidence_level"])
        bucket[level] = bucket.get(level, 0) + 1
    by_column = {column: dict(sorted(levels.items())) for column, levels in sorted(by_column.items())}

    null_count = sum(1 for r in records if r["value_state"] == "null")
    return {
        "provenance_schema_version": PROVENANCE_SCHEMA_VERSION,
        "task": TASK_ID,
        "artifact_role": "per-cell lineage record (passports v2), beside and independent of passports v1",
        "dataset": DATASET_REL,
        "records_csv": OUT_CSV_REL,
        "record_schema": list(RECORD_FIELDS),
        "cell_key_format": "{ticker}|{year}|{column}",
        "record_ordering": RECORD_ORDERING_RULE,
        "value_equality_rule": VALUE_EQUALITY_RULE,
        "lineage_scope": (
            "source_artifact records the nearest upstream artifact at which the value was verified; "
            "upstream_cells records intra-dataset dependencies only. No deeper lineage is materialized "
            "anywhere in this repository and none was invented."
        ),
        "value_state_vocabulary": list(VALUE_STATES),
        "source_class_definitions": dict(sorted(SOURCE_CLASS_DEFINITIONS.items())),
        "evidence_level_definitions": dict(sorted(EVIDENCE_LEVEL_DEFINITIONS.items())),
        "transform_definitions": dict(sorted(TRANSFORM_DEFINITIONS.items())),
        "resolution_note_definitions": dict(sorted(RESOLUTION_NOTE_DEFINITIONS.items())),
        "source_priority": [dict(rule) for rule in SOURCE_PRIORITY],
        "totals": {
            "rows": dataset_rows,
            "columns": len(dataset_columns),
            "cells": len(records),
            "value_present": len(records) - null_count,
            "value_null": null_count,
        },
        "counts_by_value_state": _counts(records, "value_state"),
        "counts_by_evidence_level": _counts(records, "evidence_level"),
        "counts_by_source_class": _counts(records, "source_class"),
        "counts_by_transform_id": _counts(records, "transform_id"),
        "counts_by_resolution_note": _counts(records, "resolution_note"),
        "counts_by_source_artifact": _counts(records, "source_artifact"),
        "counts_by_column_evidence_level": by_column,
        "multi_candidate_count": len(multi_cells),
        "multi_candidate_cells": multi_cells,
        "unknown_count": len(unknown_cells),
        "unknown_cells": unknown_cells,
        "source_artifacts": source_artifacts,
        "caveats": list(CAVEATS),
        "disclaimer": DISCLAIMER,
    }


def render_csv(records: list[dict[str, object]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(RECORD_FIELDS)
    for record in records:
        writer.writerow([record[field] for field in RECORD_FIELDS])
    return buffer.getvalue()


def render_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def render_markdown(payload: dict[str, object]) -> str:
    totals = payload["totals"]
    lines: list[str] = []
    lines.append("# Per-cell provenance — public modeling dataset (passports v2)")
    lines.append("")
    lines.append(f"- Task: `{payload['task']}`")
    lines.append(f"- Provenance schema version: `{payload['provenance_schema_version']}`")
    lines.append(f"- Dataset: `{payload['dataset']}`")
    lines.append(f"- Records: `{payload['records_csv']}`")
    lines.append(
        f"- Coverage: {totals['cells']} cells = {totals['rows']} rows x {totals['columns']} columns "
        f"({totals['value_present']} present, {totals['value_null']} null)"
    )
    lines.append("")
    lines.append(f"> {payload['disclaimer']}")
    lines.append("")

    lines.append("## Evidence level")
    lines.append("")
    lines.extend(
        _table(
            ["evidence_level", "cells", "meaning"],
            [
                [f"`{k}`", str(v), payload["evidence_level_definitions"][k]]
                for k, v in payload["counts_by_evidence_level"].items()
            ],
        )
    )
    lines.append("")

    lines.append("## Source class")
    lines.append("")
    lines.extend(
        _table(
            ["source_class", "cells"],
            [[f"`{k}`", str(v)] for k, v in payload["counts_by_source_class"].items()],
        )
    )
    lines.append("")

    lines.append("## Transformation")
    lines.append("")
    lines.extend(
        _table(
            ["transform_id", "cells", "meaning"],
            [
                [f"`{k}`", str(v), payload["transform_definitions"][k]]
                for k, v in payload["counts_by_transform_id"].items()
            ],
        )
    )
    lines.append("")

    lines.append("## Resolution notes")
    lines.append("")
    note_rows = []
    for key, value in payload["counts_by_resolution_note"].items():
        label = "`(empty)`" if key == "" else f"`{key}`"
        meaning = (
            "cell_verified with a single candidate source"
            if key == ""
            else payload["resolution_note_definitions"][key]
        )
        note_rows.append([label, str(value), meaning])
    lines.extend(_table(["resolution_note", "cells", "meaning"], note_rows))
    lines.append("")

    lines.append("## Verified source artifacts")
    lines.append("")
    lines.extend(
        _table(
            ["source_artifact", "cells verified"],
            [
                [f"`{k}`" if k else "`(none)`", str(v)]
                for k, v in payload["counts_by_source_artifact"].items()
            ],
        )
    )
    lines.append("")

    lines.append("## Unknown provenance")
    lines.append("")
    lines.append(
        f"{payload['unknown_count']} cells could not be attributed to any candidate source and are "
        "recorded as `unknown` with a mandatory reason code. They are reported, never repaired: no dataset "
        "value was changed and no tolerance was widened."
    )
    lines.append("")
    if payload["unknown_cells"]:
        unknown_by_column: dict[str, int] = {}
        for cell_id in payload["unknown_cells"]:
            unknown_by_column.setdefault(cell_id.rsplit("|", 1)[-1], 0)
            unknown_by_column[cell_id.rsplit("|", 1)[-1]] += 1
        lines.extend(
            _table(
                ["column", "unknown cells"],
                [[f"`{k}`", str(v)] for k, v in sorted(unknown_by_column.items())],
            )
        )
        lines.append("")
        lines.append("Complete list (also in the JSON report as `unknown_cells`):")
        lines.append("")
        lines.append("```")
        lines.extend(payload["unknown_cells"])
        lines.append("```")
        lines.append("")

    lines.append("## Multiple candidate sources")
    lines.append("")
    lines.append(
        f"{payload['multi_candidate_count']} cells were verified by more than one candidate source; the frozen "
        "source priority selected one and the record carries `multi_candidate_priority_applied`. Selection is "
        "never silent."
    )
    lines.append("")

    lines.append("## Query examples")
    lines.append("")
    lines.append("Which cells came from the reviewed 2024 balance-sheet override:")
    lines.append("")
    lines.append("```bash")
    lines.append(
        f"awk -F, 'NR==1 || $6==\"corrected_balance_2024\"' {payload['records_csv']}"
    )
    lines.append("```")
    lines.append("")
    lines.append("Which cells have no verified source:")
    lines.append("")
    lines.append("```bash")
    lines.append(f"awk -F, 'NR==1 || $7==\"unknown\"' {payload['records_csv']}")
    lines.append("```")
    lines.append("")
    lines.append("Provenance of one cell:")
    lines.append("")
    lines.append("```bash")
    lines.append(f"grep '^AEFES|2024|total_assets,' {payload['records_csv']}")
    lines.append("```")
    lines.append("")

    lines.append("## Caveats")
    lines.append("")
    for caveat in payload["caveats"]:
        lines.append(f"- {caveat}")
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Atomic write
# --------------------------------------------------------------------------- #
def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(text, encoding="utf-8", newline="")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def generate(root: Path = REPO_ROOT) -> dict[str, object]:
    """Build, validate, and write the three provenance artifacts. Returns the payload."""
    dataset_path = resolve_input(DATASET_REL, root)
    dataset_columns, dataset_rows = read_csv_rows(dataset_path)

    passports_path = resolve_input(PASSPORTS_V1_REL, root)
    passports = json.loads(passports_path.read_text(encoding="utf-8"))
    if passports.get("schema_version") != "1.0.0":
        raise ProvenanceError("passports v1 schema_version is not 1.0.0")
    v1_classes = {p["name"]: p["source_class"] for p in passports["passports"]}
    if set(v1_classes) != set(dataset_columns):
        raise ProvenanceError("passports v1 does not cover exactly the dataset columns")
    for column, spec in COLUMN_SPECS.items():
        if spec.kind == ASSERTED and v1_classes.get(column) != spec.nominal_source_class:
            raise ProvenanceError(
                f"column_asserted class for {column} disagrees with passports v1: "
                f"{spec.nominal_source_class!r} != {v1_classes.get(column)!r}"
            )

    tables: dict[str, dict[tuple[str, ...], dict[str, str]]] = {}
    required: dict[str, set[str]] = defaultdict(set)
    for spec in COLUMN_SPECS.values():
        for candidate in spec.candidates:
            required[candidate.source_rel].add(candidate.source_field)
    for rel in TICKER_YEAR_SOURCES:
        tables[rel] = load_keyed_table(resolve_input(rel, root), required[rel])
    tables[BENCHMARK_REL] = load_keyed_table(
        resolve_input(BENCHMARK_REL, root), required[BENCHMARK_REL], key_fields=("year",)
    )

    records = build_records(dataset_columns, dataset_rows, tables)
    validate_records(records, len(dataset_rows), len(dataset_columns), dataset_columns)

    source_artifacts = build_source_artifacts(root)
    stale = stale_source_artifacts(source_artifacts, root)
    if stale:  # pragma: no cover - defensive; digests were just computed
        raise ProvenanceError("stale source artifacts: " + "; ".join(stale))

    payload = build_payload(records, dataset_columns, len(dataset_rows), source_artifacts)
    if "limitations" in payload:  # pragma: no cover - defensive
        raise ProvenanceError("report must not carry a top-level 'limitations' key")

    csv_text = render_csv(records)
    json_text = render_json(payload)
    md_text = render_markdown(payload)

    for label, text in (("csv", csv_text), ("json", json_text), ("markdown", md_text)):
        assert_no_leakage(text, label)
    persisted_strings = [
        str(record[field])
        for record in records
        for field in ("source_artifact", "upstream_cells", "cell_id")
    ]
    assert_no_leading_slash(persisted_strings, "csv")
    assert_no_leading_slash(_json_strings(payload), "json")
    for entry in source_artifacts:
        assert_relative_clean(entry["path"])
    if {e["path"] for e in source_artifacts} != set(SOURCE_ARTIFACT_RELS):
        raise ProvenanceError("source_artifacts does not equal the frozen declared list")

    csv_bytes = csv_text.encode("utf-8")
    if len(csv_bytes) > 4 * 1024 * 1024:
        raise ProvenanceError(
            f"provenance CSV is {len(csv_bytes)} bytes (> 4 MB); the schema drifted — stop, do not shard"
        )

    out_dir = prepare_output_dir(root)
    write_atomic(out_dir / Path(OUT_CSV_REL).name, csv_text)
    write_atomic(out_dir / Path(OUT_JSON_REL).name, json_text)
    write_atomic(out_dir / Path(OUT_MD_REL).name, md_text)
    return payload


def main() -> None:
    payload = generate()
    totals = payload["totals"]
    levels = payload["counts_by_evidence_level"]
    print(f"[cell-provenance] wrote {OUT_CSV_REL}")
    print(f"[cell-provenance] wrote {OUT_JSON_REL}")
    print(f"[cell-provenance] wrote {OUT_MD_REL}")
    print(
        f"[cell-provenance] {totals['cells']} cells "
        f"({totals['rows']} rows x {totals['columns']} columns); "
        f"{totals['value_present']} present, {totals['value_null']} null"
    )
    for level in EVIDENCE_LEVELS:
        print(f"[cell-provenance]   {level}: {levels.get(level, 0)}")
    print(f"[cell-provenance] unknown_cells: {payload['unknown_count']}")
    print(f"[cell-provenance] multi_candidate_cells: {payload['multi_candidate_count']}")
    print("[cell-provenance] lineage record only; certifies no point-in-time, accuracy, or predictive claim")


if __name__ == "__main__":
    main()
