"""Deterministic, citation-complete research evidence memo (R3-MEMO-01).

The memo composes already-committed research evidence for one public-cohort
company.  It decides nothing, scores nothing, ranks nothing, and forecasts
nothing.  Every sentence is either a verbatim source string or a template whose
every value carries a citation that is re-read from the source and compared
before the sentence is emitted.

There is no LLM in this path, no network call, no statistical arithmetic, and no
export.  Allowed operations are field selection, ``len()`` of a cited list,
string templating, equality comparison for citation resolution, sha256 of file
bytes, and the injected clock that stamps the generation time.
"""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from typing import Any, Callable

from app.core.paths import resolve_repo_root
from app.services import citations, skeptic_service
from app.services.citations import CitationError


REPO_ROOT = resolve_repo_root()

COMPANY_CONTEXTS_DIR_REL = "data/trusted_clean/company_contexts"
DATA_QUALITY_REL = "data/trusted_clean/data_quality_report.json"
PASSPORTS_REL = "data/trusted_clean/feature_passports.json"
SIGNIFICANCE_REL = "experiments/results/significance_report.json"
SERVING_REL = "experiments/results_serving_eval/serving_eval_report.json"
CONTRACT_REL = "model_confidence_contract.json"
REGISTER_REL = "docs/limitations_register.md"
PACKET_REL = "docs/R3_MEMO_01_FABLE5_IMPLEMENTATION_PACKET.md"
SKEPTIC_SERVICE_REL = "backend/app/services/skeptic_service.py"

# Registered artifacts whose limitations this memo reproduces: exactly the
# registered JSON sources the memo itself cites.  Deterministic by construction.
LIMITATION_SOURCE_ARTIFACTS = (SIGNIFICANCE_REL, SERVING_REL)

PACKET_COPY_LOCATOR = "## 11. Mandatory backend-owned copy (exact strings)"
QUEUE_REL = "FINANCEIQ_AGENT_TASK_QUEUE.md"
QUEUE_TASK_LOCATOR = "### R3-MEMO-01 — Claim-aware research memo compiler"
QUEUE_INSUFFICIENT_RULE = (
    "if any section cannot be built citation-complete, emit `insufficient_data` for that "
    "section — never fill with prose"
)

SCHEMA_VERSION = 1
TASK = "R3-MEMO-01"
MEMO_TYPE = "evidence_memo"

_TICKER = re.compile(r"[A-Z0-9.]{1,16}")
_CONTEXT_NAME = re.compile(r"^(?P<ticker>[A-Z0-9.]+)_(?P<year>\d{4})\.json$")
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_RFC3339_UTC = "%Y-%m-%dT%H:%M:%SZ"

# Deployment authorities that may supply the commit, highest precedence first.
_DEPLOYMENT_COMMIT_ENV = ("RENDER_GIT_COMMIT",)

MEMO_HEADLINE = (
    "Research evidence memo — research support only, NOT investment advice. The committed "
    "conclusion is unchanged: no reliable predictive edge was established."
)
RESEARCH_BOUNDARY = (
    "This memo composes committed, historical research evidence for one company. It contains "
    "no recommendation, no forecast, no price target, and no investment-value assessment. "
    "Walk-forward evaluation found no reliable predictive edge: no ML model is statistically "
    "distinguishable from the within-year null after family-wise correction."
)
PRIMARY_DISCLAIMER = "Experimental ranking signal — research support only, NOT investment advice. Do not use for buy/sell/hold decisions."
CLOSING = (
    "Composed from committed research artifacts. No part of this memo is a recommendation; "
    "the underlying evaluation found no reliable predictive edge."
)

IDENTITY_BOUNDARY = (
    "Descriptive historical identity and coverage only; inclusion in this memo is not a "
    "selection, endorsement, or ranking."
)
SIGNIFICANCE_BOUNDARY = (
    "Raw p-values appear only together with their Bonferroni-adjusted values. Detectable-IC "
    "thresholds are design limits, not estimates of the true IC."
)
LIMITATIONS_BOUNDARY = (
    "Limitations are reproduced verbatim from their source reports; none is optional and the "
    "strongest caveat is never summarized away."
)

INSUFFICIENT_COPY = (
    "This section could not be composed citation-complete from committed artifacts, so no "
    "sentence is emitted for it. Missing evidence is named rather than filled with prose."
)

SECTIONS: tuple[tuple[str, str], ...] = (
    ("identity_and_coverage", "Identity & data coverage"),
    ("evidence_quality", "Evidence quality"),
    ("skeptic_challenge", "Skeptic challenge results"),
    ("significance_and_power", "Significance & power context"),
    ("limitations", "Limitations"),
    ("provenance_stamp", "Provenance stamp"),
)


class MemoCompanyUnknown(LookupError):
    """Raised when no committed company context exists for a well-formed ticker."""


class MemoEvidenceUnavailable(RuntimeError):
    """Raised when required global provenance or source integrity is unavailable."""


# ---------------------------------------------------------------------------
# Citation construction — every citation is verified against its source
# ---------------------------------------------------------------------------


