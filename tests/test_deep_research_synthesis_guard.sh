#!/usr/bin/env bash
# Tests for deep-research.js's synthesis grounding guard.
#
# Incident (2026-07-16, swarm-decomposition research): a deep-research run's
# verify stage did real, citation-backed work, but the final synthesis-stage
# result was a literal stub — {"summary":"test","findings":[{"claim":"test
# claim",...}],"caveats":"test caveat"} — and the workflow reported it as a
# completed report. Downstream work treated it as real research and never
# caught the placeholder.
#
# The fix is a grounding check: every synthesized finding must cite at least
# one source URL that traces back to a claim the verify stage actually
# confirmed. A stub (or any hallucinated/ungrounded synthesis, not just this
# specific incident's placeholder strings) cites no real source and fails
# the check.
#
# This test extracts looksUngrounded() straight out of the shipped workflow
# script (via `new Function`) and exercises it in isolation — the deep-research
# workflow script itself runs only inside the Workflow tool's own sandboxed
# runtime (no filesystem/require access there), so its logic can't be
# exercised end-to-end from a plain test harness. Extracting the real
# function body means this test tracks the actual shipped logic, not a
# hand-maintained duplicate that can drift.
set -u

TOOLKIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$TOOLKIT_DIR/.claude/workflows/deep-research.js"

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

assert "deep-research.js exists" test -f "$SRC"

node - "$SRC" <<'NODE'
const fs = require('fs')
const src = fs.readFileSync(process.argv[2], 'utf8')

const m = src.match(/function looksUngrounded\([^)]*\)\s*\{[\s\S]*?\n\}/)
if (!m) {
  console.error('FAIL: could not find looksUngrounded() in deep-research.js')
  process.exit(1)
}

const body = m[0].replace(/^function looksUngrounded\([^)]*\)\s*\{/, '').replace(/\}$/, '')
const looksUngrounded = new Function('report', 'confirmedClaims', body)

let pass = 0, fail = 0
function assertEq(desc, expected, actual) {
  if (expected === actual) { pass++ } else { fail++; console.error(`FAIL: ${desc} (expected ${expected}, got ${actual})`) }
}

const confirmed = [
  { sourceUrl: 'https://real-source.example/a', claim: 'Real thing happened' },
  { sourceUrl: 'https://real-source.example/b', claim: 'Another real thing' },
]

const grounded = {
  summary: 'Real synthesis.',
  findings: [{ claim: 'Real thing happened', confidence: 'high', sources: ['https://real-source.example/a'], evidence: 'because' }],
  caveats: 'none',
}
assertEq('grounded report is not flagged', false, looksUngrounded(grounded, confirmed))

// The actual incident shape: placeholder claims, no real source cited.
const stub = {
  summary: 'test',
  findings: [{ claim: 'test claim', confidence: 'low', sources: [], evidence: 'test' }],
  caveats: 'test caveat',
}
assertEq('stub report (no real source cited) is flagged', true, looksUngrounded(stub, confirmed))

// Fabricated finding citing a URL that was never actually verified.
const fabricated = {
  summary: 'Plausible-sounding synthesis.',
  findings: [{ claim: 'Something that sounds real', confidence: 'high', sources: ['https://not-a-real-source.example/x'], evidence: 'because' }],
  caveats: 'none',
}
assertEq('fabricated report citing an unverified source is flagged', true, looksUngrounded(fabricated, confirmed))

assertEq('report with zero findings is flagged', true, looksUngrounded({ summary: 'x', findings: [], caveats: 'x' }, confirmed))
assertEq('null report is flagged', true, looksUngrounded(null, confirmed))

console.log(`node-subtests: passed ${pass}, failed ${fail}`)
process.exit(fail === 0 ? 0 : 1)
NODE
node_rc=$?
assert "looksUngrounded() extraction and behavior assertions all pass" test "$node_rc" -eq 0

# ─── Static checks: the retry-then-degrade wiring is actually present ───
assert "synthesis result is checked with looksUngrounded before being trusted" \
  grep -q "looksUngrounded(report" "$SRC"
assert "an ungrounded synthesis triggers a bounded retry, not a silent pass-through" \
  grep -q "synthesize-retry" "$SRC"
assert "a still-ungrounded report after retry does not return as a completed report" \
  grep -qE "looksUngrounded\(report, confirmed\)\)\s*\{" "$SRC"

echo "---"
echo "passed: $pass, failed: $fail"
[ "$fail" -eq 0 ]
