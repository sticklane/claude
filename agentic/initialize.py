"""``agentic init``: curated bd bootstrap.

A fresh clone runs ``git clone <url> && agentic init`` and has the whole
tracker (SPEC R-B): the committed ``.beads/issues.jsonl`` is imported into a
rebuilt Dolt store. The controlled init undoes ``bd init``'s auto-commit so
its side-effect files (AGENTS.md, CLAUDE.md, settings) are left for review
rather than force-committed into the host repo, and the interaction
telemetry is gitignored so it never dirties ``git status``.
"""

import os
import subprocess
from pathlib import Path

from agentic import bd
from agentic.bd import BdError

# Local-only telemetry bd writes on every command; gitignore so it never
# rides a commit or dirties status.
INTERACTIONS_PATH = ".beads/interactions.jsonl"


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def _repo_root(cwd):
    proc = _git(["rev-parse", "--show-toplevel"], cwd)
    if proc.returncode != 0:
        raise BdError("agentic init must run inside a git repository")
    return Path(proc.stdout.strip())


def _ensure_gitignore(root):
    gi = root / ".gitignore"
    existing = gi.read_text().splitlines() if gi.exists() else []
    if INTERACTIONS_PATH in [line.strip() for line in existing]:
        return
    with gi.open("a") as handle:
        if existing and existing[-1].strip():
            handle.write("\n")
        handle.write("# bd interaction telemetry (local-only, never committed)\n")
        handle.write(INTERACTIONS_PATH + "\n")


# bd's own auto-commit always carries this exact subject line (verified
# against bd 1.1.0's `bd init`).
_BD_INIT_SUBJECT = "bd init: initialize beads issue tracking"


def _controlled_bd_init(root):
    """Run ``bd init`` then undo its auto-commit, keeping the working tree.

    bd init writes and auto-commits AGENTS.md/CLAUDE.md/settings into the host
    repo; we reset that single commit so those files are curated, never
    force-committed. A re-init over an already-committed ``.beads`` (e.g.
    rebuilding a deleted Dolt store) is idempotent and legitimately creates
    no new commit -- that's a no-op, not an error. Only a genuine advance of
    HEAD gets reset, and only after verifying it's actually bd's own commit
    sitting directly on the pre-init HEAD -- abort loudly instead of
    resetting blind if something else committed in the same window (a
    concurrent process, a hook), since a blind reset would silently
    un-commit that other work too (agentic-vtp).
    """
    prior = _git(["rev-parse", "HEAD"], root)
    had_head = prior.returncode == 0
    bd.bd_init(str(root))
    after = _git(["rev-parse", "HEAD"], root)
    if had_head:
        if after.returncode != 0 or after.stdout.strip() == prior.stdout.strip():
            return  # bd init committed nothing new -- nothing to undo.
        subject = _git(["log", "-1", "--format=%s"], root).stdout.strip()
        parent = _git(["rev-parse", "HEAD~1"], root)
        if subject != _BD_INIT_SUBJECT or parent.stdout.strip() != prior.stdout.strip():
            raise BdError(
                f"agentic init: HEAD after bd init ({after.stdout.strip()[:12]}, "
                f"subject {subject!r}) is not bd's own commit landing directly "
                "on the pre-init HEAD; refusing to reset HEAD~1 blind -- "
                "resolve manually before retrying"
            )
        _git(["reset", "-q", "HEAD~1"], root)
    else:
        # bd's commit is the root commit: drop the ref and clear the index.
        _git(["update-ref", "-d", "HEAD"], root)
        _git(["reset", "-q"], root)


def run(_args=None):
    cwd = os.getcwd()
    bd.check_pin()  # raises BdError on missing/wrong version
    root = _repo_root(cwd)
    beads = root / ".beads"
    jsonl = beads / "issues.jsonl"

    dolt_present = (beads / "embeddeddolt").is_dir()
    if not dolt_present:
        _controlled_bd_init(root)

    imported = None
    if jsonl.exists():
        bd.bd_import(str(jsonl), cwd=str(root))
        imported = len(bd.bd_list(cwd=str(root)))

    _ensure_gitignore(root)

    if imported is not None:
        print(f"agentic init: tracker ready, {imported} issue(s) imported")
    else:
        print("agentic init: tracker initialized (no committed JSONL to import)")
    return 0
