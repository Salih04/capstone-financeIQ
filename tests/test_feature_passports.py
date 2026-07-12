from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.data_collection import validate


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPO_ROOT / "data" / "trusted_clean" / "modeling_dataset_2020_2025.csv"
PASSPORT_PATH = REPO_ROOT / "data" / "trusted_clean" / "feature_passports.json"
REQUIRED_FIELDS = {
    "name",
    "registry_role",
    "source_class",
    "transform_chain",
    "leakage_risk",
    "acceptance_status",
    "caveats",
    "evidence_files",
}
SOURCE_CLASSES = {
    "vendor_xlsx",
    "corrected_yearly_csv",
    "yahoo_fetch",
    "manual_shares",
    "derived",
    "metadata",
    "unknown",
}


def _load() -> tuple[pd.DataFrame, dict, dict[str, dict]]:
    dataset = pd.read_csv(DATASET_PATH)
    artifact = json.loads(PASSPORT_PATH.read_text(encoding="utf-8"))
    by_name = {passport["name"]: passport for passport in artifact["passports"]}
    return dataset, artifact, by_name


def test_feature_passports_cover_the_final_dataset_and_registry_exactly():
    dataset, artifact, by_name = _load()
    registry = {row["column"]: row for row in validate.feature_registry(dataset)}

    assert artifact["dataset"] == DATASET_PATH.name
    assert len(artifact["passports"]) == len(dataset.columns) == 61
    assert list(by_name) == list(dataset.columns)
    assert set(by_name) == set(registry)

    for name, passport in by_name.items():
        assert set(passport) == REQUIRED_FIELDS
        assert passport["registry_role"] == registry[name]["role"]
        assert passport["leakage_risk"] == registry[name]["leakage_risk"]
        assert passport["source_class"] in SOURCE_CLASSES
        assert passport["transform_chain"]
        assert len(passport["evidence_files"]) == len(set(passport["evidence_files"]))
        for evidence_file in passport["evidence_files"]:
            assert (REPO_ROOT / evidence_file).is_file(), (name, evidence_file)


def test_feature_passport_caveats_are_evidence_backed_and_do_not_overclaim():
    _, artifact, by_name = _load()

    frozen_evidence = "data/trusted_clean/frozen_column_evidence.json"
    for name in ("market_cap", "enterprise_value", "pe_ratio", "pb_ratio", "ev_ebitda"):
        passport = by_name[name]
        assert passport["source_class"] == "derived"
        assert frozen_evidence in passport["evidence_files"]
        assert any("frozen" in caveat.lower() for caveat in passport["caveats"])
        lineage_text = " ".join(passport["transform_chain"] + passport["caveats"]).lower()
        assert "manual shares" in lineage_text

    assert by_name["sector"]["source_class"] == "metadata"
    assert "METHODOLOGY.md" in by_name["sector"]["evidence_files"]
    assert any("must not be inferred" in caveat for caveat in by_name["sector"]["caveats"])

    for name in ("revenue", "roe", "current_assets", "same_year_return_pct"):
        passport = by_name[name]
        assert passport["source_class"] == "unknown"
        assert any("mixed" in caveat.lower() for caveat in passport["caveats"])

    rendered = json.dumps(artifact, ensure_ascii=False).lower()
    assert "predictive" not in rendered
