"""Golden tests for viz.py — the shared status/timeline/DAG renderer.

Covers SPEC.md requirements R2-R4 (R1's stdlib-only/compile audit runs as a
standalone shell acceptance command, not pytest).
"""

import re

import pytest

import viz


# ---------------------------------------------------------------------------
# canonical_status / STATUS_HEX (R4)
# ---------------------------------------------------------------------------

ALIAS_TABLE = {
    "running": ["running", "in-progress", "in_progress", "claimed", "active"],
    "open": ["open", "pending", "todo", "ready", "queued"],
    "done": ["done", "completed", "closed", "deferred", "skipped"],
    "failed": ["failed", "error"],
    "stale": ["recent", "stale", "idle"],
    "blocked": ["blocked"],
}


def test_canonical_status_maps_every_alias_to_its_token():
    for token, aliases in ALIAS_TABLE.items():
        for alias in aliases:
            assert viz.canonical_status(alias) == token
            assert viz.canonical_status(alias.upper()) == token


def test_canonical_status_unknown_term_maps_to_open():
    assert viz.canonical_status("something-nobody-uses") == "open"
    assert viz.canonical_status("") == "open"
    assert viz.canonical_status(None) == "open"


def test_status_hex_covers_all_six_canonical_tokens():
    assert set(viz.STATUS_HEX) == {"running", "open", "done", "failed", "stale", "blocked"}
    for hexval in viz.STATUS_HEX.values():
        assert re.fullmatch(r"#[0-9a-f]{6}", hexval)


# ---------------------------------------------------------------------------
# dag() (R2)
# ---------------------------------------------------------------------------

def test_dag_renders_one_g_per_task_and_one_path_per_edge():
    tasks = [
        {"num": 1, "deps": [], "status": "done", "title": "root"},
        {"num": 2, "deps": [1], "status": "running", "title": "middle"},
        {"num": 3, "deps": [2], "status": "open", "title": "leaf"},
    ]
    svg = viz.dag(tasks)
    assert svg.count("<g") == 3
    assert svg.count("<path") == 2


def test_dag_returns_empty_string_when_no_edges():
    tasks = [
        {"num": 1, "deps": [], "status": "open", "title": "a"},
        {"num": 2, "deps": [], "status": "open", "title": "b"},
    ]
    assert viz.dag(tasks) == ""


def test_dag_empty_task_list_returns_empty_string():
    assert viz.dag([]) == ""


def test_dag_cyclic_deps_terminates_instead_of_infinite_looping():
    tasks = [
        {"num": 1, "deps": [2], "status": "open", "title": "a"},
        {"num": 2, "deps": [1], "status": "open", "title": "b"},
    ]
    # A cyclic deps graph still has in-list edges, so this must terminate
    # (cycle-guarded layering) rather than recurse forever.
    svg = viz.dag(tasks)
    assert svg.count("<g") == 2
    assert svg.count("<path") == 2


def test_dag_node_stroke_and_num_text_use_status_hex():
    tasks = [
        {"num": 1, "deps": [], "status": "running", "title": "a"},
        {"num": 2, "deps": [1], "status": "blocked", "title": "b"},
    ]
    svg = viz.dag(tasks)
    assert f'stroke="{viz.STATUS_HEX["running"]}"' in svg
    assert f'fill="{viz.STATUS_HEX["blocked"]}"' in svg


# ---------------------------------------------------------------------------
# timeline() (R3)
# ---------------------------------------------------------------------------

def test_timeline_orders_rows_by_start_ts_and_normalizes_left_width(monkeypatch):
    monkeypatch.setattr(viz.time, "time", lambda: 1000.0)
    rows = [
        {"label": "second", "status": "open", "start_ts": 500.0, "end_ts": 750.0,
         "tooltip": "t2", "href": None},
        {"label": "first", "status": "running", "start_ts": 0.0, "end_ts": 500.0,
         "tooltip": "t1", "href": None},
    ]
    html_out = viz.timeline(rows)

    assert html_out.count('class="viz-lane"') == 2
    assert html_out.count('viz-bar') == 2
    # ordered by start_ts: "first" (start 0) must appear before "second" (start 500)
    assert html_out.index(">first<") < html_out.index(">second<")

    # span = [min(start_ts)=0, now=1000] -> span 1000
    # "first": left=(0-0)/1000*100=0%, width=(500-0)/1000*100=50%
    assert "left:0.000%" in html_out
    assert "width:50.000%" in html_out
    # "second": left=(500-0)/1000*100=50%, width=(750-500)/1000*100=25%
    assert "left:50.000%" in html_out
    assert "width:25.000%" in html_out


def test_timeline_floors_narrow_bars_at_quarter_percent(monkeypatch):
    monkeypatch.setattr(viz.time, "time", lambda: 1000.0)
    rows = [
        {"label": "tiny", "status": "open", "start_ts": 0.0, "end_ts": 1.0,
         "tooltip": "", "href": None},
    ]
    html_out = viz.timeline(rows)
    # raw width would be (1-0)/1000*100 = 0.1%, floored up to 0.75%
    assert "width:0.750%" in html_out


def test_timeline_empty_rows_returns_fixed_empty_state():
    first = viz.timeline([])
    second = viz.timeline([])
    assert first == second
    assert "viz-empty" in first


def test_timeline_row_missing_start_ts_raises_value_error():
    rows = [{"label": "x", "status": "open", "end_ts": 100.0, "tooltip": "", "href": None}]
    with pytest.raises(ValueError):
        viz.timeline(rows)


def test_timeline_bar_class_has_css_var_fallback_for_its_status(monkeypatch):
    monkeypatch.setattr(viz.time, "time", lambda: 1000.0)
    rows = [
        {"label": "a", "status": "running", "start_ts": 0.0, "end_ts": 500.0,
         "tooltip": "t", "href": None},
    ]
    html_out = viz.timeline(rows)
    assert "viz-bar viz-running" in html_out
    # the fallback color lives in VIZ_CSS (bars are colored with zero host vars)
    assert f'var(--viz-running, {viz.STATUS_HEX["running"]})' in viz.VIZ_CSS


def test_viz_css_defines_fallback_for_every_canonical_token():
    for token, hexval in viz.STATUS_HEX.items():
        assert f"var(--viz-{token}, {hexval})" in viz.VIZ_CSS
    assert ":root" not in viz.VIZ_CSS
