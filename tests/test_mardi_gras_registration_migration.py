from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import multiprocessing
from pathlib import Path
import shutil
import sys
import time
import os

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "specs"
    / "mardi-gras-agentic-integration"
    / "migrate-registration.py"
)
MANIFEST = SCRIPT.with_name("registration-repair-v1.json")
SPEC = importlib.util.spec_from_file_location("mardi_registration_migration", SCRIPT)
assert SPEC and SPEC.loader
migration = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = migration
SPEC.loader.exec_module(migration)


OWNER_CONTEXT = {
    "machine_host_identity": "a" * 64,
    "reviewed_commit": "b" * 40,
    "authority_binary_sha256": "c" * 64,
    "identity_document_sha256": "d" * 64,
    "lock_path_sha256": "e" * 64,
}


def _ledger(path):
    return migration.EvidenceLedger(path, OWNER_CONTEXT)


def _task01_fields():
    return {
        "title": "Task 01",
        "description": "retained",
        "acceptance": "acceptance",
        "notes": "",
        "status": "blocked",
        "assignee": "",
        "priority": 0,
        "issue_type": "task",
        "external_ref": migration._external_ref(
            "specs/mardi-gras-agentic-integration/tasks/01-make-claims-session-safe.md"
        ),
    }


def _attested_manifest():
    validated = migration.validate_manifest(MANIFEST)
    data = copy.deepcopy(validated.data)
    definition_paths = {
        data["retained"]["path"],
        *(item["path"] for item in data["bootstrap"]),
        *(item["path"] for item in data["historical"]),
        *(item["path"] for item in data["replacements"]),
    }
    data["attestation"] = {
        "source_commit": "1" * 40,
        "bootstrap_source_commit": "c" * 40,
        "bootstrap_attestation_commit": "d" * 40,
        "spec_sha256": "3" * 64,
        "human_sha256": {
            item["path"]: hashlib.sha256(item["path"].encode()).hexdigest()
            for item in data["manual_blockers"]
        },
        "definition_hash": {
            path: hashlib.sha256(path.encode()).hexdigest() for path in definition_paths
        },
        "bootstrap_receipt_sha256": migration.digest(_bootstrap_receipt()),
        "task01_live_fields_sha256": migration.digest(_task01_fields()),
        "starting_tracker_snapshot": {},
    }
    return migration.ValidatedManifest(
        validated.path,
        validated.root,
        data,
        validated.replacement_paths,
        validated.external_refs,
    )


def _bootstrap_receipt():
    return {
        "schema": "agentic.registration-bootstrap-terminal-receipt/v1",
        "source_commit": "c" * 40,
        "attestation_commit": "d" * 40,
        "intent": {
            "id": "018f2a10-7b3c-7abc-8def-0123456789ab",
            "sha256": "6" * 64,
        },
        "issues": {
            "00A": "agentic-00a1",
            "00B": "agentic-00b2",
            "00C": "agentic-00c3",
            "00D": "agentic-00d4",
        },
        "published_head": "7" * 40,
        "event_chain": {"head": "8" * 64, "previous": "9" * 64},
        "provider": {
            "path": str(SCRIPT),
            "sha256": migration.file_digest(SCRIPT),
            "full_profile_identity": {
                "backend_mode": "embedded",
                "database_identity": "db-fixture",
                "project_identity": "project-fixture",
                "repository_identity": "repo-fixture",
                "core_schema_fingerprint": "a" * 64,
                "full_schema_fingerprint": "b" * 64,
            },
        },
    }


def _review_artifact():
    return {
        "schema": "agentic.registration-review/v1",
        "verdict": "READY",
        "reviewed_commit": "2" * 40,
        "source_commit": "1" * 40,
        "spec_sha256": "3" * 64,
        "reviewer_run_id": "critic-run-17",
        "evidence_summary": "Whole bundle and manifest-only child are READY.",
    }


def _run_reconciler(reconciler):
    receipt = _bootstrap_receipt()
    return reconciler.run(
        "2" * 40,
        _review_artifact(),
        receipt,
        migration.digest(receipt),
    )


def _redigest_snapshot(snapshot):
    domain = {
        key: snapshot[key]
        for key in (
            "phase",
            "primitive_index",
            "primitive_sha256",
            "issues",
            "edges",
            "history",
            "comments",
            "scoped_ready",
        )
    }
    snapshot["domain_sha256"] = migration.digest(domain)
    return snapshot


class FakeSourceGate:
    def attest(self, manifest, reviewed_commit):
        assert reviewed_commit == "2" * 40
        return {
            "reviewed_commit": reviewed_commit,
            "source_commit": manifest.data["attestation"]["source_commit"],
            "manifest_sha256": migration.file_digest(manifest.path),
        }