class _CitationRegistry:
    """Builds C001…Cnnn citations, verifying each one against its source."""

    def __init__(self) -> None:
        self._citations: list[dict[str, Any]] = []
        self._by_key: dict[tuple, str] = {}
        self._sha_cache: dict[str, str] = {}

    def _sha(self, relative: str) -> str:
        if relative not in self._sha_cache:
            self._sha_cache[relative] = citations.sha256_of(relative)
        return self._sha_cache[relative]

    def _register(self, key: tuple, build: Callable[[str], dict[str, Any]]) -> str:
        existing = self._by_key.get(key)
        if existing is not None:
            return existing
        citation_id = f"C{len(self._citations) + 1:03d}"
        self._citations.append(build(citation_id))
        self._by_key[key] = citation_id
        return citation_id

    def json_field(
        self,
        *,
        family: str,
        relative: str,
        field_path: str,
        value: Any,
        scope: str,
        label: str,
        derivation: str = "identity",
    ) -> str:
        """Cite an exact JSON field value, re-read and compared before use."""
        if derivation not in {"identity", "count"}:
            raise CitationError(f"{relative}: unsupported derivation {derivation!r}")
        citations.verify_json_field(relative, field_path, value)
        if derivation == "count" and not isinstance(value, list):
            raise CitationError(f"{relative}: count derivation requires a list at {field_path}")
        key = ("json_field", relative, field_path, derivation)
        return self._register(
            key,
            lambda citation_id: {
                "citation_id": citation_id,
                "citation_kind": "json_field",
                "evidence_family": family,
                "source_artifact": relative,
                "sha256": self._sha(relative),
                "scope": scope,
                "field_path": field_path,
                "value": value,
                "derivation": derivation,
                "locator": None,
                "quoted_text": None,
                "label": label,
            },
        )

    def text_span(
        self,
        *,
        family: str,
        relative: str,
        locator: str,
        quoted_text: str,
        scope: str,
        label: str,
    ) -> str:
        """Cite an exact contiguous quotation inside a located Markdown section."""
        citations.verify_text_span(relative, locator, quoted_text)
        key = ("text_span", relative, locator, quoted_text)
        return self._register(
            key,
            lambda citation_id: {
                "citation_id": citation_id,
                "citation_kind": "text_span",
                "evidence_family": family,
                "source_artifact": relative,
                "sha256": self._sha(relative),
                "scope": scope,
                "field_path": None,
                "value": None,
                "derivation": "exact_quotation",
                "locator": locator,
                "quoted_text": quoted_text,
                "label": label,
            },
        )

    def service_evidence(
        self,
        *,
        report: dict[str, Any],
        field_path: str,
        value: Any,
        scope: str,
        label: str,
    ) -> str:
        """Cite a field of the deterministic Skeptic response, compared before use."""
        actual = citations.resolve_field(report, field_path, source=SKEPTIC_SERVICE_REL)
        if actual != value or type(actual) is not type(value):
            raise CitationError(
                f"{SKEPTIC_SERVICE_REL}: cited value does not match the service at {field_path}"
            )
        key = ("service_evidence", SKEPTIC_SERVICE_REL, field_path)
        return self._register(
            key,
            lambda citation_id: {
                "citation_id": citation_id,
                "citation_kind": "service_evidence",
                "evidence_family": "skeptic",
                "source_artifact": SKEPTIC_SERVICE_REL,
                "sha256": self._sha(SKEPTIC_SERVICE_REL),
                "scope": scope,
                "field_path": field_path,
                "value": value,
                "derivation": "identity",
                "locator": None,
                "quoted_text": None,
                "label": label,
            },
        )

    def packet_copy(self, quoted_text: str, label: str) -> str:
        """Cite frozen backend-owned copy to its authoring authority."""
        return self.text_span(
            family="memo_copy_authority",
            relative=PACKET_REL,
            locator=PACKET_COPY_LOCATOR,
            quoted_text=quoted_text,
            scope="policy",
            label=label,
        )

    def emitted(self) -> list[dict[str, Any]]:
        return list(self._citations)

    def source_artifacts(self) -> list[dict[str, str]]:
        paths = sorted({citation["source_artifact"] for citation in self._citations})
        return [{"path": path, "sha256": self._sha(path)} for path in paths]


def _item(text: str, citation_ids: list[str]) -> dict[str, Any]:
    if not text or not citation_ids:
        raise CitationError("an evidence sentence requires text and at least one citation")
    return {"text": text, "citation_ids": list(citation_ids)}


def _section(section_id: str, title: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "section_id": section_id,
        "title": title,
        "status": "available",
        "evidence": evidence,
        "missing_evidence": [],
    }


def _insufficient_section(
    section_id: str, title: str, source_file: str, reason: str, registry: _CitationRegistry
) -> dict[str, Any]:
    """Fixed, claim-safe insufficient-data copy backed by its policy authority."""
    citation_id = registry.text_span(
        family="memo_copy_authority",
        relative=QUEUE_REL,
        locator=QUEUE_TASK_LOCATOR,
        quoted_text=QUEUE_INSUFFICIENT_RULE,
        scope="policy",
        label="Governed insufficient-data rule: never fill an evidence gap with prose",
    )
    return {
        "section_id": section_id,
        "title": title,
        "status": "insufficient_data",
        "evidence": [_item(INSUFFICIENT_COPY, [citation_id])],
        "missing_evidence": [{"source_file": source_file, "reason": reason}],
    }


# ---------------------------------------------------------------------------
# Source loading
# ---------------------------------------------------------------------------


