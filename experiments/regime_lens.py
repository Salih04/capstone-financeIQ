"""Build a descriptive macro-context lens without regime-conditioned statistics.

R2-REGIME-01 has one task-defined observed macro period and only three model
test years.  The workflow therefore validates and exposes effective-dated macro
context, assigns dates to that single period, and emits an explicit untestable
state.  It never computes per-regime IC, p-values, returns, or causal effects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MACRO = ROOT / "data" / "trusted_raw" / "macro"
CONTEXT_CSV = MACRO / "macro_context_yearly.csv"
CONTEXT_SIDECAR = MACRO / "macro_context_yearly.md"
CPI_CSV = MACRO / "cpi_yearly_tr.csv"
USDTRY_CSV = MACRO / "usdtry_year_end.csv"
BIST100_CSV = ROOT / "data" / "trusted_raw" / "bist100_benchmark_returns.csv"
NOMINAL_REPORT = ROOT / "experiments" / "results" / "significance_report.md"
REAL_TRY_REPORT = ROOT / "experiments" / "results_real_terms" / "real_try" / "significance_report.md"
USD_REPORT = ROOT / "experiments" / "results_real_terms" / "usd" / "significance_report.md"
OUTPUT_DIR = ROOT / "experiments" / "results_regime"
REPORT_JSON = OUTPUT_DIR / "regime_context_report.json"
REPORT_MD = OUTPUT_DIR / "regime_context_report.md"

MANDATORY_STATEMENT = (
    "2020–2025 spans a single extraordinary Turkish macro regime (high inflation, "
    "deep TRY depreciation). Model behavior across regimes is therefore untested — "
    "this lens shows regime context and will only compute regime-conditional "
    "diagnostics when regime diversity exists."
)

EXPECTED_COLUMNS = [
    "year",
    "regime_start_date",
    "regime_end_date",
    "regime_id",
    "cpi_december_yoy_pct",
    "cpi_effective_date",
    "cpi_source_id",
    "policy_rate_year_end_pct",
    "policy_rate_effective_date",
    "policy_rate_source_id",
    "usdtry_year_end_try_per_usd",
    "usdtry_price_date",
    "usdtry_source_id",
    "bist100_return_pct",
    "bist100_period_end_date",
    "bist100_source_id",
]

METRICS = {
    "cpi_december_yoy_pct": ("cpi_effective_date", "cpi_source_id"),
    "policy_rate_year_end_pct": ("policy_rate_effective_date", "policy_rate_source_id"),
    "usdtry_year_end_try_per_usd": ("usdtry_price_date", "usdtry_source_id"),
    "bist100_return_pct": ("bist100_period_end_date", "bist100_source_id"),
}

SOURCE_CATALOG = {
    "tuik_cpi_december_yoy": {
        "name": "TÜİK national December year-on-year CPI",
        "source_file": "data/trusted_raw/macro/cpi_yearly_tr.md",
    },
    "tcmb_one_week_repo": {
        "name": "TCMB one-week repo auction policy-rate history",
        "source_url": "https://www.tcmb.gov.tr/wps/wcm/connect/en/tcmb%2Ben/main%2Bmenu/core%2Bfunctions/monetary%2Bpolicy/central%2Bbank%2Binterest%2Brates/1%2Bweek%2Brepo",
    },
    "yahoo_try_x_year_end": {
        "name": "Yahoo chart API TRY=X year-end close",
        "source_file": "data/trusted_raw/macro/usdtry_year_end.csv",
    },
    "yfinance_xu100_calendar_return": {
        "name": "Validated yfinance BIST100 calendar-year return",
        "source_file": "data/trusted_raw/bist100_benchmark_returns.csv",
    },
}

_UNSAFE_CLAIMS = (
    re.compile(r"\b(?:found|established|demonstrated|proved) (?:a )?regime[- ]specific (?:edge|skill|signal)\b", re.I),
    re.compile(r"\bregime[- ]robust(?:ness)? (?:is|was) (?:established|proved|demonstrated)\b", re.I),
    re.compile(r"\bmacro (?:conditions|variables|moves) caused\b", re.I),
    re.compile(r"\b(?:inflation|depreciation|policy rates?) explains? (?:the )?model\b", re.I),
    re.compile(r"\bthis regime predicts future returns\b", re.I),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_claim_safety_text(text: str) -> None:
    """Reject causal or regime-edge interpretations."""
    for pattern in _UNSAFE_CLAIMS:
        if pattern.search(text):
            raise ValueError(f"Unsafe regime-lens claim: {pattern.pattern}")


def assign_regime(value, regimes: list[dict[str, str]]) -> str | None:
    """Assign an observation date to an inclusive effective-dated period."""
    when = pd.to_datetime(value, errors="coerce")
    if pd.isna(when):
        return None
    matches = []
    for regime in regimes:
        start = pd.Timestamp(regime["start_date"])
        end = pd.Timestamp(regime["end_date"])
        if start <= when <= end:
            matches.append(regime["regime_id"])
    if len(matches) > 1:
        raise ValueError(f"Overlapping regime boundaries for {when.date()}: {matches}")
    return matches[0] if matches else None


def _validate_frame(frame: pd.DataFrame, expected_years: set[int] | None = None) -> pd.DataFrame:
    if list(frame.columns) != EXPECTED_COLUMNS:
        raise ValueError(f"Macro context columns must be exactly {EXPECTED_COLUMNS}")
    out = frame.copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    if out["year"].isna().any() or out["year"].duplicated().any():
        raise ValueError("Macro context years must be numeric and unique")
    out["year"] = out["year"].astype(int)
    if expected_years is not None and set(out["year"]) != expected_years:
        raise ValueError(f"Macro context years must be exactly {sorted(expected_years)}")

    for date_column in [
        "regime_start_date",
        "regime_end_date",
        "cpi_effective_date",
        "policy_rate_effective_date",
        "usdtry_price_date",
        "bist100_period_end_date",
    ]:
        parsed = pd.to_datetime(out[date_column], errors="coerce")
        invalid = out[date_column].notna() & parsed.isna()
        if invalid.any():
            raise ValueError(f"{date_column} contains invalid dates")

    for value_column, (date_column, source_column) in METRICS.items():
        out[value_column] = pd.to_numeric(out[value_column], errors="coerce")
        value_present = out[value_column].notna()
        metadata_present = out[date_column].notna() & out[source_column].notna()
        if not value_present.eq(metadata_present).all():
            raise ValueError(
                f"{value_column} must carry both {date_column} and {source_column}, or remain fully null"
            )
        unknown = sorted(set(out.loc[value_present, source_column]) - set(SOURCE_CATALOG))
        if unknown:
            raise ValueError(f"{value_column} uses unknown source IDs: {unknown}")
        effective_year = pd.to_datetime(out.loc[value_present, date_column]).dt.year
        if not effective_year.eq(out.loc[value_present, "year"]).all():
            raise ValueError(f"{date_column} must fall inside its observation year")

    if out["usdtry_year_end_try_per_usd"].dropna().le(0).any():
        raise ValueError("USDTRY observations must be positive")
    if out["cpi_december_yoy_pct"].dropna().le(-100).any():
        raise ValueError("CPI observations must be greater than -100 percent")

    definitions = out[["regime_id", "regime_start_date", "regime_end_date"]].drop_duplicates()
    if len(definitions) != 1:
        raise ValueError("R2-REGIME-01 requires exactly one task-defined observed period")
    definition = definitions.iloc[0]
    if definition["regime_id"] != "observed_2020_2025_macro_period":
        raise ValueError("Regime ID must remain the task-defined date-based identifier")
    if definition["regime_start_date"] != "2020-01-01" or definition["regime_end_date"] != "2025-12-31":
        raise ValueError("Regime boundaries must remain the task-defined inclusive 2020–2025 period")
    return out.sort_values("year", kind="stable").reset_index(drop=True)


def _assert_close(label: str, observed: pd.Series, expected: pd.Series) -> None:
    if not np.allclose(observed.to_numpy(float), expected.to_numpy(float), rtol=0, atol=1e-10, equal_nan=True):
        raise ValueError(f"Macro context {label} drifted from its committed shared source")


def _validate_shared_sources(frame: pd.DataFrame) -> None:
    cpi = pd.read_csv(CPI_CSV).sort_values("year")
    fx = pd.read_csv(USDTRY_CSV).sort_values("year")
    bist = pd.read_csv(BIST100_CSV).sort_values("year")
    aligned = frame.sort_values("year")
    if aligned["year"].tolist() != cpi["year"].tolist() or aligned["year"].tolist() != fx["year"].tolist() or aligned["year"].tolist() != bist["year"].tolist():
        raise ValueError("Macro context years do not align with committed CPI, USDTRY, and BIST100 sources")
    _assert_close("CPI", aligned["cpi_december_yoy_pct"], cpi["cpi_december_yoy_pct"])
    _assert_close("USDTRY", aligned["usdtry_year_end_try_per_usd"], fx["try_per_usd"])
    _assert_close("BIST100", aligned["bist100_return_pct"], bist["bist100_return_pct"])
    if aligned["usdtry_price_date"].tolist() != fx["price_date"].tolist():
        raise ValueError("Macro context USDTRY price dates drifted from the committed source")


def load_context(path: Path = CONTEXT_CSV, *, validate_shared: bool = True) -> pd.DataFrame:
    frame = _validate_frame(
        pd.read_csv(path),
        expected_years=set(range(2020, 2026)) if Path(path).resolve() == CONTEXT_CSV.resolve() else None,
    )
    if validate_shared:
        _validate_shared_sources(frame)
    return frame


def _metric(value, effective_date, source_id: str | float) -> dict[str, object]:
    if pd.isna(value):
        return {"value": None, "effective_date": None, "source_id": None, "source": None}
    source = SOURCE_CATALOG[str(source_id)]
    return {
        "value": float(value),
        "effective_date": str(effective_date),
        "source_id": str(source_id),
        "source": source,
    }


def build_report(frame: pd.DataFrame) -> dict[str, object]:
    frame = _validate_frame(frame)
    definition = frame[["regime_id", "regime_start_date", "regime_end_date"]].iloc[0]
    regimes = [
        {
            "regime_id": str(definition["regime_id"]),
            "start_date": str(definition["regime_start_date"]),
            "end_date": str(definition["regime_end_date"]),
        }
    ]
    test_years = [2023, 2024, 2025]
    assignments = {
        str(year): assign_regime(f"{year}-12-31", regimes)
        for year in test_years
    }
    distinct = sorted({value for value in assignments.values() if value is not None})
    if len(distinct) != 1:
        raise ValueError("The three test years must map to exactly one task-defined observed period")

    rows = []
    for row in frame.to_dict(orient="records"):
        rows.append(
            {
                "year": int(row["year"]),
                "regime_id": row["regime_id"],
                "cpi_december_yoy_pct": _metric(row["cpi_december_yoy_pct"], row["cpi_effective_date"], row["cpi_source_id"]),
                "policy_rate_year_end_pct": _metric(row["policy_rate_year_end_pct"], row["policy_rate_effective_date"], row["policy_rate_source_id"]),
                "usdtry_year_end_try_per_usd": _metric(row["usdtry_year_end_try_per_usd"], row["usdtry_price_date"], row["usdtry_source_id"]),
                "bist100_return_pct": _metric(row["bist100_return_pct"], row["bist100_period_end_date"], row["bist100_source_id"]),
            }
        )

    source_paths = [
        CONTEXT_CSV,
        CONTEXT_SIDECAR,
        CPI_CSV,
        USDTRY_CSV,
        BIST100_CSV,
        NOMINAL_REPORT,
        REAL_TRY_REPORT,
        USD_REPORT,
    ]
    report = {
        "schema_version": "1.0.0",
        "task": "R2-REGIME-01",
        "statement": MANDATORY_STATEMENT,
        "design": {
            "analysis_type": "descriptive macro-context sensitivity lens",
            "regime_definition_origin": "task-defined date boundary; not data-derived",
            "assignment_boundary": "inclusive",
            "test_years": test_years,
            "regimes": regimes,
            "test_year_assignments": assignments,
        },
        "conditional_diagnostics": {
            "computed": False,
            "status": "not_computed_insufficient_regime_diversity",
            "required_distinct_regimes": 2,
            "observed_distinct_regimes": len(distinct),
            "reason": "All three test years map to the same task-defined observed period; a per-regime number would only relabel the aggregate.",
        },
        "basis_evidence": {
            "nominal_try": {"source": "experiments/results/significance_report.md", "reliable_predictive_edge_established": False},
            "cpi_deflated_try": {"source": "experiments/results_real_terms/real_try/significance_report.md", "reliable_predictive_edge_established": False},
            "usd_basis": {"source": "experiments/results_real_terms/usd/significance_report.md", "reliable_predictive_edge_established": False},
        },
        "macro_context": rows,
        "source_artifacts": [
            {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256(path)}
            for path in source_paths
        ],
        "findings": [
            "Regime-conditional model diagnostics are untestable with the observed regime diversity and were not computed.",
            "The macro series are displayed as effective-dated descriptive context only; no causal effect is inferred.",
            "Nominal TRY, CPI-deflated TRY, and USD-basis evidence remain parallel negative-result analyses; none establishes a reliable predictive edge.",
        ],
        "limitations": [
            "Only three model test years (2023–2025) are observed, all inside one task-defined 2020–2025 macro period.",
            "No per-regime statistic, causal effect, or regime-specific predictive edge is estimable from one observed period.",
            "Multiplicity treatment and low-power limits from the nominal and alternative-basis significance reports remain applicable and unchanged.",
            "The 81-ticker training cohort is retrospectively fixed rather than verified point-in-time BIST100 membership, so survivorship and universe-selection look-ahead risks remain unresolved.",
            "Nominal TRY, national-CPI-deflated TRY, and USD-basis returns are separate descriptive bases; none represents investor-specific value or implementability.",
            "Prediction-artifact byte reproducibility remains numerical-environment-qualified.",
            "Missing macro observations remain null and are never interpolated or imputed.",
            "Research support only; not investment advice.",
        ],
    }
    validate_claim_safety_text(json.dumps(report, ensure_ascii=False))
    return report


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Regime Lens report (R2-REGIME-01)",
        "",
        f"**{report['statement']}**",
        "",
        "This is descriptive sensitivity context only. It does not estimate causal effects, investment value, or regime-specific model performance.",
        "",
        "## Effective-dated macro context",
        "",
        "| Year | CPI YoY | Year-end policy rate | TRY per USD | BIST100 nominal return |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in report["macro_context"]:
        def shown(key: str, suffix: str = "") -> str:
            value = row[key]["value"]
            return "null" if value is None else f"{value:.2f}{suffix}"

        lines.append(
            f"| {row['year']} | {shown('cpi_december_yoy_pct', '%')} | "
            f"{shown('policy_rate_year_end_pct', '%')} | "
            f"{shown('usdtry_year_end_try_per_usd')} | "
            f"{shown('bist100_return_pct', '%')} |"
        )
    lines.extend(
        [
            "",
            "Every non-null value carries an effective date and source in `regime_context_report.json`; missing values stay null.",
            "",
            "## Diagnostic status",
            "",
            f"- Status: **{report['conditional_diagnostics']['status']}**",
            f"- Observed distinct regimes: **{report['conditional_diagnostics']['observed_distinct_regimes']}**; required before activation: **{report['conditional_diagnostics']['required_distinct_regimes']}**.",
            "- No per-regime model statistics were computed.",
            "",
            "## Findings",
            "",
        ]
    )
    lines.extend(f"- {finding}" for finding in report["findings"])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in report["limitations"])
    text = "\n".join(lines) + "\n"
    validate_claim_safety_text(text)
    return text


def run(output_dir: Path = OUTPUT_DIR) -> tuple[Path, Path]:
    frame = load_context()
    report = build_report(frame)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / REPORT_JSON.name
    md_path = output_dir / REPORT_MD.name
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(
        "[regime-lens] status="
        f"{report['conditional_diagnostics']['status']} rows={len(frame)} -> "
        f"{output_dir.relative_to(ROOT) if output_dir.is_relative_to(ROOT) else output_dir}"
    )
    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
