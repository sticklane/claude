#!/usr/bin/env bash
# Model-free test of the pre-commit review skip gate pinned in
# .claude/skills/build/SKILL.md (specs/precommit-review/SPEC.md, R6):
#
#   git add -A && git diff <step0-base> --numstat
#
# classified via the NON-product pattern list (docs/**, **/*.md, tests/**,
# test/**, **/test_*, **/*_test.*, **/*.test.*, **/*.spec.*, **/*.json,
# **/*.yaml, **/*.yml, **/*.toml, **/*.lock) and the <25 product-line
# threshold (sum of added+deleted lines over product paths only).
#
# Builds throwaway git repos under one temp root, covering mid-stream
# commits, staged edits, unstaged edits, and untracked files, and
# asserts the seven cases from the Goal end to end.
set -u

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0

assert_eq() {
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc (expected: '$expected', got: '$actual')" >&2
  fi
}

case_result() {
  local name="$1" fail_before="$2" fail_after="$3"
  if [ "$fail_after" -eq "$fail_before" ]; then
    echo "PASS: $name"
  else
    echo "FAIL: $name"
  fi
}

new_repo() {
  local dir="$1"
  mkdir -p "$dir"
  git -C "$dir" init -q
  git -C "$dir" config user.email "test@example.com"
  git -C "$dir" config user.name "Test"
  # step-0 base: a recorded initial commit, never empty (avoids the
  # "no commits yet" edge case some git versions special-case).
  echo "seed" >"$dir/.seed"
  git -C "$dir" add -A >/dev/null
  git -C "$dir" commit -q -m "step0: seed"
  git -C "$dir" rev-parse HEAD
}

gen_lines() {
  local n="$1" prefix="${2:-line}"
  local i=1
  while [ "$i" -le "$n" ]; do
    echo "$prefix $i"
    i=$((i + 1))
  done
}

# The pinned gate command itself: stage everything (so untracked new
# files become visible), diff against the recorded step-0 base.
gate_numstat() {
  local dir="$1" step0="$2"
  git -C "$dir" add -A >/dev/null
  git -C "$dir" diff "$step0" --numstat
}

# NON-product classifier, verbatim pattern list from ../SPEC.md Solution.
is_nonproduct() {
  case "$1" in
    docs/* | */docs/*) return 0 ;;
    *.md) return 0 ;;
    tests/* | */tests/*) return 0 ;;
    test/* | */test/*) return 0 ;;
    test_* | */test_*) return 0 ;;
    *_test.*) return 0 ;;
    *.test.*) return 0 ;;
    *.spec.*) return 0 ;;
    *.json | *.yaml | *.yml | *.toml | *.lock) return 0 ;;
    *) return 1 ;;
  esac
}

# Reads numstat lines on stdin, echoes "skip" or "review" per the
# <25-product-line threshold (sums added+deleted over product paths only;
# a diff with no product paths at all also skips).
decide() {
  local added deleted path total=0 has_product=0
  while IFS=$'\t' read -r added deleted path; do
    [ -z "${path:-}" ] && continue
    is_nonproduct "$path" && continue
    has_product=1
    [ "$added" = "-" ] && added=0
    [ "$deleted" = "-" ] && deleted=0
    total=$((total + added + deleted))
  done
  if [ "$has_product" -eq 0 ]; then
    echo skip
  elif [ "$total" -lt 25 ]; then
    echo skip
  else
    echo review
  fi
}

# --- case: docs-only -> skip ------------------------------------------
fail_before=$fail
dir="$TMP/docs-only"
step0="$(new_repo "$dir")"
mkdir -p "$dir/docs"
gen_lines 40 >"$dir/docs/readme.md" # untracked
result="$(gate_numstat "$dir" "$step0" | decide)"
assert_eq "docs-only classifies as skip" "skip" "$result"
case_result "docs-only" "$fail_before" "$fail"