class FakeAuthority:
    """A semantic fake for the future Task-00D authority, not a bd stub."""

    def __init__(self, manifest):
        self.manifest = manifest
        self.applied = {}
        self.primitive_before = {}
        self.primitive_after = {}
        self.primitive_receipts = {}
        self.phase_snapshots = {}
        self.mutation_count = 0
        self.release_count = 0
        self.requests = []

    def _phase_applied(self, phase):
        return self.applied.setdefault(phase, [])

    def _all_receipts(self):
        return sorted(
            [
                receipt
                for (phase, index), receipt in self.primitive_receipts.items()
                if index in self._phase_applied(phase)
            ],
            key=migration.canonical_bytes,
        )

    def _comments(self):
        if self._phase_applied("review_recorded"):
            return [
                {
                    "issue_id": self.manifest.data["retained"]["id"],
                    "schema": "agentic.registration-review/v1",
                    "digest": migration.digest(_review_artifact()),
                }
            ]
        return []

    def _history(self, extra=None):
        rows = [
            {
                "issue_id": self.manifest.data["retained"]["id"],
                "cursor": f"{phase}:{index:04d}",
                "event_digest": primitive_sha,
            }
            for (phase, index), primitive_sha in sorted(
                (
                    (key, receipt["primitive_sha256"])
                    for key, receipt in self.primitive_receipts.items()
                    if key[1] in self._phase_applied(key[0])
                ),
                key=lambda item: item[0],
            )
        ]
        if extra is not None:
            rows.append(extra)
        return sorted(rows, key=migration.canonical_bytes)

    def _issues(self):
        return [
            {
                "id": self.manifest.data["retained"]["id"],
                "external_ref": migration._external_ref(
                    self.manifest.data["retained"]["path"]
                ),
                "revision": f"rev-{self.mutation_count:04d}",
                "history_cursor": f"cursor-{self.mutation_count:04d}",
                "fields": {
                    **_task01_fields(),
                    "status": "open" if self.release_count else "blocked",
                },
                "metadata": {"registration_state": "complete"},
            }
        ]

    def _snapshot(
        self,
        phase,
        primitive_index,
        primitive_sha256,
        *,
        history=None,
        receipts=None,
        scoped_ready=None,
        comments=None,
        issues=None,
    ):
        issue_rows = self._issues() if issues is None else issues
        edges = []
        history_rows = self._history() if history is None else history
        comment_rows = self._comments() if comments is None else comments
        ready = (
            [self.manifest.data["retained"]["id"]]
            if scoped_ready is None and self.release_count
            else (scoped_ready or [])
        )
        domain = {
            "phase": phase,
            "primitive_index": primitive_index,
            "primitive_sha256": primitive_sha256,
            "issues": issue_rows,
            "edges": edges,
            "history": history_rows,
            "comments": comment_rows,
            "scoped_ready": ready,
        }
        return {
            "schema": "agentic.registration-authority-snapshot/v1",
            **domain,
            "storage_receipts": self._all_receipts()
            if receipts is None
            else sorted(receipts, key=migration.canonical_bytes),
            "domain_sha256": migration.digest(domain),
        }

    def _verification_complete(self, phase):
        if phase == "bootstrap_verified":
            return True
        if phase == "tracker_attested":
            return bool(self._phase_applied("review_recorded"))
        if phase == "container_verified":
            return bool(self._phase_applied("manual_blocked"))
        if phase == "prepared":
            return any(
                key[0] == "container_verified" for key in self.phase_snapshots
            )
        return False

    def request(self, operation, payload):
        self.requests.append((operation, copy.deepcopy(payload)))
        if operation == "inspect_phase":
            phase = payload["phase"]
            count = payload["primitive_count"]
            prefix = len(self._phase_applied(phase))
            complete = prefix == count and (
                count > 0 or self._verification_complete(phase)
            )
            key = (phase, payload["primitive_requests_sha256"])
            if complete and key not in self.phase_snapshots:
                self.phase_snapshots[key] = self._snapshot(
                    phase,
                    -1,
                    payload["primitive_requests_sha256"],
                )
            snapshot = self.phase_snapshots.get(key) or self._snapshot(
                phase,
                -1,
                payload["primitive_requests_sha256"],
            )
            return {
                "schema": "agentic.registration-authority-phase-inspection/v1",
                "phase": phase,
                "complete": complete,
                "primitive_count": count,
                "applied_prefix": prefix,
                "snapshot": snapshot,
            }
        if operation == "inspect_primitive":
            phase = payload["phase"]
            index = payload["primitive_index"]
            key = (phase, index)
            applied = index in self._phase_applied(phase)
            snapshot = (
                self.primitive_after[key]
                if applied
                else self.primitive_before.setdefault(
                    key,
                    self._snapshot(
                        phase,
                        index,
                        payload["primitive_sha256"],
                        scoped_ready=[],
                    ),
                )
            )
            return {
                "schema": "agentic.registration-authority-primitive-inspection/v1",
                "phase": phase,
                "primitive_index": index,
                "primitive_sha256": payload["primitive_sha256"],
                "applied": applied,
                "snapshot": snapshot,
                "receipt": self.primitive_receipts.get(key) if applied else None,
            }
        if operation == "plan_primitive":
            phase = payload["phase"]
            index = payload["primitive_index"]
            key = (phase, index)
            before = payload["before_snapshot"]
            extra_history = {
                "issue_id": self.manifest.data["retained"]["id"],
                "cursor": f"{phase}:{index:04d}",
                "event_digest": payload["primitive_sha256"],
            }
            after_domain_snapshot = self._snapshot(
                phase,
                index,
                payload["primitive_sha256"],
                history=sorted(
                    [*before["history"], extra_history],
                    key=migration.canonical_bytes,
                ),
                receipts=before["storage_receipts"],
                comments=(
                    sorted(
                        [
                            *before["comments"],
                            {
                                "issue_id": self.manifest.data["retained"]["id"],
                                "schema": "agentic.registration-review/v1",
                                "digest": migration.digest(_review_artifact()),
                            },
                        ],
                        key=migration.canonical_bytes,
                    )
                    if phase == "review_recorded"
                    else before["comments"]
                ),
                issues=(
                    [
                        {
                            **before["issues"][0],
                            "fields": {
                                **before["issues"][0]["fields"],
                                "status": "open",
                            },
                        }
                    ]
                    if phase == "released"
                    else before["issues"]
                ),
                scoped_ready=(
                    [self.manifest.data["retained"]["id"]]
                    if phase == "released"
                    else []
                ),
            )
            receipt = {
                "schema": "agentic.registration-storage-transaction/v1",
                "transaction_id": f"tx:{phase}:{index:04d}",
                "phase": phase,
                "primitive_index": index,
                "primitive_sha256": payload["primitive_sha256"],
                "before_domain_sha256": before["domain_sha256"],
                "after_domain_sha256": after_domain_snapshot["domain_sha256"],
                "history_cursor": f"{phase}:{index:04d}",
            }
            intended = {
                **after_domain_snapshot,
                "storage_receipts": sorted(
                    [*before["storage_receipts"], receipt],
                    key=migration.canonical_bytes,
                ),
            }
            self.primitive_after[key] = intended
            self.primitive_receipts[key] = receipt
            return {
                "schema": "agentic.registration-authority-primitive-plan/v1",
                "phase": phase,
                "primitive_index": index,
                "primitive_sha256": payload["primitive_sha256"],
                "before_snapshot": before,
                "intended_snapshot": intended,
                "receipt": receipt,
            }
        if operation == "apply_primitive":
            phase = payload["phase"]
            index = payload["primitive_index"]
            key = (phase, index)
            if index != len(self._phase_applied(phase)):
                raise AssertionError("provider received a non-prefix primitive")
            assert payload["intended_snapshot"] == self.primitive_after[key]
            assert payload["receipt"] == self.primitive_receipts[key]
            self._phase_applied(phase).append(index)
            self.mutation_count += 1
            if phase == "released":
                self.release_count += 1
            return {
                "schema": "agentic.registration-authority-apply/v1",
                "accepted": True,
                "receipt": self.primitive_receipts[key],
            }
        raise AssertionError(f"unexpected fake operation {operation}")


def _copy_validation_fixture(tmp_path):
    root = tmp_path / "repo"
    (root / "specs" / "mardi-gras-agentic-integration").mkdir(parents=True)
    (root / "AGENTS.md").write_text("fixture\n")
    shutil.copytree(
        ROOT / "specs" / "mardi-gras-agentic-integration" / "tasks",
        root / "specs" / "mardi-gras-agentic-integration" / "tasks",
    )
    shutil.copy2(MANIFEST, root / MANIFEST.relative_to(ROOT))
    return root, root / MANIFEST.relative_to(ROOT)


