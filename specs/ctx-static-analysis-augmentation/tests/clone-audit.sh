#!/usr/bin/env bash
# Runnable rediscovery check for the clone-audit skill (R3).
#
# Runs the documented clone-detection recipe (.claude/skills/clone-audit/
# reference.md) against the in-repo TS and Go fixture pairs under
# specs/ctx-static-analysis-augmentation/fixtures/clone-audit/ and asserts
# both the TS clone and the Go clone are reported. Run from the repo root.
set -euo pipefail

FIXTURES_DIR="specs/ctx-static-analysis-augmentation/fixtures/clone-audit"
REPORT_DIR="$(mktemp -d)"
trap 'rm -rf "$REPORT_DIR"' EXIT

if [ ! -d "$FIXTURES_DIR" ]; then
  echo "FAIL: fixtures dir missing: $FIXTURES_DIR" >&2
  exit 1
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "MANUAL-PENDING: npx not available in this environment; cannot run the jscpd recipe. See .claude/skills/clone-audit/reference.md for the documented command." >&2
  exit 1
fi

# The documented recipe (see .claude/skills/clone-audit/reference.md):
# npx jscpd --format typescript,go -r json -o <out> <path>
if ! npx --yes jscpd --format typescript,go -r json --silent -o "$REPORT_DIR" "$FIXTURES_DIR" >"$REPORT_DIR/run.log" 2>&1; then
  # jscpd exits 0 even when clones are found unless --threshold/--exit-code
  # is set; a nonzero exit here means the tool itself failed to run
  # (e.g. no network to fetch the package).
  echo "MANUAL-PENDING: jscpd invocation failed (no network install access?). Log:" >&2
  cat "$REPORT_DIR/run.log" >&2
  exit 1
fi

REPORT_JSON="$REPORT_DIR/jscpd-report.json"
if [ ! -f "$REPORT_JSON" ]; then
  echo "FAIL: expected report not written: $REPORT_JSON" >&2
  exit 1
fi

TS_FOUND="$(python3 -c "
import json
report = json.load(open('$REPORT_JSON'))
names = set()
for dup in report.get('duplicates', []):
    names.add(dup['firstFile']['name'])
    names.add(dup['secondFile']['name'])
print('yes' if {'ts/discount.ts', 'ts/discount-clone.ts'} <= names else 'no')
")"

GO_FOUND="$(python3 -c "
import json
report = json.load(open('$REPORT_JSON'))
names = set()
for dup in report.get('duplicates', []):
    names.add(dup['firstFile']['name'])
    names.add(dup['secondFile']['name'])
print('yes' if {'go/discount.go', 'go/discount_clone.go'} <= names else 'no')
")"

if [ "$TS_FOUND" != "yes" ]; then
  echo "FAIL: TS clone pair (discount.ts / discount-clone.ts) not reported" >&2
  cat "$REPORT_JSON" >&2
  exit 1
fi

if [ "$GO_FOUND" != "yes" ]; then
  echo "FAIL: Go clone pair (discount.go / discount_clone.go) not reported" >&2
  cat "$REPORT_JSON" >&2
  exit 1
fi

echo "PASS: clone-audit recipe rediscovered both the TS and Go fixture clones"
