#!/usr/bin/env python3
"""Compute the versioned R6 toolkit scorecard from covered raw inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

TOOLKIT_ROOT = Path(__file__).resolve().parents[1]
if str(TOOLKIT_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLKIT_ROOT))

from agentic.events import EventValidationError, validate_event

FORMULA_VERSION = "r6-v1"
RETENTION_DAYS = 90
UNKNOWN = "unknown"
JUDGMENT_SCHEMA_VERSION = 1
MATCHER_VERSION = "quoted-phrases-v1"
JUDGE_PROMPT_VERSION = "trigger-fit-v1"

STAGE_REQUIRED_FIELDS = {
    "claim": ("issue_id",),
    "session-link": ("session_id",),
    "worker-verdict": ("disposition",),
    "status-transition": ("disposition",),
    "reviewer-finding": ("finding_fingerprint", "artifact_paths"),
    "gate-finding": ("finding_fingerprint", "artifact_paths"),
    "finding-disposition": ("finding_fingerprint", "disposition"),
    "reviewer-acceptance": ("disposition",),
    "final-gate": ("disposition",),
    "close": ("result_commit",),
}
JUDGMENT_FIELDS = {
    "schema_version",
    "formula_version",
    "timestamp_utc",
    "session_id",
    "skill",
    "matcher_version",
    "skill_content_hash",
    "judge_model",
    "judge_prompt_version",
    "eligibility_verdict",
    "trigger_verdict",
    "evidence_record_ids",
}
JUDGMENT_VERDICT_PAIRS = {
    ("explicit", "explicit_invocation"),
    ("applicable", "correctly-triggered"),
    ("applicable", "missed"),
    ("not-applicable", "correctly-triggered"),
    ("not-applicable", "misfired"),
    ("not-applicable", "not-triggered"),
    ("ineligible-self-chain", "self_chained"),
    ("unknown", "unresolvable"),
}
NO_JUDGE_VERDICTS = {
    ("explicit", "explicit_invocation"),
    ("ineligible-self-chain", "self_chained"),
    ("unknown", "unresolvable"),
}


class ScorecardError(ValueError):
    """The requested scorecard cannot be reproduced from its inputs."""


def parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ScorecardError(f"expected UTC RFC3339 timestamp, got {value!r}")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ScorecardError(f"invalid timestamp {value!r}") from exc
    if parsed.utcoffset() != timedelta(0):
        raise ScorecardError(f"timestamp is not UTC: {value!r}")
    return parsed


def utc_text(value: datetime) -> str:
    value = value.astimezone(timezone.utc)
    if value.microsecond:
        return value.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScorecardError(f"{path}: {exc}") from exc


def _read_jsonl(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ScorecardError(f"{path}: {exc}") from exc
        for number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ScorecardError(f"{path}:{number}: malformed JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ScorecardError(f"{path}:{number}: expected a JSON object")
            rows.append(row)
    return rows


def _hash_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ScorecardError(f"{path}: {exc}") from exc


def _hash_source(paths: list[Path]) -> str:
    ordered = sorted(paths, key=lambda path: str(path.resolve()))
    hashes = [_hash_file(path) for path in ordered]
    if len(hashes) == 1:
        return hashes[0]
    canonical = json.dumps(hashes, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def _input_file_inventory(
    sources: dict[str, list[Path]],
) -> list[dict[str, str]]:
    inventory = []
    for source, paths in sources.items():
        for path in paths:
            inventory.append(
                {
                    "source": source,
                    "identity": str(path.resolve()),
                    "sha256": _hash_file(path),
                }
            )
    return sorted(inventory, key=lambda row: (row["source"], row["identity"]))


def _coverage_intervals(row: Any) -> list[tuple[datetime, datetime]]:
    candidates = row if isinstance(row, list) else [row]
    intervals = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ScorecardError("coverage rows must be objects or arrays of objects")
        start = parse_utc(candidate.get("start"))
        end = parse_utc(candidate.get("end"))
        if start >= end:
            raise ScorecardError("coverage interval start must precede end")
        intervals.append((start, end))
    return sorted(intervals)


def _missing_ranges(
    start: datetime,
    end: datetime,
    intervals: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    cursor = start
    missing = []
    for covered_start, covered_end in intervals:
        if covered_end <= cursor or covered_start >= end:
            continue
        if covered_start > cursor:
            missing.append((cursor, min(covered_start, end)))
        cursor = max(cursor, covered_end)
        if cursor >= end:
            break
    if cursor < end:
        missing.append((cursor, end))
    return [(left, right) for left, right in missing if left < right]


def validate_coverage(
    coverage: dict[str, Any],
    start: datetime,
    end: datetime,
    now: datetime,
) -> None:
    missing_lines = []
    retention_start = now - timedelta(days=RETENTION_DAYS)
    if start < retention_start:
        missing_lines.append(
            f"run-events retention missing "
            f"[{utc_text(start)},{utc_text(min(end, retention_start))})"
        )
    sources = coverage.get("sources", {})
    if not isinstance(sources, dict):
        raise ScorecardError("coverage.sources must be an object")
    for name in ("events", "judgments", "issues", "costs"):
        intervals = _coverage_intervals(sources.get(name, []))
        for left, right in _missing_ranges(start, end, intervals):
            missing_lines.append(
                f"{name} missing [{utc_text(left)},{utc_text(right)})"
            )
    if missing_lines:
        raise ScorecardError("raw-source coverage incomplete:\n" + "\n".join(missing_lines))


def _in_window(row: dict[str, Any], field: str, start: datetime, end: datetime) -> bool:
    value = row.get(field)
    if value is None:
        return True
    instant = parse_utc(value)
    return start <= instant < end


def _ratio(numerator: int | float, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _percentile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def normalize_finding_message(message: str) -> str:
    normalized = re.sub(r"\b0x[0-9a-fA-F]+\b", "<address>", message)
    normalized = re.sub(
        r"\bline\s+\d+(?::\d+)?\b", "line <location>", normalized, flags=re.I
    )
    normalized = re.sub(r"(?<=\D)\d+:\d+(?=\D|$)", "<location>", normalized)
    return " ".join(normalized.split())


def finding_fingerprint(producer: str, rule_id: str, path: str, message: str) -> str:
    canonical = json.dumps(
        [
            producer,
            rule_id,
            Path(path).as_posix(),
            normalize_finding_message(message),
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


def _unknown(value: Any) -> bool:
    return value == UNKNOWN or value is None or value == []


def _event_unknown(event: dict[str, Any]) -> bool:
    required = STAGE_REQUIRED_FIELDS.get(event.get("stage"), ())
    return any(_unknown(event.get(field)) for field in required)


def _validate_events(events: list[dict[str, Any]]) -> None:
    for position, event in enumerate(events):
        try:
            validate_event(event)
        except EventValidationError as exc:
            raise ScorecardError(f"events[{position}] schema: {exc}") from exc
        parse_utc(event["timestamp_utc"])


def _validate_judgment(row: dict[str, Any], position: int) -> None:
    missing = sorted(JUDGMENT_FIELDS - set(row))
    extra = sorted(set(row) - JUDGMENT_FIELDS)
    if missing or extra:
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unexpected " + ", ".join(extra))
        raise ScorecardError(f"judgments[{position}] schema: {'; '.join(details)}")
    if row["schema_version"] != JUDGMENT_SCHEMA_VERSION or isinstance(
        row["schema_version"], bool
    ):
        raise ScorecardError(f"judgments[{position}] schema_version is unsupported")
    versions = {
        "formula_version": FORMULA_VERSION,
        "matcher_version": MATCHER_VERSION,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
    }
    for field, expected in versions.items():
        if row[field] != expected:
            raise ScorecardError(
                f"judgments[{position}].{field} must be {expected!r}"
            )
    for field in ("session_id", "skill", "judge_model"):
        if not isinstance(row[field], str) or not row[field]:
            raise ScorecardError(
                f"judgments[{position}].{field} must be a non-empty string"
            )
    try:
        parse_utc(row["timestamp_utc"])
    except ScorecardError as exc:
        raise ScorecardError(
            f"judgments[{position}].timestamp_utc is invalid: {exc}"
        ) from exc
    verdicts = (row["eligibility_verdict"], row["trigger_verdict"])
    if verdicts not in JUDGMENT_VERDICT_PAIRS:
        raise ScorecardError(
            f"judgments[{position}] has invalid eligibility/trigger verdicts"
        )
    content_hash = row["skill_content_hash"]
    valid_hash = content_hash == UNKNOWN or bool(
        isinstance(content_hash, str)
        and re.fullmatch(r"[0-9a-f]{64}", content_hash)
    )
    if not valid_hash:
        raise ScorecardError(
            f"judgments[{position}].skill_content_hash is invalid"
        )
    judge_model = row["judge_model"]
    if verdicts in NO_JUDGE_VERDICTS:
        valid_model = judge_model == "none"
    else:
        valid_model = judge_model not in {"none", UNKNOWN}
    if not valid_model:
        raise ScorecardError(f"judgments[{position}].judge_model is invalid")
    evidence = row["evidence_record_ids"]
    if (
        not isinstance(evidence, list)
        or not evidence
        or any(not isinstance(record_id, str) or not record_id for record_id in evidence)
        or len(set(evidence)) != len(evidence)
    ):
        raise ScorecardError(
            f"judgments[{position}].evidence_record_ids is invalid"
        )


def _latest(events: list[dict[str, Any]], stage: str) -> dict[str, Any] | None:
    matches = [event for event in events if event.get("stage") == stage]
    return max(matches, key=lambda event: parse_utc(event["timestamp_utc"])) if matches else None


def _accepted(event: dict[str, Any] | None) -> bool:
    return bool(
        event
        and str(event.get("disposition", "")).lower()
        in {"accepted", "accept", "pass", "passed"}
    )


def _gate_passed(event: dict[str, Any] | None) -> bool:
    return bool(
        event
        and str(event.get("disposition", "")).lower()
        in {"pass", "passed"}
    )


def _artifact_paths(value: Any) -> set[str]:
    if isinstance(value, list):
        return {str(path) for path in value}
    return set()


def _repo_relative_artifact_paths(value: Any) -> set[str]:
    normalized = set()
    for raw in _artifact_paths(value):
        path = Path(raw)
        if path.is_absolute() or ".." in path.parts:
            continue
        posix = path.as_posix()
        if posix == raw:
            normalized.add(posix)
    return normalized


def _git_changed_paths(
    repo_root: Path,
    base_commit: Any,
    result_commit: Any,
) -> set[str] | None:
    if _unknown(base_commit) or _unknown(result_commit):
        return None
    if not all(
        isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40,64}", commit)
        for commit in (base_commit, result_commit)
    ):
        return None
    try:
        completed = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                "--no-renames",
                f"{base_commit}..{result_commit}",
                "--",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return {
        Path(line).as_posix()
        for line in completed.stdout.splitlines()
        if line.strip()
    }


def _issue_rows(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("issues"), list):
        return raw["issues"]
    raise ScorecardError("issues input must be an array or an object with issues")


def _dependency_parent(dependency: Any) -> str | None:
    if not isinstance(dependency, dict):
        return None
    dep_type = dependency.get("type") or dependency.get("dependency_type")
    if dep_type != "discovered-from":
        return None
    return (
        dependency.get("depends_on_id")
        or dependency.get("depends_on")
        or dependency.get("target")
    )


def _discovery_times(
    issue: dict[str, Any],
    dependency: dict[str, Any],
) -> tuple[datetime, datetime] | None:
    edge_value = (
        dependency.get("created_at")
        or dependency.get("timestamp_utc")
        or dependency.get("created_at_utc")
    )
    child_value = issue.get("created_at")
    if not edge_value or not child_value:
        return None
    return parse_utc(child_value), parse_utc(edge_value)


def _dedupe_judgments(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for position, row in enumerate(rows):
        _validate_judgment(row, position)
        formula = row.get("formula_version")
        key = (formula, row.get("session_id"), row.get("skill"))
        prior = by_key.get(key)
        if prior is not None and prior != row:
            raise ScorecardError(f"conflicting frozen judgment for {key}")
        by_key[key] = row
    return list(by_key.values())


def compute_scorecard(
    *,
    start: datetime,
    end: datetime,
    events: list[dict[str, Any]],
    judgments: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    costs: list[dict[str, Any]],
    input_hashes: dict[str, str],
    input_files: list[dict[str, str]],
    repo_root: Path,
) -> dict[str, Any]:
    _validate_events(events)
    events = [
        row for row in events if _in_window(row, "timestamp_utc", start, end)
    ]
    for position, judgment in enumerate(judgments):
        _validate_judgment(judgment, position)
    judgments = [
        row for row in judgments if _in_window(row, "timestamp_utc", start, end)
    ]
    costs = [row for row in costs if _in_window(row, "time", start, end)]
    judgments = _dedupe_judgments(judgments)

    eligible = [
        row
        for row in judgments
        if row.get("eligibility_verdict") in {"applicable", "explicit"}
    ]
    triggered = [
        row
        for row in eligible
        if row.get("trigger_verdict") == "correctly-triggered"
    ]

    by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        run_id = event.get("run_id")
        if not run_id:
            raise ScorecardError("event run_id must be non-empty")
        by_run[run_id].append(event)

    run_state: dict[str, dict[str, Any]] = {}
    run_join_unknowns: dict[str, int] = defaultdict(int)
    for run_id, rows in by_run.items():
        claim = _latest(rows, "claim")
        link = _latest(rows, "session-link")
        worker = _latest(rows, "worker-verdict")
        review = _latest(rows, "reviewer-acceptance")
        gate = _latest(rows, "final-gate")
        close = _latest(rows, "close")
        join_stages = {
            "claim",
            "session-link",
            "worker-verdict",
            "reviewer-acceptance",
            "final-gate",
            "close",
            "reviewer-finding",
            "gate-finding",
            "finding-disposition",
            "status-transition",
        }
        join_events = [
            event for event in rows if event.get("stage") in join_stages
        ]
        issue_ids = {
            event.get("issue_id")
            for event in join_events
            if not _unknown(event.get("issue_id"))
        }
        repo_ids = {
            event.get("repo_id")
            for event in join_events
            if not _unknown(event.get("repo_id"))
        }
        identity_consistent = bool(
            join_events
            and len(issue_ids) == 1
            and len(repo_ids) == 1
            and all(
                not _unknown(event.get("issue_id"))
                and not _unknown(event.get("repo_id"))
                for event in join_events
            )
        )
        complete = bool(
            claim
            and not _unknown(claim.get("issue_id"))
            and link
            and not _unknown(link.get("session_id"))
            and worker
            and not _unknown(worker.get("disposition"))
            and _accepted(review)
            and _gate_passed(gate)
            and close
            and not _unknown(close.get("result_commit"))
            and identity_consistent
        )
        join_checks = {
            "identity": identity_consistent,
            "claim": bool(claim and not _unknown(claim.get("issue_id"))),
            "session_link": bool(link and not _unknown(link.get("session_id"))),
            "worker_verdict": bool(
                worker and not _unknown(worker.get("disposition"))
            ),
            "reviewer_acceptance": _accepted(review),
            "final_gate_pass": _gate_passed(gate),
            "close": bool(close),
            "result_commit": bool(
                close and not _unknown(close.get("result_commit"))
            ),
        }
        for field, present in join_checks.items():
            if not present:
                run_join_unknowns[field] += 1
        run_state[run_id] = {
            "claim": claim,
            "link": link,
            "worker": worker,
            "review": review,
            "gate": gate,
            "close": close,
            "complete": complete,
            "identity_consistent": identity_consistent,
        }

    reaching_review = [state for state in run_state.values() if state["review"]]
    verified = [state for state in reaching_review if state["complete"]]
    verified_unknown = len(reaching_review) - len(verified)

    unique_findings: dict[tuple[str, str], dict[str, Any]] = {}
    dispositions: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    unknown_findings = 0
    for run_id, rows in by_run.items():
        for event in rows:
            fingerprint = event.get("finding_fingerprint")
            if _unknown(fingerprint):
                if event.get("stage") in {"reviewer-finding", "gate-finding"}:
                    unknown_findings += 1
                continue
            key = (run_id, fingerprint)
            if event.get("stage") in {"reviewer-finding", "gate-finding"}:
                unique_findings.setdefault(key, event)
            if event.get("stage") == "finding-disposition":
                dispositions[key].append(event)
    prevented = 0
    prevention_evidence_unknowns = 0
    changed_paths_by_run: dict[tuple[str, str], set[str] | None] = {}
    for key, finding in unique_findings.items():
        run_id, _ = key
        close = run_state[run_id]["close"]
        if close is None:
            prevention_evidence_unknowns += 1
            continue
        finding_time = parse_utc(finding["timestamp_utc"])
        close_time = parse_utc(close["timestamp_utc"])
        fixing_events = [
            event
            for event in dispositions[key]
            if str(event.get("disposition", "")).lower() == "fixed"
            and finding_time < parse_utc(event["timestamp_utc"]) <= close_time
        ]
        if not fixing_events:
            continue
        finding_snapshot = max(
            fixing_events, key=lambda event: parse_utc(event["timestamp_utc"])
        )
        cache_key = (run_id, finding_snapshot["event_id"])
        if cache_key not in changed_paths_by_run:
            changed_paths_by_run[cache_key] = _git_changed_paths(
                repo_root,
                finding_snapshot.get("base_commit"),
                finding_snapshot.get("result_commit"),
            )
        changed_paths = changed_paths_by_run[cache_key]
        finding_paths = _repo_relative_artifact_paths(
            finding.get("artifact_paths")
        )
        if changed_paths is None or not finding_paths:
            prevention_evidence_unknowns += 1
            continue
        changed = bool(finding_paths & changed_paths)
        if changed:
            prevented += 1

    instrumented_issues = {
        state["claim"].get("issue_id")
        for state in run_state.values()
        if state["claim"]
    }
    durations = []
    issue_by_id = {row.get("id") or row.get("issue_id"): row for row in issues}
    for issue_id in instrumented_issues:
        issue = issue_by_id.get(issue_id)
        if not issue or not issue.get("created_at") or not issue.get("closed_at"):
            continue
        duration = parse_utc(issue["closed_at"]) - parse_utc(issue["created_at"])
        durations.append(duration.total_seconds() / 3600)

    verdict_counts = {"done": 0, "blocked": 0, "deferred": 0}
    for state in run_state.values():
        worker = state["worker"]
        if not worker:
            continue
        if str(worker.get("disposition", "")).lower() == "done":
            verdict_counts["done"] += 1
    transitions = [
        event for event in events if event.get("stage") == "status-transition"
    ]
    for status in ("blocked", "deferred"):
        transition_count = sum(
            str(event.get("disposition", "")).lower() == status
            for event in transitions
        )
        if transition_count:
            verdict_counts[status] = transition_count
    retries = sum(
        max(int(event.get("attempt", 1)) for event in rows) - 1
        for rows in by_run.values()
    )
    reopened_runs = {
        run_id
        for run_id, rows in by_run.items()
        if any(not _unknown(event.get("prior_run_id")) for event in rows)
        or any(
            event.get("stage") == "status-transition"
            and str(event.get("disposition", "")).lower() in {"reopen", "reopened"}
            for event in rows
        )
    }
    reopens = len(reopened_runs)

    closed_parent_runs = [
        (
            state["claim"].get("issue_id"),
            parse_utc(state["claim"]["timestamp_utc"]),
            parse_utc(state["close"]["timestamp_utc"]),
        )
        for state in run_state.values()
        if state["claim"]
        and state["close"]
        and state["identity_consistent"]
    ]
    parent_runs_by_issue: dict[
        str, list[tuple[datetime, datetime]]
    ] = defaultdict(list)
    for issue_id, claim_time, close_time in closed_parent_runs:
        parent_runs_by_issue[issue_id].append((claim_time, close_time))
    discovered: set[str] = set()
    discovery_timing_unknowns = 0
    for issue in issues:
        child_id = issue.get("id") or issue.get("issue_id")
        linked_child_unknown = False
        for dependency in issue.get("dependencies", []):
            parent = _dependency_parent(dependency)
            if parent not in parent_runs_by_issue:
                continue
            timing = _discovery_times(issue, dependency)
            if timing is None:
                linked_child_unknown = True
                continue
            child_created_at, edge_created_at = timing
            if not (
                start <= child_created_at < end
                and start <= edge_created_at < end
            ):
                continue
            if any(
                claim_time <= child_created_at <= close_time
                and claim_time <= edge_created_at <= close_time
                for claim_time, close_time in parent_runs_by_issue[parent]
            ):
                if child_id:
                    discovered.add(child_id)
                else:
                    linked_child_unknown = True
        if linked_child_unknown:
            discovery_timing_unknowns += 1

    verified_sessions = {
        state["link"].get("session_id")
        for state in verified
        if state["link"] is not None
    }
    attributed_cost = 0
    unknown_models = 0
    sampled_verified_sessions: set[str] = set()
    for sample in costs:
        labels = sample.get("labels") or {}
        session_id = labels.get("session")
        if session_id not in verified_sessions:
            continue
        sampled_verified_sessions.add(session_id)
        stack = sample.get("stack") or []
        model = labels.get("model_raw") or (stack[-1] if stack else UNKNOWN)
        priced = labels.get("priced", "true")
        if model in {"unknown", "(unknown)", ""} or str(priced).lower() == "false":
            unknown_models += 1
            continue
        cost = (sample.get("values") or {}).get("cost_microusd")
        if isinstance(cost, bool) or not isinstance(cost, int) or cost < 0:
            unknown_models += 1
            continue
        attributed_cost += cost

    event_unknowns = sum(_event_unknown(event) for event in events)
    run_unknowns = sum(not state["complete"] for state in run_state.values())
    marginal_cost_unknowns = (
        len(verified_sessions - sampled_verified_sessions) + unknown_models
    )
    unknown_counts = {
        "adoption": sum(
            row.get("eligibility_verdict") == "unknown" for row in judgments
        ),
        "verified_outcome": verified_unknown,
        "prevention": unknown_findings + prevention_evidence_unknowns,
        "delivery": len(instrumented_issues) - len(durations),
        "discovery": discovery_timing_unknowns
        + len(set(parent_runs_by_issue) - set(issue_by_id)),
        "marginal_cost": marginal_cost_unknowns,
        "events": event_unknowns,
        "runs": run_unknowns,
    }

    return {
        "formula_version": FORMULA_VERSION,
        "window": {"start": utc_text(start), "end": utc_text(end)},
        "input_hashes": input_hashes,
        "input_files": input_files,
        "adoption": {
            "numerator": len(triggered),
            "denominator": len(eligible),
            "rate": _ratio(len(triggered), len(eligible)),
        },
        "verified_outcome_rate": {
            "numerator": len(verified),
            "denominator": len(reaching_review),
            "rate": _ratio(len(verified), len(reaching_review)),
            "unknown": verified_unknown,
        },
        "prevention": {
            "numerator": prevented,
            "denominator": len(unique_findings),
            "rate": _ratio(prevented, len(unique_findings)),
        },
        "delivery": {
            "median_hours": _percentile(durations, 0.5),
            "p90_hours": _percentile(durations, 0.9),
            **verdict_counts,
            "retries": retries,
            "reopens": reopens,
        },
        "discovery_ratio": {
            "numerator": len(discovered),
            "denominator": len(closed_parent_runs),
            "rate": _ratio(len(discovered), len(closed_parent_runs)),
        },
        "marginal_cost": {
            "cost_microusd": attributed_cost,
            "verified_closed_runs": len(verified),
            "microusd_per_verified_closed_run": _ratio(
                attributed_cost, len(verified)
            ),
            "unknown_models": unknown_models,
        },
        "event_unknown_rate": {
            "numerator": event_unknowns,
            "denominator": len(events),
            "rate": _ratio(event_unknowns, len(events)),
        },
        "run_unknown_rate": {
            "numerator": run_unknowns,
            "denominator": len(run_state),
            "rate": _ratio(run_unknowns, len(run_state)),
        },
        "unknown_counts": unknown_counts,
        "run_join_unknowns": dict(sorted(run_join_unknowns.items())),
    }


def _full_calendar_month(start: datetime, end: datetime) -> bool:
    if start.day != 1 or start.time() != datetime.min.time():
        return False
    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1)
    else:
        next_month = start.replace(month=start.month + 1)
    return end == next_month


def _write_monthly(path: Path, report: dict[str, Any]) -> None:
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != payload:
            raise ScorecardError(
                "immutable monthly report already exists with different inputs"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(payload, encoding="utf-8")
    os.replace(temporary, path)


def _check_report(path: Path) -> None:
    report = _read_json(path)
    if not isinstance(report, dict):
        raise ScorecardError("report must be a JSON object")
    required = {"formula_version", "source_window", "scorecard_unknown_rate"}
    missing = sorted(required - set(report))
    if missing:
        raise ScorecardError("report missing fields: " + ", ".join(missing))
    if report["formula_version"] != FORMULA_VERSION:
        raise ScorecardError("report formula_version is not current")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--now")
    parser.add_argument("--events", action="append", type=Path)
    parser.add_argument("--judgments", action="append", type=Path)
    parser.add_argument("--issues", type=Path)
    parser.add_argument("--costs", action="append", type=Path)
    parser.add_argument("--coverage", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--monthly-out", type=Path)
    parser.add_argument("--check", type=Path)
    parser.add_argument(
        "--fingerprint",
        nargs=4,
        metavar=("PRODUCER", "RULE_ID", "PATH", "MESSAGE"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.fingerprint:
            print(finding_fingerprint(*args.fingerprint))
            return 0
        if args.check:
            _check_report(args.check)
            return 0
        required = {
            "--start": args.start,
            "--end": args.end,
            "--events": args.events,
            "--judgments": args.judgments,
            "--issues": args.issues,
            "--costs": args.costs,
            "--coverage": args.coverage,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ScorecardError("missing required arguments: " + ", ".join(missing))
        start, end = parse_utc(args.start), parse_utc(args.end)
        if start >= end:
            raise ScorecardError("window start must precede end")
        now = parse_utc(args.now) if args.now else datetime.now(timezone.utc)
        coverage = _read_json(args.coverage)
        if not isinstance(coverage, dict):
            raise ScorecardError("coverage input must be an object")
        validate_coverage(coverage, start, end, now)

        events = _read_jsonl(args.events)
        judgments = _read_jsonl(args.judgments)
        costs = _read_jsonl(args.costs)
        issues = _issue_rows(_read_json(args.issues))
        source_paths = {
            "events": args.events,
            "judgments": args.judgments,
            "issues": [args.issues],
            "costs": args.costs,
            "coverage": [args.coverage],
        }
        input_hashes = {
            source: _hash_source(paths)
            for source, paths in source_paths.items()
        }
        report = compute_scorecard(
            start=start,
            end=end,
            events=events,
            judgments=judgments,
            issues=issues,
            costs=costs,
            input_hashes=input_hashes,
            input_files=_input_file_inventory(source_paths),
            repo_root=args.repo_root.resolve(),
        )
        report["source_coverage"] = coverage["sources"]
        if args.monthly_out:
            if not _full_calendar_month(start, end):
                raise ScorecardError(
                    "monthly reports require one full UTC calendar month"
                )
            _write_monthly(args.monthly_out, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except ScorecardError as exc:
        print(f"report-toolkit-outcomes: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