# --- case: tests-only (incl. .test.ts / .spec.ts) -> skip --------------
fail_before=$fail
dir="$TMP/tests-only"
step0="$(new_repo "$dir")"
mkdir -p "$dir/tests" "$dir/src"
gen_lines 10 >"$dir/tests/test_something.sh" # untracked
gen_lines 40 >"$dir/src/foo.test.ts"          # untracked, large but non-product
gen_lines 40 >"$dir/src/bar.spec.ts"          # untracked, large but non-product
result="$(gate_numstat "$dir" "$step0" | decide)"
assert_eq "tests-only (incl. .test.ts/.spec.ts) classifies as skip" "skip" "$result"
case_result "tests-only" "$fail_before" "$fail"

# --- case: 24 product lines -> skip (staged edit) -----------------------
fail_before=$fail
dir="$TMP/24-lines-skip"
step0="$(new_repo "$dir")"
mkdir -p "$dir/src"
gen_lines 24 >"$dir/src/feature.py"
git -C "$dir" add -A >/dev/null # staged edit, before the gate runs
result="$(gate_numstat "$dir" "$step0" | decide)"
assert_eq "24 product lines classifies as skip" "skip" "$result"
case_result "24-lines-skip" "$fail_before" "$fail"

# --- case: 26 product lines -> review (unstaged edit) --------------------
fail_before=$fail
dir="$TMP/26-lines-review"
step0="$(new_repo "$dir")"
mkdir -p "$dir/src"
gen_lines 26 >"$dir/src/feature.py" # unstaged edit, left for the gate's git add -A
result="$(gate_numstat "$dir" "$step0" | decide)"
assert_eq "26 product lines classifies as review" "review" "$result"
case_result "26-lines-review" "$fail_before" "$fail"

# --- case: mixed docs + 26 product lines -> review -----------------------
fail_before=$fail
dir="$TMP/mixed-docs-product"
step0="$(new_repo "$dir")"
mkdir -p "$dir/docs" "$dir/src"
gen_lines 5 >"$dir/docs/notes.md"
gen_lines 26 >"$dir/src/feature.py"
result="$(gate_numstat "$dir" "$step0" | decide)"
assert_eq "mixed docs + 26 product lines classifies as review" "review" "$result"
case_result "mixed-docs-product" "$fail_before" "$fail"

# --- case: untracked new 26-line product file -> review (git-add-first) --
fail_before=$fail
dir="$TMP/untracked-product-file"
step0="$(new_repo "$dir")"
mkdir -p "$dir/src"
gen_lines 26 >"$dir/src/newthing.py" # never staged before the gate runs
result="$(gate_numstat "$dir" "$step0" | decide)"
assert_eq "untracked new 26-line product file classifies as review" "review" "$result"
case_result "untracked-product-file" "$fail_before" "$fail"

# --- case: committed-then-modified lines counted exactly once ------------
fail_before=$fail
dir="$TMP/committed-then-modified"
step0="$(new_repo "$dir")"
mkdir -p "$dir/src"
# Mid-stream commit: file doesn't exist at step0, gets added here.
gen_lines 15 "orig" >"$dir/src/foo.py"
git -C "$dir" add -A >/dev/null
git -C "$dir" commit -q -m "mid-stream: add foo"
# Then rewritten (not just appended) in the working tree, left unstaged:
# a buggy implementation that sums each commit's own diff instead of
# diffing straight against step0 would double-count these lines.
gen_lines 26 "final" >"$dir/src/foo.py"
numstat="$(gate_numstat "$dir" "$step0")"
foo_line="$(echo "$numstat" | awk -v f="src/foo.py" '$3 == f')"
added="$(echo "$foo_line" | awk '{print $1}')"
deleted="$(echo "$foo_line" | awk '{print $2}')"
assert_eq "committed-then-modified: added counted exactly once" "26" "$added"
assert_eq "committed-then-modified: deleted counted exactly once" "0" "$deleted"
result="$(echo "$numstat" | decide)"
assert_eq "committed-then-modified classifies as review" "review" "$result"
case_result "committed-then-modified" "$fail_before" "$fail"

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
