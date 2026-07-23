"""``agentic verdict <id> --file <path>`` — record a worker's result (SPEC S5, D7).

Validates the worker's JSON against ``agentic/schema/verdict.json`` (a JSON
Schema: DONE/BLOCKED/DEFERRED, a typed Unblock required for BLOCKED, a typed
Discovered list), then — under the D8 lock and D9 sync sequence — updates the
task in bd and files each discovered item as a new issue linked
``discovered-from`` the origin. A missing or schema-invalid file records
nothing and fails, leaving the task untouched (the loop returns it to ready).

The status mapping: DONE -> bd ``closed``; BLOCKED -> bd ``blocked`` with the
typed unblock stored in metadata; DEFERRED -> bd ``deferred`` with the open
questions stored in metadata.
"""

import json
import os
from pathlib import Path

import jsonschema

from agentic import bd
from agentic.bd import BdError
from agentic.sync import sync_write

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "verdict.json"

_STATUS_TO_BD = {"DONE": "closed", "BLOCKED": "blocked", "DEFERRED": "deferred"}


def _schema():
    return json.loads(SCHEMA_PATH.read_text())


def validation_errors(doc):
    """Return a list of human-readable schema-violation messages ([] if valid)."""
    validator = jsonschema.Draft202012Validator(_schema())
    return [e.message for e in sorted(validator.iter_errors(doc), key=str)]


def _existing_discovered_titles(root, issue_id):
    """Titles already filed discovered-from ``issue_id`` (so a D9 re-apply on
    a push rejection does not double-file the same discovered work)."""
    export = bd.bd_export(cwd=str(root)) or ""
    titles = set()
    for line in export.splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        for dep in obj.get("dependencies") or []:
            if dep.get("type") == "discovered-from" and (
                dep.get("depends_on_id") == issue_id
            ):
                titles.add(obj.get("title", ""))
    return titles


def _apply_verdict(root, issue_id, doc):
    status = doc["status"]
    bd.bd_set_status(issue_id, _STATUS_TO_BD[status], cwd=str(root))

    meta = {"verdict": status, "verdict_summary": doc["summary"]}
    if "unblock" in doc:
        meta["unblock"] = doc["unblock"]
    if "deferred_questions" in doc:
        meta["deferred_questions"] = doc["deferred_questions"]
    bd.bd_set_metadata(issue_id, meta, cwd=str(root))

    already = _existing_discovered_titles(root, issue_id)
    for item in doc.get("discovered") or []:
        if item["title"] in already:
            continue  # idempotent: this discovered item is already filed
        bd.bd_create(
            item["title"],
            deps=[f"discovered-from:{issue_id}"],
            description=item.get("description"),
            priority=item.get("priority"),
            cwd=str(root),
        )
        already.add(item["title"])


def record(cwd, issue_id, file_path):
    """Validate the verdict file and apply it as a tracker write.

    Raises BdError on a missing or schema-invalid file (nothing is written).
    """
    path = Path(file_path)
    if not path.exists():
        raise BdError(f"verdict file not found: {file_path}")
    try:
        doc = json.loads(path.read_text())
    except ValueError as exc:
        raise BdError(f"verdict file is not valid JSON: {exc}")

    errors = validation_errors(doc)
    if errors:
        raise BdError(
            "verdict file failed schema validation:\n  - " + "\n  - ".join(errors)
        )

    def _apply(root):
        _apply_verdict(root, issue_id, doc)

    sync_write(cwd, _apply)


def run(args):
    record(os.getcwd(), args.id, args.file)
    print(f"recorded verdict for {args.id}")
    return 0
