"""Monthly report: total each calendar month's entries."""

from decimal import Decimal


def month_of(date):
    """The ``YYYY-MM`` month key for a ``YYYY-MM-DD`` date."""
    return date[:7]


def monthly_totals(entries):
    """Map each month key to the exact summed amount of its entries."""
    totals = {}
    for entry in entries:
        key = month_of(entry.date)
        totals[key] = totals.get(key, Decimal("0")) + entry.amount
    return totals
