"""Reproduce a registered FinanceIQ experiment run from its manifest."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATOL = 1e-12


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_versions() -> dict[str, str]:
    return {
        package: importlib.metadata.version(package)
        for package in ("numpy", "pandas", "scikit-learn")
    }


def _check_records(records: list[dict], label: str) -> list[str]:
    errors = []
    for record in records:
        path = ROOT / record["path"]
        if not path.is_file():
            errors.append(f"{label} missing: {record['path']}")
        elif _sha256(path) != record["sha256"]:
            errors.append(f"{label} checksum mismatch: {record['path']}")
    return errors


def _environment_differences(manifest: dict) -> list[str]:
    current = {
        "python": platform.python_version(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "packages": _package_versions(),
    }
    differences = []
    if current["python"] != manifest["python"]["version"]:
        differences.append(
            f"Python {manifest['python']['version']} -> {current['python']}"
        )
    for key, expected in manifest["platform"].items():
        if key in current["platform"] and current["platform"][key] != expected:
            differences.append(
                f"platform.{key} {expected} -> {current['platform'][key]}"
            )
    for package, expected in manifest["packages"].items():
        actual = current["packages"].get(package)
        if actual != expected:
            differences.append(f"{package} {expected} -> {actual}")
    return differences


def _expected_leaderboard(manifest: dict) -> pd.DataFrame:
    payload = manifest["semantic_outputs"]["leaderboard"]
    return pd.DataFrame(payload["data"], columns=payload["columns"], index=payload["index"])


def verify(manifest_path: Path, atol: float) -> int:
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != 1:
        print(f"FAIL: unsupported manifest schema: {manifest.get('schema_version')}")
        return 1

    checksum_errors = [
        *_check_records(manifest["inputs"], "input"),
        *_check_records(manifest["configuration"]["files"], "config"),
    ]
    if checksum_errors:
        for error in checksum_errors:
            print(f"FAIL: {error}")
        return 1

    environment_differences = _environment_differences(manifest)
    if environment_differences:
        print("Environment differs from the registered run:")
        for difference in environment_differences:
            print(f"  - {difference}")
    else:
        print("Environment matches registered Python, platform, and package versions.")

    with tempfile.TemporaryDirectory(prefix="financeiq-repro-") as temp_dir:
        output_root = Path(temp_dir) / "experiments"
        command = [
            sys.executable,
            str(ROOT / "experiments" / "run_experiments.py"),
            "--out",
            str(output_root),
        ]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            print("FAIL: experiment harness exited nonzero")
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            return 1

        mismatched_artifacts = []
        for artifact in manifest["artifacts"]:
            reproduced = output_root / artifact["path"]
            if not reproduced.is_file():
                mismatched_artifacts.append(f"missing {artifact['path']}")
            elif _sha256(reproduced) != artifact["sha256"]:
                mismatched_artifacts.append(f"checksum mismatch {artifact['path']}")

        expected = _expected_leaderboard(manifest)
        actual = pd.read_csv(output_root / "leaderboard.csv")
        try:
            pd.testing.assert_frame_equal(
                actual,
                expected,
                check_dtype=False,
                check_exact=False,
                rtol=0.0,
                atol=atol,
            )
        except AssertionError as exc:
            print(f"FAIL: leaderboard semantic mismatch at atol={atol:g}, rtol=0")
            print(exc)
            return 1

        matched = len(manifest["artifacts"]) - len(mismatched_artifacts)
        print(f"Artifact checksums: {matched}/{len(manifest['artifacts'])} byte-identical.")
        if mismatched_artifacts:
            for mismatch in mismatched_artifacts:
                print(f"  - {mismatch}")
            if not environment_differences:
                print("FAIL: same-environment rerun was not byte-deterministic.")
                return 1
            print("Artifact byte drift accepted only because the numerical environment differs.")

    print(f"PASS: reproduced within tolerance (atol={atol:g}, rtol=0).")
    print("Registration documents provenance; it does not certify methodology.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--atol", type=float, default=DEFAULT_ATOL)
    args = parser.parse_args()
    return verify(args.manifest, args.atol)


if __name__ == "__main__":
    raise SystemExit(main())
