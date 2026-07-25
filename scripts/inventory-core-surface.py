#!/usr/bin/env python3
"""Validate the frozen toolkit surface and its additive classifications."""

from __future__ import annotations

import argparse
import ast
import dataclasses
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from typing import Any, Iterable


SCHEMA_VERSION = 2
GIT_BLOB_PIN = 1
DISPOSITIONS = {
    "retain",
    "repair",
    "hide-stub",
    "retire-dead",
    "measure-before-decision",
}
HASH_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclasses.dataclass(frozen=True)
class LiveSurface:
    identity: str
    surface_type: str
    path: str
    content_sha256: str


def file_sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def repo_path(root: pathlib.Path, path: pathlib.Path) -> str:
    return path.relative_to(root).as_posix()


def file_surface(
    root: pathlib.Path,
    identity: str,
    surface_type: str,
    path: pathlib.Path,
) -> LiveSurface:
    return LiveSurface(
        identity=identity,
        surface_type=surface_type,
        path=repo_path(root, path),
        content_sha256=file_sha256(path),
    )


def iter_files(directory: pathlib.Path, pattern: str) -> Iterable[pathlib.Path]:
    if not directory.is_dir():
        return ()
    return sorted(path for path in directory.glob(pattern) if path.is_file())


def references_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(candidate, ast.Name) and candidate.id == name
        for candidate in ast.walk(node)
    )


def parser_registration(call: ast.Call) -> bool:
    return isinstance(call.func, ast.Attribute) and call.func.attr == "add_parser"


def statement_parser_call(statement: ast.stmt) -> ast.Call | None:
    for candidate in ast.walk(statement):
        if isinstance(candidate, ast.Call) and parser_registration(candidate):
            return candidate
    return None