def test_closed_manifest_validates_exact_definitions_and_graph():
    validated = migration.validate_manifest(MANIFEST)
    assert len(validated.replacement_paths) == 27
    assert len(validated.data["historical"]) == 11
    assert len(validated.data["known_external_rewires"]) == 2
    assert validated.data["attestation"] == {}


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda value: value.update({"unknown": True}), "manifest_schema"),
        (lambda value: value["replacements"].pop(), "manifest_graph"),
        (
            lambda value: value["historical"].__setitem__(
                2,
                {
                    **value["historical"][2],
                    "replacement": migration.TASK_PREFIX
                    + "17-instrument-native-facades-repair.md",
                },
            ),
            "manifest_history",
        ),
        (
            lambda value: value["known_external_rewires"].reverse(),
            "manifest_external",
        ),
    ],
)
def test_manifest_drift_fails_closed(tmp_path, mutation, code):
    _, path = _copy_validation_fixture(tmp_path)
    value = json.loads(path.read_text())
    mutation(value)
    path.write_text(json.dumps(value))
    with pytest.raises(migration.MigrationError, match=code):
        migration.validate_manifest(path)


def test_live_validation_requires_filled_attestation():
    with pytest.raises(migration.MigrationError, match="source_unattested"):
        migration.validate_manifest(MANIFEST, require_attestation=True)


def _snapshot_issue(issue_id):
    return {
        "id": issue_id,
        "revision": f"rev-{issue_id}",
        "history_cursor": f"history-{issue_id}",
        "fields": {
            "title": f"title {issue_id}",
            "description": "description",
            "acceptance": "acceptance",
            "notes": "",
            "status": "blocked",
            "assignee": "",
            "priority": 0,
            "issue_type": "task",
            "external_ref": f"spec-task:{issue_id}",
        },
        "metadata": {"registration_state": "complete"},
        "edges": [],
    }


def test_starting_snapshot_is_inline_complete_and_exact_domain():
    manifest = migration.validate_manifest(MANIFEST)
    snapshot = {
        "schema": "agentic.registration-starting-snapshot/v1",
        "task01": _snapshot_issue("agentic-yt1"),
        "historical": [
            _snapshot_issue(item["id"]) for item in manifest.data["historical"]
        ],
        "known_external_consumers": [
            _snapshot_issue(item["consumer"])
            for item in manifest.data["known_external_rewires"]
        ],
    }
    assert migration._validate_starting_snapshot(
        snapshot,
        manifest.data["retained"],
        manifest.data["historical"],
        manifest.data["known_external_rewires"],
    ) == snapshot
    snapshot["historical"].pop()
    with pytest.raises(migration.MigrationError, match="attestation_snapshot"):
        migration._validate_starting_snapshot(
            snapshot,
            manifest.data["retained"],
            manifest.data["historical"],
            manifest.data["known_external_rewires"],
        )


def test_relative_or_missing_authority_never_falls_back_to_bd(tmp_path):
    with pytest.raises(migration.MigrationError, match="authority_path"):
        migration.SubprocessAuthority(Path("bd"))
    with pytest.raises(migration.MigrationError, match="authority_path"):
        migration.SubprocessAuthority(tmp_path / "missing")


def test_workset_extension_binds_authored_bytes_envelope_and_downstream(tmp_path):
    task = tmp_path / "specs" / "40-new-mandatory-work.md"
    task.parent.mkdir()
    (task.parent / "02-historical.md").write_text("# historical\n")
    (task.parent / "02-replacement.md").write_text("# replacement\n")
    task.write_text(
        """# Task 40: add new mandatory work

Status: pending
Depends on: 02-replacement.md
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md
Touch: tests/test_new.py, agentic/new.py

## Goal

Implement the newly discovered mandatory behavior.

## Touch

This task owns the new implementation and its focused test.

## Steps

1. Add the failing test.
2. Implement the behavior.

## Acceptance

- [ ] `python3 -m pytest tests/test_new.py -q` passes against the new behavior.
"""
    )
    relative = task.relative_to(tmp_path).as_posix()
    touch = ["agentic/new.py", "tests/test_new.py"]
    definition = {
        "schema_version": 1,
        "path": relative,
        "title": "Task 40: add new mandatory work",
        "goal": "Implement the newly discovered mandatory behavior.",
        "touch": touch,
        "budget": "12 turns",
        "rigor": "production",
        "prerequisites": ["spec-task:specs/02-replacement.md"],
    }
    definition_hash = migration.digest(definition)
    action = {
        "schema": migration.WORKSET_SCHEMA,
        "trigger": "human",
        "task": {
            "path": relative,
            "bytes_sha256": migration.file_digest(task),
            "definition_hash": definition_hash,
            "envelope": {
                "title": definition["title"],
                "description": definition["goal"],
                "acceptance": (
                    "- [ ] `python3 -m pytest tests/test_new.py -q` passes "
                    "against the new behavior."
                ),
                "task_type": "task",
                "priority": 0,
                "metadata": {
                    "budget": "12 turns",
                    "definition_hash": definition_hash,
                    "registration_state": "complete",
                    "rigor": "production",
                    "source": relative,
                    "touch": touch,
                },
                "container": {"id": "agentic-j01", "relation": "related"},
                "source": relative,
                "touch": touch,
                "budget": "12 turns",
                "rigor": "production",
                "prerequisites": ["spec-task:specs/02-replacement.md"],
            },
        },
        "downstream": {
            "issue_id": "agentic-next",
            "revision": "rev-17",
            "edge": {
                "kind": "blocks",
                "issue_id": "agentic-next",
                "dependency_external_ref": "spec-task:" + relative,
            },
        },
    }
    assert migration.validate_workset_extension(action, tmp_path) == action

    substitutions = []
    changed = copy.deepcopy(action)
    changed["task"]["envelope"]["title"] = "plausible but unauthored title"
    substitutions.append(changed)
    changed = copy.deepcopy(action)
    changed["task"]["envelope"]["acceptance"] = "partial acceptance"
    substitutions.append(changed)
    changed = copy.deepcopy(action)
    changed["task"]["envelope"]["touch"] = list(reversed(touch))
    substitutions.append(changed)
    changed = copy.deepcopy(action)
    changed["task"]["envelope"]["container"]["relation"] = "parent-child"
    substitutions.append(changed)
    changed = copy.deepcopy(action)
    changed["task"]["envelope"]["metadata"]["definition_hash"] = "0" * 64
    substitutions.append(changed)
    changed = copy.deepcopy(action)
    changed["task"]["definition_hash"] = "0" * 64
    substitutions.append(changed)
    changed = copy.deepcopy(action)
    changed["task"]["envelope"]["source"] = "specs/substitute.md"
    substitutions.append(changed)
    changed = copy.deepcopy(action)
    changed["downstream"]["revision"] = "revision with spaces"
    substitutions.append(changed)
    changed = copy.deepcopy(action)
    changed["downstream"]["edge"]["kind"] = "related"
    substitutions.append(changed)
    changed = copy.deepcopy(action)
    changed["downstream"]["edge"]["dependency_external_ref"] = (
        "spec-task:specs/substitute.md"
    )
    substitutions.append(changed)
    changed = copy.deepcopy(action)
    changed["task"]["envelope"]["unknown"] = True
    substitutions.append(changed)
    for substituted in substitutions:
        with pytest.raises(migration.MigrationError, match="workset_extension|manifest_schema"):
            migration.validate_workset_extension(substituted, tmp_path)

    numeric_dependency_bytes = task.read_bytes().replace(
        b"Depends on: 02-replacement.md", b"Depends on: 02"
    )
    task.write_bytes(numeric_dependency_bytes)
    ambiguous = copy.deepcopy(action)
    ambiguous["task"]["bytes_sha256"] = migration.file_digest(task)
    with pytest.raises(migration.MigrationError, match="numeric dependency 02"):
        migration.validate_workset_extension(ambiguous, tmp_path)

    task.write_bytes(
        numeric_dependency_bytes.replace(b"Depends on: 02", b"Depends on: 02-replacement.md")
    )
    task.write_text(task.read_text().replace("new behavior.", "different behavior."))
    with pytest.raises(migration.MigrationError, match="bytes/hash"):
        migration.validate_workset_extension(action, tmp_path)