def _context_relative(ticker: str) -> str:
    """Latest committed company-context path for the ticker (Courtroom convention)."""
    directory = REPO_ROOT / COMPANY_CONTEXTS_DIR_REL
    if not directory.is_dir():
        raise MemoEvidenceUnavailable(
            f"Company contexts are unavailable at {COMPANY_CONTEXTS_DIR_REL}. "
            "Run `make build-company-contexts`."
        )
    years: list[int] = []
    for path in directory.glob(f"{ticker}_*.json"):
        match = _CONTEXT_NAME.fullmatch(path.name)
        if match and match.group("ticker") == ticker:
            years.append(int(match.group("year")))
    if not years:
        raise MemoCompanyUnknown(
            f"No committed company context exists for {ticker} under {COMPANY_CONTEXTS_DIR_REL}."
        )
    return f"{COMPANY_CONTEXTS_DIR_REL}/{ticker}_{max(years)}.json"


def _load_global_artifact(relative: str) -> dict[str, Any]:
    try:
        return citations.load_json_artifact(relative)
    except CitationError as exc:
        raise MemoEvidenceUnavailable(str(exc)) from exc


def _assert_evidence_state(contract: dict[str, Any], significance: dict[str, Any]) -> None:
    """Refuse to compose a memo under a changed or contradictory evidence state."""
    state = contract.get("evidence_state")
    if not isinstance(state, dict):
        raise MemoEvidenceUnavailable(f"{CONTRACT_REL}: evidence_state is missing or malformed.")
    if state.get("reliable_predictive_edge_observed") is not False:
        raise MemoEvidenceUnavailable(
            f"{CONTRACT_REL}: evidence_state.reliable_predictive_edge_observed is not false; "
            "the memo may not be composed under a changed evidence state."
        )
    if state.get("conclusion") != "no reliable predictive edge":
        raise MemoEvidenceUnavailable(
            f"{CONTRACT_REL}: evidence_state.conclusion has changed; the memo may not be "
            "composed under a changed evidence state."
        )
    headline = significance.get("headline")
    if not isinstance(headline, dict):
        raise MemoEvidenceUnavailable(f"{SIGNIFICANCE_REL}: headline is missing or malformed.")
    if headline.get("significant_fwer_0_05") is not False:
        raise MemoEvidenceUnavailable(
            f"{SIGNIFICANCE_REL} and {CONTRACT_REL} disagree: the significance headline reports "
            "a family-wise significant result while the contract records none."
        )


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def resolve_git_sha() -> tuple[str, str]:
    """Return ``(sha, authority)`` for the repository commit, or fail closed."""
    for name in _DEPLOYMENT_COMMIT_ENV:
        candidate = (os.environ.get(name) or "").strip().lower()
        if candidate and _SHA40.fullmatch(candidate):
            return candidate, f"deployment_commit_env:{name}"
    try:
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        raise MemoEvidenceUnavailable(
            "The repository commit could not be resolved truthfully from a deployment "
            "environment value or from git HEAD; the memo refuses rather than stamping an "
            "unverified commit."
        ) from None
    candidate = completed.stdout.strip().lower()
    if not _SHA40.fullmatch(candidate):
        raise MemoEvidenceUnavailable(
            "git HEAD did not return a 40-character commit id; the memo refuses rather than "
            "stamping an unverified commit."
        )
    return candidate, "repository_git_head"


