#!/usr/bin/env bash
# handoff-resume: SessionStart hook that auto-resumes from a HANDOFF.md left
# by /handoff. /clear (and any fresh session start) cannot itself "resume" —
# clearing ends the context that would carry the resume instruction, so no
# skill can do both in one action. This hook is the actual mechanism: it
# fires the moment a NEW context begins (after /clear, or a fresh launch),
# so the only manual step left is /clear (or starting a new session) itself.
#
# Silent (empty stdout, exit 0) when no HANDOFF.md is found — a repo with no
# in-flight handoff must see zero behavior change.
#
# Search: any file literally named HANDOFF.md under the project root
# (CLAUDE_PROJECT_DIR, else cwd), skipping .git and any worktrees directory
# — /handoff places it next to the active task/spec file or at
# .claude/HANDOFF.md, so a fixed single path is not enough.
set -u

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
[ -d "$root" ] || exit 0

# -not -path filters keep this cheap and out of throwaway worktree copies
# (this toolkit's own drain workers create many under .claude/worktrees/)
# and test-fixture trees (a repo's own test suite may plant a HANDOFF.md
# double to test something else, e.g. this toolkit's own
# tests/fixtures/workboard/demo-repo/HANDOFF.md — a real false positive
# found live while testing this hook, not a hypothetical one).
found="$(find "$root" \
  -type d \( -name .git -o -path '*/.claude/worktrees/*' -o -name node_modules \
             -o -name fixtures -o -name test_fixtures \) -prune -o \
  -type f -name 'HANDOFF.md' -print 2>/dev/null)"

[ -n "$found" ] || exit 0

count="$(printf '%s\n' "$found" | grep -c .)"

if [ "$count" -eq 1 ]; then
  cat <<EOF
A handoff file exists at $found from a previous session. Read it and continue from where that session left off — do not re-derive state already captured there.
EOF
else
  cat <<EOF
Multiple handoff files exist in this repo — read the one matching the task you're resuming (or ask which, if unclear) and continue from where that session left off:
$found
EOF
fi

exit 0
