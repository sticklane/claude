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

# --- the hook is wired into the repo's own pre-commit chain ------------------

assert "the repo's bd pre-commit hook chains the guard" \
  grep -qF "hooks/bd-export-guard/pre-commit" "$TOOLKIT_DIR/.beads/hooks/pre-commit"

echo "bd-export-guard hook: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