def _utc_timestamp(clock: Callable[[], datetime] | None) -> str:
    now = clock() if clock is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise MemoEvidenceUnavailable("The injected clock returned a naive datetime.")
    return now.astimezone(timezone.utc).strftime(_RFC3339_UTC)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _build_identity(
    ticker: str,
    context_rel: str,
    context: dict[str, Any],
    curated: dict[str, dict[str, str]],
    registry: _CitationRegistry,
) -> dict[str, Any]:
    section_id, title = SECTIONS[0]
    evidence = [
        _item(
            IDENTITY_BOUNDARY,
            [registry.packet_copy(IDENTITY_BOUNDARY, "Identity-section boundary copy")],
        )
    ]
    year = context["year"]
    evidence.append(
        _item(
            f"The validated company context records ticker {context['ticker']} for year {year}.",
            [
                registry.json_field(
                    family="company_context",
                    relative=context_rel,
                    field_path="ticker",
                    value=context["ticker"],
                    scope="company",
                    label=f"Validated company context identity, {ticker}",
                ),
                registry.json_field(
                    family="company_context",
                    relative=context_rel,
                    field_path="year",
                    value=year,
                    scope="company",
                    label=f"Validated company context year, {ticker}",
                ),
            ],
        )
    )
    universe = context["universe"]
    evidence.append(
        _item(
            "The context records is_public_universe="
            f"{str(universe['is_public_universe']).lower()} and is_training_universe="
            f"{str(universe['is_training_universe']).lower()}.",
            [
                registry.json_field(
                    family="company_context",
                    relative=context_rel,
                    field_path="universe.is_public_universe",
                    value=universe["is_public_universe"],
                    scope="company",
                    label="Public-cohort membership recorded in the company context",
                ),
                registry.json_field(
                    family="company_context",
                    relative=context_rel,
                    field_path="universe.is_training_universe",
                    value=universe["is_training_universe"],
                    scope="company",
                    label="Training-universe membership recorded in the company context",
                ),
            ],
        )
    )
    quality = context["data_quality"]
    missing_fields = quality["missing_fields"]
    missing_citation = registry.json_field(
        family="company_context",
        relative=context_rel,
        field_path="data_quality.missing_fields",
        value=missing_fields,
        scope="company",
        label="Missing fields listed by the validated company context",
        derivation="count",
    )
    listed = f": {', '.join(str(field) for field in missing_fields)}." if missing_fields else "."
    evidence.append(
        _item(
            f"The validated company context lists {len(missing_fields)} missing fields{listed}",
            [missing_citation],
        )
    )
    evidence.append(
        _item(
            "The context records has_data_row="
            f"{str(quality['has_data_row']).lower()}.",
            [
                registry.json_field(
                    family="company_context",
                    relative=context_rel,
                    field_path="data_quality.has_data_row",
                    value=quality["has_data_row"],
                    scope="company",
                    label="Row presence recorded in the validated company context",
                )
            ],
        )
    )
    for index, warning in enumerate(quality["warnings"]):
        evidence.append(
            _item(
                warning,
                [
                    registry.json_field(
                        family="company_context",
                        relative=context_rel,
                        field_path=f"data_quality.warnings[{index}]",
                        value=warning,
                        scope="company",
                        label=f"Context warning {index} reproduced verbatim",
                    )
                ],
            )
        )
    seed = curated["sector unpopulated"]
    evidence.append(
        _item(
            seed["source_text"],
            [
                registry.text_span(
                    family="curated_limitation",
                    relative=seed["source_path"],
                    locator=seed["source_locator"],
                    quoted_text=seed["source_text"],
                    scope="global",
                    label="Sector identity is unavailable and is never approximated",
                ),
                registry.text_span(
                    family="limitations_register",
                    relative=REGISTER_REL,
                    locator=f"### {seed['concept']}",
                    quoted_text=seed["source_text"],
                    scope="global",
                    label="Registered curated limitation: sector unpopulated",
                ),
            ],
        )
    )
    return _section(section_id, title, evidence)


def _build_evidence_quality(
    passports: dict[str, Any],
    quality: dict[str, Any],
    registry: _CitationRegistry,
) -> dict[str, Any]:
    section_id, title = SECTIONS[1]
    disclaimer = passports["disclaimer"]
    evidence = [
        _item(
            disclaimer,
            [
                registry.json_field(
                    family="feature_passports",
                    relative=PASSPORTS_REL,
                    field_path="disclaimer",
                    value=disclaimer,
                    scope="global",
                    label="Lineage-record boundary reproduced verbatim",
                )
            ],
        ),
        _item(
            f"The generated lineage record contains {len(passports['passports'])} feature "
            "passports.",
            [
                registry.json_field(
                    family="feature_passports",
                    relative=PASSPORTS_REL,
                    field_path="passports",
                    value=passports["passports"],
                    scope="global",
                    label="Per-column lineage passports",
                    derivation="count",
                )
            ],
        ),
        _item(
            f"The dataset quality report records n_features={quality['n_features']}.",
            [
                registry.json_field(
                    family="data_quality",
                    relative=DATA_QUALITY_REL,
                    field_path="n_features",
                    value=quality["n_features"],
                    scope="global",
                    label="Accepted feature count recorded by the quality report",
                )
            ],
        ),
        _item(
            "The dataset quality report lists "
            f"{len(quality['frozen_feature_columns_remaining'])} frozen feature columns "
            "remaining in the accepted dataset.",
            [
                registry.json_field(
                    family="data_quality",
                    relative=DATA_QUALITY_REL,
                    field_path="frozen_feature_columns_remaining",
                    value=quality["frozen_feature_columns_remaining"],
                    scope="global",
                    label="Frozen feature columns remaining",
                    derivation="count",
                )
            ],
        ),
        _item(
            "The dataset quality report lists "
            f"{len(quality['rejected_old_snapshot_columns'])} rejected old-snapshot columns.",
            [
                registry.json_field(
                    family="data_quality",
                    relative=DATA_QUALITY_REL,
                    field_path="rejected_old_snapshot_columns",
                    value=quality["rejected_old_snapshot_columns"],
                    scope="global",
                    label="Old-snapshot columns rejected rather than imputed",
                    derivation="count",
                )
            ],
        ),
        _item(
            "The dataset quality report records valid_for_T_to_T1_modeling="
            f"{str(quality['valid_for_T_to_T1_modeling']).lower()}.",
            [
                registry.json_field(
                    family="data_quality",
                    relative=DATA_QUALITY_REL,
                    field_path="valid_for_T_to_T1_modeling",
                    value=quality["valid_for_T_to_T1_modeling"],
                    scope="global",
                    label="Leakage-safe T to T+1 dataset validity flag",
                )
            ],
        ),
    ]
    return _section(section_id, title, evidence)