def test_review_artifact_is_external_canonical_and_identity_bound(tmp_path):
    manifest = _attested_manifest()
    artifact = tmp_path / "review.json"
    artifact.write_bytes(migration.canonical_bytes(_review_artifact()))
    assert migration.validate_review_artifact(
        artifact, manifest, "2" * 40
    ) == _review_artifact()
    changed = _review_artifact()
    changed["reviewed_commit"] = "9" * 40
    artifact.write_bytes(migration.canonical_bytes(changed))
    with pytest.raises(migration.MigrationError, match="review_artifact"):
        migration.validate_review_artifact(artifact, manifest, "2" * 40)


def test_bootstrap_terminal_receipt_is_loaded_hashed_and_identity_bound(tmp_path):
    manifest = _attested_manifest()
    receipt_value = _bootstrap_receipt()
    receipt = tmp_path / "bootstrap-receipt.json"
    receipt.write_bytes(migration.canonical_bytes(receipt_value))
    receipt.chmod(0o600)
    loaded, loaded_sha256 = migration.load_bootstrap_receipt(
        receipt, manifest, "2" * 40
    )
    assert loaded == receipt_value
    assert loaded_sha256 == manifest.data["attestation"][
        "bootstrap_receipt_sha256"
    ]
    assert loaded["source_commit"] != manifest.data["attestation"][
        "source_commit"
    ]
    assert loaded["attestation_commit"] != "2" * 40

    tampered = copy.deepcopy(receipt_value)
    tampered["event_chain"]["previous"] = tampered["event_chain"]["head"]
    receipt.write_bytes(migration.canonical_bytes(tampered))
    with pytest.raises(migration.MigrationError, match="bootstrap_receipt"):
        migration.load_bootstrap_receipt(receipt, manifest, "2" * 40)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_commit", "1" * 40),
        ("attestation_commit", "2" * 40),
    ],
)
def test_bootstrap_and_final_commit_identities_cannot_be_cross_substituted(
    tmp_path, field, value
):
    manifest = _attested_manifest()
    receipt_value = _bootstrap_receipt()
    receipt_value[field] = value
    receipt = tmp_path / "bootstrap-receipt.json"
    receipt.write_bytes(migration.canonical_bytes(receipt_value))
    receipt.chmod(0o600)
    with pytest.raises(migration.MigrationError, match="commit/schema identity"):
        migration.load_bootstrap_receipt(receipt, manifest, "2" * 40)


def test_bootstrap_receipt_path_and_provider_hash_fail_closed(tmp_path):
    manifest = _attested_manifest()
    receipt_value = _bootstrap_receipt()
    receipt_value["provider"]["sha256"] = "0" * 64
    receipt = tmp_path / "bootstrap-receipt.json"
    receipt.write_bytes(migration.canonical_bytes(receipt_value))
    receipt.chmod(0o600)
    with pytest.raises(migration.MigrationError, match="provider path/hash"):
        migration.load_bootstrap_receipt(receipt, manifest, "2" * 40)
    with pytest.raises(migration.MigrationError, match="escapes repository"):
        migration.load_bootstrap_receipt(
            Path(os.path.relpath(receipt, manifest.root)),
            manifest,
            "2" * 40,
        )


def test_source_evidence_binds_full_bootstrap_receipt_before_mutation(tmp_path):
    manifest = _attested_manifest()
    authority = FakeAuthority(manifest)
    ledger = _ledger(tmp_path / "evidence")
    _run_reconciler(
        migration.Reconciler(manifest, authority, ledger, FakeSourceGate())
    )
    source_commit = next(
        event
        for event in ledger.chain
        if event["phase"] == "source_attested"
        and event["kind"] == "operation_committed"
    )
    after = source_commit["payload"]["after_snapshot"]
    assert after["bootstrap_receipt"] == _bootstrap_receipt()
    assert after["bootstrap_receipt_sha256"] == migration.digest(
        _bootstrap_receipt()
    )
    bootstrap_prepared = next(
        event
        for event in ledger.chain
        if event["phase"] == "bootstrap_verified"
        and event["kind"] == "operation_prepared"
        and event["idempotency_key"].startswith("phase:")
    )
    assert bootstrap_prepared["payload"]["bootstrap_receipt"] == (
        _bootstrap_receipt()
    )
    assert bootstrap_prepared["payload"]["bootstrap_receipt_sha256"] == (
        migration.digest(_bootstrap_receipt())
    )
    assert authority.requests[0][0] == "inspect_phase"
    assert authority.requests[0][1]["phase"] == "bootstrap_verified"


