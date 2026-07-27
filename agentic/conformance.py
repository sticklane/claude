"""Validate completed native-orchestration traces without orchestrating work."""

from __future__ import annotations

import ast
import functools
import json
from pathlib import Path
from typing import Any, Mapping

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "orchestration-trace.json"
ISOLATION_BY_RUNTIME = {
    "claude-code": "worktree",
    "codex": "worktree",
    "antigravity": "new-project",
}
_ALLOWED_IMPORTS = {"ast", "functools", "json", "jsonschema"}
_ALLOWED_FROM_IMPORTS = {
    "__future__": {"annotations"},
    "pathlib": {"Path"},
    "typing": {"Any", "Mapping"},
}
_ALLOWED_BUILTIN_CALLS = {
    "dict",
    "enumerate",
    "isinstance",
    "len",
    "list",
    "min",
    "set",
    "sorted",
    "str",
    "sum",
    "super",
}
_ALLOWED_LIBRARY_CALLS = {
    "Path",
    "ast.parse",
    "ast.Module",
    "ast.walk",
    "ast.iter_child_nodes",
    "functools.lru_cache",
    "jsonschema.Draft202012Validator",
}
_TRUSTED_HELPER_LIBRARY_CALLS = {
    *list(_ALLOWED_LIBRARY_CALLS),
    "json.loads",
}
_ALLOWED_METHOD_CALLS = {
    "_ALLOWED_FROM_IMPORTS.get",
    "SCHEMA_PATH.read_text",
    "Path().resolve",
    "_CallVisitor().visit",
    "_trace_validator().iter_errors",
    "ancestors.add",
    "source_path.resolve",
    "claim.get",
    "cleanup.get",
    "event.get",
    "event_ids.add",
    "isolation.get",
    "name.rsplit",
    "self.generic_visit",
    "work.extend",
    "work.pop",
    "name.split",
    "names.add",
    "reviewer_sessions.add",
    "reviewers.add",
    "blocked_reviewer_sessions.add",
    "screening.get",
    "source_path.read_text",
    "super().__init__",
    "trace.get",
    "violations.append",
}


class ConformanceError(ValueError):
    """A normalized trace violates the native-orchestration contract."""

    def __init__(self, transition: str, detail: str) -> None:
        self.transition = transition
        super().__init__(f"{transition}: {detail}")


class AuthorityError(ValueError):
    """A conformance helper contains orchestration authority."""


@functools.lru_cache(maxsize=1)
def _trace_validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


def _schema_transition(error: jsonschema.ValidationError, trace: object) -> str:
    path = list(error.absolute_path)
    if (
        len(path) >= 2
        and path[0] == "events"
        and isinstance(path[1], int)
        and isinstance(trace, Mapping)
    ):
        events = trace.get("events")
        if isinstance(events, list) and path[1] < len(events):
            event = events[path[1]]
            if isinstance(event, Mapping) and isinstance(event.get("stage"), str):
                return str(event["stage"])
    return "schema"