def _build_skeptic(report: dict[str, Any], registry: _CitationRegistry) -> dict[str, Any]:
    section_id, title = SECTIONS[2]
    footer = report["footer"]
    evidence = [
        _item(
            footer,
            [
                registry.service_evidence(
                    report=report,
                    field_path="footer",
                    value=footer,
                    scope="global",
                    label="Skeptic footer reproduced verbatim",
                )
            ],
        )
    ]
    for index, check in enumerate(report["checks"]):
        check_id = check["check_id"]
        for evidence_index, entry in enumerate(check["evidence"]):
            fact = entry["fact"]
            evidence.append(
                _item(
                    fact,
                    [
                        registry.service_evidence(
                            report=report,
                            field_path=f"checks[{index}].evidence[{evidence_index}].fact",
                            value=fact,
                            scope="company",
                            label=f"Skeptic {check_id} evidence {evidence_index}, verbatim",
                        )
                    ],
                )
            )
    return _section(section_id, title, evidence)


def _build_significance(
    significance: dict[str, Any],
    serving: dict[str, Any],
    registry: _CitationRegistry,
) -> dict[str, Any]:
    section_id, title = SECTIONS[3]
    evidence = [
        _item(
            SIGNIFICANCE_BOUNDARY,
            [registry.packet_copy(SIGNIFICANCE_BOUNDARY, "Significance-section boundary copy")],
        )
    ]
    headline = significance["headline"]
    evidence.append(
        _item(
            headline["conclusion"],
            [
                registry.json_field(
                    family="significance",
                    relative=SIGNIFICANCE_REL,
                    field_path="headline.conclusion",
                    value=headline["conclusion"],
                    scope="global",
                    label="Family-wise corrected conclusion, verbatim",
                )
            ],
        )
    )
    models = significance["models"]
    ml_indexes = [
        index for index, model in enumerate(models) if model.get("kind") == "ml"
    ]
    if not ml_indexes:
        raise MemoEvidenceUnavailable(f"{SIGNIFICANCE_REL}: no ML model evidence is present.")
    for index in ml_indexes:
        model = models[index]
        pooled = model["pooled"]
        for key in (
            "observed_ic",
            "permutation_p_value_two_sided",
            "bonferroni_adjusted_p_value",
            "significant_fwer_0_05",
        ):
            if key not in pooled or pooled[key] is None:
                raise MemoEvidenceUnavailable(
                    f"{SIGNIFICANCE_REL}: models[{index}].pooled.{key} is missing; a raw "
                    "p-value is never rendered without its adjusted companion."
                )
        base = f"models[{index}].pooled"
        evidence.append(
            _item(
                f"Model {model['model']} has pooled observed IC {pooled['observed_ic']} with a "
                f"two-sided permutation p-value of {pooled['permutation_p_value_two_sided']} and "
                f"a Bonferroni-adjusted p-value of {pooled['bonferroni_adjusted_p_value']}; "
                f"significant_fwer_0_05 is {str(pooled['significant_fwer_0_05']).lower()}.",
                [
                    registry.json_field(
                        family="significance",
                        relative=SIGNIFICANCE_REL,
                        field_path=f"models[{index}].model",
                        value=model["model"],
                        scope="global",
                        label=f"ML model name at index {index}",
                    ),
                    registry.json_field(
                        family="significance",
                        relative=SIGNIFICANCE_REL,
                        field_path=f"{base}.observed_ic",
                        value=pooled["observed_ic"],
                        scope="global",
                        label=f"Pooled observed IC for {model['model']}",
                    ),
                    registry.json_field(
                        family="significance",
                        relative=SIGNIFICANCE_REL,
                        field_path=f"{base}.permutation_p_value_two_sided",
                        value=pooled["permutation_p_value_two_sided"],
                        scope="global",
                        label=f"Raw permutation p-value for {model['model']}",
                    ),
                    registry.json_field(
                        family="significance",
                        relative=SIGNIFICANCE_REL,
                        field_path=f"{base}.bonferroni_adjusted_p_value",
                        value=pooled["bonferroni_adjusted_p_value"],
                        scope="global",
                        label=f"Bonferroni-adjusted p-value for {model['model']}",
                    ),
                    registry.json_field(
                        family="significance",
                        relative=SIGNIFICANCE_REL,
                        field_path=f"{base}.significant_fwer_0_05",
                        value=pooled["significant_fwer_0_05"],
                        scope="global",
                        label=f"Family-wise significance flag for {model['model']}",
                    ),
                ],
            )
        )
    evaluated = significance["analysis"]["evaluated_tickers_per_model_split"]
    evidence.append(
        _item(
            "Persisted evaluation uses "
            f"{', '.join(str(value) for value in evaluated)} evaluated tickers per model and "
            "split.",
            [
                registry.json_field(
                    family="significance",
                    relative=SIGNIFICANCE_REL,
                    field_path="analysis.evaluated_tickers_per_model_split",
                    value=evaluated,
                    scope="global",
                    label="Evaluated tickers per model and split",
                )
            ],
        )
    )
    designs = significance["power_analysis"]["designs"]
    for index, design in enumerate(designs):
        if design.get("design_id") not in {"current_one_split", "current_three_year_pooled"}:
            continue
        evidence.append(
            _item(
                f"Design {design['design_id']} has an analytic minimum detectable absolute IC of "
                f"{design['analytic_minimum_detectable_abs_ic']}.",
                [
                    registry.json_field(
                        family="significance",
                        relative=SIGNIFICANCE_REL,
                        field_path=f"power_analysis.designs[{index}].design_id",
                        value=design["design_id"],
                        scope="global",
                        label=f"Power design identifier at index {index}",
                    ),
                    registry.json_field(
                        family="significance",
                        relative=SIGNIFICANCE_REL,
                        field_path=(
                            f"power_analysis.designs[{index}]."
                            "analytic_minimum_detectable_abs_ic"
                        ),
                        value=design["analytic_minimum_detectable_abs_ic"],
                        scope="global",
                        label=f"Detectable |IC| band for {design['design_id']}",
                    ),
                ],
            )
        )
    detectable = significance["power_analysis"]["definitions"]["detectable_ic"]
    evidence.append(
        _item(
            f"The report defines detectable IC as {detectable}",
            [
                registry.json_field(
                    family="significance",
                    relative=SIGNIFICANCE_REL,
                    field_path="power_analysis.definitions.detectable_ic",
                    value=detectable,
                    scope="global",
                    label="Detectable-IC definition, verbatim",
                )
            ],
        )
    )
    serving_result = serving["serving_result"]
    for key in ("conclusion", "test_label", "raw_permutation_p_value_two_sided", "pooled_ic"):
        if key not in serving_result or serving_result[key] is None:
            raise MemoEvidenceUnavailable(
                f"{SERVING_REL}: serving_result.{key} is missing; the serving number is never "
                "rendered without its outside-family label."
            )
    evidence.append(
        _item(
            serving_result["conclusion"],
            [
                registry.json_field(
                    family="serving_eval",
                    relative=SERVING_REL,
                    field_path="serving_result.conclusion",
                    value=serving_result["conclusion"],
                    scope="global",
                    label="Serving-heuristic evaluation conclusion, verbatim",
                )
            ],
        )
    )
    evidence.append(
        _item(
            "The serving-heuristic pooled IC "
            f"{serving_result['pooled_ic']} and its raw permutation p-value "
            f"{serving_result['raw_permutation_p_value_two_sided']} come from a "
            f"{serving_result['test_label']}; they are not family-corrected and are not "
            "comparable with the six-model Bonferroni family above.",
            [
                registry.json_field(
                    family="serving_eval",
                    relative=SERVING_REL,
                    field_path="serving_result.pooled_ic",
                    value=serving_result["pooled_ic"],
                    scope="global",
                    label="Serving-heuristic pooled IC",
                ),
                registry.json_field(
                    family="serving_eval",
                    relative=SERVING_REL,
                    field_path="serving_result.raw_permutation_p_value_two_sided",
                    value=serving_result["raw_permutation_p_value_two_sided"],
                    scope="global",
                    label="Serving-heuristic raw permutation p-value",
                ),
                registry.json_field(
                    family="serving_eval",
                    relative=SERVING_REL,
                    field_path="serving_result.test_label",
                    value=serving_result["test_label"],
                    scope="global",
                    label="Outside-family test label, verbatim",
                ),
            ],
        )
    )
    return _section(section_id, title, evidence)


