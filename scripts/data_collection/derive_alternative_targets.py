"""Derive CPI-deflated TRY and USD-basis T->T+1 return targets.

The canonical nominal target remains untouched.  For a nominal return ``r`` in
decimal form, December year-on-year CPI ``pi`` for target year T+1, and USD/TRY
year-end quotes ``fx_T`` and ``fx_T1`` (TRY per USD):

    real_return = (1 + r) / (1 + pi) - 1
    usd_return  = (1 + r) * fx_T / fx_T1 - 1

Inputs and outputs use percentage points.  Missing nominal, CPI, or FX values
propagate to null.  No interpolation, filling, or other imputation is allowed.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "data" / "trusted_clean"
MACRO = ROOT / "data" / "trusted_raw" / "macro"
MODELING = CLEAN / "modeling_dataset_training_2020_2025.csv"
CPI = MACRO / "cpi_yearly_tr.csv"
CPI_SIDECAR = MACRO / "cpi_yearly_tr.md"
FX = MACRO / "usdtry_year_end.csv"
OUTPUT = CLEAN / "modeling_targets_alternative.csv"
REPORT_JSON = CLEAN / "alternative_targets_report.json"
REPORT_MD = CLEAN / "alternative_targets_report.md"

OUTPUT_COLUMNS = [
    "ticker",
    "year",
    "target_year",
    "next_year_nominal_try_return_pct",
    "cpi_december_yoy_pct",
    "next_year_real_return_pct",
    "usdtry_start_try_per_usd",
    "usdtry_end_try_per_usd",
    "next_year_usd_return_pct",
    "real_target_status",
    "usd_target_status",
]

_UNSAFE_CLAIMS = (
    re.compile(r"\bwe found (?:a )?(?:real-terms |usd )?signal\b", re.I),
    re.compile(r"\b(?:establishes|demonstrates|proves) (?:a )?reliable predictive edge\b", re.I),
    re.compile(r"\bcreates investment value\b", re.I),
    re.compile(r"\bmarket-beating\b", re.I),
    re.compile(r"\bprofitable strategy\b", re.I),
    re.compile(r"\bpredicts future returns\b", re.I),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_claim_safety_text(text: str) -> None:
    """Reject positive performance/predictive interpretations of parallel targets."""
    for pattern in _UNSAFE_CLAIMS:
        if pattern.search(text):
            raise ValueError(f"Unsafe alternative-target claim: {pattern.pattern}")


def real_return_pct(nominal_pct, cpi_pct):
    """CPI-deflate percentage-point nominal returns with null propagation."""
    nominal = pd.to_numeric(nominal_pct, errors="coerce") / 100.0
    cpi = pd.to_numeric(cpi_pct, errors="coerce") / 100.0
    result = ((1.0 + nominal) / (1.0 + cpi) - 1.0) * 100.0
    return result.where((1.0 + cpi) > 0) if isinstance(result, pd.Series) else result


def usd_return_pct(nominal_pct, fx_start, fx_end):
    """Convert TRY nominal returns to USD basis using TRY-per-USD year-end quotes."""
    nominal = pd.to_numeric(nominal_pct, errors="coerce") / 100.0
    start = pd.to_numeric(fx_start, errors="coerce")
    end = pd.to_numeric(fx_end, errors="coerce")
    result = ((1.0 + nominal) * start / end - 1.0) * 100.0
    if isinstance(result, pd.Series):
        return result.where((start > 0) & (end > 0))
    return result if start > 0 and end > 0 else np.nan


def _load_modeling(path: Path) -> pd.DataFrame:
    required = {"ticker", "year", "target_year", "next_year_return_pct"}
    frame = pd.read_csv(path)
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    if frame.duplicated(["ticker", "year"]).any():
        raise ValueError(f"{path} contains duplicate ticker/year keys")
    years = pd.to_numeric(frame["year"], errors="coerce")
    target_years = pd.to_numeric(frame["target_year"], errors="coerce")
    if years.isna().any() or target_years.isna().any() or not target_years.eq(years + 1).all():
        raise ValueError("modeling target_year must align exactly to year + 1")
    return frame


def _load_cpi(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, comment="#")
    if list(frame.columns) != ["year", "cpi_december_yoy_pct"]:
        raise ValueError("CPI columns must be exactly ['year', 'cpi_december_yoy_pct']")
    if len(frame) > 6:
        raise ValueError("CPI input must contain at most six annual rows")
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["cpi_december_yoy_pct"] = pd.to_numeric(
        frame["cpi_december_yoy_pct"], errors="coerce"
    )
    if frame["year"].isna().any() or frame["year"].duplicated().any():
        raise ValueError("CPI years must be numeric and unique")
    if frame["cpi_december_yoy_pct"].isna().any():
        raise ValueError("CPI rows must contain numeric observations; omit unavailable years")
    if frame["cpi_december_yoy_pct"].le(-100).any():
        raise ValueError("CPI observations must be greater than -100 percent")
    return frame.astype({"year": int})


def _load_fx(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"year", "try_per_usd", "status", "source", "price_date"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    if frame["year"].isna().any() or frame["year"].duplicated().any():
        raise ValueError("USDTRY years must be numeric and unique")
    frame["try_per_usd"] = pd.to_numeric(frame["try_per_usd"], errors="coerce")
    invalid = frame["try_per_usd"].notna() & frame["try_per_usd"].le(0)
    if invalid.any():
        raise ValueError("USDTRY quotes must be positive")
    frame.loc[frame["status"].ne("success"), "try_per_usd"] = np.nan
    return frame.astype({"year": int})


def derive(
    modeling_path: Path = MODELING,
    cpi_path: Path = CPI,
    fx_path: Path = FX,
) -> pd.DataFrame:
    modeling = _load_modeling(Path(modeling_path))
    cpi = _load_cpi(Path(cpi_path)).rename(columns={"year": "target_year"})
    fx = _load_fx(Path(fx_path))[["year", "try_per_usd"]]

    out = modeling[["ticker", "year", "target_year", "next_year_return_pct"]].copy()
    out = out.rename(columns={"next_year_return_pct": "next_year_nominal_try_return_pct"})
    out = out.merge(cpi, on="target_year", how="left", validate="many_to_one", sort=False)
    out = out.merge(
        fx.rename(columns={"try_per_usd": "usdtry_start_try_per_usd"}),
        on="year",
        how="left",
        validate="many_to_one",
        sort=False,
    )
    out = out.merge(
        fx.rename(
            columns={
                "year": "target_year",
                "try_per_usd": "usdtry_end_try_per_usd",
            }
        ),
        on="target_year",
        how="left",
        validate="many_to_one",
        sort=False,
    )
    out["next_year_real_return_pct"] = real_return_pct(
        out["next_year_nominal_try_return_pct"], out["cpi_december_yoy_pct"]
    )
    out["next_year_usd_return_pct"] = usd_return_pct(
        out["next_year_nominal_try_return_pct"],
        out["usdtry_start_try_per_usd"],
        out["usdtry_end_try_per_usd"],
    )
    nominal_missing = out["next_year_nominal_try_return_pct"].isna()
    out["real_target_status"] = np.select(
        [nominal_missing, out["cpi_december_yoy_pct"].isna()],
        ["missing_nominal_target", "missing_cpi_target_year"],
        default="derived",
    )
    out["usd_target_status"] = np.select(
        [
            nominal_missing,
            out["usdtry_start_try_per_usd"].isna(),
            out["usdtry_end_try_per_usd"].isna(),
        ],
        ["missing_nominal_target", "missing_fx_start_year", "missing_fx_target_year"],
        default="derived",
    )
    return out[OUTPUT_COLUMNS]


def _report(frame: pd.DataFrame, inputs: list[Path]) -> dict:
    target_rows = int(frame["next_year_nominal_try_return_pct"].notna().sum())
    return {
        "schema_version": "1.0.0",
        "task": "R2-REAL-01",
        "design": {
            "nominal_preserved": True,
            "real_formula": "((1 + nominal_try_pct/100) / (1 + cpi_december_yoy_pct/100) - 1) * 100",
            "usd_formula": "((1 + nominal_try_pct/100) * usdtry_T / usdtry_T1 - 1) * 100",
            "fx_quote_direction": "TRY per USD; T divided by T+1",
            "missing_policy": "null propagation; no interpolation or imputation",
        },
        "inputs": [
            {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha256(path)}
            for path in inputs
        ],
        "rows": int(len(frame)),
        "nominal_target_rows": target_rows,
        "real_target_rows": int(frame["next_year_real_return_pct"].notna().sum()),
        "usd_target_rows": int(frame["next_year_usd_return_pct"].notna().sum()),
        "target_year_coverage": {
            str(int(year)): {
                "nominal": int(group["next_year_nominal_try_return_pct"].notna().sum()),
                "real": int(group["next_year_real_return_pct"].notna().sum()),
                "usd": int(group["next_year_usd_return_pct"].notna().sum()),
            }
            for year, group in frame.groupby("target_year", sort=True)
        },
        "claim_safety": {
            "descriptive_research_evidence_only": True,
            "investment_value_established": False,
            "reliable_predictive_edge_established": False,
            "statement": "Alternative return bases are descriptive research evidence only, not investment value or investment advice.",
        },
    }


def _render_markdown(report: dict) -> str:
    lines = [
        "# Alternative target derivation report (R2-REAL-01)",
        "",
        "The canonical nominal TRY targets are preserved byte-for-byte. CPI-deflated TRY and USD-basis targets are additive, descriptive research evidence only — not investment value or investment advice.",
        "",
        "## Design",
        "",
        f"- Real TRY: `{report['design']['real_formula']}`",
        f"- USD basis: `{report['design']['usd_formula']}`",
        f"- FX direction: {report['design']['fx_quote_direction']}",
        f"- Missing values: {report['design']['missing_policy']}",
        "",
        "## Coverage",
        "",
        f"- Rows: **{report['rows']}**",
        f"- Nominal target rows: **{report['nominal_target_rows']}**",
        f"- Real target rows: **{report['real_target_rows']}**",
        f"- USD target rows: **{report['usd_target_rows']}**",
        "",
        "These transformations do not establish a reliable predictive edge. Significance and multiplicity treatment are applied separately in `experiments/results_real_terms/` before any result is quoted.",
        "",
    ]
    text = "\n".join(lines)
    validate_claim_safety_text(text)
    return text


def run() -> tuple[Path, Path, Path]:
    if not CPI_SIDECAR.is_file():
        raise FileNotFoundError(f"CPI provenance sidecar missing: {CPI_SIDECAR}")
    frame = derive()
    CLEAN.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT, index=False, float_format="%.10f", lineterminator="\n")
    report = _report(frame, [MODELING, CPI, CPI_SIDECAR, FX])
    REPORT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    REPORT_MD.write_text(_render_markdown(report), encoding="utf-8")
    print(
        f"[alternative-targets] rows={len(frame)} real={report['real_target_rows']} "
        f"usd={report['usd_target_rows']} -> {OUTPUT.relative_to(ROOT)}"
    )
    return OUTPUT, REPORT_JSON, REPORT_MD


if __name__ == "__main__":
    run()