def test_evidence_is_canonical_hash_chained_and_idempotent(tmp_path):
    ledger = _ledger(tmp_path / "evidence")
    first = ledger.append(
        "operation_prepared", "source_attested", "source:1", {"before": "a"}
    )
    assert ledger.append(
        "operation_prepared", "source_attested", "source:1", {"before": "a"}
    ) == first
    ledger.append(
        "operation_committed",
        "source_attested",
        "source:1",
        {"prepared_sha256": hashlib.sha256(migration.canonical_bytes(first)).hexdigest()},
    )
    reopened = _ledger(tmp_path / "evidence")
    assert len(reopened.chain) == 2
    assert reopened.chain[1]["previous"] == hashlib.sha256(
        migration.canonical_bytes(reopened.chain[0])
    ).hexdigest()
    assert all(event["owner_uuid"] for event in reopened.chain)
    assert len(list((tmp_path / "evidence" / "owners").glob("*.json"))) == 2
    with pytest.raises(migration.MigrationError, match="evidence_conflict"):
        reopened.append(
            "operation_prepared",
            "source_attested",
            "source:1",
            {"before": "different"},
        )


def test_final_head_is_closed_canonical_and_owner_bound(tmp_path):
    ledger = _ledger(tmp_path / "evidence")
    event = ledger.append(
        "operation_prepared", "source_attested", "head-schema", {"value": 1}
    )
    raw = ledger.head.read_bytes()
    head = json.loads(raw)
    assert migration.canonical_bytes(head) == raw
    assert head == {
        "schema": "agentic.registration-migration-head/v1",
        "owner_uuid": event["owner_uuid"],
        "sequence": 0,
        "digest": hashlib.sha256(migration.canonical_bytes(event)).hexdigest(),
    }

    head["owner_uuid"] = "not-a-uuid"
    ledger.head.write_bytes(migration.canonical_bytes(head))
    ledger.head.chmod(0o600)
    with pytest.raises(migration.MigrationError, match="evidence_corrupt"):
        _ledger(tmp_path / "evidence")


def test_evidence_detects_tamper(tmp_path):
    ledger = _ledger(tmp_path / "evidence")
    ledger.append("operation_prepared", "source_attested", "x", {"a": 1})
    event = next((tmp_path / "evidence" / "events").glob("*.json"))
    event.write_bytes(event.read_bytes() + b" ")
    with pytest.raises(migration.MigrationError, match="evidence_corrupt"):
        _ledger(tmp_path / "evidence")


def test_state_paths_reject_symlinked_ancestor_and_bad_directory_mode(tmp_path):
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(migration.MigrationError, match="unsafe_state_path"):
        _ledger(linked / "evidence")

    unsafe = tmp_path / "unsafe-evidence"
    unsafe.mkdir(mode=0o755)
    unsafe.chmod(0o755)
    with pytest.raises(migration.MigrationError, match="unsafe_state_path"):
        _ledger(unsafe)


@pytest.mark.parametrize("target", ["event", "head", "owner"])
def test_evidence_rejects_non_0600_files(tmp_path, target):
    ledger = _ledger(tmp_path / target)
    event = ledger.append(
        "operation_prepared", "source_attested", "mode-test", {"value": target}
    )
    paths = {
        "event": next(ledger.events.glob("*.json")),
        "head": ledger.head,
        "owner": ledger.owners / f"{event['owner_uuid']}.json",
    }
    paths[target].chmod(0o644)
    with pytest.raises(migration.MigrationError, match="evidence_corrupt|unsafe_state_path"):
        _ledger(tmp_path / target)


def test_owner_record_binds_complete_migration_identity(tmp_path):
    ledger = _ledger(tmp_path / "evidence")
    event = ledger.append(
        "operation_prepared", "source_attested", "owner-binding", {"value": 1}
    )
    owner_path = ledger.owners / f"{event['owner_uuid']}.json"
    owner = json.loads(owner_path.read_bytes())
    assert {key: owner[key] for key in OWNER_CONTEXT} == OWNER_CONTEXT

    owner["identity_document_sha256"] = "f" * 64
    owner_path.write_bytes(migration.canonical_bytes(owner))
    owner_path.chmod(0o600)
    with pytest.raises(migration.MigrationError, match="owner invariant"):
        _ledger(tmp_path / "evidence")


def test_evidence_ancestor_swap_fails_without_redirected_write(tmp_path):
    path = tmp_path / "evidence"
    ledger = _ledger(path)
    original = tmp_path / "evidence-original"
    path.rename(original)
    redirected = tmp_path / "redirected"
    (redirected / "events").mkdir(parents=True, mode=0o700)
    (redirected / "owners").mkdir(mode=0o700)
    path.symlink_to(redirected, target_is_directory=True)

    with pytest.raises(migration.MigrationError, match="unsafe_state_path"):
        ledger.append(
            "operation_prepared",
            "source_attested",
            "ancestor-swap",
            {"value": 1},
        )
    assert list((redirected / "events").iterdir()) == []


def test_evidence_rejects_unknown_temporary_and_same_sequence_fork(tmp_path):
    ledger = _ledger(tmp_path / "temporary")
    (ledger.events / ".tmp-foreign").write_text("torn")
    with pytest.raises(migration.MigrationError, match="temporary"):
        _ledger(tmp_path / "temporary")

    ledger = _ledger(tmp_path / "fork")
    first = ledger.append("operation_prepared", "source_attested", "x", {"a": 1})
    fork = {**first, "idempotency_key": "fork"}
    raw = migration.canonical_bytes(fork)
    fork_digest = hashlib.sha256(raw).hexdigest()
    fork_path = ledger.events / f"{0:020d}-{fork_digest}.json"
    fork_path.write_bytes(raw)
    fork_path.chmod(0o600)
    with pytest.raises(migration.MigrationError, match="forked"):
        _ledger(tmp_path / "fork")


def _write_owner(ledger, owner_uuid, *, pid, process_start, boot_identity):
    owner = {
        "schema": "agentic.registration-migration-owner/v1",
        "owner_uuid": owner_uuid,
        "pid": pid,
        "process_start": process_start,
        "boot_identity": boot_identity,
        "effective_uid": os.geteuid(),
        **OWNER_CONTEXT,
    }
    path = ledger.owners / f"{owner_uuid}.json"
    path.write_bytes(migration.canonical_bytes(owner))
    path.chmod(0o600)
    return path


def _write_event_temp(ledger, owner_uuid, *, body_owner=None):
    event = {
        "schema": migration.EVENT_SCHEMA,
        "sequence": 0,
        "previous": None,
        "owner_uuid": body_owner or owner_uuid,
        "kind": "operation_prepared",
        "phase": "source_attested",
        "idempotency_key": "recovery-test",
        "payload": {"prepared": True},
    }
    raw = migration.canonical_bytes(event)
    value_digest = hashlib.sha256(raw).hexdigest()
    path = ledger.events / f".tmp-{owner_uuid}-{0:020d}-{value_digest}"
    path.write_bytes(raw)
    path.chmod(0o600)
    return path