def cli_command_hashes(path: pathlib.Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    tree = ast.parse(path.read_text(), filename=str(path))
    string_groups: dict[str, list[str]] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        if not isinstance(value, (ast.Tuple, ast.List, ast.Set)):
            continue
        strings = [
            element.value
            for element in value.elts
            if isinstance(element, ast.Constant)
            and isinstance(element.value, str)
        ]
        if len(strings) != len(value.elts):
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                string_groups[target.id] = strings

    registrations: dict[str, list[str]] = {}
    for function in (
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ):
        for statement in function.body:
            call = statement_parser_call(statement)
            if call is None or not call.args:
                continue
            argument = call.args[0]
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                binding = None
                if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                    targets = (
                        statement.targets
                        if isinstance(statement, ast.Assign)
                        else [statement.target]
                    )
                    if len(targets) == 1 and isinstance(targets[0], ast.Name):
                        binding = targets[0].id
                statements = [statement]
                if binding is not None:
                    statements.extend(
                        candidate
                        for candidate in function.body
                        if candidate is not statement
                        and statement_parser_call(candidate) is None
                        and references_name(candidate, binding)
                    )
                registrations[argument.value] = [
                    ast.dump(candidate, include_attributes=False)
                    for candidate in statements
                ]
                continue
            if not isinstance(statement, ast.For):
                continue
            if not isinstance(statement.target, ast.Name):
                continue
            if not isinstance(statement.iter, ast.Name):
                continue
            if not isinstance(argument, ast.Name):
                continue
            if argument.id != statement.target.id:
                continue
            template = [
                ast.dump(candidate, include_attributes=False)
                for candidate in statement.body
            ]
            for command in string_groups.get(statement.iter.id, []):
                registrations[command] = template

    return {
        command: canonical_sha256(
            {"command": command, "registration_ast": registration}
        )
        for command, registration in sorted(registrations.items())
    }


def discover_surfaces(root: pathlib.Path) -> tuple[dict[str, LiveSurface], list[str]]:
    discovered: list[LiveSurface] = []
    diagnostics: list[str] = []

    for path in iter_files(root / ".claude/skills", "*/SKILL.md"):
        discovered.append(
            file_surface(root, f"skill:{path.parent.name}", "skill", path)
        )
    for surface_type, directory in (
        ("agent", root / ".claude/agents"),
        ("rule", root / ".claude/rules"),
    ):
        for path in iter_files(directory, "*.md"):
            discovered.append(
                file_surface(
                    root,
                    f"{surface_type}:{path.stem}",
                    surface_type,
                    path,
                )
            )
    hooks = root / "hooks"
    if hooks.is_dir():
        for directory in sorted(path for path in hooks.iterdir() if path.is_dir()):
            implementations = sorted(
                path
                for path in directory.iterdir()
                if path.is_file()
                and path.name != "README.md"
                and path.name != "test.sh"
            )
            if len(implementations) != 1:
                diagnostics.append(
                    f"hook {directory.name!r} has {len(implementations)} "
                    "implementation files; expected exactly one"
                )
                continue
            discovered.append(
                file_surface(
                    root,
                    f"hook:{directory.name}",
                    "hook",
                    implementations[0],
                )
            )
    for path in iter_files(root / ".claude/workflows", "*.js"):
        discovered.append(
            file_surface(root, f"workflow:{path.stem}", "workflow", path)
        )
    for path in iter_files(root / "runtimes", "*.md"):
        if path.name == "README.md":
            continue
        discovered.append(
            file_surface(root, f"runtime:{path.stem}", "runtime", path)
        )
    cli_path = root / "agentic/cli.py"
    if cli_path.is_file():
        for command, content_sha256 in cli_command_hashes(cli_path).items():
            discovered.append(
                LiveSurface(
                    identity=f"cli-command:{command}",
                    surface_type="cli-command",
                    path=repo_path(root, cli_path),
                    content_sha256=content_sha256,
                )
            )
    tests = root / "tests"
    if tests.is_dir():
        for path in sorted(tests.glob("test_*")):
            if path.is_file() and path.suffix in {".py", ".sh"}:
                relative = repo_path(root, path)
                discovered.append(
                    file_surface(root, f"test:{relative}", "test", path)
                )

    by_identity: dict[str, LiveSurface] = {}
    for surface in discovered:
        prior = by_identity.get(surface.identity)
        if prior is not None:
            diagnostics.append(
                f"discovery produced duplicate surface identity {surface.identity!r}"
            )
        else:
            by_identity[surface.identity] = surface
    return by_identity, diagnostics


def valid_repo_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = pathlib.PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and value == path.as_posix()


def validate_surface(
    value: Any,
    source: pathlib.Path,
    position: int,
) -> list[str]:
    prefix = f"{source}: surfaces[{position}]"
    diagnostics: list[str] = []
    if not isinstance(value, dict):
        return [f"{prefix} must be an object"]
    required = {
        "behavioral_tests",
        "content_sha256",
        "dependents",
        "disposition",
        "identity",
        "path",
        "rationale",
        "replacement",
        "surface_type",
    }
    missing = sorted(required - value.keys())
    unknown = sorted(value.keys() - required)
    if missing:
        diagnostics.append(f"{prefix} missing fields: {', '.join(missing)}")
    if unknown:
        diagnostics.append(f"{prefix} unknown fields: {', '.join(unknown)}")
    identity = value.get("identity")
    if not isinstance(identity, str) or not identity.strip():
        diagnostics.append(f"{prefix}.identity must be a non-empty string")
    surface_type = value.get("surface_type")
    if not isinstance(surface_type, str) or not surface_type.strip():
        diagnostics.append(f"{prefix}.surface_type must be a non-empty string")
    if not valid_repo_relative_path(value.get("path")):
        diagnostics.append(f"{prefix}.path must be a normalized repo-relative path")
    if not HASH_RE.fullmatch(str(value.get("content_sha256", ""))):
        diagnostics.append(f"{prefix}.content_sha256 must be lowercase SHA-256")
    disposition = value.get("disposition")
    if disposition not in DISPOSITIONS:
        diagnostics.append(
            f"{prefix}.disposition must be one of {', '.join(sorted(DISPOSITIONS))}"
        )
    rationale = value.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        diagnostics.append(f"{prefix}.rationale must be a non-empty string")
    replacement = value.get("replacement")
    if replacement is not None and (
        not isinstance(replacement, str) or not replacement.strip()
    ):
        diagnostics.append(f"{prefix}.replacement must be null or a non-empty string")
    for field in ("behavioral_tests", "dependents"):
        entries = value.get(field)
        if not isinstance(entries, list) or any(
            not isinstance(entry, str) or not entry.strip() for entry in entries
        ):
            diagnostics.append(f"{prefix}.{field} must be an array of non-empty strings")
        elif len(entries) != len(set(entries)):
            diagnostics.append(f"{prefix}.{field} contains duplicate values")
    if disposition in {"retain", "repair"} and not value.get("behavioral_tests"):
        diagnostics.append(
            f"{prefix} disposition {disposition!r} requires behavioral test evidence"
        )
    return diagnostics


def load_manifest(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"{path}: cannot read valid JSON: {exc}"]
    if not isinstance(value, dict):
        return None, [f"{path}: manifest must be an object"]
    diagnostics: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION:
        diagnostics.append(f"{path}: schema_version must be {SCHEMA_VERSION}")
    if value.get("git_blob_pin") != GIT_BLOB_PIN:
        diagnostics.append(f"{path}: git_blob_pin must be {GIT_BLOB_PIN}")
    if not isinstance(value.get("$schema"), str):
        diagnostics.append(f"{path}: $schema must be a string")
    manifest_type = value.get("manifest_type")
    if manifest_type not in {"baseline", "fragment"}:
        diagnostics.append(f"{path}: manifest_type must be baseline or fragment")
    surfaces = value.get("surfaces")
    if not isinstance(surfaces, list):
        diagnostics.append(f"{path}: surfaces must be an array")
        surfaces = []
    for position, surface in enumerate(surfaces):
        diagnostics.extend(validate_surface(surface, path, position))
    allowed = {
        "$schema",
        "frozen_sha256",
        "git_blob_pin",
        "manifest_type",
        "schema_version",
        "surfaces",
    }
    frozen = value.get("frozen_sha256")
    if not HASH_RE.fullmatch(str(frozen or "")):
        diagnostics.append(f"{path}: frozen_sha256 must be lowercase SHA-256")
    else:
        payload = {key: item for key, item in value.items() if key != "frozen_sha256"}
        actual = canonical_sha256(payload)
        if frozen != actual:
            diagnostics.append(
                f"{path}: frozen_sha256 mismatch; manifest metadata was altered"
            )
    if manifest_type == "fragment":
        allowed.add("fragment")
        fragment = value.get("fragment")
        if not isinstance(fragment, str) or not fragment.strip():
            diagnostics.append(f"{path}: fragment must be a non-empty string")
        elif fragment != path.stem:
            diagnostics.append(
                f"{path}: fragment {fragment!r} must match filename stem {path.stem!r}"
            )
    unknown = sorted(value.keys() - allowed)
    if unknown:
        diagnostics.append(f"{path}: unknown fields: {', '.join(unknown)}")
    return value, diagnostics


def git_bytes(root: pathlib.Path, arguments: list[str]) -> bytes | None:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def repository_uses_git(root: pathlib.Path) -> bool:
    top = git_bytes(root, ["rev-parse", "--show-toplevel"])
    head = git_bytes(root, ["rev-parse", "--verify", "HEAD"])
    if top is None or head is None:
        return False
    try:
        return pathlib.Path(top.decode().strip()).resolve() == root.resolve()
    except UnicodeDecodeError:
        return False


def repository_is_shallow(root: pathlib.Path) -> bool:
    value = git_bytes(root, ["rev-parse", "--is-shallow-repository"])
    return value is not None and value.decode().strip() == "true"


def manifest_has_committed_history(root: pathlib.Path, path: pathlib.Path) -> bool:
    relative = repo_path(root, path)
    history = git_bytes(root, ["log", "-1", "--format=%H", "--", relative])
    return history is not None and bool(history.strip())


def first_versioned_git_blob(
    root: pathlib.Path,
    path: pathlib.Path,
) -> tuple[str, bytes] | None:
    relative = repo_path(root, path)
    added = git_bytes(
        root,
        ["log", "--format=%H", "--diff-filter=A", "--", relative],
    )
    history = git_bytes(root, ["log", "--format=%H", "--", relative])
    if added is None or history is None:
        return None
    commits = list(reversed(added.decode().splitlines()))
    commits.extend(
        commit
        for commit in reversed(history.decode().splitlines())
        if commit not in commits
    )
    for commit in commits:
        blob = git_bytes(root, ["show", f"{commit}:{relative}"])
        if blob is None:
            continue
        try:
            manifest = json.loads(blob)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if (
            isinstance(manifest, dict)
            and manifest.get("schema_version") == SCHEMA_VERSION
            and manifest.get("git_blob_pin") == GIT_BLOB_PIN
        ):
            return commit, blob
    return None


def historical_fragment_paths(
    root: pathlib.Path,
    fragment_dir: pathlib.Path,
) -> set[pathlib.Path]:
    relative = repo_path(root, fragment_dir)
    output = git_bytes(
        root,
        [
            "log",
            "--format=",
            "--name-only",
            "--diff-filter=A",
            "HEAD",
            "--",
            f":(glob){relative}/*.json",
        ],
    )
    if output is None:
        return set()
    return {
        root / line
        for line in output.decode().splitlines()
        if line.strip().endswith(".json")
    }


def git_manifest_diagnostics(
    root: pathlib.Path,
    path: pathlib.Path,
) -> list[str]:
    if not manifest_has_committed_history(root, path):
        return []
    if repository_is_shallow(root):
        return [
            f"{path}: shallow Git history cannot establish manifest trust; "
            "deepen Git history before validating"
        ]
    first = first_versioned_git_blob(root, path)
    if first is None:
        head_blob = git_bytes(root, ["show", f"HEAD:{repo_path(root, path)}"])
        if head_blob is not None:
            try:
                head_manifest = json.loads(head_blob)
            except (UnicodeDecodeError, json.JSONDecodeError):
                head_manifest = None
            if (
                isinstance(head_manifest, dict)
                and head_manifest.get("git_blob_pin") != GIT_BLOB_PIN
            ):
                return []
        return [
            f"{path}: cannot resolve first schema-v{SCHEMA_VERSION} Git blob; "
            "deepen Git history before validating"
        ]
    commit, blob = first
    if path.read_bytes() == blob:
        return []
    return [
        f"{path}: manifest differs from first Git blob "
        f"{commit[:12]}:{repo_path(root, path)}"
    ]


def parse_evidence_pointer(pointer: str) -> tuple[str, str, str] | None:
    if "::" in pointer:
        path, anchor = pointer.split("::", 1)
        return path, "pytest", anchor
    if "#" in pointer:
        path, anchor = pointer.split("#", 1)
        return path, "shell", anchor
    return None


def named_python_test_body(source: str, anchor: str) -> str | None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == anchor
        and node.name.startswith("test_")
    ]
    if len(matches) != 1:
        return None
    statements = [
        statement
        for statement in matches[0].body
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
        )
    ]
    return "\n".join(ast.unparse(statement) for statement in statements)


