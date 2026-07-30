#!/usr/bin/env python3
"""Fail-closed registration repair driver.

This module deliberately does not import ``agentic register-spec`` or ``bd``.
Live execution is possible only through an absolute, capability-certified
Task-00D authority subprocess speaking the closed JSON protocol below.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import sys
import time
from typing import Any, Callable, Iterable, Mapping, Protocol


SCHEMA = "agentic.registration-repair/v1"
ADAPTER_PROTOCOL = "agentic.registration-authority-subprocess/v1"
RESPONSE_SCHEMA = "agentic.registration-authority-response/v1"
EVENT_SCHEMA = "agentic.registration-migration/v1"
HEAD_SCHEMA = "agentic.registration-migration-head/v1"
WORKSET_SCHEMA = "agentic.workset-extension/v1"
TASK_PREFIX = "specs/mardi-gras-agentic-integration/tasks/"
PHASES = (
    "source_attested",
    "bootstrap_verified",
    "authority_schema_installed",
    "review_recorded",
    "tracker_attested",
    "created",
    "wired",
    "registered",
    "task01_wired",
    "redirected",
    "manual_blocked",
    "container_verified",
    "prepared",
    "released",
)
MUTATING_PHASES = {
    "authority_schema_installed",
    "review_recorded",
    "created",
    "wired",
    "registered",
    "task01_wired",
    "redirected",
    "manual_blocked",
    "released",
}
REQUIRED_CAPABILITIES = (
    "authority_identity_no_migrate",
    "authority_schema_install",
    "revision_conditional_create",
    "revision_conditional_edges",
    "registration_state_transition",
    "supersession_redirect",
    "manual_block",
    "revision_conditional_release",
)
TOP_KEYS = {
    "schema",
    "source_date_utc",
    "spec",
    "authority",
    "phases",
    "feature_container",
    "retained",
    "bootstrap",
    "historical",
    "replacements",
    "known_external_rewires",
    "manual_blockers",
    "workset_extension",
    "attestation",
}
ATTESTATION_KEYS = {
    "source_commit",
    "bootstrap_source_commit",
    "bootstrap_attestation_commit",
    "spec_sha256",
    "human_sha256",
    "definition_hash",
    "bootstrap_receipt_sha256",
    "task01_live_fields_sha256",
    "starting_tracker_snapshot",
}
EXPECTED_HISTORICAL = {
    "02-build-launch-supervisor.md": "15-build-launch-supervisor-v2.md",
    "03-evolve-run-events-v2.md": "16-evolve-run-events-v2-repair.md",
    "04-instrument-native-facades.md": "38-instrument-child-lifecycle-canaries.md",
    "05-project-live-activity.md": "18-project-live-activity-repair.md",
    "06-package-and-launch-live.md": "39-activate-live-runtime-canaries.md",
    "07-prove-installed-native-facades.md": "26-prove-final-installed-native-facades.md",
    "08-implement-cutover-receipt.md": "20-implement-cutover-receipt-repair.md",
    "09-add-mardi-gras-provider.md": "21-add-mardi-gras-provider-repair.md",
    "10-prove-terminal-journeys.md": "23-document-agentic-live-repair.md",
    "11-make-workboard-read-only.md": "24-make-workboard-read-only-repair.md",
    "12-certify-production-cutover.md": "27-certify-production-cutover-repair.md",
}
EXPECTED_BOOTSTRAP = (
    "00-add-beads-authority-core.md",
    "00-add-beads-conditional-authority.md",
    "00-add-beads-supersession-authority.md",
    "00-install-beads-authorizer-bootstrap.md",
)
EXPECTED_EXTERNAL = (
    ("agentic-2nj.5", "agentic-njk", "19-package-and-launch-live-repair.md", "package_only_exception"),
    ("agentic-868.9", "agentic-tg1", "26-prove-final-installed-native-facades.md", "ordinary_redirect"),
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HEADER_RE = re.compile(r"^([^:\n]+):[ \t]*(.*)$", re.MULTILINE)


class MigrationError(RuntimeError):
    """A typed, user-facing fail-closed error."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise MigrationError("noncanonical_json", str(exc)) from exc


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exact_keys(value: Mapping[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    if actual != expected:
        raise MigrationError(
            "manifest_schema",
            f"{where} keys differ; missing={sorted(expected-actual)!r} unknown={sorted(actual-expected)!r}",
        )


def _as_dict(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MigrationError("manifest_schema", f"{where} must be an object")
    return value


def _as_list(value: Any, where: str) -> list[Any]:
    if not isinstance(value, list):
        raise MigrationError("manifest_schema", f"{where} must be an array")
    return value


def _repo_root(manifest_path: Path) -> Path:
    resolved = manifest_path.resolve()
    for parent in (resolved.parent, *resolved.parents):
        if (parent / ".git").exists() or (parent / "AGENTS.md").exists():
            return parent
    raise MigrationError("source_root", "cannot locate repository root")


def _task_number(path: str) -> int:
    match = re.match(rf"^{re.escape(TASK_PREFIX)}(\d+)-", path)
    if not match:
        raise MigrationError("manifest_graph", f"noncanonical task path {path!r}")
    return int(match.group(1))


def _task_headers(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    headers = {key: value for key, value in HEADER_RE.findall(text)}
    required = {"Status", "Depends on", "Priority", "Budget", "Spec", "Touch"}
    if not required <= set(headers):
        raise MigrationError("task_definition", f"{path}: missing headers {sorted(required-set(headers))}")
    if "\r" in text or not text.endswith("\n"):
        raise MigrationError("task_definition", f"{path}: task bytes must be LF terminated")
    for section in ("## Goal\n", "## Touch\n", "## Steps\n", "## Acceptance\n"):
        if section not in text:
            raise MigrationError("task_definition", f"{path}: missing {section.strip()}")
    return headers


def _normalize_dep(value: str) -> str:
    if value == "none":
        return value
    if value.startswith("specs/"):
        return value
    if not re.fullmatch(r"\d{2}", value):
        raise MigrationError("manifest_graph", f"invalid dependency token {value!r}")
    return value


@dataclasses.dataclass(frozen=True)
class ValidatedManifest:
    path: Path
    root: Path
    data: dict[str, Any]
    replacement_paths: tuple[str, ...]
    external_refs: tuple[str, ...]


def _canonical_task_definition(
    root: Path,
    task_path: str,
    dependencies: Iterable[str],
    replacement_paths: Mapping[str, str],
    retained_path: str,
) -> dict[str, Any]:
    path = root / task_path
    text = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    goal_match = re.search(
        r"^## Goal\s*$\n(?P<body>.*?)(?=^##\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not title_match or not goal_match:
        raise MigrationError("task_definition", f"{task_path}: missing title/goal")
    headers = _task_headers(path)
    prerequisite_paths = []
    for dependency in dependencies:
        if dependency == "01":
            prerequisite_paths.append(retained_path)
        elif re.fullmatch(r"\d{2}", dependency):
            try:
                prerequisite_paths.append(replacement_paths[dependency])
            except KeyError as exc:
                sibling = sorted(path.parent.glob(f"{dependency}-*.md"))
                if len(sibling) != 1:
                    raise MigrationError(
                        "task_definition",
                        f"{task_path}: ambiguous dependency {dependency}",
                    ) from exc
                prerequisite_paths.append(sibling[0].relative_to(root).as_posix())
        else:
            prerequisite_paths.append(dependency)
    touch = sorted(
        item.strip() for item in headers["Touch"].split(",") if item.strip()
    )
    return {
        "schema_version": 1,
        "path": task_path,
        "title": title_match.group(1).strip(),
        "goal": goal_match.group("body").strip(),
        "touch": touch,
        "budget": headers["Budget"],
        "rigor": headers.get("Rigor") or "production",
        "prerequisites": sorted(
            {"spec-task:" + dependency for dependency in prerequisite_paths}
        ),
    }


def _definition_hash(definition: Mapping[str, Any]) -> str:
    return digest(definition)


ISSUE_FIELD_KEYS = {
    "title",
    "description",
    "acceptance",
    "notes",
    "status",
    "assignee",
    "priority",
    "issue_type",
    "external_ref",
}


def _validate_snapshot_issue(value: Any, where: str) -> dict[str, Any]:
    issue = _as_dict(value, where)
    _exact_keys(
        issue,
        {"id", "revision", "history_cursor", "fields", "metadata", "edges"},
        where,
    )
    if not all(
        isinstance(issue[key], str) and issue[key]
        for key in ("id", "revision", "history_cursor")
    ):
        raise MigrationError("attestation_snapshot", f"{where} identity/revision drift")
    fields = _as_dict(issue["fields"], f"{where}.fields")
    _exact_keys(fields, ISSUE_FIELD_KEYS, f"{where}.fields")
    if (
        not all(
            fields[key] is None or isinstance(fields[key], (str, int))
            for key in ISSUE_FIELD_KEYS
        )
        or not isinstance(issue["metadata"], dict)
    ):
        raise MigrationError("attestation_snapshot", f"{where} field/metadata drift")
    edges = _as_list(issue["edges"], f"{where}.edges")
    edge_keys = {"issue_id", "dependency_id", "kind", "revision"}
    previous = None
    for index, edge_value in enumerate(edges):
        edge = _as_dict(edge_value, f"{where}.edges[{index}]")
        _exact_keys(edge, edge_keys, f"{where}.edges[{index}]")
        if not all(isinstance(edge[key], str) and edge[key] for key in edge_keys):
            raise MigrationError("attestation_snapshot", f"{where} edge drift")
        encoded = canonical_bytes(edge)
        if previous is not None and encoded <= previous:
            raise MigrationError("attestation_snapshot", f"{where} edges must be unique/sorted")
        previous = encoded
    return issue


def _validate_starting_snapshot(
    value: Any,
    retained: Mapping[str, Any],
    historical: list[dict[str, Any]],
    rewires: list[dict[str, Any]],
) -> dict[str, Any]:
    snapshot = _as_dict(value, "starting_tracker_snapshot")
    _exact_keys(
        snapshot,
        {"schema", "task01", "historical", "known_external_consumers"},
        "starting_tracker_snapshot",
    )
    if snapshot["schema"] != "agentic.registration-starting-snapshot/v1":
        raise MigrationError("attestation_snapshot", "starting snapshot schema drift")
    task01 = _validate_snapshot_issue(snapshot["task01"], "starting_tracker_snapshot.task01")
    if task01["id"] != retained["id"]:
        raise MigrationError("attestation_snapshot", "Task01 ID drift")
    history = _as_list(snapshot["historical"], "starting_tracker_snapshot.historical")
    if len(history) != 11:
        raise MigrationError("attestation_snapshot", "historical snapshot cardinality drift")
    history_rows = [
        _validate_snapshot_issue(item, f"starting_tracker_snapshot.historical[{index}]")
        for index, item in enumerate(history)
    ]
    if [item["id"] for item in history_rows] != [item["id"] for item in historical]:
        raise MigrationError("attestation_snapshot", "historical snapshot order/IDs drift")
    consumers = _as_list(
        snapshot["known_external_consumers"],
        "starting_tracker_snapshot.known_external_consumers",
    )
    if len(consumers) != 2:
        raise MigrationError("attestation_snapshot", "known consumer cardinality drift")
    consumer_rows = [
        _validate_snapshot_issue(
            item, f"starting_tracker_snapshot.known_external_consumers[{index}]"
        )
        for index, item in enumerate(consumers)
    ]
    if [item["id"] for item in consumer_rows] != [item["consumer"] for item in rewires]:
        raise MigrationError("attestation_snapshot", "known consumer order/IDs drift")
    return snapshot


def validate_manifest(path: Path, *, require_attestation: bool = False) -> ValidatedManifest:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
            raise MigrationError("manifest_encoding", "manifest must be UTF-8 without BOM or CR")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        if isinstance(exc, MigrationError):
            raise
        raise MigrationError("manifest_json", str(exc)) from exc
    data = _as_dict(data, "manifest")
    _exact_keys(data, TOP_KEYS, "manifest")
    if data["schema"] != SCHEMA:
        raise MigrationError("manifest_schema", "unsupported schema")
    if data["spec"] != "specs/mardi-gras-agentic-integration/SPEC.md":
        raise MigrationError("manifest_schema", "unexpected spec path")
    if not isinstance(data["source_date_utc"], str) or not DATE_RE.fullmatch(data["source_date_utc"]):
        raise MigrationError("manifest_schema", "source_date_utc must be canonical YYYY-MM-DD")
    try:
        dt.date.fromisoformat(data["source_date_utc"])
    except ValueError as exc:
        raise MigrationError("manifest_schema", "invalid source_date_utc") from exc
    root = _repo_root(path)

    authority = _as_dict(data["authority"], "authority")
    _exact_keys(authority, {"protocol", "response_schema", "required_capabilities"}, "authority")
    if authority != {
        "protocol": ADAPTER_PROTOCOL,
        "response_schema": RESPONSE_SCHEMA,
        "required_capabilities": list(REQUIRED_CAPABILITIES),
    }:
        raise MigrationError("manifest_authority", "authority protocol/capabilities drift")
    if data["phases"] != list(PHASES):
        raise MigrationError("manifest_phases", "phase order drift")
    feature = _as_dict(data["feature_container"], "feature_container")
    _exact_keys(feature, {"id", "relation"}, "feature_container")
    if feature != {"id": "agentic-j01", "relation": "related"}:
        raise MigrationError("manifest_container", "feature container drift")
    retained = _as_dict(data["retained"], "retained")
    _exact_keys(retained, {"id", "path"}, "retained")
    if retained != {
        "id": "agentic-yt1",
        "path": TASK_PREFIX + "01-make-claims-session-safe.md",
    }:
        raise MigrationError("manifest_retained", "retained Task 01 drift")

    bootstrap = _as_list(data["bootstrap"], "bootstrap")
    if len(bootstrap) != 4:
        raise MigrationError("manifest_bootstrap", "exactly four bootstrap definitions required")
    previous: list[str] = []
    for index, (entry, name) in enumerate(zip(bootstrap, EXPECTED_BOOTSTRAP)):
        item = _as_dict(entry, f"bootstrap[{index}]")
        _exact_keys(item, {"path", "depends_on"}, f"bootstrap[{index}]")
        expected_path = TASK_PREFIX + name
        expected_deps = [] if index == 0 else [TASK_PREFIX + EXPECTED_BOOTSTRAP[index - 1]]
        if item != {"path": expected_path, "depends_on": expected_deps}:
            raise MigrationError("manifest_bootstrap", f"bootstrap[{index}] drift")
        previous.append(expected_path)

    historical = _as_list(data["historical"], "historical")
    if len(historical) != 11:
        raise MigrationError("manifest_history", "exactly eleven historical mappings required")
    seen_ids: set[str] = set()
    mappings: dict[str, str] = {}
    for index, entry in enumerate(historical):
        item = _as_dict(entry, f"historical[{index}]")
        _exact_keys(item, {"id", "path", "replacement"}, f"historical[{index}]")
        old_name = Path(item["path"]).name
        replacement_name = Path(item["replacement"]).name
        if item["path"] != TASK_PREFIX + old_name or item["replacement"] != TASK_PREFIX + replacement_name:
            raise MigrationError("manifest_history", "historical path outside exact task root")
        if old_name in mappings or item["id"] in seen_ids:
            raise MigrationError("manifest_history", "duplicate historical mapping/id")
        mappings[old_name] = replacement_name
        seen_ids.add(item["id"])
    if mappings != EXPECTED_HISTORICAL:
        raise MigrationError("manifest_history", "old-to-replacement mapping drift")

    replacements = _as_list(data["replacements"], "replacements")
    if len(replacements) != 27:
        raise MigrationError("manifest_graph", "exactly 27 replacement definitions required")
    numbers: list[int] = []
    paths: list[str] = []
    for index, entry in enumerate(replacements):
        item = _as_dict(entry, f"replacements[{index}]")
        _exact_keys(item, {"path", "depends_on"}, f"replacements[{index}]")
        number = _task_number(item["path"])
        numbers.append(number)
        if item["path"] in paths:
            raise MigrationError("manifest_graph", "duplicate replacement path")
        paths.append(item["path"])
        deps = [_normalize_dep(dep) for dep in _as_list(item["depends_on"], "depends_on")]
        if deps != item["depends_on"] or len(deps) != len(set(deps)):
            raise MigrationError("manifest_graph", f"noncanonical dependencies for Task {number}")
    if sorted(numbers) != list(range(13, 40)):
        raise MigrationError("manifest_graph", "replacement task numbers must be exactly 13..39")

    by_number = {number: entry for number, entry in zip(numbers, replacements)}
    for number, entry in by_number.items():
        task_path = root / entry["path"]
        if not task_path.is_file() or task_path.is_symlink():
            raise MigrationError("task_definition", f"missing regular task {entry['path']}")
        headers = _task_headers(task_path)
        expected_dep_header = ", ".join(entry["depends_on"]) if entry["depends_on"] else "none"
        if headers["Depends on"] != expected_dep_header:
            raise MigrationError(
                "manifest_graph",
                f"Task {number} dependency header {headers['Depends on']!r} != {expected_dep_header!r}",
            )
        if headers["Status"] != "pending" or headers["Priority"] != "P0":
            raise MigrationError("task_definition", f"Task {number} must be pending/P0")
        if not re.fullmatch(r"[1-9]\d* turns", headers["Budget"]):
            raise MigrationError("task_definition", f"Task {number} has invalid Budget")
        if headers["Spec"] != "../SPEC.md" and not headers["Spec"].startswith("../SPEC.md "):
            raise MigrationError("task_definition", f"Task {number} has wrong Spec")

    refs = tuple("spec-task:" + path for path in paths)
    if len(refs) != len(set(refs)):
        raise MigrationError("manifest_graph", "duplicate external refs")

    rewires = _as_list(data["known_external_rewires"], "known_external_rewires")
    actual_external = []
    for index, entry in enumerate(rewires):
        item = _as_dict(entry, f"known_external_rewires[{index}]")
        _exact_keys(item, {"consumer", "old_id", "replacement", "kind"}, f"rewire[{index}]")
        actual_external.append(
            (item["consumer"], item["old_id"], Path(item["replacement"]).name, item["kind"])
        )
    if tuple(actual_external) != EXPECTED_EXTERNAL:
        raise MigrationError("manifest_external", "known external rewires drift")

    blockers = _as_list(data["manual_blockers"], "manual_blockers")
    if len(blockers) != 2:
        raise MigrationError("manifest_manual", "exactly two manual blockers required")
    blocker_numbers = []
    for index, entry in enumerate(blockers):
        item = _as_dict(entry, f"manual_blockers[{index}]")
        _exact_keys(item, {"path", "contains"}, f"manual_blockers[{index}]")
        blocker_numbers.append(_task_number(item["path"]))
        if not isinstance(item["contains"], str) or not item["contains"]:
            raise MigrationError("manifest_manual", "manual blocker selector must be nonempty")
    if blocker_numbers != [26, 27]:
        raise MigrationError("manifest_manual", "manual blockers must be Tasks 26 then 27")

    workset = _as_dict(data["workset_extension"], "workset_extension")
    _exact_keys(
        workset,
        {"schema", "triggers", "required_edge", "registration", "cohort_policy"},
        "workset_extension",
    )
    if workset != {
        "schema": WORKSET_SCHEMA,
        "triggers": ["critique", "discovery", "human"],
        "required_edge": "blocks",
        "registration": "guarded_complete_create_with_initial_edge",
        "cohort_policy": "later_fresh_scan",
    }:
        raise MigrationError("manifest_workset", "workset-extension contract drift")

    attestation = _as_dict(data["attestation"], "attestation")
    if not attestation:
        if require_attestation:
            raise MigrationError("source_unattested", "attestation object is empty")
    else:
        _exact_keys(attestation, ATTESTATION_KEYS, "attestation")
        for key in (
            "source_commit",
            "bootstrap_source_commit",
            "bootstrap_attestation_commit",
        ):
            if not isinstance(attestation[key], str) or not COMMIT_RE.fullmatch(attestation[key]):
                raise MigrationError("attestation", f"{key} must be 40 lowercase hex")
        if (
            attestation["bootstrap_source_commit"] == attestation["source_commit"]
            or attestation["bootstrap_source_commit"]
            == attestation["bootstrap_attestation_commit"]
        ):
            raise MigrationError(
                "attestation",
                "bootstrap and final source/attestation commits must be distinct",
            )
        for key in ("spec_sha256", "bootstrap_receipt_sha256", "task01_live_fields_sha256"):
            if not isinstance(attestation[key], str) or not SHA256_RE.fullmatch(attestation[key]):
                raise MigrationError("attestation", f"{key} must be SHA-256")
        definitions = _as_dict(attestation["definition_hash"], "definition_hash")
        expected_definition_paths = {
            retained["path"],
            *(item["path"] for item in bootstrap),
            *(item["path"] for item in historical),
            *paths,
        }
        if set(definitions) != expected_definition_paths or any(
            not isinstance(value, str) or not SHA256_RE.fullmatch(value)
            for value in definitions.values()
        ):
            raise MigrationError("attestation", "definition hash domain/value drift")
        number_paths = {
            "01": retained["path"],
            **{
                f"{_task_number(item['path']):02d}": item["path"]
                for item in historical
            },
            **{
                f"{_task_number(item['path']):02d}": item["path"]
                for item in replacements
            },
        }
        dependency_by_path: dict[str, list[str]] = {
            retained["path"]: [],
            **{item["path"]: item["depends_on"] for item in bootstrap},
            **{item["path"]: item["depends_on"] for item in replacements},
        }
        for item in historical:
            raw_dependencies = _task_headers(root / item["path"])["Depends on"]
            dependency_by_path[item["path"]] = (
                []
                if raw_dependencies == "none"
                else [part.strip() for part in raw_dependencies.split(",")]
            )
        for task_path in sorted(expected_definition_paths):
            expected_hash = _definition_hash(
                _canonical_task_definition(
                    root,
                    task_path,
                    dependency_by_path[task_path],
                    number_paths,
                    retained["path"],
                )
            )
            if definitions[task_path] != expected_hash:
                raise MigrationError(
                    "attestation",
                    f"canonical definition_hash mismatch: {task_path}",
                )
        human = _as_dict(attestation["human_sha256"], "human_sha256")
        if set(human) != {item["path"] for item in blockers} or any(
            not isinstance(value, str) or not SHA256_RE.fullmatch(value) for value in human.values()
        ):
            raise MigrationError("attestation", "HUMAN digest domain/value drift")
        snapshot = _validate_starting_snapshot(
            attestation["starting_tracker_snapshot"],
            retained,
            historical,
            rewires,
        )
        if attestation["task01_live_fields_sha256"] != digest(
            snapshot["task01"]["fields"]
        ):
            raise MigrationError(
                "attestation",
                "Task01 live-field digest differs from inline starting snapshot",
            )
    return ValidatedManifest(path.resolve(), root, data, tuple(paths), refs)


def validate_workset_extension(value: Any, root: Path) -> dict[str, Any]:
    item = _as_dict(value, "workset_extension_action")
    _exact_keys(item, {"schema", "trigger", "task", "downstream"}, "workset_extension_action")
    if item["schema"] != WORKSET_SCHEMA or item["trigger"] not in {"critique", "discovery", "human"}:
        raise MigrationError("workset_extension", "schema or trigger drift")
    if len(canonical_bytes(item)) > 2 * 1024 * 1024:
        raise MigrationError("workset_extension", "action is unbounded")
    task = _as_dict(item["task"], "workset_extension.task")
    _exact_keys(
        task,
        {"path", "bytes_sha256", "definition_hash", "envelope"},
        "workset_extension.task",
    )
    path = task["path"]
    if (
        not isinstance(path, str)
        or not path.startswith("specs/")
        or ".." in Path(path).parts
        or "\\" in path
    ):
        raise MigrationError("workset_extension", "task path must be a contained authored path")
    root = root.resolve()
    lexical = Path(os.path.abspath(root / path))
    try:
        absolute = (root / path).resolve(strict=True)
    except OSError as exc:
        raise MigrationError("workset_extension", "authored task is missing") from exc
    try:
        absolute.relative_to(root.resolve())
    except ValueError as exc:
        raise MigrationError("workset_extension", "task escapes repository") from exc
    if (
        absolute != lexical
        or absolute.relative_to(root).as_posix() != path
        or not absolute.is_file()
        or absolute.is_symlink()
    ):
        raise MigrationError("workset_extension", "task path is noncanonical or linked")
    task_bytes = absolute.read_bytes()
    if (
        not task_bytes
        or len(task_bytes) > 1024 * 1024
        or b"\r" in task_bytes
        or not task_bytes.endswith(b"\n")
        or not isinstance(task["bytes_sha256"], str)
        or not SHA256_RE.fullmatch(task["bytes_sha256"])
        or hashlib.sha256(task_bytes).hexdigest() != task["bytes_sha256"]
    ):
        raise MigrationError("workset_extension", "task bytes/hash mismatch")
    try:
        text = task_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MigrationError("workset_extension", "task must be UTF-8") from exc
    headers = _task_headers(absolute)
    if (
        headers["Status"] != "pending"
        or headers["Priority"] != "P0"
        or not re.fullmatch(r"[1-9]\d* turns", headers["Budget"])
    ):
        raise MigrationError(
            "workset_extension", "authored task must be pending, P0, with canonical budget"
        )
    title_match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    goal_match = re.search(
        r"^## Goal\s*$\n(?P<body>.*?)(?=^##\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    acceptance_match = re.search(
        r"^## Acceptance\s*$\n(?P<body>.*?)(?=^##\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if (
        not title_match
        or not goal_match
        or not goal_match.group("body").strip()
        or not acceptance_match
        or not acceptance_match.group("body").strip()
    ):
        raise MigrationError(
            "workset_extension", "task requires complete title, goal, and acceptance"
        )
    raw_dependencies = headers["Depends on"]
    prerequisite_paths: list[str] = []
    if raw_dependencies != "none":
        for token in (part.strip() for part in raw_dependencies.split(",")):
            if not token:
                raise MigrationError("workset_extension", "empty dependency token")
            if token.isdigit():
                dependency_number = int(token)
                candidates = sorted(
                    sibling
                    for sibling in absolute.parent.glob("*.md")
                    if (
                        (number_match := re.match(r"^(\d+)", sibling.name))
                        and int(number_match.group(1)) == dependency_number
                    )
                )
                if len(candidates) != 1:
                    raise MigrationError(
                        "workset_extension",
                        (
                            f"numeric dependency {token} resolves to "
                            f"{len(candidates)} tasks; use one exact task filename/path"
                        ),
                    )
                target = candidates[0]
            else:
                candidate = Path(token)
                if candidate.is_absolute():
                    target = candidate
                elif token.startswith("specs/"):
                    target = root / candidate
                else:
                    target = absolute.parent / candidate
            try:
                target = target.resolve(strict=True)
                relative_target = target.relative_to(root).as_posix()
            except (OSError, ValueError) as exc:
                raise MigrationError(
                    "workset_extension", f"dependency escapes or is missing: {token}"
                ) from exc
            if not target.is_file() or target.is_symlink():
                raise MigrationError(
                    "workset_extension", f"dependency is not a regular task: {token}"
                )
            prerequisite_paths.append(relative_target)
    touch = sorted(
        item.strip() for item in headers["Touch"].split(",") if item.strip()
    )
    if not touch or len(touch) != len(set(touch)) or any(
        not item or item.startswith("/") or ".." in Path(item).parts
        for item in touch
    ):
        raise MigrationError("workset_extension", "Touch must be a nonempty path set")
    definition = {
        "schema_version": 1,
        "path": path,
        "title": title_match.group(1).strip(),
        "goal": goal_match.group("body").strip(),
        "touch": touch,
        "budget": headers["Budget"],
        "rigor": headers.get("Rigor") or "production",
        "prerequisites": sorted(
            {"spec-task:" + dependency for dependency in prerequisite_paths}
        ),
    }
    definition_hash = _definition_hash(definition)
    if (
        not isinstance(task["definition_hash"], str)
        or task["definition_hash"] != definition_hash
    ):
        raise MigrationError("workset_extension", "canonical definition hash mismatch")
    envelope = _as_dict(task["envelope"], "workset_extension.envelope")
    envelope_keys = {
        "title",
        "description",
        "acceptance",
        "task_type",
        "priority",
        "metadata",
        "container",
        "source",
        "touch",
        "budget",
        "rigor",
        "prerequisites",
    }
    _exact_keys(envelope, envelope_keys, "workset_extension.envelope")
    expected_metadata = {
        "budget": definition["budget"],
        "definition_hash": definition_hash,
        "registration_state": "complete",
        "rigor": definition["rigor"],
        "source": path,
        "touch": touch,
    }
    expected_envelope = {
        "title": definition["title"],
        "description": definition["goal"],
        "acceptance": acceptance_match.group("body").strip(),
        "task_type": "task",
        "priority": 0,
        "metadata": expected_metadata,
        "container": {"id": "agentic-j01", "relation": "related"},
        "source": path,
        "touch": touch,
        "budget": definition["budget"],
        "rigor": definition["rigor"],
        "prerequisites": definition["prerequisites"],
    }
    if envelope != expected_envelope:
        raise MigrationError(
            "workset_extension", "issue envelope differs from authored task definition"
        )
    downstream = _as_dict(item["downstream"], "workset_extension.downstream")
    _exact_keys(downstream, {"issue_id", "revision", "edge"}, "workset_extension.downstream")
    edge = _as_dict(downstream["edge"], "workset_extension.downstream.edge")
    _exact_keys(
        edge,
        {"kind", "issue_id", "dependency_external_ref"},
        "workset_extension.downstream.edge",
    )
    if (
        not isinstance(downstream["issue_id"], str)
        or not re.fullmatch(r"[a-z][a-z0-9-]*-[a-z0-9.]+", downstream["issue_id"])
        or not isinstance(downstream["revision"], str)
        or not re.fullmatch(r"[A-Za-z0-9._:-]{1,256}", downstream["revision"])
        or edge
        != {
            "kind": "blocks",
            "issue_id": downstream["issue_id"],
            "dependency_external_ref": "spec-task:" + path,
        }
    ):
        raise MigrationError("workset_extension", "downstream binding drift")
    return item


def validate_review_artifact(
    path: Path, manifest: ValidatedManifest, reviewed_commit: str
) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        if not raw or len(raw) > 16 * 1024 or raw.endswith(b"\n") or b"\r" in raw:
            raise MigrationError(
                "review_artifact",
                "review artifact must be bounded canonical no-LF JSON",
            )
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        if isinstance(exc, MigrationError):
            raise
        raise MigrationError("review_artifact", str(exc)) from exc
    value = _as_dict(value, "review_artifact")
    _exact_keys(
        value,
        {
            "schema",
            "verdict",
            "reviewed_commit",
            "source_commit",
            "spec_sha256",
            "reviewer_run_id",
            "evidence_summary",
        },
        "review_artifact",
    )
    if canonical_bytes(value) != raw:
        raise MigrationError("review_artifact", "review artifact JSON is not canonical")
    attestation = manifest.data["attestation"]
    if (
        value["schema"] != "agentic.registration-review/v1"
        or value["verdict"] != "READY"
        or value["reviewed_commit"] != reviewed_commit
        or value["source_commit"] != attestation["source_commit"]
        or value["spec_sha256"] != attestation["spec_sha256"]
        or not isinstance(value["reviewer_run_id"], str)
        or not 1 <= len(value["reviewer_run_id"].encode("utf-8")) <= 256
        or not isinstance(value["evidence_summary"], str)
        or not 1 <= len(value["evidence_summary"].encode("utf-8")) <= 4096
    ):
        raise MigrationError("review_artifact", "review artifact identity/verdict drift")
    return value


def load_bootstrap_receipt(
    path: Path,
    manifest: ValidatedManifest,
    reviewed_commit: str,
) -> tuple[dict[str, Any], str]:
    candidate = path if path.is_absolute() else manifest.root / path
    lexical_candidate = Path(os.path.abspath(candidate))
    try:
        resolved_candidate = candidate.resolve(strict=True)
    except OSError as exc:
        raise MigrationError("bootstrap_receipt", str(exc)) from exc
    if lexical_candidate != resolved_candidate:
        raise MigrationError(
            "bootstrap_receipt", "receipt path or parent contains a symlink"
        )
    candidate = resolved_candidate
    if not path.is_absolute():
        try:
            candidate.relative_to(manifest.root.resolve())
        except ValueError as exc:
            raise MigrationError(
                "bootstrap_receipt", "relative receipt path escapes repository"
            ) from exc
    try:
        info = candidate.stat()
        raw = candidate.read_bytes()
    except OSError as exc:
        raise MigrationError("bootstrap_receipt", str(exc)) from exc
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != 0o600
        or not raw
        or len(raw) > 1024 * 1024
        or raw.endswith(b"\n")
        or b"\r" in raw
    ):
        raise MigrationError(
            "bootstrap_receipt",
            "receipt must be an owned mode-0600 bounded canonical no-LF regular file",
        )
    try:
        receipt = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise MigrationError("bootstrap_receipt", str(exc)) from exc
    receipt = _as_dict(receipt, "bootstrap_receipt")
    _exact_keys(
        receipt,
        {
            "schema",
            "source_commit",
            "attestation_commit",
            "intent",
            "issues",
            "published_head",
            "event_chain",
            "provider",
        },
        "bootstrap_receipt",
    )
    if canonical_bytes(receipt) != raw:
        raise MigrationError("bootstrap_receipt", "receipt JSON is not canonical")
    if (
        receipt["schema"] != "agentic.registration-bootstrap-terminal-receipt/v1"
        or receipt["source_commit"]
        != manifest.data["attestation"]["bootstrap_source_commit"]
        or receipt["attestation_commit"]
        != manifest.data["attestation"]["bootstrap_attestation_commit"]
        or receipt["source_commit"]
        == manifest.data["attestation"]["source_commit"]
        or receipt["attestation_commit"] == reviewed_commit
        or not COMMIT_RE.fullmatch(receipt["source_commit"])
        or not COMMIT_RE.fullmatch(receipt["attestation_commit"])
        or not isinstance(receipt["published_head"], str)
        or not COMMIT_RE.fullmatch(receipt["published_head"])
    ):
        raise MigrationError("bootstrap_receipt", "receipt commit/schema identity drift")
    intent = _as_dict(receipt["intent"], "bootstrap_receipt.intent")
    _exact_keys(intent, {"id", "sha256"}, "bootstrap_receipt.intent")
    if (
        not isinstance(intent["id"], str)
        or not re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            intent["id"],
        )
        or not isinstance(intent["sha256"], str)
        or not SHA256_RE.fullmatch(intent["sha256"])
    ):
        raise MigrationError("bootstrap_receipt", "bootstrap intent identity drift")
    issues = _as_dict(receipt["issues"], "bootstrap_receipt.issues")
    _exact_keys(issues, {"00A", "00B", "00C", "00D"}, "bootstrap_receipt.issues")
    if any(
        not isinstance(issue_id, str)
        or not re.fullmatch(r"[a-z][a-z0-9-]*-[a-z0-9.]+", issue_id)
        for issue_id in issues.values()
    ):
        raise MigrationError("bootstrap_receipt", "bootstrap issue ID drift")
    event_chain = _as_dict(
        receipt["event_chain"], "bootstrap_receipt.event_chain"
    )
    _exact_keys(event_chain, {"head", "previous"}, "bootstrap_receipt.event_chain")
    if (
        not isinstance(event_chain["head"], str)
        or not SHA256_RE.fullmatch(event_chain["head"])
        or not isinstance(event_chain["previous"], str)
        or not SHA256_RE.fullmatch(event_chain["previous"])
        or event_chain["head"] == event_chain["previous"]
    ):
        raise MigrationError("bootstrap_receipt", "bootstrap event-chain drift")
    provider = _as_dict(receipt["provider"], "bootstrap_receipt.provider")
    _exact_keys(
        provider,
        {"path", "sha256", "full_profile_identity"},
        "bootstrap_receipt.provider",
    )
    provider_path = Path(provider["path"]) if isinstance(provider["path"], str) else Path()
    if (
        not provider_path.is_absolute()
        or provider_path.is_symlink()
        or Path(os.path.abspath(provider_path)) != provider_path.resolve()
        or not provider_path.is_file()
        or not isinstance(provider["sha256"], str)
        or not SHA256_RE.fullmatch(provider["sha256"])
        or file_digest(provider_path) != provider["sha256"]
    ):
        raise MigrationError("bootstrap_receipt", "final provider path/hash drift")
    identity = _as_dict(
        provider["full_profile_identity"],
        "bootstrap_receipt.provider.full_profile_identity",
    )
    identity_keys = {
        "backend_mode",
        "database_identity",
        "project_identity",
        "repository_identity",
        "core_schema_fingerprint",
        "full_schema_fingerprint",
    }
    _exact_keys(
        identity,
        identity_keys,
        "bootstrap_receipt.provider.full_profile_identity",
    )
    if any(
        not isinstance(identity[key], str)
        or not identity[key]
        or len(identity[key].encode("utf-8")) > 512
        for key in identity_keys
    ) or any(
        not SHA256_RE.fullmatch(identity[key])
        for key in ("core_schema_fingerprint", "full_schema_fingerprint")
    ):
        raise MigrationError("bootstrap_receipt", "full profile identity drift")
    receipt_sha256 = hashlib.sha256(raw).hexdigest()
    if (
        receipt_sha256
        != manifest.data["attestation"]["bootstrap_receipt_sha256"]
    ):
        raise MigrationError("bootstrap_receipt", "terminal receipt digest mismatch")
    return receipt, receipt_sha256


class Authority(Protocol):
    def request(self, operation: str, payload: Mapping[str, Any]) -> dict[str, Any]: ...


class SubprocessAuthority:
    """Strict one-request/one-response JSON adapter; no PATH lookup or shell."""

    def __init__(self, executable: Path):
        if not executable.is_absolute():
            raise MigrationError("authority_path", "authority executable must be absolute")
        try:
            info = executable.lstat()
        except OSError as exc:
            raise MigrationError("authority_path", str(exc)) from exc
        if not stat.S_ISREG(info.st_mode) or executable.is_symlink() or not os.access(executable, os.X_OK):
            raise MigrationError("authority_path", "authority must be an executable regular file")
        self.executable = executable
        self.executable_sha256 = file_digest(executable)
        handshake = self.request("handshake", {})
        if handshake != {
            "protocol": ADAPTER_PROTOCOL,
            "capabilities": list(REQUIRED_CAPABILITIES),
        }:
            raise MigrationError("authority_handshake", "capability handshake drift")

    def request(self, operation: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        if file_digest(self.executable) != self.executable_sha256:
            raise MigrationError("authority_drift", "authority executable changed")
        request = {
            "schema": ADAPTER_PROTOCOL,
            "operation": operation,
            "payload": dict(payload),
        }
        completed = subprocess.run(
            [os.fspath(self.executable)],
            input=canonical_bytes(request),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C"},
        )
        if file_digest(self.executable) != self.executable_sha256:
            raise MigrationError("authority_drift", "authority executable changed during request")
        if completed.returncode != 0:
            raise MigrationError(
                "authority_failed",
                f"{operation} exited {completed.returncode}: {completed.stderr[:512].decode('utf-8', 'replace')}",
            )
        if (
            completed.stderr
            or completed.stdout.endswith(b"\n")
            or not completed.stdout
            or len(completed.stdout) > 4 * 1024 * 1024
        ):
            raise MigrationError("authority_protocol", "response must be one no-LF JSON object on stdout")
        try:
            result = json.loads(completed.stdout)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise MigrationError("authority_protocol", str(exc)) from exc
        result = _as_dict(result, "authority_response")
        if canonical_bytes(result) != completed.stdout:
            raise MigrationError("authority_protocol", "response JSON must be canonical")
        _exact_keys(result, {"schema", "ok", "payload"}, "authority_response")
        if result["schema"] != RESPONSE_SCHEMA or result["ok"] is not True:
            raise MigrationError("authority_protocol", f"{operation} returned non-success")
        return _as_dict(result["payload"], "authority_response.payload")


class SourceGate(Protocol):
    def attest(self, manifest: ValidatedManifest, reviewed_commit: str) -> dict[str, Any]: ...


class GitSourceGate:
    def _git(self, root: Path, *args: str) -> bytes:
        completed = subprocess.run(
            ["git", "-C", os.fspath(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C"},
        )
        if completed.returncode:
            raise MigrationError("source_git", completed.stderr.decode("utf-8", "replace")[:512])
        return completed.stdout

    def attest(self, manifest: ValidatedManifest, reviewed_commit: str) -> dict[str, Any]:
        attestation = manifest.data["attestation"]
        if not COMMIT_RE.fullmatch(reviewed_commit):
            raise MigrationError("source_attestation", "reviewed commit must be 40 lowercase hex")
        head = self._git(manifest.root, "rev-parse", "HEAD").decode().strip()
        parent = self._git(manifest.root, "rev-parse", "HEAD^").decode().strip()
        if head != reviewed_commit or parent != attestation["source_commit"]:
            raise MigrationError("source_attestation", "HEAD/parent attestation mismatch")
        changed = self._git(
            manifest.root, "diff", "--name-only", attestation["source_commit"], reviewed_commit
        ).decode().splitlines()
        expected_manifest = manifest.path.relative_to(manifest.root).as_posix()
        if changed != [expected_manifest]:
            raise MigrationError("source_attestation", "attestation child must change only manifest")
        source_manifest_bytes = self._git(
            manifest.root,
            "show",
            f"{attestation['source_commit']}:{expected_manifest}",
        )
        try:
            source_manifest = json.loads(source_manifest_bytes)
        except json.JSONDecodeError as exc:
            raise MigrationError("source_attestation", "source manifest is not JSON") from exc
        current_without_attestation = copy_without_attestation(manifest.data)
        source_without_attestation = copy_without_attestation(source_manifest)
        if source_manifest.get("attestation") != {} or source_without_attestation != current_without_attestation:
            raise MigrationError(
                "source_attestation",
                "attestation child must fill only the previously empty attestation object",
            )
        if self._git(
            manifest.root,
            "status",
            "--porcelain=v2",
            "--untracked-files=all",
            "--ignored=matching",
            "--ignore-submodules=none",
        ):
            raise MigrationError("source_attestation", "worktree is not clean")
        submodules = self._git(manifest.root, "submodule", "status", "--recursive")
        if any(line[:1] in {"+", "-", "U"} for line in submodules.decode().splitlines()):
            raise MigrationError("source_attestation", "submodule state is not clean")
        commit_date = self._git(
            manifest.root, "show", "-s", "--format=%cI", attestation["source_commit"]
        ).decode().strip()
        if dt.datetime.fromisoformat(commit_date).astimezone(dt.timezone.utc).date().isoformat() != manifest.data["source_date_utc"]:
            raise MigrationError("source_attestation", "source commit UTC date mismatch")
        spec_bytes = self._git(
            manifest.root, "show", f"{attestation['source_commit']}:{manifest.data['spec']}"
        )
        if hashlib.sha256(spec_bytes).hexdigest() != attestation["spec_sha256"]:
            raise MigrationError("source_attestation", "SPEC digest mismatch")
        if (manifest.root / manifest.data["spec"]).read_bytes() != spec_bytes:
            raise MigrationError("source_attestation", "current SPEC differs from source commit")
        for path in attestation["definition_hash"]:
            source_bytes = self._git(manifest.root, "show", f"{attestation['source_commit']}:{path}")
            if (manifest.root / path).read_bytes() != source_bytes:
                raise MigrationError("source_attestation", f"definition bytes differ from source: {path}")
        human_bytes = self._git(
            manifest.root, "show", f"{attestation['source_commit']}:HUMAN.md"
        )
        if human_bytes.count(b"## Agent-filed blockers\n") != 1:
            raise MigrationError("source_attestation", "HUMAN section cardinality drift")
        for blocker in manifest.data["manual_blockers"]:
            selector = f" · {blocker['path']} · run — ".encode()
            lines = [
                line + b"\n"
                for line in human_bytes.splitlines()
                if selector in line
            ]
            if (
                len(lines) != 1
                or not lines[0].startswith(b"- [ ] ")
                or hashlib.sha256(lines[0]).hexdigest()
                != attestation["human_sha256"][blocker["path"]]
            ):
                raise MigrationError(
                    "source_attestation", f"HUMAN blocker drift: {blocker['path']}"
                )
        return {
            "reviewed_commit": reviewed_commit,
            "source_commit": attestation["source_commit"],
            "manifest_sha256": file_digest(manifest.path),
        }


def _uuid7() -> str:
    milliseconds = int(time.time_ns() // 1_000_000)
    if milliseconds >= 1 << 48:
        raise MigrationError("owner_identity", "clock exceeds UUIDv7 range")
    random = bytearray(os.urandom(10))
    value = bytearray(milliseconds.to_bytes(6, "big") + random)
    value[6] = (value[6] & 0x0F) | 0x70
    value[8] = (value[8] & 0x3F) | 0x80
    hexed = value.hex()
    return f"{hexed[:8]}-{hexed[8:12]}-{hexed[12:16]}-{hexed[16:20]}-{hexed[20:]}"


def _process_start(pid: int) -> str:
    completed = subprocess.run(
        ["ps", "-o", "lstart=", "-p", str(pid)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C"},
    )
    value = completed.stdout.decode("ascii", "strict").strip()
    if completed.returncode or not value or len(value) > 128:
        raise MigrationError("owner_identity", "cannot obtain process start identity")
    return value


def _boot_identity() -> str:
    if sys.platform.startswith("linux"):
        path = Path("/proc/sys/kernel/random/boot_id")
        try:
            value = path.read_text(encoding="ascii").strip()
        except OSError as exc:
            raise MigrationError("owner_identity", str(exc)) from exc
    elif sys.platform == "darwin":
        completed = subprocess.run(
            ["/usr/sbin/sysctl", "-n", "kern.boottime"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C"},
        )
        value = completed.stdout.decode("ascii", "strict").strip()
        if completed.returncode:
            raise MigrationError("owner_identity", "cannot obtain boot identity")
    else:
        raise MigrationError("unsupported_platform", sys.platform)
    if not value or len(value) > 256:
        raise MigrationError("owner_identity", "invalid boot identity")
    return value


_DIRECTORY_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_CLOEXEC", 0)
)
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
_OWNER_CONTEXT_KEYS = {
    "machine_host_identity",
    "reviewed_commit",
    "authority_binary_sha256",
    "identity_document_sha256",
    "lock_path_sha256",
}


def _absolute_state_path(path: Path, code: str) -> Path:
    candidate = Path(path)
    if ".." in candidate.parts:
        raise MigrationError(code, f"state path contains traversal: {path}")
    absolute = Path(os.path.abspath(os.fspath(candidate)))
    if not absolute.is_absolute():
        raise MigrationError(code, f"state path is not absolute: {path}")
    return absolute


def _at_or_below(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validate_owned_directory(info: os.stat_result, where: str, code: str) -> None:
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        raise MigrationError(code, f"{where} must be an owned mode-0700 directory")


def _validate_owned_file(info: os.stat_result, where: str, code: str) -> None:
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != 0o600
    ):
        raise MigrationError(code, f"{where} must be an owned mode-0600 regular file")


def _open_state_directory(
    path: Path,
    *,
    create: bool,
    validate_from: Path,
    code: str,
) -> int:
    """Traverse from / without following links and validate the managed suffix."""
    absolute = _absolute_state_path(path, code)
    managed_root = _absolute_state_path(validate_from, code)
    if not _at_or_below(absolute, managed_root):
        raise MigrationError(code, f"state path is outside managed root: {absolute}")
    descriptor = os.open(os.path.sep, _DIRECTORY_FLAGS)
    current = Path(os.path.sep)
    try:
        for component in absolute.parts[1:]:
            child_path = current / component
            try:
                child = os.open(component, _DIRECTORY_FLAGS, dir_fd=descriptor)
            except FileNotFoundError:
                if not create or not _at_or_below(child_path, managed_root):
                    raise
                try:
                    os.mkdir(component, 0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                child = os.open(component, _DIRECTORY_FLAGS, dir_fd=descriptor)
            except OSError as exc:
                raise MigrationError(
                    code,
                    f"state directory has a symlinked or unsafe ancestor: {absolute}",
                ) from exc
            if _at_or_below(child_path, managed_root):
                try:
                    _validate_owned_directory(
                        os.fstat(child), f"state directory {child_path}", code
                    )
                except BaseException:
                    os.close(child)
                    raise
            os.close(descriptor)
            descriptor = child
            current = child_path
        return descriptor
    except OSError as exc:
        os.close(descriptor)
        raise MigrationError(code, f"cannot open state directory: {absolute}") from exc
    except BaseException:
        os.close(descriptor)
        raise


def _open_child_directory(parent: int, name: str, *, create: bool, code: str) -> int:
    if not name or "/" in name or name in {".", ".."}:
        raise MigrationError(code, f"invalid state directory name: {name!r}")
    try:
        child = os.open(name, _DIRECTORY_FLAGS, dir_fd=parent)
    except FileNotFoundError:
        if not create:
            raise
        try:
            os.mkdir(name, 0o700, dir_fd=parent)
        except FileExistsError:
            pass
        child = os.open(name, _DIRECTORY_FLAGS, dir_fd=parent)
    except OSError as exc:
        raise MigrationError(code, f"unsafe state directory: {name}") from exc
    try:
        _validate_owned_directory(os.fstat(child), f"state directory {name}", code)
    except BaseException:
        os.close(child)
        raise
    return child


def _same_file(left: os.stat_result, right: os.stat_result) -> bool:
    return left.st_dev == right.st_dev and left.st_ino == right.st_ino


def _assert_directory_anchor(
    path: Path,
    descriptor: int,
    *,
    validate_from: Path,
    code: str,
) -> None:
    reopened = _open_state_directory(
        path, create=False, validate_from=validate_from, code=code
    )
    try:
        if not _same_file(os.fstat(descriptor), os.fstat(reopened)):
            raise MigrationError(code, f"state directory identity changed: {path}")
    finally:
        os.close(reopened)


def _stat_file_at(parent: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return None


def _read_owned_file(parent: int, name: str, where: str, code: str) -> bytes:
    before = _stat_file_at(parent, name)
    if before is None:
        raise MigrationError(code, f"missing {where}: {name}")
    _validate_owned_file(before, where, code)
    try:
        descriptor = os.open(
            name, os.O_RDONLY | _NOFOLLOW | _CLOEXEC, dir_fd=parent
        )
    except OSError as exc:
        raise MigrationError(code, f"cannot open {where}: {name}") from exc
    try:
        opened = os.fstat(descriptor)
        _validate_owned_file(opened, where, code)
        if not _same_file(before, opened):
            raise MigrationError(code, f"{where} changed during open: {name}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    finally:
        os.close(descriptor)


def _write_all(descriptor: int, raw: bytes) -> None:
    remaining = memoryview(raw)
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:
            raise OSError("short state-file write")
        remaining = remaining[written:]


def _write_new_owned_file(
    parent: int, name: str, raw: bytes, where: str, code: str
) -> None:
    try:
        descriptor = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW | _CLOEXEC,
            0o600,
            dir_fd=parent,
        )
    except OSError as exc:
        raise MigrationError(code, f"cannot create {where}: {name}") from exc
    try:
        os.fchmod(descriptor, 0o600)
        _validate_owned_file(os.fstat(descriptor), where, code)
        _write_all(descriptor, raw)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class EvidenceLedger:
    """Small content-addressed, prepared/committed hash-chain."""

    def __init__(
        self,
        directory: Path,
        owner_context: Mapping[str, Any],
        *,
        secure_root: Path | None = None,
    ):
        self.directory = _absolute_state_path(directory, "unsafe_state_path")
        self.events = self.directory / "events"
        self.owners = self.directory / "owners"
        self.head = self.directory / "head.json"
        self._validate_from = _absolute_state_path(
            secure_root if secure_root is not None else self.directory,
            "unsafe_state_path",
        )
        context = _as_dict(dict(owner_context), "owner_context")
        _exact_keys(context, _OWNER_CONTEXT_KEYS, "owner_context")
        if (
            not isinstance(context["reviewed_commit"], str)
            or not COMMIT_RE.fullmatch(context["reviewed_commit"])
            or any(
                not isinstance(context[key], str)
                or not SHA256_RE.fullmatch(context[key])
                for key in _OWNER_CONTEXT_KEYS - {"reviewed_commit"}
            )
        ):
            raise MigrationError("owner_identity", "owner context identity drift")
        self.owner_context = context
        self._root_fd: int | None = None
        self._events_fd: int | None = None
        self._owners_fd: int | None = None
        try:
            self._root_fd = _open_state_directory(
                self.directory,
                create=True,
                validate_from=self._validate_from,
                code="unsafe_state_path",
            )
            self._events_fd = _open_child_directory(
                self._root_fd, "events", create=True, code="unsafe_state_path"
            )
            self._owners_fd = _open_child_directory(
                self._root_fd, "owners", create=True, code="unsafe_state_path"
            )
            self._recover_temporaries()
            self.owner_uuid = _uuid7()
            owner = {
                "schema": "agentic.registration-migration-owner/v1",
                "owner_uuid": self.owner_uuid,
                "pid": os.getpid(),
                "process_start": _process_start(os.getpid()),
                "boot_identity": _boot_identity(),
                "effective_uid": os.geteuid(),
                **self.owner_context,
            }
            _write_new_owned_file(
                self._owners_fd,
                f"{self.owner_uuid}.json",
                canonical_bytes(owner),
                "owner record",
                "evidence_corrupt",
            )
            os.fsync(self._owners_fd)
            self.chain = self._load()
        except BaseException:
            self.close()
            raise

    def __enter__(self) -> "EvidenceLedger":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        for attribute in ("_events_fd", "_owners_fd", "_root_fd"):
            descriptor = getattr(self, attribute, None)
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
                setattr(self, attribute, None)

    def _assert_anchor(self) -> None:
        if self._root_fd is None or self._events_fd is None or self._owners_fd is None:
            raise MigrationError("unsafe_state_path", "evidence ledger is closed")
        _assert_directory_anchor(
            self.directory,
            self._root_fd,
            validate_from=self._validate_from,
            code="unsafe_state_path",
        )
        for name, descriptor in (
            ("events", self._events_fd),
            ("owners", self._owners_fd),
        ):
            current = os.stat(name, dir_fd=self._root_fd, follow_symlinks=False)
            _validate_owned_directory(
                current, f"evidence {name} directory", "unsafe_state_path"
            )
            if not _same_file(current, os.fstat(descriptor)):
                raise MigrationError(
                    "unsafe_state_path", f"evidence {name} directory changed"
                )

    def _recover_temporaries(self) -> None:
        self._assert_anchor()
        assert self._root_fd is not None
        assert self._events_fd is not None
        assert self._owners_fd is not None
        candidates = sorted(
            (scope, name, descriptor)
            for scope, descriptor in (
                ("root", self._root_fd),
                ("events", self._events_fd),
            )
            for name in os.listdir(descriptor)
            if name.startswith(".tmp")
        )
        for scope, name, parent in candidates:
            temporary_match = re.fullmatch(
                r"\.tmp-"
                r"(?P<owner>[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-"
                r"[89ab][0-9a-f]{3}-[0-9a-f]{12})-"
                r"(?P<sequence>\d{20})-(?P<digest>[0-9a-f]{64})",
                name,
            )
            if temporary_match is None:
                raise MigrationError(
                    "temporary_unknown",
                    f"unrecognized migration temporary file {name}",
                )
            owner_uuid = temporary_match.group("owner")
            if _stat_file_at(self._owners_fd, f"{owner_uuid}.json") is None:
                raise MigrationError(
                    "temporary_owner_unknown",
                    f"temporary owner record is missing: {owner_uuid}",
                )
            self._validate_owner(owner_uuid)
            try:
                raw = _read_owned_file(
                    parent, name, "migration temporary", "temporary_malformed"
                )
            except MigrationError as exc:
                raise MigrationError(
                    "temporary_unknown", f"cannot inspect temporary file {name}"
                ) from exc
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise MigrationError(
                    "temporary_malformed", f"invalid JSON in {name}"
                ) from exc
            if canonical_bytes(value) != raw:
                raise MigrationError(
                    "temporary_malformed", f"noncanonical temporary file {name}"
                )
            if scope == "events":
                if (
                    not isinstance(value, dict)
                    or value.get("owner_uuid") != owner_uuid
                    or value.get("sequence")
                    != int(temporary_match.group("sequence"))
                    or hashlib.sha256(raw).hexdigest()
                    != temporary_match.group("digest")
                ):
                    raise MigrationError(
                        "temporary_cross_owner",
                        f"event temporary binding mismatch {name}",
                    )
            else:
                if (
                    not isinstance(value, dict)
                    or set(value)
                    != {"schema", "owner_uuid", "sequence", "digest"}
                    or value.get("schema") != HEAD_SCHEMA
                ):
                    raise MigrationError(
                        "temporary_malformed",
                        f"head temporary schema mismatch {name}",
                    )
                if value["owner_uuid"] != owner_uuid:
                    raise MigrationError(
                        "temporary_cross_owner",
                        f"head temporary owner mismatch {name}",
                    )
                if (
                    not isinstance(value["sequence"], int)
                    or value["sequence"] < 0
                    or value["sequence"]
                    != int(temporary_match.group("sequence"))
                    or not isinstance(value["digest"], str)
                    or not SHA256_RE.fullmatch(value["digest"])
                    or hashlib.sha256(raw).hexdigest()
                    != temporary_match.group("digest")
                ):
                    raise MigrationError(
                        "temporary_malformed", f"head temporary binding mismatch {name}"
                    )
            liveness = self._owner_liveness(owner_uuid)
            if liveness == "live":
                raise MigrationError(
                    "temporary_owner_live",
                    f"temporary owner is still live: {owner_uuid}",
                )
            if liveness != "exact_dead":
                raise MigrationError(
                    "temporary_owner_unknown",
                    f"temporary owner liveness is unknown: {owner_uuid}",
                )
            os.unlink(name, dir_fd=parent)
            os.fsync(parent)

    def _load(self) -> list[dict[str, Any]]:
        self._assert_anchor()
        assert self._root_fd is not None
        assert self._events_fd is not None
        files = sorted(name for name in os.listdir(self._events_fd) if name.endswith(".json"))
        parsed: dict[int, tuple[str, dict[str, Any], str]] = {}
        for name in files:
            match = re.fullmatch(r"(\d{20})-([0-9a-f]{64})\.json", name)
            if not match:
                raise MigrationError("evidence_corrupt", f"invalid event file {name}")
            raw = _read_owned_file(
                self._events_fd, name, "evidence event", "evidence_corrupt"
            )
            actual = hashlib.sha256(raw).hexdigest()
            if actual != match.group(2):
                raise MigrationError("evidence_corrupt", f"event digest mismatch {name}")
            try:
                event = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise MigrationError("evidence_corrupt", str(exc)) from exc
            if canonical_bytes(event) != raw:
                raise MigrationError("evidence_corrupt", f"noncanonical event {name}")
            sequence = int(match.group(1))
            if sequence in parsed:
                raise MigrationError("evidence_corrupt", f"forked event sequence {sequence}")
            parsed[sequence] = (name, event, actual)
        chain: list[dict[str, Any]] = []
        previous = None
        for sequence in range(len(parsed)):
            if sequence not in parsed:
                raise MigrationError("evidence_corrupt", "event sequence gap")
            _, event, actual = parsed[sequence]
            _exact_keys(
                event,
                {
                    "schema",
                    "sequence",
                    "previous",
                    "owner_uuid",
                    "kind",
                    "phase",
                    "idempotency_key",
                    "payload",
                },
                "evidence_event",
            )
            if (
                event["schema"] != EVENT_SCHEMA
                or event["sequence"] != sequence
                or event["previous"] != previous
                or event["kind"] not in {"operation_prepared", "operation_committed"}
                or event["phase"] not in PHASES
                or not isinstance(event["owner_uuid"], str)
            ):
                raise MigrationError("evidence_corrupt", f"event invariant failed at {sequence}")
            self._validate_owner(event["owner_uuid"])
            chain.append(event)
            previous = actual
        expected_head = None if not chain else {"sequence": len(chain) - 1, "digest": previous}
        if _stat_file_at(self._root_fd, "head.json") is not None:
            try:
                head_raw = _read_owned_file(
                    self._root_fd, "head.json", "evidence head", "evidence_corrupt"
                )
                head = json.loads(head_raw)
            except json.JSONDecodeError as exc:
                raise MigrationError("evidence_corrupt", "invalid head") from exc
            if canonical_bytes(head) != head_raw:
                raise MigrationError("evidence_corrupt", "noncanonical head")
            _exact_keys(
                _as_dict(head, "evidence_head"),
                {"schema", "owner_uuid", "sequence", "digest"},
                "evidence_head",
            )
            if (
                head["schema"] != HEAD_SCHEMA
                or not isinstance(head["owner_uuid"], str)
                or not isinstance(head["sequence"], int)
                or head["sequence"] < 0
                or not isinstance(head["digest"], str)
                or not SHA256_RE.fullmatch(head["digest"])
            ):
                raise MigrationError("evidence_corrupt", "head invariant drift")
            self._validate_owner(head["owner_uuid"])
            pointer = {"sequence": head["sequence"], "digest": head["digest"]}
            if pointer != expected_head:
                # Exactly one durable next event without a head update is recovered.
                if len(chain) > 0 and pointer == {
                    "sequence": len(chain) - 2,
                    "digest": chain[-1]["previous"],
                }:
                    self._write_head(expected_head)
                else:
                    raise MigrationError("evidence_corrupt", "head outside hash chain")
        elif chain:
            if len(chain) == 1 and chain[0]["sequence"] == 0 and chain[0]["previous"] is None:
                self._write_head(expected_head)
            else:
                raise MigrationError("evidence_corrupt", "events exist without head")
        return chain

    def _validate_owner(self, owner_uuid: str) -> dict[str, Any]:
        if not re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            owner_uuid,
        ):
            raise MigrationError("evidence_corrupt", "invalid owner UUIDv7")
        try:
            assert self._owners_fd is not None
            raw = _read_owned_file(
                self._owners_fd,
                f"{owner_uuid}.json",
                "owner record",
                "evidence_corrupt",
            )
            value = json.loads(raw)
        except (MigrationError, json.JSONDecodeError) as exc:
            raise MigrationError("evidence_corrupt", f"invalid owner record: {owner_uuid}") from exc
        if canonical_bytes(value) != raw:
            raise MigrationError("evidence_corrupt", f"unsafe owner record: {owner_uuid}")
        _exact_keys(
            _as_dict(value, "owner_record"),
            {
                "schema",
                "owner_uuid",
                "pid",
                "process_start",
                "boot_identity",
                "effective_uid",
                *_OWNER_CONTEXT_KEYS,
            },
            "owner_record",
        )
        if (
            value["schema"] != "agentic.registration-migration-owner/v1"
            or value["owner_uuid"] != owner_uuid
            or not isinstance(value["pid"], int)
            or value["pid"] <= 0
            or value["effective_uid"] != os.geteuid()
            or not isinstance(value["process_start"], str)
            or not value["process_start"]
            or not isinstance(value["boot_identity"], str)
            or not value["boot_identity"]
            or any(value[key] != expected for key, expected in self.owner_context.items())
        ):
            raise MigrationError("evidence_corrupt", f"owner invariant drift: {owner_uuid}")
        return value

    def _owner_record(self, owner_uuid: str) -> dict[str, Any]:
        return self._validate_owner(owner_uuid)

    def _owner_liveness(self, owner_uuid: str) -> str:
        owner = self._owner_record(owner_uuid)
        try:
            current_boot = _boot_identity()
        except MigrationError:
            return "unknown"
        if owner["boot_identity"] != current_boot:
            return "exact_dead"
        pid = owner["pid"]
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return "exact_dead"
        except PermissionError:
            return "unknown"
        try:
            observed_start = _process_start(pid)
        except MigrationError:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return "exact_dead"
            except PermissionError:
                return "unknown"
            return "unknown"
        return "live" if observed_start == owner["process_start"] else "exact_dead"

    def _write_head(self, value: dict[str, Any]) -> None:
        self._assert_anchor()
        assert self._root_fd is not None
        if (
            set(value) != {"sequence", "digest"}
            or not isinstance(value["sequence"], int)
            or value["sequence"] < 0
            or not isinstance(value["digest"], str)
            or not SHA256_RE.fullmatch(value["digest"])
        ):
            raise MigrationError("evidence_corrupt", "invalid head pointer")
        record = {
            "schema": HEAD_SCHEMA,
            "owner_uuid": self.owner_uuid,
            **value,
        }
        raw = canonical_bytes(record)
        existing = _stat_file_at(self._root_fd, "head.json")
        if existing is not None:
            _validate_owned_file(existing, "evidence head", "evidence_corrupt")
        temporary = (
            f".tmp-{self.owner_uuid}-{value['sequence']:020d}-"
            f"{hashlib.sha256(raw).hexdigest()}"
        )
        _write_new_owned_file(
            self._root_fd,
            temporary,
            raw,
            "temporary evidence head",
            "evidence_corrupt",
        )
        os.replace(
            temporary,
            "head.json",
            src_dir_fd=self._root_fd,
            dst_dir_fd=self._root_fd,
        )
        os.fsync(self._root_fd)

    def append(
        self, kind: str, phase: str, idempotency_key: str, payload: Mapping[str, Any]
    ) -> dict[str, Any]:
        self._assert_anchor()
        assert self._events_fd is not None
        matches = [
            event
            for event in self.chain
            if event["kind"] == kind and event["idempotency_key"] == idempotency_key
        ]
        if matches:
            if len(matches) != 1 or matches[0]["phase"] != phase or matches[0]["payload"] != dict(payload):
                raise MigrationError("evidence_conflict", f"idempotency conflict: {idempotency_key}")
            return matches[0]
        sequence = len(self.chain)
        previous = None
        if self.chain:
            previous = hashlib.sha256(canonical_bytes(self.chain[-1])).hexdigest()
        event = {
            "schema": EVENT_SCHEMA,
            "sequence": sequence,
            "previous": previous,
            "owner_uuid": self.owner_uuid,
            "kind": kind,
            "phase": phase,
            "idempotency_key": idempotency_key,
            "payload": dict(payload),
        }
        raw = canonical_bytes(event)
        value_digest = hashlib.sha256(raw).hexdigest()
        final = f"{sequence:020d}-{value_digest}.json"
        temporary = f".tmp-{self.owner_uuid}-{sequence:020d}-{value_digest}"
        _write_new_owned_file(
            self._events_fd,
            temporary,
            raw,
            "temporary evidence event",
            "evidence_corrupt",
        )
        try:
            os.link(
                temporary,
                final,
                src_dir_fd=self._events_fd,
                dst_dir_fd=self._events_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise MigrationError("evidence_corrupt", f"event fork at {sequence}") from exc
        os.unlink(temporary, dir_fd=self._events_fd)
        os.fsync(self._events_fd)
        self._write_head({"sequence": sequence, "digest": value_digest})
        self.chain.append(event)
        return event

    def committed_phases(self) -> set[str]:
        return {
            event["phase"]
            for event in self.chain
            if event["kind"] == "operation_committed"
            and event["idempotency_key"].startswith("phase:")
        }


class MigrationLock:
    def __init__(self, path: Path, *, secure_root: Path | None = None):
        self.path = _absolute_state_path(path, "migration_lock")
        self._validate_from = _absolute_state_path(
            secure_root if secure_root is not None else self.path.parent,
            "migration_lock",
        )
        self._parent_fd: int | None = None
        self._descriptor: int | None = None
        self._locked = False
        try:
            self._parent_fd = _open_state_directory(
                self.path.parent,
                create=True,
                validate_from=self._validate_from,
                code="migration_lock",
            )
            existing = _stat_file_at(self._parent_fd, self.path.name)
            if existing is None:
                self._descriptor = os.open(
                    self.path.name,
                    os.O_RDWR | os.O_CREAT | os.O_EXCL | _NOFOLLOW | _CLOEXEC,
                    0o600,
                    dir_fd=self._parent_fd,
                )
                os.fchmod(self._descriptor, 0o600)
            else:
                _validate_owned_file(existing, "migration lock", "migration_lock")
                self._descriptor = os.open(
                    self.path.name,
                    os.O_RDWR | _NOFOLLOW | _CLOEXEC,
                    dir_fd=self._parent_fd,
                )
                if not _same_file(existing, os.fstat(self._descriptor)):
                    raise MigrationError("migration_lock", "lock changed during open")
            _validate_owned_file(
                os.fstat(self._descriptor), "migration lock", "migration_lock"
            )
        except BaseException:
            self.close()
            raise

    def _assert_anchor(self) -> None:
        if self._parent_fd is None or self._descriptor is None:
            raise MigrationError("migration_lock", "lock is closed")
        _assert_directory_anchor(
            self.path.parent,
            self._parent_fd,
            validate_from=self._validate_from,
            code="migration_lock",
        )
        current = os.stat(
            self.path.name, dir_fd=self._parent_fd, follow_symlinks=False
        )
        _validate_owned_file(current, "migration lock", "migration_lock")
        if not _same_file(current, os.fstat(self._descriptor)):
            raise MigrationError("migration_lock", "lock path identity changed")

    def __enter__(self) -> "MigrationLock":
        try:
            self._assert_anchor()
            assert self._descriptor is not None
            fcntl.flock(self._descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.close()
            raise MigrationError("migration_busy", "another migration owns the lock") from exc
        except BaseException:
            self.close()
            raise
        self._locked = True
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        if self._descriptor is not None:
            if self._locked:
                try:
                    fcntl.flock(self._descriptor, fcntl.LOCK_UN)
                except OSError:
                    pass
            try:
                os.close(self._descriptor)
            except OSError:
                pass
            self._descriptor = None
            self._locked = False
        if self._parent_fd is not None:
            try:
                os.close(self._parent_fd)
            except OSError:
                pass
            self._parent_fd = None


PHASE_OPERATION = {
    "bootstrap_verified": "verify_bootstrap",
    "authority_schema_installed": "install_authority_schema",
    "review_recorded": "conditional_transaction",
    "tracker_attested": "attest_tracker",
    "created": "conditional_transaction",
    "wired": "conditional_transaction",
    "registered": "conditional_transaction",
    "task01_wired": "conditional_transaction",
    "redirected": "conditional_transaction",
    "manual_blocked": "conditional_transaction",
    "container_verified": "verify_container",
    "prepared": "prepare_release",
    "released": "conditional_update",
}


def copy_without_attestation(value: Mapping[str, Any]) -> dict[str, Any]:
    copied = dict(value)
    copied.pop("attestation", None)
    return copied


def _external_ref(path: str) -> str:
    return "spec-task:" + path


def _dependency_ref(token: str, replacements: Mapping[str, str], retained: Mapping[str, Any]) -> str:
    if token == "01":
        return _external_ref(retained["path"])
    if re.fullmatch(r"\d{2}", token):
        return _external_ref(replacements[token])
    return _external_ref(token)


def primitive_requests(manifest: ValidatedManifest, phase: str) -> list[dict[str, Any]]:
    """Construct migration semantics from the closed manifest.

    Returned objects are generic Task-00D authority primitives.  The adapter
    validates revisions and executes them; it does not decide the graph.
    """
    data = manifest.data
    replacements = {f"{_task_number(item['path']):02d}": item["path"] for item in data["replacements"]}
    if phase == "authority_schema_installed":
        return [
            {
                "primitive": "install_authority_schema",
                "profile": "full",
                "bootstrap_receipt_sha256": data["attestation"][
                    "bootstrap_receipt_sha256"
                ],
            }
        ]
    if phase == "review_recorded":
        return [
            {
                "primitive": "conditional_append_comment",
                "issue_id": data["retained"]["id"],
                "expected_live_fields_sha256": data["attestation"][
                    "task01_live_fields_sha256"
                ],
                "comment": "{review_artifact}",
                "unique_schema": "agentic.registration-review/v1",
            }
        ]
    if phase == "created":
        result = []
        for item in data["replacements"]:
            task_path = manifest.root / item["path"]
            text = task_path.read_text(encoding="utf-8")
            definition = _canonical_task_definition(
                manifest.root,
                item["path"],
                item["depends_on"],
                replacements,
                data["retained"]["path"],
            )
            acceptance = text.split("## Acceptance\n", 1)[1].strip()
            result.append(
                {
                    "primitive": "create_if_external_ref_absent",
                    "external_ref": _external_ref(item["path"]),
                    "fields": {
                        "title": definition["title"],
                        "description": definition["goal"],
                        "acceptance": acceptance,
                        "task_type": "task",
                        "priority": 0,
                        "metadata": {
                            "registration_state": "pending",
                            "budget": definition["budget"],
                            "source": item["path"],
                            "touch": definition["touch"],
                            "definition_hash": _definition_hash(definition),
                            "rigor": definition["rigor"],
                        },
                    },
                    "initial_dependencies": [
                        {
                            "external_ref": _external_ref(data["retained"]["path"]),
                            "kind": "blocks",
                        },
                        {
                            "issue_id": data["feature_container"]["id"],
                            "kind": "related",
                        },
                    ],
                }
            )
        return result
    if phase == "wired":
        return [
            {
                "primitive": "ensure_blocking_edge",
                "issue_external_ref": _external_ref(item["path"]),
                "dependency_external_ref": _dependency_ref(dep, replacements, data["retained"]),
            }
            for item in data["replacements"]
            for dep in item["depends_on"]
            if dep != "01"
        ]
    if phase == "registered":
        return [
            {
                "primitive": "conditional_metadata_transition",
                "external_ref": _external_ref(item["path"]),
                "from": {"registration_state": "pending"},
                "to": {"registration_state": "complete"},
            }
            for item in data["replacements"]
        ]
    if phase == "task01_wired":
        return [
            {
                "primitive": "ensure_blocking_edge",
                "issue_id": data["retained"]["id"],
                "dependency_external_ref": _external_ref(data["bootstrap"][-1]["path"]),
            },
            {
                "primitive": "retype_edge",
                "issue_id": data["retained"]["id"],
                "dependency_id": data["feature_container"]["id"],
                "from": "parent-child",
                "to": "related",
            },
        ]
    if phase == "redirected":
        package = data["known_external_rewires"][0]
        requests = [
            {
                "primitive": "conditional_rewire",
                "consumer_id": package["consumer"],
                "old_dependency_id": package["old_id"],
                "replacement_external_ref": _external_ref(package["replacement"]),
                "old_relation": "related",
                "replacement_relation": "blocks",
            }
        ]
        ordinary = data["known_external_rewires"][1]
        requests.append(
            {
                "primitive": "ensure_blocking_edge",
                "issue_id": ordinary["consumer"],
                "dependency_external_ref": _external_ref(ordinary["replacement"]),
            }
        )
        requests.extend(
            {
                "primitive": "conditional_supersede_with_redirect",
                "historical_id": item["id"],
                "historical_external_ref": _external_ref(item["path"]),
                "replacement_external_ref": _external_ref(item["replacement"]),
                "enumerate_live_consumers": item["id"] != package["old_id"],
            }
            for item in data["historical"]
        )
        return requests
    if phase == "manual_blocked":
        return [
            {
                "primitive": "conditional_manual_block",
                "external_ref": _external_ref(item["path"]),
                "human_selector": item["contains"],
                "note_type": "run",
            }
            for item in data["manual_blockers"]
        ]
    if phase == "released":
        return [
            {
                "primitive": "conditional_issue_update",
                "issue_id": data["retained"]["id"],
                "expected_live_fields_sha256": data["attestation"]["task01_live_fields_sha256"],
                "from": {"status": "blocked", "assignee": ""},
                "to": {"status": "open", "assignee": ""},
                "actor": "agentic:migration:{reviewed_commit}",
                "require_single_history_event": True,
            }
        ]
    return []


def _require_sorted_unique(values: list[Any], where: str) -> None:
    encoded = [canonical_bytes(value) for value in values]
    if encoded != sorted(encoded) or len(encoded) != len(set(encoded)):
        raise MigrationError("authority_snapshot", f"{where} must be canonical sorted/unique")


def _validate_storage_receipt(
    value: Any,
    *,
    phase: str,
    primitive_index: int,
    primitive_sha256: str,
) -> dict[str, Any]:
    receipt = _as_dict(value, "storage_transaction_receipt")
    _exact_keys(
        receipt,
        {
            "schema",
            "transaction_id",
            "phase",
            "primitive_index",
            "primitive_sha256",
            "before_domain_sha256",
            "after_domain_sha256",
            "history_cursor",
        },
        "storage_transaction_receipt",
    )
    if (
        receipt["schema"] != "agentic.registration-storage-transaction/v1"
        or receipt["phase"] != phase
        or receipt["primitive_index"] != primitive_index
        or receipt["primitive_sha256"] != primitive_sha256
        or not isinstance(receipt["transaction_id"], str)
        or not receipt["transaction_id"]
        or len(receipt["transaction_id"].encode("utf-8")) > 512
        or not isinstance(receipt["history_cursor"], str)
        or not receipt["history_cursor"]
        or len(receipt["history_cursor"].encode("utf-8")) > 512
        or any(
            not isinstance(receipt[key], str)
            or not SHA256_RE.fullmatch(receipt[key])
            for key in ("before_domain_sha256", "after_domain_sha256")
        )
    ):
        raise MigrationError("authority_receipt", "storage transaction receipt drift")
    return receipt


def _validate_authority_snapshot(
    value: Any,
    *,
    phase: str,
    primitive_index: int,
    primitive_sha256: str,
) -> dict[str, Any]:
    snapshot = _as_dict(value, "authority_snapshot")
    _exact_keys(
        snapshot,
        {
            "schema",
            "phase",
            "primitive_index",
            "primitive_sha256",
            "issues",
            "edges",
            "history",
            "comments",
            "scoped_ready",
            "storage_receipts",
            "domain_sha256",
        },
        "authority_snapshot",
    )
    if (
        snapshot["schema"] != "agentic.registration-authority-snapshot/v1"
        or snapshot["phase"] != phase
        or snapshot["primitive_index"] != primitive_index
        or snapshot["primitive_sha256"] != primitive_sha256
    ):
        raise MigrationError("authority_snapshot", "snapshot phase/primitive binding drift")
    issues = _as_list(snapshot["issues"], "authority_snapshot.issues")
    for index, issue_value in enumerate(issues):
        issue = _as_dict(issue_value, f"authority_snapshot.issues[{index}]")
        _exact_keys(
            issue,
            {
                "id",
                "external_ref",
                "revision",
                "history_cursor",
                "fields",
                "metadata",
            },
            f"authority_snapshot.issues[{index}]",
        )
        if (
            not all(
                isinstance(issue[key], str) and issue[key]
                for key in ("id", "revision", "history_cursor")
            )
            or (
                issue["external_ref"] is not None
                and not isinstance(issue["external_ref"], str)
            )
        ):
            raise MigrationError("authority_snapshot", "issue identity/revision drift")
        fields = _as_dict(issue["fields"], "authority_snapshot.issue.fields")
        _exact_keys(
            fields,
            ISSUE_FIELD_KEYS,
            "authority_snapshot.issue.fields",
        )
        if (
            not isinstance(fields["priority"], int)
            or isinstance(fields["priority"], bool)
            or fields["priority"] < 0
            or any(
                fields[key] is not None and not isinstance(fields[key], str)
                for key in ISSUE_FIELD_KEYS - {"priority"}
            )
        ):
            raise MigrationError("authority_snapshot", "issue live-field type drift")
        metadata = _as_dict(
            issue["metadata"], "authority_snapshot.issue.metadata"
        )
        if len(canonical_bytes(metadata)) > 1024 * 1024:
            raise MigrationError("authority_snapshot", "issue metadata is unbounded")
    _require_sorted_unique(issues, "issues")
    edges = _as_list(snapshot["edges"], "authority_snapshot.edges")
    for index, edge_value in enumerate(edges):
        edge = _as_dict(edge_value, f"authority_snapshot.edges[{index}]")
        _exact_keys(
            edge,
            {"issue_id", "dependency_id", "kind", "revision"},
            f"authority_snapshot.edges[{index}]",
        )
        if not all(isinstance(edge[key], str) and edge[key] for key in edge):
            raise MigrationError("authority_snapshot", "edge identity/revision drift")
    _require_sorted_unique(edges, "edges")
    history = _as_list(snapshot["history"], "authority_snapshot.history")
    for index, history_value in enumerate(history):
        row = _as_dict(history_value, f"authority_snapshot.history[{index}]")
        _exact_keys(
            row,
            {"issue_id", "cursor", "event_digest"},
            f"authority_snapshot.history[{index}]",
        )
        if (
            not isinstance(row["issue_id"], str)
            or not row["issue_id"]
            or not isinstance(row["cursor"], str)
            or not row["cursor"]
            or not isinstance(row["event_digest"], str)
            or not SHA256_RE.fullmatch(row["event_digest"])
        ):
            raise MigrationError("authority_snapshot", "history identity/digest drift")
    _require_sorted_unique(history, "history")
    comments = _as_list(snapshot["comments"], "authority_snapshot.comments")
    for index, comment_value in enumerate(comments):
        comment = _as_dict(comment_value, f"authority_snapshot.comments[{index}]")
        _exact_keys(
            comment,
            {"issue_id", "schema", "digest"},
            f"authority_snapshot.comments[{index}]",
        )
        if (
            not isinstance(comment["issue_id"], str)
            or not comment["issue_id"]
            or not isinstance(comment["schema"], str)
            or not comment["schema"]
            or not isinstance(comment["digest"], str)
            or not SHA256_RE.fullmatch(comment["digest"])
        ):
            raise MigrationError("authority_snapshot", "comment identity/digest drift")
    _require_sorted_unique(comments, "comments")
    ready = _as_list(snapshot["scoped_ready"], "authority_snapshot.scoped_ready")
    if (
        any(not isinstance(issue_id, str) or not issue_id for issue_id in ready)
        or ready != sorted(set(ready))
    ):
        raise MigrationError("authority_snapshot", "scoped-ready domain drift")
    receipts = _as_list(
        snapshot["storage_receipts"], "authority_snapshot.storage_receipts"
    )
    for receipt in receipts:
        receipt_value = _as_dict(receipt, "authority_snapshot.storage_receipt")
        receipt_phase = receipt_value.get("phase")
        receipt_index = receipt_value.get("primitive_index")
        receipt_digest = receipt_value.get("primitive_sha256")
        if (
            not isinstance(receipt_phase, str)
            or receipt_phase not in PHASES
            or not isinstance(receipt_index, int)
            or receipt_index < 0
            or not isinstance(receipt_digest, str)
            or not SHA256_RE.fullmatch(receipt_digest)
        ):
            raise MigrationError("authority_snapshot", "stored receipt identity drift")
        _validate_storage_receipt(
            receipt,
            phase=receipt_phase,
            primitive_index=receipt_index,
            primitive_sha256=receipt_digest,
        )
    _require_sorted_unique(receipts, "storage_receipts")
    domain = {
        "phase": phase,
        "primitive_index": primitive_index,
        "primitive_sha256": primitive_sha256,
        "issues": issues,
        "edges": edges,
        "history": history,
        "comments": comments,
        "scoped_ready": ready,
    }
    if (
        not isinstance(snapshot["domain_sha256"], str)
        or snapshot["domain_sha256"] != digest(domain)
    ):
        raise MigrationError("authority_snapshot", "snapshot domain digest drift")
    return snapshot


class Reconciler:
    def __init__(
        self,
        manifest: ValidatedManifest,
        authority: Authority,
        ledger: EvidenceLedger,
        source_gate: SourceGate,
        *,
        crash: Callable[[str], None] | None = None,
    ):
        self.manifest = manifest
        self.authority = authority
        self.ledger = ledger
        self.source_gate = source_gate
        self.crash = crash or (lambda _point: None)

    def _assert_task01_snapshot(
        self, snapshot: Mapping[str, Any], phase: str
    ) -> None:
        task01 = [
            issue
            for issue in snapshot["issues"]
            if issue["id"] == self.manifest.data["retained"]["id"]
        ]
        if len(task01) != 1:
            raise MigrationError(
                "tracker_drift", "exact Task01 issue absent from authority snapshot"
            )
        if (
            phase != "released"
            and digest(task01[0]["fields"])
            != self.manifest.data["attestation"]["task01_live_fields_sha256"]
        ):
            raise MigrationError(
                "tracker_drift", "Task01 live fields differ from attested snapshot"
            )

    def _phase_inspection(
        self, phase: str, payload: Mapping[str, Any]
    ) -> dict[str, Any]:
        requests = payload["primitive_requests"]
        requests_sha256 = digest(requests)
        state = self.authority.request(
            "inspect_phase",
            {
                "phase": phase,
                "primitive_count": len(requests),
                "primitive_requests_sha256": requests_sha256,
                "manifest": payload,
            },
        )
        _exact_keys(
            state,
            {
                "schema",
                "phase",
                "complete",
                "primitive_count",
                "applied_prefix",
                "snapshot",
            },
            "authority_phase_inspection",
        )
        if (
            state["schema"]
            != "agentic.registration-authority-phase-inspection/v1"
            or state["phase"] != phase
            or not isinstance(state["complete"], bool)
            or state["primitive_count"] != len(requests)
            or not isinstance(state["applied_prefix"], int)
            or isinstance(state["applied_prefix"], bool)
            or not 0 <= state["applied_prefix"] <= len(requests)
            or state["complete"] != (state["applied_prefix"] == len(requests))
        ):
            raise MigrationError(
                "tracker_drift", f"invalid phase inspection for {phase}"
            )
        snapshot = _validate_authority_snapshot(
            state["snapshot"],
            phase=phase,
            primitive_index=-1,
            primitive_sha256=requests_sha256,
        )
        self._assert_task01_snapshot(snapshot, phase)
        release_prepared = any(
            event["phase"] == "released"
            and event["kind"] == "operation_prepared"
            and event["idempotency_key"].startswith("primitive:")
            for event in self.ledger.chain
        )
        if phase != "released":
            if not release_prepared and snapshot["scoped_ready"]:
                raise MigrationError(
                    "early_exposure", f"{phase} exposed scoped ready work"
                )
        elif state["complete"]:
            if snapshot["scoped_ready"] not in (
                [],
                [self.manifest.data["retained"]["id"]],
            ):
                raise MigrationError(
                    "release_invariant", "released scoped-ready domain drift"
                )
        if (
            state["complete"]
            and PHASES.index(phase) >= PHASES.index("review_recorded")
        ):
            reviews = [
                row
                for row in snapshot["comments"]
                if row["issue_id"] == self.manifest.data["retained"]["id"]
                and row["schema"] == "agentic.registration-review/v1"
            ]
            if len(reviews) != 1:
                raise MigrationError(
                    "review_invariant", "READY review record count drift"
                )
        return state

    def _primitive_inspection(
        self,
        phase: str,
        primitive_index: int,
        primitive: Mapping[str, Any],
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        primitive_sha256 = digest(primitive)
        state = self.authority.request(
            "inspect_primitive",
            {
                "phase": phase,
                "primitive_index": primitive_index,
                "primitive_sha256": primitive_sha256,
                "manifest": payload,
            },
        )
        _exact_keys(
            state,
            {
                "schema",
                "phase",
                "primitive_index",
                "primitive_sha256",
                "applied",
                "snapshot",
                "receipt",
            },
            "authority_primitive_inspection",
        )
        if (
            state["schema"]
            != "agentic.registration-authority-primitive-inspection/v1"
            or state["phase"] != phase
            or state["primitive_index"] != primitive_index
            or state["primitive_sha256"] != primitive_sha256
            or not isinstance(state["applied"], bool)
        ):
            raise MigrationError(
                "authority_snapshot",
                f"primitive inspection binding drift: {phase}/{primitive_index}",
            )
        snapshot = _validate_authority_snapshot(
            state["snapshot"],
            phase=phase,
            primitive_index=primitive_index,
            primitive_sha256=primitive_sha256,
        )
        self._assert_task01_snapshot(snapshot, phase)
        if state["applied"]:
            receipt = _validate_storage_receipt(
                state["receipt"],
                phase=phase,
                primitive_index=primitive_index,
                primitive_sha256=primitive_sha256,
            )
            if receipt not in state["snapshot"]["storage_receipts"]:
                raise MigrationError(
                    "authority_receipt", "applied receipt absent from exact snapshot"
                )
        elif state["receipt"] is not None:
            raise MigrationError(
                "authority_receipt", "unapplied primitive returned a receipt"
            )
        return state

    def _primitive_events(
        self, key: str
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        prepared = [
            event
            for event in self.ledger.chain
            if event["kind"] == "operation_prepared"
            and event["idempotency_key"] == key
        ]
        committed = [
            event
            for event in self.ledger.chain
            if event["kind"] == "operation_committed"
            and event["idempotency_key"] == key
        ]
        if len(prepared) > 1 or len(committed) > 1 or (committed and not prepared):
            raise MigrationError(
                "evidence_corrupt", f"primitive evidence cardinality drift: {key}"
            )
        return (
            prepared[0] if prepared else None,
            committed[0] if committed else None,
        )

    def _apply_primitive(
        self,
        phase: str,
        primitive_index: int,
        primitive: Mapping[str, Any],
        payload: Mapping[str, Any],
    ) -> None:
        primitive_sha256 = digest(primitive)
        key = f"primitive:{phase}:{primitive_index:04d}:{primitive_sha256}"
        prepared, committed = self._primitive_events(key)
        current = self._primitive_inspection(
            phase, primitive_index, primitive, payload
        )
        if committed:
            if (
                not current["applied"]
                or current["snapshot"]
                != committed["payload"]["after_snapshot"]
                or current["receipt"] != committed["payload"]["receipt"]
            ):
                raise MigrationError(
                    "tracker_drift",
                    f"committed primitive drift: {phase}/{primitive_index}",
                )
            return
        if prepared is None:
            if current["applied"]:
                raise MigrationError(
                    "unprepared_mutation",
                    f"primitive applied without evidence: {phase}/{primitive_index}",
                )
            plan = self.authority.request(
                "plan_primitive",
                {
                    "phase": phase,
                    "primitive_index": primitive_index,
                    "primitive": dict(primitive),
                    "primitive_sha256": primitive_sha256,
                    "before_snapshot": current["snapshot"],
                    "manifest": payload,
                },
            )
            _exact_keys(
                plan,
                {
                    "schema",
                    "phase",
                    "primitive_index",
                    "primitive_sha256",
                    "before_snapshot",
                    "intended_snapshot",
                    "receipt",
                },
                "authority_primitive_plan",
            )
            if (
                plan["schema"]
                != "agentic.registration-authority-primitive-plan/v1"
                or plan["phase"] != phase
                or plan["primitive_index"] != primitive_index
                or plan["primitive_sha256"] != primitive_sha256
                or plan["before_snapshot"] != current["snapshot"]
            ):
                raise MigrationError(
                    "authority_plan",
                    f"primitive plan binding drift: {phase}/{primitive_index}",
                )
            _validate_authority_snapshot(
                plan["before_snapshot"],
                phase=phase,
                primitive_index=primitive_index,
                primitive_sha256=primitive_sha256,
            )
            intended = _validate_authority_snapshot(
                plan["intended_snapshot"],
                phase=phase,
                primitive_index=primitive_index,
                primitive_sha256=primitive_sha256,
            )
            self._assert_task01_snapshot(intended, phase)
            receipt = _validate_storage_receipt(
                plan["receipt"],
                phase=phase,
                primitive_index=primitive_index,
                primitive_sha256=primitive_sha256,
            )
            if (
                receipt["before_domain_sha256"]
                != current["snapshot"]["domain_sha256"]
                or receipt["after_domain_sha256"] != intended["domain_sha256"]
                or receipt not in intended["storage_receipts"]
            ):
                raise MigrationError(
                    "authority_plan",
                    f"primitive plan receipt mismatch: {phase}/{primitive_index}",
                )
            prepared_payload = {
                "primitive": dict(primitive),
                "primitive_sha256": primitive_sha256,
                "primitive_index": primitive_index,
                "before_snapshot": current["snapshot"],
                "intended_snapshot": intended,
                "receipt": receipt,
                "manifest_sha256": file_digest(self.manifest.path),
            }
            prepared = self.ledger.append(
                "operation_prepared", phase, key, prepared_payload
            )
            self.crash(f"{phase}:primitive:{primitive_index}:after_prepared")
        else:
            if (
                prepared["payload"]["primitive"] != dict(primitive)
                or prepared["payload"]["primitive_sha256"] != primitive_sha256
                or prepared["payload"]["primitive_index"] != primitive_index
            ):
                raise MigrationError(
                    "evidence_conflict",
                    f"prepared primitive identity drift: {phase}/{primitive_index}",
                )
            if current["applied"]:
                if (
                    current["snapshot"]
                    != prepared["payload"]["intended_snapshot"]
                    or current["receipt"] != prepared["payload"]["receipt"]
                ):
                    raise MigrationError(
                        "tracker_drift",
                        f"partial primitive post-state drift: {phase}/{primitive_index}",
                    )
                self.ledger.append(
                    "operation_committed",
                    phase,
                    key,
                    {
                        "prepared_sha256": hashlib.sha256(
                            canonical_bytes(prepared)
                        ).hexdigest(),
                        "after_snapshot": current["snapshot"],
                        "receipt": current["receipt"],
                    },
                )
                self.crash(
                    f"{phase}:primitive:{primitive_index}:after_committed"
                )
                return
            if current["snapshot"] != prepared["payload"]["before_snapshot"]:
                raise MigrationError(
                    "tracker_drift",
                    f"partial primitive before-state drift: {phase}/{primitive_index}",
                )
        response = self.authority.request(
            "apply_primitive",
            {
                "idempotency_key": key,
                "phase": phase,
                "primitive_index": primitive_index,
                "primitive": dict(primitive),
                "primitive_sha256": primitive_sha256,
                "before_snapshot": prepared["payload"]["before_snapshot"],
                "intended_snapshot": prepared["payload"]["intended_snapshot"],
                "receipt": prepared["payload"]["receipt"],
                "manifest": payload,
            },
        )
        _exact_keys(
            response,
            {"schema", "accepted", "receipt"},
            "authority_apply_response",
        )
        if (
            response["schema"]
            != "agentic.registration-authority-apply/v1"
            or response["accepted"] is not True
            or response["receipt"] != prepared["payload"]["receipt"]
        ):
            raise MigrationError(
                "authority_rejected",
                f"primitive rejected: {phase}/{primitive_index}",
            )
        self.crash(f"{phase}:primitive:{primitive_index}:after_mutation")
        after = self._primitive_inspection(
            phase, primitive_index, primitive, payload
        )
        if (
            not after["applied"]
            or after["snapshot"] != prepared["payload"]["intended_snapshot"]
            or after["receipt"] != prepared["payload"]["receipt"]
        ):
            raise MigrationError(
                "tracker_drift",
                f"primitive post-state differs from plan: {phase}/{primitive_index}",
            )
        self.ledger.append(
            "operation_committed",
            phase,
            key,
            {
                "prepared_sha256": hashlib.sha256(
                    canonical_bytes(prepared)
                ).hexdigest(),
                "after_snapshot": after["snapshot"],
                "receipt": after["receipt"],
            },
        )
        self.crash(f"{phase}:primitive:{primitive_index}:after_committed")

    def _commit_phase(
        self, phase: str, payload: Mapping[str, Any]
    ) -> None:
        key = f"phase:{phase}:{digest(payload)}"
        prepared, committed = self._primitive_events(key)
        inspection = self._phase_inspection(phase, payload)
        if not inspection["complete"]:
            raise MigrationError(
                "tracker_drift", f"phase prefix incomplete: {phase}"
            )
        if committed:
            if committed["payload"]["after_snapshot"] != inspection["snapshot"]:
                raise MigrationError(
                    "tracker_drift", f"committed phase snapshot drift: {phase}"
                )
            return
        if prepared is None:
            phase_binding = {
                "phase_payload_sha256": digest(payload),
            }
            if phase == "bootstrap_verified":
                phase_binding.update(
                    {
                        "bootstrap_receipt": payload["bootstrap_receipt"],
                        "bootstrap_receipt_sha256": payload[
                            "bootstrap_receipt_sha256"
                        ],
                    }
                )
            prepared = self.ledger.append(
                "operation_prepared",
                phase,
                key,
                {
                    "primitive_count": len(payload["primitive_requests"]),
                    "primitive_requests_sha256": digest(
                        payload["primitive_requests"]
                    ),
                    "after_snapshot": inspection["snapshot"],
                    "manifest_sha256": file_digest(self.manifest.path),
                    **phase_binding,
                },
            )
            self.crash(f"{phase}:after_prepared")
        elif prepared["payload"]["after_snapshot"] != inspection["snapshot"]:
            raise MigrationError(
                "tracker_drift", f"prepared phase snapshot drift: {phase}"
            )
        self.ledger.append(
            "operation_committed",
            phase,
            key,
            {
                "prepared_sha256": hashlib.sha256(
                    canonical_bytes(prepared)
                ).hexdigest(),
                "after_snapshot": inspection["snapshot"],
            },
        )
        self.crash(f"{phase}:after_committed")

    def _source_phase(self, payload: Mapping[str, Any]) -> None:
        key = f"phase:source_attested:{digest(payload)}"
        prepared, committed = self._primitive_events(key)
        if committed:
            if committed["payload"]["after_snapshot"] != dict(payload):
                raise MigrationError("source_attestation", "source evidence drift")
            return
        if prepared is None:
            prepared = self.ledger.append(
                "operation_prepared",
                "source_attested",
                key,
                {
                    "before_snapshot": {"attested": False},
                    "after_snapshot": dict(payload),
                },
            )
            self.crash("source_attested:after_prepared")
        self.ledger.append(
            "operation_committed",
            "source_attested",
            key,
            {
                "prepared_sha256": hashlib.sha256(
                    canonical_bytes(prepared)
                ).hexdigest(),
                "after_snapshot": dict(payload),
            },
        )
        self.crash("source_attested:after_committed")

    def run(
        self,
        reviewed_commit: str,
        review_artifact: Mapping[str, Any],
        bootstrap_receipt: Mapping[str, Any],
        bootstrap_receipt_sha256: str,
    ) -> dict[str, Any]:
        source = {
            **self.source_gate.attest(self.manifest, reviewed_commit),
            "bootstrap_receipt": dict(bootstrap_receipt),
            "bootstrap_receipt_sha256": bootstrap_receipt_sha256,
        }
        self._source_phase(source)
        common = {
            "reviewed_commit": reviewed_commit,
            "source_commit": self.manifest.data["attestation"]["source_commit"],
            "retained": self.manifest.data["retained"],
            "bootstrap": self.manifest.data["bootstrap"],
            "bootstrap_receipt": dict(bootstrap_receipt),
            "bootstrap_receipt_sha256": bootstrap_receipt_sha256,
            "replacements": self.manifest.data["replacements"],
            "historical": self.manifest.data["historical"],
            "known_external_rewires": self.manifest.data["known_external_rewires"],
            "manual_blockers": self.manifest.data["manual_blockers"],
            "feature_container": self.manifest.data["feature_container"],
            "starting_tracker_snapshot": self.manifest.data["attestation"][
                "starting_tracker_snapshot"
            ],
            "review_artifact": dict(review_artifact),
            "review_artifact_sha256": digest(review_artifact),
        }
        for phase in PHASES[1:]:
            requests = primitive_requests(self.manifest, phase)
            for request in requests:
                if request.get("actor") == "agentic:migration:{reviewed_commit}":
                    request["actor"] = f"agentic:migration:{reviewed_commit}"
                if request.get("comment") == "{review_artifact}":
                    request["comment"] = dict(review_artifact)
            phase_payload = {
                **common,
                "phase": phase,
                "primitive_requests": requests,
            }
            for primitive_index, primitive in enumerate(requests):
                self._apply_primitive(
                    phase,
                    primitive_index,
                    primitive,
                    phase_payload,
                )
            self._commit_phase(phase, phase_payload)
        released = [
            event
            for event in self.ledger.chain
            if event["phase"] == "released"
            and event["kind"] == "operation_committed"
            and event["idempotency_key"].startswith("phase:")
        ]
        if len(released) != 1:
            raise MigrationError(
                "release_invariant", "exactly one release phase receipt required"
            )
        return {
            "schema": EVENT_SCHEMA,
            "status": "released",
            "reviewed_commit": reviewed_commit,
            "event_count": len(self.ledger.chain),
        }


def _identity(authority: Authority) -> dict[str, Any]:
    value = authority.request("identity_no_migrate", {})
    expected = {
        "backend_mode",
        "database_identity",
        "project_identity",
        "repository_identity",
        "core_schema_fingerprint",
        "full_schema_fingerprint",
        "state_root",
    }
    _exact_keys(value, expected, "authority_identity")
    bounded = {key: value[key] for key in expected - {"state_root"}}
    if any(not isinstance(item, str) or not item or len(item.encode()) > 512 for item in bounded.values()):
        raise MigrationError("authority_identity", "identity values must be bounded nonempty strings")
    if any(
        not SHA256_RE.fullmatch(value[key])
        for key in ("core_schema_fingerprint", "full_schema_fingerprint")
    ):
        raise MigrationError(
            "authority_identity", "schema fingerprints must be lowercase SHA-256"
        )
    state_root = Path(value["state_root"])
    if not state_root.is_absolute():
        raise MigrationError("authority_identity", "state_root must be absolute")
    expected_root = _r8_state_root()
    if state_root != expected_root:
        raise MigrationError(
            "authority_identity",
            f"authority state root differs from independent R8 resolver: {state_root}",
        )
    return value


def _r8_state_root() -> Path:
    try:
        account = pwd.getpwuid(os.geteuid())
    except KeyError as exc:
        raise MigrationError("state_root", "effective user is absent from OS account database") from exc
    home = Path(account.pw_dir)
    if not home.is_absolute() or home.is_symlink():
        raise MigrationError("state_root", "physical account home is not an absolute regular directory")
    physical_home = home.resolve(strict=True)
    if sys.platform == "darwin":
        relative = Path("Library") / "Application Support" / "agentic"
    elif sys.platform.startswith("linux"):
        relative = Path(".local") / "state" / "agentic"
    else:
        raise MigrationError("unsupported_platform", sys.platform)
    root = physical_home / relative
    if root.exists() and root.resolve(strict=True) != root:
        raise MigrationError("state_root", "R8 state root contains a symlink")
    current = physical_home
    for part in relative.parts:
        current = current / part
        if not current.exists():
            raise MigrationError("state_root", f"R8 component does not exist: {current}")
        info = current.lstat()
        if (
            not stat.S_ISDIR(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o700
        ):
            raise MigrationError("state_root", f"unsafe R8 component: {current}")
    return root


def _os_machine_identity() -> str:
    if sys.platform.startswith("linux"):
        for path in (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")):
            try:
                value = path.read_text(encoding="ascii").strip().lower()
            except OSError:
                continue
            if re.fullmatch(r"[0-9a-f]{32}", value):
                return "linux-machine-id:" + value
        raise MigrationError("owner_identity", "cannot obtain canonical OS machine identity")
    if sys.platform == "darwin":
        completed = subprocess.run(
            ["/usr/sbin/ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={"PATH": "/usr/bin:/bin:/usr/sbin", "LC_ALL": "C", "LANG": "C"},
        )
        value = completed.stdout.decode("ascii", "strict")
        match = re.search(
            r'"IOPlatformUUID"\s*=\s*"([0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12})"',
            value,
        )
        if completed.returncode or match is None:
            raise MigrationError("owner_identity", "cannot obtain canonical OS machine identity")
        return "darwin-ioplatformuuid:" + match.group(1).lower()
    raise MigrationError("unsupported_platform", sys.platform)


def _migration_host_identity(state_root: Path) -> str:
    root = _absolute_state_path(state_root, "owner_identity")
    descriptor = _open_state_directory(
        root,
        create=False,
        validate_from=root,
        code="owner_identity",
    )
    try:
        info = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    return digest(
        {
            "machine_identity": _os_machine_identity(),
            "effective_uid": os.geteuid(),
            "state_root": {
                "path": os.fspath(root),
                "device": info.st_dev,
                "inode": info.st_ino,
            },
        }
    )


def run_live(
    manifest_path: Path,
    authority_path: Path,
    reviewed_commit: str,
    review_artifact_path: Path,
    bootstrap_receipt_path: Path,
    *,
    confirmed: bool,
) -> dict[str, Any]:
    if not confirmed:
        raise MigrationError("confirmation_required", "live migration requires --confirmed")
    manifest = validate_manifest(manifest_path, require_attestation=True)
    review_artifact = validate_review_artifact(
        review_artifact_path, manifest, reviewed_commit
    )
    bootstrap_receipt, bootstrap_receipt_sha256 = load_bootstrap_receipt(
        bootstrap_receipt_path, manifest, reviewed_commit
    )
    authority = SubprocessAuthority(authority_path)
    identity = _identity(authority)
    receipt_provider = bootstrap_receipt["provider"]
    if (
        Path(receipt_provider["path"]) != authority_path
        or receipt_provider["sha256"] != authority.executable_sha256
        or any(
            receipt_provider["full_profile_identity"][key] != identity[key]
            for key in (
                "backend_mode",
                "database_identity",
                "project_identity",
                "repository_identity",
                "core_schema_fingerprint",
                "full_schema_fingerprint",
            )
        )
    ):
        raise MigrationError(
            "bootstrap_receipt",
            "receipt provider identity differs from executable/no-migrate identity",
        )
    identity_document = {key: identity[key] for key in sorted(identity) if key != "state_root"}
    identity_hash = digest(identity_document)
    state_root = Path(identity["state_root"])
    lock_path = (
        state_root
        / "locks"
        / identity_hash
        / "registration-migration.mardi-gras-agentic-integration-v1.lock"
    )
    evidence_path = (
        state_root
        / "migrations"
        / identity_hash
        / "mardi-gras-agentic-integration-v1"
    )
    owner_context = {
        "machine_host_identity": _migration_host_identity(state_root),
        "reviewed_commit": reviewed_commit,
        "authority_binary_sha256": authority.executable_sha256,
        "identity_document_sha256": identity_hash,
        "lock_path_sha256": hashlib.sha256(os.fsencode(lock_path)).hexdigest(),
    }
    with MigrationLock(lock_path, secure_root=state_root):
        with EvidenceLedger(
            evidence_path, owner_context, secure_root=state_root
        ) as ledger:
            return Reconciler(manifest, authority, ledger, GitSourceGate()).run(
                reviewed_commit,
                review_artifact,
                bootstrap_receipt,
                bootstrap_receipt_sha256,
            )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate authored manifest and graph")
    validate.add_argument("--manifest", type=Path, required=True)
    run = sub.add_parser("run", help="execute reviewed migration through Task-00D authority")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--authority", type=Path, required=True)
    run.add_argument("--reviewed-commit", required=True)
    run.add_argument("--review-artifact", type=Path, required=True)
    run.add_argument("--bootstrap-receipt", type=Path, required=True)
    run.add_argument("--confirmed", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            validated = validate_manifest(args.manifest)
            output = {
                "schema": SCHEMA,
                "status": "valid",
                "attested": bool(validated.data["attestation"]),
                "replacement_count": len(validated.replacement_paths),
                "historical_count": len(validated.data["historical"]),
            }
        else:
            output = run_live(
                args.manifest,
                args.authority,
                args.reviewed_commit,
                args.review_artifact,
                args.bootstrap_receipt,
                confirmed=args.confirmed,
            )
    except MigrationError as exc:
        print(canonical_bytes({"error": exc.code, "detail": exc.detail}).decode(), file=sys.stderr)
        return 2
    print(canonical_bytes(output).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
