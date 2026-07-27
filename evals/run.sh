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
# Shared script deps are provisioned centrally so scenarios don't hand-copy
# them: .claude/skills/_shared and the top-level runtimes/ land in every
# fixture. A scenario may add an optional skill-deps.txt (one sibling skill
# dir name per line; blanks and #-comments ignored) to also provision skills
# its script loads as a library (e.g. a scanner that loads workboard.py). A
# scenario may also add an optional runner-cmd.txt naming its own default
# RUNNER_CMD (e.g. a permanent stub-CLI-tier scenario's fixture-local stub
# script) — read only when the caller hasn't already set RUNNER_CMD in the
# environment, so an explicit override always wins. This makes the
# documented `evals/run.sh <skill>` invocation run such a scenario
# deterministically without the caller needing to know its stub convention
# out of band.
#
# Env knobs: EVALS_ROOT (scenario dir), SKILLS_ROOT (skill provisioning
# source, for external repos' evals), AGENTS_ROOT (agents provisioning
# source; defaults to SKILLS_ROOT's sibling agents/, skipped if absent),
# MAX_TURNS (claude-code runner turn cap, default 40), SESSION_TIMEOUT
# (headless process ceiling in seconds, default 900), EVAL_BUDGET_USD (spend
# ceiling for the whole run, default 5.00), and EVAL_LEDGER (where the priced
# per-scenario rows append). A scenario may
# provide timeout-seconds.txt when its native orchestration legitimately
# needs a larger ceiling; an explicit SESSION_TIMEOUT overrides that file.
# It may likewise provide max-turns.txt — a trigger scenario needs only enough
# turns to observe the routing decision — which an explicit MAX_TURNS
# overrides. A scenario's assert.sh can call the graders under EVALS_LIB,
# including assert-trigger.sh for trigger scenarios.
# A scenario may
# ship an optional teardown.sh — run whenever setup.sh was attempted,
# pass or fail, to reverse external live-service state; its failure
# fails the scenario.
#
# Runtime: EVAL_RUNTIME explicitly selects the native runtime for this eval
# invocation. It is required whenever no RUNNER_CMD override is present, so a
# Codex or Antigravity caller can never fall through to a Claude Code launch.
# runtimes/parse_headless.py resolves that runtime's `## Headless` contract.
# Provisioning always writes BOTH layouts
# (.claude/skills/ and .agents/skills/) regardless of which runtime runs,
# so a fixture is runtime-portable: switch `.claude/runtime.md` to `codex`
# (confirmed live via `codex exec`) and re-run without re-provisioning. A
# runtime whose profile has no `## Headless` fenced block (returns NONE)
# cannot run through this path and exits 1 rather than fabricate a run
# (docs/memory/unattended-worker-tool-limits.md). `antigravity` has a
# fenced block (`agy -p --new-project ...`) confirmed safe for this path
# live on 2026-07-13 (runtimes/antigravity.md, Headless section) — an
# earlier version without `--new-project` was hard-blocked here after a
# live mutation of real repo files; that block is gone now that the
# template pins the fix.
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

# EVALS_LIB: where the graders a scenario's assert.sh may call live. It tracks
# the runner, not EVALS_ROOT, so an external repo's scenarios can call
# assert-trigger.sh without vendoring it.
EVALS_LIB="$ROOT/evals"
export EVALS_LIB

# SKILLS_ROOT override: provision the skill under test from another
# repo's skills dir (e.g. SKILLS_ROOT=~/automation/skills) instead of
# this checkout's .claude/skills/. AGENTS_ROOT defaults to the sibling
# agents/ dir of SKILLS_ROOT and is skipped when absent, so external
# repos without agent definitions just don't get one provisioned.
SKILLS_ROOT="${SKILLS_ROOT:-$ROOT/.claude/skills}"
AGENTS_ROOT="${AGENTS_ROOT:-$(dirname "$SKILLS_ROOT")/agents}"
RULES_ROOT="${RULES_ROOT:-$(dirname "$SKILLS_ROOT")/rules}"
skills_parent="$(cd "$(dirname "$SKILLS_ROOT")" && pwd)"
if [ "$(basename "$skills_parent")" = .claude ]; then
  default_source_root="$(cd "$skills_parent/.." && pwd)"
