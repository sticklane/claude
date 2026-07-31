#!/usr/bin/env python3
"""Crash-recoverable controller for the source-attested Mardi Gras bootstrap.

The controller is deliberately outside Beads because it creates the first
bootstrap Bead.  It has one narrow lifecycle: create and run 00A, publish its
reviewed commit, install the authority core, atomically finalize 00A, then run
and close 00B--00D with the progressively stronger provider.  Every external
effect is bracketed by an owner-bound prepared/committed evidence pair.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import platform
import pwd
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, NoReturn


SCRIPT_PATH = Path(__file__).resolve()
SPEC_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[2]
CONFIG_PATH = SPEC_DIR / "bootstrap-registration-v1.json"
SPEC_PATH = "specs/mardi-gras-agentic-integration/SPEC.md"
WORKFLOW_PATH = (
    "specs/mardi-gras-agentic-integration/bootstrap-00a-workflow.md"
)
CONFIG_SCHEMA = "agentic.registration-bootstrap/v1"
RESULT_SCHEMA = "agentic.registration-bootstrap-control-result/v1"
ATTESTATION_SCHEMA = "agentic.registration-bootstrap-attestation/v1"
EVENT_SCHEMA = "agentic.registration-bootstrap-event/v1"
HEAD_SCHEMA = "agentic.registration-bootstrap-head/v1"
WORKER_RESULT_SCHEMA = "agentic.registration-bootstrap-worker-result/v1"
REVIEW_RESULT_SCHEMA = "agentic.registration-bootstrap-review-result/v1"
DEFINITION_SCHEMA_VERSION = 1
EXTERNAL_REF_PREFIX = "spec-task:"
CONTAINER_ID = "agentic-j01"
PINNED_BEADS_COMMIT = "8e4e59d39f3459a43cf21a3236a13eca4dd874f7"

TASKS = (
    (
        "00A",
        "specs/mardi-gras-agentic-integration/tasks/"
        "00-add-beads-authority-core.md",
        (),
        None,
        "post_core",
    ),
    (
        "00B",
        "specs/mardi-gras-agentic-integration/tasks/"
        "00-add-beads-conditional-authority.md",
        (
            "spec-task:specs/mardi-gras-agentic-integration/tasks/"
            "00-add-beads-authority-core.md",
        ),
        "spec-task:specs/mardi-gras-agentic-integration/tasks/"
        "00-add-beads-conditional-authority.md",
        "initial",
    ),
    (
        "00C",
        "specs/mardi-gras-agentic-integration/tasks/"
        "00-add-beads-supersession-authority.md",
        (
            "spec-task:specs/mardi-gras-agentic-integration/tasks/"
            "00-add-beads-conditional-authority.md",
        ),
        "spec-task:specs/mardi-gras-agentic-integration/tasks/"
        "00-add-beads-supersession-authority.md",
        "initial",
    ),
    (
        "00D",
        "specs/mardi-gras-agentic-integration/tasks/"
        "00-install-beads-authorizer-bootstrap.md",
        (
            "spec-task:specs/mardi-gras-agentic-integration/tasks/"
            "00-add-beads-supersession-authority.md",
        ),
        "spec-task:specs/mardi-gras-agentic-integration/tasks/"
        "00-install-beads-authorizer-bootstrap.md",
        "initial",
    ),
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ISSUE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*-[0-9a-f]{12}$")
_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_SECTION_TEMPLATE = r"^## {name}\s*$\n(?P<body>.*?)(?=^##\s|\Z)"
_GIT40 = re.compile(r"^[0-9a-f]{40}$")
_SECURE_STATE_ROOTS: set[Path] = set()
_EMPTY_ATTESTATION = {
    "schema_version": ATTESTATION_SCHEMA,
    "source_commit": "",
    "source_date_utc": "",
    "source_config_sha256": "",
    "spec_sha256": "",
    "workflow_sha256": "",
    "controller_sha256": "",
    "task_sha256": {},
    "ready_review": {
        "reviewer": "",
        "verdict": "",
        "subject_sha256": "",
        "evidence_sha256": "",
    },
}
_PROVIDER_DECLARATION = {
    "beads_commit": PINNED_BEADS_COMMIT,
    "control_plane": "crash-recoverable-attended",
    "live_mutation": True,
    "request_schemas": {
        "bootstrap_finalize": "agentic.bd-bootstrap-finalize/v1",
        "guarded_create": "agentic.bd-guarded-create/v1",
        "conditional_transaction": "agentic.bd-authority-transaction/v1",
    },
    "response_schemas": {
        "identity": "agentic.bd-authority-identity-result/v1",
        "install": "agentic.bd-authority-install-result/v1",
        "bootstrap_finalize": "agentic.bd-bootstrap-finalize-result/v1",
        "guarded_create": "agentic.bd-guarded-create-result/v1",
        "conditional_transaction": "agentic.bd-authority-transaction-result/v1",
    },
    "runtime_argv": {
        "claude": ["--print"],
        "codex": ["exec"],
    },
}


class BootstrapControlError(Exception):
    """A typed fail-closed validation or authority error."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        exit_code: int = 2,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.exit_code = exit_code


def _fail(
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    exit_code: int = 2,
) -> NoReturn:
    raise BootstrapControlError(
        code,
        message,
        details=details,
        exit_code=exit_code,
    )


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        # Match agentic.register.definition_hash exactly.
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(
                "duplicate_json_key",
                f"duplicate JSON key {key!r}",
            )
        result[key] = value
    return result


