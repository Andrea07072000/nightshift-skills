"""Skill honest-numbers: affermazioni non sostenute trovate, affermazioni oneste lasciate stare."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "honest-numbers" / "scripts" / "check_report.py"
spec = importlib.util.spec_from_file_location("check_report", SCRIPT)
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)


def rules(text):
    return [(f["rule"], f["text"].lower()) for f in cr.check(text)]


@pytest.mark.parametrize("line,rule", [
    ("The migration is 85% complete.", "PCT_NO_BASE"),
    ("It is fully tested.", "STATUS_NO_EVID"),
    ("The cache makes the API much faster.", "VAGUE_GAIN"),
    ("All tests pass.", "STATUS_NO_EVID"),
    ("Zero bugs this week.", "ABSOLUTE"),
    ("The release is production-ready.", "STATUS_NO_EVID"),
    ("It never fails.", "ABSOLUTE"),
])
def test_unbacked_claims_are_found(line, rule):
    assert rule in [r for r, _ in rules(line)]


@pytest.mark.parametrize("line", [
    "Coverage went from 61% to 74% (412/557 lines, `pytest --cov`, commit 3f2a9c1).",
    "17 of 20 checklist items done (85%).",
    "Accuracy 72.7% on the holdout (n=22).",
    "| Daily | 18 | 32 | 56 % |",                                 # tabella: il denominatore e' nelle colonne
    "| Gate | VERIFIED |",                                         # etichetta di stato, non un'affermazione
    "Target: error rate below 5%.",                               # obiettivo dichiarato
    "All tests pass: `pytest -q` 142 passed, 0 failed.",
    "p50 latency 420 ms -> 95 ms, much faster on the same benchmark.",
])
def test_backed_or_declared_lines_are_left_alone(line):
    assert rules(line) == []


def test_code_blocks_are_ignored():
    text = "\n".join(["Example of a bad report:", "```", "It is 100% done and fully tested.", "```"])
    assert rules(text) == []


def test_neighbouring_lines_do_not_vouch_for_a_claim():
    """Una riga con prove non rende credibile quella accanto (difetto della prima versione)."""
    text = "\n".join(["Coverage 412/557 lines (`pytest --cov`).", "All tests pass."])
    assert ("STATUS_NO_EVID", "all tests pass") in rules(text)


def test_cli_exit_codes(tmp_path):
    bad, good = tmp_path / "bad.md", tmp_path / "good.md"
    bad.write_text("We are 90% done.\n", encoding="utf-8")
    good.write_text("18 of 20 done (90%).\n", encoding="utf-8")
    run = lambda p: subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)  # noqa: E731
    assert run(bad).returncode == 1 and run(good).returncode == 0
    assert subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / "missing.md")]).returncode == 2


@pytest.mark.parametrize("line", [
    "Dashboards are now 10x faster.",
    "It is much more reliable now that we have 3 servers.",           # un numero qualunque non e' una misura
    "Churn dropped significantly.",
])
def test_v11_multipliers_and_trends_need_a_measurement(line):
    """v1.1, dall'eval: la v1.0 mancava '10x faster', 'much more reliable' accanto a un numero, 'dropped significantly'."""
    assert "VAGUE_GAIN" in [r for r, _ in rules(line)]


def test_v11_measured_multiplier_is_fine():
    assert rules("Dashboards are now 10x faster (p50 2,000 ms -> 200 ms on 500 requests).") == []
