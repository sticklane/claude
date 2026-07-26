"""Correction coverage for the append-only run-event substrate."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agentic import events  # noqa: E402


def _git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "tracked").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    return repo


def _record(run: events.RunContext | None = None, **changes):
    run = run or events.new_run()
    values = {
        "run": run,
        "producer": "test-corrections",
        "runtime": "codex",
        "repo_id": "repo-1",
        "issue_id": "agentic-1",
        "stage": "claim",
    }
    values.update(changes)
    return events.make_event(**values)


def test_portable_schema_and_runtime_reject_invalid_calendar_corpus():
    schema = json.loads(
        (REPO_ROOT / "agentic" / "schema" / "run-event.json").read_text(
            encoding="utf-8"
        )
    )
    validator = jsonschema.Draft202012Validator(schema)
    baseline = _record(timestamp_utc="2026-07-25T12:00:00Z")
    accepted = (
        "2024-02-29T12:00:00Z",
        "2026-04-30T12:00:00.123456Z",
    )
    rejected = (
        "0000-01-01T12:00:00Z",
        "2025-02-29T12:00:00Z",
        "2024-02-30T12:00:00Z",
        "2026-04-31T12:00:00Z",
        "2026-13-01T12:00:00Z",
        "2026-01-32T12:00:00Z",
    )

    for timestamp in accepted:
        record = {**baseline, "timestamp_utc": timestamp}
        assert events.validate_event(record) == record
        assert not list(validator.iter_errors(record))

    for timestamp in rejected:
        record = {**baseline, "timestamp_utc": timestamp}
        with pytest.raises(events.EventValidationError):
            events.validate_event(record)
        assert list(validator.iter_errors(record)), timestamp


def test_append_recovers_short_unterminated_tail_before_next_record(
    tmp_path, monkeypatch
):
    repo = _git_repo(tmp_path)
    first = _record(
        timestamp_utc="2026-07-25T12:00:00Z",
        reason="complete-before-short-write",
    )
    interrupted = _record(
        timestamp_utc="2026-07-25T12:00:01Z",
        reason="interrupted",
    )
    recovered = _record(
        timestamp_utc="2026-07-25T12:00:02Z",
        reason="after-recovery",
    )
    events.append_event(first, cwd=repo)
    real_write = os.write

    def short_write(fd, payload):
        return real_write(fd, payload[:31])

    monkeypatch.setattr(events.os, "write", short_write)
    with pytest.raises(OSError, match="short append"):
        events.append_event(interrupted, cwd=repo)
    monkeypatch.setattr(events.os, "write", real_write)

    events.append_event(recovered, cwd=repo)

    records = events.read_events(cwd=repo, month="2026-07")
    assert [record["reason"] for record in records] == [
        "complete-before-short-write",
        "after-recovery",
    ]


def test_reader_ignores_valid_json_final_record_without_terminating_newline(tmp_path):
    repo = _git_repo(tmp_path)
    path = events.monthly_log_path(
        repo,
        datetime(2026, 7, 25, 12, tzinfo=timezone.utc),
    )
    path.parent.mkdir(parents=True)
    record = _record(timestamp_utc="2026-07-25T12:00:00Z")
    path.write_bytes(json.dumps(record).encode())

    with pytest.warns(events.IncompleteFinalRecordWarning):
        assert events.read_events(cwd=repo, month="2026-07") == []


def test_cli_persistence_failure_is_nonfatal_and_does_not_touch_tracker(tmp_path):
    repo = _git_repo(tmp_path)
    tracker_path = repo / ".beads" / "tracker-state.json"
    tracker_path.parent.mkdir()
    tracker_path.write_text('{"status":"in_progress"}\n', encoding="utf-8")
    tracker_before = tracker_path.read_bytes()
    common_dir = events.git_common_dir(repo)
    (common_dir / "agentic").write_text(
        "blocks run-event directory\n", encoding="utf-8"
    )
    record = _record(timestamp_utc="2026-07-25T12:00:00Z")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}

    appended = subprocess.run(
        [sys.executable, "-m", "agentic", "event", "append"],
        cwd=repo,
        env=env,
        input=json.dumps(record),
        capture_output=True,
        text=True,
    )

    assert appended.returncode == 0, appended.stderr
    result = json.loads(appended.stdout)
    assert result["event_id"] == record["event_id"]
    assert not result["written"]
    assert result["run_unknown"]
    assert result["result"] == "unknown"
    assert result["error"]
    assert "run telemetry is unknown" in appended.stderr
    assert tracker_path.read_bytes() == tracker_before


def test_cli_append_reports_written_result(tmp_path):
    repo = _git_repo(tmp_path)
    record = _record(timestamp_utc="2026-07-25T12:00:00Z")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}

    appended = subprocess.run(
        [sys.executable, "-m", "agentic", "event", "append"],
        cwd=repo,
        env=env,
        input=json.dumps(record),
        capture_output=True,
        text=True,
    )

    assert appended.returncode == 0, appended.stderr
    assert json.loads(appended.stdout) == {
        "error": None,
        "event_id": record["event_id"],
        "result": "written",
        "run_unknown": False,
        "written": True,
    }
