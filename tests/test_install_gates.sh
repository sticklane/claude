#!/usr/bin/env bash
# Tests for bin/install-gates (SPEC R1–R7b, R9 — detection, tiers,
# generation, settings merge, existing-hook handling, guards, idempotence).
# Runs against throwaway fixture repos in a temp dir. Never touches a real
# repo.
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
    echo "FAIL: $desc" >&2
  fi
}

assert_not() { # assert_not <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    fail=$((fail + 1))
    echo "FAIL: $desc" >&2
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
    echo "FAIL: $desc (expected: '$expected', got: '$actual')" >&2
  fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkrepo() { # mkrepo <dir>
  mkdir -p "$1"
  git -C "$1" init -q
}

run_install() { # run_install [flags...] <repo> — sets RI_EXIT / RI_OUT
  RI_OUT="$("$INSTALL" "$@" 2>&1)"
  RI_EXIT=$?
}

out_has() { printf '%s' "$RI_OUT" | grep -q "$1"; }

# stage_line <file> <pattern> — line number of first match, or empty
stage_line() { grep -n "$2" "$1" | head -1 | cut -d: -f1; }

# ---------------------------------------------------------------------------
# R1: installer exists and is executable
# ---------------------------------------------------------------------------

assert "bin/install-gates exists and is executable" test -x "$INSTALL"

# ---------------------------------------------------------------------------
# Python fixture (full tier) — path contains a space to test space-safety.
# pyproject with [tool.ruff] (formatter config present) + tests/.
# ---------------------------------------------------------------------------

PY="$TMP/py fix"
mkrepo "$PY"
cat > "$PY/pyproject.toml" <<'EOF'
[project]
name = "pyfix"
version = "0.0.1"

[tool.ruff]
line-length = 100
EOF
mkdir -p "$PY/tests"
printf 'def test_ok():\n    assert True\n' > "$PY/tests/test_sample.py"
printf '# Py fixture\n' > "$PY/CLAUDE.md"

run_install "$PY"
assert_eq "python fixture: installer exits 0" 0 "$RI_EXIT"
assert "python fixture: prints stack python" out_has "stack: python"
assert "python fixture: prints tier full" out_has "tier: full"

PY_CHECK="$PY/scripts/check.sh"
PY_HOOK="$PY/.git/hooks/pre-commit"
assert "python fixture: scripts/check.sh exists" test -f "$PY_CHECK"
assert_eq "python fixture: check.sh mode 755" 755 "$(stat -f '%Lp' "$PY_CHECK")"
assert "python fixture: check.sh uses ruff (acceptance grep)" \
  grep -q 'uvx ruff\|^ruff\| ruff ' "$PY_CHECK"
assert_not "python fixture: no bare npx in check.sh or pre-commit" \
  grep -E 'npx [a-z]' "$PY_CHECK" "$PY_HOOK"
assert_not "python fixture: no typecheck stage (mypy not configured)" \
  grep -q mypy "$PY_CHECK"

fmt_ln="$(stage_line "$PY_CHECK" '^run_stage "format-check"')"
lint_ln="$(stage_line "$PY_CHECK" '^run_stage "lint"')"
test_ln="$(stage_line "$PY_CHECK" '^run_stage "tests"')"
assert "python fixture: format-check stage present" test -n "$fmt_ln"
assert "python fixture: lint stage present" test -n "$lint_ln"
assert "python fixture: tests stage present" test -n "$test_ln"
assert "python fixture: stage order format < lint < tests" \
  test -n "$fmt_ln" -a -n "$lint_ln" -a -n "$test_ln" -a \
       "$fmt_ln" -lt "$lint_ln" -a "$lint_ln" -lt "$test_ln"

assert "python fixture: pre-commit exists and is executable" test -x "$PY_HOOK"
assert "python fixture: pre-commit reads staged files (ACMR)" \
  grep -q 'git diff --cached --name-only --diff-filter=ACMR' "$PY_HOOK"
assert "python fixture: pre-commit lints with ruff" grep -q 'ruff check' "$PY_HOOK"
assert "python fixture: pre-commit format-checks with ruff" \
  grep -q 'ruff format --check' "$PY_HOOK"

for h in stop-gate post-tool-format pre-tool-protect; do
  assert "python fixture: .claude/hooks/$h.sh matches template" \
    cmp -s "$TOOLKIT_DIR/templates/$h.sh" "$PY/.claude/hooks/$h.sh"
done

PY_SETTINGS="$PY/.claude/settings.json"
assert "python fixture: settings.json is valid JSON" jq -e . "$PY_SETTINGS"
assert "python fixture: settings wires Stop" jq -e '.hooks.Stop' "$PY_SETTINGS"
assert "python fixture: settings wires PostToolUse" jq -e '.hooks.PostToolUse' "$PY_SETTINGS"
assert "python fixture: settings wires PreToolUse" jq -e '.hooks.PreToolUse' "$PY_SETTINGS"

assert "python fixture: CLAUDE.md keeps pre-existing content" \
  grep -q '^# Py fixture' "$PY/CLAUDE.md"
assert "python fixture: CLAUDE.md stamp names scripts/check.sh" \
  grep -q 'scripts/check.sh' "$PY/CLAUDE.md"
assert "python fixture: CLAUDE.md stamp is marker-delimited" \
  grep -q 'install-gates:checks' "$PY/CLAUDE.md"

# Idempotence (task-02 slice of R3): second run leaves every managed file
# byte-identical (content hash), including CLAUDE.md.
managed_hash() { # managed_hash <repo>
  (cd "$1" && shasum -a 256 \
    .claude/settings.json .claude/hooks/*.sh \
    scripts/check.sh .git/hooks/pre-commit CLAUDE.md 2>/dev/null)
}

# find_hash <repo> — the acceptance-criterion hash over every managed file
find_hash() {
  find "$1" \( -path '*/.claude/*' -o -name pre-commit \
    -o -path '*/scripts/check.sh' -o -name CLAUDE.md \) \
    -type f -exec shasum -a 256 {} + | sort
}
h1="$(managed_hash "$PY")"
run_install "$PY"
assert_eq "python fixture: second run exits 0" 0 "$RI_EXIT"
h2="$(managed_hash "$PY")"
assert_eq "python fixture: managed files byte-identical after re-run" "$h1" "$h2"

# ---------------------------------------------------------------------------
# Dry run (R1): prints tier + planned files, writes nothing.
# ---------------------------------------------------------------------------

PYDRY="$TMP/pydry"
mkrepo "$PYDRY"
printf 'requests\n' > "$PYDRY/requirements.txt"
before="$(find "$PYDRY" | sort)"
run_install --dry-run "$PYDRY"
after="$(find "$PYDRY" | sort)"
assert_eq "dry-run: exits 0" 0 "$RI_EXIT"
assert "dry-run: prints tier" out_has "tier: "
assert "dry-run: prints planned check.sh" out_has "scripts/check.sh"
assert "dry-run: prints planned settings.json" out_has ".claude/settings.json"
assert "dry-run: prints existing-hook handling" out_has "existing pre-commit:"
assert_eq "dry-run: writes nothing" "$before" "$after"

# ---------------------------------------------------------------------------
# Python without formatter config or tests (requirements.txt only):
# no-test-stage tier, lint stage but NO format stage.
# ---------------------------------------------------------------------------

PYNF="$TMP/pynofmt"
mkrepo "$PYNF"
printf 'requests\n' > "$PYNF/requirements.txt"
printf 'x = 1\n' > "$PYNF/app.py"
run_install "$PYNF"
assert_eq "py-nofmt: exits 0" 0 "$RI_EXIT"
assert "py-nofmt: tier no-test-stage" out_has "tier: no-test-stage"
assert "py-nofmt: check.sh lints with ruff" grep -q 'ruff check' "$PYNF/scripts/check.sh"
assert_not "py-nofmt: no format stage in check.sh" \
  grep -q 'format --check' "$PYNF/scripts/check.sh"
assert_not "py-nofmt: no tests stage in check.sh" \
  grep -q 'run_stage "tests"' "$PYNF/scripts/check.sh"
assert_not "py-nofmt: no format stage in pre-commit" \
  grep -q 'format --check' "$PYNF/.git/hooks/pre-commit"

# ---------------------------------------------------------------------------
# Node with a `check` script that runs tests: check.sh delegates, tier full.
# ---------------------------------------------------------------------------

NC="$TMP/nodecheck"
mkrepo "$NC"
cat > "$NC/package.json" <<'EOF'
{
  "name": "nodecheck",
  "scripts": {
    "check": "npm run lint && npm run test",
    "lint": "eslint .",
    "test": "node test.js"
  }
}
EOF
run_install "$NC"
assert_eq "node-check: exits 0" 0 "$RI_EXIT"
assert "node-check: stack node" out_has "stack: node"
assert "node-check: tier full (check script runs tests)" out_has "tier: full"
NC_CHECK="$NC/scripts/check.sh"
assert "node-check: check.sh delegates to npm run check" \
  grep -q 'npm run check' "$NC_CHECK"
assert_eq "node-check: exactly one stage (delegation, nothing synthesized)" \
  1 "$(grep -c '^run_stage ' "$NC_CHECK")"
assert_not "node-check: no synthesized eslint stage" grep -q 'eslint' "$NC_CHECK"
assert_not "node-check: no synthesized prettier stage" grep -q 'prettier' "$NC_CHECK"

# ---------------------------------------------------------------------------
# Node with lint script but no formatter config, no tests:
# no-test-stage; no format stage anywhere; no per-file eslint (not installed).
# ---------------------------------------------------------------------------

NNF="$TMP/nodenofmt"
mkrepo "$NNF"
cat > "$NNF/package.json" <<'EOF'
{
  "name": "nodenofmt",
  "scripts": {
    "lint": "eslint ."
  }
}
EOF
run_install "$NNF"
assert_eq "node-nofmt: exits 0" 0 "$RI_EXIT"
assert "node-nofmt: tier no-test-stage" out_has "tier: no-test-stage"
assert "node-nofmt: lint stage uses repo lint script" \
  grep -q 'npm run lint' "$NNF/scripts/check.sh"
assert_not "node-nofmt: no format stage in check.sh" \
  grep -qi 'prettier\|format' "$NNF/scripts/check.sh"
assert_not "node-nofmt: no format stage in pre-commit" \
  grep -q 'prettier' "$NNF/.git/hooks/pre-commit"
assert_not "node-nofmt: no per-file eslint in pre-commit (not resolvable)" \
  grep -q 'eslint' "$NNF/.git/hooks/pre-commit"
assert_not "node-nofmt: no bare npx" \
  grep -E 'npx [a-z]' "$NNF/scripts/check.sh" "$NNF/.git/hooks/pre-commit"

# ---------------------------------------------------------------------------
# Node with prettier config and repo-local prettier + eslint stubs:
# format stage present via node_modules/.bin, per-file eslint in pre-commit.
# ---------------------------------------------------------------------------

NF="$TMP/nodefmt"
mkrepo "$NF"
cat > "$NF/package.json" <<'EOF'
{
  "name": "nodefmt",
  "scripts": {
    "lint": "eslint ."
  }
}
EOF
printf '{}\n' > "$NF/.prettierrc"
mkdir -p "$NF/node_modules/.bin"
printf '#!/bin/sh\nexit 0\n' > "$NF/node_modules/.bin/prettier"
printf '#!/bin/sh\nexit 0\n' > "$NF/node_modules/.bin/eslint"
chmod 755 "$NF/node_modules/.bin/prettier" "$NF/node_modules/.bin/eslint"
run_install "$NF"
assert_eq "node-fmt: exits 0" 0 "$RI_EXIT"
assert "node-fmt: format stage via repo-local prettier" \
  grep -q 'node_modules/.bin/prettier --check' "$NF/scripts/check.sh"
assert "node-fmt: pre-commit format-checks staged files with prettier" \
  grep -q 'node_modules/.bin/prettier --check' "$NF/.git/hooks/pre-commit"
assert "node-fmt: pre-commit lints staged files with eslint binary" \
  grep -q 'node_modules/.bin/eslint' "$NF/.git/hooks/pre-commit"
assert_not "node-fmt: no bare npx" \
  grep -E 'npx [a-z]' "$NF/scripts/check.sh" "$NF/.git/hooks/pre-commit"

# ---------------------------------------------------------------------------
# Node whose `lint` script is actually a typechecker (tsc --noEmit):
# classified as typecheck stage, never lint, never per-file.
# ---------------------------------------------------------------------------

NT="$TMP/nodetsc"
mkrepo "$NT"
cat > "$NT/package.json" <<'EOF'
{
  "name": "nodetsc",
  "scripts": {
    "lint": "tsc --noEmit"
  }
}
EOF
printf '{}\n' > "$NT/tsconfig.json"
run_install "$NT"
assert_eq "node-tsc: exits 0" 0 "$RI_EXIT"
assert_not "node-tsc: no lint stage in check.sh" \
  grep -q '^run_stage "lint"' "$NT/scripts/check.sh"
assert "node-tsc: lint script classified as typecheck stage" \
  grep -q '^run_stage "typecheck" npm run lint' "$NT/scripts/check.sh"
NT_HOOK="$NT/.git/hooks/pre-commit"
assert "node-tsc: pre-commit records typecheck measurement decision" \
  grep -q '# install-gates-typecheck: excluded' "$NT_HOOK"
assert_not "node-tsc: no typecheck invocation in pre-commit (excluded)" \
  grep -q 'fail "typecheck"' "$NT_HOOK"
assert_not "node-tsc: no per-file tsc in pre-commit" \
  grep -q 'staged\[@\].*tsc\|tsc.*staged\[@\]' "$NT_HOOK"

# R3: the typecheck-timing marker is reused on re-runs, never re-measured
# implicitly; only --remeasure re-measures.
sed -i '' 's/^# install-gates-typecheck: excluded$/# install-gates-typecheck: included/' "$NT_HOOK"
run_install "$NT"
assert_eq "R3 marker: re-run exits 0" 0 "$RI_EXIT"
assert "R3 marker: decision reused absent --remeasure" \
  grep -q '^# install-gates-typecheck: included' "$NT_HOOK"
run_install --remeasure "$NT"
assert_eq "R3 marker: --remeasure exits 0" 0 "$RI_EXIT"
assert "R3 marker: --remeasure re-measures the decision" \
  grep -q '^# install-gates-typecheck: excluded' "$NT_HOOK"

# ---------------------------------------------------------------------------
# Go fixture: go.mod + *_test.go → full tier; gofmt format stage (go.mod is
# the formatter config), go vet lint (check.sh only), go test tests;
# pre-commit runs gofmt on staged files, never go vet.
# ---------------------------------------------------------------------------

GO="$TMP/gofix"
mkrepo "$GO"
printf 'module example.com/gofix\n\ngo 1.22\n' > "$GO/go.mod"
printf 'package main\n\nfunc main() {}\n' > "$GO/main.go"
printf 'package main\n\nimport "testing"\n\nfunc TestOK(t *testing.T) {}\n' > "$GO/main_test.go"
run_install "$GO"
assert_eq "go: exits 0" 0 "$RI_EXIT"
assert "go: stack go" out_has "stack: go"
assert "go: tier full" out_has "tier: full"
GO_CHECK="$GO/scripts/check.sh"
assert "go: format stage uses gofmt" grep -q 'gofmt -l' "$GO_CHECK"
assert "go: lint stage is go vet" grep -q 'go vet ./...' "$GO_CHECK"
assert "go: tests stage is go test" grep -q 'go test ./...' "$GO_CHECK"
assert "go: pre-commit format-checks staged files with gofmt" \
  grep -q 'gofmt -l' "$GO/.git/hooks/pre-commit"
assert_not "go: no go vet in pre-commit (package-level, check.sh only)" \
  grep -q 'go vet' "$GO/.git/hooks/pre-commit"

# ---------------------------------------------------------------------------
# Generic fixture: no stack → edit-time hooks only. No check.sh, no
# pre-commit, no Stop wiring, no CLAUDE.md stamp.
# ---------------------------------------------------------------------------

GEN="$TMP/genfix"
mkrepo "$GEN"
printf 'hello\n' > "$GEN/README.md"
run_install "$GEN"
assert_eq "generic: exits 0" 0 "$RI_EXIT"
assert "generic: tier generic" out_has "tier: generic"
assert "generic: no scripts/check.sh and no pre-commit" \
  test ! -e "$GEN/scripts/check.sh" -a ! -e "$GEN/.git/hooks/pre-commit"
GEN_SETTINGS="$GEN/.claude/settings.json"
assert "generic: settings wires PostToolUse" jq -e '.hooks.PostToolUse' "$GEN_SETTINGS"
assert "generic: settings wires PreToolUse" jq -e '.hooks.PreToolUse' "$GEN_SETTINGS"
assert_eq "generic: settings has no Stop hook" \
  "null" "$(jq '.hooks.Stop' "$GEN_SETTINGS")"
assert "generic: no stop-gate hook installed" \
  test ! -e "$GEN/.claude/hooks/stop-gate.sh"
assert "generic: edit-time hooks installed" \
  test -f "$GEN/.claude/hooks/post-tool-format.sh" -a -f "$GEN/.claude/hooks/pre-tool-protect.sh"
assert "generic: no CLAUDE.md stamp" test ! -e "$GEN/CLAUDE.md"

# ---------------------------------------------------------------------------
# R7a: a foreign pre-existing pre-commit hook is archived to
# pre-commit.pre-gates and replaced by the gate hook; pre-commit.old,
# pre-commit.backup, and non-pre-commit hooks are never touched; legacy
# AI-review chains are dropped (not carried into the gate hook).
# ---------------------------------------------------------------------------

FOREIGN="$TMP/foreignhook"
mkrepo "$FOREIGN"
printf 'requests\n' > "$FOREIGN/requirements.txt"
printf '#!/bin/sh\necho legacy\nclaude -p "review the diff"\n' > "$FOREIGN/.git/hooks/pre-commit"
printf '#!/bin/sh\necho old-link\n' > "$FOREIGN/.git/hooks/pre-commit.old"
printf '#!/bin/sh\necho backup\n' > "$FOREIGN/.git/hooks/pre-commit.backup"
printf '#!/bin/sh\necho post-merge\n' > "$FOREIGN/.git/hooks/post-merge"
chmod 755 "$FOREIGN/.git/hooks/pre-commit"

run_install --dry-run "$FOREIGN"
assert_eq "R7a dry-run: exits 0" 0 "$RI_EXIT"
assert "R7a dry-run: reports foreign hook" out_has "existing pre-commit: foreign"
assert "R7a dry-run: plans archive to pre-commit.pre-gates" \
  out_has "archive.*pre-commit.pre-gates"
assert "R7a dry-run: writes nothing" \
  test ! -e "$FOREIGN/.git/hooks/pre-commit.pre-gates" -a ! -e "$FOREIGN/scripts"

untouched_before="$(cd "$FOREIGN/.git/hooks" && shasum -a 256 pre-commit.old pre-commit.backup post-merge)"
run_install "$FOREIGN"
assert_eq "R7a: real run exits 0" 0 "$RI_EXIT"
assert "R7a: legacy hook archived to pre-commit.pre-gates" \
  grep -q 'echo legacy' "$FOREIGN/.git/hooks/pre-commit.pre-gates"
assert "R7a: gate hook installed over pre-commit" \
  grep -q 'Generated by install-gates' "$FOREIGN/.git/hooks/pre-commit"
assert_not "R7a: AI-review chain not carried into gate hook" \
  grep -q 'claude' "$FOREIGN/.git/hooks/pre-commit"
untouched_after="$(cd "$FOREIGN/.git/hooks" && shasum -a 256 pre-commit.old pre-commit.backup post-merge)"
assert_eq "R7a: .old/.backup/non-pre-commit hooks untouched" \
  "$untouched_before" "$untouched_after"

fh1="$(find_hash "$FOREIGN")"
run_install "$FOREIGN"
assert_eq "R7a: second run exits 0" 0 "$RI_EXIT"
fh2="$(find_hash "$FOREIGN")"
assert_eq "R7a/R3: double-run managed-file hashes identical" "$fh1" "$fh2"

# ---------------------------------------------------------------------------
# R7a abort path: pre-commit.pre-gates already occupied — abort for the repo,
# name the occupied file, mutate nothing.
# ---------------------------------------------------------------------------

OCC="$TMP/occupied"
mkrepo "$OCC"
printf 'requests\n' > "$OCC/requirements.txt"
printf '#!/bin/sh\necho legacy\n' > "$OCC/.git/hooks/pre-commit"
printf '#!/bin/sh\necho already-archived\n' > "$OCC/.git/hooks/pre-commit.pre-gates"
chmod 755 "$OCC/.git/hooks/pre-commit"

run_install --dry-run "$OCC"
assert_eq "R7a occupied dry-run: exits 0" 0 "$RI_EXIT"
assert "R7a occupied dry-run: plans abort" out_has "abort"
assert "R7a occupied dry-run: names pre-commit.pre-gates" out_has "pre-commit.pre-gates"
assert "R7a occupied dry-run: writes nothing" \
  test ! -d "$OCC/.claude" -a ! -e "$OCC/scripts"

run_install "$OCC"
assert_not "R7a occupied: real run exits non-zero" test "$RI_EXIT" -eq 0
assert "R7a occupied: error names pre-commit.pre-gates" out_has "pre-commit.pre-gates"
assert "R7a occupied: existing hook unmodified" \
  grep -q 'echo legacy' "$OCC/.git/hooks/pre-commit"
assert "R7a occupied: archive unmodified" \
  grep -q 'echo already-archived' "$OCC/.git/hooks/pre-commit.pre-gates"
assert "R7a occupied: nothing written" test ! -d "$OCC/.claude" -a ! -e "$OCC/scripts"

# ---------------------------------------------------------------------------
# R7c: generic-tier repos get no pre-commit install, but an existing hook is
# still archived and removed (review chains retired everywhere).
# ---------------------------------------------------------------------------

GH="$TMP/generichook"
mkrepo "$GH"
printf 'notes\n' > "$GH/README.md"
printf '#!/bin/sh\nclaude -p review\n' > "$GH/.git/hooks/pre-commit"
chmod 755 "$GH/.git/hooks/pre-commit"
run_install "$GH"
assert_eq "R7c: exits 0" 0 "$RI_EXIT"
assert "R7c: tier generic" out_has "tier: generic"
assert "R7c: existing hook archived" \
  grep -q 'claude -p review' "$GH/.git/hooks/pre-commit.pre-gates"
assert "R7c: no pre-commit installed (hook removed)" \
  test ! -e "$GH/.git/hooks/pre-commit"
assert "R7c: edit-time hooks still installed" \
  test -f "$GH/.claude/hooks/pre-tool-protect.sh"
assert "R7c: no check.sh" test ! -e "$GH/scripts/check.sh"

# ---------------------------------------------------------------------------
# R4: existing .claude/settings.json is merged opaquely — gate entries are
# appended; non-standard shapes, unknown top-level keys, and credentials are
# preserved; re-runs never duplicate entries.
# ---------------------------------------------------------------------------

MG="$TMP/mergefix"
mkrepo "$MG"
cat > "$MG/pyproject.toml" <<'EOF'
[project]
name = "mergefix"
version = "0.0.1"
EOF
mkdir -p "$MG/tests"
printf 'def test_ok():\n    assert True\n' > "$MG/tests/test_sample.py"
mkdir -p "$MG/.claude"
cat > "$MG/.claude/settings.json" <<'EOF'
{
  "mcpServers": {
    "corp": {
      "command": "corp-mcp",
      "env": { "CORP_TOKEN": "dummy-token-abc123" }
    }
  },
  "permissions": { "allow": ["Bash(ls:*)"] },
  "hooks": {
    "Stop": [
      { "type": "command", "command": "echo legacy-stop" }
    ],
    "PreToolUse": [
      {
        "matcher": { "tool_name": "Bash" },
        "hooks": [{ "type": "command", "command": "echo legacy-pre" }]
      }
    ]
  }
}
EOF
run_install "$MG"
MG_S="$MG/.claude/settings.json"
assert_eq "R4: exits 0" 0 "$RI_EXIT"
assert "R4: valid JSON after merge" jq -e . "$MG_S"
assert "R4: mcpServers dummy token preserved" \
  jq -e '.mcpServers.corp.env.CORP_TOKEN == "dummy-token-abc123"' "$MG_S"
assert "R4: unknown top-level key preserved" \
  jq -e '.permissions.allow == ["Bash(ls:*)"]' "$MG_S"
assert "R4: bare event entry preserved first in Stop" \
  jq -e '.hooks.Stop[0] == {"type":"command","command":"echo legacy-stop"}' "$MG_S"
assert "R4: object-valued matcher entry preserved" \
  jq -e '.hooks.PreToolUse[0].matcher == {"tool_name":"Bash"}' "$MG_S"
assert "R4: gate Stop hook appended" \
  jq -e '.hooks.Stop | tostring | contains("stop-gate.sh")' "$MG_S"
assert "R4: gate PreToolUse hook appended" \
  jq -e '.hooks.PreToolUse | tostring | contains("pre-tool-protect.sh")' "$MG_S"
assert "R4: gate PostToolUse hook added" \
  jq -e '.hooks.PostToolUse | tostring | contains("post-tool-format.sh")' "$MG_S"
cp "$MG_S" "$TMP/settings.run1.json"
mgh1="$(find_hash "$MG")"
run_install "$MG"
assert_eq "R4: second run exits 0" 0 "$RI_EXIT"
assert "R4: second run adds nothing (settings byte-identical)" \
  cmp -s "$TMP/settings.run1.json" "$MG_S"
assert_eq "R4: exactly one gate Stop entry after re-run" \
  1 "$(jq '[.hooks.Stop[] | tostring | select(contains("stop-gate.sh"))] | length' "$MG_S")"
mgh2="$(find_hash "$MG")"
assert_eq "R4/R3: double-run managed-file hashes identical" "$mgh1" "$mgh2"

# ---------------------------------------------------------------------------
# R7b: self-installing hook sources — a prepare/setup:hooks script plus
# scripts/git-hooks/pre-commit triggers replacement of the source hook with
# the gate hook; other files in the source dir are left alone.
# ---------------------------------------------------------------------------

SH="$TMP/selfhook"
mkrepo "$SH"
cat > "$SH/package.json" <<'EOF'
{
  "name": "selfhook",
  "scripts": {
    "prepare": "npm run setup:hooks",
    "setup:hooks": "node scripts/install-hooks.js",
    "lint": "eslint ."
  }
}
EOF
mkdir -p "$SH/scripts/git-hooks"
printf '#!/bin/sh\nbd sync --flush\nclaude -p review\n' > "$SH/scripts/git-hooks/pre-commit"
printf '#!/bin/sh\necho legacy-post\n' > "$SH/scripts/git-hooks/post-commit"
cp "$SH/scripts/git-hooks/pre-commit" "$SH/.git/hooks/pre-commit"
chmod 755 "$SH/.git/hooks/pre-commit" "$SH/scripts/git-hooks/pre-commit"

run_install --dry-run "$SH"
assert_eq "R7b dry-run: exits 0" 0 "$RI_EXIT"
assert "R7b dry-run: plans source-hook replacement" out_has "scripts/git-hooks/pre-commit"
assert "R7b dry-run: writes nothing" grep -q 'bd sync' "$SH/scripts/git-hooks/pre-commit"

run_install "$SH"
assert_eq "R7b: exits 0" 0 "$RI_EXIT"
assert "R7b: live hook archived" grep -q 'bd sync' "$SH/.git/hooks/pre-commit.pre-gates"
assert "R7b: source hook replaced with gate hook" \
  cmp -s "$SH/scripts/git-hooks/pre-commit" "$SH/.git/hooks/pre-commit"
assert "R7b: source hook is the gate hook" \
  grep -q 'Generated by install-gates' "$SH/scripts/git-hooks/pre-commit"
assert "R7b: other source-dir files untouched" \
  grep -q 'echo legacy-post' "$SH/scripts/git-hooks/post-commit"
assert_not "R9: no bd invocation in any installed hook" \
  grep -E '(^|[^[:alnum:]_])bd ' \
    "$SH/.git/hooks/pre-commit" "$SH/scripts/git-hooks/pre-commit" \
    "$SH/scripts/check.sh" "$SH/.claude/hooks/pre-tool-protect.sh" \
    "$SH/.claude/hooks/post-tool-format.sh" "$SH/.claude/hooks/stop-gate.sh"

shh1="$(find_hash "$SH")"
run_install "$SH"
assert_eq "R7b: second run exits 0" 0 "$RI_EXIT"
shh2="$(find_hash "$SH")"
assert_eq "R7b/R3: double-run managed-file hashes identical" "$shh1" "$shh2"

# R7b negative: prepare script but no scripts/git-hooks/pre-commit → no
# source replacement.
NP="$TMP/nodeprepare"
mkrepo "$NP"
cat > "$NP/package.json" <<'EOF'
{
  "name": "nodeprepare",
  "scripts": {
    "prepare": "npm run build",
    "lint": "eslint ."
  }
}
EOF
run_install --dry-run "$NP"
assert_eq "R7b negative: exits 0" 0 "$RI_EXIT"
assert_not "R7b negative: no source replacement without scripts/git-hooks/pre-commit" \
  out_has "git-hooks"

# ---------------------------------------------------------------------------
# R9: beads leftovers abort the run with a pointer to the beads exit spec.
# ---------------------------------------------------------------------------

BD="$TMP/beadsfix"
mkrepo "$BD"
printf 'requests\n' > "$BD/requirements.txt"
mkdir "$BD/.beads"
run_install "$BD"
assert_not "R9: beads repo aborts" test "$RI_EXIT" -eq 0
assert "R9: abort mentions beads-full-exit" out_has "beads-full-exit"
assert "R9: nothing written" test ! -d "$BD/.claude" -a ! -e "$BD/scripts"

# ---------------------------------------------------------------------------
# R6: inventory exclusion rules — worktrees and hidden paths programmatic;
# dead/non-candidate by inventory list membership; space-safe paths; excluded
# targets are skipped and reported; active-list repos with zero commits still
# proceed (the activity rule is never re-derived).
# ---------------------------------------------------------------------------

assert "R6: repo inventory copied into toolkit docs" \
  test -f "$TOOLKIT_DIR/docs/repo-inventory.md"

FH="$TMP/fakehome"
mkdir -p "$FH"

run_excluded() { # run_excluded <repo> — run installer with a fake $HOME
  RI_OUT="$(HOME="$FH" "$INSTALL" "$1" 2>&1)"
  RI_EXIT=$?
}

mkrepo "$FH/goal tracker"
printf 'requests\n' > "$FH/goal tracker/requirements.txt"
run_excluded "$FH/goal tracker"
assert_eq "R6 dead-list (space-safe): exits 0" 0 "$RI_EXIT"
assert "R6 dead-list: reported excluded" out_has "excluded"
assert "R6 dead-list: nothing written" test ! -d "$FH/goal tracker/.claude"

mkrepo "$FH/vaults/life"
run_excluded "$FH/vaults/life"
assert_eq "R6 non-candidate: exits 0" 0 "$RI_EXIT"
assert "R6 non-candidate: reported excluded" out_has "excluded"
assert "R6 non-candidate: nothing written" test ! -d "$FH/vaults/life/.claude"

mkrepo "$FH/.hidden/repo"
run_excluded "$FH/.hidden/repo"
assert_eq "R6 hidden path: exits 0" 0 "$RI_EXIT"
assert "R6 hidden path: reported excluded" out_has "excluded"

mkrepo "$FH/mainrepo"
printf 'x\n' > "$FH/mainrepo/f.txt"
git -C "$FH/mainrepo" add f.txt
git -C "$FH/mainrepo" -c user.email=t@example.com -c user.name=t commit -qm init
git -C "$FH/mainrepo" worktree add -q "$FH/wtree" >/dev/null 2>&1
run_excluded "$FH/wtree"
assert_eq "R6 worktree (.git is a file): exits 0" 0 "$RI_EXIT"
assert "R6 worktree: reported excluded" out_has "excluded"

mkrepo "$FH/automation"
printf 'requests\n' > "$FH/automation/requirements.txt"
run_excluded "$FH/automation"
assert_eq "R6 in-scope control: exits 0" 0 "$RI_EXIT"
assert "R6 in-scope control: not excluded (active list, zero commits)" \
  out_has "stack: python"
assert "R6 in-scope control: gates installed" \
  test -f "$FH/automation/.claude/settings.json"

# ---------------------------------------------------------------------------

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