else
  default_source_root="$skills_parent"
fi
SOURCE_ROOT="${SOURCE_ROOT:-$default_source_root}"

# MAX_TURNS override for the claude-code runner (MCP-heavy skills may
# need headroom beyond the default).
MAX_TURNS_EXPLICIT="${MAX_TURNS:-}"
MAX_TURNS="${MAX_TURNS:-40}"

# Isolate git from the user's global config (signing, hooks, templates)
# for every setup.sh and claude invocation: null the global config and
# inject commit.gpgsign=false via GIT_CONFIG_COUNT so git commands run
# inside the claude session never try to sign. The isolation also strips
# the user's identity, so inject the fixture identity setup.sh scripts
# use inline (eval/eval@example.com) — without it, a worker's commit
# inside the fixture dies with "Author identity unknown" on any machine
# whose identity lives in the nulled global config. Live-service evalsets
# set EVAL_GIT_ISOLATION=0 to keep the user's real config — their
# sessions and teardowns push to real remotes, which needs the credential
# helper the isolation would strip.
if [ "${EVAL_GIT_ISOLATION:-1}" != "0" ]; then
  export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
  export GIT_CONFIG_COUNT=3 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false
  export GIT_CONFIG_KEY_1=user.name GIT_CONFIG_VALUE_1=eval
  export GIT_CONFIG_KEY_2=user.email GIT_CONFIG_VALUE_2=eval@example.com
fi

filter="${1:-}"
if [ -n "$filter" ] && [ ! -d "$SKILLS_ROOT/$filter" ]; then
  echo "unknown skill: $filter" >&2
  exit 1
fi

# Cost accounting. Every scenario is a paid headless session, so each run
# appends one priced row to EVAL_LEDGER and stops before launching a scenario
# the remaining EVAL_BUDGET_USD cannot cover — projected from the most
# expensive scenario seen so far, so the ceiling holds without knowing a
# scenario's cost in advance. A runtime whose transcript carries no cost field
# records null rather than 0: unknown spend must not read as free.
EVAL_LEDGER="${EVAL_LEDGER:-$ROOT/evals/cost-ledger.jsonl}"
EVAL_BUDGET_USD="${EVAL_BUDGET_USD:-5.00}"
spend=0
worst=0
over_budget=0

# scenario_cost prints the total cost of the session captured in $1, or the
# empty string when the transcript carries no cost field.
scenario_cost() {
  [ -s "$1" ] || return 0
  grep -o '"total_cost_usd":[0-9.]*' "$1" | tail -n 1 | cut -d: -f2
}

