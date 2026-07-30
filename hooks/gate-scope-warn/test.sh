#!/usr/bin/env bash
# Behavior tests for scope-check.sh — the Stop hook that notices a gated repo
# whose own Stop gate did not load. Drives the hook against throwaway fixture
# repositories; never touches real session state or any real checkout.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$DIR/scope-check.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0

check() { # check <name> <0|1>
  if [ "$2" -eq 0 ]; then
    pass=$((pass + 1)); printf 'ok   - %s\n' "$1"
  else
    fail=$((fail + 1)); printf 'FAIL - %s\n' "$1"
    printf '       rc=%s out=%s\n' "${RC-}" "${OUT-}"
  fi
}

# gated_repo <name> — a git repo with scripts/check.sh and a Stop hook in its
# own .claude/settings.json: the shape whose gate is supposed to run.
gated_repo() {
  local r="$TMP/$1"
  mkdir -p "$r/scripts" "$r/.claude"
  git -C "$r" init -q . 2>/dev/null || (cd "$r" && git init -q .)
  printf '#!/usr/bin/env bash\nexit 0\n' >"$r/scripts/check.sh"
  chmod +x "$r/scripts/check.sh"
  printf '{"hooks":{"Stop":[{"hooks":[{"type":"command","command":"x"}]}]}}\n' \
    >"$r/.claude/settings.json"
  printf '%s' "$r"
}

run_hook() { # run_hook <cwd> <CLAUDE_PROJECT_DIR> — sets OUT, RC
  OUT="$(printf '{"stop_hook_active":false,"cwd":"%s"}' "$1" \
    | CLAUDE_PROJECT_DIR="$2" bash "$HOOK" 2>&1)"
  RC=$?
}

warns() { printf '%s' "$OUT" | grep -q "gate-scope-warn"; }

GATED="$(gated_repo gated)"

# 1. The reported bug: cwd is inside a gated repo, but the session's project
#    root is somewhere else, so that repo's Stop hooks never loaded.
run_hook "$GATED" "$TMP"
check "warns when the gated repo is not the session's project root" \
  "$([ "$RC" -eq 0 ] && warns && echo 0 || echo 1)"
check "names the repo whose gate did not load" \
  "$(printf '%s' "$OUT" | grep -q "$GATED" && echo 0 || echo 1)"
check "names the check the session skipped" \
  "$(printf '%s' "$OUT" | grep -q 'scripts/check.sh' && echo 0 || echo 1)"

# 2. Correctly-scoped session: the gate loaded, so this hook says nothing.
run_hook "$GATED" "$GATED"
check "silent when the project root IS the gated repo" \
  "$([ "$RC" -eq 0 ] && [ -z "$OUT" ] && echo 0 || echo 1)"

# 3. A repo with no gate installed is not this hook's business.
UNGATED="$TMP/plain"
mkdir -p "$UNGATED"
(cd "$UNGATED" && git init -q .)
run_hook "$UNGATED" "$TMP"
check "silent for a repo with no check script and no Stop hook" \
  "$([ "$RC" -eq 0 ] && [ -z "$OUT" ] && echo 0 || echo 1)"

# 4. A repo with a check script but no Stop hook of its own has nothing that
#    failed to load — the human never asked for a gate there.
HALF="$TMP/half"
mkdir -p "$HALF/scripts"
(cd "$HALF" && git init -q .)
printf '#!/usr/bin/env bash\nexit 0\n' >"$HALF/scripts/check.sh"
chmod +x "$HALF/scripts/check.sh"
run_hook "$HALF" "$TMP"
check "silent for a check script with no Stop hook declared" \
  "$([ "$RC" -eq 0 ] && [ -z "$OUT" ] && echo 0 || echo 1)"

# 5. Loop protection: a Stop already being blocked must not be re-warned.
OUT="$(printf '{"stop_hook_active":true,"cwd":"%s"}' "$GATED" \
  | CLAUDE_PROJECT_DIR="$TMP" bash "$HOOK" 2>&1)"
RC=$?
check "silent when stop_hook_active is true" \
  "$([ "$RC" -eq 0 ] && [ -z "$OUT" ] && echo 0 || echo 1)"

# 6. Never blocks. A warn-only hook that exits nonzero would trap the session.
run_hook "$GATED" "$TMP"
check "exits 0 even when warning" "$([ "$RC" -eq 0 ] && echo 0 || echo 1)"

# 7. Fail-open on junk input, a missing cwd, and an absent CLAUDE_PROJECT_DIR.
OUT="$(printf 'not json' | CLAUDE_PROJECT_DIR="$TMP" bash "$HOOK" 2>&1)"; RC=$?
check "fail-open on malformed stdin" \
  "$([ "$RC" -eq 0 ] && [ -z "$OUT" ] && echo 0 || echo 1)"
run_hook "$TMP/does-not-exist" "$TMP"
check "fail-open on a cwd that does not exist" \
  "$([ "$RC" -eq 0 ] && [ -z "$OUT" ] && echo 0 || echo 1)"
OUT="$(printf '{"stop_hook_active":false,"cwd":"%s"}' "$GATED" \
  | env -u CLAUDE_PROJECT_DIR bash "$HOOK" 2>&1)"; RC=$?
check "fail-open when CLAUDE_PROJECT_DIR is unset" \
  "$([ "$RC" -eq 0 ] && [ -z "$OUT" ] && echo 0 || echo 1)"

# 8. A subdirectory of the gated repo still resolves to its git root.
mkdir -p "$GATED/sub/dir"
run_hook "$GATED/sub/dir" "$TMP"
check "resolves the git root from a subdirectory" \
  "$([ "$RC" -eq 0 ] && warns && echo 0 || echo 1)"

# 9. Project root inside the gated repo (a subdirectory session) still counts
#    as loaded — Claude Code reads the project dir's settings, and the repo's
#    .claude/ is above it only when the root itself is the project.
run_hook "$GATED" "$GATED/sub"
check "warns when the project root is a subdirectory of the gated repo" \
  "$([ "$RC" -eq 0 ] && warns && echo 0 || echo 1)"

printf '\n%s: %d passed, %d failed\n' "$(basename "$DIR")" "$pass" "$fail"
[ "$fail" -eq 0 ]