def _validated_document(trace: Mapping[str, Any]) -> dict[str, Any]:
    candidate = dict(trace)
    errors = sorted(
        _trace_validator().iter_errors(candidate),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        error = errors[0]
        raise ConformanceError(_schema_transition(error, candidate), error.message)
    return candidate


def _validate_event_identities(run_id: str, events: list[dict[str, Any]]) -> None:
    event_ids: set[str] = set()
    for event in events:
        if event["run_id"] != run_id:
            raise ConformanceError(
                event["stage"],
                f"event run {event['run_id']!r} does not match trace run {run_id!r}",
            )
        event_id = event["event_id"]
        if event_id in event_ids:
            raise ConformanceError(event["stage"], f"duplicate event id {event_id!r}")
        event_ids.add(event_id)


def _validate_parent_ancestry(events: list[dict[str, Any]]) -> None:
    ancestors: set[str] = set()
    for index, event in enumerate(events):
        parent_event_id = event["parent_event_id"]
        if index == 0:
            if parent_event_id is not None:
                raise ConformanceError("ready", "the first event cannot have a parent")
        elif parent_event_id not in ancestors:
            raise ConformanceError(
                event["stage"],
                f"parent event {parent_event_id!r} is not an earlier trace event",
            )
        ancestors.add(event["event_id"])


def validate_trace(trace: Mapping[str, Any]) -> dict[str, Any]:
    """Return a valid trace or raise at the first violated transition."""
    if not isinstance(trace, Mapping):
        raise ConformanceError("schema", "trace must be an object")
    candidate = _validated_document(trace)
    run_id = candidate["run_id"]
    runtime = candidate["runtime"]
    events = candidate["events"]
    _validate_event_identities(run_id, events)

    if sum(event["stage"] == "final-gate" for event in events) != 1:
        raise ConformanceError("final-gate", "exactly one final gate is required")

    index = 0

    def consume(stage: str, outcome: str) -> dict[str, Any]:
        nonlocal index
        if index >= len(events):
            raise ConformanceError(stage, "event is missing")
        event = events[index]
        if event["stage"] != stage:
            raise ConformanceError(
                stage,
                f"expected {stage!r}, received {event['stage']!r}",
            )
        if event["outcome"] != outcome:
            raise ConformanceError(
                stage,
                f"expected outcome {outcome!r}, received {event['outcome']!r}",
            )
        index += 1
        return event

    consume("ready", "ready")
    claim = consume("claim", "claimed")
    if claim.get("atomic") is not True:
        raise ConformanceError("claim", "claim must be atomic")

    screening = consume("prompt-screening", "passed")
    if screening.get("compact") is not True or screening.get("screened") is not True:
        raise ConformanceError(
            "prompt-screening",
            "prompt must be compact and screened before dispatch",
        )

    isolation = consume("isolation", "isolated")
    expected_isolation = ISOLATION_BY_RUNTIME[runtime]
    if isolation.get("method") != expected_isolation:
        raise ConformanceError(
            "isolation",
            f"{runtime} requires isolation method {expected_isolation!r}",
        )

    consume("write-boundary", "allowed")
    worker_verdict = consume("worker-verdict", "DONE")
    pre_review_sessions = {
        event.get("session_id")
        for event in events[:index]
        if event.get("session_id")
    }
    blocked_reviewer_sessions = set(pre_review_sessions)
    blocked_reviewer_sessions.add(worker_verdict["session_id"])

    reviewers: set[str] = set()
    reviewer_sessions: set[str] = set()
    while index < len(events) and events[index]["stage"] == "review":
        event = events[index]
        index += 1
        if event["outcome"] != "accepted":
            raise ConformanceError("review-barrier", "every reviewer must accept")
        reviewer = event.get("reviewer")
        if reviewer in reviewers:
            raise ConformanceError("review-barrier", f"duplicate reviewer {reviewer!r}")
        if event["parent_event_id"] != worker_verdict["event_id"]:
            raise ConformanceError(
                "review-barrier",
                "reviewers must share the worker verdict as their parent",
            )
        session_id = event["session_id"]
        if session_id in reviewer_sessions:
            raise ConformanceError(
                "review-barrier",
                "verifier and critic must run in distinct sessions",
            )
        if session_id in blocked_reviewer_sessions:
            raise ConformanceError(
                "review-barrier",
                "verifier and critic cannot reuse pre-review or worker sessions",
            )
        reviewers.add(reviewer)
        reviewer_sessions.add(session_id)
    if reviewers != {"verifier", "critic"}:
        raise ConformanceError(
            "review-barrier",
            "verifier and critic acceptance are both required",
        )

    consume("final-gate", "passed")
    consume("merge", "merged")
    consume("close", "closed")
    cleanup = consume("cleanup", "complete")
    if (
        cleanup.get("worktree_removed") is not True
        or cleanup.get("claim_released") is not True
    ):
        raise ConformanceError(
            "cleanup",
            "worktree removal and claim release are both required",
        )
    if index != len(events):
        raise ConformanceError("complete", "events remain after cleanup")
    _validate_parent_ancestry(events)
    return candidate


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return f"{_call_name(node.func)}()"
    return ""


def _collect_target_names(node: ast.AST, names: set[str]) -> None:
    if isinstance(node, ast.Name):
        names.add(node.id)
    elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for element in node.elts:
            _collect_target_names(element, names)
    elif isinstance(node, ast.Starred):
        _collect_target_names(node.value, names)


def _assigned_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    work = [node]
    while work:
        current = work.pop()
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        if isinstance(current, ast.arg):
            names.add(current.arg)
        elif isinstance(current, ast.Assign):
            for target in current.targets:
                _collect_target_names(target, names)
        elif isinstance(current, ast.AnnAssign):
            _collect_target_names(current.target, names)
        elif isinstance(current, ast.AugAssign):
            _collect_target_names(current.target, names)
        elif isinstance(current, ast.NamedExpr):
            _collect_target_names(current.target, names)
        elif isinstance(current, ast.ExceptHandler) and current.name:
            names.add(current.name)
        elif isinstance(current, ast.withitem):
            if current.optional_vars is not None:
                _collect_target_names(current.optional_vars, names)
        elif isinstance(current, (ast.For, ast.AsyncFor, ast.comprehension)):
            _collect_target_names(current.target, names)
        work.extend(ast.iter_child_nodes(current))
    return names


def _disallowed_shadowed_allowlist_calls(
    name: str,
    trusted_bindings: set[str],
    allowed_library_calls: set[str],
) -> bool:
    if name in _ALLOWED_METHOD_CALLS or name in allowed_library_calls:
        root = name.split(".", 1)[0]
        return root in trusted_bindings
    return False


def _allowed_call(
    name: str,
    local_callables: set[str],
    trusted_bindings: set[str],
    allowed_library_calls: set[str],
) -> bool:
    if _disallowed_shadowed_allowlist_calls(
        name, trusted_bindings, allowed_library_calls
    ):
        return False
    if name in local_callables:
        return True
    if name in _ALLOWED_BUILTIN_CALLS or name in allowed_library_calls:
        return True
    return name in _ALLOWED_METHOD_CALLS


def validate_helper_authority(path: str | Path | None = None) -> None:
    """Reject production helpers that exceed the pure validator allowlist."""
    source_path = Path(path) if path is not None else Path(__file__)
    trusted = source_path.resolve() == Path(__file__).resolve()
    allowed_library_calls = (
        _TRUSTED_HELPER_LIBRARY_CALLS if trusted else _ALLOWED_LIBRARY_CALLS
    )

    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    violations: list[tuple[int, str]] = []
    module_callables = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    module_bindings = _assigned_names(tree)
    trusted_bindings = module_bindings if not trusted else set()

    def _validate_calls(
        statements: list[ast.stmt],
        local_callables: set[str],
        trusted_bindings: set[str],
    ) -> None:
        class _CallVisitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                call_name = _call_name(node.func)
                if not _allowed_call(
                    call_name,
                    local_callables,
                    trusted_bindings,
                    allowed_library_calls,
                ):
                    violations.append((node.lineno, call_name))
                self.generic_visit(node)

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                _validate_calls(
                    node.body,
                    local_callables | {node.name},
                    trusted_bindings,
                )

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                _validate_calls(
                    node.body,
                    local_callables | {node.name},
                    trusted_bindings,
                )

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                _validate_calls(
                    node.body,
                    local_callables | {node.name},
                    trusted_bindings,
                )

        _CallVisitor().visit(ast.Module(body=statements, type_ignores=[]))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in _ALLOWED_IMPORTS or alias.asname is not None:
                    violations.append((node.lineno, f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            allowed_names = _ALLOWED_FROM_IMPORTS.get(node.module or "", set())
            for alias in node.names:
                if (
                    node.level != 0
                    or alias.name not in allowed_names
                    or alias.asname is not None
                ):
                    module = "." * node.level + (node.module or "")
                    violations.append(
                        (node.lineno, f"from {module} import {alias.name}")
                    )

    _validate_calls(tree.body, module_callables, trusted_bindings)
    if violations:
        line, symbol = min(violations)
        raise AuthorityError(
            f"{source_path}:{line}: orchestration authority is forbidden: {symbol}"
        )
