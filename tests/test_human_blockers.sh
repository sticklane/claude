#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKER="$ROOT/bin/check-human-blockers"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0

ok() {
  pass=$((pass + 1))
  printf 'ok   - %s\n' "$1"
}

nope() {
  fail=$((fail + 1))
  printf 'FAIL - %s\n' "$1"
}

sha256_of() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

file_census() {
  (cd "$1" && find . -type f -not -path '*/.git/*' | sort)
}

new_fixture() {
  local name="$1" fixture="$TMP/$1"
  mkdir -p "$fixture/scripts/blocker-probes"
  printf '%s\n' '#!/usr/bin/env bash' 'exit 0' \
    >"$fixture/scripts/blocker-probes/blocked"
  printf '%s\n' '#!/usr/bin/env bash' 'exit 1' \
    >"$fixture/scripts/blocker-probes/dissolved"
  printf '%s\n' '#!/usr/bin/env bash' 'exit 3' \
    >"$fixture/scripts/blocker-probes/undetermined"
  printf '%s\n' '#!/usr/bin/env bash' 'sleep 30' 'exit 0' \
    >"$fixture/scripts/blocker-probes/slow"
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -u' \
    'case "${1-}" in' \
    '  present) target="sibling-present" ;;' \
    '  absent) target="sibling-absent" ;;' \
    '  *) exit 3 ;;' \
    'esac' \
    'if [ ! -d "$target/.git" ]; then exit 3; fi' \
    'if ! git -C "$target" rev-parse --git-dir >/dev/null 2>&1; then exit 3; fi' \
    'exit 0' >"$fixture/scripts/blocker-probes/sibling-queue"
  chmod 755 "$fixture/scripts/blocker-probes/"*
  printf '%s\n' '#!/usr/bin/env bash' 'exit 0' \
    >"$fixture/scripts/blocker-probes/unarmed"
  chmod 644 "$fixture/scripts/blocker-probes/unarmed"
  mkdir -p "$fixture/sibling-present"
  git -C "$fixture/sibling-present" init -q
  git -C "$fixture" init -q
  git -C "$fixture" config user.email fixture@example.invalid
  git -C "$fixture" config user.name "Blocker Fixture"
  git -C "$fixture" config core.hooksPath /dev/null
  printf '%s' "$fixture"
}

plant_armed_repository() {
  local target="$1"
  mkdir -p "$target/.git"
  printf '%s\n' \
    '[core]' \
    '	repositoryformatversion = 0' \
    '	fsmonitor = "touch SENTINEL"' \
    '	sshCommand = "touch SENTINEL"' \
    '	pager = "touch SENTINEL"' >"$target/.git/config"
  printf '%s\n' 'ref: refs/heads/main' >"$target/.git/HEAD"
  mkdir -p "$target/.git/objects" "$target/.git/refs"
}

write_human() {
  local fixture="$1"
  shift
  {
    printf '%s\n\n' '# Human-actionable items'
    printf '%s\n\n' '## Agent-filed blockers'
    printf '%s\n' "$@"
    printf '\n%s\n\n' '## Human notes'
    printf '%s\n' 'Human-owned prose below the machine-owned section.'
  } >"$fixture/HUMAN.md"
}

CHECK_OUT=""
CHECK_RC=0
FIXTURE_INTACT=0

run_checker() {
  local fixture="$1" probe_timeout="${2-}"
  local before_hash after_hash before_census after_census
  before_hash="$(sha256_of "$fixture/HUMAN.md")"
  before_census="$(file_census "$fixture")"
  CHECK_OUT="$(
    env ${probe_timeout:+HUMAN_BLOCKER_PROBE_TIMEOUT="$probe_timeout"} \
      "$CHECKER" "$fixture/HUMAN.md" 2>&1
  )"
  CHECK_RC=$?
  after_hash="$(sha256_of "$fixture/HUMAN.md")"
  after_census="$(file_census "$fixture")"
  FIXTURE_INTACT=0
  if [ "$before_hash" = "$after_hash" ] \
    && [ "$before_census" = "$after_census" ]; then
    FIXTURE_INTACT=1
  fi
}

expect_case() {
  local name="$1" expected_rc="$2"
  shift 2
  local problems="" pattern
  if [ "$CHECK_RC" != "$expected_rc" ]; then
    problems="exit $CHECK_RC, wanted $expected_rc"
  fi
  for pattern in "$@"; do
    if ! printf '%s\n' "$CHECK_OUT" | grep -q "$pattern"; then
      problems="$problems; no match for /$pattern/"
    fi
  done
  if [ "$FIXTURE_INTACT" != 1 ]; then
    problems="$problems; checker mutated the fixture (R6)"
  fi
  if [ -z "$problems" ]; then
    ok "$name"
  else
    nope "$name ($problems)"
    printf '%s\n' "$CHECK_OUT" | sed 's/^/       /'
  fi
}

expect_no_sentinel() {
  local name="$1" planted
  planted="$(find "$TMP" -name SENTINEL -print -quit)"
  test -z "$planted" && ok "$name" || nope "$name"
}

entry() {
  printf '%s %s · %s · decide — %s — Blocks: task 02 — Still-blocked: %s' \
    "$1" "$2" "$3" "$4" "$5"
}

fixture="$(new_fixture still-blocked)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-29 specs/demo/one.md \
    'answer whether the queue may move' blocked)"
run_checker "$fixture"
expect_case "probe exiting 0 lands in still-blocked with exit 0" 0 \
  'still-blocked (1):' '2026-07-29 · specs/demo/one.md' 'stale (0):'

fixture="$(new_fixture stale)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-28 specs/demo/two.md \
    'adopt the tracker in the sibling repo' dissolved)"
