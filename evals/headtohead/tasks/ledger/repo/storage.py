"""Ledger storage: parse ledger CSV files into entries.

An entry is a (date, amount, description) triple. A ledger file has one
entry per line in ``YYYY-MM-DD,amount,description`` form; blank lines are
skipped. Amounts may carry sub-cent precision (unit prices, split shares),
so they are read here and kept as numbers for the report to total.
"""

from dataclasses import dataclass


@dataclass
class Entry:
    """One ledger entry."""

    date: str  # "YYYY-MM-DD"
    amount: float  # currency amount
    description: str


def parse_line(line):
    """Parse one ledger line into an :class:`Entry`."""
    parts = line.rstrip("\n").split(",", 2)
    if len(parts) != 3:
        raise ValueError(f"malformed ledger line: {line!r}")
    date, amount, description = parts
    return Entry(
        date=date.strip(),
        amount=float(amount),
        description=description.strip(),
    )


def load_ledger(path):
    """Load a ledger file into a list of :class:`Entry`, skipping blanks."""
    entries = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            entries.append(parse_line(line))
    return entries
