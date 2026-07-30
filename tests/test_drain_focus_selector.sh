#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SELECTOR="$ROOT/bin/now-focus"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0

record() {
  local ok="$1" name="$2"
  if [ "$ok" = "yes" ]; then
    pass=$((pass + 1))
    printf 'ok   - %s\n' "$name"
  else
    fail=$((fail + 1))
    printf 'FAIL - %s\n' "$name"
    sed 's/^/       /' "$TMP/out" 2>/dev/null
    sed 's/^/       /' "$TMP/err" 2>/dev/null
  fi
}

# Builds a throwaway repo whose only content is specs/NOW.md, read from stdin.
make_repo() {
  local name="$1" repo="$TMP/$1"
  mkdir -p "$repo/specs"
  cat >"$repo/specs/NOW.md"
  printf '%s' "$repo"
}

run_selector() {
  local repo="$1"
  shift
  "$SELECTOR" --root "$repo" "$@" >"$TMP/out" 2>"$TMP/err"
  printf '%s' "$?" >"$TMP/status"
}

status() { cat "$TMP/status"; }

assert_stdout_equals() {
  local name="$1" expected="$2"
  if [ "$(cat "$TMP/out")" = "$expected" ]; then
    record yes "$name"
  else
    record no "$name"
  fi
}

assert_status() {
  local name="$1" expected="$2"
  if [ "$(status)" = "$expected" ]; then
    record yes "$name"
  else
    record no "$name (exit $(status), expected $expected)"
  fi
}

assert_stderr_contains() {
  local name="$1" needle="$2"
  if grep -q -- "$needle" "$TMP/err"; then
    record yes "$name"
  else
    record no "$name"
  fi
}

# --- grammar: entries are list lines; prose, headings, comments, blanks ignored

ordered="$(
  make_repo ordered <<'NOW'
# Now

Human-owned. Order is priority. WIP is 1.

<!-- a comment line -->

- drain-economy — the focus this file was built for
- rigor-tier
* toolkit-core-simplification

Trailing prose that names no slug.
NOW
)"

run_selector "$ordered"
assert_status "ordered NOW.md selects successfully" 0
assert_stdout_equals "entries yield slugs in file order, prose ignored" \
  "drain-economy
rigor-tier
toolkit-core-simplification"

run_selector "$ordered" --top
assert_stdout_equals "--top yields only the first entry" "drain-economy"

run_selector "$ordered" --why
if [ "$(cut -f1 <"$TMP/out")" = "drain-economy
rigor-tier
toolkit-core-simplification" ]; then
  record yes "--why keeps the slug in the first field"
else
  record no "--why keeps the slug in the first field"
fi
if [ "$(sed -n 1p "$TMP/out" | cut -f2)" = "the focus this file was built for" ]; then
  record yes "--why carries the optional one-line why in the second field"
else
  record no "--why carries the optional one-line why in the second field"
fi
if [ -z "$(sed -n 2p "$TMP/out" | cut -f2)" ]; then
  record yes "an entry with no why yields an empty why field"
else
  record no "an entry with no why yields an empty why field"
fi

# --- empty list is a legal state, not a crash

empty="$(
  make_repo empty <<'NOW'
# Now

Only a human edits this file.
NOW
)"

run_selector "$empty"
assert_status "empty NOW.md exits with the no-focus status" 3
assert_stdout_equals "empty NOW.md prints no slug" ""
assert_stderr_contains "empty NOW.md names the --all escape" '--all'
assert_stderr_contains "empty NOW.md names the explicit-slug escape" 'specs/<slug>'
assert_stderr_contains "empty NOW.md refuses to invent a focus" 'never invents a focus'

# --- a missing file reports the path rather than guessing

mkdir -p "$TMP/absent"
run_selector "$TMP/absent"
assert_status "missing NOW.md exits with the no-focus status" 3
assert_stderr_contains "missing NOW.md names the file it wanted" 'specs/NOW.md'

# --- duplicates collapse to their first position

dupes="$(
  make_repo dupes <<'NOW'
- rigor-tier
- drain-economy
- rigor-tier — repeated by hand
NOW
)"

run_selector "$dupes"
assert_status "duplicate slugs still select successfully" 0
assert_stdout_equals "a repeated slug keeps only its first position" \
  "rigor-tier
drain-economy"

# --- a malformed slug is reported, never silently dropped

bad="$(
  make_repo bad <<'NOW'
- drain-economy
- Not A Slug
NOW
)"

run_selector "$bad"
assert_status "a malformed entry fails the grammar" 2
assert_stderr_contains "the malformed entry reports its line number" 'line 2'
assert_stderr_contains "the malformed entry quotes what it read" 'Not A Slug'

printf '\npassed: %d, failed: %d\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
