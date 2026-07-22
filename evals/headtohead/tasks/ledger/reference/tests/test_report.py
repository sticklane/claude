from report import month_of, monthly_totals
from storage import parse_line


def _entries(rows):
    return [parse_line(row) for row in rows]


def test_month_of_extracts_year_month():
    assert month_of("2024-07-15") == "2024-07"


def test_monthly_totals_groups_entries_by_month():
    totals = monthly_totals(
        _entries(
            [
                "2024-01-03,10.00,rent",
                "2024-01-17,20.50,groceries",
                "2024-02-04,10.00,rent",
            ]
        )
    )
    assert set(totals) == {"2024-01", "2024-02"}


def test_monthly_totals_sums_a_month_of_clean_amounts():
    totals = monthly_totals(
        _entries(
            [
                "2024-01-03,10.00,rent",
                "2024-01-17,20.50,groceries",
                "2024-01-28,5.25,bus",
            ]
        )
    )
    assert abs(float(totals["2024-01"]) - 35.75) < 1e-9
