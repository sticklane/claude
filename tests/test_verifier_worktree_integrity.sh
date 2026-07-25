#!/usr/bin/env bash
# Tests .claude/agents/verifier.md's worktree-integrity precheck: when the
# verifier is given a BRANCH to verify, it must confirm the tree it is about
# to read is the tree that branch would merge, and halt INCOMPLETE otherwise
# instead of evaluating a stale or foreign checkout (agentic-f7r).
#
# Two live variants motivate it, and each is exercised below against the
# precheck snippet extracted from verifier.md itself — so the test runs the
# documented commands rather than a copy of them:
#   1. stale worktree: the branch ref was advanced with `git update-ref`
#      while a checkout of the old commit stayed put, so HEAD resolves to the
#      new commit but the index/files are the old one.
#   2. foreign checkout: the verifier ran in the shared main working copy, so
#      HEAD is the default branch while the branch ref is somewhere else.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENT="$TOOLKIT_DIR/.claude/agents/verifier.md"

pass=0
fail=0

check() { # check <description> <condition-result 0/1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $1"
  fi
}

# --- contract text ----------------------------------------------------------

# The precheck section: from its heading line to the "Process:" list, so the
# assertions below cannot be satisfied by unrelated prose elsewhere.
section="$(awk '
  /[Ww]orktree-integrity precheck/ {f=1}
  /^Process:/ {f=0}
  f
' "$AGENT")"

[ -n "$section" ]
check "verifier.md carries a worktree-integrity precheck section" $?

precheck_line="$(grep -n '[Ww]orktree-integrity precheck' "$AGENT" | head -1 | cut -d: -f1)"
process_line="$(grep -n '^Process:' "$AGENT" | head -1 | cut -d: -f1)"
[ -n "$precheck_line" ] && [ -n "$process_line" ] && [ "$precheck_line" -lt "$process_line" ]
check "the precheck is positioned before the numbered Process steps" $?

printf '%s\n' "$section" | grep -q "INCOMPLETE"
check "the precheck names INCOMPLETE as its halt verdict" $?

# The wrinkle the issue calls out: a verifier is sometimes legitimately given
# a diff or a working tree with no branch at all. The precheck must say so
# explicitly rather than leaving that mode's behavior implied.
printf '%s\n' "$section" | grep -qi "no branch"
check "the precheck states what it does when no branch was given" $?

printf '%s\n' "$section" | grep -qiE "never (repair|fix)|do not (repair|fix)"
check "the precheck forbids repairing the mismatch itself" $?

# --- the snippet itself -----------------------------------------------------

snippet_dir="$(mktemp -d)"
trap 'rm -rf "$snippet_dir"' EXIT
snippet="$snippet_dir/precheck.sh"

awk '
  /^```bash$/ {inblock=1; next}
  /^```$/ {if (inblock) exit}
  inblock
' "$AGENT" > "$snippet"

[ -s "$snippet" ]
check "the precheck ships a runnable snippet in a bash fence" $?

# run_precheck <fixture-dir> <branch> — runs the snippet, setting `out` to its
# combined output and RC to its exit status. Both land in globals because a
# command substitution would run the call in a subshell and lose RC.
RC=0
out=""
run_precheck() {
  out="$(cd "$1" && BRANCH="$2" bash "$snippet" 2>&1)"
  RC=$?
}

# mkrepo — a repo on branch `feat` with two commits, `feat` at the second.
# Echoes the repo path.
mkrepo() {
  local r
  r="$(mktemp -d)"
  git init -q -b main "$r" >/dev/null 2>&1
  printf 'one\n' > "$r/f.txt"
  git -C "$r" add f.txt >/dev/null 2>&1
  git -C "$r" -c user.email=t@t -c user.name=t commit -qm c1 >/dev/null 2>&1
  git -C "$r" checkout -qb feat >/dev/null 2>&1
  printf 'two\n' > "$r/f.txt"
  git -C "$r" -c user.email=t@t -c user.name=t commit -qam c2 >/dev/null 2>&1
  printf '%s' "$r"
}

# 1. Healthy worktree: HEAD is the branch tip and nothing is uncommitted.
repo="$(mkrepo)"
run_precheck "$repo" feat
[ "$RC" -eq 0 ]
check "healthy worktree on the branch passes the precheck" $?
if printf '%s\n' "$out" | grep -q "INCOMPLETE"; then quiet=1; else quiet=0; fi
check "healthy worktree is not reported as a mismatch" "$quiet"
rm -rf "$repo"

# 2. Stale worktree (the live agentic-z7b.3 shape): the branch ref advanced
#    past the checked-out tree via `git update-ref`.
repo="$(mkrepo)"
tip="$(git -C "$repo" rev-parse HEAD)"
git -C "$repo" reset -q --hard HEAD~1 >/dev/null 2>&1
git -C "$repo" update-ref refs/heads/feat "$tip" >/dev/null 2>&1
run_precheck "$repo" feat
[ "$RC" -ne 0 ]
check "stale worktree (branch ref advanced past the checkout) halts" $?
printf '%s\n' "$out" | grep -q "INCOMPLETE"
check "stale worktree halt is reported as INCOMPLETE" $?
printf '%s\n' "$out" | grep -q "feat"
check "stale worktree halt names the branch" $?
printf '%s\n' "$out" | grep -q "f\.txt"
check "stale worktree halt names the file that differs" $?
rm -rf "$repo"

# 3. Foreign checkout: verifying branch `feat` from a tree sitting on main.
repo="$(mkrepo)"
branch_rev="$(git -C "$repo" rev-parse refs/heads/feat)"
git -C "$repo" checkout -q main >/dev/null 2>&1
main_rev="$(git -C "$repo" rev-parse HEAD)"
run_precheck "$repo" feat
[ "$RC" -ne 0 ]
check "foreign checkout (tree on main, branch elsewhere) halts" $?
printf '%s\n' "$out" | grep -q "INCOMPLETE"
check "foreign checkout halt is reported as INCOMPLETE" $?
printf '%s\n' "$out" | grep -q "$main_rev"
check "foreign checkout halt names the revision actually checked out" $?
printf '%s\n' "$out" | grep -q "$branch_rev"
check "foreign checkout halt names the branch revision it should have been" $?
rm -rf "$repo"

# 4. Uncommitted work on an otherwise-matching checkout: still not the tree
#    the branch would merge, because step 0 stages everything before diffing.
repo="$(mkrepo)"
printf 'three\n' > "$repo/f.txt"
run_precheck "$repo" feat
[ "$RC" -ne 0 ]
check "dirty tree on the right commit halts" $?
printf '%s\n' "$out" | grep -q "INCOMPLETE"
check "dirty-tree halt is reported as INCOMPLETE" $?
rm -rf "$repo"

# 5. A branch that does not resolve at all is a halt, never a silent pass.
repo="$(mkrepo)"
run_precheck "$repo" nonexistent-branch
[ "$RC" -ne 0 ]
check "unresolvable branch halts rather than passing" $?
rm -rf "$repo"

echo "passed: $pass, failed: $fail"
[ "$fail" -eq 0 ]
