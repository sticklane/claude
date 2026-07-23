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


def bd_import(path, cwd=None):
    """Import issues from a JSONL file (upsert; preserves issue IDs)."""
    return _run(["import", str(path)], cwd=cwd)


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
