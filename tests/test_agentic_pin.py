"""SPEC R-V: the agentic bd wrapper is version-pinned.

`agentic init` must refuse to run against any bd version but the pin, with an
upgrade pointer, and must give a MISSING bd a clean install-command error
rather than a confusing pin mismatch.

These drive `agentic init` through a subprocess so PATH manipulation (a fake
bd, or no bd at all) is exercised exactly as a real invocation would see it.
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_fake_bd(directory, version_line):
    fake = directory / "bd"
    fake.write_text(f'#!/usr/bin/env bash\necho "{version_line}"\n')
    fake.chmod(0o755)
    return fake


def _run_init(tmp_path, path_value):
    """Run `agentic init` in a scratch git repo with a controlled PATH."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "."], cwd=repo, check=True)
    env = dict(os.environ)
    env["PATH"] = path_value
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "agentic", "init"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )


def test_wrong_version_refuses_with_pin_and_upgrade_pointer(tmp_path):
    fake_dir = tmp_path / "fakebin"
    fake_dir.mkdir()
    _write_fake_bd(fake_dir, "bd version 9.9.9 (fake)")
    # Fake bd wins over any real bd on PATH.
    path_value = f"{fake_dir}:{os.environ.get('PATH', '')}"

    result = _run_init(tmp_path, path_value)

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "1.1.0" in combined  # names the pin
    assert "9.9.9" in combined  # names what was found
    assert "brew upgrade beads" in combined  # upgrade pointer
    # A wrong version is NOT reported as a missing-install problem.
    assert "not found" not in combined.lower()


def test_missing_bd_reports_install_command(tmp_path):
    # PATH with no bd at all -> clean install-command error, not a pin mismatch.
    empty = tmp_path / "emptybin"
    empty.mkdir()

    result = _run_init(tmp_path, str(empty))

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "not found" in combined.lower()
    assert "brew install beads" in combined  # install pointer
    # Must not masquerade as a version-mismatch / upgrade prompt.
    assert "brew upgrade beads" not in combined
