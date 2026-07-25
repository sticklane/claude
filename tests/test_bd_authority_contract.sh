#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pytest \
  .claude/skills/workboard/test_workboard.py::TestBdTaskAuthority::test_bd_status_and_dependencies_win_over_frozen_markdown_headers \
  .claude/skills/workboard/test_workboard.py::TestBdBlockerDetailAuthority \
  .claude/skills/workboard/test_workboard.py::TestBdTrackerSnapshot \
  .claude/skills/workboard/test_workboard.py::TestNeedsAnswerInbox::test_uninitialized_tracker_points_to_initialization_not_registration \
  .claude/skills/workboard/test_workboard.py::TestNeedsAnswerInbox::test_tracker_read_error_points_to_retry_not_registration \
  -q

# Build and drain are prose orchestrators, so their deepest executable routing
# boundary is the shared agentic claim/ready CLI. Deliberately contradict
# frozen markdown in both directions and prove the bd state wins.
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from agentic import bd

repo_root = Path.cwd()
with tempfile.TemporaryDirectory() as tmp:
    store = Path(tmp) / "authority-fixture"
    store.mkdir()
    subprocess.run(["git", "init", "-q", "."], cwd=store, check=True)
    subprocess.run(
        ["git", "config", "user.email", "authority@example.com"],
        cwd=store,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Authority fixture"],
        cwd=store,
        check=True,
    )
    bd.bd_init(str(store))

    tasks = store / "specs" / "demo" / "tasks"
    tasks.mkdir(parents=True)
    (store / "specs" / "demo" / "SPEC.md").write_text("# Demo\n")
    (tasks / "01-build.md").write_text("# Build\nStatus: done\n")
    (tasks / "02-drain-open.md").write_text("# Drain open\nStatus: done\n")
    (tasks / "03-drain-closed.md").write_text("# Drain closed\nStatus: pending\n")

    rows = [
        {
            "id": "fx-build",
            "title": "build target",
            "external_ref": "spec-task:specs/demo/tasks/01-build.md",
            "status": "open",
            "priority": 1,
            "issue_type": "task",
            "metadata": {"touch": ["src/build.py"]},
        },
        {
            "id": "fx-drain-open",
            "title": "drain target",
            "external_ref": "spec-task:specs/demo/tasks/02-drain-open.md",
            "status": "open",
            "priority": 1,
            "issue_type": "task",
            "metadata": {"touch": ["src/drain.py"]},
        },
        {
            "id": "fx-drain-closed",
            "title": "closed target",
            "external_ref": "spec-task:specs/demo/tasks/03-drain-closed.md",
            "status": "closed",
            "priority": 1,
            "issue_type": "task",
            "metadata": {"touch": ["src/closed.py"]},
        },
    ]
    seed = store / "seed.jsonl"
    seed.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    bd.bd_import(str(seed), cwd=str(store))

    env = {**os.environ, "PYTHONPATH": str(repo_root), "BD_ACTOR": "authority-test"}
    ready = subprocess.run(
        [sys.executable, "-m", "agentic", "ready", "--json"],
        cwd=store,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    ready_ids = {row["id"] for row in json.loads(ready.stdout)}
    assert "fx-drain-open" in ready_ids, ready.stdout
    assert "fx-drain-closed" not in ready_ids, ready.stdout

    claimed = subprocess.run(
        [sys.executable, "-m", "agentic", "claim", "fx-build"],
        cwd=store,
        env=env,
        capture_output=True,
        text=True,
    )
    assert claimed.returncode == 0, claimed.stderr
    current = json.loads(
        subprocess.run(
            ["bd", "--readonly", "show", "fx-build", "--json"],
            cwd=store,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )[0]
    assert current["status"] == "in_progress", current
    assert "Status: done" in (tasks / "01-build.md").read_text()

print("build/drain disagreement fixtures: bd wins")
PY

for file in \
  .claude/skills/build/SKILL.md \
  .claude/skills/drain/SKILL.md \
  .claude/skills/workboard/SKILL.md \
  .claude/skills/workboard/reference.md \
  .claude/skills/workflow-author/SKILL.md \
  .claude/skills/workflow-author/reference.md
do
  if grep -Eq 'mark (its |the )?`?Status:|flip(s|ping)? (task )?`?Status:|writes? .*`Status:|Status: (in-progress|done|blocked|deferred).*header|grep -l .Status: pending.' "$file"; then
    echo "live procedure still writes or advances markdown task status: $file" >&2
    exit 1
  fi
done

if grep -Eq 'STATUS_RE|DEPENDS_RE' .claude/skills/workboard/workboard.py; then
  echo "workboard still reads markdown status or dependencies" >&2
  exit 1
fi

if grep -Eq '^STATUS_RE|^DEPENDS_RE' .claude/skills/_shared/headers.py; then
  echo "shared live-header parser still exports task state authority" >&2
  exit 1
fi

grep -q 'bd is the only live authority' .claude/skills/build/SKILL.md
grep -q 'bd is the only live authority' .claude/skills/drain/SKILL.md

if grep -q 'HANDOFF\.md' .claude/skills/workboard/SKILL.md; then
  echo "workboard skill still treats HANDOFF.md as live handoff state" >&2
  exit 1
fi

python3 - <<'PY'
from pathlib import Path

text = Path(".claude/skills/workflow-author/reference.md").read_text()
queue_wave = text.split("## Template: queue-wave.js", 1)[1]
required = [
    "phase('settle')",
    "await pipeline(results",
    "Close bd issue ${r.issueId}",
    "Set bd issue ${r.issueId} to blocked",
    "Reopen bd issue ${r.issueId}",
]
missing = [token for token in required if token not in queue_wave]
assert not missing, f"queue-wave lacks awaited terminal tracker settlement: {missing}"
print("workflow queue-wave settlement contract: pass")
PY
