"""Contract tests for normalized native-orchestration traces."""

from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agentic import conformance  # noqa: E402


PROFILE_SURFACES = {
    "claude-code": (
        REPO_ROOT / "runtimes" / "claude-code.md",
        "worktree: true",
        "worktree",
    ),
    "codex": (
        REPO_ROOT / "runtimes" / "codex.md",
        "explicit git worktree",
        "worktree",
    ),
    "antigravity": (
        REPO_ROOT / "runtimes" / "antigravity.md",
        "--new-project",
        "new-project",
    ),
}

_PREVIOUS_EVENT = object()


class FakeRuntimeCallbacks:
    def __init__(self, runtime: str, repo: Path) -> None:
        profile_path, isolation_marker, isolation_method = PROFILE_SURFACES[runtime]
        profile = profile_path.read_text(encoding="utf-8")
        if isolation_marker not in profile:
            raise AssertionError(
                f"{profile_path} no longer exposes {isolation_marker!r}"
            )
        self.runtime = runtime
        self.repo = repo
        self.profile_path = profile_path
        self.isolation_method = isolation_method
        self.run_id = f"run-{runtime}-fixture"
        self.orchestrator_session_id = f"session-{runtime}-orchestrator"
        self.events: list[dict] = []

    def emit(
        self,
        stage: str,
        outcome: str,
        *,
        session_id: str | None = None,
        parent_event_id: object = _PREVIOUS_EVENT,
        **fields: object,
    ) -> dict:
        if parent_event_id is _PREVIOUS_EVENT:
            parent_event_id = self.events[-1]["event_id"] if self.events else None
        event = {
            "event_id": f"{self.run_id}:event-{len(self.events) + 1}",
            "run_id": self.run_id,
            "session_id": session_id or self.orchestrator_session_id,
            "parent_event_id": parent_event_id,
            "stage": stage,
            "outcome": outcome,
            **fields,
        }
        self.events.append(event)
        return event

    def ready(self) -> None:
        if not (self.repo / ".git").is_dir():
            raise AssertionError(f"{self.repo} is not an isolated fixture repository")
        self.emit("ready", "ready")

    def claim(self) -> None:
        self.emit("claim", "claimed", atomic=True)

    def screen_prompt(self) -> None:
        self.emit("prompt-screening", "passed", compact=True, screened=True)

    def isolate(self) -> None:
        (self.repo / ".fake-native-isolation").mkdir()
        self.emit("isolation", "isolated", method=self.isolation_method)

    def allow_write(self) -> None:
        self.emit("write-boundary", "allowed")

    def worker_verdict(self) -> dict:
        return self.emit(
            "worker-verdict",
            "DONE",
            session_id=f"session-{self.runtime}-worker",
        )

    def review(self, reviewer: str, parent_event_id: str) -> None:
        self.emit(
            "review",
            "accepted",
            reviewer=reviewer,
            session_id=f"session-{self.runtime}-{reviewer}",
            parent_event_id=parent_event_id,
        )

    def final_gate(self) -> None:
        self.emit("final-gate", "passed")

    def merge(self) -> None:
        self.emit("merge", "merged")

    def close(self) -> None:
        self.emit("close", "closed")

    def cleanup(self) -> None:
        self.emit(
            "cleanup",
            "complete",
            worktree_removed=True,
            claim_released=True,
        )

    def trace(self) -> dict:
        return {
            "schema_version": 1,
            "run_id": self.run_id,
            "runtime": self.runtime,
            "events": self.events,
        }


