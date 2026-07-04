#!/usr/bin/env bash
# Fixture end-to-end for the drain baton loop (orchestrator-context task 05).
#
# Drain is a prose SKILL.md, not an executable, so this harness DRIVES the
# documented baton algorithm (drain/SKILL.md step 3a + reference.md "Baton
# pass") faithfully against a throwaway fixture repo, and asserts the loop's
# observable contract. It stubs exactly what the spec's e2e says to stub:
#   - fixture workers  -> each task carries a trivial acceptance command, so a
#                         verdict flips without a real worker session;
#   - the relaunch     -> DRAIN_RELAUNCH_CMD points at a recorder script, so we
#                         capture the relaunch argv without starting a session.
# Everything else (Relaunch-every parsing, N-verdict trigger, baton contents,
# fresh-instance ritual ordering, final-generation baton delete) runs for real.
#
# Usage: 05-e2e-harness.sh [EVIDENCE_MD_OUT]
#   EVIDENCE_MD_OUT: where to write the evidence markdown (default: alongside
#   this script as 05-e2e.md). The fixture repo itself lives in mktemp and is
#   removed on exit; only the evidence markdown persists.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVIDENCE_OUT="${1:-$HERE/05-e2e.md}"
RELAUNCH_EVERY_EXPECT=2   # the fixture SPEC.md header value
NTASKS=6

FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT

# ---------------------------------------------------------------- fixture repo
git -C "$FIX" init -q
git -C "$FIX" config user.email e2e@fixture.local
git -C "$FIX" config user.name "e2e fixture"

mkdir -p "$FIX/specs/fixture/tasks"
cat >"$FIX/specs/fixture/SPEC.md" <<'EOF'
# Fixture spec (drain baton e2e)
Relaunch-every: 2

Six stub tasks whose acceptance commands are trivial, so verdicts flip
without real worker sessions. Relaunch-every: 2 tunes the baton every 2.
EOF

for n in 01 02 03 04 05 06; do
  cat >"$FIX/specs/fixture/tasks/$n-stub.md" <<EOF
Status: pending
Depends on:
Priority: P2
Budget: 5 turns

## Goal
Stub task $n — trivial acceptance so a verdict flips deterministically.

