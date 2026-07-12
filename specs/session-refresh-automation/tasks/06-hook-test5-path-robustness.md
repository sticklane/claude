Status: draft
Discovered-from: spec-completion review (specs/session-refresh-automation/evidence/spec-review.md)
Spec: ../SPEC.md
Blocking: no

# hook test.sh test 5 may not exercise the intended jq-absent branch

Test 5 in hooks/session-refresh/test.sh sets `PATH=/usr/bin:/bin` to test
the agentprof-absent path, but on macOS `jq` commonly lives in
/usr/local/bin or /opt/homebrew/bin — the hook likely exits at the earlier
`command -v jq` check instead of the intended branch. The assertion still
passes but may not exercise the intended code path; machine-dependent.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
