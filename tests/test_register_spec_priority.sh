#!/usr/bin/env bash
# Create-only registration reads the authored Priority header (bd agentic-7t1w).
#
# CLAUDE.md lists Priority among the fields read at create-only registration,
# but agentic/register.py passed no priority to bd, so every registered task
# landed at bd's default P2 and /breakdown's priority rubric was discarded.
# Registration stays create-only: an already-registered issue keeps whatever
# priority it carries, however the task file was later re-authored.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTIC="$REPO_ROOT/bin/agentic"

if ! command -v bd >/dev/null 2>&1; then
  echo "test_register_spec_priority.sh: bd not on PATH, skipped"
  exit 0
fi

pass=0
fail=0

expect_eq() { # expect_eq <description> <expected> <actual>
  if [ "$2" = "$3" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $1 (expected '$2', got '$3')" >&2
  fi
}

T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
cd "$T" || exit 1

git init -q .
git config user.name test
git config user.email test@example.com
BD_NON_INTERACTIVE=1 bd init --prefix rp >/dev/null 2>&1
mkdir -p specs/demo/tasks

write_task() { # write_task <file-stem> <priority-header-or-empty>
  local stem="$1" header="$2" path="specs/demo/tasks/$1.md"
  {
    printf 'Depends on: none\n'
    if [ -n "$header" ]; then printf '%s\n' "$header"; fi
    printf 'Budget: 5 turns\nTouch: src/%s.py\n\n' "$stem"
    printf '# Task %s\n\n## Goal\n\nExercise priority registration for %s.\n' \
      "$stem" "$stem"
  } >"$path"
}

# One task per authored level, plus one with no Priority header at all.
write_task 01-p0 'Priority: P0'
write_task 02-p1 'Priority: P1'
write_task 03-p2 'Priority: P2'
write_task 04-p3 'Priority: P3'
write_task 05-absent ''

field_of() { # field_of <task-file-stem> <field>
  bd export -o "$T/export.jsonl" >/dev/null 2>&1
  python3 - "$T/export.jsonl" "spec-task:specs/demo/tasks/$1.md" "$2" <<'PY'
import json
import sys

path, ref, field = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, encoding="utf-8") as handle:
    for line in handle:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("external_ref") == ref:
            print(row.get(field))
            break
    else:
        print("MISSING")
PY
}

"$AGENTIC" register-spec specs/demo >/dev/null 2>&1

expect_eq "authored P0 registers at bd priority 0" 0 "$(field_of 01-p0 priority)"
expect_eq "authored P1 registers at bd priority 1" 1 "$(field_of 02-p1 priority)"
expect_eq "authored P2 registers at bd priority 2" 2 "$(field_of 03-p2 priority)"
expect_eq "authored P3 registers at bd priority 3" 3 "$(field_of 04-p3 priority)"
expect_eq "an absent Priority header registers at bd priority 2" \
  2 "$(field_of 05-absent priority)"

# Create-only boundary: registration never syncs an existing issue's priority.
existing_id="$(field_of 01-p0 id)"
bd update "$existing_id" --priority 3 >/dev/null 2>&1
expect_eq "the existing issue now differs from its authored header" \
  3 "$(field_of 01-p0 priority)"

"$AGENTIC" register-spec specs/demo >/dev/null 2>&1

expect_eq "re-registration leaves the existing bd priority unchanged" \
  3 "$(field_of 01-p0 priority)"
expect_eq "re-registration reuses the existing issue" \
  "$existing_id" "$(field_of 01-p0 id)"

echo "test_register_spec_priority.sh: ${pass} passed, ${fail} failed"
[ "$fail" -eq 0 ]