run_checker "$fixture"
expect_case "probe exiting nonzero is stale, exit 1, named by date and source" \
  1 'stale (1):' '2026-07-28 · specs/demo/two.md' 'still-blocked (0):'

fixture="$(new_fixture cannot-determine)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-27 specs/demo/three.md \
    'decide the retention policy' undetermined)"
run_checker "$fixture"
expect_case "probe exiting 3 lands in unknown, never stale, exit 0" 0 \
  'unknown (1):' 'stale (0):' 'still-blocked (0):'

fixture="$(new_fixture missing-clause)"
write_human "$fixture" \
  '- [ ] 2026-07-26 · specs/demo/four.md · decide — decide something — Blocks: task 02'
run_checker "$fixture"
expect_case "an entry with no clause is a violation with exit 2" 2 \
  'violation (1):' '2026-07-26 · specs/demo/four.md' 'Still-blocked'

fixture="$(new_fixture unprobed)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-25 specs/demo/five.md \
    'pick a name for the release' 'none — no runnable signal exists yet')"
run_checker "$fixture"
expect_case "none — <reason> lands in unprobed with its reason, exit 0" 0 \
  'unprobed (1):' 'no runnable signal exists yet' 'violation (0):'

fixture="$(new_fixture timeout)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-24 specs/demo/six.md \
    'restart the ingest job' slow)"
run_checker "$fixture" 1
expect_case "a probe past HUMAN_BLOCKER_PROBE_TIMEOUT is unknown, exit 0" 0 \
  'unknown (1):' 'timed out' 'stale (0):'

fixture="$(new_fixture resolved-entry)"
write_human "$fixture" \
  '- [x] 2026-07-23 · specs/demo/seven.md · decide — already handled — Blocks: nothing'
run_checker "$fixture"
expect_case "a checked entry without a clause does not trip exit 2" 0 \
  'violation (0):' 'still-blocked (0):'

fixture="$(new_fixture unbalanced-quote)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-22 specs/demo/eight.md \
    'confirm the export' 'blocked "unterminated')"
run_checker "$fixture"
expect_case "an unbalanced quote is a violation with exit 2" 2 \
  'violation (1):' '2026-07-22 · specs/demo/eight.md'

fixture="$(new_fixture absent-sibling)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-21 specs/demo/nine.md \
    'adopt the tracker in the absent checkout' 'sibling-queue absent')"
run_checker "$fixture"
expect_case "a probe whose sibling checkout is absent is unknown, exit 0" 0 \
  'unknown (1):' 'stale (0):' 'violation (0):'

fixture="$(new_fixture present-sibling)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-20 specs/demo/ten.md \
    'adopt the tracker in the present checkout' 'sibling-queue present')"
run_checker "$fixture"
expect_case "a probe whose sibling checkout is present is still-blocked" 0 \
  'still-blocked (1):' 'stale (0):' 'violation (0):'

fixture="$(new_fixture hostile-command-list)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-19 specs/demo/eleven.md \
    'check the sibling queue' 'bd list; touch SENTINEL')"
run_checker "$fixture"
expect_case "hostile clause 'bd list; touch SENTINEL' is a violation" 2 \
  'violation (1):' '2026-07-19 · specs/demo/eleven.md'
expect_no_sentinel "hostile clause 'bd list; touch SENTINEL' left no SENTINEL"

fixture="$(new_fixture hostile-git-alias)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-18 specs/demo/twelve.md \
    'check the repository state' 'git -c alias.p=!touch\ SENTINEL p')"
run_checker "$fixture"
expect_case "hostile clause 'git -c alias.p=!touch SENTINEL p' is a violation" \
  2 'violation (1):' '2026-07-18 · specs/demo/twelve.md'
expect_no_sentinel "hostile git alias clause left no SENTINEL file"

fixture="$(new_fixture hostile-traversal)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-17 specs/demo/thirteen.md \
    'run the neighbouring helper' '../../../bin/evil')"
run_checker "$fixture"
expect_case "hostile clause '../../../bin/evil' is a violation" 2 \
  'violation (1):' '2026-07-17 · specs/demo/thirteen.md'
expect_no_sentinel "hostile path-traversal clause left no SENTINEL file"

fixture="$(new_fixture hostile-argument)"
plant_armed_repository "$fixture/planted"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-16 specs/demo/fourteen.md \
    'check the planted checkout' "sibling-queue $fixture/planted")"
run_checker "$fixture"
expect_case "a hostile probe argument is refused by the probe's fixed set" 0 \
  'unknown (1):' 'still-blocked (0):' 'stale (0):'
expect_no_sentinel "hostile probe argument (armed core.fsmonitor) left no SENTINEL"

fixture="$(new_fixture unexecutable-probe)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-15 specs/demo/fifteen.md \
    'check the unarmed probe' unarmed)"
run_checker "$fixture"
expect_case "a non-executable probe is a violation, never unknown" 2 \
  'violation (1):' 'unknown (0):'

fixture="$(new_fixture reserved-name)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-14 specs/demo/sixteen.md \
    'check the reserved name' none)"
run_checker "$fixture"
expect_case "the reserved name 'none' without a reason is a violation" 2 \
  'violation (1):' 'unprobed (0):'

fixture="$(new_fixture violation-outranks-stale)"
write_human "$fixture" \
  "$(entry '- [ ]' 2026-07-13 specs/demo/seventeen.md \
    'confirm the dissolved condition' dissolved)" \
  '- [ ] 2026-07-12 · specs/demo/eighteen.md · decide — no clause here — Blocks: task 02'
run_checker "$fixture"
expect_case "a violation outranks a stale entry in the exit code" 2 \
  'violation (1):' 'stale (1):'

printf '\npassed: %d, failed: %d\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
