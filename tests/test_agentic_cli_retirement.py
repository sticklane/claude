"""The remaining pre-2.0 compatibility aliases are exact and non-mutating."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

DIAGNOSTICS = {
    "compose": (
        "agentic compose: retired by the native-orchestration pivot; "
        "use /work, /build, or /drain"
    ),
    "inbox": "agentic inbox: retired; use bd ready and bd human list",
    "demote": "agentic demote: retired; use bd update <id> --status deferred",
    "shadow-sync": (
        "agentic shadow-sync: retired; task state lives in bd; "
        "use register-spec only for new tasks"
    ),
}


def _agentic(cwd, *args):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "agentic", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def test_retired_aliases_are_hidden_from_help_and_parser_choices(tmp_path):
    result = _agentic(tmp_path, "--help")
    assert result.returncode == 0
    for name in DIAGNOSTICS:
        assert name not in result.stdout
    assert "register-spec" in result.stdout

    from agentic.cli import build_parser

    subcommands = next(
        action.choices
        for action in build_parser()._actions
        if getattr(action, "choices", None)
    )
    assert not DIAGNOSTICS.keys() & subcommands.keys()


@pytest.mark.parametrize("name,message", DIAGNOSTICS.items())
def test_exact_retired_alias_diagnostic_is_exit_2(tmp_path, name, message):
    result = _agentic(tmp_path, name)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == message + "\n"


def test_retired_aliases_do_not_mutate_markdown_or_create_tracker_state(tmp_path):
    task = tmp_path / "specs" / "demo" / "tasks" / "01-task.md"
    task.parent.mkdir(parents=True)
    task.write_text("Status: pending\n", encoding="utf-8")
    before = task.read_bytes()

    for name in DIAGNOSTICS:
        assert _agentic(tmp_path, name).returncode == 2

    assert task.read_bytes() == before
    assert not (tmp_path / ".beads").exists()


def test_only_exact_retired_names_receive_compatibility_diagnostics(tmp_path):
    result = _agentic(tmp_path, "shadow-syn")
    assert result.returncode == 2
    assert "invalid choice" in result.stderr
    assert DIAGNOSTICS["shadow-sync"] not in result.stderr