def _happy_trace(runtime: str, tmp_path: Path) -> tuple[dict, FakeRuntimeCallbacks]:
    repo = tmp_path / runtime
    subprocess.run(
        ["git", "init", "--quiet", str(repo)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    callbacks = FakeRuntimeCallbacks(runtime, repo)
    callbacks.ready()
    callbacks.claim()
    callbacks.screen_prompt()
    callbacks.isolate()
    callbacks.allow_write()
    worker = callbacks.worker_verdict()
    callbacks.review("verifier", worker["event_id"])
    callbacks.review("critic", worker["event_id"])
    callbacks.final_gate()
    callbacks.merge()
    callbacks.close()
    callbacks.cleanup()
    return callbacks.trace(), callbacks


def _event(trace: dict, stage: str, reviewer: str | None = None) -> dict:
    matches = [
        event
        for event in trace["events"]
        if event["stage"] == stage
        and (reviewer is None or event.get("reviewer") == reviewer)
    ]
    assert len(matches) == 1
    return matches[0]


@pytest.mark.parametrize("runtime", tuple(PROFILE_SURFACES))
def test_each_runtime_profile_emits_happy_path_in_temp_repo(runtime, tmp_path):
    trace, callbacks = _happy_trace(runtime, tmp_path)

    assert callbacks.repo.parent == tmp_path
    assert callbacks.profile_path.is_file()
    assert conformance.validate_trace(trace) == trace


@pytest.mark.parametrize("runtime", tuple(PROFILE_SURFACES))
@pytest.mark.parametrize(
    ("name", "mutate", "transition"),
    [
        (
            "lock-contention",
            lambda trace: _event(trace, "claim").update(outcome="contended"),
            "claim",
        ),
        (
            "malformed-verdict",
            lambda trace: _event(trace, "worker-verdict").update(outcome="MAYBE"),
            "worker-verdict",
        ),
        (
            "missing-verdict",
            lambda trace: trace["events"].remove(_event(trace, "worker-verdict")),
            "worker-verdict",
        ),
        (
            "denied-write",
            lambda trace: _event(trace, "write-boundary").update(outcome="denied"),
            "write-boundary",
        ),
        (
            "reviewer-rejection",
            lambda trace: _event(trace, "review", "verifier").update(
                outcome="rejected"
            ),
            "review-barrier",
        ),
        (
            "final-gate-failure",
            lambda trace: _event(trace, "final-gate").update(outcome="failed"),
            "final-gate",
        ),
        (
            "interrupted-cleanup",
            lambda trace: _event(trace, "cleanup").update(
                outcome="interrupted", claim_released=False
            ),
            "cleanup",
        ),
    ],
)
def test_named_negative_trace_fails_at_exact_transition(
    runtime, tmp_path, name, mutate, transition
):
    trace, _callbacks = _happy_trace(runtime, tmp_path)
    mutate(trace)

    with pytest.raises(conformance.ConformanceError) as raised:
        conformance.validate_trace(trace)

    assert raised.value.transition == transition, name


@pytest.mark.parametrize("runtime", tuple(PROFILE_SURFACES))
def test_runtime_requires_its_native_isolation(runtime, tmp_path):
    trace, _callbacks = _happy_trace(runtime, tmp_path)
    _event(trace, "isolation")["method"] = "shared-checkout"

    with pytest.raises(conformance.ConformanceError) as raised:
        conformance.validate_trace(trace)

    assert raised.value.transition == "isolation"


def test_review_barrier_accepts_parallel_completion_order(tmp_path):
    trace, _callbacks = _happy_trace("codex", tmp_path)
    verifier = trace["events"].index(_event(trace, "review", "verifier"))
    critic = trace["events"].index(_event(trace, "review", "critic"))
    trace["events"][verifier], trace["events"][critic] = (
        trace["events"][critic],
        trace["events"][verifier],
    )

    assert conformance.validate_trace(trace) == trace


def test_review_barrier_requires_distinct_reviewer_sessions(tmp_path):
    trace, _callbacks = _happy_trace("codex", tmp_path)
    verifier = _event(trace, "review", "verifier")
    _event(trace, "review", "critic")["session_id"] = verifier["session_id"]

    with pytest.raises(conformance.ConformanceError) as raised:
        conformance.validate_trace(trace)

    assert raised.value.transition == "review-barrier"


def test_review_barrier_rejects_reviewer_session_reuse_of_worker(tmp_path):
    trace, _callbacks = _happy_trace("codex", tmp_path)
    worker = _event(trace, "worker-verdict")
    _event(trace, "review", "critic")["session_id"] = worker["session_id"]

    with pytest.raises(conformance.ConformanceError) as raised:
        conformance.validate_trace(trace)

    assert raised.value.transition == "review-barrier"


def test_review_barrier_rejects_reviewer_session_reuse_of_preamble(tmp_path):
    trace, _callbacks = _happy_trace("codex", tmp_path)
    ready = _event(trace, "ready")
    _event(trace, "review", "critic")["session_id"] = ready["session_id"]

    with pytest.raises(conformance.ConformanceError) as raised:
        conformance.validate_trace(trace)

    assert raised.value.transition == "review-barrier"


def test_review_barrier_requires_worker_verdict_as_shared_parent(tmp_path):
    trace, _callbacks = _happy_trace("claude-code", tmp_path)
    _event(trace, "review", "critic")["parent_event_id"] = _event(
        trace, "write-boundary"
    )["event_id"]

    with pytest.raises(conformance.ConformanceError) as raised:
        conformance.validate_trace(trace)

    assert raised.value.transition == "review-barrier"


def test_event_run_identity_must_match_trace_run(tmp_path):
    trace, _callbacks = _happy_trace("antigravity", tmp_path)
    claim = _event(trace, "claim")
    claim["run_id"] = "another-run"

    with pytest.raises(conformance.ConformanceError) as raised:
        conformance.validate_trace(trace)

    assert raised.value.transition == "claim"


def test_event_ids_must_be_unique_within_the_trace(tmp_path):
    trace, _callbacks = _happy_trace("antigravity", tmp_path)
    _event(trace, "claim")["event_id"] = _event(trace, "ready")["event_id"]

    with pytest.raises(conformance.ConformanceError) as raised:
        conformance.validate_trace(trace)

    assert raised.value.transition == "claim"


def test_exactly_one_final_gate_is_required(tmp_path):
    trace, _callbacks = _happy_trace("claude-code", tmp_path)
    gate = _event(trace, "final-gate")
    duplicate = copy.deepcopy(gate)
    duplicate["event_id"] = f"{trace['run_id']}:duplicate-gate"
    trace["events"].insert(trace["events"].index(gate) + 1, duplicate)

    with pytest.raises(conformance.ConformanceError) as raised:
        conformance.validate_trace(trace)

    assert raised.value.transition == "final-gate"


def test_cleanup_requires_worktree_and_claim_cleanup(tmp_path):
    trace, _callbacks = _happy_trace("antigravity", tmp_path)
    _event(trace, "cleanup")["worktree_removed"] = False

    with pytest.raises(conformance.ConformanceError) as raised:
        conformance.validate_trace(trace)

    assert raised.value.transition == "cleanup"


def test_production_helper_has_only_pure_validator_authority():
    assert conformance.validate_helper_authority() is None


@pytest.mark.parametrize(
    ("source", "symbol"),
    [
        (
            "import os\n"
            "def validate():\n"
            "    return os.system('native-agent --run')\n",
            "import os",
        ),
        (
            "import asyncio\n"
            "def validate(task):\n"
            "    return asyncio.create_task(task)\n",
            "import asyncio",
        ),
        (
            "def validate():\n"
            "    return __import__('subprocess').run(['native-agent'])\n",
            "__import__",
        ),
        (
            "import concurrent.futures\n"
            "def validate(job):\n"
            "    return concurrent.futures.ThreadPoolExecutor().submit(job)\n",
            "import concurrent.futures",
        ),
        (
            "import json\n"
            "def validate(json):\n"
            "    return json.loads('{\"a\": 1}')\n",
            "json.loads",
        ),
        (
            "from pathlib import Path\n"
            "SCHEMA_PATH = Path('agentic')\n"
            "def validate():\n"
            "    SCHEMA_PATH = 'not-a-path'\n"
            "    return SCHEMA_PATH.read_text()\n",
            "SCHEMA_PATH.read_text",
        ),
    ],
)
def test_helper_authority_rejects_launch_and_scheduling_bypasses(
    tmp_path, source, symbol
):
    helper = tmp_path / "bad_helper.py"
    helper.write_text(source, encoding="utf-8")

    with pytest.raises(conformance.AuthorityError, match=symbol):
        conformance.validate_helper_authority(helper)
