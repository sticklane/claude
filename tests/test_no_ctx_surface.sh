#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/config/ctx-retirement-paths.txt"
GENERIC_ALLOWLIST="$ROOT/config/ctx-generic-allowlist.txt"

fail() {
  echo "test_no_ctx_surface: FAIL — $*" >&2
  exit 1
}

test -f "$MANIFEST" || fail "missing retirement manifest"
test -f "$GENERIC_ALLOWLIST" || fail "missing generic-context allowlist"

while IFS= read -r rel; do
  case "$rel" in
    ''|'#'*) continue ;;
    /*|*'..'*|*'*'*|*'?'*|*'['*)
      fail "unsafe retirement path: $rel"
      ;;
  esac
  case "$rel" in
    specs/codebase-memory-hard-cutover*|hooks/session-refresh*|agent-console/tests/test_ctx_budget_flag.py)
      fail "retirement manifest overlaps a protected generic/current path: $rel"
      ;;
  esac
  if test -e "$ROOT/$rel" || test -L "$ROOT/$rel"; then
    fail "retirement target remains: $rel"
  fi
done <"$MANIFEST"

patterns='(^|[^[:alnum:]_])ctx([^[:alnum:]_]|$)|context-tree|agentic:ctx|skills/ctx|evals/ctx|specs/ctx-|specs/ctxignore|\\.context/|\\.ctxignore|\\.ctxzones'
product_patterns='context-tree|agentic:ctx|skills/ctx|evals/ctx|specs/ctx-|specs/ctxignore|\\.context/|\\.ctxignore|\\.ctxzones'
while IFS= read -r rel; do
  case "$rel" in
    ''|'#'*) continue ;;
    /*|*'..'*|*'*'*|*'?'*|*'['*)
      fail "unsafe generic-context allowlist path: $rel"
      ;;
  esac
  test -f "$ROOT/$rel" || fail "generic-context allowlist path missing: $rel"
  rg -qi "$patterns" "$ROOT/$rel" \
    || fail "stale generic-context allowlist path: $rel"
  if rg -qi "$product_patterns" "$ROOT/$rel"; then
    fail "generic-context allowlist hides a product reference: $rel"
  fi
done <"$GENERIC_ALLOWLIST"

raw_matches="$(
  cd "$ROOT"
  rg -n -i --hidden \
    --glob '!.git/**' \
    --glob '!.beads/**' \
    "$patterns" . 2>/dev/null || true
)"
violations=""
while IFS= read -r match; do
  test -n "$match" || continue
  rel="${match%%:*}"
  rel="${rel#./}"
  case "$rel" in
    config/ctx-generic-allowlist.txt|\
    config/ctx-retirement-*|\
    docs/codebase-memory-adoption-research-2026-07.md|\
    scripts/inventory-core-surface.py|\
    specs/codebase-memory-hard-cutover/*|\
    specs/toolkit-core-simplification/BASELINE.json|\
    tests/test_codebase_memory_integration.sh|\
    tests/test_no_ctx_surface.sh)
      continue
      ;;
  esac
  if grep -Fxq "$rel" "$GENERIC_ALLOWLIST"; then
    continue
  fi
  violations="${violations}${violations:+$'\n'}$match"
done <<<"$raw_matches"
test -z "$violations" || {
  printf '%s\n' "$violations" >&2
  fail "non-allowlisted ctx product references remain"
}

echo "test_no_ctx_surface: PASS"
