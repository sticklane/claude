"""Append-only run events shared by every worktree of a repository.

This module owns record construction, validation, and durable append/read
operations. It deliberately has no tracker or orchestration dependencies.
"""

from __future__ import annotations

import argparse
import dataclasses
import fcntl
import functools
import json
import os
import secrets
import subprocess
import sys
import uuid
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

import jsonschema

SCHEMA_VERSION = 1
UNKNOWN = "unknown"
MAX_RECORD_BYTES = 64 * 1024
RETENTION_DAYS = 90
SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "run-event.json"
EVENT_FIELDS = (
    "schema_version",
    "event_id",
    "run_id",
    "prior_run_id",
    "timestamp_utc",
    "producer",
    "runtime",
    "repo_id",
    "issue_id",
    "attempt",
    "stage",
    "parent_event_id",
    "session_id",
    "base_commit",
    "result_commit",
    "artifact_paths",
    "finding_fingerprint",
    "disposition",
    "reason",
)


class EventError(ValueError):
    """Base class for run-event failures."""


class EventValidationError(EventError):
    """A record does not conform to the run-event schema."""


class EventTooLarge(EventError):
    """A serialized record exceeds the atomic append limit."""


class MalformedEventLog(EventError):
    """A complete record in an event log is malformed."""


class IncompleteFinalRecordWarning(UserWarning):
    """The reader ignored a final record interrupted during an external write."""


class EventWriteWarning(UserWarning):
    """Telemetry could not be persisted and this run is therefore unknown."""


@dataclass(frozen=True)
class RunContext:
    run_id: str
    prior_run_id: str = UNKNOWN
    attempt: int = 1

    def __post_init__(self) -> None:
        if not is_uuid7(self.run_id):
            raise EventValidationError("run_id must be UUIDv7")
        if self.prior_run_id != UNKNOWN and not is_uuid7(self.prior_run_id):
            raise EventValidationError("prior_run_id must be UUIDv7 or 'unknown'")
        if isinstance(self.attempt, bool) or not isinstance(self.attempt, int):
            raise EventValidationError("attempt must be an integer")
        if self.attempt < 1:
            raise EventValidationError("attempt must be at least 1")


@dataclass(frozen=True)
class EventWriteResult:
    written: bool
    run_unknown: bool
    error: str | None = None


@dataclass(frozen=True)
class MonthRetention:
    month: str
    cutoff_utc: datetime
    raw_window_ended_before_cutoff: bool
    aggregate_written: bool
    prunable: bool


def uuid7(now: datetime | None = None) -> str:
    """Return an RFC 9562 UUIDv7 without requiring a bleeding-edge Python."""
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("UUIDv7 time must be timezone-aware")
    milliseconds = int(instant.timestamp() * 1000)
    if not 0 <= milliseconds < (1 << 48):
        raise ValueError("UUIDv7 timestamp is outside its 48-bit range")
    value = milliseconds << 80
    value |= 0x7 << 76
    value |= secrets.randbits(12) << 64
    value |= 0b10 << 62
    value |= secrets.randbits(62)
    return str(uuid.UUID(int=value))


