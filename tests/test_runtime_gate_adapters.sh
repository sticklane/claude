#!/usr/bin/env bash
# Native Codex and Antigravity lifecycle adapters for bin/install-gates.
# Fixtures are isolated temp git repos; no installed user config is touched.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL="$TOOLKIT_DIR/bin/install-gates"

pass=0
fail=0

assert() { # assert <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    printf 'FAIL: %s\n' "$desc" >&2
  fi
}

assert_not() { # assert_not <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    fail=$((fail + 1))
    printf 'FAIL: %s\n' "$desc" >&2
  else
    pass=$((pass + 1))
  fi
}

assert_eq() { # assert_eq <description> <expected> <actual>
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    printf "FAIL: %s (expected '%s', got '%s')\n" "$desc" "$expected" "$actual" >&2
  fi
}

assert "canonical runtime gate adapter test remains installed" \
  test -f "$TOOLKIT_DIR/tests/test_runtime_gate_adapters.sh"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkrepo() { # mkrepo <path>
  mkdir -p "$1"
  git -C "$1" init -q
  printf 'requests\n' > "$1/requirements.txt"
}

run_install() { # run_install <args...>
  INSTALL_OUT="$("$INSTALL" "$@" 2>&1)"
  INSTALL_EXIT=$?
}

run_hook() { # run_hook <runtime> <script> <payload> <cwd>
  local runtime="$1" script="$2" payload="$3" cwd="$4"
  local out_file="$TMP/hook.out" err_file="$TMP/hook.err"
  (
    cd "$cwd" || exit 97
    printf '%s' "$payload" |
      AGENTIC_HOOK_RUNTIME="$runtime" "$script" >"$out_file" 2>"$err_file"
  )
  HOOK_EXIT=$?
  HOOK_OUT="$(cat "$out_file")"
  HOOK_ERR="$(cat "$err_file")"
}

managed_hash() { # managed_hash <repo> <runtime-dir> <guidance>
  find "$1/$2" "$1/scripts" "$1/.git/hooks/pre-commit" "$1/$3" \
    -type f -exec shasum -a 256 {} + 2>/dev/null | sort
}

# ---------------------------------------------------------------------------
# Codex: native project config, opaque merge, hook contracts, idempotence.
# ---------------------------------------------------------------------------

CODEX_REPO="$TMP/codex repo"
mkrepo "$CODEX_REPO"
mkdir -p "$CODEX_REPO/.codex" "$CODEX_REPO/.beads"
cat > "$CODEX_REPO/.codex/hooks.json" <<'EOF'
{
  "description": "keep me",
  "hooks": {
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "echo existing"}]}
    ]
  }
}
EOF
printf '# Existing Codex guidance\n' > "$CODEX_REPO/AGENTS.md"

run_install --runtime codex "$CODEX_REPO"
assert_eq "codex installer exits 0" 0 "$INSTALL_EXIT"
assert "codex reports selected runtime" grep -q 'runtime: codex' <<<"$INSTALL_OUT"
assert "codex writes .codex/hooks.json" test -f "$CODEX_REPO/.codex/hooks.json"
assert_not "codex writes no Claude lifecycle config" test -e "$CODEX_REPO/.claude"
assert "codex hook config remains valid JSON" jq -e . "$CODEX_REPO/.codex/hooks.json"
assert "codex opaque merge preserves description" \
  jq -e '.description == "keep me"' "$CODEX_REPO/.codex/hooks.json"
assert "codex opaque merge preserves existing hook" \
  jq -e '.hooks.SessionStart[0].hooks[0].command == "echo existing"' \
  "$CODEX_REPO/.codex/hooks.json"
assert "codex wires native file protection" \
  jq -e '.hooks.PreToolUse | tostring | contains("AGENTIC_HOOK_RUNTIME=codex")' \
  "$CODEX_REPO/.codex/hooks.json"
assert "codex wires native auto-format" \
  jq -e '.hooks.PostToolUse | tostring | contains("post-tool-format.sh")' \
  "$CODEX_REPO/.codex/hooks.json"
