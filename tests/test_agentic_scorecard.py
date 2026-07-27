"""Golden behavioral coverage for the reproducible R6 scorecard."""

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "report-toolkit-outcomes.py"
START = "2026-07-01T00:00:00Z"
END = "2026-08-01T00:00:00Z"
NOW = "2026-08-15T00:00:00Z"
RUN_0 = "0197f000-0000-7000-8000-000000000001"
RUN_1 = "0197f000-0000-7000-8000-000000000002"
RUN_2 = "0197f000-0000-7000-8000-000000000003"
FINDING_A = "a" * 64
SKILL_HASH = "b" * 64
_EVENT_IDS = itertools.count(100)


def _uuid7(serial: int) -> str:
    return f"0197f000-0000-7000-8000-{serial:012x}"


def _write_json(path: Path, value) -> Path:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _event(run: str, issue: str, stage: str, at: str, **changes) -> dict:
    row = {
        "schema_version": 1,
        "event_id": _uuid7(next(_EVENT_IDS)),
        "run_id": run,
        "prior_run_id": "unknown",
        "timestamp_utc": at,
        "producer": "drain",
        "runtime": "codex",
        "repo_id": "repo-1",
        "issue_id": issue,
        "attempt": 1,
        "stage": stage,
        "parent_event_id": "unknown",
        "session_id": "unknown",
        "base_commit": "unknown",
        "result_commit": "unknown",
        "artifact_paths": "unknown",
        "finding_fingerprint": "unknown",
        "disposition": "unknown",
        "reason": "unknown",
    }
    row.update(changes)
    return row


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _prevention_repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Scorecard Fixture")
    _git(repo, "config", "user.email", "scorecard@example.invalid")
    artifact = repo / "agentic" / "work.py"
    artifact.parent.mkdir()
    artifact.write_text("before = True\n", encoding="utf-8")
    _git(repo, "add", "agentic/work.py")
    _git(repo, "commit", "-q", "-m", "fixture base")
    base = _git(repo, "rev-parse", "HEAD")
    artifact.write_text("before = False\n", encoding="utf-8")
    _git(repo, "add", "agentic/work.py")
    _git(repo, "commit", "-q", "-m", "fixture result")
    return repo, base, _git(repo, "rev-parse", "HEAD")


def _judgment(
    session_id: str,
    eligibility: str,
    trigger: str,
    *,
    at: str,
) -> dict:
    return {
        "schema_version": 1,
        "formula_version": "r6-v1",
        "timestamp_utc": at,
        "session_id": session_id,
        "skill": "build",
        "matcher_version": "quoted-phrases-v1",
        "skill_content_hash": SKILL_HASH,
        "judge_model": "none" if eligibility == "explicit" else "opus",
        "judge_prompt_version": "trigger-fit-v1",
        "eligibility_verdict": eligibility,
        "trigger_verdict": trigger,
        "evidence_record_ids": [f"{session_id}#evidence"],
    }


