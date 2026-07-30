#!/usr/bin/env bash
# Executable definition of the acceptance-block grammar
# (specs/drain-economy, EP11; doctrine in
# docs/memory/acceptance-block-grammar.md).
#
# This file owns the reference parser: `parse_acceptance_block` below is the
# one runnable statement of the grammar until bin/spec-gate (task 08) consumes
# it. A criterion line is:
#
#   - [ ] A<k> (<cheap|expensive>): `<command>` — <expected>
set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

pass=0
fail=0

assert() {
  local desc="$1" ok="$2"
  if [ "$ok" -eq 0 ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  fi
}

# --- the reference parser ---------------------------------------------------
# Reads a block on stdin. Prints one `A<k>|<tier>` record per criterion in
# source order. Exits 0 when every criterion line conforms and every id is
# unique; exits 1 with a reason on stderr otherwise.
CRITERION_RE='^- \[[ x]\] (A[0-9]+) \((cheap|expensive)\): `([^`]+)` — (.+)$'

parse_acceptance_block() {
  local line seen=" " ids=0
  while IFS= read -r line; do
    case "$line" in
      '- '*) ;;
      *) continue ;;
    esac
    if [[ ! "$line" =~ $CRITERION_RE ]]; then
      echo "non-conforming criterion line: $line" >&2
      return 1
    fi
    local id="${BASH_REMATCH[1]}" tier="${BASH_REMATCH[2]}"
    case "$seen" in
      *" $id "*)
        echo "duplicate criterion id: $id" >&2
        return 1
        ;;
    esac
    seen="$seen$id "
    ids=$((ids + 1))
    printf '%s|%s\n' "$id" "$tier"
  done
  if [ "$ids" -eq 0 ]; then
    echo "acceptance block has no criteria" >&2
    return 1
  fi
  return 0
}

extract_block() {
  # $1 = file, $2 = heading. Emits the criterion lines of that section.
  awk -v heading="$2" '
    $0 == heading { inblock = 1; next }
    inblock && /^## / { exit }
    inblock { print }
  ' "$1"
}

# --- fixtures ---------------------------------------------------------------
conforming="$tmp/conforming.md"
cat >"$conforming" <<'BLOCK'
- [ ] A1 (cheap): `bash tests/test_command_policy.sh` — exits 0 (R1)
- [ ] A2 (cheap): `bin/spec-gate drain-economy --tier cheap` — exit 0 (R2)
- [ ] A3 (expensive): `evals/run.sh drain` — the NOT-READY fixture is refused
BLOCK

missing_id="$tmp/missing-id.md"
cat >"$missing_id" <<'BLOCK'
- [ ] (cheap): `bash tests/test_command_policy.sh` — exits 0
BLOCK

unknown_tier="$tmp/unknown-tier.md"
cat >"$unknown_tier" <<'BLOCK'
- [ ] A1 (medium): `bash tests/test_command_policy.sh` — exits 0
BLOCK

no_command="$tmp/no-command.md"
cat >"$no_command" <<'BLOCK'
- [ ] A1 (cheap): run the command policy tests — they exit 0
BLOCK

duplicate_ids="$tmp/duplicate-ids.md"
cat >"$duplicate_ids" <<'BLOCK'
- [ ] A1 (cheap): `bash tests/test_command_policy.sh` — exits 0
- [ ] A1 (cheap): `bash tests/test_doc_links.sh` — exits 0
BLOCK

# --- conforming block: parses, and every id and tier is recovered -----------
recovered="$(parse_acceptance_block <"$conforming" 2>"$tmp/err")"
status=$?
assert "conforming block parses (exit 0)" "$status"
expected_records='A1|cheap
A2|cheap
A3|expensive'
if [ "$recovered" = "$expected_records" ]; then
  assert "conforming block recovers every id and tier" 0
else
  assert "conforming block recovers every id and tier (got: $recovered)" 1
fi

# --- malformed fixtures, one case each --------------------------------------
reject_case() {
  local desc="$1" fixture="$2"
  if parse_acceptance_block <"$fixture" >/dev/null 2>&1; then
    assert "$desc is rejected" 1
  else
    assert "$desc is rejected" 0
  fi
}

reject_case "a criterion with a missing id" "$missing_id"
reject_case "a criterion with an unknown tier" "$unknown_tier"
reject_case "a criterion with no backticked command" "$no_command"
reject_case "a block with duplicate ids" "$duplicate_ids"

# --- the /idea SPEC.md template emits the grammar ---------------------------
idea_skill="$repo_root/.claude/skills/idea/SKILL.md"
if [ ! -f "$idea_skill" ]; then
  assert "/idea SKILL.md exists" 1
else
  template_block="$tmp/idea-template.md"
  extract_block "$idea_skill" "## Acceptance criteria" >"$template_block"
  template_records="$(parse_acceptance_block <"$template_block" 2>"$tmp/idea-err")"
  template_status=$?
  if [ "$template_status" -eq 0 ]; then
    assert "the /idea SPEC.md template's acceptance block parses" 0
  else
    assert "the /idea SPEC.md template's acceptance block parses ($(cat "$tmp/idea-err"))" 1
  fi
  if printf '%s\n' "$template_records" | grep -q '^A1|'; then
    assert "the /idea template's criteria carry ids" 0
  else
    assert "the /idea template's criteria carry ids" 1
  fi
fi

# --- the grammar doc exists and states its binding rules --------------------
grammar_doc="$repo_root/docs/memory/acceptance-block-grammar.md"
if [ ! -f "$grammar_doc" ]; then
  assert "docs/memory/acceptance-block-grammar.md exists" 1
else
  assert "docs/memory/acceptance-block-grammar.md exists" 0
  for phrase in 'acceptance-block grammar' 'anchored-acceptance-criteria' \
    'read-only' 'expensive' 'conform acceptance block to grammar'; do
    if grep -qF "$phrase" "$grammar_doc"; then
      assert "grammar doc states '$phrase'" 0
    else
      assert "grammar doc states '$phrase'" 1
    fi
  done
  # The doc's own worked example must itself parse under the parser above.
  doc_example="$tmp/doc-example.md"
  extract_block "$grammar_doc" "## Worked example" >"$doc_example"
  if parse_acceptance_block <"$doc_example" >/dev/null 2>&1; then
    assert "the grammar doc's worked example parses" 0
  else
    assert "the grammar doc's worked example parses" 1
  fi
fi

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ]