assert "codex wires native Stop gate" \
  jq -e '.hooks.Stop | tostring | contains("stop-gate.sh")' \
  "$CODEX_REPO/.codex/hooks.json"
assert "codex wires native bd-compliance Stop handler" \
  jq -e '.hooks.Stop | tostring | contains("bd-compliance.sh")' \
  "$CODEX_REPO/.codex/hooks.json"
assert "codex installs native bd-compliance script" \
  test -x "$CODEX_REPO/.codex/hooks/bd-compliance.sh"
assert "codex stamps AGENTS.md without losing content" \
  grep -q '^# Existing Codex guidance' "$CODEX_REPO/AGENTS.md"
assert_not "codex does not create CLAUDE.md" test -e "$CODEX_REPO/CLAUDE.md"

codex_hash_1="$(managed_hash "$CODEX_REPO" .codex AGENTS.md)"
run_install --runtime codex "$CODEX_REPO"
codex_hash_2="$(managed_hash "$CODEX_REPO" .codex AGENTS.md)"
assert_eq "codex second install exits 0" 0 "$INSTALL_EXIT"
assert_eq "codex install is byte-idempotent" "$codex_hash_1" "$codex_hash_2"
assert_eq "codex has one Stop gate after re-install" 1 \
  "$(jq '[.hooks.Stop[] | tostring | select(contains("stop-gate.sh"))] | length' \
    "$CODEX_REPO/.codex/hooks.json")"

codex_protected="$(jq -nc --arg cwd "$CODEX_REPO" '{
  cwd:$cwd, tool_name:"apply_patch",
  tool_input:{command:"*** Begin Patch\n*** Update File: .env\n@@\n-old\n+new\n*** End Patch"}
}')"
run_hook codex "$CODEX_REPO/.codex/hooks/pre-tool-protect.sh" \
  "$codex_protected" "$CODEX_REPO"
assert_eq "codex protected-file hook returns successfully with JSON decision" 0 "$HOOK_EXIT"
assert "codex protected-file hook returns native deny" \
  jq -e '.hookSpecificOutput.permissionDecision == "deny"' <<<"$HOOK_OUT"

mkdir -p "$TMP/fake-bin"
cat > "$TMP/fake-bin/ruff" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$FORMAT_LOG"
exit 0
EOF
chmod 755 "$TMP/fake-bin/ruff"
printf 'x=1\n' > "$CODEX_REPO/app.py"
codex_format="$(jq -nc --arg cwd "$CODEX_REPO" '{
  cwd:$cwd, tool_name:"apply_patch",
  tool_input:{command:"*** Begin Patch\n*** Update File: app.py\n@@\n-x=1\n+x = 1\n*** End Patch"}
}')"
FORMAT_LOG="$TMP/codex-format.log"
export FORMAT_LOG
PATH="$TMP/fake-bin:$PATH"
export PATH
run_hook codex "$CODEX_REPO/.codex/hooks/post-tool-format.sh" \
  "$codex_format" "$CODEX_REPO"
assert_eq "codex formatter hook exits 0" 0 "$HOOK_EXIT"
assert "codex formatter extracts apply_patch target" \
  grep -q 'format .*/app.py' "$FORMAT_LOG"
assert "codex formatter returns valid empty JSON" jq -e 'length == 0' <<<"$HOOK_OUT"

cat > "$CODEX_REPO/scripts/check.sh" <<'EOF'
#!/usr/bin/env bash
printf 'codex check failed\n'
exit 1
EOF
chmod 755 "$CODEX_REPO/scripts/check.sh"
codex_stop="$(jq -nc --arg cwd "$CODEX_REPO" '{
  cwd:$cwd, stop_hook_active:false, last_assistant_message:"Done"
}')"
run_hook codex "$CODEX_REPO/.codex/hooks/stop-gate.sh" "$codex_stop" "$CODEX_REPO"
assert_eq "codex failing Stop hook exits 0 with decision JSON" 0 "$HOOK_EXIT"
assert "codex failing Stop hook asks Codex to continue" \
  jq -e '.decision == "block" and (.reason | contains("codex check failed"))' <<<"$HOOK_OUT"

