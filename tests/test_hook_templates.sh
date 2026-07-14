#!/usr/bin/env bash
# Tests for templates/{stop-gate,post-tool-format,pre-tool-protect}.sh
# (SPEC R10, R11, R12, R13). Runs against throwaway fixture repos in a temp dir.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STOP_GATE="$TOOLKIT_DIR/templates/stop-gate.sh"
POST_FORMAT="$TOOLKIT_DIR/templates/post-tool-format.sh"
PRE_PROTECT="$TOOLKIT_DIR/templates/pre-tool-protect.sh"

pass=0
fail=0

assert() { # assert <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
  fi
}

assert_eq() { # assert_eq <description> <expected> <actual>
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $desc (expected: '$expected', got: '$actual')" >&2
  fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# run_hook <script> <stdin> [cwd]
# Sets RH_EXIT / RH_OUT / RH_ERR. Honors HOOK_PATH to constrain PATH.
run_hook() {
  local script="$1" stdin="$2" cwd="${3:-$TMP}"
  local out_f="$TMP/.rh_out" err_f="$TMP/.rh_err"
  (
    cd "$cwd" || exit 97
    [ -n "${HOOK_PATH:-}" ] && export PATH="$HOOK_PATH"
    printf '%s' "$stdin" | "$script" >"$out_f" 2>"$err_f"
  )
  RH_EXIT=$?
  RH_OUT="$(cat "$out_f")"
  RH_ERR="$(cat "$err_f")"
}

stderr_line_count() { printf '%s' "$RH_ERR" | grep -c .; }

# Fixture repo (name contains a space: paths must be space-safe throughout).
REPO="$TMP/fixture repo"
mkdir -p "$REPO/scripts" "$REPO/sub dir"
git -C "$REPO" init -q

json_stop_false='{"stop_hook_active": false}'
json_stop_true='{"stop_hook_active": true}'

# --- Templates exist and are executable -------------------------------------

assert "stop-gate.sh exists and is executable" test -x "$STOP_GATE"
assert "post-tool-format.sh exists and is executable" test -x "$POST_FORMAT"
assert "pre-tool-protect.sh exists and is executable" test -x "$PRE_PROTECT"

# --- stop-gate: failing check -> exit 2 with check output on stderr (R10) ---

cat > "$REPO/scripts/check.sh" <<'EOF'
#!/usr/bin/env bash
echo "CHECK FAILED marker" >&2
exit 1
EOF
chmod 755 "$REPO/scripts/check.sh"

run_hook "$STOP_GATE" "$json_stop_false" "$REPO"
assert_eq "stop-gate exits 2 on failing check" 2 "$RH_EXIT"
assert "stop-gate relays check failure output on stderr" \
  grep -q "CHECK FAILED marker" <<<"$RH_ERR"

# --- stop-gate: exit 127 from check (missing tool) is a failure, not fail-open

cat > "$REPO/scripts/check.sh" <<'EOF'
#!/usr/bin/env bash
some-tool-that-does-not-exist-anywhere
EOF
chmod 755 "$REPO/scripts/check.sh"

run_hook "$STOP_GATE" "$json_stop_false" "$REPO"
assert_eq "stop-gate exits 2 when check exits 127 (missing tool)" 2 "$RH_EXIT"

# --- stop-gate: green check -> exit 0 ---------------------------------------

cat > "$REPO/scripts/check.sh" <<'EOF'
#!/usr/bin/env bash
touch check-ran.marker
exit 0
EOF
chmod 755 "$REPO/scripts/check.sh"

run_hook "$STOP_GATE" "$json_stop_false" "$REPO"
assert_eq "stop-gate exits 0 on green check" 0 "$RH_EXIT"
assert "green check actually ran" test -f "$REPO/check-ran.marker"
rm -f "$REPO/check-ran.marker"

# --- stop-gate: repo root resolved from a subdirectory cwd ------------------

run_hook "$STOP_GATE" "$json_stop_false" "$REPO/sub dir"
assert_eq "stop-gate exits 0 when run from repo subdir" 0 "$RH_EXIT"
assert "check ran at repo root when hook cwd is a subdir" \
  test -f "$REPO/check-ran.marker"
rm -f "$REPO/check-ran.marker"

# --- stop-gate: cwd field in hook JSON locates the repo ---------------------

run_hook "$STOP_GATE" \
  "{\"stop_hook_active\": false, \"cwd\": \"$REPO\"}" "$TMP"
assert_eq "stop-gate exits 0 using cwd from hook JSON" 0 "$RH_EXIT"
assert "check ran in the repo named by hook JSON cwd" \
  test -f "$REPO/check-ran.marker"
rm -f "$REPO/check-ran.marker"

# --- stop-gate: stop_hook_active true -> exit 0, check NOT run (R10) --------

run_hook "$STOP_GATE" "$json_stop_true" "$REPO"
assert_eq "stop-gate exits 0 when stop_hook_active is true" 0 "$RH_EXIT"
assert "check.sh was not run when stop_hook_active is true" \
  test ! -f "$REPO/check-ran.marker"

# --- stop-gate: check.sh missing -> exit 0 with warning (fail-open boundary)

mv "$REPO/scripts/check.sh" "$REPO/scripts/check.sh.aside"
run_hook "$STOP_GATE" "$json_stop_false" "$REPO"
assert_eq "stop-gate exits 0 when check.sh is missing" 0 "$RH_EXIT"
assert_eq "missing check.sh warns with one stderr line" 1 "$(stderr_line_count)"
mv "$REPO/scripts/check.sh.aside" "$REPO/scripts/check.sh"

# --- stop-gate: check.sh present but unusable -> exit 0 with warning --------
# The stop-gate fails open (one warning, exit 0) when scripts/check.sh exists
# but can't be used. chmod 000 exercises that via the `! -r` guard for an
# ordinary user, but root's DAC bypass makes any regular file readable, so
# chmod 000 can't deny root. For root we substitute a broken symlink: no user
# (root included) can resolve it, so `! -f` fires the SAME fail-open branch.
# Non-root keeps chmod 000 so the `-r` guard itself stays covered.
if [ "$(id -u)" -eq 0 ]; then
  rm -f "$REPO/scripts/check.sh"
  ln -s "$REPO/scripts/no-such-target" "$REPO/scripts/check.sh"
else
  chmod 000 "$REPO/scripts/check.sh"
fi
run_hook "$STOP_GATE" "$json_stop_false" "$REPO"
assert_eq "stop-gate exits 0 when check.sh is unusable" 0 "$RH_EXIT"
assert_eq "unusable check.sh warns with one stderr line" 1 "$(stderr_line_count)"
# Restore a working, readable check.sh for the R13 hardening cases below.
rm -f "$REPO/scripts/check.sh"
cat > "$REPO/scripts/check.sh" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
chmod 755 "$REPO/scripts/check.sh"

# --- stop-gate: R13 hardening ------------------------------------------------

run_hook "$STOP_GATE" "" "$REPO"
assert_eq "stop-gate exits 0 on empty stdin" 0 "$RH_EXIT"
assert_eq "empty stdin warns with one stderr line" 1 "$(stderr_line_count)"

run_hook "$STOP_GATE" "this is not json {" "$REPO"
assert_eq "stop-gate exits 0 on malformed JSON" 0 "$RH_EXIT"
assert_eq "malformed JSON warns with one stderr line" 1 "$(stderr_line_count)"

# --- post-tool-format: R13 hardening -----------------------------------------

run_hook "$POST_FORMAT" "" "$REPO"
assert_eq "post-tool-format exits 0 on empty stdin" 0 "$RH_EXIT"
assert_eq "post-tool-format empty stdin warns (one line)" 1 "$(stderr_line_count)"

run_hook "$POST_FORMAT" "not json at all" "$REPO"
assert_eq "post-tool-format exits 0 on malformed JSON" 0 "$RH_EXIT"
assert_eq "post-tool-format malformed JSON warns (one line)" 1 "$(stderr_line_count)"

run_hook "$POST_FORMAT" '{"tool_name": "Edit"}' "$REPO"
assert_eq "post-tool-format exits 0 when file_path field is missing" 0 "$RH_EXIT"
assert_eq "missing file_path warns (one line)" 1 "$(stderr_line_count)"

run_hook "$POST_FORMAT" \
  "{\"tool_input\": {\"file_path\": \"$REPO/nope/missing.py\"}}" "$REPO"
assert_eq "post-tool-format exits 0 on nonexistent file" 0 "$RH_EXIT"
assert_eq "nonexistent file warns (one line)" 1 "$(stderr_line_count)"

# --- post-tool-format: no formatter on PATH -> exit 0 + warning (R11/R13) ----

echo "x=1" > "$REPO/thing.py"
HOOK_PATH="/usr/bin:/bin" \
  run_hook "$POST_FORMAT" \
  "{\"tool_input\": {\"file_path\": \"$REPO/thing.py\"}}" "$REPO"
assert_eq "post-tool-format exits 0 with no formatter on PATH" 0 "$RH_EXIT"
assert_eq "missing formatter warns (one line)" 1 "$(stderr_line_count)"
assert_eq "file untouched when no formatter available" "x=1" "$(cat "$REPO/thing.py")"
unset HOOK_PATH

# --- post-tool-format: unknown extension -> exit 0 + warning -----------------

echo "hello" > "$REPO/notes.txt"
run_hook "$POST_FORMAT" \
  "{\"tool_input\": {\"file_path\": \"$REPO/notes.txt\"}}" "$REPO"
assert_eq "post-tool-format exits 0 on unmatched stack" 0 "$RH_EXIT"
assert_eq "unmatched stack warns (one line)" 1 "$(stderr_line_count)"

# --- post-tool-format: formatter dispatch via recording stubs ----------------

STUBS="$TMP/stubs"
mkdir -p "$STUBS"
make_stub() { # make_stub <name> [exit_code]
  local rc="${2:-0}"
  cat > "$STUBS/$1" <<EOF
#!/bin/bash
printf '%s\n' "\$*" >> "$STUBS/$1.calls"
exit $rc
EOF
  chmod 755 "$STUBS/$1"
}

# .py -> ruff format <file> when ruff is on PATH
make_stub ruff
HOOK_PATH="$STUBS:/usr/bin:/bin" \
  run_hook "$POST_FORMAT" \
  "{\"tool_input\": {\"file_path\": \"$REPO/thing.py\"}}" "$REPO"
assert_eq "post-tool-format exits 0 formatting .py via ruff" 0 "$RH_EXIT"
assert "ruff invoked as: format <file>" \
  grep -qx "format $REPO/thing.py" "$STUBS/ruff.calls"
unset HOOK_PATH

# .go -> gofmt -w <file>
make_stub gofmt
echo "package main" > "$REPO/main.go"
HOOK_PATH="$STUBS:/usr/bin:/bin" \
  run_hook "$POST_FORMAT" \
  "{\"tool_input\": {\"file_path\": \"$REPO/main.go\"}}" "$REPO"
assert_eq "post-tool-format exits 0 formatting .go via gofmt" 0 "$RH_EXIT"
assert "gofmt invoked as: -w <file>" \
  grep -qx "\-w $REPO/main.go" "$STUBS/gofmt.calls"
unset HOOK_PATH

# .ts -> repo-local node_modules/.bin/prettier preferred over npx
mkdir -p "$REPO/node_modules/.bin"
cat > "$REPO/node_modules/.bin/prettier" <<EOF
#!/bin/bash
printf '%s\n' "\$*" >> "$STUBS/local-prettier.calls"
exit 0
EOF
chmod 755 "$REPO/node_modules/.bin/prettier"
make_stub npx
echo "const x=1" > "$REPO/app.ts"
HOOK_PATH="$STUBS:/usr/bin:/bin" \
  run_hook "$POST_FORMAT" \
  "{\"tool_input\": {\"file_path\": \"$REPO/app.ts\"}}" "$REPO"
assert_eq "post-tool-format exits 0 formatting .ts via local prettier" 0 "$RH_EXIT"
assert "repo-local prettier invoked with --write <file>" \
  grep -qx "\-\-write $REPO/app.ts" "$STUBS/local-prettier.calls"
assert "npx not used when repo-local prettier exists" \
  test ! -f "$STUBS/npx.calls"
unset HOOK_PATH

# .ts without repo-local prettier -> npx --no-install prettier (never bare npx)
rm -rf "$REPO/node_modules"
HOOK_PATH="$STUBS:/usr/bin:/bin" \
  run_hook "$POST_FORMAT" \
  "{\"tool_input\": {\"file_path\": \"$REPO/app.ts\"}}" "$REPO"
assert_eq "post-tool-format exits 0 via npx fallback" 0 "$RH_EXIT"
assert "npx fallback passes --no-install" \
  grep -qx "\-\-no-install prettier --write $REPO/app.ts" "$STUBS/npx.calls"
unset HOOK_PATH

# formatter failure -> exit 0 + warning (fail-open)
make_stub ruff 1
HOOK_PATH="$STUBS:/usr/bin:/bin" \
  run_hook "$POST_FORMAT" \
  "{\"tool_input\": {\"file_path\": \"$REPO/thing.py\"}}" "$REPO"
assert_eq "post-tool-format exits 0 when formatter fails" 0 "$RH_EXIT"
assert_eq "formatter failure warns (one line)" 1 "$(stderr_line_count)"
unset HOOK_PATH

# --- pre-tool-protect: protected paths denied with exit 2 (R12) --------------

protect_denies() { # protect_denies <description> <path>
  local desc="$1" path="$2"
  run_hook "$PRE_PROTECT" \
    "{\"tool_name\": \"Edit\", \"tool_input\": {\"file_path\": \"$path\"}}" "$REPO"
  assert_eq "$desc: exit 2" 2 "$RH_EXIT"
  assert_eq "$desc: one-line stderr reason" 1 "$(stderr_line_count)"
  assert "$desc: reason names the path" grep -qF "$path" <<<"$RH_ERR"
}

protect_allows() { # protect_allows <description> <path>
  local desc="$1" path="$2"
  run_hook "$PRE_PROTECT" \
    "{\"tool_name\": \"Write\", \"tool_input\": {\"file_path\": \"$path\"}}" "$REPO"
  assert_eq "$desc: exit 0" 0 "$RH_EXIT"
}

protect_denies "deny .env" "$REPO/.env"
protect_denies "deny .env.local" "$REPO/.env.local"
protect_denies "deny package-lock.json" "$REPO/package-lock.json"
protect_denies "deny pnpm-lock.yaml" "$REPO/pnpm-lock.yaml"
protect_denies "deny *.lock (uv.lock)" "$REPO/uv.lock"
protect_denies "deny absolute path under .git/" "$REPO/.git/config"
protect_denies "deny relative path under .git/" ".git/hooks/pre-commit"

protect_allows "allow ordinary source file" "$REPO/src/app.ts"
protect_allows "allow .github path (not .git/)" "$REPO/.github/workflows/ci.yml"
protect_allows "allow environment.ts (not .env*)" "$REPO/src/environment.ts"
protect_allows "allow lockfile-ish name (flock.py)" "$REPO/flock.py"

# --- pre-tool-protect: R13 hardening -----------------------------------------

run_hook "$PRE_PROTECT" "" "$REPO"
assert_eq "pre-tool-protect exits 0 on empty stdin" 0 "$RH_EXIT"
assert_eq "pre-tool-protect empty stdin warns (one line)" 1 "$(stderr_line_count)"

run_hook "$PRE_PROTECT" "{{{ nope" "$REPO"
assert_eq "pre-tool-protect exits 0 on malformed JSON" 0 "$RH_EXIT"
assert_eq "pre-tool-protect malformed JSON warns (one line)" 1 "$(stderr_line_count)"

run_hook "$PRE_PROTECT" '{"tool_name": "Edit", "tool_input": {}}' "$REPO"
assert_eq "pre-tool-protect exits 0 when file_path missing" 0 "$RH_EXIT"
assert_eq "pre-tool-protect missing file_path warns (one line)" 1 "$(stderr_line_count)"

# --- stop-gate: docs-only diff scoping (R4) ----------------------------------
# When every file changed since the last commit matches CLAUDE.md's
# paths-ignore globs (**.md, docs/**, specs/**, .claude/**), the full check is
# skipped; any non-docs change still runs it in full (never a blanket skip).

DOCS_REPO="$TMP/docs only repo"
mkdir -p "$DOCS_REPO/scripts" "$DOCS_REPO/docs"
git -C "$DOCS_REPO" init -q
git -C "$DOCS_REPO" config user.email test@example.com
git -C "$DOCS_REPO" config user.name test
# A check.sh that records the fact it ran, so we can assert run-vs-skipped.
cat > "$DOCS_REPO/scripts/check.sh" <<'EOF'
#!/usr/bin/env bash
touch check-ran.marker
exit 0
EOF
chmod 755 "$DOCS_REPO/scripts/check.sh"
echo "# readme" > "$DOCS_REPO/README.md"
git -C "$DOCS_REPO" add -A
git -C "$DOCS_REPO" commit -qm baseline

# clean tree (no changes since HEAD) is NOT docs-only -> full check runs
git -C "$DOCS_REPO" clean -fdq
rm -f "$DOCS_REPO/check-ran.marker"
run_hook "$STOP_GATE" "$json_stop_false" "$DOCS_REPO"
assert_eq "stop-gate exits 0 on a clean tree" 0 "$RH_EXIT"
assert "check.sh runs on a clean tree (not skipped as docs-only)" \
  test -f "$DOCS_REPO/check-ran.marker"

# docs-only change (a new .md file) -> check skipped, exit 0, no marker
git -C "$DOCS_REPO" clean -fdq
rm -f "$DOCS_REPO/check-ran.marker"
echo "note" >> "$DOCS_REPO/HUMAN.md"
run_hook "$STOP_GATE" "$json_stop_false" "$DOCS_REPO"
assert_eq "stop-gate exits 0 on docs-only (.md) diff" 0 "$RH_EXIT"
assert "check.sh NOT run for docs-only (.md) diff" \
  test ! -f "$DOCS_REPO/check-ran.marker"

# change confined to the docs/ subtree also counts as docs-only
git -C "$DOCS_REPO" clean -fdq
mkdir -p "$DOCS_REPO/docs"
echo "doc" > "$DOCS_REPO/docs/guide.txt"
run_hook "$STOP_GATE" "$json_stop_false" "$DOCS_REPO"
assert_eq "stop-gate exits 0 on docs/ subtree-only diff" 0 "$RH_EXIT"
assert "check.sh NOT run for docs/ subtree-only diff" \
  test ! -f "$DOCS_REPO/check-ran.marker"

# a non-docs change alongside a docs change -> full check still runs
git -C "$DOCS_REPO" clean -fdq
echo "note" >> "$DOCS_REPO/HUMAN.md"
echo "x = 1" > "$DOCS_REPO/app.py"
run_hook "$STOP_GATE" "$json_stop_false" "$DOCS_REPO"
assert_eq "stop-gate exits 0 when mixed diff's check passes" 0 "$RH_EXIT"
assert "check.sh DID run when a non-docs file changed" \
  test -f "$DOCS_REPO/check-ran.marker"
git -C "$DOCS_REPO" clean -fdq

# a .claude/** change is docs-only in a repo with NO .claude-plugin/ marker
# (a typical consumer repo, where .claude/ is incidental config) -> skipped
git -C "$DOCS_REPO" clean -fdq
mkdir -p "$DOCS_REPO/.claude/skills/foo"
echo "skill" > "$DOCS_REPO/.claude/skills/foo/SKILL.md"
run_hook "$STOP_GATE" "$json_stop_false" "$DOCS_REPO"
assert_eq "stop-gate exits 0 on .claude/** diff (no plugin marker)" 0 "$RH_EXIT"
assert "check.sh NOT run for .claude/** diff without a .claude-plugin/ marker" \
  test ! -f "$DOCS_REPO/check-ran.marker"
git -C "$DOCS_REPO" clean -fdq
rm -rf "$DOCS_REPO/.claude"

# a .claude/** change is NOT docs-only in a repo WITH a .claude-plugin/
# marker (this toolkit's own shape: .claude/ IS the shipped product) -> runs
PLUGIN_REPO="$TMP/plugin repo"
mkdir -p "$PLUGIN_REPO/scripts" "$PLUGIN_REPO/.claude-plugin" "$PLUGIN_REPO/.claude/skills/foo"
git -C "$PLUGIN_REPO" init -q
git -C "$PLUGIN_REPO" config user.email test@example.com
git -C "$PLUGIN_REPO" config user.name test
cat > "$PLUGIN_REPO/scripts/check.sh" <<'EOF'
#!/usr/bin/env bash
touch check-ran.marker
exit 0
EOF
chmod 755 "$PLUGIN_REPO/scripts/check.sh"
echo '{"name": "agentic"}' > "$PLUGIN_REPO/.claude-plugin/plugin.json"
echo "skill" > "$PLUGIN_REPO/.claude/skills/foo/SKILL.md"
git -C "$PLUGIN_REPO" add -A
git -C "$PLUGIN_REPO" commit -qm baseline
echo "skill v2" > "$PLUGIN_REPO/.claude/skills/foo/SKILL.md"
run_hook "$STOP_GATE" "$json_stop_false" "$PLUGIN_REPO"
assert_eq "stop-gate exits 0 on .claude/** diff (plugin marker present)" 0 "$RH_EXIT"
assert "check.sh DID run for .claude/** diff with a .claude-plugin/ marker" \
  test -f "$PLUGIN_REPO/check-ran.marker"

# a pure-docs change (.md) in that same plugin repo is still docs-only
git -C "$PLUGIN_REPO" checkout -q -- .
git -C "$PLUGIN_REPO" clean -fdq
echo "note" >> "$PLUGIN_REPO/HUMAN.md"
run_hook "$STOP_GATE" "$json_stop_false" "$PLUGIN_REPO"
assert_eq "stop-gate exits 0 on .md diff in a plugin repo" 0 "$RH_EXIT"
assert "check.sh NOT run for .md diff in a plugin repo" \
  test ! -f "$PLUGIN_REPO/check-ran.marker"
git -C "$PLUGIN_REPO" clean -fdq

# --- Summary -----------------------------------------------------------------

echo "pass: $pass, fail: $fail"
[ "$fail" -eq 0 ]
