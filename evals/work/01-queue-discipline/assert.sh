#!/usr/bin/env bash
# Grades the /work queue-discipline run. CWD is $EVAL_DIR; exit 0 = pass,
# non-zero with output explaining what failed. Grades the artifacts a
# compliant /work session must produce, per .claude/skills/work/SKILL.md:
#   (a) a claim happened before implementation work (session.log ordering)
#   (b) the issue is closed on done, and unclaimed (session-claims cleared)
#   (c) the authored fan-out script carries a cheap-tier model option
# Structured checks via python3 where the artifact is JSON (bd's own
# convention, e.g. evals/gate/01-happy-path/assert.sh); a proximity grep
# for the workflow file, matching the task's own "model near haiku"
# convention rather than an exact-string match.
#
# bash 3.2 compatible (macOS system bash): no `declare -A` or bash-4 syntax.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

[ -f .beads/seed-id ] || fail ".beads/seed-id is missing — setup.sh did not seed an issue"
id="$(cat .beads/seed-id)"
[ -n "$id" ] || fail ".beads/seed-id is empty"

# --- (a) claim happened before implementation work -------------------------
log=session.log
[ -s "$log" ] || fail "$log is missing or empty — no session transcript to grade"

claim_line="$(grep -nF "session: claiming $id" "$log" | head -1 | cut -d: -f1)"
impl_line="$(grep -n '^session: implementing' "$log" | head -1 | cut -d: -f1)"
close_line="$(grep -nF "session: closing $id" "$log" | head -1 | cut -d: -f1)"
[ -n "$claim_line" ] || fail "no 'claiming $id' line found in $log — claim never happened"
[ -n "$impl_line" ] || fail "no 'implementing' line found in $log — no implementation step recorded"
[ -n "$close_line" ] || fail "no 'closing $id' line found in $log — close never happened"
[ "$claim_line" -lt "$impl_line" ] \
  || fail "claim ($log:$claim_line) did not happen before implementation ($log:$impl_line)"
[ "$impl_line" -lt "$close_line" ] \
  || fail "implementation ($log:$impl_line) did not happen before close ($log:$close_line)"

# --- (b) closed on done, and unclaimed --------------------------------------
bd show "$id" --json > bd-show.json 2>/dev/null
[ -s bd-show.json ] || fail "bd show $id --json returned nothing"

python3 - bd-show.json "$id" <<'PY' || exit 1
import json, sys

path, issue_id = sys.argv[1], sys.argv[2]
try:
    data = json.load(open(path))
except Exception as exc:
    print(f"ASSERT FAIL: {path} is not valid JSON: {exc}", file=sys.stderr)
    sys.exit(1)

issue = data[0] if isinstance(data, list) else data
if issue.get("id") != issue_id:
    print(f"ASSERT FAIL: bd show returned id {issue.get('id')!r}, expected {issue_id!r}", file=sys.stderr)
    sys.exit(1)
if issue.get("status") != "closed":
    print(f"ASSERT FAIL: issue {issue_id} status is {issue.get('status')!r}, expected 'closed'", file=sys.stderr)
    sys.exit(1)

print(f"assert: issue {issue_id} is closed")
PY

if [ -f .beads/session-claims ] && grep -qxF "$id" .beads/session-claims; then
  fail ".beads/session-claims still lists $id after close — claim was not cleared"
fi

# --- (c) authored fan-out script carries a cheap-tier model option ---------
shopt -s nullglob
workflows=(.claude/workflows/*.js)
[ "${#workflows[@]}" -ge 1 ] || fail "no authored fan-out workflow found under .claude/workflows/*.js"
workflow="${workflows[0]}"
[ -s "$workflow" ] || fail "$workflow is empty"

haiku_line="$(grep -n 'haiku' "$workflow" | head -1 | cut -d: -f1)"
[ -n "$haiku_line" ] || fail "$workflow does not mention a haiku (cheap) tier"
window_start=$((haiku_line > 2 ? haiku_line - 2 : 1))
window_end=$((haiku_line + 2))
sed -n "${window_start},${window_end}p" "$workflow" | grep -qi 'model' \
  || fail "$workflow mentions haiku but no 'model' option within 2 lines of it"

echo "assert: all checks passed (claim before implementation before close, issue closed+unclaimed, fan-out workflow carries a haiku-tier model option)"
