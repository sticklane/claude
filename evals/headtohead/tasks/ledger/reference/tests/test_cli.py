import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(__file__))


def _run(ledger_name):
    return subprocess.run(
        [sys.executable, "cli.py", os.path.join(REPO, "ledgers", ledger_name)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )


def test_cli_reports_clean_sample_totals():
    result = _run("sample.csv")
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["2024-01: 35.75", "2024-02: 10.00"]


def test_cli_repro_report_line_is_well_formed():
    result = _run("repro.csv")
    assert result.returncode == 0
    lines = result.stdout.splitlines()
    assert len(lines) == 1
    assert re.fullmatch(r"2024-02: \d+\.\d{2}", lines[0])
