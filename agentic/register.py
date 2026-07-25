"""Create-only registration of spec task definitions in bd."""

import hashlib
import json
import os
import re
from pathlib import Path

from agentic import bd
from agentic.bd import BdError
from agentic.lock import DEFAULT_ACQUIRE_TIMEOUT, RepoLock
from agentic.sync import repo_root

SCHEMA_VERSION = 1
EXTERNAL_REF_PREFIX = "spec-task:"

_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_DEPENDS_RE = re.compile(r"^Depends on:\s*(.*?)\s*$", re.MULTILINE)
_TOUCH_RE = re.compile(r"^Touch:\s*(.*?)\s*$", re.MULTILINE)
_BUDGET_RE = re.compile(r"^Budget:\s*(.*?)\s*$", re.MULTILINE)
_RIGOR_RE = re.compile(r"^Rigor:\s*(.*?)\s*$", re.MULTILINE)
_GOAL_RE = re.compile(
    r"^## Goal\s*$\n(?P<body>.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL
)
_NUMBER_RE = re.compile(r"^(\d+)")


class RegistrationConflict(BdError):
    """An existing issue or edge disagrees with a task definition."""


def _header(regex, text):
    match = regex.search(text)
    return match.group(1).strip() if match and match.group(1).strip() else None


def _repo_relative(path, root):
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(Path(root).resolve()).as_posix()
    except ValueError as exc:
        raise BdError(f"task path is outside the repository: {path}") from exc


def _dependency_paths(path, root, text):
    raw = _header(_DEPENDS_RE, text)
    if raw is None or raw.lower() == "none":
        return []

    task_dir = Path(path).parent
    by_number = {}
    for sibling in task_dir.glob("*.md"):
        match = _NUMBER_RE.match(sibling.name)
        if match:
            number = int(match.group(1))
            if number in by_number:
                raise BdError(
                    f"duplicate task number {number:02d} in {task_dir}"
                )
            by_number[number] = sibling

    paths = []
    for token in (part.strip() for part in raw.split(",")):
        if not token:
            continue
        if token.isdigit():
            target = by_number.get(int(token))
            if target is None:
                raise BdError(f"{path}: unresolved dependency {token}")
        else:
            candidate = Path(token)
            if candidate.is_absolute():
                target = candidate
            elif token.startswith("specs/"):
                target = Path(root) / candidate
            else:
                target = task_dir / candidate
            if not target.is_file():
                raise BdError(f"{path}: unresolved dependency {token}")
        paths.append(_repo_relative(target, root))
    return sorted(set(paths))


