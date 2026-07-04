#!/usr/bin/env bash
# Tests for bin/sync-workflows (SPEC R5, amended 2026-07-03).
#
# sync-workflows symlinks ONLY the toolkit's .claude/workflows/* FILES into the
# user workflows dir. Runs entirely against temp-dir fixtures via the
# SYNC_WORKFLOWS_SRC / SYNC_WORKFLOWS_DEST env overrides, so it NEVER touches the
# real home directory. Mirrors the retired tests/test_sync_skills.sh precedent
# (commit cbe3097), adapted from directories to files.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SYNC="$TOOLKIT_DIR/bin/sync-workflows"

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

SRC="$TMP/toolkit/.claude/workflows"
DEST="$TMP/home/.claude/workflows"
mkdir -p "$SRC" "$DEST"
echo "// alpha" > "$SRC/alpha.js"
echo "// beta" > "$SRC/beta.js"

run_sync() {
  SYNC_WORKFLOWS_SRC="$SRC" SYNC_WORKFLOWS_DEST="$DEST" "$SYNC" 2>&1
}

assert "sync-workflows exists and is executable" test -x "$SYNC"

# --- Env override: the run must NEVER touch the real ~/.claude/workflows ------
# (Guaranteed structurally by only ever reading SYNC_WORKFLOWS_SRC/_DEST; the
# fixtures below live entirely under $TMP.)
assert "dest starts empty" test -z "$(ls -A "$DEST")"

# --- Fresh run links every toolkit workflow FILE as a symlink -----------------
out="$(run_sync)"
assert "alpha.js is a symlink after first run" test -L "$DEST/alpha.js"
assert "alpha.js symlink (not a copy)" test -L "$DEST/alpha.js"
assert_eq "alpha.js symlink points at toolkit file" "$SRC/alpha.js" "$(readlink "$DEST/alpha.js")"
assert "beta.js is a symlink after first run" test -L "$DEST/beta.js"
assert_eq "first run summary" "linked 2, removed 0, kept 0 local" "$out"

# --- Idempotence: second run re-links nothing ---------------------------------
before="$(for f in "$DEST"/*; do echo "$f -> $(readlink "$f" || true)"; done)"
out="$(run_sync)"
after="$(for f in "$DEST"/*; do echo "$f -> $(readlink "$f" || true)"; done)"
assert_eq "no-op run prints linked 0" "linked 0, removed 0, kept 0 local" "$out"
assert_eq "readlink state identical across runs" "$before" "$after"

# --- Local non-symlink files are kept, never touched --------------------------
echo "mine" > "$DEST/local.js"
out="$(run_sync)"
assert "local file still a plain file" test -f "$DEST/local.js"
assert "local file is not a symlink" test ! -L "$DEST/local.js"
assert_eq "local file content untouched" "mine" "$(cat "$DEST/local.js")"
assert_eq "local file counted as kept" "linked 0, removed 0, kept 1 local" "$out"

# --- Name collision with local file: skip + report conflict -------------------
echo "toolkit version" > "$SRC/local.js"
out="$(run_sync)"
assert "collision file not overwritten" test ! -L "$DEST/local.js"
assert_eq "collision file content untouched" "mine" "$(cat "$DEST/local.js")"
assert "conflict reported by name" grep -q "conflict: local.js" <<<"$out"
assert "summary lists conflicts" grep -q "linked 0, removed 0, kept 1 local, conflicts: local.js" <<<"$out"
rm -f "$SRC/local.js"

# --- Symlink pointing outside the toolkit is never touched --------------------
echo "other" > "$TMP/elsewhere.js"
ln -s "$TMP/elsewhere.js" "$DEST/other.js"
out="$(run_sync)"
assert_eq "foreign symlink untouched" "$TMP/elsewhere.js" "$(readlink "$DEST/other.js")"
assert_eq "foreign symlink counted as kept" "linked 0, removed 0, kept 2 local" "$out"

# --- New toolkit workflow gets linked (linked 1) ------------------------------
echo "// gamma" > "$SRC/gamma.js"
out="$(run_sync)"
assert "gamma.js linked" test -L "$DEST/gamma.js"
assert_eq "added workflow reports linked 1" "linked 1, removed 0, kept 2 local" "$out"

# --- Removed toolkit workflow: dangling symlink removed (removed 1) -----------
rm -f "$SRC/gamma.js"
out="$(run_sync)"
assert "dangling gamma.js symlink removed" test ! -e "$DEST/gamma.js"
assert "dangling gamma.js symlink really gone" test ! -L "$DEST/gamma.js"
assert_eq "removed workflow reports removed 1" "linked 0, removed 1, kept 2 local" "$out"

# --- Toolkit symlink with wrong target gets re-linked -------------------------
rm -f "$DEST/beta.js"
ln -s "$SRC/alpha.js" "$DEST/beta.js"
out="$(run_sync)"
assert_eq "wrong-target toolkit symlink corrected" "$SRC/beta.js" "$(readlink "$DEST/beta.js")"
assert_eq "correction counted as linked" "linked 1, removed 0, kept 2 local" "$out"

# --- Missing source dir is a hard error --------------------------------------
out="$(SYNC_WORKFLOWS_SRC="$TMP/nonexistent" SYNC_WORKFLOWS_DEST="$DEST" "$SYNC" 2>&1)"; rc=$?
assert "missing source dir exits nonzero" test "$rc" -ne 0
assert "missing source dir reports the path" grep -q "source dir not found" <<<"$out"

echo "---"
echo "passed: $pass, failed: $fail"
[ "$fail" -eq 0 ]