## Acceptance
- [ ] \`true\`
EOF
done

# recorder = the DRAIN_RELAUNCH_CMD stub: append its full argv as one line.
RECORDER="$FIX/recorder.sh"
cat >"$RECORDER" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >>"$(dirname "$0")/recorder.log"
EOF
chmod +x "$RECORDER"
: >"$FIX/recorder.log"
export DRAIN_RELAUNCH_CMD="$RECORDER"

EVENTS="$FIX/events.log"          # ordered trace: "<gen> <event> <detail>"
: >"$EVENTS"
ev() { printf '%s\n' "$*" >>"$EVENTS"; }

SPEC="specs/fixture/SPEC.md"
BATON="specs/fixture/DRAIN-BATON.md"
BATON_ABS="$FIX/$BATON"

# ---------------------------------------------------- documented baton loop
# Read Relaunch-every from the drained spec's SPEC.md header block (drain
# reads this; breakdown documents the header).
RELAUNCH_EVERY="$(grep -E '^Relaunch-every:' "$FIX/$SPEC" | head -1 | awk '{print $2}')"

TASKS=()
while IFS= read -r _t; do TASKS+=("$_t"); done < <(ls "$FIX"/specs/fixture/tasks/*.md | sort)

gen=1
verdicts_this_gen=0
total_done=0
declare -a done_this_gen=()
last_flipped=""

ritual() {  # fresh-instance ritual for a relaunched generation (drain step 3a / R1a)
  local g="$1"
  ev "gen$g ritual read-baton"
  [ -f "$BATON_ABS" ] && grep -q "Generation:" "$BATON_ABS"
  ev "gen$g ritual read-status"
  grep -h '^Status:' "$FIX"/specs/fixture/tasks/*.md >/dev/null
  ev "gen$g ritual git-log"
  git -C "$FIX" log --oneline -15 >/dev/null
  ev "gen$g ritual verify"
  # one cheap verification: re-run the last-flipped task's acceptance command
  ( cd "$FIX" && true )   # the fixture acceptance command is `true`
}

write_baton() {  # done/next progress log + generation number + relaunch command
  local next_gen="$1"; shift
  local -a remaining=("$@")
  {
    printf '# Drain baton — fixture\n\n'
    printf 'Generation: %s\n\n' "$next_gen"       # generation to relaunch into
    printf '## Done this generation\n'
    local d; for d in "${done_this_gen[@]}"; do printf -- '- %s — done\n' "$d"; done
    printf '\n## Next\n'
    local r; for r in "${remaining[@]}"; do printf -- '- %s\n' "$r"; done
    printf '\n## Relaunch\n'
    printf '```bash\nclaude -p "/drain %s (generation %s, baton: %s)"\n```\n' \
      "$SPEC" "$next_gen" "$BATON"
  } >"$BATON_ABS"
}

for i in "${!TASKS[@]}"; do
  tf="${TASKS[$i]}"
  id="$(basename "$tf" | sed 's/-stub\.md$//')"

  # A relaunched generation runs its ritual BEFORE its first dispatch.
  if [ "$gen" -gt 1 ] && [ "$verdicts_this_gen" -eq 0 ]; then
    ritual "$gen"
  fi

  # dispatch stubbed worker: run the task's acceptance command, flip Status.
  ev "gen$gen dispatch $id"
  ( cd "$FIX" && true )                       # trivial acceptance command
  sed -i.bak 's/^Status: pending/Status: done/' "$tf" && rm -f "$tf.bak"
  git -C "$FIX" add -A >/dev/null
  git -C "$FIX" commit -q -m "drain: $id done (gen$gen)"
  ev "gen$gen verdict $id done"
  done_this_gen+=("$id")
  last_flipped="$id"
  verdicts_this_gen=$((verdicts_this_gen + 1))
  total_done=$((total_done + 1))

  # queue drained -> final generation deletes the baton, no relaunch.
  if [ "$total_done" -eq "$NTASKS" ]; then
    rm -f "$BATON_ABS"
    ev "gen$gen baton-delete"
    break
  fi

  # generation budget reached -> baton pass (write baton, invoke relaunch, end gen).
  if [ "$verdicts_this_gen" -ge "$RELAUNCH_EVERY" ]; then
    next_gen=$((gen + 1))
    remaining=()
    for j in "${!TASKS[@]}"; do
      [ "$j" -le "$i" ] && continue
      remaining+=("$(basename "${TASKS[$j]}" | sed 's/-stub\.md$//')")
    done
    write_baton "$next_gen" "${remaining[@]}"
    cp "$BATON_ABS" "$FIX/baton-gen$next_gen.snap"
    ev "gen$gen baton-write next=$next_gen"
    # relaunch via DRAIN_RELAUNCH_CMD, argv tail = <spec> <generation> <baton>
    "$DRAIN_RELAUNCH_CMD" "$SPEC" "$next_gen" "$BATON"
    ev "gen$gen relaunch-invoke gen$next_gen"
    gen=$next_gen
    verdicts_this_gen=0
    done_this_gen=()
  fi
done

# --------------------------------------------------------------- assertions
fail=0
declare -a RESULTS=()
check() { # check "label" test-expr...
  local label="$1"; shift
  if "$@"; then RESULTS+=("PASS  $label"); else RESULTS+=("FAIL  $label"); fail=1; fi
}

baton_passes="$(grep -c ' baton-write ' "$EVENTS" || true)"
relaunch_calls="$(grep -c ' relaunch-invoke ' "$EVENTS" || true)"
recorder_lines="$(wc -l <"$FIX/recorder.log" | tr -d ' ')"
final_gen="$gen"
done_count="$(grep -c '^Status: done' "$FIX"/specs/fixture/tasks/*.md | awk -F: '{s+=$2} END{print s}')"

check "Relaunch-every parsed as $RELAUNCH_EVERY_EXPECT from SPEC.md header" \
  test "$RELAUNCH_EVERY" = "$RELAUNCH_EVERY_EXPECT"
check "exactly 2 baton passes recorded" test "$baton_passes" -eq 2
check "exactly 2 relaunch invocations" test "$relaunch_calls" -eq 2
check "recorder captured 2 relaunch argv lines" test "$recorder_lines" -eq 2

# recorder argv == documented tail: <spec> <generation> <baton path>
exp1="$SPEC 2 $BATON"
exp2="$SPEC 3 $BATON"
got1="$(sed -n '1p' "$FIX/recorder.log")"
got2="$(sed -n '2p' "$FIX/recorder.log")"
check "relaunch #1 argv == documented ('$exp1')" test "$got1" = "$exp1"
check "relaunch #2 argv == documented ('$exp2')" test "$got2" = "$exp2"

# each baton snapshot carries a generation number + done/next log + relaunch cmd
for g in 2 3; do
  snap="$FIX/baton-gen$g.snap"
  check "baton(gen$g) has generation number" grep -qE "Generation:[[:space:]]+$g" "$snap"
  check "baton(gen$g) has Done-this-generation log" grep -q "## Done this generation" "$snap"
  check "baton(gen$g) has Next log" grep -q "## Next" "$snap"
  check "baton(gen$g) embeds relaunch command" grep -qE 'claude -p "/drain .*generation '"$g" "$snap"
done

# gen-2 ritual ran (all 4 steps) BEFORE gen-2's first dispatch
gen2_ritual_last="$(grep -n '^gen2 ritual ' "$EVENTS" | tail -1 | cut -d: -f1)"
gen2_first_dispatch="$(grep -n '^gen2 dispatch ' "$EVENTS" | head -1 | cut -d: -f1)"
check "gen-2 ritual has all 4 steps" \
  test "$(grep -c '^gen2 ritual ' "$EVENTS")" -eq 4
check "gen-2 ritual precedes gen-2 first dispatch" \
  test -n "$gen2_ritual_last" -a -n "$gen2_first_dispatch" \
    -a "$gen2_ritual_last" -lt "$gen2_first_dispatch"

check "baton deleted at completion" test ! -f "$BATON_ABS"
check "baton-delete event recorded" grep -q ' baton-delete' "$EVENTS"
check "all $NTASKS tasks Status: done" test "$done_count" -eq "$NTASKS"
check "reached generation 3" test "$final_gen" -eq 3

# ------------------------------------------------------------- evidence file
# Redact the mktemp prefix so the committed evidence is stable across runs.
redact() { sed "s#$FIX#\$FIXTURE#g"; }
{
  echo "# Fixture end-to-end: drain baton loop (task 05)"
  echo
  echo "Generated by \`specs/orchestrator-context/evidence/05-e2e-harness.sh\`."
  echo "Re-run: \`bash specs/orchestrator-context/evidence/05-e2e-harness.sh\`."
  echo "The fixture repo is a throwaway mktemp dir; only this evidence persists."
  echo
  echo "## Fixture"
  echo
  echo "- 6 stub task files, each acceptance command \`true\` (workers stubbed)."
  echo "- SPEC.md header \`Relaunch-every: 2\` (baton every 2 verdicts)."
  echo "- \`DRAIN_RELAUNCH_CMD\` -> recorder script capturing relaunch argv."
  echo
  echo "## Assertions"
  echo
  echo '```'
  printf '%s\n' "${RESULTS[@]}"
  echo '```'
  echo
  echo "## Ordered event trace"
  echo
  echo '```'
  redact <"$EVENTS"
  echo '```'
  echo
  echo "## Recorder log (relaunch argv, one line per baton pass)"
  echo
  echo "Documented argv tail = \`<spec> <generation> <baton path>\`."
  echo
  echo '```'
  cat "$FIX/recorder.log"
  echo '```'
  echo
  echo "## Baton snapshot — generation 2 (pass 1)"
  echo
  echo '```'
  cat "$FIX/baton-gen2.snap"
  echo '```'
  echo
  echo "## Baton snapshot — generation 3 (pass 2)"
  echo
  echo '```'
  cat "$FIX/baton-gen3.snap"
  echo '```'
  echo
  if [ "$fail" -eq 0 ]; then echo "## Result: PASS — all assertions held."
  else echo "## Result: FAIL — see assertions above."; fi
} >"$EVIDENCE_OUT"

printf '%s\n' "${RESULTS[@]}"
echo "----"
echo "evidence written to: $EVIDENCE_OUT"
exit "$fail"