# ---------------------------------------------------------------------------
# Antigravity: native named-hook config and camelCase hook contracts.
# ---------------------------------------------------------------------------

AG_REPO="$TMP/antigravity repo"
mkrepo "$AG_REPO"
mkdir -p "$AG_REPO/.agents" "$AG_REPO/.beads"
cat > "$AG_REPO/.agents/hooks.json" <<'EOF'
{
  "existing-team-hook": {
    "enabled": false,
    "PreInvocation": [{"type": "command", "command": "echo existing"}]
  }
}
EOF
printf '# Existing Antigravity guidance\n' > "$AG_REPO/AGENTS.md"

run_install --runtime antigravity "$AG_REPO"
assert_eq "antigravity installer exits 0" 0 "$INSTALL_EXIT"
assert "antigravity reports selected runtime" \
  grep -q 'runtime: antigravity' <<<"$INSTALL_OUT"
assert "antigravity writes .agents/hooks.json" test -f "$AG_REPO/.agents/hooks.json"
assert_not "antigravity writes no Claude lifecycle config" test -e "$AG_REPO/.claude"
assert "antigravity hook config remains valid JSON" jq -e . "$AG_REPO/.agents/hooks.json"
assert "antigravity opaque merge preserves existing named hook" \
  jq -e '.["existing-team-hook"].enabled == false' "$AG_REPO/.agents/hooks.json"
assert "antigravity wires native file-tool matcher" \
  jq -e '.["agentic-protected-files"].PreToolUse[0].matcher
    == "write_to_file|replace_file_content|multi_replace_file_content"' \
  "$AG_REPO/.agents/hooks.json"
assert "antigravity Stop uses direct handler list" \
  jq -e '.["agentic-stop-gate"].Stop[0].type == "command"' \
  "$AG_REPO/.agents/hooks.json"
assert "antigravity wires separate native bd-compliance handler" \
  jq -e '.["agentic-bd-compliance"].Stop[0].command
    | contains("bd-compliance.sh")' "$AG_REPO/.agents/hooks.json"
assert "antigravity installs native bd-compliance script" \
  test -x "$AG_REPO/.agents/hooks/bd-compliance.sh"
assert "antigravity commands select their native adapter" \
  jq -e 'tostring | contains("AGENTIC_HOOK_RUNTIME=antigravity")' \
  "$AG_REPO/.agents/hooks.json"
assert_not "antigravity does not create CLAUDE.md" test -e "$AG_REPO/CLAUDE.md"

ag_hash_1="$(managed_hash "$AG_REPO" .agents AGENTS.md)"
run_install --runtime antigravity "$AG_REPO"
ag_hash_2="$(managed_hash "$AG_REPO" .agents AGENTS.md)"
assert_eq "antigravity second install exits 0" 0 "$INSTALL_EXIT"
assert_eq "antigravity install is byte-idempotent" "$ag_hash_1" "$ag_hash_2"
assert_eq "antigravity has one Stop handler after re-install" 1 \
  "$(jq '[.["agentic-stop-gate"].Stop[] | select(.command | contains("stop-gate.sh"))]
    | length' "$AG_REPO/.agents/hooks.json")"

ag_protected="$(jq -nc '{
  conversationId:"gate-test",
  toolCall:{name:"write_to_file",args:{TargetFile:".env"}}
}')"
run_hook antigravity "$AG_REPO/.agents/hooks/pre-tool-protect.sh" \
  "$ag_protected" "$AG_REPO"
assert_eq "antigravity protected-file hook exits 0" 0 "$HOOK_EXIT"
assert "antigravity protected-file hook returns native deny" \
  jq -e '.decision == "deny"' <<<"$HOOK_OUT"

