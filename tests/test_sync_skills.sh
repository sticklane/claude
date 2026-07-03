#!/usr/bin/env bash
# Tests for bin/sync-skills (SPEC R24).
# Runs entirely against temp-dir fixtures via SYNC_SKILLS_SRC / SYNC_SKILLS_DEST.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SYNC="$TOOLKIT_DIR/bin/sync-skills"

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

SRC="$TMP/toolkit/.claude/skills"
DEST="$TMP/home/.claude/skills"
mkdir -p "$SRC/alpha" "$SRC/beta" "$DEST"
echo "alpha skill" > "$SRC/alpha/SKILL.md"
echo "beta skill" > "$SRC/beta/SKILL.md"

run_sync() {
  SYNC_SKILLS_SRC="$SRC" SYNC_SKILLS_DEST="$DEST" "$SYNC" 2>&1
}

assert "sync-skills exists and is executable" test -x "$SYNC"

# --- Fresh run links every toolkit skill dir -------------------------------
out="$(run_sync)"
assert "alpha is a symlink after first run" test -L "$DEST/alpha"
assert_eq "alpha symlink points at toolkit skill" "$SRC/alpha" "$(readlink "$DEST/alpha")"
assert "beta is a symlink after first run" test -L "$DEST/beta"
assert_eq "first run summary" "linked 2, removed 0, kept 0 local" "$out"

# --- Idempotence: second run re-links nothing ------------------------------
before="$(for f in "$DEST"/*; do echo "$f -> $(readlink "$f" || true)"; done)"
out="$(run_sync)"
after="$(for f in "$DEST"/*; do echo "$f -> $(readlink "$f" || true)"; done)"
assert_eq "no-op run prints linked 0" "linked 0, removed 0, kept 0 local" "$out"
assert_eq "readlink state identical across runs" "$before" "$after"

# --- Local non-symlink entries are kept, never touched ---------------------
mkdir -p "$DEST/local-skill"
echo "mine" > "$DEST/local-skill/SKILL.md"
out="$(run_sync)"
assert "local dir still a plain dir" test -d "$DEST/local-skill"
assert "local dir is not a symlink" test ! -L "$DEST/local-skill"
assert_eq "local dir file untouched" "mine" "$(cat "$DEST/local-skill/SKILL.md")"
assert_eq "local entry counted as kept" "linked 0, removed 0, kept 1 local" "$out"

# --- Name collision with local entry: skip + report conflict ---------------
mkdir -p "$SRC/local-skill"
echo "toolkit version" > "$SRC/local-skill/SKILL.md"
out="$(run_sync)"
assert "collision entry not overwritten" test ! -L "$DEST/local-skill"
assert_eq "collision entry content untouched" "mine" "$(cat "$DEST/local-skill/SKILL.md")"
assert "conflict reported by name" grep -q "conflict: local-skill" <<<"$out"
assert "summary lists conflicts" grep -q "linked 0, removed 0, kept 1 local, conflicts: local-skill" <<<"$out"
rm -rf "$SRC/local-skill"

# --- Symlink pointing outside the toolkit is never touched -----------------
mkdir -p "$TMP/elsewhere/other-skill"
ln -s "$TMP/elsewhere/other-skill" "$DEST/other-skill"
out="$(run_sync)"
assert_eq "foreign symlink untouched" "$TMP/elsewhere/other-skill" "$(readlink "$DEST/other-skill")"
assert_eq "foreign symlink counted as kept" "linked 0, removed 0, kept 2 local" "$out"

# --- New toolkit skill gets linked (linked 1) -------------------------------
mkdir -p "$SRC/gamma"
echo "gamma" > "$SRC/gamma/SKILL.md"
out="$(run_sync)"
assert "gamma linked" test -L "$DEST/gamma"
assert_eq "added skill reports linked 1" "linked 1, removed 0, kept 2 local" "$out"

# --- Removed toolkit skill: dangling symlink removed (removed 1) ------------
rm -rf "$SRC/gamma"
out="$(run_sync)"
assert "dangling gamma symlink removed" test ! -e "$DEST/gamma"
assert "dangling gamma symlink really gone" test ! -L "$DEST/gamma"
assert_eq "removed skill reports removed 1" "linked 0, removed 1, kept 2 local" "$out"

# --- Toolkit symlink with wrong target gets re-linked ------------------------
rm "$DEST/beta"
ln -s "$SRC/alpha" "$DEST/beta"
out="$(run_sync)"
assert_eq "wrong-target toolkit symlink corrected" "$SRC/beta" "$(readlink "$DEST/beta")"
assert_eq "correction counted as linked" "linked 1, removed 0, kept 2 local" "$out"

echo "---"
echo "passed: $pass, failed: $fail"
[ "$fail" -eq 0 ]
