#!/usr/bin/env bash
# Hidden acceptance grader for the T3 `sitegen` fixture.
#
# Held OUT of both arms' filesystems: it lives beside (not inside) the `repo/`
# snapshot that gets mounted, and it is never copied into an arm's worktree.
#
# Usage: assert.sh <target-repo-dir>
#   RED  — exits non-zero against the untouched snapshot (repo/)
#   GREEN— exits 0 against the committed reference solution (reference/)
#
# Checks, all independent:
#   1. the full node:test suite passes in the target
#   2. exactly ONE date-format definition remains across the target's src/
#   3. the built sample site matches the golden output tree byte-for-byte
#   4. the known-bad December date renders correctly (no "undefined")
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GOLDEN="$HERE/golden"

if [ "$#" -lt 1 ]; then
  echo "usage: assert.sh <target-repo-dir>" >&2
  exit 2
fi
TARGET="$(cd "$1" 2>/dev/null && pwd)" || { echo "no such target dir: $1" >&2; exit 2; }

fails=0
fail() { echo "FAIL: $*"; fails=$((fails + 1)); }
ok()   { echo "ok:   $*"; }

# 1. Full test suite must be green.
if ( cd "$TARGET" && node --test ) >/dev/null 2>&1; then
  ok "node --test suite is green"
else
  fail "node --test suite is not green"
fi

# 2. Exactly one date-format definition across src/ (unified, not duplicated).
defs="$(grep -rE '^function formatDate' "$TARGET/src" 2>/dev/null | wc -l | tr -d ' ')"
if [ "$defs" = "1" ]; then
  ok "exactly one formatDate definition across src/"
else
  fail "expected exactly one formatDate definition across src/, found $defs"
fi

# 3. Built sample site must match the golden tree exactly.
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT
if OUT_DIR="$OUT" node "$TARGET/build.js" >/dev/null 2>&1; then
  built="$OUT"
  # Fall back to a conventional out/ if the target ignored OUT_DIR.
  if [ -z "$(ls -A "$OUT" 2>/dev/null)" ] && [ -d "$TARGET/out" ]; then
    built="$TARGET/out"
  fi
  if diff -ru "$GOLDEN" "$built" >/dev/null 2>&1; then
    ok "built sample site matches the golden tree"
  else
    fail "built sample site differs from the golden tree"
    diff -ru "$GOLDEN" "$built" 2>&1 | head -20
  fi
else
  fail "build.js failed to run"
  built=""
fi

# 4. The known-bad December date renders correctly, nowhere leaks "undefined".
if [ -n "$built" ] && [ -f "$built/index.html" ]; then
  if grep -q 'December 25, 2023' "$built/index.html" && \
     ! grep -rq 'undefined' "$built"; then
    ok "known-bad December date renders correctly"
  else
    fail "December date is wrong or 'undefined' leaked into the built site"
  fi
else
  fail "no index.html produced to check the December date"
fi

if [ "$fails" -eq 0 ]; then
  echo "PASS: all sitegen checks satisfied"
  exit 0
fi
echo "$fails check(s) failed"
exit 1