def _build_limitations(
    register: dict[str, Any], registry: _CitationRegistry
) -> dict[str, Any]:
    section_id, title = SECTIONS[4]
    evidence = [
        _item(
            LIMITATIONS_BOUNDARY,
            [registry.packet_copy(LIMITATIONS_BOUNDARY, "Limitations-section boundary copy")],
        )
    ]
    for relative in LIMITATION_SOURCE_ARTIFACTS:
        entries = register["auto"].get(relative)
        if not entries:
            raise MemoEvidenceUnavailable(
                f"{REGISTER_REL}: no registered limitations are recorded for {relative}."
            )
        for index, text in enumerate(entries):
            evidence.append(
                _item(
                    text,
                    [
                        registry.json_field(
                            family="registered_limitation",
                            relative=relative,
                            field_path=f"limitations[{index}]",
                            value=text,
                            scope="global",
                            label=f"Registered limitation {index} of {relative}",
                        ),
                        registry.text_span(
                            family="limitations_register",
                            relative=REGISTER_REL,
                            locator=f"### {relative}",
                            quoted_text=text,
                            scope="global",
                            label=f"Merged register entry for {relative}",
                        ),
                    ],
                )
            )
    for concept, seed in register["curated"].items():
        evidence.append(
            _item(
                seed["source_text"],
                [
                    registry.text_span(
                        family="curated_limitation",
                        relative=seed["source_path"],
                        locator=seed["source_locator"],
                        quoted_text=seed["source_text"],
                        scope="global",
                        label=f"Curated limitation source quotation: {concept}",
                    ),
                    registry.text_span(
                        family="limitations_register",
                        relative=REGISTER_REL,
                        locator=f"### {concept}",
                        quoted_text=seed["source_text"],
                        scope="global",
                        label=f"Merged register curated entry: {concept}",
                    ),
                ],
            )
        )
    return _section(section_id, title, evidence)


