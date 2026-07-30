#!/usr/bin/env bash
# Root entrypoint for the gate-scope-warn hook's behavior suite.
#
# scripts/check.sh enumerates root tests/test_*.sh and nothing else, so a
# hook-local test.sh is a suite the gate never runs. This wrapper is the
# delegation that puts hooks/gate-scope-warn/test.sh inside the gate; the
# authoritative cases live there.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

test -x "$ROOT/hooks/gate-scope-warn/scope-check.sh" ||
  { echo "FAIL: hooks/gate-scope-warn/scope-check.sh is missing or not executable"; exit 1; }

bash "$ROOT/hooks/gate-scope-warn/test.sh"
