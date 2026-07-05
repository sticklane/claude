"""Tests for spec_readiness.open_questions_unresolved (spec R0 contract).

See specs/list-specs/SPEC.md (R0, R0-note) and
specs/list-specs/tasks/01-spec-readiness.md for the exact contract these
seven cases enforce.
"""

from spec_readiness import open_questions_unresolved


def test_heading_absent_returns_false():
    spec_md = "# Some Spec\n\nNo open questions heading here at all.\n"
    assert open_questions_unresolved(spec_md) is False


def test_heading_present_body_blank_returns_false():
    spec_md = "## Open questions\n\n## Requirements\n\nSome text.\n"
    assert open_questions_unresolved(spec_md) is False


def test_body_exactly_none_returns_false():
    spec_md = "## Open questions\n\n(none)\n\n## Requirements\n"
    assert open_questions_unresolved(spec_md) is False


def test_body_single_line_none_dash_ready_returns_false():
    spec_md = "## Open questions\n\n(none — ready for breakdown)\n\n## Requirements\n"
    assert open_questions_unresolved(spec_md) is False


def test_body_multiline_none_dash_example_returns_false():
    spec_md = (
        "## Open questions\n\n"
        "(none — the four decisions are recorded in Solution; recommended\n"
        "options adopted per the non-interactive fallback, reversible before\n"
        "implementation.)\n\n"
        "## Requirements\n"
    )
    assert open_questions_unresolved(spec_md) is False


def test_body_with_real_unresolved_prose_returns_true():
    spec_md = (
        "## Open questions\n\n"
        "Still deciding whether to support nested specs.\n\n"
        "## Requirements\n"
    )
    assert open_questions_unresolved(spec_md) is True


def test_heading_last_in_file_blank_body_returns_false():
    spec_md = "# Some Spec\n\n## Open questions\n\n"
    assert open_questions_unresolved(spec_md) is False


def test_heading_last_in_file_unresolved_prose_returns_true():
    spec_md = "# Some Spec\n\n## Open questions\n\nStill unresolved: X.\n"
    assert open_questions_unresolved(spec_md) is True
