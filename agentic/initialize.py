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


def _controlled_bd_init(root):
    """Run ``bd init`` then undo its auto-commit, keeping the working tree.

    bd init writes and auto-commits AGENTS.md/CLAUDE.md/settings into the host
    repo; we reset that single commit so those files are curated, never
    force-committed.
    """
    prior = _git(["rev-parse", "HEAD"], root)
    had_head = prior.returncode == 0
    bd.bd_init(str(root))
    if had_head:
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
