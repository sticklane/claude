#!/usr/bin/env bash
# gate-scope-warn: a USER-level Stop hook that notices when the repository you
# are actually working in is gated, but its gate never loaded.
#
# Claude Code reads project hooks from the session's project directory. A
# session launched at $HOME that then commits into ~/claude gets none of
# ~/claude/.claude/settings.json's hooks — its Stop gate, its bd-compliance
# check, its formatter. Nothing announces the absence: the gate is not
# bypassed, it was never there. Measured 2026-07-29: a session rooted at
# /Users/sjaconette landed 21 commits in ~/claude with zero Stop-hook runs,
# while the repo's git pre-commit review gate fired on every one of them —
# so the loud gate was the weak one and the strong gate was silent.
#
# This hook must be wired in ~/.claude/settings.json (user level), because a
# project-level hook cannot warn about project hooks that did not load.
#
# Warn-only and silent unless the mismatch is real: it prints when the git
# root containing the session's cwd both ships scripts/check.sh and declares
# its own Stop hook, yet is not the session's project root. It never blocks —
# an advisory that traps a session would be worse than the gap it reports.
# Fail-open on every missing dependency or parse error.
set -u

exit_quiet() { exit 0; }

command -v jq >/dev/null 2>&1 || exit_quiet

payload="$(cat 2>/dev/null || true)"
[ -n "$payload" ] || exit_quiet

active="$(printf '%s' "$payload" | jq -r '.stop_hook_active // false' 2>/dev/null)" \
  || exit_quiet
[ "$active" = "true" ] && exit_quiet

# The project root the harness loaded settings from. Unset means we cannot
# compare, so we say nothing rather than guess.
project="${CLAUDE_PROJECT_DIR:-}"
[ -n "$project" ] || exit_quiet

cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null || true)"
[ -n "$cwd" ] && [ -d "$cwd" ] || exit_quiet

root="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)" || exit_quiet
[ -n "$root" ] || exit_quiet

# Only repositories that asked for a gate are this hook's business: a check
# script AND a Stop hook the repo declares for itself.
[ -r "$root/scripts/check.sh" ] || exit_quiet
settings="$root/.claude/settings.json"
[ -r "$settings" ] || exit_quiet
jq -e '(.hooks.Stop // []) | length > 0' "$settings" >/dev/null 2>&1 || exit_quiet

# Resolve both sides before comparing so a symlinked or relative project dir
# does not read as a mismatch.
resolve() { (cd "$1" 2>/dev/null && pwd -P) || printf '%s' "$1"; }
root_real="$(resolve "$root")"
project_real="$(resolve "$project")"

[ "$root_real" = "$project_real" ] && exit_quiet

printf 'gate-scope-warn: this session'"'"'s project root is %s, but you are working in %s.\n' \
  "$project_real" "$root_real" >&2
printf 'gate-scope-warn: that repository declares its own Stop hooks, which do NOT load for this session — its gate has not run.\n' >&2
printf 'gate-scope-warn: run `cd %s && bash scripts/check.sh` yourself before calling the work done, or restart the session with %s as its project root.\n' \
  "$root_real" "$root_real" >&2
exit 0
