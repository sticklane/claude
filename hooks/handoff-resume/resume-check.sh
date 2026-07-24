#!/usr/bin/env bash
# handoff-resume: SessionStart hook that flags an open handoff issue left in
# bd by /handoff. /clear (and any fresh session start) cannot itself
# "resume" — clearing ends the context that would carry the resume
# instruction, so no skill can do both in one action. This hook is the flag:
# it fires the moment a NEW context begins (after /clear, or a fresh launch)
# and names the resume-handoff skill as the deterministic next step, since
# prose telling the session to "read it and continue" is advisory context
# that a live user message asking for something else correctly outranks
# (CLAUDE.md's precedence order) — naming a skill by name is what actually
# gets invoked consistently.
#
# Silent (empty stdout, exit 0) whenever no open handoff-labeled issue is
# found — including when bd or jq is missing from PATH and when the project
# has no .beads store at all. This hook is wired globally per user and fires
# in every repo, most of which carry no bd store, so a repo with no
# in-flight handoff must see zero behavior change (the same tolerance
# convention hooks/bd-compliance/check.sh follows: a missing binary is a
# reason to skip, never a reason to speak up).
set -u

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
[ -d "$root" ] || exit 0

command -v bd >/dev/null 2>&1 || exit 0
command -v jq >/dev/null 2>&1 || exit 0

open_handoffs="$(cd "$root" && bd list --label handoff --status=open --json 2>/dev/null)"
found="$(printf '%s' "$open_handoffs" | jq -r '.[]? | "\(.id) — \(.title)"' 2>/dev/null)"

[ -n "$found" ] || exit 0

count="$(printf '%s\n' "$found" | grep -c .)"

if [ "$count" -eq 1 ]; then
  cat <<EOF
An open handoff issue is parked in bd from a previous session: $found. Run the resume-handoff skill to read it and continue from where that session left off — do not re-derive state already captured there, and do not read-and-continue ad hoc.
EOF
else
  cat <<EOF
Multiple open handoff issues are parked in bd — run the resume-handoff skill; it will ask which one matches the task you're resuming (or continue from where that session left off once you tell it):
$found
EOF
fi

exit 0