printf 'x=1\n' > "$AG_REPO/app.py"
ag_allowed="$(jq -nc --arg file "$AG_REPO/app.py" '{
  conversationId:"gate-format",
  toolCall:{name:"replace_file_content",args:{TargetFile:$file}}
}')"
run_hook antigravity "$AG_REPO/.agents/hooks/pre-tool-protect.sh" \
  "$ag_allowed" "$AG_REPO"
assert "antigravity allowed file edit returns native allow" \
  jq -e '.decision == "allow"' <<<"$HOOK_OUT"
FORMAT_LOG="$TMP/antigravity-format.log"
export FORMAT_LOG
ag_post="$(jq -nc --arg workspace "$AG_REPO" '{
  conversationId:"gate-format", workspacePaths:[$workspace], stepIdx:1, error:""
}')"
run_hook antigravity "$AG_REPO/.agents/hooks/post-tool-format.sh" \
  "$ag_post" "$AG_REPO"
assert_eq "antigravity formatter hook exits 0" 0 "$HOOK_EXIT"
assert "antigravity formatter uses PreToolUse-captured target" \
  grep -q 'format .*/app.py' "$FORMAT_LOG"
assert "antigravity PostToolUse returns required empty JSON" \
  jq -e 'length == 0' <<<"$HOOK_OUT"

cat > "$AG_REPO/scripts/check.sh" <<'EOF'
#!/usr/bin/env bash
printf 'antigravity check failed\n'
exit 1
EOF
chmod 755 "$AG_REPO/scripts/check.sh"
ag_stop="$(jq -nc --arg workspace "$AG_REPO" '{
  executionNum:1, terminationReason:"model_stop", fullyIdle:true,
  workspacePaths:[$workspace]
}')"
run_hook antigravity "$AG_REPO/.agents/hooks/stop-gate.sh" "$ag_stop" "$AG_REPO"
assert_eq "antigravity failing Stop hook exits 0 with decision JSON" 0 "$HOOK_EXIT"
assert "antigravity failing Stop hook asks Antigravity to continue" \
  jq -e '.decision == "continue"
    and (.reason | contains("antigravity check failed"))' <<<"$HOOK_OUT"

ag_busy="$(jq -nc --arg workspace "$AG_REPO" '{
  executionNum:1, terminationReason:"model_stop", fullyIdle:false,
  workspacePaths:[$workspace]
}')"
run_hook antigravity "$AG_REPO/.agents/hooks/stop-gate.sh" "$ag_busy" "$AG_REPO"
assert "antigravity Stop permits runtime with background work" \
  jq -e '.decision == "allow"' <<<"$HOOK_OUT"

# No native adapter command or script may launch a different agent runtime.
assert_not "codex adapter does not launch another agent runtime" \
  grep -R -E '(^|[;&|[:space:]])(claude|agy)([[:space:]]|$)' \
  "$CODEX_REPO/.codex"
assert_not "antigravity adapter does not launch another agent runtime" \
  grep -R -E '(^|[;&|[:space:]])(claude|codex)([[:space:]]|$)' \
  "$AG_REPO/.agents/hooks" "$AG_REPO/.agents/hooks.json"

# AGENTIC_RUNTIME is the non-interactive selector used by native skill runs.
ENV_REPO="$TMP/env runtime repo"
mkrepo "$ENV_REPO"
INSTALL_OUT="$(AGENTIC_RUNTIME=codex "$INSTALL" "$ENV_REPO" 2>&1)"
INSTALL_EXIT=$?
assert_eq "AGENTIC_RUNTIME=codex selects native adapter" 0 "$INSTALL_EXIT"
assert "environment-selected Codex adapter writes .codex/hooks.json" \
  test -f "$ENV_REPO/.codex/hooks.json"

run_install --runtime not-a-runtime "$ENV_REPO"
assert_eq "unsupported runtime exits with usage status" 64 "$INSTALL_EXIT"
assert "unsupported runtime names the invalid value" \
  grep -q 'unsupported runtime' <<<"$INSTALL_OUT"

printf 'pass: %s, fail: %s\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
