"""Thin wrapper around the pinned ``bd`` (beads) binary.

Every agentic command that touches the tracker goes through these helpers;
nothing else in the toolkit shells out to ``bd`` directly. The version pin
(SPEC R-V) is enforced here: a MISSING bd yields a clean install-command
error, never a confusing pin mismatch, and a wrong version yields the pin
plus an upgrade pointer.
"""

import json
import os
import re
import shutil
import subprocess

# SPEC pins bd 1.1.0. The brew bottle is the clean install path on this host
# (bd is not buildable from source here — go install fails on ICU headers).
PINNED_VERSION = "1.1.0"
INSTALL_CMD = "brew install beads"
UPGRADE_CMD = "brew upgrade beads"

_VERSION_RE = re.compile(r"(\d+\.\d+\.\d+)")


class BdError(Exception):
    """A bd problem surfaced to the user with a clean, actionable message."""


def bd_which():
    """Absolute path to ``bd`` on PATH, or ``None`` if it is not installed."""
    return shutil.which("bd")


def _missing_error():
    return BdError(
        f"bd not found on PATH. Install the pinned version "
        f"({PINNED_VERSION}): {INSTALL_CMD}"
    )


def installed_version():
    """Return the installed bd version string (e.g. ``1.1.0``)."""
    exe = bd_which()
    if exe is None:
        raise _missing_error()
    proc = subprocess.run([exe, "version"], capture_output=True, text=True)
    text = proc.stdout or proc.stderr or ""
    match = _VERSION_RE.search(text)
    if not match:
        raise BdError(f"could not parse a bd version from: {text!r}")
    return match.group(1)


def check_pin():
    """Verify bd is present and exactly the pinned version.

    Missing bd -> clean install-command error (never a pin mismatch).
    Wrong version -> the pin plus an upgrade pointer.
    """
    if bd_which() is None:
        raise _missing_error()
    version = installed_version()
    if version != PINNED_VERSION:
        raise BdError(
            f"bd version {version} found, but {PINNED_VERSION} is pinned. "
            f"Upgrade with: {UPGRADE_CMD}"
        )
    return version


def _run(args, cwd=None):
    """Run ``bd <args>`` non-interactively; raise BdError on failure."""
    exe = bd_which()
    if exe is None:
        raise _missing_error()
    env = {**os.environ, "BD_NON_INTERACTIVE": "1"}
    proc = subprocess.run(
        [exe, *args], cwd=cwd, capture_output=True, text=True, env=env
    )
    if proc.returncode != 0:
        detail = (proc.stderr.strip() or proc.stdout.strip() or "").splitlines()
        msg = detail[-1] if detail else f"exit {proc.returncode}"
        raise BdError(f"bd {' '.join(args)} failed: {msg}")
    return proc.stdout


def bd_init(cwd):
    """Initialize a fresh bd tracker in ``cwd`` (creates the Dolt store)."""
    return _run(["init", "--non-interactive"], cwd=cwd)


def bd_import(path, cwd=None, allow_stale=False):
    """Import issues from a JSONL file (upsert; preserves issue IDs).

    By default bd only rewrites a local issue when the imported row is strictly
    newer (last-write-wins). ``allow_stale=True`` forces every row in, even
    over newer local state — D9's "on conflict, take the remote version" when
    a rejected push means our local write must yield to the peer's.
    """
    args = ["import"]
    if allow_stale:
        args.append("--allow-stale")
    args.append(str(path))
    return _run(args, cwd=cwd)


def bd_export(path=None, cwd=None):
    """Export all issues to JSONL — to ``path`` if given, else return stdout."""
    if path is None:
        return _run(["export"], cwd=cwd)
    _run(["export", "-o", str(path)], cwd=cwd)
    return None


def bd_list(cwd=None):
    """Return the tracker's issues as a list of dicts (``bd list --json``)."""
    out = _run(["list", "--json"], cwd=cwd)
    return json.loads(out or "[]")


def bd_claim(issue_id, cwd=None):
    """Atomically claim ``issue_id`` (assignee=actor, status=in_progress).

    Idempotent if the current actor already holds it; raises BdError with bd's
    "already claimed" message if another actor holds it.
    """
    return _run(["update", issue_id, "--claim"], cwd=cwd)


def bd_set_status(issue_id, status, cwd=None):
    """Set ``issue_id``'s status (e.g. closed, blocked, deferred)."""
    return _run(["update", issue_id, "--status", status], cwd=cwd)


def bd_metadata(issue_id, cwd=None):
    """The issue's current metadata dict (empty if none / not found)."""
    out = _run(["show", issue_id, "--json"], cwd=cwd)
    data = json.loads(out or "[]")
    if isinstance(data, list):
        data = data[0] if data else {}
    return data.get("metadata") or {}


def bd_set_metadata(issue_id, pairs, cwd=None):
    """Merge ``pairs`` (a dict of str->JSON-encodable) into an issue's
    metadata, preserving existing keys (touch/rigor) AND nested structure.

    ``--set-metadata`` stores each value as a bare string, so nested objects
    would round-trip as text; instead we read the current metadata, merge in
    Python, and write the whole map back with ``--metadata`` (which parses
    JSON), keeping typed values typed.
    """
    merged = {**bd_metadata(issue_id, cwd=cwd), **pairs}
    return _run(["update", issue_id, "--metadata", json.dumps(merged)], cwd=cwd)


def bd_create(title, deps=None, description=None, priority=None, cwd=None):
    """Create an issue and return its new id (``--silent`` prints id only).

    ``deps`` are ``type:id`` strings (e.g. ``discovered-from:bd-4``).
    """
    args = ["create", title, "--silent"]
    if deps:
        args += ["--deps", ",".join(deps)]
    if description:
        args += ["--description", description]
    if priority is not None:
        args += ["--priority", str(priority)]
    out = _run(args, cwd=cwd)
    return (out or "").strip().splitlines()[-1].strip() if out else ""