# exceeds prints "yes" when $1 is greater than $2, using awk so the comparison
# stays float-correct under bash 3.2.
exceeds() { awk -v a="$1" -v b="$2" 'BEGIN { print (a > b) ? "yes" : "no" }'; }

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

  if [ "$(exceeds "$(awk -v s="$spend" -v w="$worst" 'BEGIN { print s + w }')" "$EVAL_BUDGET_USD")" = yes ]; then
    echo "STOP  budget reached: \$$spend spent of \$$EVAL_BUDGET_USD; not launching $name" >&2
    over_budget=1
    break
  fi

  scenario_timeout="${SESSION_TIMEOUT:-}"
  if [ -z "$scenario_timeout" ] && [ -f "$scenario/timeout-seconds.txt" ]; then
    scenario_timeout="$(head -n 1 "$scenario/timeout-seconds.txt")"
  fi
  # Per-scenario turn cap, mirroring timeout-seconds.txt. A trigger scenario
  # only needs to observe the routing decision, so capping its turns is the
  # difference between reading a verdict and paying for a whole task run.
  scenario_turns="${MAX_TURNS}"
  if [ -z "${MAX_TURNS_EXPLICIT:-}" ] && [ -f "$scenario/max-turns.txt" ]; then
    scenario_turns="$(head -n 1 "$scenario/max-turns.txt" | tr -d '[:space:]')"
  fi
  case "$scenario_turns" in
    *[!0-9]*|'') echo "invalid max turns for $name: $scenario_turns" >&2; exit 1 ;;
  esac

  scenario_timeout="${scenario_timeout:-900}"
  case "$scenario_timeout" in
    *[!0-9]*|'') echo "invalid session timeout for $name: $scenario_timeout" >&2; exit 1 ;;
  esac
  [ "$scenario_timeout" -gt 0 ] ||
    { echo "invalid session timeout for $name: $scenario_timeout" >&2; exit 1; }

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
    [ -d "$RULES_ROOT" ] && cp -r "$RULES_ROOT" "$EVAL_DIR/.claude/rules"
    [ -d "$SOURCE_ROOT/hooks" ] && cp -r "$SOURCE_ROOT/hooks" "$EVAL_DIR/hooks"

    # Provision shared script dependencies centrally so scenarios don't
    # hand-copy them: several skills' scripts import .claude/skills/_shared
    # (headers.py, viz.py, …) and the top-level runtimes/ (parse_headless.py).
    # Both are shared assets, not skills (no SKILL.md), so provisioning them
    # never adds a spurious skill to the sandbox's listing. Sourced the same
    # way as the skill under test — _shared from SKILLS_ROOT, runtimes/ from
    # this checkout — and guarded by existence so external-repo evals that
    # lack them are unaffected.
    [ -d "$SKILLS_ROOT/_shared" ] && cp -rL "$SKILLS_ROOT/_shared" "$EVAL_DIR/.claude/skills/"
    [ -d "$ROOT/runtimes" ] && cp -rL "$ROOT/runtimes" "$EVAL_DIR/runtimes"

    # Optional skill-deps.txt: a scenario naming sibling *skills* its script
    # loads as a library (e.g. drain loading build/beads doctrine). One
    # skill dir name per line; blank lines and #-comments ignored. Provision
    # each dependency into both discovery layouts so the same fixture works
    # under Claude Code and Codex.
    if [ -f "$scenario/skill-deps.txt" ]; then
      while IFS= read -r dep || [ -n "$dep" ]; do
        dep="${dep%%#*}"
        dep="$(printf '%s' "$dep" | tr -d '[:space:]')"
        [ -z "$dep" ] && continue
        if [ -d "$SKILLS_ROOT/$dep" ]; then
          cp -rL "$SKILLS_ROOT/$dep" "$EVAL_DIR/.claude/skills/"
          mkdir -p "$EVAL_DIR/.agents/skills"
          agents_dep_src="$SOURCE_ROOT/.agents/skills/$dep"
          [ -e "$agents_dep_src" ] || agents_dep_src="$SKILLS_ROOT/$dep"
          mkdir -p "$EVAL_DIR/.agents/skills/$dep"
          cp -rL "$agents_dep_src/." "$EVAL_DIR/.agents/skills/$dep/"
        else
          echo "eval: skill-dep '$dep' for '$name' not found under $SKILLS_ROOT (skipped)" >&2
        fi
      done < "$scenario/skill-deps.txt"
    fi

    # Also provision the repository-root Agent Skills layout
    # (.agents/skills/) that Codex discovers from. The portability pivot
    # retired per-runtime mirror trees, so source the shared root symlink
    # and dereference it into the fixture. External SKILLS_ROOT callers fall
    # back to that real skill directory when no root entrypoint exists.
    agents_skill_src="$SOURCE_ROOT/.agents/skills/$skill"
    [ -e "$agents_skill_src" ] || agents_skill_src="$SKILLS_ROOT/$skill"
    if [ -e "$agents_skill_src" ]; then
      mkdir -p "$EVAL_DIR/.agents/skills/$skill"
      cp -rL "$agents_skill_src/." "$EVAL_DIR/.agents/skills/$skill/"
      if [ -d "$SKILLS_ROOT/_shared" ]; then
        cp -rL "$SKILLS_ROOT/_shared" "$EVAL_DIR/.agents/skills/"
      fi
    fi

    allowed="$DEFAULT_ALLOWED"
    [ -f "$scenario/allowed-tools.txt" ] && allowed="$(head -n 1 "$scenario/allowed-tools.txt")"

    # Capture the exact pre-session repository and tracker state after all
    # runner-owned provisioning. Scenario graders that promise non-mutation
    # can compare these snapshots with the post-session fixture without
    # mistaking provisioned skills/rules/hooks for model edits. Store them in
    # the Git directory so the snapshot files do not perturb `git status`.
    : > "$EVAL_DIR/session.log"
    eval_git_dir="$(git -C "$EVAL_DIR" rev-parse --absolute-git-dir 2>/dev/null || true)"
    if [ -n "$eval_git_dir" ]; then
      if command -v bd >/dev/null 2>&1 && [ -d "$EVAL_DIR/.beads" ]; then
        (cd "$EVAL_DIR" && bd list --all --json 2>/dev/null |
          python3 -c 'import json,sys; json.dump(json.load(sys.stdin),sys.stdout,sort_keys=True,separators=(",",":"))') \
          > "$eval_git_dir/eval-pre-session-bd.json" ||
          rm -f "$eval_git_dir/eval-pre-session-bd.json"
      fi
      git -C "$EVAL_DIR" status --porcelain=v1 -uall |
        LC_ALL=C sort > "$eval_git_dir/eval-pre-session-status"
    fi

    # RUNNER_CMD override: run a non-Claude headless command instead,
    # word-split, with the scenario prompt appended as the final
    # argument. The resolved allowlist is exported as ALLOWED_TOOLS;
    # custom runners may consume or ignore it. Execution happens inside
    # the fixture dir, so RUNNER_CMD's first word must be absolute or
    # PATH-resolvable. A scenario's own runner-cmd.txt (see header comment)
    # supplies the default when the caller left RUNNER_CMD unset — computed
    # fresh each loop iteration so one scenario's default never leaks into
    # the next.
    scenario_runner_cmd="${RUNNER_CMD:-}"
    if [ -z "$scenario_runner_cmd" ] && [ -f "$scenario/runner-cmd.txt" ]; then
      scenario_runner_cmd="$(head -n 1 "$scenario/runner-cmd.txt")"
    fi
    session_rc=0
    # EVAL_TRANSCRIPT: absolute path to this run's JSONL transcript, exposed
    # to assert.sh for trajectory assertions. Claude Code and Codex both emit
    # JSONL on stdout under their checked-in headless profiles, so session.log
    # doubles as the transcript for those runtimes. RUNNER_CMD and runtimes
    # without a JSONL profile leave it empty and warn. Resolved and exported
    # centrally after the runner branches, below.
    EVAL_TRANSCRIPT=""
    if [ -n "$scenario_runner_cmd" ]; then
      read -r -a runner <<<"$scenario_runner_cmd"
      (cd "$EVAL_DIR" && ALLOWED_TOOLS="$allowed" timeout "$scenario_timeout" "${runner[@]}" \
          "$(cat "$scenario/prompt.txt")" 2>&1 \
          | tee "$EVAL_DIR/session.log") || session_rc=$?
    else
      # No override set: require the caller to select its own runtime.
      # This guard is intentionally before command resolution — an omitted
      # selector must never turn into another runtime's paid session.
      if [ -z "${EVAL_RUNTIME:-}" ]; then
        echo "eval: EVAL_RUNTIME is required (claude-code, codex, or antigravity); refusing to guess an agent runtime" >&2
        exit 1
      fi
      runtime="$EVAL_RUNTIME"
      case "$runtime" in
        claude|claude-code) runtime=claude-code ;;
        codex|antigravity) ;;
        *)
          echo "eval: unsupported EVAL_RUNTIME '$runtime' (expected claude-code, codex, or antigravity)" >&2
          exit 1
          ;;
      esac

      # The selected runtime substitutes the scenario prompt (and allowlist)
      # into its `## Headless` template, resolved via parse_headless.py.
      # Set EVAL_DRY_RUN=1 to echo the resolved runner instead of invoking
      # it (previewing the derived command without a live session).
      if [ "$runtime" = "claude-code" ]; then
        if [ -n "${EVAL_DRY_RUN:-}" ]; then
          printf 'DRY-RUN [claude-code] runner: claude -p "<prompt>" --output-format stream-json --verbose --permission-mode dontAsk --max-turns %s --allowed-tools %q\n' "$scenario_turns" "$allowed"
        else
          # --output-format stream-json --verbose makes claude emit a JSONL
          # transcript on stdout; tee captures it as session.log, which then
          # doubles as EVAL_TRANSCRIPT (a single invocation cannot emit both
          # plaintext and JSONL, so session.log IS the transcript).
          (cd "$EVAL_DIR" && timeout "$scenario_timeout" claude -p "$(cat "$scenario/prompt.txt")" \
              --output-format stream-json --verbose \
              --permission-mode dontAsk --max-turns "$scenario_turns" --allowed-tools "$allowed" 2>&1 \
              | tee "$EVAL_DIR/session.log") || session_rc=$?
          EVAL_TRANSCRIPT="$EVAL_DIR/session.log"
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
        # Drain's Codex adapter writes Git refs/worktrees through the common
        # Git directory. The generic Codex profile stays workspace-write for
        # ordinary skills; an explicit/active Codex drain eval raises only
        # this scenario to the documented trusted-fixture prerequisite.
        if [ "$runtime" = codex ] && [ "$skill" = drain ]; then
          i=0
          while [ "$i" -lt "${#runner[@]}" ]; do
            if [ "${runner[$i]}" = --sandbox ] &&
               [ "$((i + 1))" -lt "${#runner[@]}" ]; then
              runner[$((i + 1))]=danger-full-access
            fi
            i=$((i + 1))
          done
        fi
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
          (cd "$EVAL_DIR" && ALLOWED_TOOLS="$allowed" timeout "$scenario_timeout" "${runner[@]}" 2>&1 \
              | tee "$EVAL_DIR/session.log") || session_rc=$?
          if [ "$runtime" = codex ]; then
            EVAL_TRANSCRIPT="$EVAL_DIR/session.log"
          fi
        fi
      fi
    fi
    # Resolve and export EVAL_TRANSCRIPT for assert.sh. A candidate path is
    # set by a JSONL-capable runtime branch above; keep it when the file was
    # actually produced and is non-empty, otherwise clear it and warn so an
    # assertion that requires a transcript fails loudly instead of reading a
    # stale or missing path. Skipped under dry-run (no session, no assert.sh).
    if [ -z "${EVAL_DRY_RUN:-}" ]; then
      if [ -z "$EVAL_TRANSCRIPT" ] || [ ! -s "$EVAL_TRANSCRIPT" ]; then
        EVAL_TRANSCRIPT=""
        echo "eval: no locatable transcript for '$name'; EVAL_TRANSCRIPT is empty (assertions requiring it must fail loudly)" >&2
      fi
      export EVAL_TRANSCRIPT
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

  if [ -z "${EVAL_DRY_RUN:-}" ]; then
    cost="$(scenario_cost "$EVAL_DIR/session.log")"
    printf '{"at":"%s","skill":"%s","scenario":"%s","runtime":"%s","verdict":"%s","cost_usd":%s}\n' \
      "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$skill" "$(basename "$scenario")" \
      "${EVAL_RUNTIME:-claude-code}" "$verdict" "${cost:-null}" >> "$EVAL_LEDGER"
    if [ -n "$cost" ]; then
      spend="$(awk -v s="$spend" -v c="$cost" 'BEGIN { printf "%.4f", s + c }')"
      [ "$(exceeds "$cost" "$worst")" = yes ] && worst="$cost"
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
echo "spend: \$$spend of \$$EVAL_BUDGET_USD budget (ledger: $EVAL_LEDGER)"
[ "$over_budget" -eq 0 ] && [ "$fail" -eq 0 ]
