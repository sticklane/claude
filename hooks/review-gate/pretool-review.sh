#!/usr/bin/env bash
# review-gate PreToolUse hook: denies a Bash `git commit` until an
# adversarial review has been recorded against the exact staged diff
# (bin/review-gate).
#
# Contract:
#   - stdin is the PreToolUse hook payload; `.tool_input.command` is the
#     command about to run and `.cwd` locates the repository.
#   - the command performs a git commit AND `review-gate check` fails ->
#     a permissionDecision "deny" object on stdout, exit 0.
#   - anything else -> no output, exit 0.
#   - every unexpected condition (no jq, malformed payload, no repository,
#     review-gate not found) fails OPEN: no output, exit 0. A broken gate
#     must never wedge commits.
set -u

warn() { printf 'review-gate-hook: %s\n' "$1" >&2; }

COMMIT_ALL=0
COMMIT_AMEND=0
COMMIT_PATHSPEC=0
COMMIT_DIR=""

# scan_commit_args reads the arguments that follow `commit`, recording the
# flags that change what the commit contains and whether a pathspec is present.
# Value-taking flags are consumed with their values, so a message or an author
# is never mistaken for a path.
scan_commit_args() {
  local args=("$@")
  local n="${#args[@]}"
  local i=0 token rest ch
  while [ "$i" -lt "$n" ]; do
    token="${args[$i]}"
    i=$((i + 1))
    case "$token" in
      --)
        [ "$i" -lt "$n" ] && COMMIT_PATHSPEC=1
        return 0
        ;;
      --amend) COMMIT_AMEND=1 ;;
      --all) COMMIT_ALL=1 ;;
      --*=*) ;;
      --message | --file | --author | --date | --reuse-message | --reedit-message | --squash | --fixup | --template | --cleanup | --pathspec-from-file)
        i=$((i + 1))
        ;;
      --*) ;;
      -) COMMIT_PATHSPEC=1 ;;
      -*)
        rest="${token#-}"
        while [ -n "$rest" ]; do
          ch="${rest:0:1}"
          rest="${rest:1}"
          case "$ch" in
            a) COMMIT_ALL=1 ;;
            m | F | c | C | t)
              [ -n "$rest" ] || i=$((i + 1))
              rest=""
              ;;
            S | u) rest="" ;;
          esac
        done
        ;;
      *) COMMIT_PATHSPEC=1 ;;
    esac
  done
}

parse_git_commit() {
  local cmd stripped segment
  # Keep quoted values as single tokens instead of deleting them: a deleted
  # `-C "/path with spaces"` would swallow the following word as its argument
  # and hide the commit entirely. Spaces inside quotes become \001, restored
  # after tokenizing. Heredoc bodies are dropped entirely: text being written
  # to a file is data, not a command.
  cmd="$(printf '%s' "$1" | awk '
    BEGIN { q = ""; hd = ""; hdtab = 0 }
    {
      if (hd != "") {
        t = $0
        if (hdtab) { sub(/^\t+/, "", t) }
        if (t == hd) { hd = ""; hdtab = 0 }
        next
      }
      out = ""
      n = length($0)
      for (i = 1; i <= n; i++) {
        c = substr($0, i, 1)
        if (q == "") {
          if (c == "\"" || c == "'"'"'") { q = c; continue }
          if (c == "<" && substr($0, i + 1, 1) == "<" && substr($0, i + 2, 1) != "<") {
            j = i + 2
            hdtab = 0
            if (substr($0, j, 1) == "-") { hdtab = 1; j++ }
            while (substr($0, j, 1) == " " || substr($0, j, 1) == "\t") { j++ }
            dq = substr($0, j, 1)
            delim = ""
            if (dq == "\"" || dq == "'"'"'") {
              j++
              while (j <= n && substr($0, j, 1) != dq) { delim = delim substr($0, j, 1); j++ }
              j++
            } else {
              while (j <= n) {
                ch = substr($0, j, 1)
                if (ch == " " || ch == "\t" || ch == ";" || ch == "&" || ch == "|" || ch == ")") { break }
                delim = delim ch
                j++
              }
            }
            if (delim != "") { hd = delim; i = j - 1; continue }
            hdtab = 0
          }
          out = out c
        } else {
          if (c == q) { q = ""; continue }
          out = out (c == " " ? "\001" : c)
        }
      }
      print out
    }')"
  stripped="${cmd//&&/$'\n'}"
  stripped="${stripped//||/$'\n'}"
  stripped="${stripped//;/$'\n'}"
  stripped="${stripped//|/$'\n'}"

  while IFS= read -r segment; do
    local -a tokens=()
    read -r -a tokens <<< "$segment"
    [ "${#tokens[@]}" -gt 0 ] || continue
    # Strip what commonly precedes the command word: shell keywords, wrappers,
    # and leading VAR=value assignments. `git commit` inside `if ...; then` or
    # a loop body is still a commit.
    while [ "${#tokens[@]}" -gt 0 ]; do
      case "${tokens[0]}" in
        then | else | elif | do | '{' | '!' | time | command | sudo | exec | nohup | eval)
          tokens=("${tokens[@]:1}") ;;
        env) tokens=("${tokens[@]:1}") ;;
        [A-Za-z_]*=*) tokens=("${tokens[@]:1}") ;;
        *) break ;;
      esac
    done
    [ "${#tokens[@]}" -gt 0 ] || continue
    case "${tokens[0]}" in
      git | */git | '\git') ;;
      *) continue ;;
    esac
    local i=1 token
    while [ "$i" -lt "${#tokens[@]}" ]; do
      token="${tokens[$i]}"
      case "$token" in
        -C)
          COMMIT_DIR="${tokens[$((i + 1))]:-}"
          COMMIT_DIR="${COMMIT_DIR//$'\001'/ }"
          i=$((i + 2))
          ;;
        -c | --git-dir | --work-tree | --namespace | --exec-path | --super-prefix)
          i=$((i + 2))
          ;;
        -*)
          i=$((i + 1))
          ;;
        commit)
          local -a cargs=()
          [ "$((i + 1))" -lt "${#tokens[@]}" ] && cargs=("${tokens[@]:$((i + 1))}")
          scan_commit_args ${cargs[@]+"${cargs[@]}"}
          return 0
          ;;
        *)
          break
          ;;
      esac
    done
  done <<< "$stripped"
  return 1
}

