"""Tests for the "Cost (7d)" workboard panel + `POST /api/cost/refresh`
(spec workboard-weekly-cost-view, task 03; requirements R5/R6/R7).

The summary JSON shape is the value contract pinned in SPEC.md R3:
`{by_project, by_skill, by_agent_type, by_model}` each `{name: {sample_type:
total}}`, a `totals` object, and a top-level `sessions_added` int. Cost is
`totals.cost_microusd`, formatted as a dollar string by plain division.

`render_workboard` stays a pure function of a board dict + a summary dict (or
None); the `/workboard` HTTP handler owns the file read. The refresh endpoint's
subprocess boundary is mocked here — real-binary integration is task 04's job.
"""

import importlib.util
import io
import json
import types
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch

_spec = importlib.util.spec_from_file_location(
    "ac", str(Path(__file__).resolve().parent.parent / "agent-console.py")
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


def _headers(mapping):
    msg = Message()
    for k, v in mapping.items():
        msg[k] = v
    return msg


def _get(path, host="127.0.0.1:8899"):
    h = ac.Handler.__new__(ac.Handler)
    h.path = path
    h.headers = _headers({"Host": host})
    cap = {}

    def _send(body, ctype="text/html; charset=utf-8", code=200):
        cap.update(body=body, ctype=ctype, code=code)

    h._send = _send
    return h, cap


def _post(path, headers, body=b"{}"):
    h = ac.Handler.__new__(ac.Handler)
    h.path = path
    hdrs = dict(headers)
    hdrs.setdefault("Content-Length", str(len(body)))
    h.headers = _headers(hdrs)
    h.rfile = io.BytesIO(body)
    cap = {}

    def _send(b, ctype="text/html; charset=utf-8", code=200):
        cap.update(body=b, ctype=ctype, code=code)

    h._send = _send
    return h, cap


def _board():
    """A minimal, valid board dict via the real adapter (no live scan)."""
    assembled = {
        "repos": [],
        "orphan_sessions": [],
        "inbox": [],
        "liveness_unknown": False,
    }
    return ac._adapt_board(assembled, [], [])


_SUMMARY = {
    "by_project": {
        "alpha": {"cost_microusd": 3_000_000, "input_tokens": 100},
        "beta": {"cost_microusd": 1_000_000},
    },
    "by_skill": {
        "skill:build": {"cost_microusd": 2_500_000},
        "(no skill)": {"cost_microusd": 500_000},
    },
    "by_agent_type": {"agent:worker": {"cost_microusd": 4_000_000}},
    "by_model": {
        "opus-model": {"cost_microusd": 3_500_000},
        "sonnet-model": {"cost_microusd": 500_000},
    },
    "totals": {"cost_microusd": 4_000_000, "input_tokens": 100},
    "sessions_added": 2,
}


class RenderCostPanel(unittest.TestCase):
    def test_renders_dollar_total_and_dimension_rows(self):
        html = ac.render_workboard(_board(), _SUMMARY)
        self.assertIn("Cost (7d)", html)  # R6 panel title
        self.assertIn("$4.00", html)  # 4_000_000 microusd -> $4.00
        # top rows from each dimension are present
        self.assertIn("opus-model", html)
        self.assertIn("skill:build", html)
        self.assertIn("alpha", html)

    def test_dimension_rows_capped_at_top_five_by_cost(self):
        by_model = {
            f"zzmodel{i}": {"cost_microusd": (7 - i) * 1_000_000} for i in range(7)
        }
        summary = dict(_SUMMARY, by_model=by_model)
        html = ac.render_workboard(_board(), summary)
        # top 5 by cost = zzmodel0..zzmodel4; the two cheapest are dropped
        self.assertIn("zzmodel0", html)
        self.assertIn("zzmodel4", html)
        self.assertNotIn("zzmodel5", html)
        self.assertNotIn("zzmodel6", html)

    def test_missing_summary_renders_pending_state_not_error(self):
        html = ac.render_workboard(_board(), None)  # no exception
        self.assertIn("Cost (7d)", html)
        self.assertIn("pending", html.lower())  # R7 explicit empty state


_REPRIME = {
    "count": 3,
    "cache_write_tokens": 210_000,
    "cost_microusd": 2_540_000,
    "by_project": {
        "alpha": {
            "count": 3,
            "cache_write_tokens": 210_000,
            "cost_microusd": 2_540_000,
        }
    },
}


class RenderReprimeLine(unittest.TestCase):
    def test_reprime_line_rendered_when_section_present(self):
        summary = dict(_SUMMARY, reprime=_REPRIME)
        html = ac.render_workboard(_board(), summary)
        self.assertIn("3 re-prime", html.lower())  # count + label
        self.assertIn("$2.54", html)  # 2_540_000 microusd -> $2.54

    def test_reprime_line_absent_when_section_missing(self):
        # older cache: summary has no `reprime` key -> panel renders as today
        html = ac.render_workboard(_board(), _SUMMARY)
        self.assertNotIn("re-prime", html.lower())
        self.assertIn("Cost (7d)", html)  # rest of panel unaffected

    def test_reprime_section_none_is_omitted_gracefully(self):
        summary = dict(_SUMMARY, reprime=None)
        html = ac.render_workboard(_board(), summary)  # no exception
        self.assertNotIn("re-prime", html.lower())


class WorkboardHandlerReadsSummary(unittest.TestCase):
    def test_missing_summary_page_load_is_200_pending(self):
        with (
            patch.object(ac, "get_board", return_value=_board()),
            patch.object(ac, "_read_cost_summary", return_value=None),
        ):
            h, cap = _get("/workboard")
            h.do_GET()
        self.assertEqual(cap["code"], 200)  # R7 never 500
        self.assertIn("pending", cap["body"].decode("utf-8").lower())

    def test_present_summary_is_rendered_into_page(self):
        with (
            patch.object(ac, "get_board", return_value=_board()),
            patch.object(ac, "_read_cost_summary", return_value=_SUMMARY),
        ):
            h, cap = _get("/workboard")
            h.do_GET()
        self.assertEqual(cap["code"], 200)
        body = cap["body"].decode("utf-8")
        self.assertIn("Cost (7d)", body)
        self.assertIn("$4.00", body)


class CostRefreshEndpoint(unittest.TestCase):
    def test_rejected_without_csrf_token(self):
        h, cap = _post("/api/cost/refresh", {"Host": "127.0.0.1:8899"})
        h.do_POST()
        self.assertEqual(cap["code"], 403)  # R5 CSRF-protected

    def test_csrf_post_returns_sessions_added_from_written_summary(
        self,
    ):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "weekly-7d-summary.json"

            def fake_run(*a, **k):  # the mocked refresh "writes" the summary
                summary_path.write_text(json.dumps(dict(_SUMMARY, sessions_added=4)))
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")

            with (
                patch.object(ac, "_cost_summary_path", return_value=summary_path),
                patch.object(ac.subprocess, "run", side_effect=fake_run),
            ):
                h, cap = _post(
                    "/api/cost/refresh",
                    {"Host": "127.0.0.1:8899", "X-CSRF": ac.CSRF_TOKEN},
                )
                h.do_POST()
        self.assertEqual(cap["code"], 200)
        payload = json.loads(cap["body"])
        self.assertIs(payload["ok"], True)
        self.assertEqual(payload["sessions_added"], 4)  # read from summary, R5

    def test_refresh_failure_reports_not_ok(self):
        def fail_run(*a, **k):
            return types.SimpleNamespace(returncode=1, stdout="", stderr="boom")

        with patch.object(ac.subprocess, "run", side_effect=fail_run):
            h, cap = _post(
                "/api/cost/refresh",
                {"Host": "127.0.0.1:8899", "X-CSRF": ac.CSRF_TOKEN},
            )
            h.do_POST()
        self.assertEqual(cap["code"], 400)
        self.assertIs(json.loads(cap["body"])["ok"], False)


if __name__ == "__main__":
    unittest.main()
