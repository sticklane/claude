"""Monthly report: total each calendar month's entries."""


def month_of(date):
    """The ``YYYY-MM`` month key for a ``YYYY-MM-DD`` date."""
    return date[:7]


def monthly_totals(entries):
    """Map each month key to the summed amount of its entries."""
    totals = {}
    for entry in entries:
        key = month_of(entry.date)
        totals[key] = totals.get(key, 0.0) + entry.amount
    return totals