def _write_head_temp(
    ledger,
    owner_uuid,
    *,
    body_owner=None,
    body_sequence=0,
    filename_sequence=0,
    filename_digest=None,
):
    head = {
        "schema": "agentic.registration-migration-head/v1",
        "owner_uuid": body_owner or owner_uuid,
        "sequence": body_sequence,
        "digest": "a" * 64,
    }
    raw = migration.canonical_bytes(head)
    content_digest = hashlib.sha256(raw).hexdigest()
    path = ledger.directory / (
        f".tmp-{owner_uuid}-{filename_sequence:020d}-"
        f"{filename_digest or content_digest}"
    )
    path.write_bytes(raw)
    path.chmod(0o600)
    return path


def test_exact_dead_prior_owner_temporary_is_removed(tmp_path):
    ledger = _ledger(tmp_path / "evidence")
    dead_owner = migration._uuid7()
    _write_owner(
        ledger,
        dead_owner,
        pid=2_147_483_647,
        process_start="definitely-not-a-process",
        boot_identity=migration._boot_identity(),
    )
    temporary = _write_event_temp(ledger, dead_owner)
    reopened = _ledger(tmp_path / "evidence")
    assert not temporary.exists()
    assert reopened.chain == []


def test_exact_dead_prior_owner_head_temporary_is_removed(tmp_path):
    ledger = _ledger(tmp_path / "evidence")
    dead_owner = migration._uuid7()
    _write_owner(
        ledger,
        dead_owner,
        pid=2_147_483_647,
        process_start="definitely-not-a-process",
        boot_identity=migration._boot_identity(),
    )
    temporary = _write_head_temp(ledger, dead_owner)
    reopened = _ledger(tmp_path / "evidence")
    assert not temporary.exists()
    assert reopened.chain == []


def test_live_prior_owner_temporary_fails_closed(tmp_path):
    ledger = _ledger(tmp_path / "evidence")
    live_owner = migration._uuid7()
    _write_owner(
        ledger,
        live_owner,
        pid=os.getpid(),
        process_start=migration._process_start(os.getpid()),
        boot_identity=migration._boot_identity(),
    )
    _write_event_temp(ledger, live_owner)
    with pytest.raises(migration.MigrationError, match="temporary_owner_live"):
        _ledger(tmp_path / "evidence")


def test_live_and_unknown_head_temporary_owners_fail_closed(tmp_path):
    live_ledger = _ledger(tmp_path / "live-head")
    live_owner = migration._uuid7()
    _write_owner(
        live_ledger,
        live_owner,
        pid=os.getpid(),
        process_start=migration._process_start(os.getpid()),
        boot_identity=migration._boot_identity(),
    )
    _write_head_temp(live_ledger, live_owner)
    with pytest.raises(migration.MigrationError, match="temporary_owner_live"):
        _ledger(tmp_path / "live-head")

    unknown_ledger = _ledger(tmp_path / "unknown-head")
    _write_head_temp(unknown_ledger, migration._uuid7())
    with pytest.raises(migration.MigrationError, match="temporary_owner_unknown"):
        _ledger(tmp_path / "unknown-head")


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        ({"body_owner": "another"}, "temporary_cross_owner"),
        ({"body_sequence": 1}, "temporary_malformed"),
        ({"filename_digest": "f" * 64}, "temporary_malformed"),
    ],
)
def test_head_temporary_binding_mismatch_fails_closed(tmp_path, changes, error):
    ledger = _ledger(tmp_path / "head-binding")
    dead_owner = migration._uuid7()
    another_owner = migration._uuid7()
    _write_owner(
        ledger,
        dead_owner,
        pid=2_147_483_647,
        process_start="definitely-not-a-process",
        boot_identity=migration._boot_identity(),
    )
    values = dict(changes)
    if values.get("body_owner") == "another":
        values["body_owner"] = another_owner
    _write_head_temp(ledger, dead_owner, **values)
    with pytest.raises(migration.MigrationError, match=error):
        _ledger(tmp_path / "head-binding")


def test_unknown_and_cross_owner_temporaries_fail_closed(tmp_path):
    unknown_ledger = _ledger(tmp_path / "unknown")
    missing_owner = migration._uuid7()
    _write_event_temp(unknown_ledger, missing_owner)
    with pytest.raises(migration.MigrationError, match="temporary_owner_unknown"):
        _ledger(tmp_path / "unknown")

    cross_ledger = _ledger(tmp_path / "cross")
    dead_owner = migration._uuid7()
    another_owner = migration._uuid7()
    _write_owner(
        cross_ledger,
        dead_owner,
        pid=2_147_483_647,
        process_start="definitely-not-a-process",
        boot_identity=migration._boot_identity(),
    )
    _write_event_temp(cross_ledger, dead_owner, body_owner=another_owner)
    with pytest.raises(migration.MigrationError, match="temporary_cross_owner"):
        _ledger(tmp_path / "cross")


def test_full_reconcile_keeps_pending_until_registered_and_releases_once(tmp_path):
    manifest = _attested_manifest()
    authority = FakeAuthority(manifest)
    ledger = _ledger(tmp_path / "evidence")
    result = migration.Reconciler(
        manifest, authority, ledger, FakeSourceGate()
    )
    result = _run_reconciler(result)
    assert result["status"] == "released"
    assert authority.release_count == 1
    assert {key[0] for key in authority.phase_snapshots} >= set(
        migration.PHASES[1:]
    )
    created_post = [
        request
        for request in authority.requests
        if request[0] == "inspect_phase"
        and request[1]["phase"] == "created"
    ][-1]
    assert created_post
    assert len(
        [
            event
            for event in ledger.chain
            if event["phase"] == "released"
            and event["kind"] == "operation_committed"
            and event["idempotency_key"].startswith("phase:")
        ]
    ) == 1
    primitive_events = [
        event
        for event in ledger.chain
        if event["idempotency_key"].startswith("primitive:")
    ]
    prepared_primitive_events = [
        event
        for event in primitive_events
        if event["kind"] == "operation_prepared"
    ]
    expected_primitive_count = sum(
        len(migration.primitive_requests(manifest, phase))
        for phase in migration.PHASES[1:]
    )
    assert len(prepared_primitive_events) == expected_primitive_count
    expected_primitive_keys = {
        event["idempotency_key"] for event in prepared_primitive_events
    }
    assert all(
        event["idempotency_key"]
        == (
            f"primitive:{event['phase']}:"
            f"{event['payload']['primitive_index']:04d}:"
            f"{migration.digest(event['payload']['primitive'])}"
        )
        for event in prepared_primitive_events
    )
    assert all(
        len(
            [
                event
                for event in primitive_events
                if event["idempotency_key"] == key
                and event["kind"] == kind
            ]
        )
        == 1
        for key in expected_primitive_keys
        for kind in ("operation_prepared", "operation_committed")
    )
    assert {
        event["phase"]
        for event in ledger.chain
        if event["kind"] == "operation_committed"
        and event["idempotency_key"].startswith("phase:")
    } == set(migration.PHASES)
    mutation_count = authority.mutation_count
    _run_reconciler(
        migration.Reconciler(manifest, authority, ledger, FakeSourceGate())
    )
    assert authority.mutation_count == mutation_count
    assert authority.release_count == 1