def _exact_keys(
    value: Any,
    expected: set[str],
    where: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("invalid_schema", f"{where} must be an object")
    actual = set(value)
    if actual != expected:
        _fail(
            "invalid_schema",
            f"{where} has unknown or missing keys",
            details={
                "where": where,
                "missing": sorted(expected - actual),
                "unknown": sorted(actual - expected),
            },
        )
    return value


def _regular_contained_file(
    raw_path: str | os.PathLike[str],
    *,
    exact_path: Path | None = None,
) -> tuple[Path, bytes]:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        _fail(
            "missing_file",
            f"required file is unavailable: {candidate}",
            details={"error": str(exc)},
        )

    try:
        relative = resolved.relative_to(REPO_ROOT)
    except ValueError:
        _fail(
            "path_escape",
            f"path is outside the canonical repository: {resolved}",
        )

    if exact_path is not None and resolved != exact_path.resolve(strict=True):
        _fail(
            "unexpected_path",
            f"path does not identify the attested file: {resolved}",
            details={"expected": str(exact_path.resolve(strict=True))},
        )

    cursor = REPO_ROOT
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            _fail(
                "symlink_rejected",
                f"attested path contains a symlink: {cursor}",
            )

    try:
        mode = resolved.stat().st_mode
    except OSError as exc:
        _fail(
            "unreadable_file",
            f"cannot stat required file: {resolved}",
            details={"error": str(exc)},
        )
    if not stat.S_ISREG(mode):
        _fail("not_regular_file", f"required path is not a file: {resolved}")

    try:
        return resolved, resolved.read_bytes()
    except OSError as exc:
        _fail(
            "unreadable_file",
            f"cannot read required file: {resolved}",
            details={"error": str(exc)},
        )


def _load_closed_json(path: str | os.PathLike[str]) -> tuple[dict[str, Any], bytes]:
    _, raw = _regular_contained_file(path, exact_path=CONFIG_PATH)
    if raw.startswith(b"\xef\xbb\xbf"):
        _fail("invalid_json_encoding", "configuration must not contain a BOM")
    if b"\r" in raw:
        _fail("invalid_json_encoding", "configuration must use LF line endings")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        _fail(
            "invalid_json_encoding",
            "configuration is not valid UTF-8",
            details={"error": str(exc)},
        )
    try:
        value = json.loads(text, object_pairs_hook=_object_pairs)
    except json.JSONDecodeError as exc:
        _fail(
            "invalid_json",
            "configuration is not valid JSON",
            details={"error": str(exc)},
        )
    if not isinstance(value, dict):
        _fail("invalid_schema", "configuration root must be an object")
    return value, raw


def _one_header(text: str, name: str) -> str:
    pattern = re.compile(
        rf"^{re.escape(name)}:\s*(.*?)\s*$",
        re.MULTILINE,
    )
    values = [match.group(1).strip() for match in pattern.finditer(text)]
    if len(values) != 1 or not values[0]:
        _fail(
            "invalid_task_definition",
            f"task must contain exactly one nonempty {name}: header",
        )
    return values[0]


def _one_section(text: str, name: str) -> str:
    pattern = re.compile(
        _SECTION_TEMPLATE.format(name=re.escape(name)),
        re.MULTILINE | re.DOTALL,
    )
    bodies = [match.group("body").strip() for match in pattern.finditer(text)]
    if len(bodies) != 1 or not bodies[0]:
        _fail(
            "invalid_task_definition",
            f"task must contain exactly one nonempty ## {name} section",
        )
    return bodies[0]


def _parse_task(
    bootstrap_id: str,
    source: str,
    prerequisite_refs: tuple[str, ...],
) -> tuple[dict[str, Any], dict[str, Any], str]:
    task_path, raw = _regular_contained_file(REPO_ROOT / source)
    if task_path.relative_to(REPO_ROOT).as_posix() != source:
        _fail(
            "task_path_mismatch",
            f"{bootstrap_id} source does not resolve to its exact repository path",
        )
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        _fail(
            "invalid_task_encoding",
            f"{source} must be BOM-free UTF-8 with LF endings and a final LF",
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        _fail(
            "invalid_task_encoding",
            f"{source} is not valid UTF-8",
            details={"error": str(exc)},
        )

    titles = [match.group(1).strip() for match in _TITLE_RE.finditer(text)]
    if len(titles) != 1 or not titles[0]:
        _fail(
            "invalid_task_definition",
            f"{source} must contain exactly one level-one title",
        )
    title = titles[0]
    if _one_header(text, "Status") != "pending":
        _fail("invalid_task_definition", f"{source} must have Status: pending")
    if _one_header(text, "Priority") != "P0":
        _fail("invalid_task_definition", f"{source} must have Priority: P0")

    raw_depends = _one_header(text, "Depends on")
    if prerequisite_refs:
        expected_source = prerequisite_refs[0][len(EXTERNAL_REF_PREFIX) :]
        expected_depends = Path(expected_source).name
    else:
        expected_depends = "none"
    if raw_depends != expected_depends:
        _fail(
            "dependency_mismatch",
            f"{source} has a noncanonical Depends on header",
            details={"actual": raw_depends, "expected": expected_depends},
        )

    touch = sorted(
        part.strip()
        for part in _one_header(text, "Touch").split(",")
        if part.strip()
    )
    if not touch:
        _fail("invalid_task_definition", f"{source} has an empty Touch set")
    budget = _one_header(text, "Budget")
    if re.fullmatch(r"[1-9][0-9]* turns", budget) is None:
        _fail(
            "invalid_task_definition",
            f"{source} has a noncanonical Budget header",
        )
    rigor_headers = re.findall(r"^Rigor:\s*(.*?)\s*$", text, re.MULTILINE)
    if len(rigor_headers) > 1:
        _fail(
            "invalid_task_definition",
            f"{source} has duplicate Rigor headers",
        )
    rigor = rigor_headers[0].strip() if rigor_headers else "production"
    if not rigor:
        _fail("invalid_task_definition", f"{source} has an empty Rigor header")

    definition = {
        "schema_version": DEFINITION_SCHEMA_VERSION,
        "path": source,
        "title": title,
        "goal": _one_section(text, "Goal"),
        "touch": touch,
        "budget": budget,
        "rigor": rigor,
        "prerequisites": list(prerequisite_refs),
    }
    parsed = {
        "title": title,
        "description": definition["goal"],
        "acceptance": _one_section(text, "Acceptance"),
        "definition": definition,
        "definition_hash": _sha256(_canonical_json(definition)),
        "task_sha256": _sha256(raw),
    }
    return parsed, definition, _sha256(raw)


def _expected_task_record(
    bootstrap_id: str,
    source: str,
    prerequisite_refs: tuple[str, ...],
    initial_external_ref: str | None,
    container_phase: str,
) -> dict[str, Any]:
    parsed, definition, task_sha256 = _parse_task(
        bootstrap_id,
        source,
        prerequisite_refs,
    )
    definition_hash = parsed["definition_hash"]
    canonical_ref = EXTERNAL_REF_PREFIX + source
    metadata = {
        "budget": definition["budget"],
        "definition_hash": definition_hash,
        "registration_state": "pending",
        "rigor": definition["rigor"],
        "source": source,
        "touch": definition["touch"],
    }
    return {
        "bootstrap_id": bootstrap_id,
        "source": source,
        "task_sha256": task_sha256,
        "definition": definition,
        "definition_hash": definition_hash,
        "envelope": {
            "title": parsed["title"],
            "description": parsed["description"],
            "acceptance": parsed["acceptance"],
            "issue_type": "task",
            "priority": 0,
            "external_ref": initial_external_ref,
            "canonical_external_ref": canonical_ref,
            "metadata": metadata,
            "container": {
                "issue_id": CONTAINER_ID,
                "relation": "related",
                "phase": container_phase,
            },
            "dependency_refs": list(prerequisite_refs),
        },
    }


def _validate_attestation(value: Any) -> dict[str, Any]:
    attestation = _exact_keys(value, set(_EMPTY_ATTESTATION), "attestation")
    review = _exact_keys(
        attestation["ready_review"],
        set(_EMPTY_ATTESTATION["ready_review"]),
        "attestation.ready_review",
    )
    if attestation == _EMPTY_ATTESTATION:
        return {"state": "empty"}
    if attestation["schema_version"] != ATTESTATION_SCHEMA:
        _fail("invalid_attestation", "unsupported bootstrap attestation schema")
    if _GIT40.fullmatch(attestation["source_commit"]) is None:
        _fail("invalid_attestation", "source_commit must be lowercase Git SHA-1")
    if re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
        attestation["source_date_utc"],
    ) is None:
        _fail("invalid_attestation", "source_date_utc is not canonical UTC")
    for name in (
        "source_config_sha256",
        "spec_sha256",
        "workflow_sha256",
        "controller_sha256",
    ):
        if _HEX64.fullmatch(attestation[name]) is None:
            _fail("invalid_attestation", f"{name} must be lowercase SHA-256")
    task_hashes = _exact_keys(
        attestation["task_sha256"],
        {source for _, source, *_ in TASKS},
        "attestation.task_sha256",
    )
    if any(_HEX64.fullmatch(value) is None for value in task_hashes.values()):
        _fail("invalid_attestation", "task attestation hashes must be SHA-256")
    if (
        not isinstance(review["reviewer"], str)
        or not review["reviewer"].strip()
        or review["verdict"] != "READY"
        or _HEX64.fullmatch(review["subject_sha256"]) is None
        or _HEX64.fullmatch(review["evidence_sha256"]) is None
    ):
        _fail(
            "invalid_attestation",
            "bootstrap attestation requires one independent READY review",
        )
    subject = {
        key: item
        for key, item in attestation.items()
        if key != "ready_review"
    }
    if _sha256(_canonical_json(subject)) != review["subject_sha256"]:
        _fail(
            "invalid_attestation",
            "READY review does not bind the attestation subject",
        )
    return {"state": "attested", "subject_sha256": review["subject_sha256"]}


def validate_config(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Return a bounded validation receipt or fail without reading Beads."""
    config, raw = _load_closed_json(path)
    _exact_keys(
        config,
        {
            "schema_version",
            "spec_path",
            "workflow_path",
            "provider",
            "attestation",
            "tasks",
        },
        "configuration",
    )
    if config["schema_version"] != CONFIG_SCHEMA:
        _fail(
            "invalid_schema",
            "configuration schema_version is not supported",
        )
    if config["spec_path"] != SPEC_PATH:
        _fail("invalid_schema", "configuration spec_path is not canonical")
    if config["workflow_path"] != WORKFLOW_PATH:
        _fail("invalid_schema", "configuration workflow_path is not canonical")
    _regular_contained_file(REPO_ROOT / SPEC_PATH)
    _regular_contained_file(REPO_ROOT / WORKFLOW_PATH)

    provider = _exact_keys(
        config["provider"],
        set(_PROVIDER_DECLARATION),
        "provider",
    )
    if provider != _PROVIDER_DECLARATION:
        _fail(
            "invalid_schema",
            "provider declaration is not the executable bootstrap profile",
        )
    attestation = _validate_attestation(config["attestation"])

    tasks = config["tasks"]
    if not isinstance(tasks, list) or len(tasks) != len(TASKS):
        _fail(
            "invalid_schema",
            "configuration must contain exactly four bootstrap tasks",
        )

    validated = []
    for index, expected_parts in enumerate(TASKS):
        actual = tasks[index]
        expected = _expected_task_record(*expected_parts)
        if actual != expected:
            bootstrap_id = expected_parts[0]
            _fail(
                "task_envelope_mismatch",
                f"{bootstrap_id} does not match its checked-in task definition",
                details={
                    "bootstrap_id": bootstrap_id,
                    "expected_task_sha256": expected["task_sha256"],
                    "expected_definition_hash": expected["definition_hash"],
                },
            )
        validated.append(
            {
                "bootstrap_id": expected["bootstrap_id"],
                "source": expected["source"],
                "task_sha256": expected["task_sha256"],
                "definition_hash": expected["definition_hash"],
                "dependency_refs": expected["envelope"]["dependency_refs"],
            }
        )

    return {
        "schema_version": RESULT_SCHEMA,
        "ok": True,
        "operation": "validate",
        "config_sha256": _sha256(raw),
        "provider_beads_commit": PINNED_BEADS_COMMIT,
        "live_mutation_enabled": True,
        "attestation_state": attestation["state"],
        "tasks": validated,
    }


def _uuid7(value: str) -> str:
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        _fail(
            "invalid_intent",
            "intent must be a canonical UUIDv7",
            details={"error": str(exc)},
        )
    if parsed.version != 7 or str(parsed) != value:
        _fail("invalid_intent", "intent must be a canonical UUIDv7")
    return value


def _json_result(raw: str, operation: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        _fail(
            "invalid_command_result",
            f"{operation} returned non-JSON output",
            details={"error": str(exc)},
        )
    if isinstance(value, list):
        if len(value) != 1 or not isinstance(value[0], dict):
            _fail(
                "invalid_command_result",
                f"{operation} returned an ambiguous result",
            )
        value = value[0]
    if not isinstance(value, dict):
        _fail("invalid_command_result", f"{operation} did not return an object")
    return value


def _lexical_absolute(path: Path) -> Path:
    value = Path(os.path.abspath(os.fspath(path)))
    if ".." in value.parts:
        _fail("unsafe_state_path", f"state path contains traversal: {path}")
    return value


def _open_absolute_dir_nofollow(path: Path, *, create: bool = False) -> int:
    """Open an absolute directory by descriptor-relative, no-follow traversal."""
    absolute = _lexical_absolute(path)
    descriptor = os.open(
        os.path.sep,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
    )
    try:
        for component in absolute.parts[1:]:
            try:
                child = os.open(
                    component,
                    os.O_RDONLY
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=descriptor,
                )
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(component, 0o700, dir_fd=descriptor)
                child = os.open(
                    component,
                    os.O_RDONLY
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=descriptor,
                )
            except OSError as exc:
                _fail(
                    "unsafe_state_path",
                    f"state directory has a symlinked or unsafe ancestor: {path}",
                    details={"error": str(exc)},
                )
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _register_secure_root(path: Path, *, create: bool = False) -> Path:
    root = _lexical_absolute(path)
    try:
        descriptor = _open_absolute_dir_nofollow(root, create=create)
    except OSError as exc:
        _fail(
            "unsafe_state_path",
            f"cannot open secure state root: {root}",
            details={"error": str(exc)},
        )
    try:
        os.fchmod(descriptor, 0o700)
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) != 0o700
        ):
            _fail(
                "unsafe_state_path",
                f"secure state root is not owned mode-0700: {root}",
            )
    finally:
        os.close(descriptor)
    _SECURE_STATE_ROOTS.add(root)
    return root


def _secure_root_for(path: Path) -> Path:
    absolute = _lexical_absolute(path)
    candidates = []
    for root in _SECURE_STATE_ROOTS:
        try:
            absolute.relative_to(root)
        except ValueError:
            continue
        candidates.append(root)
    if not candidates:
        _fail("unsafe_state_path", f"state path is outside a secure root: {path}")
    return max(candidates, key=lambda item: len(item.parts))


def _open_secure_dir(path: Path, *, create: bool = False) -> int:
    absolute = _lexical_absolute(path)
    root = _secure_root_for(absolute)
    try:
        descriptor = _open_absolute_dir_nofollow(root)
    except OSError as exc:
        _fail(
            "unsafe_state_path",
            f"cannot open secure root for {path}",
            details={"error": str(exc)},
        )
    try:
        root_metadata = os.fstat(descriptor)
        if (
            root_metadata.st_uid != os.geteuid()
            or stat.S_IMODE(root_metadata.st_mode) != 0o700
        ):
            _fail("unsafe_state_path", f"unsafe secure root for {path}")
        relative = absolute.relative_to(root)
        for component in relative.parts:
            try:
                child = os.open(
                    component,
                    os.O_RDONLY
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=descriptor,
                )
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(component, 0o700, dir_fd=descriptor)
                child = os.open(
                    component,
                    os.O_RDONLY
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=descriptor,
                )
            except OSError as exc:
                _fail(
                    "unsafe_state_path",
                    f"state path has a symlinked or unsafe ancestor: {path}",
                    details={"error": str(exc)},
                )
            metadata = os.fstat(child)
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid != os.geteuid()
                or stat.S_IMODE(metadata.st_mode) != 0o700
            ):
                os.close(child)
                _fail("unsafe_state_path", f"unsafe state directory: {path}")
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _open_secure_parent(path: Path, *, create: bool = False) -> tuple[int, str]:
    absolute = _lexical_absolute(path)
    if absolute.name in {"", ".", ".."}:
        _fail("unsafe_state_path", f"invalid state file name: {path}")
    return _open_secure_dir(absolute.parent, create=create), absolute.name


def _secure_exists(path: Path) -> bool:
    try:
        parent, name = _open_secure_parent(path)
    except FileNotFoundError:
        return False
    try:
        try:
            os.stat(name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return False
        return True
    finally:
        os.close(parent)


def _secure_mkdir(path: Path) -> None:
    descriptor = _open_secure_dir(path, create=True)
    os.close(descriptor)


def _secure_listdir(path: Path) -> list[str]:
    descriptor = _open_secure_dir(path)
    try:
        return sorted(os.listdir(descriptor))
    finally:
        os.close(descriptor)


def _read_secure_bytes(
    path: Path,
    where: str,
    *,
    expected_mode: int | None = None,
) -> bytes:
    parent, name = _open_secure_parent(path)
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent,
        )
        try:
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.geteuid()
                or (
                    expected_mode is not None
                    and stat.S_IMODE(metadata.st_mode) != expected_mode
                )
            ):
                _fail("unsafe_state_path", f"unsafe {where} file")
            chunks = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)
        finally:
            os.close(descriptor)
    finally:
        os.close(parent)


def _fsync_dir(path: Path) -> None:
    descriptor = _open_secure_dir(path)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_atomic(
    path: Path,
    value: Any,
    mode: int = 0o600,
    *,
    immutable: bool = False,
    temp_owner: str | None = None,
) -> None:
    parent, name = _open_secure_parent(path, create=True)
    raw = _canonical_json(value)
    owner_component = f".{temp_owner}" if temp_owner else ""
    temporary = (
        f".{name}{owner_component}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    )
    try:
        try:
            existing = os.stat(name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None and not stat.S_ISREG(existing.st_mode):
            _fail("unsafe_state_path", f"unsafe evidence target: {path}")
        descriptor = os.open(
            temporary,
            os.O_CREAT
            | os.O_EXCL
            | os.O_WRONLY
            | getattr(os, "O_NOFOLLOW", 0),
            mode,
            dir_fd=parent,
        )
        try:
            with os.fdopen(descriptor, "wb", closefd=False) as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.fchmod(descriptor, mode)
        finally:
            os.close(descriptor)
        if immutable:
            try:
                os.link(
                    temporary,
                    name,
                    src_dir_fd=parent,
                    dst_dir_fd=parent,
                    follow_symlinks=False,
                )
            except FileExistsError:
                os.unlink(temporary, dir_fd=parent)
                _fail(
                    "immutable_evidence_exists",
                    f"immutable evidence exists: {path}",
                )
            os.unlink(temporary, dir_fd=parent)
        else:
            os.replace(
                temporary,
                name,
                src_dir_fd=parent,
                dst_dir_fd=parent,
            )
        os.fsync(parent)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary, dir_fd=parent)
        os.close(parent)


def _read_json_file(path: Path, where: str) -> dict[str, Any]:
    parent: int | None = None
    try:
        parent, name = _open_secure_parent(path)
        metadata = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            _fail("unsafe_state_path", f"unsafe {where} file")
        descriptor = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent,
        )
        try:
            opened = os.fstat(descriptor)
            if (
                opened.st_dev != metadata.st_dev
                or opened.st_ino != metadata.st_ino
            ):
                _fail("unsafe_state_path", f"{where} changed during open")
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                raw = handle.read()
        finally:
            os.close(descriptor)
    except OSError as exc:
        _fail("missing_evidence", f"cannot read {where}", details={"error": str(exc)})
    finally:
        if parent is not None:
            os.close(parent)
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("invalid_evidence", f"{where} is not canonical JSON", details={"error": str(exc)})
    if not isinstance(value, dict) or raw != _canonical_json(value):
        _fail("invalid_evidence", f"{where} is not canonical JSON")
    return value


def _write_immutable_direct(path: Path, value: Any) -> None:
    parent, name = _open_secure_parent(path, create=True)
    raw = _canonical_json(value)
    try:
        descriptor = os.open(
            name,
            os.O_CREAT
            | os.O_EXCL
            | os.O_WRONLY
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=parent,
        )
    except FileExistsError:
        os.close(parent)
        _fail("immutable_evidence_exists", f"immutable evidence exists: {path}")
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)
    os.fsync(parent)
    os.close(parent)


def _process_start_identity(pid: int | None = None) -> str:
    process_id = pid or os.getpid()
    if platform.system() == "Linux":
        try:
            fields = Path(f"/proc/{process_id}/stat").read_text().split()
            return f"linux-procfs:{int(fields[21])}"
        except (OSError, ValueError, IndexError):
            return "unavailable"
    if platform.system() == "Darwin":
        result = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(process_id)],
            text=True,
            capture_output=True,
            check=False,
        )
        return "darwin-ps:" + result.stdout.strip()
    return "unavailable"


def _boot_identity() -> str:
    if platform.system() == "Linux":
        try:
            value = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
            return f"linux-boot-id:{value}"
        except OSError:
            return "unavailable"
    if platform.system() == "Darwin":
        result = subprocess.run(
            ["sysctl", "-n", "kern.boottime"],
            text=True,
            capture_output=True,
            check=False,
        )
        return "darwin-kern-boottime:" + result.stdout.strip()
    return "unavailable"


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _secure_tree_files(root: Path) -> list[Path]:
    """Return regular files while rejecting every non-directory tree entry."""
    root = _lexical_absolute(root)
    root_descriptor = _open_secure_dir(root)
    found: list[Path] = []

    def visit(descriptor: int, relative: Path) -> None:
        for name in sorted(os.listdir(descriptor)):
            metadata = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            child_relative = relative / name
            if stat.S_ISLNK(metadata.st_mode):
                _fail(
                    "unsafe_state_path",
                    f"symlink inside secure state tree: {root / child_relative}",
                )
            if stat.S_ISDIR(metadata.st_mode):
                if not relative.parts and name in {"outputs", "worktrees"}:
                    # Runtime-owned payload trees are validated at their exact
                    # consumption points; they are not evidence-temp trees.
                    continue
                if (
                    metadata.st_uid != os.geteuid()
                    or stat.S_IMODE(metadata.st_mode) != 0o700
                ):
                    _fail(
                        "unsafe_state_path",
                        f"unsafe directory inside state tree: {root / child_relative}",
                    )
                child = os.open(
                    name,
                    os.O_RDONLY
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=descriptor,
                )
                try:
                    visit(child, child_relative)
                finally:
                    os.close(child)
                continue
            if not stat.S_ISREG(metadata.st_mode):
                _fail(
                    "unsafe_state_path",
                    f"non-regular entry inside state tree: {root / child_relative}",
                )
            found.append(root / child_relative)

    try:
        visit(root_descriptor, Path())
    finally:
        os.close(root_descriptor)
    return found


def _cleanup_exact_dead_temps(root: Path, intent: str) -> None:
    pattern = re.compile(
        r"^\..+\.([0-9a-f]{32})\.(\d+)\.[0-9a-f]{32}\.tmp$"
    )
    for path in (
        candidate
        for candidate in _secure_tree_files(root)
        if candidate.name.endswith(".tmp")
    ):
        match = pattern.fullmatch(path.name)
        if match is None:
            _fail("invalid_evidence", f"unknown bootstrap temporary: {path.name}")
        process_owner = match.group(1)
        pid = int(match.group(2))
        owner_path = root / "owners" / f"process-{process_owner}.json"
        owner = _read_json_file(owner_path, "temporary process owner")
        _exact_keys(
            owner,
            {
                "schema_version",
                "process_owner",
                "intent",
                "pid",
                "process_start",
                "boot",
            },
            "temporary process owner",
        )
        if (
            owner.get("schema_version")
            != "agentic.registration-bootstrap-process-owner/v1"
            or owner.get("process_owner") != process_owner
            or owner.get("pid") != pid
            or owner.get("intent") != intent
            or not isinstance(owner.get("process_start"), str)
            or not owner["process_start"]
            or owner["process_start"] == "unavailable"
            or not isinstance(owner.get("boot"), str)
            or not owner["boot"]
            or owner["boot"] == "unavailable"
        ):
            _fail("invalid_evidence", "temporary owner binding is malformed")
        current_boot = _boot_identity()
        if current_boot == "unavailable" or owner["boot"] == "unavailable":
            _fail("unknown_temporary_owner", "temporary boot identity is unknown")
        if owner["boot"] == current_boot and _pid_exists(pid):
            current_start = _process_start_identity(pid)
            if current_start == "unavailable":
                _fail(
                    "unknown_temporary_owner",
                    "temporary process identity is unknown",
                )
            if current_start == owner["process_start"]:
                _fail(
                    "live_temporary_owner",
                    f"live process still owns temporary {path.name}",
                )
        parent, name = _open_secure_parent(path)
        try:
            metadata = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.geteuid()
            ):
                _fail("unsafe_state_path", f"unsafe dead temporary: {path}")
            os.unlink(name, dir_fd=parent)
            os.fsync(parent)
        finally:
            os.close(parent)


class _FileLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.handle: Any = None

    def __enter__(self) -> "_FileLock":
        parent, name = _open_secure_parent(self.path, create=True)
        try:
            descriptor = os.open(
                name,
                os.O_CREAT
                | os.O_RDWR
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=parent,
            )
        except OSError as exc:
            _fail(
                "unsafe_state_path",
                f"unsafe lock target: {self.path}",
                details={"error": str(exc)},
            )
        finally:
            os.close(parent)
        self.handle = os.fdopen(descriptor, "a+b")
        os.fchmod(descriptor, 0o600)
        metadata = os.fstat(self.handle.fileno())
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            self.handle.close()
            _fail("unsafe_state_path", f"unsafe lock file: {self.path}")
        fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *_: Any) -> None:
        fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        self.handle.close()


class EvidenceJournal:
    """Owner-bound, hash-chained prepared/committed evidence."""

    def __init__(self, root: Path, owner: str) -> None:
        self.root = _lexical_absolute(root)
        if not any(
            self.root == candidate or self.root.is_relative_to(candidate)
            for candidate in _SECURE_STATE_ROOTS
        ):
            _register_secure_root(self.root, create=True)
        else:
            _secure_mkdir(self.root)
        self.events = self.root / "events"
        self.owner = owner
        self.owners = self.root / "owners"
        _secure_mkdir(self.events)
        _secure_mkdir(self.owners)
        self.process_owner = uuid.uuid4().hex
        current_start = _process_start_identity()
        current_boot = _boot_identity()
        if current_start == "unavailable" or current_boot == "unavailable":
            _fail(
                "unknown_process_identity",
                "bootstrap evidence requires exact process start and boot identity",
            )
        process_record = {
            "schema_version": "agentic.registration-bootstrap-process-owner/v1",
            "process_owner": self.process_owner,
            "intent": owner,
            "pid": os.getpid(),
            "process_start": current_start,
            "boot": current_boot,
        }
        _write_immutable_direct(
            self.owners / f"process-{self.process_owner}.json",
            process_record,
        )
        owner_path = self.owners / f"{owner}.json"
        if _secure_exists(owner_path):
            owner_record = _read_json_file(owner_path, "bootstrap owner")
            _exact_keys(
                owner_record,
                {"schema_version", "owner", "run_token", "creator"},
                "bootstrap owner",
            )
            creator = _exact_keys(
                owner_record["creator"],
                {"pid", "process_start", "boot"},
                "bootstrap owner creator",
            )
            if (
                owner_record.get("schema_version")
                != "agentic.registration-bootstrap-owner/v1"
                or owner_record.get("owner") != owner
                or not isinstance(owner_record.get("run_token"), str)
                or re.fullmatch(
                    r"[0-9a-f]{32}",
                    owner_record["run_token"],
                )
                is None
                or not isinstance(creator["pid"], int)
                or creator["pid"] <= 0
                or not isinstance(creator["process_start"], str)
                or not creator["process_start"]
                or not isinstance(creator["boot"], str)
                or not creator["boot"]
            ):
                _fail("foreign_bootstrap_owner", "bootstrap evidence has another owner")
        else:
            owner_record = {
                "schema_version": "agentic.registration-bootstrap-owner/v1",
                "owner": owner,
                "run_token": uuid.uuid4().hex,
                "creator": {
                    "pid": os.getpid(),
                    "process_start": current_start,
                    "boot": current_boot,
                },
            }
            _write_immutable_direct(owner_path, owner_record)
        self.run_token = owner_record["run_token"]
        _cleanup_exact_dead_temps(self.root, owner)
        self._recover()

    def _event_files(self) -> list[tuple[int, str, Path, dict[str, Any]]]:
        found: list[tuple[int, str, Path, dict[str, Any]]] = []
        for name in _secure_listdir(self.events):
            path = self.events / name
            match = re.fullmatch(r"([0-9]{20})-([0-9a-f]{64})\.json", name)
            if match is None:
                _fail("invalid_evidence", f"unexpected event file {name}")
            event = _read_json_file(path, f"event {name}")
            if _sha256(_canonical_json(event)) != match.group(2):
                _fail("invalid_evidence", f"event digest mismatch: {name}")
            found.append((int(match.group(1)), match.group(2), path, event))
        return found

    def _validate_event(
        self,
        event: dict[str, Any],
        *,
        sequence: int,
        previous: str,
    ) -> None:
        _exact_keys(
            event,
            {
                "schema_version",
                "owner",
                "writer",
                "sequence",
                "previous",
                "kind",
                "state",
                "payload",
                "recorded_monotonic_ns",
                "recorded_wall_utc",
            },
            f"bootstrap event {sequence}",
        )
        if (
            event["schema_version"] != EVENT_SCHEMA
            or event["owner"] != self.owner
            or event["sequence"] != sequence
            or event["previous"] != previous
            or re.fullmatch(r"[a-z0-9_]+", str(event["kind"])) is None
            or event["state"] not in {"prepared", "committed"}
            or not isinstance(event["payload"], dict)
            or not isinstance(event["recorded_monotonic_ns"], int)
            or event["recorded_monotonic_ns"] < 0
            or re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z",
                str(event["recorded_wall_utc"]),
            )
            is None
            or re.fullmatch(r"[0-9a-f]{32}", str(event["writer"])) is None
        ):
            _fail("invalid_evidence", f"bootstrap event {sequence} is malformed")
        writer = _read_json_file(
            self.owners / f"process-{event['writer']}.json",
            f"event {sequence} writer",
        )
        _exact_keys(
            writer,
            {
                "schema_version",
                "process_owner",
                "intent",
                "pid",
                "process_start",
                "boot",
            },
            f"event {sequence} writer",
        )
        if (
            writer["schema_version"]
            != "agentic.registration-bootstrap-process-owner/v1"
            or writer["process_owner"] != event["writer"]
            or writer["intent"] != self.owner
            or not isinstance(writer["pid"], int)
            or writer["pid"] <= 0
            or not isinstance(writer["process_start"], str)
            or not writer["process_start"]
            or not isinstance(writer["boot"], str)
            or not writer["boot"]
        ):
            _fail("invalid_evidence", f"event {sequence} writer is malformed")

    def _head(self) -> tuple[int, str]:
        path = self.root / "head.json"
        if not _secure_exists(path):
            return 0, ""
        value = _read_json_file(path, "bootstrap head")
        _exact_keys(value, {"schema_version", "owner", "sequence", "digest"}, "head")
        if (
            value["schema_version"] != HEAD_SCHEMA
            or value["owner"] != self.owner
            or not isinstance(value["sequence"], int)
            or value["sequence"] < 0
            or (value["sequence"] and _HEX64.fullmatch(value["digest"]) is None)
            or (not value["sequence"] and value["digest"] != "")
        ):
            _fail("invalid_evidence", "bootstrap head is malformed")
        return value["sequence"], value["digest"]

    def _commit_head(self, sequence: int, digest: str) -> None:
        _write_atomic(
            self.root / "head.json",
            {
                "schema_version": HEAD_SCHEMA,
                "owner": self.owner,
                "sequence": sequence,
                "digest": digest,
            },
            temp_owner=self.process_owner,
        )

    def _recover(self) -> None:
        sequence, digest = self._head()
        files = self._event_files()
        committed = [entry for entry in files if entry[0] <= sequence]
        if len(committed) != sequence:
            _fail("invalid_evidence", "bootstrap event chain has a gap")
        previous = ""
        for expected, entry in enumerate(committed, 1):
            number, item_digest, _, event = entry
            if number != expected:
                _fail("invalid_evidence", "bootstrap event chain is forked")
            self._validate_event(
                event,
                sequence=expected,
                previous=previous,
            )
            previous = item_digest
        if previous != digest:
            _fail("invalid_evidence", "bootstrap head does not name its event")
        unreferenced = [entry for entry in files if entry[0] > sequence]
        if not unreferenced:
            return
        if len(unreferenced) != 1:
            _fail("invalid_evidence", "multiple unreferenced bootstrap events")
        number, item_digest, _, event = unreferenced[0]
        if number != sequence + 1:
            _fail("invalid_evidence", "unreferenced event is not the unique next event")
        self._validate_event(
            event,
            sequence=sequence + 1,
            previous=digest,
        )
        self._commit_head(number, item_digest)

    def records(self) -> list[dict[str, Any]]:
        sequence, _ = self._head()
        return [entry[3] for entry in self._event_files() if entry[0] <= sequence]

    def append(self, kind: str, state: str, payload: dict[str, Any]) -> dict[str, Any]:
        sequence, previous = self._head()
        event = {
            "schema_version": EVENT_SCHEMA,
            "owner": self.owner,
            "writer": self.process_owner,
            "sequence": sequence + 1,
            "previous": previous,
            "kind": kind,
            "state": state,
            "payload": payload,
            "recorded_monotonic_ns": time.monotonic_ns(),
            "recorded_wall_utc": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
        }
        raw = _canonical_json(event)
        digest = _sha256(raw)
        path = self.events / f"{sequence + 1:020d}-{digest}.json"
        _write_atomic(
            path,
            event,
            immutable=True,
            temp_owner=self.process_owner,
        )
        self._commit_head(sequence + 1, digest)
        return event

    def committed(self, kind: str) -> dict[str, Any] | None:
        matches = [
            event["payload"]
            for event in self.records()
            if event["kind"] == kind and event["state"] == "committed"
        ]
        if len(matches) > 1:
            _fail("invalid_evidence", f"duplicate committed event for {kind}")
        return matches[0] if matches else None

    def prepared(self, kind: str) -> dict[str, Any] | None:
        matches = [
            event["payload"]
            for event in self.records()
            if event["kind"] == kind and event["state"] == "prepared"
        ]
        if len(matches) > 1:
            _fail("invalid_evidence", f"duplicate prepared event for {kind}")
        return matches[0] if matches else None

    def event_record(
        self,
        kind: str,
        state: str,
    ) -> tuple[str, dict[str, Any]]:
        matches = [
            (digest, event)
            for _, digest, _, event in self._event_files()
            if event["kind"] == kind and event["state"] == state
        ]
        if len(matches) != 1:
            _fail(
                "invalid_evidence",
                f"expected one {kind}/{state} event, found {len(matches)}",
            )
        return matches[0]


@dataclass
class ControllerDependencies:
    state_root: Path
    bd: Path
    runtime: Path
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run
    crash: Callable[[str], None] = lambda _point: None


def _default_state_root() -> Path:
    account_home = Path(pwd.getpwuid(os.geteuid()).pw_dir).resolve(strict=True)
    system = platform.system()
    if system == "Darwin":
        root = account_home / "Library" / "Application Support" / "agentic"
    elif system == "Linux":
        root = account_home / ".local" / "state" / "agentic"
    else:
        _fail("unsupported_platform", f"unsupported bootstrap platform: {system}")
    return root


def _default_dependencies(runtime: str) -> ControllerDependencies:
    bd = shutil.which("bd")
    runtime_path = shutil.which(runtime)
    if bd is None:
        _fail("missing_bd", "bd is not installed on PATH")
    if runtime_path is None:
        _fail("missing_runtime", f"{runtime} is not installed on PATH")
    return ControllerDependencies(
        state_root=_default_state_root(),
        bd=Path(bd).resolve(strict=True),
        runtime=Path(runtime_path).resolve(strict=True),
    )


def _ensure_secure_state_root(path: Path) -> None:
    _register_secure_root(path, create=True)


class BootstrapController:
    def __init__(
        self,
        args: argparse.Namespace,
        dependencies: ControllerDependencies,
    ) -> None:
        self.args = args
        self.deps = dependencies
        self.provider: Path | None = None
        self.intent = _uuid7(args.intent)
        self.actor = f"agentic:registration-bootstrap:{self.intent}"
        self.config, self.config_raw = _load_closed_json(args.config)
        self.validation = validate_config(args.config)
        self.attestation = self.config["attestation"]
        if self.validation["attestation_state"] != "attested":
            _fail(
                "bootstrap_not_attested",
                "run-00a requires the reviewed attestation child",
            )
        self.launch_commit = self._verify_attestation()
        self.context = self._bd_json(["context", "--json"], "bd context")
        self.repository_identity = self._repository_identity(self.context)
        self._verify_context_repository()
        identity_digest = _sha256(
            _canonical_json(
                {
                    "repository_identity": self.repository_identity,
                    "source_commit": self.attestation["source_commit"],
                    "source_config_sha256": self.attestation[
                        "source_config_sha256"
                    ],
                    "definition_hash": self.config["tasks"][0][
                        "definition_hash"
                    ],
                }
            )
        )
        prefix = self._issue_prefix(self.context)
        self.expected_issue = f"{prefix}-{identity_digest[:12]}"
        if args.issue != self.expected_issue:
            _fail(
                "non_deterministic_issue_id",
                "operator issue does not equal the attested deterministic ID",
                details={"expected": self.expected_issue, "actual": args.issue},
            )
        root = (
            dependencies.state_root
            / "bootstraps"
            / _sha256(_canonical_json(self.repository_identity))
            / "mardi-gras-agentic-integration-v1"
        )
        _secure_mkdir(root)
        self.root = root
        self.journal = EvidenceJournal(root, self.intent)
        self.worker_token = self.journal.run_token
        self.issue_ids: dict[str, str] = {"00A": self.expected_issue}
        self.current_head = self._git(["rev-parse", "HEAD"]).strip()
        self._verify_resume_head()

    def _verify_resume_head(self) -> None:
        records = self.journal.records()
        committed = [
            event
            for event in records
            if event["state"] == "committed" and event["kind"].endswith("_publish")
        ]
        prepared = [
            event
            for event in records
            if event["state"] == "prepared"
            and event["kind"].endswith("_publish")
            and not any(
                later["kind"] == event["kind"] and later["state"] == "committed"
                for later in records
            )
        ]
        allowed = {self.launch_commit}
        if committed:
            allowed = {committed[-1]["payload"]["after"]}
        if len(prepared) > 1:
            _fail("invalid_evidence", "multiple uncommitted publish preparations")
        if prepared:
            allowed.add(prepared[0]["payload"]["commit"])
        if self.current_head not in allowed:
            _fail(
                "publish_target_moved",
                "launch target is not the exact journal-bound resume head",
                details={"allowed": sorted(allowed), "actual": self.current_head},
            )

    def _invoke(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        operation: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        guarded_executables = {
            str(self.deps.bd): "bd",
            str(self.deps.runtime): "runtime",
        }
        if self.provider is not None:
            guarded_executables[str(self.provider)] = "provider"
        fingerprint_name = guarded_executables.get(argv[0])
        before = None
        if fingerprint_name == "provider":
            before = _sha256(
                _read_secure_bytes(
                    Path(argv[0]),
                    "provider executable",
                    expected_mode=0o700,
                )
            )
        elif fingerprint_name is not None:
            before = _sha256(Path(argv[0]).read_bytes())
        result = self.deps.run(
            argv,
            cwd=str(cwd or REPO_ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if before is not None:
            try:
                after = (
                    _sha256(
                        _read_secure_bytes(
                            Path(argv[0]),
                            "provider executable",
                            expected_mode=0o700,
                        )
                    )
                    if fingerprint_name == "provider"
                    else _sha256(Path(argv[0]).read_bytes())
                )
            except OSError:
                _fail(
                    "executable_drift",
                    f"{fingerprint_name} disappeared during {operation}",
                )
            if after != before:
                _fail(
                    "executable_drift",
                    f"{fingerprint_name} changed during {operation}",
                )
        if check and result.returncode != 0:
            _fail(
                "command_failed",
                f"{operation} failed",
                details={
                    "argv": argv,
                    "returncode": result.returncode,
                    "stderr": result.stderr[-4000:],
                },
            )
        return result

    def _git(self, argv: list[str], *, cwd: Path | None = None) -> str:
        return self._invoke(
            ["git", *argv],
            cwd=cwd,
            operation=f"git {argv[0]}",
        ).stdout

    def _bd_json(self, argv: list[str], operation: str) -> dict[str, Any]:
        result = self._invoke(
            [str(self.deps.bd), *argv],
            operation=operation,
        )
        return _json_result(result.stdout, operation)

    @staticmethod
    def _repository_identity(context: dict[str, Any]) -> dict[str, Any]:
        aliases = {
            "backend": ("backend", "backend_type"),
            "database": ("database", "database_name", "db"),
            "project": ("project", "project_id", "issue_prefix"),
        }
        identity: dict[str, Any] = {}
        for output, names in aliases.items():
            found = next((context[name] for name in names if context.get(name)), None)
            if found is None:
                _fail("invalid_bd_context", f"bd context lacks {output} identity")
            identity[output] = found
        for name in ("server_id", "server", "server_identity"):
            if context.get(name):
                identity["server"] = context[name]
                break
        return identity

    def _verify_context_repository(self) -> None:
        raw = (
            self.context.get("repo_root")
            or self.context.get("repository_root")
            or self.context.get("repo")
        )
        if not isinstance(raw, str):
            _fail("invalid_bd_context", "bd context lacks local repo_root")
        try:
            context_root = Path(raw).resolve(strict=True)
            context_common = Path(
                self._git(
                    ["-C", str(context_root), "rev-parse", "--git-common-dir"]
                ).strip()
            )
            if not context_common.is_absolute():
                context_common = context_root / context_common
            local_common = Path(self._git(["rev-parse", "--git-common-dir"]).strip())
            if not local_common.is_absolute():
                local_common = REPO_ROOT / local_common
            if context_common.resolve(strict=True) != local_common.resolve(strict=True):
                _fail(
                    "repository_identity_mismatch",
                    "bd repo_root is not this checkout's shared Git repository",
                )
        except (OSError, subprocess.SubprocessError):
            _fail("invalid_bd_context", "bd repo_root cannot be resolved")

    @staticmethod
    def _issue_prefix(context: dict[str, Any]) -> str:
        prefix = (
            context.get("issue_prefix")
            or context.get("prefix")
            or CONTAINER_ID.rsplit("-", 1)[0]
        )
        if not isinstance(prefix, str) or re.fullmatch(r"[a-z0-9][a-z0-9-]*", prefix) is None:
            _fail("invalid_bd_context", "bd context lacks canonical issue prefix")
        return prefix

    def _verify_attestation(self) -> str:
        status = self._git(
            [
                "status",
                "--porcelain=v2",
                "--untracked-files=all",
                "--ignored=matching",
            ]
        )
        if status:
            _fail(
                "dirty_attestation_checkout",
                "bootstrap checkout must have no tracked, untracked, or ignored dirt",
            )
        submodules = self._git(["submodule", "status", "--recursive"])
        for line in submodules.splitlines():
            if line[:1] in {"-", "+", "U"}:
                _fail(
                    "dirty_attestation_checkout",
                    "bootstrap submodule state is not exact",
                )
            fields = line[1:].split()
            if len(fields) < 2 or _GIT40.fullmatch(fields[0]) is None:
                _fail("dirty_attestation_checkout", "malformed submodule status")
            submodule = (REPO_ROOT / fields[1]).resolve(strict=True)
            submodule.relative_to(REPO_ROOT.resolve(strict=True))
            if (
                self._git(["rev-parse", "HEAD"], cwd=submodule).strip()
                != fields[0]
                or self._git(
                    [
                        "status",
                        "--porcelain=v2",
                        "--untracked-files=all",
                        "--ignored=matching",
                    ],
                    cwd=submodule,
                )
            ):
                _fail(
                    "dirty_attestation_checkout",
                    f"dirty recursive submodule: {fields[1]}",
                )
        current_head = self._git(["rev-parse", "HEAD"]).strip()
        head = self.args.reviewed_commit
        if _GIT40.fullmatch(head) is None:
            _fail("reviewed_commit_mismatch", "--reviewed-commit is not a Git commit")
        if self._invoke(
            ["git", "merge-base", "--is-ancestor", head, current_head],
            operation="verify reviewed bootstrap ancestor",
            check=False,
        ).returncode != 0:
            _fail(
                "reviewed_commit_mismatch",
                "reviewed attestation is not an ancestor of the launch target",
            )
        parent = self._git(["rev-parse", f"{head}^"]).strip()
        if parent != self.attestation["source_commit"]:
            _fail("invalid_attestation", "attestation child has the wrong parent")
        changed = [
            line
            for line in self._git(
                ["diff-tree", "--no-commit-id", "--name-only", "-r", head]
            ).splitlines()
            if line
        ]
        config_relative = CONFIG_PATH.relative_to(REPO_ROOT).as_posix()
        if changed != [config_relative]:
            _fail(
                "invalid_attestation",
                "attestation child must change only the bootstrap config",
                details={"changed": changed},
            )
        checks = {
            SPEC_PATH: self.attestation["spec_sha256"],
            WORKFLOW_PATH: self.attestation["workflow_sha256"],
            SCRIPT_PATH.relative_to(REPO_ROOT).as_posix(): self.attestation[
                "controller_sha256"
            ],
            **self.attestation["task_sha256"],
        }
        for path, expected in checks.items():
            blob = self._git(["show", f"{parent}:{path}"]).encode("utf-8")
            if _sha256(blob) != expected:
                _fail("invalid_attestation", f"attested source hash drift: {path}")
            current = (REPO_ROOT / path).read_bytes()
            if path != config_relative and current != blob:
                _fail("invalid_attestation", f"attested working bytes drift: {path}")
        source_config = self._git(["show", f"{parent}:{config_relative}"]).encode(
            "utf-8"
        )
        if _sha256(source_config) != self.attestation["source_config_sha256"]:
            _fail("invalid_attestation", "source config digest mismatch")
        source_timestamp = int(
            self._git(["show", "-s", "--format=%at", parent]).strip()
        )
        source_date = datetime.fromtimestamp(
            source_timestamp,
            tz=timezone.utc,
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        if source_date != self.attestation["source_date_utc"]:
            _fail("invalid_attestation", "source commit date mismatch")
        return head

    def _effect(
        self,
        kind: str,
        request: dict[str, Any],
        observe: Callable[[], dict[str, Any] | None],
        action: Callable[[], Any],
        *,
        reobserve_committed: bool = False,
    ) -> dict[str, Any]:
        committed = self.journal.committed(kind)
        if committed is not None:
            if reobserve_committed:
                observed = observe()
                if observed is None:
                    _fail(
                        "committed_stage_drift",
                        f"{kind} committed receipt can no longer be observed",
                    )
                expected_observation = committed.get("observation")
                if expected_observation != observed:
                    _fail(
                        "committed_stage_drift",
                        f"{kind} committed observation changed",
                    )
            return committed
        prepared = self.journal.prepared(kind)
        if prepared is not None and prepared != request:
            _fail("prepared_request_mismatch", f"{kind} prepared request changed")
        if prepared is None:
            self.journal.append(kind, "prepared", request)
            self.deps.crash(f"{kind}:after_prepare")
        observed = observe()
        action_response: Any = None
        if observed is None:
            action_response = action()
            self.deps.crash(f"{kind}:after_action")
            observed = observe()
        if observed is None:
            _fail("missing_poststate", f"{kind} has no exact post-state")
        if (
            action_response is not None
            and isinstance(observed.get("provider_response"), dict)
            and action_response != observed["provider_response"]
        ):
            _fail(
                "invalid_provider_response",
                f"{kind} action response differs from durable provider history",
            )
        receipt = {
            "request_sha256": _sha256(_canonical_json(request)),
            "observation": observed,
            **observed,
        }
        if action_response is not None:
            receipt["action_response"] = action_response
        self.journal.append(kind, "committed", receipt)
        self.deps.crash(f"{kind}:after_commit")
        return receipt

    def _show(self, issue: str) -> dict[str, Any] | None:
        result = self._invoke(
            [str(self.deps.bd), "show", "--json", "--", issue],
            operation=f"show {issue}",
            check=False,
        )
        if result.returncode != 0:
            return None
        return _json_result(result.stdout, f"show {issue}")

    def _history(self, issue: str) -> list[dict[str, Any]]:
        result = self._invoke(
            [str(self.deps.bd), "history", "--json", "--", issue],
            operation=f"history {issue}",
        )
        try:
            value = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            _fail(
                "invalid_command_result",
                f"history {issue} returned invalid JSON",
                details={"error": str(exc)},
            )
        if isinstance(value, dict):
            value = value.get("events") or value.get("history")
        if not isinstance(value, list) or not all(
            isinstance(event, dict) for event in value
        ):
            _fail("invalid_command_result", f"history {issue} is not an event list")
        return value

    @staticmethod
    def _edge_multiset(issue: dict[str, Any]) -> list[tuple[str, str]]:
        raw = issue.get("dependencies")
        if raw is None:
            raw = issue.get("edges", [])
        if not isinstance(raw, list):
            _fail("invalid_issue_state", "issue dependencies are not a list")
        edges: list[tuple[str, str]] = []
        for edge in raw:
            if isinstance(edge, str):
                edges.append((edge, "blocks"))
                continue
            if not isinstance(edge, dict):
                _fail("invalid_issue_state", "issue dependency is malformed")
            target = (
                edge.get("depends_on_id")
                or edge.get("depends_on")
                or edge.get("id")
                or edge.get("issue_id")
            )
            edge_type = (
                edge.get("dependency_type")
                or edge.get("type")
                or edge.get("relation")
            )
            if not isinstance(target, str) or not isinstance(edge_type, str):
                _fail("invalid_issue_state", "issue dependency edge is unbounded")
            edges.append((target, edge_type))
        return sorted(edges)

    def _require_edges(
        self,
        issue: dict[str, Any],
        expected: list[tuple[str, str]],
        where: str,
    ) -> None:
        actual = self._edge_multiset(issue)
        if actual != sorted(expected):
            _fail(
                "issue_edge_mismatch",
                f"{where} dependency edge multiset differs",
                details={"actual": actual, "expected": sorted(expected)},
            )

    def _incident_edges(
        self,
        issue_id: str,
        issues: list[dict[str, Any]],
    ) -> list[list[str]]:
        incident: list[list[str]] = []
        for source in issues:
            source_id = source.get("id")
            if not isinstance(source_id, str):
                _fail("invalid_issue_state", "issue list contains no stable id")
            for target, edge_type in self._edge_multiset(source):
                if source_id == issue_id or target == issue_id:
                    incident.append([source_id, target, edge_type])
        return sorted(incident)

    def _issue_definition_projection(
        self,
        issue: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "id": issue.get("id"),
            "title": issue.get("title"),
            "description": issue.get("description"),
            "acceptance": issue.get("acceptance"),
            "issue_type": issue.get("issue_type") or issue.get("type"),
            "priority": issue.get("priority"),
            "external_ref": issue.get("external_ref"),
            "metadata": self._issue_metadata(issue),
            "edges": [list(edge) for edge in self._edge_multiset(issue)],
        }

    def _terminal_issue_proof(
        self,
        bootstrap_id: str,
        issue_id: str,
        all_issues: list[dict[str, Any]],
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        worker_actor = (
            f"agentic:bootstrap-build:{self.intent}:"
            f"{self.worker_token}:{bootstrap_id.lower()}"
        )
        matches = [
            candidate
            for candidate in all_issues
            if candidate.get("id") == issue_id
        ]
        if len(matches) != 1:
            _fail(
                "terminal_poststate_mismatch",
                f"{bootstrap_id} is absent or duplicated in terminal snapshot",
            )
        issue = self._exact_issue(
            bootstrap_id,
            issue_id,
            status="closed",
            assignee=worker_actor,
            finalized=True,
            exact_metadata=True,
            empty_notes=True,
            candidate=matches[0],
        )
        if issue is None:
            _fail(
                "terminal_poststate_mismatch",
                f"{bootstrap_id} is not in the exact complete terminal state",
            )
        outgoing = [(CONTAINER_ID, "related")]
        previous = {
            "00B": self.issue_ids.get("00A"),
            "00C": self.issue_ids.get("00B"),
            "00D": self.issue_ids.get("00C"),
        }.get(bootstrap_id)
        if previous is not None:
            outgoing.append((previous, "blocks"))
        self._require_edges(issue, outgoing, f"{bootstrap_id} terminal")
        expected_incident = [
            [issue_id, target, edge_type] for target, edge_type in outgoing
        ]
        following = {
            "00A": self.issue_ids.get("00B"),
            "00B": self.issue_ids.get("00C"),
            "00C": self.issue_ids.get("00D"),
        }.get(bootstrap_id)
        if following is not None:
            expected_incident.append([following, issue_id, "blocks"])
        actual_incident = self._incident_edges(issue_id, all_issues)
        if actual_incident != sorted(expected_incident):
            _fail(
                "terminal_poststate_mismatch",
                f"{bootstrap_id} incident edge multiset differs",
                details={
                    "actual": actual_incident,
                    "expected": sorted(expected_incident),
                },
            )
        claim = self.journal.committed(f"{bootstrap_id.lower()}_claim")
        mutation_kind = (
            "00a_finalize"
            if bootstrap_id == "00A"
            else f"{bootstrap_id.lower()}_close"
        )
        mutation = self.journal.committed(mutation_kind)
        if claim is None or mutation is None:
            _fail(
                "invalid_evidence",
                f"{bootstrap_id} terminal proof lacks claim/mutation evidence",
            )
        claim_history = claim.get("observation", {}).get("history")
        mutation_event = mutation.get("observation", {}).get("history")
        if not isinstance(claim_history, list) or not isinstance(
            mutation_event,
            dict,
        ):
            _fail(
                "invalid_evidence",
                f"{bootstrap_id} terminal history evidence is incomplete",
            )
        expected_history = [*claim_history, mutation_event]
        actual_history = history
        if sorted(map(_canonical_json, actual_history)) != sorted(
            map(_canonical_json, expected_history)
        ):
            _fail(
                "terminal_poststate_mismatch",
                f"{bootstrap_id} complete history differs",
            )
        provider_receipt = mutation["observation"]["provider_response"]["receipt"]
        if (
            issue.get("authority_revision")
            != provider_receipt["after_revision"]
        ):
            _fail(
                "terminal_poststate_mismatch",
                f"{bootstrap_id} terminal revision differs from authority receipt",
            )
        return {
            **self._issue_definition_projection(issue),
            "status": issue.get("status"),
            "assignee": issue.get("assignee") or None,
            "notes": issue.get("notes") or "",
            "authority_revision": issue.get("authority_revision"),
            "history": actual_history,
            "incident_edges": actual_incident,
        }

    def _capture_terminal_snapshot_once(self) -> dict[str, Any]:
        # Provider mutations advance the authority identity.  Bracket tracker
        # reads with that identity so a provider-mediated write cannot produce
        # a torn issue/history proof.
        authority_before = self._authority_identity(
            "terminal snapshot authority before",
        )
        self.deps.crash("terminal_snapshot:after_authority_before")
        all_issues = self._all_issues()
        histories = {
            bootstrap_id: self._history(issue_id)
            for bootstrap_id, issue_id in self.issue_ids.items()
        }
        self.deps.crash("terminal_snapshot:after_tracker_reads")
        authority_after = self._authority_identity(
            "terminal snapshot authority after",
        )
        if authority_before != authority_after:
            _fail(
                "terminal_snapshot_drift",
                "authority changed during terminal tracker reads",
            )
        issue_proofs = {
            bootstrap_id: self._terminal_issue_proof(
                bootstrap_id,
                issue_id,
                all_issues,
                histories[bootstrap_id],
            )
            for bootstrap_id, issue_id in self.issue_ids.items()
        }
        final_close = self.journal.committed("00d_close")
        final_cursor = (
            final_close.get("observation", {})
            .get("provider_response", {})
            .get("receipt", {})
            .get("history_cursor")
            if final_close is not None
            else None
        )
        if (
            authority_after["profiles"] != ["core", "conditional", "full"]
            or authority_after["schema_fingerprint"]
            != authority_after["full_profile_identity"][
                "full_schema_fingerprint"
            ]
            or authority_after["history_cursor"] != final_cursor
        ):
            _fail(
                "terminal_poststate_mismatch",
                "terminal provider does not expose the exact full profile",
            )
        return {
            "issues": issue_proofs,
            "authority": authority_after,
        }

    def _capture_stable_terminal_snapshot(self) -> dict[str, Any]:
        first = self._capture_terminal_snapshot_once()
        self.deps.crash("terminal_snapshot:between_captures")
        second = self._capture_terminal_snapshot_once()
        if first != second:
            _fail(
                "terminal_snapshot_drift",
                "terminal tracker/provider snapshot changed across barrier",
            )
        return second

    def _require_history_event(
        self,
        issue_id: str,
        *,
        action: str,
        actor: str,
        reason: str | None = None,
        request_sha256: str | None = None,
        before_revision: str | None | object = ...,
        after_revision: str | None = None,
        history_cursor: str | None = None,
    ) -> dict[str, Any]:
        matches = []
        for event in self._history(issue_id):
            if event.get("action") != action or event.get("actor") != actor:
                continue
            if reason is not None and event.get("reason") != reason:
                continue
            if (
                request_sha256 is not None
                and event.get("request_sha256") != request_sha256
            ):
                continue
            if (
                after_revision is not None
                and event.get("after_revision") != after_revision
            ):
                continue
            if (
                before_revision is not ...
                and event.get("before_revision") != before_revision
            ):
                continue
            if (
                history_cursor is not None
                and event.get("history_cursor") != history_cursor
            ):
                continue
            matches.append(event)
        if len(matches) != 1:
            _fail(
                "issue_history_mismatch",
                f"{issue_id} has {len(matches)} matching {action} events",
            )
        event = matches[0]
        expected_keys = {"action", "actor"}
        if reason is not None:
            expected_keys.add("reason")
        if request_sha256 is not None:
            expected_keys.add("request_sha256")
        if (
            after_revision is not None
            or before_revision is not ...
            or history_cursor is not None
        ):
            expected_keys.update(
                {"before_revision", "after_revision", "history_cursor"}
            )
        if set(event) != expected_keys:
            _fail(
                "issue_history_mismatch",
                f"{issue_id} {action} history event has an open schema",
            )
        return event

    @staticmethod
    def _issue_metadata(issue: dict[str, Any]) -> dict[str, Any]:
        metadata = issue.get("metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                return {}
        return metadata if isinstance(metadata, dict) else {}

    def _expected_issue_metadata(self, bootstrap_id: str) -> dict[str, Any]:
        task = next(
            item
            for item in self.config["tasks"]
            if item["bootstrap_id"] == bootstrap_id
        )
        metadata = dict(task["envelope"]["metadata"])
        if bootstrap_id == "00A":
            metadata["bootstrap"] = {
                "schema_version": "agentic.registration-bootstrap-metadata/v1",
                "intent": self.intent,
                "source_commit": self.attestation["source_commit"],
                "task_sha256": task["task_sha256"],
                "definition_hash": task["definition_hash"],
            }
        return metadata

    def _exact_issue(
        self,
        bootstrap_id: str,
        issue_id: str,
        *,
        status: str,
        assignee: str | None,
        finalized: bool,
        exact_metadata: bool = False,
        empty_notes: bool = False,
        candidate: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        issue = candidate if candidate is not None else self._show(issue_id)
        if issue is None:
            return None
        task = next(
            item for item in self.config["tasks"] if item["bootstrap_id"] == bootstrap_id
        )
        envelope = task["envelope"]
        expected_ref = envelope["canonical_external_ref"] if finalized else envelope["external_ref"]
        actual_ref = issue.get("external_ref")
        actual_assignee = issue.get("assignee") or None
        required = {
            "id": issue_id,
            "title": envelope["title"],
            "description": envelope["description"],
            "acceptance": envelope["acceptance"],
            "issue_type": envelope["issue_type"],
            "status": status,
            "priority": 0,
        }
        for key, value in required.items():
            actual = (
                issue.get("type")
                if key == "issue_type" and "issue_type" not in issue
                else issue.get(key)
            )
            if key == "priority" and isinstance(actual, str) and actual.startswith("P"):
                actual = int(actual[1:])
            if actual != value:
                return None
        if actual_ref != expected_ref or actual_assignee != assignee:
            return None
        metadata = self._issue_metadata(issue)
        expected_metadata = self._expected_issue_metadata(bootstrap_id)
        if (
            metadata != expected_metadata
            if exact_metadata
            else any(
                metadata.get(key) != value
                for key, value in expected_metadata.items()
            )
        ):
            return None
        if empty_notes and (issue.get("notes") or "") != "":
            return None
        revision = issue.get("authority_revision")
        if not isinstance(revision, str) or not revision:
            return None
        return issue

    def _request_file(self, name: str, value: dict[str, Any]) -> Path:
        digest = _sha256(_canonical_json(value))
        path = self.root / "requests" / f"{name}-{digest}.json"
        if _secure_exists(path):
            if _read_json_file(path, name) != value:
                _fail("request_collision", f"request file collision for {name}")
        else:
            _write_atomic(
                path,
                value,
                immutable=True,
                temp_owner=self.journal.process_owner,
            )
        return path

    def _create_00a(self) -> dict[str, Any]:
        task = self.config["tasks"][0]
        envelope = task["envelope"]
        metadata = self._expected_issue_metadata("00A")
        metadata_path = self._request_file("00a-metadata", metadata)
        argv = [
            str(self.deps.bd),
            "create",
            "--id",
            self.expected_issue,
            "--title",
            envelope["title"],
            "--description",
            envelope["description"],
            "--acceptance",
            envelope["acceptance"],
            "--type",
            "task",
            "--priority",
            "0",
            "--metadata",
            f"@{metadata_path}",
            "--actor",
            self.actor,
            "--json",
        ]
        request = {
            "argv": argv,
            "issue": self.expected_issue,
            "metadata_sha256": _sha256(_canonical_json(metadata)),
        }

        def observe() -> dict[str, Any] | None:
            issue = self._exact_issue(
                "00A",
                self.expected_issue,
                status="open",
                assignee=None,
                finalized=False,
            )
            if issue is None:
                return None
            actual_metadata = self._issue_metadata(issue)
            if actual_metadata.get("bootstrap") != metadata["bootstrap"]:
                _fail(
                    "bootstrap_issue_conflict",
                    "deterministic 00A ID names a foreign envelope",
                )
            self._require_edges(issue, [], "00A pre-core create")
            creation = self._require_history_event(
                self.expected_issue,
                action="create",
                actor=self.actor,
            )
            return {
                "issue": self.expected_issue,
                "post": issue,
                "creation": creation,
            }

        def action() -> None:
            result = self._invoke(argv, operation="create 00A", check=False)
            if result.returncode != 0 and observe() is None:
                _fail(
                    "bootstrap_issue_conflict",
                    "00A create failed without the exact intended issue",
                    details={"stderr": result.stderr[-4000:]},
                )

        return self._effect("issue00a", request, observe, action)

    def _claim(self, bootstrap_id: str, issue_id: str, run_id: str) -> dict[str, Any]:
        actor = (
            f"agentic:bootstrap-build:{run_id}:"
            f"{self.worker_token}:{bootstrap_id.lower()}"
        )
        request = {
            "issue": issue_id,
            "bootstrap_id": bootstrap_id,
            "actor": actor,
            "argv": [
                str(self.deps.bd),
                "update",
                "--claim",
                "--actor",
                actor,
                "--json",
                "--",
                issue_id,
            ],
        }

        def observe() -> dict[str, Any] | None:
            issue = self._exact_issue(
                bootstrap_id,
                issue_id,
                status="in_progress",
                assignee=actor,
                finalized=bootstrap_id != "00A",
            )
            return (
                {
                    "issue": issue_id,
                    "actor": actor,
                    "post": issue,
                    "history": self._history(issue_id),
                }
                if issue
                else None
            )

        def action() -> None:
            ready = self._invoke(
                [str(self.deps.bd), "ready", "--json"],
                operation=f"ready check {bootstrap_id}",
            )
            try:
                ready_value = json.loads(ready.stdout)
            except json.JSONDecodeError as exc:
                _fail(
                    "invalid_command_result",
                    "bd ready returned invalid JSON",
                    details={"error": str(exc)},
                )
            if (
                not isinstance(ready_value, list)
                or issue_id not in {item.get("id") for item in ready_value if isinstance(item, dict)}
            ):
                _fail("claim_not_ready", f"{bootstrap_id} is not freshly ready")
            result = self._invoke(request["argv"], operation=f"claim {bootstrap_id}", check=False)
            if result.returncode != 0 and observe() is None:
                _fail(
                    "claim_lost",
                    f"{bootstrap_id} claim lost",
                    details={"stderr": result.stderr[-4000:]},
                )

        return self._effect(
            f"{bootstrap_id.lower()}_claim",
            request,
            observe,
            action,
            reobserve_committed=True,
        )

    def _reverify_claim_before_authority_action(
        self,
        bootstrap_id: str,
        issue_id: str,
    ) -> None:
        # Publication does not preserve a tracker lease.  A prepared provider
        # stage may resume after requeue or reassignment, so spend the committed
        # claim again immediately before any not-yet-observed authority action.
        self._claim(bootstrap_id, issue_id, self.intent)

    def _worktree(self, bootstrap_id: str, base: str) -> Path:
        path = self.root / "worktrees" / bootstrap_id.lower()
        request = {"bootstrap_id": bootstrap_id, "base": base, "path": str(path)}

        def observe() -> dict[str, Any] | None:
            if not path.exists():
                return None
            head = self._git(["rev-parse", "HEAD"], cwd=path).strip()
            if head != base and self.journal.committed(
                f"{bootstrap_id.lower()}_worker"
            ) is None:
                _fail("worktree_drift", f"{bootstrap_id} worktree moved before worker receipt")
            return {"path": str(path), "head": head}

        def action() -> None:
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            self._invoke(
                ["git", "worktree", "add", "--detach", str(path), base],
                operation=f"create {bootstrap_id} worktree",
            )

        self._effect(f"{bootstrap_id.lower()}_worktree", request, observe, action)
        return path

    def _pointer_prompt(
        self,
        task_path: str,
        dispatch: str,
        workflow_path: Path,
    ) -> str:
        return "\n".join(
            (
                f"Read and follow the workflow skill at {workflow_path}.",
                "The user explicitly authorizes this workflow to act only on the supplied target.",
                f"Target: artifact {task_path}",
                f"Dispatch: {dispatch}",
            )
        )

    def _launch_role(
        self,
        *,
        bootstrap_id: str,
        issue_id: str,
        run_id: str,
        worktree: Path,
        role: str,
    ) -> dict[str, Any]:
        task = next(
            item for item in self.config["tasks"] if item["bootstrap_id"] == bootstrap_id
        )
        result_path = self.root / "results" / f"{bootstrap_id.lower()}-{role}.json"
        envelope = {
            "schema_version": "agentic.registration-bootstrap-launch/v1",
            "role": role,
            "intent": self.intent,
            "run_id": run_id,
            "issue": issue_id,
            "bootstrap_id": bootstrap_id,
            "actor": (
                f"agentic:bootstrap-build:{run_id}:"
                f"{self.worker_token}:{bootstrap_id.lower()}"
            ),
            "repository": str(REPO_ROOT),
            "worktree": str(worktree),
            "base_commit": self._git(["merge-base", self.current_head, self.current_head]).strip(),
            "task": task["source"],
            "task_sha256": task["task_sha256"],
            "definition_hash": task["definition_hash"],
            "config_sha256": _sha256(self.config_raw),
            "attestation_commit": self.launch_commit,
            "result_path": str(result_path),
        }
        envelope_path = self._request_file(
            f"{bootstrap_id.lower()}-{role}-envelope",
            envelope,
        )
        workflow = (worktree / WORKFLOW_PATH).resolve(strict=True)
        task_in_worktree = (worktree / task["source"]).resolve(strict=True)
        prompt = self._pointer_prompt(
            task["source"],
            run_id,
            workflow,
        )
        argv = [
            str(self.deps.runtime),
            *self.config["provider"]["runtime_argv"][self.args.runtime],
            prompt,
        ]
        request = {
            "envelope_sha256": _sha256(_canonical_json(envelope)),
            "argv": argv,
            "role": role,
            "result_path": str(result_path),
        }
        schema = WORKER_RESULT_SCHEMA if role == "worker" else REVIEW_RESULT_SCHEMA

        def observe() -> dict[str, Any] | None:
            if not _secure_exists(result_path):
                return None
            result = _read_json_file(result_path, f"{bootstrap_id} {role} result")
            if (
                result.get("schema_version") != schema
                or result.get("intent") != self.intent
                or result.get("run_id") != run_id
                or result.get("bootstrap_id") != bootstrap_id
                or result.get("issue") != issue_id
                or result.get("ok") is not True
            ):
                _fail("invalid_child_result", f"{bootstrap_id} {role} result is unbound")
            if role == "worker":
                _exact_keys(
                    result,
                    {
                        "schema_version",
                        "ok",
                        "intent",
                        "run_id",
                        "bootstrap_id",
                        "issue",
                        "base_commit",
                        "commit",
                        "provider",
                    },
                    f"{bootstrap_id} worker result",
                )
            else:
                _exact_keys(
                    result,
                    {
                        "schema_version",
                        "ok",
                        "verdict",
                        "intent",
                        "run_id",
                        "bootstrap_id",
                        "issue",
                        "base_commit",
                        "commit",
                        "reviewer",
                        "diff_sha256",
                    },
                    f"{bootstrap_id} review result",
                )
                if result.get("verdict") != "READY":
                    _fail("review_rejected", f"{bootstrap_id} independent review is not READY")
                if (
                    result.get("commit")
                    != self._git(["rev-parse", "HEAD"], cwd=worktree).strip()
                    or result.get("base_commit") != envelope["base_commit"]
                    or not isinstance(result.get("reviewer"), str)
                    or not result["reviewer"].strip()
                ):
                    _fail("review_rejected", f"{bootstrap_id} review binding is incomplete")
                diff = self._invoke(
                    [
                        "git",
                        "diff",
                        "--binary",
                        envelope["base_commit"],
                        result["commit"],
                        "--",
                    ],
                    cwd=worktree,
                    operation=f"{bootstrap_id} review diff",
                ).stdout.encode()
                if result.get("diff_sha256") != _sha256(diff):
                    _fail("review_rejected", f"{bootstrap_id} review did not bind exact diff")
            return {"result": result, "result_sha256": _sha256(_canonical_json(result))}

        def action() -> None:
            _secure_mkdir(result_path.parent)
            env = {
                **os.environ,
                "AGENTIC_BOOTSTRAP_ENVELOPE": str(envelope_path),
                "AGENTIC_BOOTSTRAP_RESULT": str(result_path),
                "AGENTIC_BOOTSTRAP_ROLE": role,
            }
            result = self._invoke(
                argv,
                cwd=worktree,
                env=env,
                operation=f"launch {bootstrap_id} {role}",
                check=False,
            )
            if result.returncode != 0 and observe() is None:
                _fail(
                    "native_runtime_failed",
                    f"{bootstrap_id} {role} runtime failed",
                    details={"returncode": result.returncode, "stderr": result.stderr[-4000:]},
                )

        receipt = self._effect(
            f"{bootstrap_id.lower()}_{role}",
            request,
            observe,
            action,
        )
        if role == "worker":
            commit = receipt["result"].get("commit")
            if _GIT40.fullmatch(str(commit)) is None:
                _fail("invalid_child_result", f"{bootstrap_id} worker omitted commit")
            actual = self._git(["rev-parse", "HEAD"], cwd=worktree).strip()
            if actual != commit:
                _fail("invalid_child_result", f"{bootstrap_id} worker commit is not worktree HEAD")
            if self._git(
                [
                    "status",
                    "--porcelain=v2",
                    "--untracked-files=all",
                    "--ignored=matching",
                ],
                cwd=worktree,
            ):
                _fail("dirty_worker", f"{bootstrap_id} worker left a dirty worktree")
            reviewed_head = self._git(["rev-parse", "HEAD"], cwd=worktree).strip()
            if reviewed_head != commit:
                _fail("reviewed_commit_moved", f"{bootstrap_id} changed after review")
            task_in_worktree.relative_to(worktree)
        return receipt["result"]

    def _accept(self, bootstrap_id: str, worktree: Path) -> dict[str, Any]:
        task = next(
            item for item in self.config["tasks"] if item["bootstrap_id"] == bootstrap_id
        )
        acceptance = task["envelope"]["acceptance"]
        commands = re.findall(r"`([^`\n]+)`\s*→", acceptance)
        if not commands:
            _fail("invalid_task_definition", f"{bootstrap_id} has no runnable acceptance")
        argv_commands: list[list[str]] = []
        for command in commands:
            argv = shlex.split(command)
            if not argv or any(token in {";", "&&", "||", "|", ">", "<"} for token in argv):
                _fail("unsafe_acceptance", f"{bootstrap_id} acceptance is not one argv command")
            argv_commands.append(argv)
        request = {"bootstrap_id": bootstrap_id, "commands": argv_commands}

        def observe() -> dict[str, Any] | None:
            path = self.root / "results" / f"{bootstrap_id.lower()}-acceptance.json"
            if not _secure_exists(path):
                return None
            value = _read_json_file(path, f"{bootstrap_id} acceptance")
            return value if value.get("ok") is True and value.get("commands") == argv_commands else None

        def action() -> None:
            results = []
            for argv in argv_commands:
                process = self._invoke(
                    argv,
                    cwd=worktree,
                    operation=f"{bootstrap_id} acceptance",
                    check=False,
                )
                results.append(
                    {
                        "argv": argv,
                        "returncode": process.returncode,
                        "stdout_sha256": _sha256(process.stdout.encode()),
                        "stderr_sha256": _sha256(process.stderr.encode()),
                    }
                )
                if process.returncode != 0:
                    _fail(
                        "acceptance_failed",
                        f"{bootstrap_id} acceptance failed",
                        details={"argv": argv, "stderr": process.stderr[-4000:]},
                    )
            _write_atomic(
                self.root / "results" / f"{bootstrap_id.lower()}-acceptance.json",
                {"ok": True, "commands": argv_commands, "results": results},
                immutable=True,
                temp_owner=self.journal.process_owner,
            )

        return self._effect(
            f"{bootstrap_id.lower()}_acceptance",
            request,
            observe,
            action,
        )

    def _publish(self, bootstrap_id: str, commit: str, base: str) -> dict[str, Any]:
        request = {
            "bootstrap_id": bootstrap_id,
            "base": base,
            "commit": commit,
            "target": str(REPO_ROOT),
        }

        def observe() -> dict[str, Any] | None:
            head = self._git(["rev-parse", "HEAD"]).strip()
            if head == commit:
                return {"before": base, "after": commit}
            if head != base:
                _fail(
                    "publish_target_moved",
                    f"{bootstrap_id} target moved outside this bootstrap",
                    details={"expected": base, "actual": head},
                )
            return None

        def action() -> None:
            if self._git(
                [
                    "status",
                    "--porcelain=v2",
                    "--untracked-files=all",
                    "--ignored=matching",
                ]
            ):
                _fail("dirty_publish_target", "bootstrap publish target is dirty")
            ancestor = self._invoke(
                ["git", "merge-base", "--is-ancestor", base, commit],
                operation=f"verify {bootstrap_id} ancestry",
                check=False,
            )
            if ancestor.returncode != 0:
                _fail("non_fast_forward_worker", f"{bootstrap_id} commit is not a descendant")
            self._invoke(
                ["git", "merge", "--ff-only", "--no-edit", commit],
                operation=f"publish {bootstrap_id}",
            )

        receipt = self._effect(
            f"{bootstrap_id.lower()}_publish",
            request,
            observe,
            action,
        )
        self.current_head = commit
        return receipt

    def _provider_from_result(self, result: dict[str, Any], worktree: Path) -> Path:
        provider = result.get("provider")
        if not isinstance(provider, dict):
            _fail("invalid_child_result", "worker omitted provider artifact")
        relative = provider.get("path")
        digest = provider.get("sha256")
        if (
            not isinstance(relative, str)
            or _HEX64.fullmatch(str(digest)) is None
            or provider.get("source_commit") != result.get("commit")
        ):
            _fail("invalid_child_result", "worker provider artifact is malformed")
        provider_path = Path(relative)
        if not provider_path.is_absolute():
            _fail(
                "invalid_child_result",
                "provider artifact must be outside Git in bootstrap state",
            )
        provider_path = _lexical_absolute(provider_path)
        try:
            provider_path.relative_to(self.root / "outputs")
        except ValueError:
            _fail(
                "invalid_child_result",
                "provider artifact escaped the bootstrap output root",
            )
        provider_raw = _read_secure_bytes(
            provider_path,
            "worker provider",
            expected_mode=0o700,
        )
        if _sha256(provider_raw) != digest:
            _fail("provider_digest_mismatch", "worker provider digest mismatch")
        if not os.access(provider_path, os.X_OK):
            _fail("provider_digest_mismatch", "worker provider is not executable")
        artifact_dir = self.root / "providers" / str(digest)
        artifact = artifact_dir / "bd"
        _secure_mkdir(artifact_dir)
        if _secure_exists(artifact):
            if (
                _sha256(
                    _read_secure_bytes(
                        artifact,
                        "state provider",
                        expected_mode=0o700,
                    )
                )
                != digest
            ):
                _fail("provider_digest_mismatch", "state provider artifact drift")
        else:
            temporary_name = (
                f".bd.{self.journal.process_owner}.{os.getpid()}."
                f"{uuid.uuid4().hex}.tmp"
            )
            parent = _open_secure_dir(artifact_dir)
            descriptor = os.open(
                temporary_name,
                os.O_CREAT
                | os.O_EXCL
                | os.O_WRONLY
                | getattr(os, "O_NOFOLLOW", 0),
                0o700,
                dir_fd=parent,
            )
            try:
                with os.fdopen(descriptor, "wb", closefd=False) as handle:
                    handle.write(provider_raw)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.fchmod(descriptor, 0o700)
                os.close(descriptor)
                descriptor = -1
                try:
                    os.link(
                        temporary_name,
                        "bd",
                        src_dir_fd=parent,
                        dst_dir_fd=parent,
                        follow_symlinks=False,
                    )
                except FileExistsError:
                    if (
                        _sha256(
                            _read_secure_bytes(
                                artifact,
                                "raced state provider",
                                expected_mode=0o700,
                            )
                        )
                        != digest
                    ):
                        _fail(
                            "provider_digest_mismatch",
                            "raced provider artifact has another digest",
                        )
                os.unlink(temporary_name, dir_fd=parent)
                os.fsync(parent)
            finally:
                if descriptor >= 0:
                    os.close(descriptor)
                with contextlib.suppress(FileNotFoundError):
                    os.unlink(temporary_name, dir_fd=parent)
                os.close(parent)
        artifact_raw = _read_secure_bytes(
            artifact,
            "content-addressed provider",
            expected_mode=0o700,
        )
        if _sha256(artifact_raw) != digest or not os.access(artifact, os.X_OK):
            _fail("provider_digest_mismatch", "content-addressed provider copy failed")
        return artifact

    def _provider_json(self, argv: list[str], operation: str) -> dict[str, Any]:
        if self.provider is None:
            _fail("provider_unavailable", f"{operation} requires the published provider")
        result = self._invoke(
            [str(self.provider), *argv],
            operation=operation,
            check=False,
        )
        if result.returncode != 0:
            _fail(
                "provider_failed",
                f"{operation} failed",
                details={"stderr": result.stderr[-4000:]},
            )
        value = _json_result(result.stdout, operation)
        if value.get("ok") is not True:
            _fail("provider_failed", f"{operation} did not report ok")
        return value

    def _provider_sha256(self) -> str:
        if self.provider is None:
            _fail("provider_unavailable", "provider digest requested before publish")
        return _sha256(
            _read_secure_bytes(
                self.provider,
                "published provider",
                expected_mode=0o700,
            )
        )

    def _provider_exact_keys(
        self,
        value: Any,
        expected: set[str],
        where: str,
    ) -> dict[str, Any]:
        try:
            return _exact_keys(value, expected, where)
        except BootstrapControlError as exc:
            if exc.code != "invalid_schema":
                raise
            _fail(
                "invalid_provider_response",
                f"{where} has unknown or missing keys",
                details=exc.details,
            )

    def _validate_install_receipt(self, value: Any) -> dict[str, Any]:
        receipt = self._provider_exact_keys(
            value,
            {
                "schema_version",
                "request_sha256",
                "actor",
                "profile",
                "migration_id",
                "migration_host",
                "before_schema",
                "after_schema",
                "history_cursor",
            },
            "provider install receipt",
        )
        if (
            receipt["schema_version"]
            != "agentic.bd-authority-install-receipt/v1"
            or _HEX64.fullmatch(str(receipt["request_sha256"])) is None
            or not isinstance(receipt["actor"], str)
            or receipt["profile"] not in {"core", "conditional", "full"}
            or _HEX64.fullmatch(str(receipt["migration_id"])) is None
            or _HEX64.fullmatch(str(receipt["migration_host"])) is None
            or _HEX64.fullmatch(str(receipt["before_schema"])) is None
            or _HEX64.fullmatch(str(receipt["after_schema"])) is None
            or not isinstance(receipt["history_cursor"], str)
            or not receipt["history_cursor"]
        ):
            _fail("invalid_provider_response", "provider install receipt is malformed")
        return receipt

    def _validate_mutation_receipt(self, value: Any) -> dict[str, Any]:
        receipt = self._provider_exact_keys(
            value,
            {
                "schema_version",
                "request_sha256",
                "operation",
                "actor",
                "reason",
                "issue_id",
                "before_revision",
                "after_revision",
                "history_cursor",
            },
            "provider mutation receipt",
        )
        if (
            receipt["schema_version"]
            != "agentic.bd-authority-mutation-receipt/v1"
            or _HEX64.fullmatch(str(receipt["request_sha256"])) is None
            or receipt["operation"]
            not in {"bootstrap_finalize", "guarded_create", "conditional_close"}
            or not isinstance(receipt["actor"], str)
            or not receipt["actor"]
            or not isinstance(receipt["reason"], str)
            or not receipt["reason"]
            or _ISSUE_ID.fullmatch(str(receipt["issue_id"])) is None
            or (
                receipt["before_revision"] is not None
                and not isinstance(receipt["before_revision"], str)
            )
            or not isinstance(receipt["after_revision"], str)
            or not receipt["after_revision"]
            or not isinstance(receipt["history_cursor"], str)
            or not receipt["history_cursor"]
        ):
            _fail("invalid_provider_response", "provider mutation receipt is malformed")
        return receipt

    def _authority_identity(self, operation: str) -> dict[str, Any]:
        value = self._provider_json(
            ["authority", "identity", "--no-migrate", "--json"],
            operation,
        )
        identity = self._provider_exact_keys(
            value,
            {
                "schema_version",
                "ok",
                "full_profile_identity",
                "profiles",
                "schema_fingerprint",
                "history_cursor",
                "install_receipts",
                "mutation_receipts",
            },
            "provider identity response",
        )
        profiles = identity["profiles"]
        canonical_profiles = ["core", "conditional", "full"]
        full_identity = self._provider_exact_keys(
            identity["full_profile_identity"],
            {
                "backend_mode",
                "database_identity",
                "project_identity",
                "repository_identity",
                "core_schema_fingerprint",
                "full_schema_fingerprint",
            },
            "provider full profile identity",
        )
        expected_repository_identity = _sha256(
            _canonical_json(self.repository_identity)
        )
        if (
            identity["schema_version"]
            != self.config["provider"]["response_schemas"]["identity"]
            or identity["ok"] is not True
            or full_identity["backend_mode"] != self.repository_identity["backend"]
            or full_identity["database_identity"]
            != self.repository_identity["database"]
            or full_identity["project_identity"]
            != self.repository_identity["project"]
            or full_identity["repository_identity"]
            != expected_repository_identity
            or _HEX64.fullmatch(
                str(full_identity["core_schema_fingerprint"])
            )
            is None
            or _HEX64.fullmatch(
                str(full_identity["full_schema_fingerprint"])
            )
            is None
            or not isinstance(profiles, list)
            or profiles != canonical_profiles[: len(profiles)]
            or _HEX64.fullmatch(str(identity["schema_fingerprint"])) is None
            or not isinstance(identity["history_cursor"], str)
            or not identity["history_cursor"]
            or not isinstance(identity["install_receipts"], list)
            or not isinstance(identity["mutation_receipts"], list)
        ):
            _fail("invalid_provider_response", "provider identity response is malformed")
        identity["install_receipts"] = [
            self._validate_install_receipt(receipt)
            for receipt in identity["install_receipts"]
        ]
        identity["mutation_receipts"] = [
            self._validate_mutation_receipt(receipt)
            for receipt in identity["mutation_receipts"]
        ]
        return identity

    def _validate_install_response(
        self,
        value: dict[str, Any],
        *,
        request_sha256: str,
        actor: str,
        profile: str,
        migration_id: str,
        migration_host: str,
        before_schema: str,
    ) -> dict[str, Any]:
        response = self._provider_exact_keys(
            value,
            {"schema_version", "ok", "operation", "receipt"},
            "provider install response",
        )
        receipt = self._validate_install_receipt(response["receipt"])
        if (
            response["schema_version"]
            != self.config["provider"]["response_schemas"]["install"]
            or response["ok"] is not True
            or response["operation"] != "install"
            or receipt["request_sha256"] != request_sha256
            or receipt["actor"] != actor
            or receipt["profile"] != profile
            or receipt["migration_id"] != migration_id
            or receipt["migration_host"] != migration_host
            or receipt["before_schema"] != before_schema
        ):
            _fail("invalid_provider_response", "provider install response is unbound")
        return response

    def _validate_mutation_response(
        self,
        value: dict[str, Any],
        *,
        schema_key: str,
        operation: str,
        request_sha256: str,
        actor: str,
        reason: str,
        issue_id: str,
        before_revision: str | None,
    ) -> dict[str, Any]:
        response = self._provider_exact_keys(
            value,
            {"schema_version", "ok", "operation", "receipt"},
            "provider mutation response",
        )
        receipt = self._validate_mutation_receipt(response["receipt"])
        if (
            response["schema_version"]
            != self.config["provider"]["response_schemas"][schema_key]
            or response["ok"] is not True
            or response["operation"] != operation
            or receipt["operation"] != operation
            or receipt["request_sha256"] != request_sha256
            or receipt["actor"] != actor
            or receipt["reason"] != reason
            or receipt["issue_id"] != issue_id
            or receipt["before_revision"] != before_revision
        ):
            _fail("invalid_provider_response", "provider mutation response is unbound")
        return response

    @staticmethod
    def _receipt_in_identity(
        identity: dict[str, Any],
        receipt: dict[str, Any],
        key: str,
    ) -> bool:
        return any(candidate == receipt for candidate in identity[key])

    def _validate_install_chain(
        self,
        identity: dict[str, Any],
        receipt: dict[str, Any],
    ) -> None:
        installs = identity["install_receipts"]
        cursors = [item["history_cursor"] for item in installs]
        if len(cursors) != len(set(cursors)):
            _fail(
                "invalid_provider_response",
                "install history cursors are not unique",
            )
        try:
            position = installs.index(receipt)
        except ValueError:
            _fail(
                "invalid_provider_response",
                "install receipt is absent from fresh identity history",
            )
        if position and installs[position - 1]["after_schema"] != receipt["before_schema"]:
            _fail(
                "invalid_provider_response",
                "install receipt is not schema-chain adjacent",
            )
        for previous, following in zip(installs, installs[1:]):
            if previous["after_schema"] != following["before_schema"]:
                _fail(
                    "invalid_provider_response",
                    "provider install schema history is discontinuous",
                )
        if installs[-1]["after_schema"] != identity["schema_fingerprint"]:
            _fail(
                "invalid_provider_response",
                "fresh identity schema is not the install-history head",
            )
        expected_profile_schema = {
            "core": identity["full_profile_identity"]["core_schema_fingerprint"],
            "full": identity["full_profile_identity"]["full_schema_fingerprint"],
        }.get(receipt["profile"])
        if (
            expected_profile_schema is not None
            and receipt["after_schema"] != expected_profile_schema
        ):
            _fail(
                "invalid_provider_response",
                f"{receipt['profile']} receipt has the wrong after_schema",
            )
        if identity["profiles"] != [
            item["profile"] for item in installs
        ]:
            _fail(
                "invalid_provider_response",
                "fresh identity profiles do not match install history",
            )

    def _install(self, bootstrap_id: str, profile: str) -> dict[str, Any]:
        kind = f"{bootstrap_id.lower()}_{profile}_install"
        prepared = self.journal.prepared(kind)
        if prepared is None:
            identity = self._authority_identity(
                f"{bootstrap_id} authority identity",
            )
            migration_id = _sha256(
                _canonical_json(
                    {
                        "intent": self.intent,
                        "repository": self.repository_identity,
                        "profile": profile,
                    }
                )
            )
            migration_host = _sha256(
                _canonical_json(
                    {
                        "machine": platform.node(),
                        "uid": os.geteuid(),
                        "state_root": str(self.deps.state_root.resolve()),
                    }
                )
            )
            install_argv = [
                "authority",
                "install",
                "--profile",
                profile,
                "--migration-id",
                migration_id,
                "--migration-host",
                migration_host,
                "--if-schema",
                str(identity.get("schema_fingerprint", "base")),
                "--actor",
                self.actor,
                "--json",
            ]
            install_request = {
                "profile": profile,
                "migration_id": migration_id,
                "migration_host": migration_host,
                "if_schema": identity["schema_fingerprint"],
                "actor": self.actor,
            }
            request = {
                "bootstrap_id": bootstrap_id,
                "profile": profile,
                "provider_path": str(self.provider),
                "provider_sha256": self._provider_sha256(),
                "before_schema": identity["schema_fingerprint"],
                "install_request": install_request,
                "install_request_sha256": _sha256(
                    _canonical_json(install_request)
                ),
                "install_argv": install_argv,
            }
        else:
            request = prepared
            install_argv = request["install_argv"]
        if (
            str(self.provider) != request["provider_path"]
            or self._provider_sha256() != request["provider_sha256"]
        ):
            _fail(
                "provider_stage_drift",
                f"{kind} provider path/digest changed",
            )

        def observe() -> dict[str, Any] | None:
            current = self._authority_identity(
                f"observe {profile} install",
            )
            matches = [
                receipt
                for receipt in current["install_receipts"]
                if receipt["request_sha256"]
                == request["install_request_sha256"]
                and receipt["actor"] == self.actor
                and receipt["profile"] == profile
                and receipt["migration_id"]
                == request["install_request"]["migration_id"]
                and receipt["migration_host"]
                == request["install_request"]["migration_host"]
                and receipt["before_schema"] == request["before_schema"]
            ]
            if not matches:
                return None
            if len(matches) != 1 or profile not in current["profiles"]:
                _fail(
                    "invalid_provider_response",
                    f"{profile} install receipt is duplicate or profile absent",
                )
            matched = matches[0]
            self._validate_install_chain(current, matched)
            if self.journal.committed(kind) is None and (
                current["schema_fingerprint"] != matched["after_schema"]
                or current["history_cursor"] != matched["history_cursor"]
            ):
                _fail(
                    "invalid_provider_response",
                    f"{profile} install receipt is not the fresh identity head",
                )
            response = {
                "schema_version": self.config["provider"]["response_schemas"][
                    "install"
                ],
                "ok": True,
                "operation": "install",
                "receipt": matched,
            }
            return {"provider_response": response}

        def action() -> dict[str, Any]:
            self._reverify_claim_before_authority_action(
                bootstrap_id,
                self.issue_ids[bootstrap_id],
            )
            value = self._provider_json(
                install_argv,
                f"install {profile}",
            )
            return self._validate_install_response(
                value,
                request_sha256=request["install_request_sha256"],
                actor=self.actor,
                profile=profile,
                migration_id=request["install_request"]["migration_id"],
                migration_host=request["install_request"]["migration_host"],
                before_schema=request["before_schema"],
            )

        return self._effect(
            kind,
            request,
            observe,
            action,
            reobserve_committed=True,
        )

    def _finalize_00a(self, run_id: str) -> dict[str, Any]:
        task = self.config["tasks"][0]
        kind = "00a_finalize"
        worker_actor = (
            f"agentic:bootstrap-build:{run_id}:"
            f"{self.worker_token}:00a"
        )
        prepared = self.journal.prepared(kind)
        if prepared is None:
            pre_issue = self._exact_issue(
                "00A",
                self.expected_issue,
                status="in_progress",
                assignee=worker_actor,
                finalized=False,
            )
            if pre_issue is None:
                _fail(
                    "bootstrap_finalize_prestate",
                    "00A does not have the exact fresh pre-finalize state",
                )
            before_revision = pre_issue.get("authority_revision")
            if not isinstance(before_revision, str) or not before_revision:
                _fail(
                    "authority_revision_missing",
                    "00A finalize requires a fresh authority revision",
                )
            request_body = {
                "schema_version": self.config["provider"]["request_schemas"][
                    "bootstrap_finalize"
                ],
                "repository_identity": self.repository_identity,
                "issue_id": self.expected_issue,
                "bootstrap_definition_hash": task["definition_hash"],
                "bootstrap_metadata_hash": _sha256(
                    _canonical_json(task["envelope"]["metadata"])
                ),
                "intent": self.intent,
                "run_id": run_id,
                "actor": self.actor,
                "reason": f"bootstrap-published:{self.current_head}",
                "expected": {
                    "status": "in_progress",
                    "assignee": worker_actor,
                    "external_ref": None,
                    "authority_revision": before_revision,
                },
                "after": {
                    "status": "closed",
                    "external_ref": task["envelope"]["canonical_external_ref"],
                    "container": task["envelope"]["container"],
                },
            }
            path = self._request_file("00a-finalize", request_body)
            request_body_sha256 = _sha256(_canonical_json(request_body))
            request = {
                "request": request_body,
                "request_sha256": request_body_sha256,
                "request_path": str(path),
                "provider_path": str(self.provider),
                "provider_sha256": self._provider_sha256(),
                "pre_state_sha256": _sha256(
                    _canonical_json(
                        {
                            "issue": pre_issue,
                            "history": self._history(self.expected_issue),
                        }
                    )
                ),
            }
        else:
            request = prepared
            request_body = request["request"]
            request_body_sha256 = request["request_sha256"]
            path = Path(request["request_path"])
            before_revision = request_body["expected"]["authority_revision"]
        if (
            str(self.provider) != request["provider_path"]
            or self._provider_sha256() != request["provider_sha256"]
        ):
            _fail("provider_stage_drift", "00A finalize provider changed")

        def observe() -> dict[str, Any] | None:
            issue = self._exact_issue(
                "00A",
                self.expected_issue,
                status="closed",
                assignee=worker_actor,
                finalized=True,
            )
            if issue is None:
                return None
            self._require_edges(
                issue,
                [(CONTAINER_ID, "related")],
                "00A finalize",
            )
            identity = self._authority_identity("observe 00A finalize")
            matches = [
                receipt
                for receipt in identity["mutation_receipts"]
                if receipt["request_sha256"] == request_body_sha256
                and receipt["operation"] == "bootstrap_finalize"
                and receipt["actor"] == self.actor
                and receipt["reason"] == request_body["reason"]
                and receipt["issue_id"] == self.expected_issue
            ]
            if not matches:
                return None
            if len(matches) != 1:
                _fail("invalid_provider_response", "duplicate 00A finalize receipt")
            receipt = matches[0]
            if (
                self.journal.committed(kind) is None
                and identity["history_cursor"] != receipt["history_cursor"]
            ):
                _fail(
                    "invalid_provider_response",
                    "00A finalize receipt is not the fresh provider history head",
                )
            if receipt["before_revision"] != before_revision:
                _fail(
                    "invalid_provider_response",
                    "00A finalize receipt has the wrong before_revision",
                )
            if issue.get("authority_revision") != receipt["after_revision"]:
                _fail(
                    "invalid_provider_response",
                    "00A finalize issue/provider revision differs",
                )
            history = self._require_history_event(
                self.expected_issue,
                action="bootstrap_finalize",
                actor=self.actor,
                reason=request_body["reason"],
                request_sha256=request_body_sha256,
                before_revision=before_revision,
                after_revision=receipt["after_revision"],
                history_cursor=receipt["history_cursor"],
            )
            response = {
                "schema_version": self.config["provider"]["response_schemas"][
                    "bootstrap_finalize"
                ],
                "ok": True,
                "operation": "bootstrap_finalize",
                "receipt": receipt,
            }
            return {
                "issue": self.expected_issue,
                "post": issue,
                "history": history,
                "provider_response": response,
            }

        def action() -> dict[str, Any]:
            self._reverify_claim_before_authority_action(
                "00A",
                self.expected_issue,
            )
            value = self._provider_json(
                [
                    "authority",
                    "bootstrap-finalize",
                    "--request",
                    str(path),
                    "--json",
                ],
                "finalize 00A",
            )
            return self._validate_mutation_response(
                value,
                schema_key="bootstrap_finalize",
                operation="bootstrap_finalize",
                request_sha256=request_body_sha256,
                actor=self.actor,
                reason=request_body["reason"],
                issue_id=self.expected_issue,
                before_revision=before_revision,
            )

        return self._effect(
            kind,
            request,
            observe,
            action,
            reobserve_committed=True,
        )

    def _all_issues(self) -> list[dict[str, Any]]:
        result = self._invoke(
            [str(self.deps.bd), "list", "--all", "--json"],
            operation="list all issues",
        )
        try:
            value = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            _fail("invalid_command_result", "bd list returned invalid JSON", details={"error": str(exc)})
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            _fail("invalid_command_result", "bd list did not return an issue list")
        return value

    def _find_external_ref(self, external_ref: str) -> dict[str, Any] | None:
        matches = [
            issue
            for issue in self._all_issues()
            if issue.get("external_ref") == external_ref
        ]
        if len(matches) > 1:
            _fail("external_ref_not_unique", f"multiple issues use {external_ref}")
        return matches[0] if matches else None

    def _guarded_create(self, bootstrap_id: str, dependency_id: str) -> dict[str, Any]:
        kind = f"{bootstrap_id.lower()}_create"
        task = next(
            item for item in self.config["tasks"] if item["bootstrap_id"] == bootstrap_id
        )
        envelope = task["envelope"]
        issue_id = (
            f"{self._issue_prefix(self.context)}-"
            f"{_sha256(_canonical_json({'identity': self.repository_identity, 'source': task['source']}))[:12]}"
        )
        request_body = {
            "schema_version": self.config["provider"]["request_schemas"][
                "guarded_create"
            ],
            "repository_identity": self.repository_identity,
            "intent": self.intent,
            "actor": self.actor,
            "reason": f"bootstrap-register:{bootstrap_id.lower()}",
            "issue_id": issue_id,
            "envelope": {
                **envelope,
                "external_ref": envelope["canonical_external_ref"],
            },
            "initial_edges": [
                {"type": "blocks", "depends_on": dependency_id},
                {
                    "type": envelope["container"]["relation"],
                    "depends_on": envelope["container"]["issue_id"],
                },
            ],
        }
        path = self._request_file(f"{bootstrap_id.lower()}-create", request_body)
        request_body_sha256 = _sha256(_canonical_json(request_body))
        request = {
            "request": request_body,
            "request_sha256": request_body_sha256,
            "request_path": str(path),
            "provider_path": str(self.provider),
            "provider_sha256": self._provider_sha256(),
        }
        if (
            str(self.provider) != request["provider_path"]
            or self._provider_sha256() != request["provider_sha256"]
        ):
            _fail("provider_stage_drift", f"{bootstrap_id} create provider changed")

        def observe() -> dict[str, Any] | None:
            existing = self._find_external_ref(envelope["canonical_external_ref"])
            if existing is None:
                return None
            if existing.get("id") != issue_id:
                _fail(
                    "bootstrap_ref_conflict",
                    f"{bootstrap_id} canonical ref belongs to a foreign issue",
                    details={"foreign_issue": existing.get("id")},
                )
            exact = self._exact_issue(
                bootstrap_id,
                issue_id,
                status=str(existing.get("status")),
                assignee=existing.get("assignee") or None,
                finalized=True,
            )
            if exact is None:
                _fail("bootstrap_ref_conflict", f"{bootstrap_id} envelope drift")
            self._require_edges(
                exact,
                [
                    (dependency_id, "blocks"),
                    (envelope["container"]["issue_id"], "related"),
                ],
                f"{bootstrap_id} guarded create",
            )
            identity = self._authority_identity(
                f"observe {bootstrap_id} guarded create"
            )
            matches = [
                receipt
                for receipt in identity["mutation_receipts"]
                if receipt["request_sha256"] == request_body_sha256
                and receipt["operation"] == "guarded_create"
                and receipt["actor"] == self.actor
                and receipt["reason"] == request_body["reason"]
                and receipt["issue_id"] == issue_id
            ]
            if not matches:
                return None
            if len(matches) != 1:
                _fail(
                    "invalid_provider_response",
                    f"duplicate {bootstrap_id} create receipt",
                )
            provider_receipt = matches[0]
            if (
                self.journal.committed(kind) is None
                and identity["history_cursor"]
                != provider_receipt["history_cursor"]
            ):
                _fail(
                    "invalid_provider_response",
                    f"{bootstrap_id} create receipt is not the fresh history head",
                )
            if provider_receipt["before_revision"] is not None:
                _fail(
                    "invalid_provider_response",
                    f"{bootstrap_id} create receipt has a pre-existing revision",
                )
            # The issue can legitimately have later claim/close revisions when a
            # committed create is re-observed.  At the immediate post-create
            # state, however, the issue and provider receipt must agree.
            if (
                exact.get("status") == "open"
                and exact.get("assignee") is None
                and exact.get("authority_revision")
                != provider_receipt["after_revision"]
            ):
                _fail(
                    "invalid_provider_response",
                    f"{bootstrap_id} create issue/provider revision differs",
                )
            history = self._require_history_event(
                issue_id,
                action="guarded_create",
                actor=self.actor,
                reason=request_body["reason"],
                request_sha256=request_body_sha256,
                before_revision=None,
                after_revision=provider_receipt["after_revision"],
                history_cursor=provider_receipt["history_cursor"],
            )
            response = {
                "schema_version": self.config["provider"]["response_schemas"][
                    "guarded_create"
                ],
                "ok": True,
                "operation": "guarded_create",
                "receipt": provider_receipt,
            }
            return {
                "issue": issue_id,
                "definition": self._issue_definition_projection(exact),
                "history": history,
                "provider_response": response,
            }

        def action() -> dict[str, Any]:
            value = self._provider_json(
                [
                    "authority",
                    "guarded-create",
                    "--request",
                    str(path),
                    "--json",
                ],
                f"create {bootstrap_id}",
            )
            return self._validate_mutation_response(
                value,
                schema_key="guarded_create",
                operation="guarded_create",
                request_sha256=request_body_sha256,
                actor=self.actor,
                reason=request_body["reason"],
                issue_id=issue_id,
                before_revision=None,
            )

        receipt = self._effect(
            kind,
            request,
            observe,
            action,
            reobserve_committed=True,
        )
        self.issue_ids[bootstrap_id] = receipt["issue"]
        return receipt

    def _conditional_close(
        self,
        bootstrap_id: str,
        issue_id: str,
        run_id: str,
    ) -> dict[str, Any]:
        kind = f"{bootstrap_id.lower()}_close"
        prepared = self.journal.prepared(kind)
        worker_actor = (
            f"agentic:bootstrap-build:{run_id}:"
            f"{self.worker_token}:{bootstrap_id.lower()}"
        )
        if prepared is None:
            issue = self._show(issue_id)
            if issue is None:
                _fail("missing_issue", f"{bootstrap_id} issue vanished before close")
            revision = issue.get("authority_revision")
            if not isinstance(revision, str) or not revision:
                _fail(
                    "authority_revision_missing",
                    f"{bootstrap_id} close requires provider authority revision",
                )
            request_body = {
                "schema_version": self.config["provider"]["request_schemas"][
                    "conditional_transaction"
                ],
                "repository_identity": self.repository_identity,
                "intent": self.intent,
                "actor": self.actor,
                "reason": f"bootstrap-published:{self.current_head}",
                "expected": [
                    {
                        "issue_id": issue_id,
                        "authority_revision": revision,
                        "status": "in_progress",
                        "assignee": worker_actor,
                    }
                ],
                "operations": [
                    {
                        "op": "close",
                        "issue_id": issue_id,
                        "status": "closed",
                    }
                ],
            }
            path = self._request_file(f"{bootstrap_id.lower()}-close", request_body)
            request_body_sha256 = _sha256(_canonical_json(request_body))
            request = {
                "request": request_body,
                "request_sha256": request_body_sha256,
                "request_path": str(path),
                "provider_path": str(self.provider),
                "provider_sha256": self._provider_sha256(),
                "pre_state_sha256": _sha256(
                    _canonical_json(
                        {
                            "issue": issue,
                            "history": self._history(issue_id),
                        }
                    )
                ),
            }
        else:
            request = prepared
            request_body = request["request"]
            request_body_sha256 = request["request_sha256"]
            revision = request_body["expected"][0]["authority_revision"]
            path = Path(request["request_path"])
        if (
            str(self.provider) != request["provider_path"]
            or self._provider_sha256() != request["provider_sha256"]
        ):
            _fail(
                "provider_stage_drift",
                f"{bootstrap_id} close provider changed",
            )

        def observe() -> dict[str, Any] | None:
            closed = self._exact_issue(
                bootstrap_id,
                issue_id,
                status="closed",
                assignee=worker_actor,
                finalized=True,
            )
            if closed is None:
                return None
            current_revision = closed.get("authority_revision")
            if current_revision == revision or not isinstance(current_revision, str):
                _fail("conditional_close_unproven", f"{bootstrap_id} revision did not advance")
            previous_id = {
                "00B": self.issue_ids["00A"],
                "00C": self.issue_ids["00B"],
                "00D": self.issue_ids["00C"],
            }[bootstrap_id]
            self._require_edges(
                closed,
                [(previous_id, "blocks"), (CONTAINER_ID, "related")],
                f"{bootstrap_id} conditional close",
            )
            identity = self._authority_identity(
                f"observe {bootstrap_id} conditional close"
            )
            matches = [
                receipt
                for receipt in identity["mutation_receipts"]
                if receipt["request_sha256"] == request_body_sha256
                and receipt["operation"] == "conditional_close"
                and receipt["actor"] == self.actor
                and receipt["reason"] == request_body["reason"]
                and receipt["issue_id"] == issue_id
            ]
            if not matches:
                return None
            if len(matches) != 1:
                _fail(
                    "invalid_provider_response",
                    f"duplicate {bootstrap_id} close receipt",
                )
            provider_receipt = matches[0]
            if (
                self.journal.committed(kind) is None
                and identity["history_cursor"]
                != provider_receipt["history_cursor"]
            ):
                _fail(
                    "conditional_close_unproven",
                    f"{bootstrap_id} receipt is not the fresh history head",
                )
            if provider_receipt["before_revision"] != revision:
                _fail(
                    "conditional_close_unproven",
                    f"{bootstrap_id} receipt has the wrong before_revision",
                )
            if provider_receipt["after_revision"] != current_revision:
                _fail(
                    "conditional_close_unproven",
                    f"{bootstrap_id} issue/provider revision differs",
                )
            history = self._require_history_event(
                issue_id,
                action="conditional_close",
                actor=self.actor,
                reason=request_body["reason"],
                request_sha256=request_body_sha256,
                before_revision=revision,
                after_revision=current_revision,
                history_cursor=provider_receipt["history_cursor"],
            )
            response = {
                "schema_version": self.config["provider"]["response_schemas"][
                    "conditional_transaction"
                ],
                "ok": True,
                "operation": "conditional_close",
                "receipt": provider_receipt,
            }
            return {
                "issue": issue_id,
                "before_revision": revision,
                "after_revision": current_revision,
                "post": closed,
                "history": history,
                "provider_response": response,
            }

        def action() -> dict[str, Any]:
            self._reverify_claim_before_authority_action(
                bootstrap_id,
                issue_id,
            )
            value = self._provider_json(
                [
                    "authority",
                    "transaction",
                    "--request",
                    str(path),
                    "--json",
                ],
                f"close {bootstrap_id}",
            )
            return self._validate_mutation_response(
                value,
                schema_key="conditional_transaction",
                operation="conditional_close",
                request_sha256=request_body_sha256,
                actor=self.actor,
                reason=request_body["reason"],
                issue_id=issue_id,
                before_revision=revision,
            )

        return self._effect(
            kind,
            request,
            observe,
            action,
            reobserve_committed=True,
        )

    def _run_task(self, bootstrap_id: str, issue_id: str) -> tuple[dict[str, Any], Path, str]:
        dispatch = self.intent
        published = self.journal.committed(f"{bootstrap_id.lower()}_publish")
        worker_receipt = self.journal.committed(f"{bootstrap_id.lower()}_worker")
        worktree_receipt = self.journal.committed(
            f"{bootstrap_id.lower()}_worktree"
        )
        if published is not None:
            claim = self.journal.committed(f"{bootstrap_id.lower()}_claim")
            if claim is None or worker_receipt is None or worktree_receipt is None:
                _fail(
                    "invalid_evidence",
                    f"{bootstrap_id} publication lacks claim/worker/worktree evidence",
                )
            self.current_head = published["after"]
            return (
                worker_receipt["result"],
                Path(worktree_receipt["path"]),
                claim["actor"],
            )
        claim = self._claim(bootstrap_id, issue_id, dispatch)
        prior_worktree = self.journal.prepared(
            f"{bootstrap_id.lower()}_worktree"
        )
        base = prior_worktree["base"] if prior_worktree else self.current_head
        worktree = self._worktree(bootstrap_id, base)
        # A committed claim is authority evidence, not a lease.  Re-observe it
        # immediately before each action that would spend or publish work.
        self._claim(bootstrap_id, issue_id, dispatch)
        worker = self._launch_role(
            bootstrap_id=bootstrap_id,
            issue_id=issue_id,
            run_id=dispatch,
            worktree=worktree,
            role="worker",
        )
        task = next(
            item
            for item in self.config["tasks"]
            if item["bootstrap_id"] == bootstrap_id
        )
        changed_raw = self._invoke(
            [
                "git",
                "diff",
                "--name-only",
                "-z",
                base,
                str(worker["commit"]),
                "--",
            ],
            cwd=worktree,
            operation=f"{bootstrap_id} Touch verification",
        ).stdout
        changed = {path for path in changed_raw.split("\0") if path}
        allowed = set(task["definition"]["touch"])
        if not changed or not changed.issubset(allowed):
            _fail(
                "touch_violation",
                f"{bootstrap_id} changed paths outside its immutable Touch set",
                details={
                    "changed": sorted(changed),
                    "allowed": sorted(allowed),
                    "outside": sorted(changed - allowed),
                },
            )
        self._accept(bootstrap_id, worktree)
        self._launch_role(
            bootstrap_id=bootstrap_id,
            issue_id=issue_id,
            run_id=dispatch,
            worktree=worktree,
            role="review",
        )
        commit = str(worker["commit"])
        if self._git(["rev-parse", "HEAD"], cwd=worktree).strip() != commit:
            _fail("reviewed_commit_moved", f"{bootstrap_id} changed during review")
        if self._git(
            [
                "status",
                "--porcelain=v2",
                "--untracked-files=all",
                "--ignored=matching",
            ],
            cwd=worktree,
        ):
            _fail("dirty_worker", f"{bootstrap_id} review left worktree dirt")
        self._claim(bootstrap_id, issue_id, dispatch)
        self._publish(bootstrap_id, commit, base)
        return worker, worktree, claim["actor"]

    def _cleanup_worktree(
        self,
        bootstrap_id: str,
        worktree: Path,
        commit: str,
    ) -> dict[str, Any]:
        request = {
            "bootstrap_id": bootstrap_id,
            "path": str(worktree),
            "commit": commit,
        }

        def observe() -> dict[str, Any] | None:
            listed = self._git(["worktree", "list", "--porcelain"])
            registered = any(
                line == f"worktree {worktree}"
                for line in listed.splitlines()
            )
            if not worktree.exists() and not registered:
                return {"removed": True, "path": str(worktree)}
            return None

        def action() -> None:
            if not worktree.exists():
                self._invoke(
                    ["git", "worktree", "prune"],
                    operation=f"prune {bootstrap_id} worktree registration",
                )
                return
            if (
                self._git(["rev-parse", "HEAD"], cwd=worktree).strip() != commit
                or self._git(
                    [
                        "status",
                        "--porcelain=v2",
                        "--untracked-files=all",
                        "--ignored=matching",
                    ],
                    cwd=worktree,
                )
            ):
                _fail(
                    "worktree_cleanup_unsafe",
                    f"{bootstrap_id} worktree is not the exact clean worker commit",
                )
            self._invoke(
                ["git", "worktree", "remove", str(worktree)],
                operation=f"remove {bootstrap_id} worktree",
            )
            self._invoke(
                ["git", "worktree", "prune"],
                operation=f"prune {bootstrap_id} worktrees",
            )

        return self._effect(
            f"{bootstrap_id.lower()}_worktree_cleanup",
            request,
            observe,
            action,
        )

    def run(self) -> dict[str, Any]:
        intent_request = {
            "intent": self.intent,
            "issue": self.expected_issue,
            "runtime": self.args.runtime,
            "repository_identity": self.repository_identity,
            "source_commit": self.attestation["source_commit"],
            "attestation_commit": self.launch_commit,
            "config_sha256": _sha256(self.config_raw),
            "bd_path": str(self.deps.bd),
            "bd_sha256": _sha256(self.deps.bd.read_bytes()),
            "runtime_path": str(self.deps.runtime),
            "runtime_sha256": _sha256(self.deps.runtime.read_bytes()),
            "tasks": [
                {
                    "bootstrap_id": task["bootstrap_id"],
                    "source": task["source"],
                    "task_sha256": task["task_sha256"],
                    "definition_hash": task["definition_hash"],
                }
                for task in self.config["tasks"]
            ],
        }
        intent_sha256 = _sha256(_canonical_json(intent_request))
        prepared_intent = self.journal.prepared("intent")
        committed_intent = self.journal.committed("intent")
        if prepared_intent not in (None, intent_request):
            _fail("intent_drift", "current complete bootstrap intent differs")
        if prepared_intent is None:
            if committed_intent is not None:
                _fail("invalid_evidence", "committed intent lacks prepared event")
            self.journal.append("intent", "prepared", intent_request)
        if committed_intent is None:
            self.journal.append(
                "intent",
                "committed",
                {
                    "intent_sha256": intent_sha256,
                    "bd_path": intent_request["bd_path"],
                    "bd_sha256": intent_request["bd_sha256"],
                    "runtime_path": intent_request["runtime_path"],
                    "runtime_sha256": intent_request["runtime_sha256"],
                },
            )
        else:
            _exact_keys(
                committed_intent,
                {
                    "intent_sha256",
                    "bd_path",
                    "bd_sha256",
                    "runtime_path",
                    "runtime_sha256",
                },
                "committed bootstrap intent",
            )
            if committed_intent != {
                "intent_sha256": intent_sha256,
                "bd_path": intent_request["bd_path"],
                "bd_sha256": intent_request["bd_sha256"],
                "runtime_path": intent_request["runtime_path"],
                "runtime_sha256": intent_request["runtime_sha256"],
            }:
                _fail(
                    "intent_drift",
                    "current intent or bd/runtime path/digest differs",
                )

        self._create_00a()
        worker_a, worktree_a, _ = self._run_task("00A", self.expected_issue)
        self.provider = self._provider_from_result(worker_a, worktree_a)
        self._install("00A", "core")
        self._finalize_00a(self.intent)
        self._cleanup_worktree(
            "00A",
            worktree_a,
            str(worker_a["commit"]),
        )

        previous = self.expected_issue
        for bootstrap_id in ("00B", "00C", "00D"):
            created = self._guarded_create(bootstrap_id, previous)
            previous = created["issue"]

        for bootstrap_id in ("00B", "00C", "00D"):
            issue_id = self.issue_ids[bootstrap_id]
            worker, worktree, _ = self._run_task(bootstrap_id, issue_id)
            if bootstrap_id in {"00B", "00C"}:
                self.provider = self._provider_from_result(worker, worktree)
                self._install(
                    bootstrap_id,
                    "conditional" if bootstrap_id == "00B" else "full",
                )
            self._conditional_close(bootstrap_id, issue_id, self.intent)
            self._cleanup_worktree(
                bootstrap_id,
                worktree,
                str(worker["commit"]),
            )

        terminal_snapshot = self._capture_stable_terminal_snapshot()
        terminal_states = terminal_snapshot["issues"]
        final_provider_identity = terminal_snapshot["authority"]
        terminal_request = {
            "intent": self.intent,
            "head": self.current_head,
            "issues": self.issue_ids,
            "issue_state_sha256": {
                bootstrap_id: _sha256(_canonical_json(issue))
                for bootstrap_id, issue in terminal_states.items()
            },
            "provider_identity": final_provider_identity,
            "terminal_snapshot_sha256": _sha256(
                _canonical_json(terminal_snapshot)
            ),
            "provider_path": str(self.provider),
            "provider_sha256": self._provider_sha256(),
        }
        terminal = self.journal.committed("terminal")
        if terminal is None:
            if self.journal.prepared("terminal") not in (None, terminal_request):
                _fail("prepared_request_mismatch", "terminal request changed")
            if self.journal.prepared("terminal") is None:
                self.journal.append("terminal", "prepared", terminal_request)
            terminal = {
                "request_sha256": _sha256(_canonical_json(terminal_request)),
                "issues": self.issue_ids,
                "published_head": self.current_head,
            }
            self.journal.append("terminal", "committed", terminal)
            self.deps.crash("terminal:after_commit")
        elif terminal.get("request_sha256") != _sha256(
            _canonical_json(terminal_request)
        ):
            _fail(
                "terminal_poststate_mismatch",
                "terminal tracker/provider/source state drifted after receipt",
            )
        post_terminal_snapshot = self._capture_stable_terminal_snapshot()
        if post_terminal_snapshot != terminal_snapshot:
            _fail(
                "terminal_snapshot_drift",
                "terminal state changed between proof and terminal commit",
            )
        terminal_event_digest, terminal_event = self.journal.event_record(
            "terminal",
            "committed",
        )
        receipt_value = {
            "schema": "agentic.registration-bootstrap-terminal-receipt/v1",
            "source_commit": self.attestation["source_commit"],
            "attestation_commit": self.launch_commit,
            "intent": {
                "id": self.intent,
                "sha256": intent_sha256,
            },
            "issues": {
                bootstrap_id: self.issue_ids[bootstrap_id]
                for bootstrap_id in ("00A", "00B", "00C", "00D")
            },
            "published_head": self.current_head,
            "event_chain": {
                "head": terminal_event_digest,
                "previous": terminal_event["previous"],
            },
            "provider": {
                "path": str(self.provider),
                "sha256": self._provider_sha256(),
                "full_profile_identity": final_provider_identity[
                    "full_profile_identity"
                ],
            },
        }
        receipt_sha256 = _sha256(_canonical_json(receipt_value))
        receipt_path = self.root / "receipts" / f"{receipt_sha256}.json"
        receipt_request = {
            "receipt_path": str(receipt_path),
            "receipt_sha256": receipt_sha256,
            "terminal_event": terminal_event_digest,
        }

        def observe_terminal_receipt() -> dict[str, Any] | None:
            if not _secure_exists(receipt_path):
                return None
            if self._capture_stable_terminal_snapshot() != terminal_snapshot:
                _fail(
                    "terminal_snapshot_drift",
                    "terminal state changed before receipt observation",
                )
            value = _read_json_file(receipt_path, "terminal bootstrap receipt")
            if value != receipt_value:
                _fail(
                    "terminal_receipt_drift",
                    "terminal receipt bytes do not match terminal state",
                )
            return {
                "receipt_path": str(receipt_path),
                "receipt_sha256": receipt_sha256,
            }

        def write_terminal_receipt() -> dict[str, Any]:
            self.deps.crash("terminal_receipt:before_revalidation")
            if self._capture_stable_terminal_snapshot() != terminal_snapshot:
                _fail(
                    "terminal_snapshot_drift",
                    "terminal state changed before immutable receipt creation",
                )
            _write_atomic(
                receipt_path,
                receipt_value,
                immutable=True,
                temp_owner=self.journal.process_owner,
            )
            return {
                "receipt_path": str(receipt_path),
                "receipt_sha256": receipt_sha256,
            }

        terminal_receipt = self._effect(
            "terminal_receipt",
            receipt_request,
            observe_terminal_receipt,
            write_terminal_receipt,
            reobserve_committed=True,
        )
        return {
            "schema_version": RESULT_SCHEMA,
            "ok": True,
            "operation": "run-00a",
            "intent": self.intent,
            "issues": self.issue_ids,
            "published_head": self.current_head,
            "event_head": self.journal._head()[1],
            "terminal": terminal,
            "receipt_path": terminal_receipt["receipt_path"],
            "receipt_sha256": terminal_receipt["receipt_sha256"],
        }


def run_00a(
    args: argparse.Namespace,
    dependencies: ControllerDependencies | None = None,
) -> dict[str, Any]:
    """Run or resume the complete attended Bootstrap 00A--00D lifecycle."""
    if not args.confirmed:
        _fail("confirmation_required", "run-00a requires explicit --confirmed")
    if _ISSUE_ID.fullmatch(args.issue) is None:
        _fail("invalid_issue_id", "issue must end in 12 lowercase hex characters")
    task_path, _ = _regular_contained_file(args.task)
    if task_path != (REPO_ROOT / TASKS[0][1]).resolve(strict=True):
        _fail("unexpected_task", "run-00a accepts only the checked-in 00A task")
    deps = dependencies or _default_dependencies(args.runtime)
    _ensure_secure_state_root(deps.state_root)
    state_lock = deps.state_root / "locks" / "bootstrap-registration-state.lock"
    with _FileLock(state_lock):
        controller = BootstrapController(args, deps)
        repo_lock = (
            deps.state_root
            / "locks"
            / f"repository-{_sha256(_canonical_json(controller.repository_identity))}.lock"
        )
        with _FileLock(repo_lock):
            return controller.run()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate or resume the attended Mardi Gras authority bootstrap.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate",
        help="validate the closed bootstrap definition without tracker access",
    )
    validate.add_argument("--config", required=True)

    run = subparsers.add_parser(
        "run-00a",
        help="run/resume the source-attested serial 00A through 00D lifecycle",
    )
    run.add_argument("--intent", required=True)
    run.add_argument("--issue", required=True)
    run.add_argument("--task", required=True)
    run.add_argument("--runtime", required=True, choices=("claude", "codex"))
    run.add_argument(
        "--reviewed-commit",
        required=True,
        help="the independently reviewed attestation-child commit",
    )
    run.add_argument("--config", default=str(CONFIG_PATH))
    run.add_argument("--confirmed", action="store_true")
    return parser


def _emit(value: dict[str, Any], *, stream: Any = sys.stdout) -> None:
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        file=stream,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if args.command == "validate":
            result = validate_config(args.config)
        elif args.command == "run-00a":
            result = run_00a(args)
        else:  # argparse makes this unreachable.
            _fail("invalid_command", f"unsupported command: {args.command}")
        _emit(result)
        return 0
    except BootstrapControlError as exc:
        _emit(
            {
                "schema_version": RESULT_SCHEMA,
                "ok": False,
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            stream=sys.stderr,
        )
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
