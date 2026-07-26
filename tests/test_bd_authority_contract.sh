#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pytest \
  .claude/skills/workboard/test_workboard.py::TestBdTaskAuthority::test_bd_status_and_dependencies_win_over_frozen_markdown_headers \
  -q

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