def expand_shell_variables(statement: str, variables: dict[str, str]) -> str:
    pattern = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")
    expanded = statement
    for _ in range(len(variables) + 1):
        updated = pattern.sub(
            lambda match: variables.get(
                match.group(1) or match.group(2),
                match.group(0),
            ),
            expanded,
        )
        if updated == expanded:
            break
        expanded = updated
    return expanded


def joined_shell_statements(source: str) -> list[str]:
    statements: list[str] = []
    pending = ""
    for raw in source.splitlines():
        stripped = raw.strip()
        if not pending and (not stripped or stripped.startswith("#")):
            continue
        continued = raw.rstrip().endswith("\\")
        part = raw.rstrip()
        if continued:
            part = part[:-1]
        pending = f"{pending} {part.strip()}".strip()
        if continued:
            continue
        if pending:
            statements.append(" ".join(pending.split()))
        pending = ""
    if pending:
        statements.append(" ".join(pending.split()))
    return statements


def simple_shell_assignment(statement: str) -> tuple[str, str] | None:
    match = re.fullmatch(
        r"(?:local\s+)?([A-Za-z_][A-Za-z0-9_]*)=(\"[^\"]*\"|'[^']*'|[^\s]+)",
        statement,
    )
    if match is None:
        return None
    value = match.group(2)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return match.group(1), value


