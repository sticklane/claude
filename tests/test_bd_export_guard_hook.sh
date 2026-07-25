#!/usr/bin/env bash
# Tests for hooks/bd-export-guard/pre-commit (bd issue agentic-kts): a commit
# that would record a zero-issue .beads/issues.jsonl while the bd database
# still holds issues is refused. The guard's condition is the MISMATCH, not
# the bare zero — a genuinely empty database still exports zero issues and
# still commits. Runs against throwaway bd-tracked fixture repos in a temp dir.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$TOOLKIT_DIR/hooks/bd-export-guard/pre-commit"

for dep in bd jq git; do
  if ! command -v "$dep" >/dev/null 2>&1; then
    echo "SKIP: $dep not on PATH; bd-export-guard hook cannot be exercised"
    exit 0
  fi
done

pass=0
fail=0

assert() { # assert <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  fi
}

assert_eq() { # assert_eq <description> <expected> <actual>
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc (expected: '$expected', got: '$actual')" >&2
  fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# run_hook <cwd> [env assignments...] -- sets RH_EXIT / RH_ERR.
run_hook() {
  local cwd="$1"; shift
  local err_f="$TMP/.rh_err"
  (
    cd "$cwd" || exit 97
    env "$@" "$HOOK" >/dev/null 2>"$err_f"
  )
  RH_EXIT=$?
  RH_ERR="$(cat "$err_f")"
}

# make_repo <dir> <prefix> -- a git repo with bd initialized and no issues.
make_repo() {
  local dir="$1" prefix="$2"
  mkdir -p "$dir"
  git -C "$dir" init -q
  git -C "$dir" config user.name test
  git -C "$dir" config user.email test@example.com
  git -C "$dir" commit -q --allow-empty -m init
  (cd "$dir" && BD_NON_INTERACTIVE=1 bd init --prefix "$prefix") >/dev/null 2>&1
}

# stage_export <dir> -- write the real export and stage it.
stage_export() {
  local dir="$1"
  (cd "$dir" && bd export -o .beads/issues.jsonl) >/dev/null 2>&1
  git -C "$dir" add -f .beads/issues.jsonl
}

# stage_empty_export <dir> -- stage a zero-issue export, the failure mode.
stage_empty_export() {
  local dir="$1"
  : > "$dir/.beads/issues.jsonl"
  git -C "$dir" add -f .beads/issues.jsonl
}

assert "hook exists and is executable" test -x "$HOOK"

POPULATED="$TMP/populated"
make_repo "$POPULATED" bdeg
if ! (cd "$POPULATED" && bd create "guard fixture issue" >/dev/null 2>&1); then
  echo "FAIL: fixture setup could not create a bd issue" >&2
  exit 1
fi

EMPTY="$TMP/empty"
make_repo "$EMPTY" bdegempty

# --- a real export of a populated database commits ---------------------------

stage_export "$POPULATED"
run_hook "$POPULATED"
assert_eq "a nonempty export of a populated database is allowed" 0 "$RH_EXIT"

# --- zero-issue export while the database holds issues is refused ------------

stage_empty_export "$POPULATED"
run_hook "$POPULATED"
assert_eq "a zero-issue export of a populated database is refused" 1 "$RH_EXIT"
assert "refusal names the export file" \
  grep -qF ".beads/issues.jsonl" <<<"$RH_ERR"

# --- a staged DELETION of the export is the same failure ---------------------

git -C "$POPULATED" add -f .beads/issues.jsonl
git -C "$POPULATED" commit -q -m "record export" --no-verify
rm -f "$POPULATED/.beads/issues.jsonl"
git -C "$POPULATED" rm -q --cached .beads/issues.jsonl >/dev/null 2>&1
run_hook "$POPULATED"
assert_eq "a staged deletion of the export is refused too" 1 "$RH_EXIT"
git -C "$POPULATED" reset -q --hard HEAD

# --- the genuinely empty database is NOT blocked -----------------------------

stage_empty_export "$EMPTY"
run_hook "$EMPTY"
assert_eq "a zero-issue export of an empty database is allowed" 0 "$RH_EXIT"

# --- nothing staged for the export path -> nothing to guard ------------------

stage_empty_export "$POPULATED"
git -C "$POPULATED" reset -q
run_hook "$POPULATED"
assert_eq "an unstaged export path is not guarded" 0 "$RH_EXIT"

# --- escape hatches ----------------------------------------------------------

stage_empty_export "$POPULATED"
run_hook "$POPULATED" BD_EXPORT_GUARD=0
assert_eq "BD_EXPORT_GUARD=0 turns the guard off" 0 "$RH_EXIT"

# /usr/bin:/bin carries bash, git and jq on this host but never bd, which
# installs under a package manager's prefix.
run_hook "$POPULATED" PATH=/usr/bin:/bin
assert_eq "bd missing from PATH never bricks the commit" 0 "$RH_EXIT"

# --- the chain block refuses a real `git commit` -----------------------------
#
# Everything above runs $HOOK directly. This drives git itself through the
# repo's own chain block — its `git rev-parse --show-toplevel` resolution, its
# executable test, and its `|| exit $?` propagation — copied verbatim out of
# .beads/hooks/pre-commit. The beads and review-gate blocks around it are left
# out: beads' block re-exports and re-stages the very file under test, and
# review-gate's hardcoded path points outside the fixture.

CHAIN_BLOCK="$TMP/chain-block.sh"
awk '/BEGIN AGENTIC BD-EXPORT-GUARD/,/END AGENTIC BD-EXPORT-GUARD/' \
  "$TOOLKIT_DIR/.beads/hooks/pre-commit" > "$CHAIN_BLOCK"
assert "the repo's bd pre-commit hook carries the guard chain block" \
  test -s "$CHAIN_BLOCK"

# The guard must run after the beads block, which is what stages the export it
# reads — and that block exits early on its own nonzero status.
beads_end="$(grep -n 'END BEADS INTEGRATION' "$TOOLKIT_DIR/.beads/hooks/pre-commit" | cut -d: -f1)"
guard_begin="$(grep -n 'BEGIN AGENTIC BD-EXPORT-GUARD' "$TOOLKIT_DIR/.beads/hooks/pre-commit" | cut -d: -f1)"
assert "the guard is chained after the beads block, not before it" \
  test "${beads_end:-0}" -lt "${guard_begin:-0}"

CHAINED="$TMP/chained"
make_repo "$CHAINED" bdegchain
if ! (cd "$CHAINED" && bd create "chain fixture issue" >/dev/null 2>&1); then
  echo "FAIL: chain fixture setup could not create a bd issue" >&2
  exit 1
fi
mkdir -p "$CHAINED/hooks/bd-export-guard" "$CHAINED/.githooks"
cp "$HOOK" "$CHAINED/hooks/bd-export-guard/pre-commit"
chmod +x "$CHAINED/hooks/bd-export-guard/pre-commit"
{ printf '#!/usr/bin/env sh\n'; cat "$CHAIN_BLOCK"; } > "$CHAINED/.githooks/pre-commit"
chmod +x "$CHAINED/.githooks/pre-commit"
git -C "$CHAINED" config core.hooksPath .githooks

# commit_chained [env assignments...] -- sets CC_EXIT / CC_ERR / CC_HEAD.
commit_chained() {
  local err_f="$TMP/.cc_err"
  (
    cd "$CHAINED" || exit 97
    env "$@" git commit -m "record export" >/dev/null 2>"$err_f"
  )
  CC_EXIT=$?
  CC_ERR="$(cat "$err_f")"
  CC_HEAD="$(git -C "$CHAINED" rev-parse HEAD)"
}

before_head="$(git -C "$CHAINED" rev-parse HEAD)"
stage_empty_export "$CHAINED"
commit_chained
assert_eq "git commit itself is refused through the chained hook" 1 "$CC_EXIT"
assert "the refusal reaching git comes from the guard" \
  grep -qF "bd-export-guard" <<<"$CC_ERR"
assert_eq "the refused commit left HEAD where it was" "$before_head" "$CC_HEAD"

commit_chained BD_EXPORT_GUARD=0
assert_eq "the chained hook lets a commit through when the guard stands down" 0 "$CC_EXIT"
assert "the allowed commit advanced HEAD" test "$before_head" != "$CC_HEAD"

echo "bd-export-guard hook: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