def parse_task(path, root):
    """Read the definition fields from one task, deliberately ignoring Status."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    title = _header(_TITLE_RE, text)
    goal_match = _GOAL_RE.search(text)
    goal = goal_match.group("body").strip() if goal_match else None
    if not title or not goal:
        raise BdError(f"{path}: task requires a title and ## Goal")

    rel = _repo_relative(path, root)
    touch = _header(_TOUCH_RE, text)
    prerequisite_paths = _dependency_paths(path, root, text)
    return {
        "schema_version": SCHEMA_VERSION,
        "path": rel,
        "title": title,
        "goal": goal,
        "touch": sorted(
            item.strip() for item in (touch or "").split(",") if item.strip()
        ),
        "budget": _header(_BUDGET_RE, text),
        "rigor": _header(_RIGOR_RE, text) or "production",
        "prerequisites": [
            EXTERNAL_REF_PREFIX + dependency for dependency in prerequisite_paths
        ],
    }


def definition_hash(task):
    """SHA-256 of the task's canonical compact, sorted-key JSON definition."""
    payload = json.dumps(task, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _all_issues(root):
    raw = bd._run(["list", "--all", "--json", "--limit", "0"], cwd=str(root))
    rows = json.loads(raw or "[]")
    return rows if isinstance(rows, list) else []


def _metadata(issue):
    value = issue.get("metadata") or {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def _initial_metadata(task):
    return {
        "budget": task["budget"],
        "definition_hash": definition_hash(task),
        "rigor": task["rigor"],
        "registration_state": "pending",
        "source": task["path"],
        "touch": task["touch"],
    }


def _create_issue(task, root):
    metadata = _initial_metadata(task)
    external_ref = EXTERNAL_REF_PREFIX + task["path"]
    issue_id = bd._run(
        [
            "create",
            task["title"],
            "--silent",
            "--type",
            "task",
            "--description",
            task["goal"],
            "--external-ref",
            external_ref,
            "--metadata",
            json.dumps(metadata, sort_keys=True, separators=(",", ":")),
        ],
        cwd=str(root),
    ).strip()
    return issue_id


def _add_edge(issue_id, prerequisite_id, root):
    bd._run(
        ["dep", "add", issue_id, prerequisite_id, "--type", "blocks"],
        cwd=str(root),
    )


def _mark_complete(issue_id, root):
    bd._run(
        ["update", issue_id, "--set-metadata", "registration_state=complete"],
        cwd=str(root),
    )


def _edge_tuples(issues):
    edges = set()
    for issue in issues:
        for edge in issue.get("dependencies", []) or []:
            edges.add(
                (
                    edge.get("issue_id"),
                    edge.get("depends_on_id"),
                    edge.get("type") or "blocks",
                )
            )
    return edges


def _register_under_lock(tasks, root):
    by_ref = {}
    for issue in _all_issues(root):
        external_ref = issue.get("external_ref")
        if not external_ref:
            continue
        if external_ref in by_ref:
            raise RegistrationConflict(
                f"{external_ref}: multiple existing issues use this external reference"
            )
        by_ref[external_ref] = issue

    for task in tasks:
        external_ref = EXTERNAL_REF_PREFIX + task["path"]
        issue = by_ref.get(external_ref)
        if issue is None:
            continue
        metadata = _metadata(issue)
        actual_hash = metadata.get("definition_hash")
        expected_hash = definition_hash(task)
        if actual_hash != expected_hash:
            raise RegistrationConflict(
                f"{external_ref}: definition hash conflict "
                f"(existing {actual_hash!r}, expected {expected_hash!r})"
            )
        state = metadata.get("registration_state")
        if state not in {"pending", "complete"}:
            raise RegistrationConflict(
                f"{external_ref}: invalid registrar state {state!r}"
            )

    for task in tasks:
        external_ref = EXTERNAL_REF_PREFIX + task["path"]
        if external_ref in by_ref:
            continue
        issue_id = _create_issue(task, root)
        by_ref[external_ref] = {
            "id": issue_id,
            "external_ref": external_ref,
            "metadata": _initial_metadata(task),
        }

    issues = _all_issues(root)
    by_ref = {
        issue["external_ref"]: issue
        for issue in issues
        if issue.get("external_ref")
    }
    edges = _edge_tuples(issues)

    ordered_issues = []
    missing_edges = []
    for task in tasks:
        task_ref = EXTERNAL_REF_PREFIX + task["path"]
        issue = by_ref[task_ref]
        ordered_issues.append(issue)
        expected_edges = []
        for prerequisite_ref in task["prerequisites"]:
            prerequisite = by_ref.get(prerequisite_ref)
            if prerequisite is None:
                raise RegistrationConflict(
                    f"{task_ref}: prerequisite is not registered: {prerequisite_ref}"
                )
            expected_edges.append((issue["id"], prerequisite["id"], "blocks"))

        for expected in expected_edges:
            related = {
                edge
                for edge in edges
                if {edge[0], edge[1]} == {expected[0], expected[1]}
            }
            if related and related != {expected}:
                rendered = ", ".join(
                    f"{source}->{target}:{kind}"
                    for source, target, kind in sorted(related)
                )
                raise RegistrationConflict(
                    f"{task_ref}: conflicting edge exists: {rendered}"
                )
            if expected not in edges:
                missing_edges.append(expected)

    for edge in missing_edges:
        _add_edge(edge[0], edge[1], root)
    for issue in ordered_issues:
        if _metadata(issue).get("registration_state") != "complete":
            _mark_complete(issue["id"], root)

    return len(tasks)


def register_spec(spec_dir, *, store_cwd=None, acquire_timeout=None):
    """Register every task in ``spec_dir`` under the repository write lock."""
    root = (
        Path(store_cwd).resolve()
        if store_cwd is not None
        else repo_root(os.getcwd()).resolve()
    )
    spec_dir = Path(spec_dir)
    if not spec_dir.is_absolute():
        spec_dir = root / spec_dir
    tasks_dir = spec_dir / "tasks"
    if not tasks_dir.is_dir():
        raise BdError(f"spec directory has no tasks/: {spec_dir}")
    tasks = [parse_task(path, root) for path in sorted(tasks_dir.glob("*.md"))]
    timeout = (
        DEFAULT_ACQUIRE_TIMEOUT if acquire_timeout is None else acquire_timeout
    )
    with RepoLock(root, acquire_timeout=timeout):
        return _register_under_lock(tasks, root)


def run(args):
    count = register_spec(args.spec_dir)
    print(f"register-spec: {count} task(s) registered")
    return 0