def _build_provenance_section(
    contract: dict[str, Any], registry: _CitationRegistry
) -> dict[str, Any]:
    section_id, title = SECTIONS[5]
    boundary = contract["limitations"][2]
    state = contract["evidence_state"]
    evidence = [
        _item(
            boundary,
            [
                registry.json_field(
                    family="mcc",
                    relative=CONTRACT_REL,
                    field_path="limitations[2]",
                    value=boundary,
                    scope="policy",
                    label="Model Confidence Contract limitation, verbatim",
                )
            ],
        ),
        _item(
            f"The Model Confidence Contract version recorded for this memo is "
            f"{contract['version']}.",
            [
                registry.json_field(
                    family="mcc",
                    relative=CONTRACT_REL,
                    field_path="version",
                    value=contract["version"],
                    scope="policy",
                    label="Model Confidence Contract version",
                )
            ],
        ),
        _item(
            f"The contract records evidence_state.conclusion=\"{state['conclusion']}\" and "
            "evidence_state.reliable_predictive_edge_observed="
            f"{str(state['reliable_predictive_edge_observed']).lower()}.",
            [
                registry.json_field(
                    family="mcc",
                    relative=CONTRACT_REL,
                    field_path="evidence_state.conclusion",
                    value=state["conclusion"],
                    scope="policy",
                    label="Governed conclusion recorded by the contract",
                ),
                registry.json_field(
                    family="mcc",
                    relative=CONTRACT_REL,
                    field_path="evidence_state.reliable_predictive_edge_observed",
                    value=state["reliable_predictive_edge_observed"],
                    scope="policy",
                    label="Governed evidence state recorded by the contract",
                ),
            ],
        ),
    ]
    return _section(section_id, title, evidence)


# ---------------------------------------------------------------------------
# Limitations register parsing
# ---------------------------------------------------------------------------