def is_uuid7(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = uuid.UUID(value)
    except ValueError:
        return False
    return (
        str(parsed) == value and parsed.version == 7 and parsed.variant == uuid.RFC_4122
    )


def new_run(prior_run_id: str = UNKNOWN) -> RunContext:
    if prior_run_id != UNKNOWN and not is_uuid7(prior_run_id):
        raise EventValidationError("prior_run_id must be UUIDv7 or 'unknown'")
    return RunContext(run_id=uuid7(), prior_run_id=prior_run_id, attempt=1)


def retry_run(run: RunContext) -> RunContext:
    if not isinstance(run, RunContext):
        raise TypeError("retry_run requires a RunContext")
    return dataclasses.replace(run, attempt=run.attempt + 1)


def reopen_run(prior: RunContext | str) -> RunContext:
    prior_run_id = prior.run_id if isinstance(prior, RunContext) else prior
    return new_run(prior_run_id=prior_run_id)


def run_environment(run: RunContext) -> dict[str, str]:
    """Return the opt-in environment propagation payload for an orchestrator."""
    return {"AGENTIC_RUN_ID": run.run_id}


def _utc_timestamp(instant: datetime | None = None) -> str:
    value = (instant or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def make_event(
    *,
    run: RunContext,
    producer: str,
    runtime: str,
    repo_id: str,
    issue_id: str,
    stage: str,
    event_id: str | None = None,
    timestamp_utc: str | None = None,
    parent_event_id: str = UNKNOWN,
    session_id: str = UNKNOWN,
    base_commit: str = UNKNOWN,
    result_commit: str = UNKNOWN,
    artifact_paths: list[str] | str = UNKNOWN,
    finding_fingerprint: str = UNKNOWN,
    disposition: str = UNKNOWN,
    reason: str = UNKNOWN,
) -> dict[str, Any]:
    record = {
        "schema_version": SCHEMA_VERSION,
        "event_id": event_id or uuid7(),
        "run_id": run.run_id,
        "prior_run_id": run.prior_run_id,
        "timestamp_utc": timestamp_utc or _utc_timestamp(),
        "producer": producer,
        "runtime": runtime,
        "repo_id": repo_id,
        "issue_id": issue_id,
        "attempt": run.attempt,
        "stage": stage,
        "parent_event_id": parent_event_id,
        "session_id": session_id,
        "base_commit": base_commit,
        "result_commit": result_commit,
        "artifact_paths": artifact_paths,
        "finding_fingerprint": finding_fingerprint,
        "disposition": disposition,
        "reason": reason,
    }
    return validate_event(record)


def _parse_timestamp(value: str) -> datetime:
    if not value.endswith("Z"):
        raise EventValidationError("timestamp_utc must be a UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise EventValidationError("timestamp_utc must be valid RFC 3339") from exc
    if parsed.utcoffset() != timedelta(0):
        raise EventValidationError("timestamp_utc must be UTC")
    return parsed


@functools.lru_cache(maxsize=1)
def _event_validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


def validate_event(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise EventValidationError("event must be an object")
    candidate = dict(record)
    errors = sorted(
        _event_validator().iter_errors(candidate),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path)
        prefix = f"{location}: " if location else ""
        raise EventValidationError(f"{prefix}{error.message}")
    return candidate


def git_common_dir(cwd: str | os.PathLike[str] = ".") -> Path:
    working_dir = Path(cwd).resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=working_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        diagnostic = result.stderr.strip() or "not a Git repository"
        raise EventError(f"cannot resolve git common directory: {diagnostic}")
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        path = working_dir / path
    return path.resolve()


def monthly_log_path(
    cwd: str | os.PathLike[str],
    instant: datetime,
) -> Path:
    if instant.tzinfo is None:
        raise EventValidationError("monthly log timestamp must be timezone-aware")
    month = instant.astimezone(timezone.utc).strftime("%Y-%m")
    return git_common_dir(cwd) / "agentic" / "run-events" / f"{month}.jsonl"


def _encoded_record(record: Mapping[str, Any]) -> tuple[dict[str, Any], bytes]:
    valid = validate_event(record)
    payload = (
        json.dumps(valid, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")
    if len(payload) > MAX_RECORD_BYTES:
        raise EventTooLarge(
            f"encoded event is {len(payload)} bytes; maximum is {MAX_RECORD_BYTES}"
        )
    return valid, payload


def _truncate_unterminated_tail(fd: int) -> None:
    end = os.lseek(fd, 0, os.SEEK_END)
    if end == 0 or os.pread(fd, 1, end - 1) == b"\n":
        return
    position = end
    while position:
        start = max(0, position - MAX_RECORD_BYTES)
        chunk = os.pread(fd, position - start, start)
        newline = chunk.rfind(b"\n")
        if newline >= 0:
            os.ftruncate(fd, start + newline + 1)
            os.fsync(fd)
            return
        position = start
    os.ftruncate(fd, 0)
    os.fsync(fd)


def append_event(
    record: Mapping[str, Any],
    *,
    cwd: str | os.PathLike[str] = ".",
) -> Path:
    valid, payload = _encoded_record(record)
    path = monthly_log_path(cwd, _parse_timestamp(valid["timestamp_utc"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        _truncate_unterminated_tail(fd)
        written = os.write(fd, payload)
        if written != len(payload):
            raise OSError(f"short append: wrote {written} of {len(payload)} bytes")
        os.fsync(fd)
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
    return path


def try_append_event(
    record: Mapping[str, Any],
    *,
    cwd: str | os.PathLike[str] = ".",
) -> EventWriteResult:
    try:
        append_event(record, cwd=cwd)
    except (EventValidationError, EventTooLarge):
        raise
    except (EventError, OSError, subprocess.SubprocessError) as exc:
        warnings.warn(
            f"run event write failed; run telemetry is unknown: {exc}",
            EventWriteWarning,
            stacklevel=2,
        )
        return EventWriteResult(written=False, run_unknown=True, error=str(exc))
    return EventWriteResult(written=True, run_unknown=False)


def _month_start(month: str) -> datetime:
    try:
        parsed = datetime.strptime(month, "%Y-%m")
    except ValueError as exc:
        raise EventValidationError("month must use YYYY-MM") from exc
    if parsed.strftime("%Y-%m") != month:
        raise EventValidationError("month must use YYYY-MM")
    return parsed.replace(tzinfo=timezone.utc)


def _next_month(start: datetime) -> datetime:
    if start.month == 12:
        return start.replace(year=start.year + 1, month=1)
    return start.replace(month=start.month + 1)


def month_retention(
    month: str,
    *,
    now: datetime | None = None,
    aggregate_written: bool,
) -> MonthRetention:
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise EventValidationError("retention time must be timezone-aware")
    cutoff = instant.astimezone(timezone.utc) - timedelta(days=RETENTION_DAYS)
    ended = _next_month(_month_start(month)) <= cutoff
    return MonthRetention(
        month=month,
        cutoff_utc=cutoff,
        raw_window_ended_before_cutoff=ended,
        aggregate_written=aggregate_written,
        prunable=ended and aggregate_written,
    )


def _read_locked(path: Path) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY)
    except FileNotFoundError:
        return b""
    try:
        fcntl.flock(fd, fcntl.LOCK_SH)
        chunks = []
        while True:
            chunk = os.read(fd, 64 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def read_events(
    *,
    cwd: str | os.PathLike[str] = ".",
    month: str,
) -> list[dict[str, Any]]:
    start = _month_start(month)
    path = monthly_log_path(cwd, start)
    data = _read_locked(path)
    if not data:
        return []
    lines = data.splitlines(keepends=True)
    records = []
    for index, raw in enumerate(lines, start=1):
        final_unterminated = index == len(lines) and not raw.endswith(b"\n")
        if final_unterminated:
            warnings.warn(
                f"ignored incomplete final event record at {path}:{index}",
                IncompleteFinalRecordWarning,
                stacklevel=2,
            )
            break
        try:
            value = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise MalformedEventLog(
                f"{path}: malformed record at line {index}: {exc}"
            ) from exc
        try:
            records.append(validate_event(value))
        except EventValidationError as exc:
            raise MalformedEventLog(
                f"{path}: malformed record at line {index}: {exc}"
            ) from exc
    return records


def configure_cli(parser: argparse.ArgumentParser) -> None:
    actions = parser.add_subparsers(dest="event_action", required=True)
    new = actions.add_parser("new-run", help="create a UUIDv7 run context")
    new.add_argument("--prior-run-id", default=UNKNOWN)
    retry = actions.add_parser("retry", help="increment an existing run attempt")
    retry.add_argument("run_id")
    retry.add_argument("attempt", type=int)
    retry.add_argument("--prior-run-id", default=UNKNOWN)
    reopen = actions.add_parser("reopen", help="create a run linked to a prior run")
    reopen.add_argument("prior_run_id")
    append = actions.add_parser("append", help="append one event from JSON")
    append.add_argument("--file", default="-", help="JSON file, or - for stdin")
    append.add_argument("--cwd", default=".", help="repository worktree")
    read = actions.add_parser("read", help="read one validated monthly event log")
    read.add_argument("--month", required=True)
    read.add_argument("--cwd", default=".", help="repository worktree")
    parser.set_defaults(func=run_cli)


def _print_run(run: RunContext) -> None:
    print(json.dumps(dataclasses.asdict(run), sort_keys=True))


def run_cli(args: argparse.Namespace) -> int:
    try:
        if args.event_action == "new-run":
            _print_run(new_run(args.prior_run_id))
        elif args.event_action == "retry":
            _print_run(
                retry_run(RunContext(args.run_id, args.prior_run_id, args.attempt))
            )
        elif args.event_action == "reopen":
            _print_run(reopen_run(args.prior_run_id))
        elif args.event_action == "append":
            if args.file == "-":
                record = json.load(sys.stdin)
            else:
                with open(args.file, encoding="utf-8") as handle:
                    record = json.load(handle)
            result = try_append_event(record, cwd=args.cwd)
            print(
                json.dumps(
                    {
                        **dataclasses.asdict(result),
                        "event_id": record["event_id"],
                        "result": "written" if result.written else UNKNOWN,
                    },
                    sort_keys=True,
                )
            )
        elif args.event_action == "read":
            print(
                json.dumps(read_events(cwd=args.cwd, month=args.month), sort_keys=True)
            )
        return 0
    except (EventError, OSError, json.JSONDecodeError) as exc:
        print(f"agentic event: {exc}", file=sys.stderr)
        return 1
