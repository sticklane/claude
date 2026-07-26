"""Behavioral tests for the append-only run-event substrate."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agentic import events  # noqa: E402


def _git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "tracked").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    return repo


def _record(run: events.RunContext | None = None, **changes):
    run = run or events.new_run()
    values = {
        "run": run,
        "producer": "test",
        "runtime": "codex",
        "repo_id": "repo-1",
        "issue_id": "agentic-1",
        "stage": "claim",
    }
    values.update(changes)
    return events.make_event(**values)


def test_uuidv7_run_retry_reopen_and_environment_propagation():
    first = events.new_run()
    assert events.is_uuid7(first.run_id)
    assert first.prior_run_id == events.UNKNOWN
    assert first.attempt == 1
    assert events.run_environment(first) == {"AGENTIC_RUN_ID": first.run_id}

    retry = events.retry_run(first)
    assert retry == events.RunContext(first.run_id, events.UNKNOWN, 2)

    reopened = events.reopen_run(first)
    assert events.is_uuid7(reopened.run_id)
    assert reopened.run_id != first.run_id
    assert reopened.prior_run_id == first.run_id
    assert reopened.attempt == 1


def test_linked_worktrees_resolve_one_common_monthly_log(tmp_path):
    repo = _git_repo(tmp_path)
    linked = tmp_path / "linked"
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", "linked", str(linked)],
        cwd=repo,
        check=True,
    )
    when = datetime(2026, 7, 25, 12, tzinfo=timezone.utc)

    assert events.git_common_dir(repo) == events.git_common_dir(linked)
    assert events.monthly_log_path(repo, when) == events.monthly_log_path(linked, when)

    events.append_event(_record(timestamp_utc="2026-07-25T12:00:00Z"), cwd=repo)
    events.append_event(_record(timestamp_utc="2026-07-25T12:00:01Z"), cwd=linked)
    assert len(events.read_events(cwd=repo, month="2026-07")) == 2


def test_concurrent_cross_process_writers_do_not_interleave(tmp_path):
    repo = _git_repo(tmp_path)
    run = events.new_run()
    script = """
