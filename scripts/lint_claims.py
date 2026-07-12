#!/usr/bin/env python3
"""Enforce FinanceIQ's versioned Model Confidence Contract using stdlib only."""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any


CONTRACT_FILENAME = "model_confidence_contract.json"


def _load_contract(root: Path) -> dict[str, Any]:
    path = root / CONTRACT_FILENAME
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"{CONTRACT_FILENAME}:1: contract file is missing") from None
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{CONTRACT_FILENAME}:{exc.lineno}: invalid JSON: {exc.msg}"
        ) from None

    required = {
        "contract_name",
        "version",
        "versioning_procedure",
        "evidence_basis",
        "evidence_state",
        "approved_wording",
        "rules",
        "scan",
        "required_disclaimer",
        "inference_contract",
        "limitations",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(
            f"{CONTRACT_FILENAME}:1: missing required keys: {', '.join(missing)}"
        )
    return data


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def lint_repository(root: Path) -> list[str]:
    """Return stable file:line diagnostics; an empty list means the contract passes."""
    try:
        contract = _load_contract(root)
    except ValueError as exc:
        return [str(exc)]

    errors: list[str] = []

    for evidence in contract["evidence_basis"]:
        evidence_path = root / evidence["path"]
        if not evidence_path.is_file():
            errors.append(f"{evidence['path']}:1: [MCC-EVIDENCE] cited evidence is missing")

    allowlist: dict[tuple[str, int, str], dict[str, Any]] = {}
    for entry in contract["scan"]["allowlist"]:
        key = (entry["path"], int(entry["line"]), entry["text"])
        allowlist[key] = entry

    matched_allowlist: set[tuple[str, int, str]] = set()
    scan_paths = [
        Path(p)
        for p in glob.glob(str(root / contract["scan"]["frontend_glob"]), recursive=True)
    ]
    scan_paths.extend(root / path for path in contract["scan"]["backend_response_files"])

    compiled_rules: list[tuple[str, re.Pattern[str]]] = []
    for rule in contract["rules"]:
        for pattern in rule["patterns"]:
            compiled_rules.append((rule["id"], re.compile(pattern, re.IGNORECASE)))

    for path in sorted(set(scan_paths)):
        rel = _relative(root, path)
        if not path.is_file():
            errors.append(f"{rel}:1: [MCC-SCAN] configured scan file is missing")
            continue
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw_line.strip()
            matching_rule_ids = {
                rule_id for rule_id, pattern in compiled_rules if pattern.search(line)
            }
            if not matching_rule_ids:
                continue
            key = (rel, line_number, line)
            if key in allowlist:
                matched_allowlist.add(key)
                continue
            for rule_id in sorted(matching_rule_ids):
                errors.append(
                    f"{rel}:{line_number}: [{rule_id}] unsafe or unreviewed claim wording: {line}"
                )

    for key, entry in allowlist.items():
        if key not in matched_allowlist:
            errors.append(
                f"{entry['path']}:{entry['line']}: [MCC-ALLOWLIST] stale allowlist entry; "
                "review its exact line and wording"
            )

    disclaimer = contract["required_disclaimer"]
    fragments = [fragment.casefold() for fragment in disclaimer["required_fragments"]]
    any_fragments = [
        fragment.casefold() for fragment in disclaimer.get("required_any_fragments", [])
    ]
    for rel in disclaimer["pages"]:
        path = root / rel
        if not path.is_file():
            errors.append(f"{rel}:1: [MCC-DISCLAIMER] required data page is missing")
            continue
        text = path.read_text(encoding="utf-8").casefold()
        missing = [fragment for fragment in fragments if fragment not in text]
        if missing:
            errors.append(
                f"{rel}:1: [MCC-DISCLAIMER] missing required disclaimer fragments: "
                f"{', '.join(missing)}"
            )
        if any_fragments and not any(fragment in text for fragment in any_fragments):
            errors.append(
                f"{rel}:1: [MCC-DISCLAIMER] disclaimer must use at least one approved "
                f"claim class marker: {', '.join(any_fragments)}"
            )

    inference = contract["inference_contract"]
    service_path = root / inference["service_file"]
    if service_path.is_file():
        service_text = service_path.read_text(encoding="utf-8")
        required_literals = [
            f'"{inference["response_status_field"]}": "{inference["required_status"]}"',
            '"is_inference":',
            '"realized_return_available":',
        ]
        for literal in required_literals:
            if literal not in service_text:
                errors.append(
                    f"{inference['service_file']}:1: [MCC-INFERENCE] missing response literal {literal!r}"
                )
    else:
        errors.append(
            f"{inference['service_file']}:1: [MCC-INFERENCE] configured service file is missing"
        )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to this script's parent repository)",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors = lint_repository(root)
    if errors:
        for error in errors:
            print(error)
        print(f"Claims lint FAILED: {len(errors)} violation(s).")
        return 1
    print(f"Claims lint PASSED: Model Confidence Contract v{_load_contract(root)['version']} satisfied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
