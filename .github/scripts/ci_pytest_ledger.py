"""Pytest plugin: record what pytest itself collected, deselected and reported.

JUnit XML cannot carry this. pytest writes a non-strict XPASS as a plain pass
and never records a deselection, so a gate that reads JUnit alone accepts both.
Loaded with `-p ci_pytest_ledger` (this directory on PYTHONPATH) and
CI_TEST_GATE_LEDGER naming the output file; ci_test_gate.py cross-checks the
ledger against the JUnit report. Passive: it changes no collection or outcome.
See docs/CI_TEST_GATES.md.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

ENV = "CI_TEST_GATE_LEDGER"
SCHEMA = "financeiq-ci-pytest-ledger/1"


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.collected: list[str] = []
        self.deselected: list[str] = []
        self.selected: list[str] | None = None
        self.collection_errors = 0
        self.phases: dict[str, dict[str, tuple[str, bool]]] = {}

    # Every item as it is collected, before any plugin, conftest or option
    # filters the list. Anything removed later must show up as deselected.
    def pytest_itemcollected(self, item: pytest.Item) -> None:
        self.collected.append(item.nodeid)

    def pytest_deselected(self, items) -> None:
        self.deselected.extend(item.nodeid for item in items)

    def pytest_collectreport(self, report) -> None:
        if report.failed:
            self.collection_errors += 1

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session: pytest.Session) -> None:
        self.selected = [item.nodeid for item in session.items]

    def pytest_runtest_logreport(self, report) -> None:
        self.phases.setdefault(report.nodeid, {})[report.when] = (report.outcome, hasattr(report, "wasxfail"))

    @staticmethod
    def outcome(phases: dict[str, tuple[str, bool]]) -> str:
        setup, call, teardown = (phases.get(when) for when in ("setup", "call", "teardown"))
        if any(phase and phase[0] == "failed" for phase in (setup, teardown)):
            return "error"
        if call and call[0] == "failed":
            return "failed"  # includes a strict XPASS
        for phase in (setup, call):
            if phase and phase[0] == "skipped":
                return "xfailed" if phase[1] else "skipped"
        if call and call[0] == "passed":
            return "xpassed" if call[1] else "passed"
        return "incomplete"

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: pytest.Session, exitstatus) -> None:
        document = {
            "schema": SCHEMA,
            "pytest_version": pytest.__version__,
            "exitstatus": int(exitstatus),
            "collection_errors": self.collection_errors,
            "collected": self.collected,
            "deselected": self.deselected,
            "selected": self.selected if self.selected is not None else [],
            "outcomes": {node_id: self.outcome(phases) for node_id, phases in self.phases.items()},
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        partial = self.path.with_name(self.path.name + ".partial")
        partial.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")
        partial.replace(self.path)


def pytest_configure(config: pytest.Config) -> None:
    target = os.environ.get(ENV)
    if not target:
        raise pytest.UsageError(f"ci_pytest_ledger is loaded but {ENV} does not name an output file")
    config.pluginmanager.register(Ledger(Path(target)), "ci_pytest_ledger_recorder")
