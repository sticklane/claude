"""Ledger CLI: print a monthly report for a ledger file.

Usage: ``python3 cli.py <ledger-file>``

Prints one line per month, ``YYYY-MM: <total>``, in chronological order,
with the total rounded to the cent. Totals are summed exactly and rounded
once, at display time, half-cents rounding up.
"""

import sys
from decimal import ROUND_HALF_UP, Decimal

from report import monthly_totals
from storage import load_ledger

CENT = Decimal("0.01")


def format_report(totals):
    """Render monthly totals as ``YYYY-MM: <total>`` report lines."""
    lines = []
    for month in sorted(totals):
        cents = totals[month].quantize(CENT, rounding=ROUND_HALF_UP)
        lines.append(f"{month}: {cents:.2f}")
    return lines


def main(argv):
    """Load the ledger named in ``argv`` and print its monthly report."""
    if len(argv) != 2:
        print("usage: python3 cli.py <ledger-file>", file=sys.stderr)
        return 2
    entries = load_ledger(argv[1])
    totals = monthly_totals(entries)
    for line in format_report(totals):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
