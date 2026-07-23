"""D9: git is the only tracker transport, with explicit sync rules.

A tracker write is: take the D8 lock, ``git pull`` (fast-forward), import the
committed JSONL if it changed, apply the semantic operation to bd, export,
commit, and push. If the push is rejected, take the remote version of the
JSONL, re-import, re-apply the operation, re-export, and push once more —
the generated JSONL is never hand-merged (on conflict the remote wins, then
we re-apply). Operations are semantic (claim X, record verdict on Y), so a
re-apply after a sync either succeeds or fails cleanly ("already claimed").

The loop batches one export-commit-push per iteration via ``batch=True``; a
single command commits per command (the default).
"""

import os
import subprocess
from pathlib import Path

from agentic.bd import BdError, bd_export, bd_import

JSONL_REL = ".beads/issues.jsonl"


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def repo_root(cwd):
    proc = _git(["rev-parse", "--show-toplevel"], cwd)
    if proc.returncode != 0:
        raise BdError("agentic write commands must run inside a git repository")
    return Path(proc.stdout.strip())


def _current_branch(root):
    proc = _git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    return proc.stdout.strip() if proc.returncode == 0 else "HEAD"


def _has_upstream(root):
    return (
        _git(
            ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], root
        ).returncode
        == 0
    )


def _import_committed(root, allow_stale=False):
    jsonl = root / JSONL_REL
    if jsonl.exists():
        bd_import(str(jsonl), cwd=str(root), allow_stale=allow_stale)


def _pull_ff(root):
    """Best-effort fast-forward pull; a diverged history is left for the
    push-rejection retry path to reconcile (take-remote-then-reapply)."""
    if not _has_upstream(root):
        return
    _git(["fetch", "--quiet"], root)
    branch = _current_branch(root)
    _git(["merge", "--ff-only", "--quiet", f"origin/{branch}"], root)


def _export_commit(root):
    """Export bd to the JSONL and commit it; return True if a commit was made."""
    bd_export(str(root / JSONL_REL), cwd=str(root))
    _git(["add", JSONL_REL], root)
    if _git(["diff", "--cached", "--quiet"], root).returncode == 0:
        return False  # nothing changed -> no empty commit
    commit = _git(["commit", "-q", "-m", "drain: tracker write"], root)
    if commit.returncode != 0:
        raise BdError(f"tracker commit failed: {commit.stderr.strip()}")
    return True


def _take_remote(root):
    """Discard local tracker commits, adopt the remote JSONL, re-import it."""
    branch = _current_branch(root)
    _git(["fetch", "--quiet"], root)
    reset = _git(["reset", "--hard", f"origin/{branch}"], root)
    if reset.returncode != 0:
        raise BdError(f"could not adopt remote tracker state: {reset.stderr.strip()}")
    # Force the remote snapshot in, overriding our rejected local write, so the
    # semantic re-apply runs against the peer's state (D9 take-remote).
    _import_committed(root, allow_stale=True)


def sync_write(cwd, apply_fn, *, batch=False):
    """Run ``apply_fn`` under the D8 lock and the D9 sync sequence.

    ``apply_fn`` performs the semantic bd operation and returns any value the
    caller wants back. With ``batch=False`` (single command) the JSONL is
    exported, committed, and pushed. With ``batch=True`` the caller owns the
    export-commit-push (the loop's per-iteration batch).
    """
    # Import here to avoid a circular import at module load.
    from agentic.lock import RepoLock

    root = repo_root(cwd)
    with RepoLock(root):
        _pull_ff(root)
        # Reflect the committed transport into bd before applying, so a write
        # made against a JSONL a peer just advanced sees the current state.
        _import_committed(root)
        result = apply_fn(root)

        if batch:
            return result

        _export_commit(root)
        if _has_upstream(root):
            _push_with_retry(root, apply_fn)
        return result


def _push_with_retry(root, apply_fn):
    branch = _current_branch(root)
    first = _git(["push", "--quiet", "origin", f"HEAD:{branch}"], root)
    if first.returncode == 0:
        return
    # Rejected (a peer pushed first): take remote, re-apply once, push again.
    _take_remote(root)
    apply_fn(root)  # semantic re-apply — succeeds or raises cleanly
    _export_commit(root)
    second = _git(["push", "--quiet", "origin", f"HEAD:{branch}"], root)
    if second.returncode != 0:
        raise BdError(f"tracker push failed after re-apply: {second.stderr.strip()}")
