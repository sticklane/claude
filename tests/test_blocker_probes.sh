#!/usr/bin/env bash
# Drive every shipped scripts/blocker-probes/ script against constructed
# inputs. The contract under test is .claude/rules/human-blockers.md's:
# exit 0 while the blocker holds, 3 when the probe cannot determine the
# answer, any other nonzero once the blocker dissolved. Probes take no
# arguments or validate them against a fixed set, and treat argv as hostile.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROBE_DIR="$ROOT/scripts/blocker-probes"
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

expect_exit() {
  local want="$1" got="$2" what="$3"
  if [ "$got" = "$want" ]; then
    ok "$what (exit $got)"
  else
    nope "$what — wanted exit $want, got $got"
  fi
}

run_probe() {
  # run_probe <probe-path> <home> [args...] -> echoes the exit status
  local probe="$1" home="$2"
  shift 2
  (cd "$ROOT" && HOME="$home" "$probe" "$@" >/dev/null 2>&1)
  printf '%s' "$?"
}

plant_determinate_home() {
  # A HOME under which every shipped probe answers definitely — never 3. The
  # argv-refusal cases below run against it so that "refused the argument"
  # (exit 3) is distinguishable from "ignored the argument and answered
  # anyway"; under an unreachable HOME both look like exit 3 and the
  # assertion would hold against a probe that never reads argv at all.
  local home="$TMP/determinate"
  mkdir -p "$home/ynab-mcp-new/.beads"
  printf '%s\n' '{"id":"ynab-1"}' >"$home/ynab-mcp-new/.beads/issues.jsonl"
  printf '%s' "$home"
}

plant_armed_repository() {
  # A directory whose .git/config runs a command on any git invocation that
  # honours it. A probe must never use argv as a repository it runs git in.
  local planted="$TMP/planted"
  mkdir -p "$planted/.git"
  printf '%s\n' \
    '[core]' \
    "  fsmonitor = \"touch $TMP/SENTINEL\"" \
    "  sshCommand = \"touch $TMP/SENTINEL\"" \
    >"$planted/.git/config"
  printf '%s' "$planted"
}

if [ -d "$PROBE_DIR" ]; then
  ok "scripts/blocker-probes/ exists"
else
  nope "scripts/blocker-probes/ exists"
fi

probes=()
if [ -d "$PROBE_DIR" ]; then
  while IFS= read -r probe; do
    probes+=("$probe")
  done < <(find "$PROBE_DIR" -maxdepth 1 -type f | sort)
fi

if [ "${#probes[@]}" -gt 0 ]; then
  ok "scripts/blocker-probes/ ships ${#probes[@]} probe(s)"
else
  nope "scripts/blocker-probes/ ships at least one probe"
fi

# --- the contract every shipped probe owns ---------------------------------
armed="$(plant_armed_repository)"
determinate="$(plant_determinate_home)"
for probe in ${probes[@]+"${probes[@]}"}; do
  name="$(basename "$probe")"

  if [ -x "$probe" ]; then
    ok "$name is executable"
  else
    nope "$name is executable"
  fi

  if printf '%s' "$name" | grep -Eq '^[a-z0-9][a-z0-9-]*$'; then
    ok "$name matches the clause name grammar"
  else
    nope "$name matches the clause name grammar"
  fi

  # An unexpected argument is refused, never acted on: the probe reports
  # "cannot determine" (3) rather than guessing that the blocker dissolved.
  # Both cases run under a HOME the probe answers definitely from, so a probe
  # that ignored argv would return that definite answer and fail them.
  baseline="$(run_probe "$probe" "$determinate")"
  if [ "$baseline" = 3 ]; then
    nope "$name answers definitely under the determinate HOME — got 3, so the argv-refusal cases below cannot tell refusal from indifference; extend plant_determinate_home for $name"
  else
    ok "$name answers definitely under the determinate HOME (exit $baseline)"
  fi

  status="$(run_probe "$probe" "$determinate" "$armed")"
  expect_exit 3 "$status" "$name refuses an unexpected argument"

  status="$(run_probe "$probe" "$determinate" --root "$armed")"
  expect_exit 3 "$status" "$name refuses an unexpected option pair"

  if [ -e "$TMP/SENTINEL" ]; then
    nope "$name left no sentinel when handed a planted repository"
    rm -f "$TMP/SENTINEL"
  else
    ok "$name left no sentinel when handed a planted repository"
  fi

  if grep -Eq '(git|bd)[^|]*\$[{]?[1-9@*]' "$probe"; then
    nope "$name never interpolates argv into a VCS or tracker command"
  else
    ok "$name never interpolates argv into a VCS or tracker command"
  fi
done

# --- ynab-mcp-new-bd-export: all three contract values ---------------------
EXPORT_PROBE="$PROBE_DIR/ynab-mcp-new-bd-export"

fake_home() {
  # fake_home <name> [export-content] -> echoes the HOME to use
  local home="$TMP/home-$1"
  mkdir -p "$home/ynab-mcp-new/.beads"
  if [ "$#" -ge 2 ]; then
    printf '%s' "$2" >"$home/ynab-mcp-new/.beads/issues.jsonl"
  fi
  printf '%s' "$home"
}

if [ -x "$EXPORT_PROBE" ]; then
  status="$(run_probe "$EXPORT_PROBE" "$TMP/no-such-home")"
  expect_exit 3 "$status" "ynab-mcp-new-bd-export cannot determine without the checkout"

  status="$(run_probe "$EXPORT_PROBE" "$(fake_home missing)")"
  expect_exit 0 "$status" "ynab-mcp-new-bd-export still blocked when no export exists"

  status="$(run_probe "$EXPORT_PROBE" "$(fake_home empty '')")"
  expect_exit 0 "$status" "ynab-mcp-new-bd-export still blocked on a zero-byte export"

  populated="$(fake_home populated '{"id":"ynab-1"}
{"id":"ynab-2"}
')"
  status="$(run_probe "$EXPORT_PROBE" "$populated")"
  if [ "$status" != 0 ] && [ "$status" != 3 ]; then
    ok "ynab-mcp-new-bd-export reports stale on a populated export (exit $status)"
  else
    nope "ynab-mcp-new-bd-export reports stale on a populated export — got exit $status"
  fi

  # The probe reads; it must not repair, rewrite, or extend the checkout.
  census_before="$(cd "$populated" && find . -type f | sort)"
  run_probe "$EXPORT_PROBE" "$populated" >/dev/null
  census_after="$(cd "$populated" && find . -type f | sort)"
  if [ "$census_before" = "$census_after" ]; then
    ok "ynab-mcp-new-bd-export leaves the target checkout unchanged"
  else
    nope "ynab-mcp-new-bd-export leaves the target checkout unchanged"
  fi
else
  nope "ynab-mcp-new-bd-export is a shipped executable probe"
fi

printf '\n%s: %s passed, %s failed\n' "$(basename "$0")" "$pass" "$fail"
[ "$fail" -eq 0 ]
