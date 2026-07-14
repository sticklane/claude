#!/usr/bin/env bash
# Mechanical antigravity CONTENT-parity gate
# (spec codequality-antigravity-content-parity).
#
# Complements test_antigravity_parity.sh (which is existence-only, R5): this
# gate asserts byte-identity for the narrow, contractually-identical subset of
# mirrored .py files — those that must stay a straight copy across
# .claude/skills/<path> and antigravity/.agents/skills/<path>.
#
# INCLUDE-LIST (fixed, enumerated on purpose — NOT a glob): only files with a
# byte-parity contract belong here. Mirrored .py files that carry a SANCTIONED
# port adaptation are deliberately EXCLUDED, because including them would make
# the gate go permanently red on a legitimate divergence:
#   - prioritize/*.py                 (standalone-install docstring + run-path)
#   - list-specs/test_list_specs.py   (.agents/skills/ run-path adaptation)
#   - workboard/test_workboard.py     (.agents/skills/ run-path adaptation in
#                                      its `Run:` docstring; antigravity commit
#                                      cf8e2b3 re-applied it deliberately)
# SKILL.md prose divergence is also out of scope (antigravity is a port, not a
# copy). See the spec's Problem/Out-of-scope sections.
#
# Output: on success, exit 0 with NO output. On failure, print each divergent
# include-list path (one per line) and exit 1.
#
# Fixture-redirect seam: pass --fixture (or set CONTENT_PARITY_FIXTURE=1) to
# swap the ENTIRE compared file set to the committed self-test fixture pair
# under tests/fixtures/content-parity/{claude-side,antigravity-side}/. This
# proves the gate catches divergence without depending on the real tree ever
# being broken.
set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"

fixture_mode="${CONTENT_PARITY_FIXTURE:-0}"
if [ "${1:-}" = "--fixture" ]; then
  fixture_mode=1
fi

if [ "$fixture_mode" != "0" ]; then
  # Self-test mode: compare the deliberately-divergent fixture pair.
  claude_root="$repo_root/tests/fixtures/content-parity/claude-side"
  ag_root="$repo_root/tests/fixtures/content-parity/antigravity-side"
  files=(
    example.py
  )
else
  # Real tree: the byte-identical, contractually-mirrored .py subset.
  claude_root="$repo_root/.claude/skills"
  ag_root="$repo_root/antigravity/.agents/skills"
  files=(
    _shared/spec_readiness.py
    _shared/test_spec_readiness.py
    _shared/test_viz.py
    _shared/viz.py
    workboard/workboard.py
    list-specs/list_specs.py
  )
fi

divergent=()
for f in "${files[@]}"; do
  if ! diff -q "$claude_root/$f" "$ag_root/$f" >/dev/null 2>&1; then
    divergent+=("$f")
  fi
done

if [ "${#divergent[@]}" -gt 0 ]; then
  for d in "${divergent[@]}"; do
    echo "$d"
  done
  exit 1
fi
exit 0