input="$(cat 2>/dev/null || true)"
[ -n "$input" ] || exit 0

command -v jq >/dev/null 2>&1 || {
  warn "jq not found on PATH; allowing"
  exit 0
}

command_line="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)" || {
  warn "malformed hook JSON on stdin; allowing"
  exit 0
}
[ -n "$command_line" ] || exit 0

parse_git_commit "$command_line" || exit 0
[ "${REVIEW_GATE:-1}" != "0" ] || exit 0

BYPASS_CLAUSE="If you have decided this commit should not be gated, run it with REVIEW_GATE=0 in its environment."

emit_deny() {
  jq -nc --arg reason "$1" \
    '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $reason}}'
  exit 0
}

hook_cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null || true)"
if [ -n "$hook_cwd" ] && [ -d "$hook_cwd" ]; then
  cd "$hook_cwd" || exit 0
fi
# `git -C <dir> commit` acts on <dir>, so the gate must decide there.
if [ -n "$COMMIT_DIR" ]; then
  [ -d "$COMMIT_DIR" ] || {
    warn "git -C target $COMMIT_DIR is not a directory; allowing"
    exit 0
  }
  cd "$COMMIT_DIR" || exit 0
fi

git rev-parse --git-common-dir >/dev/null 2>&1 || {
  warn "not inside a git repository; allowing"
  exit 0
}

if [ "$COMMIT_PATHSPEC" -eq 1 ]; then
  emit_deny "This commit names a pathspec, so it would take content straight from the worktree rather than the index — nothing the review gate can key on, and so a commit it cannot gate. Stage the paths you mean (\`git add <paths>\`) and commit without a pathspec; the gate then checks the exact diff the commit would contain. $BYPASS_CLAUSE"
fi

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE="$HOOK_DIR/../../bin/review-gate"
if [ ! -x "$GATE" ]; then
  GATE="$(command -v review-gate 2>/dev/null || true)"
fi
[ -n "$GATE" ] && [ -x "$GATE" ] || {
  warn "bin/review-gate not found; allowing"
  exit 0
}

GATE_FLAGS=()
[ "$COMMIT_ALL" -eq 1 ] && GATE_FLAGS+=(--all)
[ "$COMMIT_AMEND" -eq 1 ] && GATE_FLAGS+=(--amend)

gate_stderr="$("$GATE" check ${GATE_FLAGS[@]+"${GATE_FLAGS[@]}"} 2>&1 >/dev/null)"
gate_status=$?
[ "$gate_status" -eq 0 ] && exit 0

record_cmd="$GATE record${GATE_FLAGS[*]:+ ${GATE_FLAGS[*]}}"
[ -n "$COMMIT_DIR" ] && record_cmd="cd \"$COMMIT_DIR\" && $record_cmd"

if [ "$gate_status" -ne 1 ]; then
  emit_deny "The review gate cannot determine what this commit would contain, so it cannot tell a reviewed commit from an unreviewed one: ${gate_stderr:-review-gate check failed}. Fix that before committing. $BYPASS_CLAUSE"
fi

key="$("$GATE" key ${GATE_FLAGS[@]+"${GATE_FLAGS[@]}"} 2>/dev/null || true)"
[ -n "$key" ] || exit 0

diff_cmd="git diff --cached"
[ "$COMMIT_ALL" -eq 1 ] && diff_cmd="git diff HEAD"
[ "$COMMIT_AMEND" -eq 1 ] && diff_cmd="$diff_cmd HEAD^"

emit_deny "No adversarial review is recorded for the diff this commit would contain (key $key). Before this commit: (1) run an adversarial review of it — dispatch the \`critic\` subagent on \`$diff_cmd\` or run /code-review; (2) record the verdict with \`printf '%s' \"\$verdict\" | $record_cmd\`; (3) then retry the commit. Changing what the commit would contain invalidates the recorded review and requires a fresh one. $BYPASS_CLAUSE"
