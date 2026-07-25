"""Behavioral tests for the append-only run-event substrate."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
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


@pytest.fixture
def event_contract_corpus():
    baseline = _record(timestamp_utc="2026-07-25T12:00:00Z")
    detailed = {
        **baseline,
        "event_id": events.uuid7(),
        "timestamp_utc": "2026-07-25T12:00:00.123456Z",
        "artifact_paths": ["evidence/report.json"],
        "finding_fingerprint": "a" * 64,
    }

    def changed(**values):
        return {**baseline, **values}

    accepted = [
        ("baseline", baseline),
        ("detailed", detailed),
    ]
    rejected = [
        ("uppercase UUID", changed(event_id=baseline["event_id"].upper())),
        ("compact UUID", changed(run_id=baseline["run_id"].replace("-", ""))),
        ("wrong UUID version", changed(event_id=str(events.uuid7()).replace("-7", "-4", 1))),
        ("timestamp offset", changed(timestamp_utc="2026-07-25T12:00:00+00:00")),
        ("timestamp without seconds", changed(timestamp_utc="2026-07-25T12:00Z")),
        ("timestamp leap second", changed(timestamp_utc="2026-07-25T12:00:60Z")),
        ("boolean attempt", changed(attempt=True)),
        ("empty artifacts", changed(artifact_paths=[])),
        ("uppercase fingerprint", changed(finding_fingerprint="A" * 64)),
        ("missing field", {key: value for key, value in baseline.items() if key != "reason"}),
        ("extra field", changed(unexpected="value")),
    ]
    return accepted, rejected


def test_runtime_and_json_schema_share_one_contract(event_contract_corpus):
    schema = json.loads(
        (REPO_ROOT / "agentic" / "schema" / "run-event.json").read_text(
            encoding="utf-8"
        )
    )
    schema_validator = jsonschema.Draft202012Validator(schema)
    accepted, rejected = event_contract_corpus

    for label, record in accepted:
        assert events.validate_event(record) == record, label
        assert not list(schema_validator.iter_errors(record)), label

    for label, record in rejected:
        with pytest.raises(events.EventValidationError):
            events.validate_event(record)
        assert list(schema_validator.iter_errors(record)), label


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


def test_reader_ignores_valid_json_final_record_without_terminating_newline(tmp_path):
    repo = _git_repo(tmp_path)
    path = events.monthly_log_path(
        repo, datetime(2026, 7, 25, tzinfo=timezone.utc)
    )
    path.parent.mkdir(parents=True)
    record = _record(timestamp_utc="2026-07-25T12:00:00Z")
    path.write_bytes(json.dumps(record).encode())

    with pytest.warns(events.IncompleteFinalRecordWarning):
        assert events.read_events(cwd=repo, month="2026-07") == []


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


def test_cli_persistence_failure_is_nonfatal_and_does_not_touch_tracker(tmp_path):
    repo = _git_repo(tmp_path)
    tracker_path = repo / ".beads" / "tracker-state.json"
    tracker_path.parent.mkdir()
    tracker_path.write_text('{"status":"in_progress"}\n', encoding="utf-8")
    tracker_before = tracker_path.read_bytes()
    common_dir = events.git_common_dir(repo)
    (common_dir / "agentic").write_text("blocks run-event directory\n", encoding="utf-8")
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
    write_result = json.loads(written.stdout)
    assert write_result == {
        "error": None,
        "event_id": record["event_id"],
        "result": "written",
        "run_unknown": False,
        "written": True,
    }
    read = subprocess.run(
        [sys.executable, "-m", "agentic", "event", "read", "--month", "2026-07"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert read.returncode == 0, read.stderr
    assert json.loads(read.stdout) == [record]