def executable_shell_assertion(statement: str) -> bool:
    if re.match(r"^(?:assert(?:_[A-Za-z0-9_]+)?|refute)\s+", statement):
        return not re.search(r"\s(?:true|:)\s*$", statement)
    if re.match(r"^(?:test\s|\[\s|\[\[\s|grep\s|rg\s)", statement):
        return True
    return "||" in statement and not statement.lstrip().startswith("#")


def shell_assertion_reference(statement: str) -> str:
    return re.sub(
        r"^((?:assert(?:_[A-Za-z0-9_]+)?|refute)\s+)"
        r"(?:\"[^\"]*\"|'[^']*')\s+",
        r"\1",
        statement,
        count=1,
    )


def shell_assertions(source: str) -> dict[str, list[str]]:
    variables: dict[str, str] = {}
    assertions: dict[str, list[str]] = {}
    for statement in joined_shell_statements(source):
        assignment = simple_shell_assignment(statement)
        if assignment is not None:
            name, value = assignment
            variables[name] = expand_shell_variables(value, variables)
            continue
        expanded = expand_shell_variables(statement, variables)
        if not executable_shell_assertion(expanded):
            continue
        normalized = " ".join(expanded.split())
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        assertions.setdefault(digest, []).append(
            shell_assertion_reference(normalized)
        )
    return assertions


