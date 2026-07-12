#!/usr/bin/env bash
# Skill eval runner. Usage: evals/run.sh [skill-name]
#
# For each scenario evals/<skill>/<NN-name>/ (optionally filtered to one
# skill): build a fresh fixture via setup.sh, provision the skill under
# test plus the source repo's agents into it, run the scenario prompt
# headlessly, then grade with assert.sh. Prints one pass/fail line per
# scenario and a summary; exits non-zero if any scenario failed.
# Failed fixtures are kept (path printed) for forensics; passing ones
# are deleted.
#
# Env knobs: EVALS_ROOT (scenario dir), SKILLS_ROOT (skill provisioning
# source, for external repos' evals), AGENTS_ROOT (agents provisioning
# source; defaults to SKILLS_ROOT's sibling agents/, skipped if absent),
# MAX_TURNS (claude-code runner turn cap, default 40). A scenario may
# ship an optional teardown.sh — run whenever setup.sh was attempted,
# pass or fail, to reverse external live-service state; its failure
# fails the scenario.
#
# Runtime: the active runtime (`.claude/runtime.md`, default claude-code)
# picks the headless template via runtimes/parse_headless.py — see that
# file's `## Headless` contract. Provisioning always writes BOTH layouts
# (.claude/skills/ and .agents/skills/) regardless of which runtime runs,
# so a fixture is runtime-portable: switch `.claude/runtime.md` to `codex`
# and re-run without re-provisioning. Antigravity has no `## Headless`
# section (no scriptable relaunch), so it cannot run through this path —
# runtimes/parse_headless.py returns NONE and this script exits 1 rather
# than fabricate a run (a repo's `.claude/runtime.md` should not name
# antigravity for evals; see docs/memory/unattended-worker-tool-limits.md).
#
# Compat: scenario setup.sh/assert.sh run under bare `bash`, and macOS's
# system bash is 3.2 — write them to bash 3.2, no `declare -A` or other
# bash-4+ syntax.
set -u -o pipefail
shopt -s nullglob

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Fixed default allowlist — deliberately no Task; fan-out skills add it
# via their scenario's allowed-tools.txt.
DEFAULT_ALLOWED='Read,Edit,Write,Glob,Grep,Bash(git *)'

# EVALS_ROOT override: scenario discovery scans
# $EVALS_ROOT/<skill>/<NN-name>/ instead of this checkout's evals/.
EVALS_ROOT="${EVALS_ROOT:-$ROOT/evals}"

# SKILLS_ROOT override: provision the skill under test from another
# repo's skills dir (e.g. SKILLS_ROOT=~/automation/skills) instead of
# this checkout's .claude/skills/. AGENTS_ROOT defaults to the sibling
# agents/ dir of SKILLS_ROOT and is skipped when absent, so external
# repos without agent definitions just don't get one provisioned.
SKILLS_ROOT="${SKILLS_ROOT:-$ROOT/.claude/skills}"
AGENTS_ROOT="${AGENTS_ROOT:-$(dirname "$SKILLS_ROOT")/agents}"

# MAX_TURNS override for the claude-code runner (MCP-heavy skills may
# need headroom beyond the default).
MAX_TURNS="${MAX_TURNS:-40}"

# Isolate git from the user's global config (signing, hooks, templates)
# for every setup.sh and claude invocation: null the global config and
# inject commit.gpgsign=false via GIT_CONFIG_COUNT so git commands run
# inside the claude session never try to sign. Live-service evalsets set
# EVAL_GIT_ISOLATION=0 to keep the user's real config — their sessions
# and teardowns push to real remotes, which needs the credential helper
# the isolation would strip.
if [ "${EVAL_GIT_ISOLATION:-1}" != "0" ]; then
  export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
  export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false
fi

filter="${1:-}"
if [ -n "$filter" ] && [ ! -d "$SKILLS_ROOT/$filter" ]; then
  echo "unknown skill: $filter" >&2
  exit 1
fi

# Clean up the in-flight fixture on exit or interrupt; kept-on-FAIL
# fixtures set EVAL_DIR="" first so the trap never removes them.
EVAL_DIR=""
trap 'rm -rf "$EVAL_DIR"' EXIT
trap 'exit 130' INT TERM