@pytest.fixture
def scorecard_inputs(tmp_path: Path) -> dict[str, Path]:
    repo, base_commit, result_commit = _prevention_repo(tmp_path)
    judgments = [
        _judgment(
            "session-1",
            "applicable",
            "correctly-triggered",
            at="2026-07-01T00:10:00Z",
        ),
        _judgment(
            "session-2",
            "explicit",
            "explicit_invocation",
            at="2026-07-02T00:10:00Z",
        ),
        _judgment(
            "session-3",
            "applicable",
            "missed",
            at="2026-07-03T00:10:00Z",
        ),
        _judgment(
            "session-4",
            "not-applicable",
            "not-triggered",
            at="2026-07-04T00:10:00Z",
        ),
    ]
    events = [
        _event(RUN_1, "issue-1", "claim", "2026-07-01T01:00:00Z"),
        _event(
            RUN_1,
            "issue-1",
            "session-link",
            "2026-07-01T01:01:00Z",
            session_id="session-1",
        ),
        _event(
            RUN_1,
            "issue-1",
            "worker-verdict",
            "2026-07-01T05:00:00Z",
            disposition="DONE",
            attempt=2,
        ),
        _event(
            RUN_1,
            "issue-1",
            "reviewer-finding",
            "2026-07-01T05:10:00Z",
            producer="critic",
            finding_fingerprint=FINDING_A,
            artifact_paths=["agentic/work.py"],
        ),
        _event(
            RUN_1,
            "issue-1",
            "reviewer-finding",
            "2026-07-01T05:11:00Z",
            producer="critic",
            finding_fingerprint=FINDING_A,
            artifact_paths=["agentic/work.py"],
        ),
        _event(
            RUN_1,
            "issue-1",
            "finding-disposition",
            "2026-07-01T05:20:00Z",
            finding_fingerprint=FINDING_A,
            disposition="fixed",
            base_commit=base_commit,
            result_commit=result_commit,
        ),
        _event(
            RUN_1,
            "issue-1",
            "reviewer-acceptance",
            "2026-07-01T05:30:00Z",
            disposition="accepted",
        ),
        _event(
            RUN_1,
            "issue-1",
            "final-gate",
            "2026-07-01T05:40:00Z",
            disposition="PASS",
        ),
        _event(
            RUN_1,
            "issue-1",
            "close",
            "2026-07-01T06:00:00Z",
            base_commit=base_commit,
            result_commit=result_commit,
            artifact_paths=["agentic/work.py"],
        ),
        _event(
            RUN_2,
            "issue-2",
            "claim",
            "2026-07-02T01:00:00Z",
            prior_run_id=RUN_0,
        ),
        _event(
            RUN_2,
            "issue-2",
            "session-link",
            "2026-07-02T01:01:00Z",
            session_id="session-2",
        ),
        _event(
            RUN_2,
            "issue-2",
            "worker-verdict",
            "2026-07-02T05:00:00Z",
            disposition="BLOCKED",
        ),
        _event(
            RUN_2,
            "issue-2",
            "reviewer-acceptance",
            "2026-07-02T05:30:00Z",
            disposition="accepted",
        ),
        _event(
            RUN_2,
            "issue-2",
            "final-gate",
            "2026-07-02T05:40:00Z",
            disposition="unknown",
        ),
    ]
    issues = [
        {
            "id": "issue-1",
            "created_at": "2026-07-01T00:00:00Z",
            "closed_at": "2026-07-01T10:00:00Z",
            "status": "closed",
            "dependencies": [],
        },
        {
            "id": "issue-2",
            "created_at": "2026-07-02T00:00:00Z",
            "closed_at": "2026-07-02T20:00:00Z",
            "status": "closed",
            "dependencies": [],
        },
        {
            "id": "issue-child",
            "created_at": "2026-07-01T05:50:00Z",
            "closed_at": None,
            "status": "open",
            "dependencies": [
                {
                    "type": "discovered-from",
                    "depends_on_id": "issue-1",
                    "created_at": "2026-07-01T05:50:00Z",
                }
            ],
        },
    ]
    costs = [
        {
            "time": "2026-07-01T02:00:00Z",
            "stack": ["repo", "claude-sonnet"],
            "values": {"cost_microusd": 3_000_000},
            "labels": {"session": "session-1"},
        },
        {
            "time": "2026-07-02T02:00:00Z",
            "stack": ["repo", "claude-sonnet"],
            "values": {"cost_microusd": 2_000_000},
            "labels": {"session": "session-2"},
        },
    ]
    paths = {
        "repo": repo,
        "events": _write_jsonl(tmp_path / "events.jsonl", events),
        "judgments": _write_jsonl(tmp_path / "judgments.jsonl", judgments),
        "issues": _write_json(tmp_path / "issues.json", issues),
        "costs": _write_jsonl(tmp_path / "costs.jsonl", costs),
    }
    paths["coverage"] = _write_json(
        tmp_path / "coverage.json",
        {
            "sources": {
                name: {"start": START, "end": END}
                for name in ("events", "judgments", "issues", "costs")
            }
        },
    )
    return paths