def evidence_references_surface(
    source: str,
    identity: str,
    surface: dict[str, Any],
) -> bool:
    if surface.get("surface_type") == "test":
        return True
    path = surface.get("path")
    if isinstance(path, str) and path in source:
        return True
    if identity in source:
        return True
    if surface.get("surface_type") == "cli-command":
        command = identity.split(":", 1)[1]
        return re.search(
            rf"(?:[\"']{re.escape(command)}[\"']"
            rf"|(?:^|\s){re.escape(command)}(?:\s|$))",
            source,
        ) is not None
    return False


def evidence_diagnostics(
    root: pathlib.Path,
    source_manifest: pathlib.Path,
    identity: str,
    surface: dict[str, Any],
    pointer: str,
    classified: dict[str, tuple[pathlib.Path, dict[str, Any]]],
) -> list[str]:
    parsed = parse_evidence_pointer(pointer)
    if parsed is None:
        return [
            f"{source_manifest}: behavioral test for {identity!r} must name "
            f"a test case or assertion: {pointer!r}"
        ]
    test_path, anchor_type, anchor = parsed
    if not valid_repo_relative_path(test_path) or not (root / test_path).is_file():
        return [
            f"{source_manifest}: behavioral test missing for "
            f"{identity!r}: {pointer!r}"
        ]
    if f"test:{test_path}" not in classified:
        return [
            f"{source_manifest}: behavioral test is unclassified for "
            f"{identity!r}: {pointer!r}"
        ]
    source = (root / test_path).read_text(errors="replace")
    scoped_source = source
    if anchor_type == "pytest":
        if pathlib.PurePosixPath(test_path).suffix != ".py":
            return [
                f"{source_manifest}: pytest evidence must point to a Python "
                f"test for {identity!r}: {pointer!r}"
            ]
        scoped_source = named_python_test_body(source, anchor) or ""
        if not scoped_source:
            return [
                f"{source_manifest}: named pytest case missing for "
                f"{identity!r}: {pointer!r}"
            ]
    else:
        match = re.fullmatch(r"assert:([0-9a-f]{64})", anchor)
        if pathlib.PurePosixPath(test_path).suffix != ".sh" or match is None:
            return [
                f"{source_manifest}: shell evidence must name an exact "
                f"assertion hash "
                f"for {identity!r}: {pointer!r}"
            ]
        matches = shell_assertions(source).get(match.group(1), [])
        if len(matches) != 1:
            return [
                f"{source_manifest}: named shell assertion missing or not unique "
                f"for {identity!r}: {pointer!r}"
            ]
        scoped_source = matches[0]
    if not evidence_references_surface(scoped_source, identity, surface):
        return [
            f"{source_manifest}: behavioral test {pointer!r} does not "
            f"reference surface {identity!r} at {surface.get('path')!r}"
        ]
    return []


