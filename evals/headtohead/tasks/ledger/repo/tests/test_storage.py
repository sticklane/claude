import pytest

from storage import load_ledger, parse_line


def test_parse_line_splits_date_amount_description():
    entry = parse_line("2024-01-05,10.50,groceries")
    assert entry.date == "2024-01-05"
    assert entry.description == "groceries"
    assert abs(float(entry.amount) - 10.50) < 1e-9


def test_parse_line_rejects_line_missing_fields():
    with pytest.raises(ValueError):
        parse_line("2024-01-05,10.50")


def test_load_ledger_skips_blank_lines(tmp_path):
    ledger = tmp_path / "l.csv"
    ledger.write_text("2024-01-01,1.00,a\n\n2024-01-02,2.00,b\n", encoding="utf-8")
    entries = load_ledger(str(ledger))
    assert [e.date for e in entries] == ["2024-01-01", "2024-01-02"]