def _run(paths: dict[str, Path], *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--start",
            START,
            "--end",
            END,
            "--now",
            NOW,
            "--events",
            str(paths["events"]),
            "--judgments",
            str(paths["judgments"]),
            "--issues",
            str(paths["issues"]),
            "--costs",
            str(paths["costs"]),
            "--coverage",
            str(paths["coverage"]),
            "--repo-root",
            str(paths["repo"]),
            *extra,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_golden_scorecard_computes_every_r6_formula(scorecard_inputs):
    result = _run(scorecard_inputs)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)

    assert report["formula_version"] == "r6-v1"
    assert report["window"] == {"start": START, "end": END}
    assert report["adoption"] == {
        "numerator": 1,
        "denominator": 3,
        "rate": pytest.approx(1 / 3),
    }
    assert report["verified_outcome_rate"] == {
        "numerator": 1,
        "denominator": 2,
        "rate": 0.5,
        "unknown": 1,
    }
    assert report["prevention"] == {
        "numerator": 1,
        "denominator": 1,
        "rate": 1.0,
    }
    assert report["delivery"] == {
        "median_hours": 15.0,
        "p90_hours": 19.0,
        "done": 1,
        "blocked": 0,
        "deferred": 0,
        "retries": 1,
        "reopens": 1,
    }
    assert report["discovery_ratio"] == {
        "numerator": 1,
        "denominator": 1,
        "rate": 1.0,
    }
    assert report["marginal_cost"] == {
        "cost_microusd": 3_000_000,
        "verified_closed_runs": 1,
        "microusd_per_verified_closed_run": 3_000_000.0,
        "unknown_models": 0,
    }
    assert report["event_unknown_rate"] == {
        "numerator": 1,
        "denominator": 14,
        "rate": pytest.approx(1 / 14),
    }
    assert report["run_unknown_rate"] == {
        "numerator": 1,
        "denominator": 2,
        "rate": 0.5,
    }
    assert set(report["input_hashes"]) == {
        "events",
        "judgments",
        "issues",
        "costs",
        "coverage",
    }
    assert len(report["input_files"]) == 5


def test_uncovered_window_fails_with_exact_missing_ranges(scorecard_inputs):
    _write_json(
        scorecard_inputs["coverage"],
        {
            "sources": {
                "events": {"start": START, "end": "2026-07-15T00:00:00Z"},
                "judgments": {"start": "2026-07-05T00:00:00Z", "end": END},
                "issues": {"start": START, "end": END},
                "costs": {"start": START, "end": END},
            }
        },
    )

    result = _run(scorecard_inputs)

    assert result.returncode == 1
    assert (
        "events missing [2026-07-15T00:00:00Z,2026-08-01T00:00:00Z)"
        in result.stderr
    )
    assert (
        "judgments missing [2026-07-01T00:00:00Z,2026-07-05T00:00:00Z)"
        in result.stderr
    )


def test_window_older_than_raw_retention_fails_explicitly(scorecard_inputs):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--start",
            START,
            "--end",
            END,
            "--now",
            "2026-10-15T00:00:00Z",
            "--events",
            str(scorecard_inputs["events"]),
            "--judgments",
            str(scorecard_inputs["judgments"]),
            "--issues",
            str(scorecard_inputs["issues"]),
            "--costs",
            str(scorecard_inputs["costs"]),
            "--coverage",
            str(scorecard_inputs["coverage"]),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "run-events retention missing [2026-07-01T00:00:00Z" in result.stderr


