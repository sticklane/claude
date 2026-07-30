#!/usr/bin/env bash
# Runtime-neutral Stop hook (SPEC R10): run the repo's canonical check before
# allowing the session to stop. bin/install-gates sets AGENTIC_HOOK_RUNTIME
# and installs this verbatim into the active runtime's project hook directory.
# Fail-open ONLY when scripts/check.sh is missing/unreadable; any non-zero
# exit from an existing check script asks the active runtime to continue.
set -u

warn() { printf 'stop-gate: %s\n' "$1" >&2; }

runtime="${AGENTIC_HOOK_RUNTIME:-claude-code}"
case "$runtime" in
  claude|claude-code) runtime=claude-code ;;
  codex|antigravity) ;;
  *) warn "warning: unknown AGENTIC_HOOK_RUNTIME=$runtime; using Claude Code hook semantics"; runtime=claude-code ;;
esac

# Stop-hook output differs by runtime. Claude Code blocks on exit 2, Codex
# expects decision:block JSON, and Antigravity expects decision:continue JSON.
allow_stop() {
  case "$runtime" in
    codex) printf '{}\n' ;;
    antigravity) printf '{"decision":"allow"}\n' ;;
  esac
  exit 0
}

block_stop() { # block_stop <reason>
  case "$runtime" in
    claude-code)
      printf '%s\n' "$1" >&2
      exit 2
      ;;
    codex)
      jq -n --arg reason "$1" '{decision:"block", reason:$reason}'
      exit 0
      ;;
    antigravity)
      jq -n --arg reason "$1" '{decision:"continue", reason:$reason}'
      exit 0
      ;;
  esac
}

input="$(cat 2>/dev/null || true)"
if [ -z "$input" ]; then
  warn "warning: empty hook input on stdin; skipping check"
  allow_stop
fi
if ! command -v jq >/dev/null 2>&1; then
  warn "warning: jq not found on PATH; skipping check"
  allow_stop
fi
if ! active="$(printf '%s' "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)"; then
  warn "warning: malformed hook JSON on stdin; skipping check"
  allow_stop
fi
if [ "$active" = "true" ]; then
  allow_stop  # loop protection: a previous Stop-hook rejection is already active
fi
if [ "$runtime" = antigravity ]; then
  # Antigravity has no stop_hook_active field. Let the normal runtime keep
  # waiting while background work exists, and cap this gate at one retry.
  fully_idle="$(printf '%s' "$input" | jq -r \
    'if has("fullyIdle") then .fullyIdle else true end' 2>/dev/null || true)"
  execution_num="$(printf '%s' "$input" | jq -r '.executionNum // 0' 2>/dev/null || true)"
  [ "$fully_idle" = "true" ] || allow_stop
  case "$execution_num" in ''|*[!0-9]*) execution_num=0 ;; esac
  [ "$execution_num" -le 1 ] || allow_stop
fi

# Sanctioned stop: unattended workers are contractually required to stop
# mid-red with a final message beginning with a verdict line (DEFERRED,
# BLOCKED, or the verifier's INCOMPLETE) — let such a stop through instead
# of trapping the worker in a block loop. Codex provides the last message
# directly. Claude Code and Antigravity expose a transcript path; the stable
# Claude JSONL shape is used when present and otherwise the one-retry cap is
# the loop-safety boundary.
last="$(printf '%s' "$input" | jq -r '.last_assistant_message // empty' 2>/dev/null || true)"
transcript="$(printf '%s' "$input" | jq -r '.transcript_path // .transcriptPath // empty' 2>/dev/null || true)"
if [ -n "$transcript" ] && [ -r "$transcript" ]; then
  transcript_last="$(tail -50 "$transcript" \
    | jq -rs '[.[] | select(.type == "assistant")] | last
              | .message.content[]? | select(.type == "text") | .text' \
    2>/dev/null || true)"
  [ -n "$transcript_last" ] && last="$transcript_last"
fi
if printf '%s' "$last" | head -1 | grep -qE '^(DEFERRED|BLOCKED|INCOMPLETE)\b'; then
  allow_stop
fi

# Resolve the repo root: hook JSON cwd if present, else current directory,
# widened to the enclosing git toplevel when available.
hook_cwd="$(printf '%s' "$input" | jq -r '.cwd // .workspacePaths[0] // empty' 2>/dev/null || true)"
if [ -n "$hook_cwd" ] && [ -d "$hook_cwd" ]; then
  cd "$hook_cwd" || { warn "warning: cannot cd to $hook_cwd; skipping check"; allow_stop; }
fi
root="$(git rev-parse --show-toplevel 2>/dev/null)" || root="$PWD"