def check_inventory(root: pathlib.Path, baseline_path: pathlib.Path) -> list[str]:
    diagnostics: list[str] = []
    uses_git = repository_uses_git(root)
    baseline, errors = load_manifest(baseline_path)
    diagnostics.extend(errors)
    if baseline is None:
        return diagnostics
    if baseline.get("manifest_type") != "baseline":
        diagnostics.append(f"{baseline_path}: checked manifest must be a baseline")
    if uses_git:
        diagnostics.extend(git_manifest_diagnostics(root, baseline_path))

    fragment_dir = baseline_path.parent / "surface-inventory"
    if uses_git:
        for historical_path in sorted(historical_fragment_paths(root, fragment_dir)):
            if historical_path.is_file():
                continue
            first = first_versioned_git_blob(root, historical_path)
            if first is not None:
                diagnostics.append(
                    f"historical fragment missing: "
                    f"{repo_path(root, historical_path)}"
                )
            elif manifest_has_committed_history(root, historical_path):
                diagnostics.append(
                    f"{historical_path}: cannot resolve first "
                    f"schema-v{SCHEMA_VERSION} Git blob; "
                    "deepen Git history before validating"
                )
    manifests: list[tuple[pathlib.Path, dict[str, Any]]] = [(baseline_path, baseline)]
    for path in iter_files(fragment_dir, "*.json"):
        fragment, errors = load_manifest(path)
        diagnostics.extend(errors)
        if uses_git:
            diagnostics.extend(git_manifest_diagnostics(root, path))
        if fragment is not None:
            if fragment.get("manifest_type") != "fragment":
                diagnostics.append(f"{path}: additive manifest must be a fragment")
            manifests.append((path, fragment))

    classified: dict[str, tuple[pathlib.Path, dict[str, Any]]] = {}
    fragments: dict[str, pathlib.Path] = {}
    for source, manifest in manifests:
        fragment = manifest.get("fragment")
        if isinstance(fragment, str):
            prior_fragment = fragments.get(fragment)
            if prior_fragment is not None:
                diagnostics.append(
                    f"duplicate fragment name {fragment!r}: {prior_fragment} and {source}"
                )
            else:
                fragments[fragment] = source
        for surface in manifest.get("surfaces", []):
            if not isinstance(surface, dict):
                continue
            identity = surface.get("identity")
            if not isinstance(identity, str):
                continue
            prior = classified.get(identity)
            if prior is not None:
                diagnostics.append(
                    f"duplicate surface identity {identity!r}: {prior[0]} and {source}"
                )
            else:
                classified[identity] = (source, surface)

    live, discovery_errors = discover_surfaces(root)
    diagnostics.extend(discovery_errors)
    for identity, surface in sorted(live.items()):
        row = classified.get(identity)
        if row is None:
            diagnostics.append(
                f"unclassified surface {identity!r} at {surface.path}; "
                "add a uniquely named surface-inventory fragment"
            )
            continue
        source, expected = row
        if expected.get("surface_type") != surface.surface_type:
            diagnostics.append(
                f"{source}: {identity!r} type changed from "
                f"{expected.get('surface_type')!r} to {surface.surface_type!r}"
            )
        if expected.get("path") != surface.path:
            diagnostics.append(
                f"{source}: {identity!r} moved from {expected.get('path')!r} "
                f"to {surface.path!r}"
            )
        if (
            expected.get("disposition") == "retain"
            and expected.get("content_sha256") != surface.content_sha256
        ):
            diagnostics.append(
                f"{source}: frozen content hash drift for {identity!r} at {surface.path}"
            )

    for identity, (source, surface) in sorted(classified.items()):
        disposition = surface.get("disposition")
        if identity not in live and disposition != "retire-dead":
            diagnostics.append(
                f"{source}: missing non-retired surface {identity!r} "
                f"at {surface.get('path')!r}"
            )
        if disposition not in {"retain", "repair"}:
            continue
        for pointer in surface.get("behavioral_tests", []):
            diagnostics.extend(
                evidence_diagnostics(
                    root,
                    source,
                    identity,
                    surface,
                    pointer,
                    classified,
                )
            )
    return diagnostics


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the frozen toolkit surface and additive fragments."
    )
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=pathlib.Path.cwd(),
        help="repository root (default: current directory)",
    )
    parser.add_argument(
        "--check",
        required=True,
        type=pathlib.Path,
        help="frozen BASELINE.json to validate",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root.resolve()
    baseline = args.check
    if not baseline.is_absolute():
        baseline = root / baseline
    diagnostics = check_inventory(root, baseline.resolve())
    if diagnostics:
        for diagnostic in diagnostics:
            print(f"inventory-core-surface: {diagnostic}", file=sys.stderr)
        return 1
    live, _ = discover_surfaces(root)
    print(f"inventory-core-surface: {len(live)} classified surfaces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