def test_monthly_report_is_full_calendar_and_immutable(scorecard_inputs, tmp_path):
    monthly = tmp_path / "2026-07.json"
    first = _run(scorecard_inputs, "--monthly-out", str(monthly))
    assert first.returncode == 0, first.stderr
    original = monthly.read_bytes()
    assert json.loads(original)["input_hashes"]["events"] == hashlib.sha256(
        scorecard_inputs["events"].read_bytes()
    ).hexdigest()

    second = _run(scorecard_inputs, "--monthly-out", str(monthly))
    assert second.returncode == 0, second.stderr
    assert monthly.read_bytes() == original

    scorecard_inputs["costs"].write_text(
        scorecard_inputs["costs"].read_text(encoding="utf-8")
        + json.dumps(
            {
                "time": "2026-07-04T00:00:00Z",
                "stack": ["repo", "claude-sonnet"],
                "values": {"cost_microusd": 1},
                "labels": {"session": "session-1"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    changed = _run(scorecard_inputs, "--monthly-out", str(monthly))
    assert changed.returncode == 1
    assert "immutable monthly report already exists with different inputs" in changed.stderr


def test_events_are_validated_against_the_run_event_schema(scorecard_inputs):
    rows = [
        json.loads(line)
        for line in scorecard_inputs["events"].read_text(encoding="utf-8").splitlines()
    ]
    rows[0]["event_id"] = "not-a-uuid"
    rows[0]["unexpected"] = True
    _write_jsonl(scorecard_inputs["events"], rows)

    result = _run(scorecard_inputs)

    assert result.returncode == 1
    assert "events[0]" in result.stderr
    assert "schema" in result.stderr


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", 2),
        ("formula_version", "r6-v0"),
        ("matcher_version", "quoted-phrases-v0"),
        ("skill_content_hash", "not-a-sha256"),
        ("judge_model", ""),
        ("judge_prompt_version", "trigger-fit-v0"),
        ("eligibility_verdict", "maybe"),
        ("trigger_verdict", "sometimes"),
        ("timestamp_utc", "2026-07-01 00:10:00"),
        ("evidence_record_ids", []),
        ("unexpected", True),
    ],
)
def test_scorecard_rejects_invalid_frozen_judgment_fields(
    scorecard_inputs, field, value
):
    rows = [
        json.loads(line)
        for line in scorecard_inputs["judgments"]
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    rows[0][field] = value
    _write_jsonl(scorecard_inputs["judgments"], rows)

    result = _run(scorecard_inputs)

    assert result.returncode == 1
    assert "judgment" in result.stderr


def test_verified_join_identity_conflict_is_unknown(scorecard_inputs):
    rows = [
        json.loads(line)
        for line in scorecard_inputs["events"].read_text(encoding="utf-8").splitlines()
    ]
    gate = next(
        row
        for row in rows
        if row["run_id"] == RUN_1 and row["stage"] == "final-gate"
    )
    gate["issue_id"] = "different-issue"
    _write_jsonl(scorecard_inputs["events"], rows)

    result = _run(scorecard_inputs)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["verified_outcome_rate"]["numerator"] == 0
    assert report["run_unknown_rate"] == {
        "numerator": 2,
        "denominator": 2,
        "rate": 1.0,
    }
    assert report["run_join_unknowns"]["identity"] == 1


def test_verified_join_rejects_conflict_hidden_by_later_stage(scorecard_inputs):
    rows = [
        json.loads(line)
        for line in scorecard_inputs["events"].read_text(encoding="utf-8").splitlines()
    ]
    rows.insert(
        0,
        _event(
            RUN_1,
            "different-issue",
            "claim",
            "2026-07-01T00:59:00Z",
            repo_id="different-repo",
        ),
    )
    _write_jsonl(scorecard_inputs["events"], rows)

    result = _run(scorecard_inputs)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["verified_outcome_rate"]["numerator"] == 0
    assert report["run_join_unknowns"]["identity"] == 1


def test_prevention_rejects_asserted_path_without_commit_diff(scorecard_inputs):
    rows = [
        json.loads(line)
        for line in scorecard_inputs["events"].read_text(encoding="utf-8").splitlines()
    ]
    for row in rows:
        if row["run_id"] == RUN_1 and row["stage"] in {
            "reviewer-finding",
            "close",
        }:
            row["artifact_paths"] = ["README.md"]
    _write_jsonl(scorecard_inputs["events"], rows)

    result = _run(scorecard_inputs)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["prevention"]["numerator"] == 0


def test_prevention_requires_fixed_before_close(scorecard_inputs):
    rows = [
        json.loads(line)
        for line in scorecard_inputs["events"].read_text(encoding="utf-8").splitlines()
    ]
    disposition = next(
        row
        for row in rows
        if row["run_id"] == RUN_1 and row["stage"] == "finding-disposition"
    )
    disposition["timestamp_utc"] = "2026-07-01T06:01:00Z"
    _write_jsonl(scorecard_inputs["events"], rows)

    result = _run(scorecard_inputs)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["prevention"]["numerator"] == 0


def test_adoption_excludes_explicit_invocation_as_numerator(scorecard_inputs):
    result = _run(scorecard_inputs)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["adoption"]["numerator"] == 1
    assert report["adoption"]["denominator"] == 3


def test_delivery_blocked_and_deferred_count_only_status_transitions(scorecard_inputs):
    rows = [
        json.loads(line)
        for line in scorecard_inputs["events"].read_text(encoding="utf-8").splitlines()
    ]
    for row in rows:
        if row["run_id"] == RUN_2 and row["stage"] == "worker-verdict":
            row["disposition"] = "DONE"
    rows.append(
        _event(
            RUN_2,
            "issue-2",
            "status-transition",
            "2026-07-02T05:25:00Z",
            disposition="blocked",
        )
    )
    _write_jsonl(scorecard_inputs["events"], rows)

    result = _run(scorecard_inputs)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["delivery"]["done"] == 2
    assert report["delivery"]["blocked"] == 1
    assert report["delivery"]["deferred"] == 0


def test_prevention_uses_finding_disposition_commit_snapshot(scorecard_inputs):
    repo = scorecard_inputs["repo"]
    readme = repo / "README.md"
    if not readme.exists():
        readme.write_text("prevention fixture", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "unrelated prevention fixture")
    unrelated_commit = _git(repo, "rev-parse", "HEAD")
    base_for_close = _git(repo, "rev-parse", "HEAD~1")

    rows = [
        json.loads(line)
        for line in scorecard_inputs["events"].read_text(encoding="utf-8").splitlines()
    ]
    close = next(
        row
        for row in rows
        if row["run_id"] == RUN_1 and row["stage"] == "close"
    )
    close["base_commit"] = base_for_close
    close["result_commit"] = unrelated_commit
    close["artifact_paths"] = ["README.md"]
    _write_jsonl(scorecard_inputs["events"], rows)

    result = _run(scorecard_inputs)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["prevention"]["numerator"] == 1


def test_identity_must_be_consistent_across_findings_and_dispositions(scorecard_inputs):
    rows = [
        json.loads(line)
        for line in scorecard_inputs["events"].read_text(encoding="utf-8").splitlines()
    ]
    for row in rows:
        if row["run_id"] == RUN_1 and row["stage"] == "reviewer-finding":
            row["issue_id"] = "different-issue"
            row["repo_id"] = "different-repo"
    _write_jsonl(scorecard_inputs["events"], rows)

    result = _run(scorecard_inputs)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["run_join_unknowns"]["identity"] == 1


@pytest.mark.parametrize(
    "created_at",
    ["2026-07-01T06:01:00Z", "2026-08-02T00:00:00Z"],
)
def test_discovery_is_bounded_by_parent_close_and_window(
    scorecard_inputs, created_at
):
    issues = json.loads(scorecard_inputs["issues"].read_text(encoding="utf-8"))
    child = next(row for row in issues if row["id"] == "issue-child")
    child["created_at"] = created_at
    child["dependencies"][0]["created_at"] = created_at
    _write_json(scorecard_inputs["issues"], issues)

    result = _run(scorecard_inputs)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["discovery_ratio"]["numerator"] == 0


def test_discovery_with_unavailable_timing_is_unknown(scorecard_inputs):
    issues = json.loads(scorecard_inputs["issues"].read_text(encoding="utf-8"))
    child = next(row for row in issues if row["id"] == "issue-child")
    child.pop("created_at")
    child["dependencies"][0].pop("created_at")
    _write_json(scorecard_inputs["issues"], issues)

    result = _run(scorecard_inputs)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["discovery_ratio"]["numerator"] == 0
    assert report["unknown_counts"]["discovery"] == 1


def test_discovery_with_only_child_timing_is_unknown(scorecard_inputs):
    issues = json.loads(scorecard_inputs["issues"].read_text(encoding="utf-8"))
    child = next(row for row in issues if row["id"] == "issue-child")
    child["dependencies"][0].pop("created_at")
    _write_json(scorecard_inputs["issues"], issues)

    result = _run(scorecard_inputs)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["discovery_ratio"]["numerator"] == 0
    assert report["unknown_counts"]["discovery"] == 1


def test_input_inventory_keeps_each_file_identity_and_hash(
    scorecard_inputs, tmp_path
):
    second_events = tmp_path / "second-events.jsonl"
    second_events.write_text("", encoding="utf-8")

    result = _run(scorecard_inputs, "--events", str(second_events))

    assert result.returncode == 0, result.stderr
    inventory = [
        row
        for row in json.loads(result.stdout)["input_files"]
        if row["source"] == "events"
    ]
    assert inventory == sorted(inventory, key=lambda row: row["identity"])
    assert inventory == [
        {
            "source": "events",
            "identity": str(path.resolve()),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(
            [scorecard_inputs["events"], second_events],
            key=lambda path: str(path.resolve()),
        )
    ]


def test_finding_fingerprint_normalizes_locations_addresses_and_space(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--fingerprint",
            "critic",
            "R123",
            "agentic/work.py",
            "bad value at line 42:7 address 0x7ffeeabc   retry",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    second = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--fingerprint",
            "critic",
            "R123",
            "agentic/work.py",
            "bad value at line 900:2 address 0xabc retry",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert second.returncode == 0, second.stderr
    assert result.stdout.strip() == second.stdout.strip()
