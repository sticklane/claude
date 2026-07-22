"""Regression coverage for the float-drift bug.

These sub-cent ledgers land on half-cent monthly totals, which the old
float pipeline rounded the wrong way. They pin the exact-to-the-cent
behavior the Decimal fix guarantees.
"""

import os
import subprocess
import sys

REF = os.path.dirname(os.path.dirname(__file__))


def _run(ledger_path):
    return subprocess.run(
        [sys.executable, "cli.py", ledger_path],
        cwd=REF,
        capture_output=True,
        text=True,
    )


def test_repro_ledger_total_is_exact_to_the_cent():
    result = _run(os.path.join(REF, "ledgers", "repro.csv"))
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["2024-02: 6.35"]


def test_subcent_shares_round_half_cent_up(tmp_path):
    ledger = tmp_path / "shares.csv"
    ledger.write_text(
        "2024-01-05,0.015,share\n2024-01-11,0.015,share\n2024-01-19,0.015,share\n",
        encoding="utf-8",
    )
    result = _run(str(ledger))
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["2024-01: 0.05"]