def test_driver_constructs_exact_low_level_migration_actions():
    manifest = _attested_manifest()
    created = migration.primitive_requests(manifest, "created")
    assert len(created) == 27
    assert all(item["primitive"] == "create_if_external_ref_absent" for item in created)
    assert created[0]["fields"]["title"].startswith("Task 13:")
    assert all(
        item["fields"]["metadata"]["registration_state"] == "pending"
        and isinstance(item["fields"]["metadata"]["touch"], list)
        and item["fields"]["metadata"]["touch"]
        == sorted(item["fields"]["metadata"]["touch"])
        and set(item["fields"]["metadata"])
        == {
            "registration_state",
            "budget",
            "source",
            "touch",
            "definition_hash",
            "rigor",
        }
        and item["initial_dependencies"][0]
        == {
            "external_ref": migration._external_ref(
                manifest.data["retained"]["path"]
            ),
            "kind": "blocks",
        }
        and item["initial_dependencies"][1]
        == {"issue_id": "agentic-j01", "kind": "related"}
        for item in created
    )
    wired = migration.primitive_requests(manifest, "wired")
    expected_non_task01_dependencies = sum(
        len([dep for dep in item["depends_on"] if dep != "01"])
        for item in manifest.data["replacements"]
    )
    assert len(wired) == expected_non_task01_dependencies
    assert all(item["primitive"] == "ensure_blocking_edge" for item in wired)
    registered = migration.primitive_requests(manifest, "registered")
    assert len(registered) == 27
    assert all(
        item["from"] == {"registration_state": "pending"}
        and item["to"] == {"registration_state": "complete"}
        for item in registered
    )
    redirected = migration.primitive_requests(manifest, "redirected")
    assert redirected[0]["primitive"] == "conditional_rewire"
    assert redirected[0]["consumer_id"] == "agentic-2nj.5"
    assert redirected[1]["issue_id"] == "agentic-868.9"
    assert [item["primitive"] for item in redirected[2:]] == [
        "conditional_supersede_with_redirect"
    ] * 11
    assert len(migration.primitive_requests(manifest, "manual_blocked")) == 2
    assert migration.primitive_requests(manifest, "released")[0][
        "expected_live_fields_sha256"
    ] == migration.digest(_task01_fields())
    review = migration.primitive_requests(manifest, "review_recorded")
    assert review == [
        {
            "primitive": "conditional_append_comment",
            "issue_id": "agentic-yt1",
            "expected_live_fields_sha256": migration.digest(_task01_fields()),
            "comment": "{review_artifact}",
            "unique_schema": "agentic.registration-review/v1",
        }
    ]


@pytest.mark.parametrize(
    "point",
    [
        "authority_schema_installed:primitive:0:after_prepared",
        "created:primitive:0:after_mutation",
        "redirected:primitive:6:after_mutation",
        "released:primitive:0:after_mutation",
    ],
)
def test_crash_rerun_completes_without_duplicate_mutation_or_release(tmp_path, point):
    manifest = _attested_manifest()
    authority = FakeAuthority(manifest)
    ledger = _ledger(tmp_path / "evidence")
    crashed = False

    def inject(candidate):
        nonlocal crashed
        if not crashed and candidate == point:
            crashed = True
            raise RuntimeError("injected crash")

    with pytest.raises(RuntimeError, match="injected crash"):
        _run_reconciler(
            migration.Reconciler(
                manifest, authority, ledger, FakeSourceGate(), crash=inject
            )
        )
    reopened = _ledger(tmp_path / "evidence")
    _run_reconciler(
        migration.Reconciler(manifest, authority, reopened, FakeSourceGate())
    )
    assert authority.release_count == 1
    assert len(
        [
            event
            for event in reopened.chain
                if event["phase"] == "released"
                and event["kind"] == "operation_committed"
                and event["idempotency_key"].startswith("phase:")
            ]
        ) == 1


def test_crash_hooks_cover_every_primitive_boundary(tmp_path):
    manifest = _attested_manifest()
    authority = FakeAuthority(manifest)
    observed = set()
    _run_reconciler(
        migration.Reconciler(
            manifest,
            authority,
            _ledger(tmp_path / "evidence"),
            FakeSourceGate(),
            crash=observed.add,
        )
    )
    expected = {
        f"{phase}:primitive:{index}:{boundary}"
        for phase in migration.PHASES[1:]
        for index, _ in enumerate(migration.primitive_requests(manifest, phase))
        for boundary in ("after_prepared", "after_mutation", "after_committed")
    }
    assert expected <= observed


def test_first_created_write_crash_resumes_prefix_without_replay(tmp_path):
    manifest = _attested_manifest()
    authority = FakeAuthority(manifest)
    crashed = False

    def inject(point):
        nonlocal crashed
        if not crashed and point == "created:primitive:0:after_mutation":
            crashed = True
            raise RuntimeError("first create committed in storage")

    ledger = _ledger(tmp_path / "evidence")
    with pytest.raises(RuntimeError, match="first create"):
        _run_reconciler(
            migration.Reconciler(
                manifest, authority, ledger, FakeSourceGate(), crash=inject
            )
        )
    assert authority._phase_applied("created") == [0]
    mutation_count_after_first = authority.mutation_count
    _run_reconciler(
        migration.Reconciler(
            manifest,
            authority,
            _ledger(tmp_path / "evidence"),
            FakeSourceGate(),
        )
    )
    total_primitives = sum(
        len(migration.primitive_requests(manifest, phase))
        for phase in migration.PHASES[1:]
    )
    assert authority.mutation_count == total_primitives
    assert authority.mutation_count > mutation_count_after_first
    assert authority._phase_applied("created") == list(range(27))