check="$root/scripts/check.sh"
if [ ! -f "$check" ] || [ ! -r "$check" ]; then
  warn "warning: $check missing or unreadable; skipping check (fail-open)"
  allow_stop
fi

# docs-only diff scoping: when every file changed since the last commit
# matches CLAUDE.md's paths-ignore globs (**.md, docs/**, specs/**,
# .claude/**) or is generated tracker export under .beads/, skip the full check — the same convention CLAUDE.md states for
# push-triggered CI, applied to the local Stop-hook gate. A change that
# touches any non-docs path still runs scripts/check.sh in full; this is a
# scoping optimization, never a blanket skip. No change since HEAD (a clean
# tree) is NOT docs-only and runs the check.
#
# .claude/** carve-out: a repo whose root has a `.claude-plugin/` directory
# ships `.claude/` itself as its product (a Claude Code plugin manifest is
# the generic signal, e.g. this toolkit repo) rather than incidental config,
# so a `.claude/**`-only diff there is NOT docs-only and still runs the full
# check — every other docs-only path (`**.md`, `docs/**`, `specs/**`) is
# unaffected and stays skippable regardless of this marker.
changed_paths() { # changed_paths <repo-root> — one working-tree path per line
  local changed line path
  changed="$(git -C "$1" status --porcelain --untracked-files=all 2>/dev/null)" \
    || return 1
  [ -n "$changed" ] || return 1
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    path="${line:3}"                                # strip "XY " status prefix
    case "$path" in *" -> "*) path="${path##* -> }" ;; esac  # rename: destination
    path="${path#\"}"; path="${path%\"}"            # unquote paths with specials
    printf '%s\n' "$path"
  done <<EOF
$changed
EOF
}

docs_only_diff() { # docs_only_diff <repo-root>
  local paths path claude_is_product=0
  [ -d "$1/.claude-plugin" ] && claude_is_product=1
  paths="$(changed_paths "$1")" || return 1
  [ -n "$paths" ] || return 1
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    case "$path" in
      .claude/*) [ "$claude_is_product" -eq 0 ] || return 1 ;;  # product repo: run check
      .beads/*) : ;;                                # generated tracker export
      *.md|docs/*|specs/*) : ;;                     # docs path: keep scanning
      *) return 1 ;;                                 # non-docs change: run check
    esac
  done <<EOF
$paths
EOF
  return 0
}

if docs_only_diff "$root"; then
  warn "docs-only diff since last commit; skipping check"
  allow_stop
fi

# Re-running a multi-minute suite over a tree that has not changed since it
# last passed buys nothing and costs the whole suite, every stop. Worse, a
# CLEAN tree is deliberately not docs-only (above), so committing your work —
# the tidy state — is what makes every subsequent stop pay in full. This keys
# a pass to the exact tree that produced it: same tree, skip; anything moved,
# run. A failing run records nothing, so a red tree re-runs until it is green.
tree_state() { # tree_state <repo-root> — a content key for the working tree
  local digest
  digest="$(command -v shasum || command -v sha256sum)" || return 1
  {
    git -C "$1" rev-parse HEAD 2>/dev/null
    git -C "$1" diff HEAD 2>/dev/null
    git -C "$1" ls-files --others --exclude-standard -z 2>/dev/null \
      | xargs -0 -I{} stat -f '%N %z %m' "$1/{}" 2>/dev/null \
      || git -C "$1" ls-files --others --exclude-standard 2>/dev/null
  } | "$digest" -a 256 2>/dev/null | cut -d' ' -f1
}

pass_marker="$(git -C "$root" rev-parse --git-dir 2>/dev/null)/agentic-stop-gate-pass"
current_state="$(tree_state "$root" 2>/dev/null || true)"
if [ -n "$current_state" ] && [ -r "$pass_marker" ] &&
   [ "$(cat "$pass_marker" 2>/dev/null)" = "$current_state" ]; then
  warn "tree unchanged since the last passing check; skipping"
  allow_stop
fi

# Hand check.sh the changed paths so it can skip a single-language stage whose
# language did not change (run_scoped_stage). An empty or unexported scope
# means "unknown" there and runs everything, so a failure to derive it costs
# time, never coverage.
CHECK_SCOPE="$(changed_paths "$root" || true)"
export CHECK_SCOPE

output="$(cd "$root" && bash "$check" 2>&1)"
status=$?
if [ "$status" -ne 0 ]; then
  block_stop "$output"
fi
[ -n "$current_state" ] && printf '%s\n' "$current_state" >"$pass_marker" 2>/dev/null
allow_stop