def _parse_register(text: str) -> dict[str, Any]:
    """Parse the generated register into auto-extracted and curated entries."""
    auto: dict[str, list[str]] = {}
    curated: dict[str, dict[str, str]] = {}
    part = None
    current: str | None = None
    lines = text.split("\n")
    index = 0
    while index < len(lines):
        line = lines[index]
        if line == "## Auto-extracted limitations":
            part, current = "auto", None
        elif line == "## Curated seed limitations":
            part, current = "curated", None
        elif line.startswith("### "):
            current = line[4:]
            if part == "auto":
                auto.setdefault(current, [])
            elif part == "curated":
                curated[current] = {"concept": current}
        elif part == "auto" and current and line.startswith("- "):
            auto[current].append(line[2:])
        elif part == "curated" and current:
            if line.startswith("Source: `") and line.endswith("`"):
                curated[current]["source_path"] = line[len("Source: `") : -1]
            elif line.startswith("Locator: `") and line.endswith("`"):
                curated[current]["source_locator"] = line[len("Locator: `") : -1]
            elif line == "```text":
                closing = index + 1
                while closing < len(lines) and lines[closing] != "```":
                    closing += 1
                if closing >= len(lines):
                    raise MemoEvidenceUnavailable(
                        f"{REGISTER_REL}: an unterminated quotation block was found."
                    )
                curated[current]["source_text"] = "\n".join(lines[index + 1 : closing])
                index = closing
        index += 1
    for concept, seed in curated.items():
        if not {"source_path", "source_locator", "source_text"} <= set(seed):
            raise MemoEvidenceUnavailable(
                f"{REGISTER_REL}: curated entry {concept!r} is missing its source binding."
            )
    if not auto or not curated:
        raise MemoEvidenceUnavailable(f"{REGISTER_REL}: the register has an unsupported shape.")
    return {"auto": auto, "curated": curated}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def memo_report(
    ticker: str, *, clock: Callable[[], datetime] | None = None
) -> dict[str, Any]:
    """Compose the deterministic evidence memo, or fail closed."""
    ticker = str(ticker).strip().upper()
    if not ticker or not _TICKER.fullmatch(ticker):
        raise ValueError("ticker must contain 1-16 uppercase letters, digits, or dots")

    context_rel = _context_relative(ticker)
    contract = _load_global_artifact(CONTRACT_REL)
    significance = _load_global_artifact(SIGNIFICANCE_REL)
    serving = _load_global_artifact(SERVING_REL)
    passports = _load_global_artifact(PASSPORTS_REL)
    quality = _load_global_artifact(DATA_QUALITY_REL)
    _assert_evidence_state(contract, significance)
    try:
        register = _parse_register(citations.load_text_artifact(REGISTER_REL))
    except CitationError as exc:
        raise MemoEvidenceUnavailable(str(exc)) from exc

    registry = _CitationRegistry()
    generated_at = _utc_timestamp(clock)
    git_sha, git_sha_authority = resolve_git_sha()

    # The four response-level policy sentences are bound to explicit repository
    # authorities first, so none of them is ever a source-free claim.
    try:
        policy_authorities = {
            "headline": [registry.packet_copy(MEMO_HEADLINE, "Frozen memo headline copy")],
            "research_boundary": [
                registry.packet_copy(RESEARCH_BOUNDARY, "Frozen research-boundary copy")
            ],
            "disclaimer": [
                registry.json_field(
                    family="mcc",
                    relative=CONTRACT_REL,
                    field_path="approved_wording.primary_disclaimer",
                    value=PRIMARY_DISCLAIMER,
                    scope="policy",
                    label="Authoritative primary disclaimer recorded by the contract",
                ),
                registry.packet_copy(PRIMARY_DISCLAIMER, "Frozen primary-disclaimer copy"),
            ],
            "closing": [
                registry.packet_copy(CLOSING, "Frozen, non-optional closing line"),
                registry.text_span(
                    family="memo_copy_authority",
                    relative=QUEUE_REL,
                    locator=QUEUE_TASK_LOCATOR,
                    quoted_text=CLOSING,
                    scope="policy",
                    label="Governed closing line mandated by the task record",
                ),
            ],
        }
    except CitationError as exc:
        raise MemoEvidenceUnavailable(
            f"A mandatory policy sentence lost its repository authority: {exc}"
        ) from exc

    sections: list[dict[str, Any]] = []

    # Company-scoped composition may degrade to insufficient_data; global
    # composition may not, and raises MemoEvidenceUnavailable instead.
    try:
        context = citations.load_json_artifact(context_rel)
        if context.get("ticker") != ticker or not isinstance(context.get("year"), int):
            raise CitationError(f"{context_rel}: company context identity is malformed")
        company_year: int | None = context["year"]
        sections.append(
            _build_identity(ticker, context_rel, context, register["curated"], registry)
        )
    except (CitationError, KeyError, TypeError) as exc:
        company_year = None
        sections.append(
            _insufficient_section(
                SECTIONS[0][0],
                SECTIONS[0][1],
                context_rel,
                f"company context evidence is incomplete or malformed ({type(exc).__name__})",
                registry,
            )
        )

    try:
        sections.append(_build_evidence_quality(passports, quality, registry))
    except (CitationError, KeyError, TypeError) as exc:
        raise MemoEvidenceUnavailable(
            f"{PASSPORTS_REL} / {DATA_QUALITY_REL}: evidence-quality sources are incomplete or "
            f"malformed ({type(exc).__name__})."
        ) from exc

    try:
        skeptic_report = skeptic_service.skeptic_report(ticker)
        sections.append(_build_skeptic(skeptic_report, registry))
    except (CitationError, KeyError, TypeError, ValueError, OSError) as exc:
        sections.append(
            _insufficient_section(
                SECTIONS[2][0],
                SECTIONS[2][1],
                SKEPTIC_SERVICE_REL,
                f"Skeptic evidence is unavailable ({type(exc).__name__})",
                registry,
            )
        )

    try:
        sections.append(_build_significance(significance, serving, registry))
    except MemoEvidenceUnavailable:
        raise
    except (CitationError, KeyError, TypeError, IndexError) as exc:
        raise MemoEvidenceUnavailable(
            f"{SIGNIFICANCE_REL} / {SERVING_REL}: significance or serving evidence is incomplete "
            f"or malformed ({type(exc).__name__})."
        ) from exc

    try:
        sections.append(_build_limitations(register, registry))
    except MemoEvidenceUnavailable:
        raise
    except (CitationError, KeyError, TypeError, IndexError) as exc:
        raise MemoEvidenceUnavailable(
            f"{REGISTER_REL}: a registered limitation could not be resolved to its underlying "
            f"source ({type(exc).__name__})."
        ) from exc

    try:
        sections.append(_build_provenance_section(contract, registry))
    except (CitationError, KeyError, TypeError, IndexError) as exc:
        raise MemoEvidenceUnavailable(
            f"{CONTRACT_REL}: contract provenance fields are incomplete or malformed "
            f"({type(exc).__name__})."
        ) from exc

    unavailable = [
        {
            "section_id": section["section_id"],
            "reason": section["missing_evidence"][0]["reason"],
            "source_file": section["missing_evidence"][0]["source_file"],
        }
        for section in sections
        if section["status"] == "insufficient_data"
    ]
    source_artifacts = registry.source_artifacts()
    sections[5]["provenance"] = {
        "git_sha": git_sha,
        "git_sha_authority": git_sha_authority,
        "mcc_version": contract["version"],
        "generated_at_utc": generated_at,
        "schema_version": SCHEMA_VERSION,
        "source_artifacts": source_artifacts,
        "section_inventory": [
            {
                "section_id": section["section_id"],
                "status": section["status"],
                "evidence_count": len(section["evidence"]),
                "citation_ids": sorted(
                    {
                        citation_id
                        for item in section["evidence"]
                        for citation_id in item["citation_ids"]
                    }
                ),
            }
            for section in sections
        ],
        "source_inventory": [
            {
                "path": artifact["path"],
                "citation_count": sum(
                    1
                    for citation in registry.emitted()
                    if citation["source_artifact"] == artifact["path"]
                ),
                "evidence_families": sorted(
                    {
                        citation["evidence_family"]
                        for citation in registry.emitted()
                        if citation["source_artifact"] == artifact["path"]
                    }
                ),
            }
            for artifact in source_artifacts
        ],
    }

    return {
        "task": TASK,
        "schema_version": SCHEMA_VERSION,
        "memo_type": MEMO_TYPE,
        "ticker": ticker,
        "company_year": company_year,
        "headline": MEMO_HEADLINE,
        "research_boundary": RESEARCH_BOUNDARY,
        "disclaimer": PRIMARY_DISCLAIMER,
        "policy_authorities": policy_authorities,
        "evidence_status": "partial" if unavailable else "complete",
        "unavailable_sections": unavailable,
        "sections": sections,
        "citations": registry.emitted(),
        "claim_safety": {
            "statement": CLOSING,
            "investment_value_established": False,
            "reliable_predictive_edge_established": False,
        },
        "closing": CLOSING,
        "mcc": {
            "version": contract["version"],
            "conclusion": contract["evidence_state"]["conclusion"],
        },
    }