def test_task01_live_field_drift_fails_before_next_mutation(tmp_path):
    manifest = _attested_manifest()
    authority = FakeAuthority(manifest)
    authority.manifest.data["attestation"]["task01_live_fields_sha256"] = "6" * 64
    # The adapter now reports a digest different from the reviewed manifest.
    authority_digest = "5" * 64
    original_request = authority.request

    def request(operation, payload):
        response = original_request(operation, payload)
        if operation == "inspect":
            response["task01_live_fields_sha256"] = authority_digest
        return response

    authority.request = request
    with pytest.raises(migration.MigrationError, match="tracker_drift"):
        _run_reconciler(
            migration.Reconciler(
                manifest,
                authority,
                _ledger(tmp_path / "evidence"),
                FakeSourceGate(),
            )
        )
    assert authority.mutation_count == 0


def test_ready_exposure_before_release_fails_closed(tmp_path):
    manifest = _attested_manifest()
    authority = FakeAuthority(manifest)
    original_request = authority.request

    def request(operation, payload):
        response = original_request(operation, payload)
        if (
            operation == "inspect_phase"
            and payload["phase"] == "bootstrap_verified"
        ):
            response = copy.deepcopy(response)
            response["snapshot"]["scoped_ready"] = ["agentic-leak"]
            _redigest_snapshot(response["snapshot"])
        return response

    authority.request = request
    with pytest.raises(migration.MigrationError, match="early_exposure"):
        _run_reconciler(
            migration.Reconciler(
                manifest,
                authority,
                _ledger(tmp_path / "evidence"),
                FakeSourceGate(),
            )
        )
    assert authority.mutation_count == 0


def test_opaque_phase_snapshot_is_rejected_before_mutation(tmp_path):
    manifest = _attested_manifest()
    authority = FakeAuthority(manifest)
    original_request = authority.request

    def request(operation, payload):
        response = original_request(operation, payload)
        if (
            operation == "inspect_phase"
            and payload["phase"] == "bootstrap_verified"
        ):
            response = copy.deepcopy(response)
            response["snapshot"] = {"bounded": True}
        return response

    authority.request = request
    with pytest.raises(migration.MigrationError, match="authority_snapshot|manifest_schema"):
        _run_reconciler(
            migration.Reconciler(
                manifest,
                authority,
                _ledger(tmp_path / "evidence"),
                FakeSourceGate(),
            )
        )
    assert authority.mutation_count == 0


def test_primitive_plan_requires_complete_closed_domain_and_binding(tmp_path):
    manifest = _attested_manifest()
    authority = FakeAuthority(manifest)
    original_request = authority.request

    def request(operation, payload):
        response = original_request(operation, payload)
        if operation == "plan_primitive":
            response = copy.deepcopy(response)
            response["primitive_index"] += 1
        return response

    authority.request = request
    with pytest.raises(migration.MigrationError, match="authority_plan"):
        _run_reconciler(
            migration.Reconciler(
                manifest,
                authority,
                _ledger(tmp_path / "evidence"),
                FakeSourceGate(),
            )
        )
    assert authority.mutation_count == 0


def test_cli_requires_bootstrap_receipt_argument():
    required = [
        "run",
        "--manifest",
        str(MANIFEST),
        "--authority",
        str(SCRIPT),
        "--reviewed-commit",
        "2" * 40,
        "--review-artifact",
        "review.json",
        "--confirmed",
    ]
    with pytest.raises(SystemExit):
        migration._parser().parse_args(required)
    parsed = migration._parser().parse_args(
        [*required, "--bootstrap-receipt", "receipt.json"]
    )
    assert parsed.bootstrap_receipt == Path("receipt.json")


def _hold_lock(path, ready):
    with migration.MigrationLock(Path(path)):
        ready.set()
        time.sleep(1.0)


def test_lock_race_has_one_owner_and_reopens_after_death(tmp_path):
    lock = tmp_path / "locks" / "migration.lock"
    ready = multiprocessing.Event()
    process = multiprocessing.Process(target=_hold_lock, args=(lock, ready))
    process.start()
    assert ready.wait(3)
    try:
        with pytest.raises(migration.MigrationError, match="migration_busy"):
            with migration.MigrationLock(lock):
                pass
    finally:
        process.terminate()
        process.join(3)
    with migration.MigrationLock(lock):
        pass


def test_lock_rejects_non_0600_file_and_ancestor_swap(tmp_path):
    unsafe_parent = tmp_path / "unsafe-lock"
    unsafe_parent.mkdir(mode=0o700)
    unsafe_lock = unsafe_parent / "migration.lock"
    unsafe_lock.write_bytes(b"")
    unsafe_lock.chmod(0o644)
    with pytest.raises(migration.MigrationError, match="migration_lock"):
        migration.MigrationLock(unsafe_lock)

    parent = tmp_path / "locks"
    lock = parent / "migration.lock"
    guard = migration.MigrationLock(lock)
    original = tmp_path / "locks-original"
    parent.rename(original)
    redirected = tmp_path / "redirected-locks"
    redirected.mkdir(mode=0o700)
    parent.symlink_to(redirected, target_is_directory=True)
    with pytest.raises(migration.MigrationError, match="migration_lock"):
        with guard:
            pass
    assert list(redirected.iterdir()) == []


def test_manual_block_and_redirect_invariants_are_mandatory(tmp_path):
    manifest = _attested_manifest()
    authority = FakeAuthority(manifest)
    original_request = authority.request

    def request(operation, payload):
        response = original_request(operation, payload)
        if (
            operation == "plan_primitive"
            and payload["phase"] == "redirected"
            and payload["primitive_index"] == 0
        ):
            response = copy.deepcopy(response)
            response["receipt"]["after_domain_sha256"] = "0" * 64
        return response

    authority.request = request
    with pytest.raises(migration.MigrationError, match="authority_"):
        _run_reconciler(
            migration.Reconciler(
                manifest,
                authority,
                _ledger(tmp_path / "evidence"),
                FakeSourceGate(),
            )
        )
    assert authority.release_count == 0


def test_provider_integration_future_task00d_provider_protocol_and_identity():
    raw = os.environ.get("MARDI_AUTHORITY_BINARY")
    if not raw:
        pytest.skip("post-00D provider gate requires MARDI_AUTHORITY_BINARY")
    binary = Path(raw)
    assert binary.is_absolute(), "MARDI_AUTHORITY_BINARY must be absolute"
    authority = migration.SubprocessAuthority(binary)
    identity = migration._identity(authority)
    assert set(identity) == {
        "backend_mode",
        "database_identity",
        "project_identity",
        "repository_identity",
        "core_schema_fingerprint",
        "full_schema_fingerprint",
        "state_root",
    }
    assert all(isinstance(value, str) and value for value in identity.values())
