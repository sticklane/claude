#!/usr/bin/env bash
# Tests for bin/install-gates (SPEC R1, R2, R5, R7 — task 02 clean-install
# path: detection, tiers, generation). Runs against throwaway fixture repos
# in a temp dir. Never touches a real repo.
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
# Clean-install guard: a foreign pre-existing pre-commit hook aborts (merging
# and archival are task 03 — never silently clobber).
# ---------------------------------------------------------------------------

FOREIGN="$TMP/foreignhook"
mkrepo "$FOREIGN"
printf 'requests\n' > "$FOREIGN/requirements.txt"
printf '#!/bin/sh\necho legacy\n' > "$FOREIGN/.git/hooks/pre-commit"
chmod 755 "$FOREIGN/.git/hooks/pre-commit"
run_install "$FOREIGN"
assert_not "foreign hook: real run aborts (task 03 handles merging)" \
  test "$RI_EXIT" -eq 0
assert "foreign hook: original hook untouched" \
  grep -q 'echo legacy' "$FOREIGN/.git/hooks/pre-commit"
run_install --dry-run "$FOREIGN"
assert_eq "foreign hook: dry-run still exits 0" 0 "$RI_EXIT"
assert "foreign hook: dry-run reports foreign hook" out_has "existing pre-commit: foreign"

# ---------------------------------------------------------------------------

echo "pass: $pass fail: $fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