import json, sys
from agentic import events
record = json.loads(sys.argv[2])
events.append_event(record, cwd=sys.argv[1])
"""
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    processes = []
    for index in range(16):
        record = _record(
            run=run,
            stage="worker-verdict",
            reason=f"writer-{index}",
            timestamp_utc=f"2026-07-25T12:00:{index:02d}Z",
        )
        processes.append(
            subprocess.Popen(
                [sys.executable, "-c", script, str(repo), json.dumps(record)],
                env=env,
            )
        )
    assert [process.wait() for process in processes] == [0] * len(processes)
    records = events.read_events(cwd=repo, month="2026-07")
    assert {record["reason"] for record in records} == {
        f"writer-{index}" for index in range(16)
    }


def test_record_size_limit_is_64_kib_including_newline(tmp_path):
    repo = _git_repo(tmp_path)
    record = _record(reason="x" * events.MAX_RECORD_BYTES)
    with pytest.raises(events.EventTooLarge, match="65536"):
        events.append_event(record, cwd=repo)
    assert not events.monthly_log_path(
        repo, datetime(2026, 7, 25, tzinfo=timezone.utc)
    ).exists()


def test_append_uses_one_write_and_fsync_before_unlock(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    calls = []
    real_write = os.write
    real_fsync = os.fsync

    def observed_write(fd, payload):
        calls.append(("write", len(payload)))
        return real_write(fd, payload)

    def observed_fsync(fd):
        calls.append(("fsync", fd))
        return real_fsync(fd)

    monkeypatch.setattr(events.os, "write", observed_write)
    monkeypatch.setattr(events.os, "fsync", observed_fsync)
    events.append_event(_record(timestamp_utc="2026-07-25T12:00:00Z"), cwd=repo)

    assert [name for name, _ in calls] == ["write", "fsync"]


def test_reader_rejects_malformed_interior_record(tmp_path):
    repo = _git_repo(tmp_path)
    path = events.monthly_log_path(
        repo, datetime(2026, 7, 25, tzinfo=timezone.utc)
    )
    path.parent.mkdir(parents=True)
    valid = json.dumps(_record(timestamp_utc="2026-07-25T12:00:00Z"))
    path.write_text(f"{valid}\n{{bad}}\n{valid}\n", encoding="utf-8")

    with pytest.raises(events.MalformedEventLog, match="line 2"):
        events.read_events(cwd=repo, month="2026-07")


def test_reader_ignores_only_an_incomplete_final_record(tmp_path):
    repo = _git_repo(tmp_path)
    path = events.monthly_log_path(
        repo, datetime(2026, 7, 25, tzinfo=timezone.utc)
    )
    path.parent.mkdir(parents=True)
    record = _record(timestamp_utc="2026-07-25T12:00:00Z")
    path.write_bytes(json.dumps(record).encode() + b"\n{\"schema_version\":")

    with pytest.warns(events.IncompleteFinalRecordWarning):
        assert events.read_events(cwd=repo, month="2026-07") == [record]

    path.write_bytes(json.dumps(record).encode() + b"\n{bad}\n")
    with pytest.raises(events.MalformedEventLog, match="line 2"):
        events.read_events(cwd=repo, month="2026-07")


def test_reader_validates_schema_and_explicit_unknowns(tmp_path):
    repo = _git_repo(tmp_path)
    record = _record(timestamp_utc="2026-07-25T12:00:00Z")
    record["session_id"] = None
    path = events.monthly_log_path(
        repo, datetime(2026, 7, 25, tzinfo=timezone.utc)
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(events.MalformedEventLog, match="session_id"):
        events.read_events(cwd=repo, month="2026-07")

    record["session_id"] = events.UNKNOWN
    assert events.validate_event(record) == record


def test_retention_boundary_requires_complete_old_month_and_aggregate():
    now = datetime(2026, 7, 25, 12, tzinfo=timezone.utc)
    cutoff = now - timedelta(days=events.RETENTION_DAYS)
    old_month = events.month_retention("2026-03", now=now, aggregate_written=True)
    boundary_month = events.month_retention(
        cutoff.strftime("%Y-%m"), now=now, aggregate_written=True
    )

    assert old_month.raw_window_ended_before_cutoff
    assert old_month.prunable
    assert not boundary_month.raw_window_ended_before_cutoff
    assert not boundary_month.prunable
    assert not events.month_retention(
        "2026-03", now=now, aggregate_written=False
    ).prunable


def test_event_write_failure_warns_and_marks_only_telemetry_unknown(
    tmp_path, monkeypatch
):
    repo = _git_repo(tmp_path)
    tracker_state = {"status": "in_progress"}

    def fail(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(events, "append_event", fail)
    with pytest.warns(events.EventWriteWarning, match="disk full"):
        result = events.try_append_event(_record(), cwd=repo)

    assert not result.written
    assert result.run_unknown
    assert tracker_state == {"status": "in_progress"}


def test_cli_event_new_run_write_and_read(tmp_path):
    repo = _git_repo(tmp_path)
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    created = subprocess.run(
        [sys.executable, "-m", "agentic", "event", "new-run"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert created.returncode == 0, created.stderr
    run = json.loads(created.stdout)
    record = _record(
        run=events.RunContext(**run),
        timestamp_utc="2026-07-25T12:00:00Z",
    )
    written = subprocess.run(
        [sys.executable, "-m", "agentic", "event", "append"],
        cwd=repo,
        env=env,
        input=json.dumps(record),
        capture_output=True,
        text=True,
    )
    assert written.returncode == 0, written.stderr
    read = subprocess.run(
        [sys.executable, "-m", "agentic", "event", "read", "--month", "2026-07"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert read.returncode == 0, read.stderr
    assert json.loads(read.stdout) == [record]