pass=0
fail=0

for scenario in "$EVALS_ROOT"/*/[0-9][0-9]-*/; do
  scenario="${scenario%/}"
  skill="$(basename "$(dirname "$scenario")")"
  name="$skill/$(basename "$scenario")"
  [ -n "$filter" ] && [ "$skill" != "$filter" ] && continue

  EVAL_DIR="$(mktemp -d)"
  verdict="FAIL"
  setup_ran=0
  if [ ! -d "$SKILLS_ROOT/$skill" ]; then
    reason="unknown skill"
  elif ! { setup_ran=1; EVAL_DIR="$EVAL_DIR" bash "$scenario/setup.sh"; }; then
    reason="setup.sh failed"
  else
    # Provision the skill under test (real skill text is the point of
    # the eval) and the source repo's agents, which fan-out skills
    # spawn (skipped when the repo has none). -L dereferences symlinked
    # skill dirs (external repos often symlink into ~/.claude/skills).
    mkdir -p "$EVAL_DIR/.claude/skills"
    cp -rL "$SKILLS_ROOT/$skill" "$EVAL_DIR/.claude/skills/"
    [ -d "$AGENTS_ROOT" ] && cp -r "$AGENTS_ROOT" "$EVAL_DIR/.claude/agents"

    # Also provision the Agent Skills layout (.agents/skills/) that
    # Antigravity and Codex discover from, unconditionally and regardless
    # of the resolved runtime below — cheap, and harmless for a
    # claude-code run. Source real content, dereferencing symlinks
    # (-L) since codex/.agents/skills/<name> is often a relative symlink
    # into antigravity/ whose target would otherwise dangle outside
    # $EVAL_DIR. Prefer codex's copy (covers the four launch-gated
    # skills' codex-specific SKILL.md); fall back to antigravity's.
    agents_skill_src="$ROOT/codex/.agents/skills/$skill"
    [ -e "$agents_skill_src" ] || agents_skill_src="$ROOT/antigravity/.agents/skills/$skill"
    if [ -e "$agents_skill_src" ]; then
      mkdir -p "$EVAL_DIR/.agents/skills"
      cp -rL "$agents_skill_src" "$EVAL_DIR/.agents/skills/$skill"
      if [ -d "$ROOT/antigravity/.agents/skills/_shared" ]; then
        cp -rL "$ROOT/antigravity/.agents/skills/_shared" "$EVAL_DIR/.agents/skills/"
      fi
    fi

    allowed="$DEFAULT_ALLOWED"
    [ -f "$scenario/allowed-tools.txt" ] && allowed="$(head -n 1 "$scenario/allowed-tools.txt")"

    # RUNNER_CMD override: run a non-Claude headless command instead,
    # word-split, with the scenario prompt appended as the final
    # argument. The resolved allowlist is exported as ALLOWED_TOOLS;
    # custom runners may consume or ignore it. Execution happens inside
    # the fixture dir, so RUNNER_CMD's first word must be absolute or
    # PATH-resolvable.
    session_rc=0
    if [ -n "${RUNNER_CMD:-}" ]; then
      read -r -a runner <<<"$RUNNER_CMD"
      (cd "$EVAL_DIR" && ALLOWED_TOOLS="$allowed" timeout 900 "${runner[@]}" \
          "$(cat "$scenario/prompt.txt")" 2>&1 \
          | tee "$EVAL_DIR/session.log") || session_rc=$?
    else
      # No override set: the default runner derives from the repo's active
      # runtime profile. Absent .claude/runtime.md — or one naming
      # claude-code — keeps today's exact hardcoded `claude -p` line: the
      # inline Claude default, a byte-identical regression path. Any other
      # runtime substitutes the scenario prompt (and allowlist) into that
      # runtime's `## Headless` template, resolved via parse_headless.py.
      # Set EVAL_DRY_RUN=1 to echo the resolved runner instead of invoking
      # it (previewing the derived command without a live session).
      runtime="claude-code"
      if [ -f "$ROOT/.claude/runtime.md" ]; then
        rt_line="$(grep -Ev '^[[:space:]]*(#|$)' "$ROOT/.claude/runtime.md" | head -n 1)"
        case "$rt_line" in
          runtime:*) runtime="$(printf '%s' "${rt_line#runtime:}" | tr -d '[:space:]')" ;;
        esac
      fi

      if [ "$runtime" = "claude-code" ]; then
        if [ -n "${EVAL_DRY_RUN:-}" ]; then
          printf 'DRY-RUN [claude-code] runner: claude -p "<prompt>" --permission-mode dontAsk --max-turns %s --allowed-tools %q\n' "$MAX_TURNS" "$allowed"
        else
          (cd "$EVAL_DIR" && timeout 900 claude -p "$(cat "$scenario/prompt.txt")" \
              --permission-mode dontAsk --max-turns "$MAX_TURNS" --allowed-tools "$allowed" 2>&1 \
              | tee "$EVAL_DIR/session.log") || session_rc=$?
        fi
      else
        template="$(cd "$ROOT" && python3 runtimes/parse_headless.py "$runtime")"
        if [ "$template" = "NONE" ]; then
          echo "eval: runtime '$runtime' has no scriptable headless relaunch (parse_headless.py returned NONE); evals require one" >&2
          exit 1
        fi
        # Word-split the joined template, then replace the placeholder
        # tokens with the concrete prompt/allowlist as single argv
        # elements (so a prompt with spaces is never re-split).
        read -r -a runner <<<"$template"
        prompt_text="$(cat "$scenario/prompt.txt")"
        for i in "${!runner[@]}"; do
          case "${runner[$i]}" in
            '"<prompt>"'|'<prompt>')       runner[$i]="$prompt_text" ;;
            '"<allowlist>"'|'<allowlist>') runner[$i]="$allowed" ;;
          esac
        done
        if [ -n "${EVAL_DRY_RUN:-}" ]; then
          printf 'DRY-RUN [%s] runner:' "$runtime"; printf ' %q' "${runner[@]}"; printf '\n'
        else
          (cd "$EVAL_DIR" && ALLOWED_TOOLS="$allowed" timeout 900 "${runner[@]}" 2>&1 \
              | tee "$EVAL_DIR/session.log") || session_rc=$?
        fi
      fi
    fi
    if [ -n "${EVAL_DRY_RUN:-}" ]; then
      verdict="PASS"
      reason=""
    elif [ "$session_rc" -ne 0 ]; then
      reason="session failed (timeout or non-zero exit)"
    elif ! (cd "$EVAL_DIR" && bash "$scenario/assert.sh"); then
      reason="assert.sh failed"
    else
      verdict="PASS"
      reason=""
    fi
  fi

  # Optional teardown.sh: reverses external (live-service) state the
  # scenario seeded. Runs whenever setup.sh was attempted — even on
  # FAIL, and even when setup itself failed partway — but never in
  # dry-run. A teardown failure means scratch state may have leaked,
  # which must be loud: it fails the scenario.
  if [ "$setup_ran" -eq 1 ] && [ -f "$scenario/teardown.sh" ] && [ -z "${EVAL_DRY_RUN:-}" ]; then
    if ! EVAL_DIR="$EVAL_DIR" bash "$scenario/teardown.sh"; then
      if [ "$verdict" = "PASS" ]; then
        verdict="FAIL"
        reason="teardown.sh failed"
      else
        reason="$reason; teardown.sh also failed"
      fi
    fi
  fi

  if [ "$verdict" = "PASS" ]; then
    rm -rf "$EVAL_DIR"
    pass=$((pass + 1))
    echo "PASS  $name"
  else
    fail=$((fail + 1))
    echo "FAIL  $name ($reason) — fixture kept: $EVAL_DIR"
  fi
  EVAL_DIR=""
done

total=$((pass + fail))
if [ "$total" -eq 0 ]; then
  echo "no scenarios found${filter:+ for skill '$filter'}" >&2
  exit 1
fi
echo "----"
echo "$pass/$total scenarios passed"
[ "$fail" -eq 0 ]
