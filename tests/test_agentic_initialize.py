"""agentic-vtp: `_controlled_bd_init` must not blindly reset `HEAD~1`.

`bd init` auto-commits into the host repo; `_controlled_bd_init` resets that
single commit so the files land as uncommitted working-tree changes for
review. The reset assumed the commit it's undoing is always exactly `bd
init`'s own fresh commit sitting on the pre-init HEAD — false whenever
something else commits in the same window (a concurrent process, a hook):
the blind `git reset HEAD~1` then un-commits that other, real work instead
(agentic-vtp, discovered during the ~/automation cutover). A re-init that
legitimately creates no new commit (rebuilding a deleted Dolt store over an
already-committed `.beads`) must stay a no-op, not an error.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agentic import bd, initialize  # noqa: E402
from agentic.bd import BdError  # noqa: E402
from agentic.initialize import _BD_INIT_SUBJECT  # noqa: E402

requires_bd = pytest.mark.skipif(
    bd.bd_which() is None, reason="bd not installed on PATH"
)


def _git(args, cwd):
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


def _repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(["init", "-q", "."], root)
    _git(["config", "user.email", "t@e.com"], root)
    _git(["config", "user.name", "t"], root)
    (root / "README.md").write_text("seed\n")
    _git(["add", "README.md"], root)
    _git(["commit", "-q", "-m", "seed"], root)
    return root


@requires_bd
def test_controlled_bd_init_resets_its_own_commit(tmp_path):
    root = _repo(tmp_path)
    prior = _git(["rev-parse", "HEAD"], root)

    initialize._controlled_bd_init(root)

    assert _git(["rev-parse", "HEAD"], root) == prior
    assert (root / ".beads").exists()


@requires_bd
def test_controlled_bd_init_is_a_noop_when_bd_init_makes_no_new_commit(
    tmp_path, monkeypatch
):
    """Re-init over an already-committed .beads (rebuilding a deleted Dolt
    store) legitimately commits nothing new -- must not touch HEAD."""
    root = _repo(tmp_path)
    (root / "real_work.txt").write_text("important\n")
    _git(["add", "real_work.txt"], root)
    _git(["commit", "-q", "-m", "real already-pushed work"], root)
    prior = _git(["rev-parse", "HEAD"], root)

    monkeypatch.setattr(initialize.bd, "bd_init", lambda cwd: None)

    initialize._controlled_bd_init(root)  # must not raise

    assert _git(["rev-parse", "HEAD"], root) == prior
    assert "real already-pushed work" in _git(["log", "--format=%s"], root).splitlines()


@requires_bd
def test_controlled_bd_init_aborts_when_another_commit_lands_first(
    tmp_path, monkeypatch
):
    """The real incident: something else commits between the pre-init HEAD
    capture and bd's own auto-commit, so bd's commit lands on top of it
    instead of directly on the pre-init HEAD."""
    root = _repo(tmp_path)
    prior = _git(["rev-parse", "HEAD"], root)
    real_bd_init = bd.bd_init

    def racing_bd_init(cwd):
        (root / "unrelated.txt").write_text("real work\n")
        _git(["add", "unrelated.txt"], root)
        _git(["commit", "-q", "-m", "unrelated already-pushed work"], root)
        return real_bd_init(cwd)

    monkeypatch.setattr(initialize.bd, "bd_init", racing_bd_init)

    with pytest.raises(BdError):
        initialize._controlled_bd_init(root)

    # HEAD must be untouched -- both the unrelated commit and bd's own
    # commit stay exactly as they landed, for a human to sort out.
    assert _git(["rev-parse", "HEAD"], root) != prior
    log = _git(["log", "--format=%s"], root)
    assert "unrelated already-pushed work" in log.splitlines()
    assert _BD_INIT_SUBJECT in log.splitlines()
