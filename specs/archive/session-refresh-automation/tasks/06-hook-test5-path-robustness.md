Status: done
Promotion-ready: true
Promoted-by-run: a219d53ef6bba100
Discovered-from: spec-completion review (specs/session-refresh-automation/evidence/spec-review.md)
Spec: ../SPEC.md
Blocking: no
Depends on: 03
Budget: 6
Touch: hooks/session-refresh/test.sh, hooks/session-refresh/fixtures/fake-jq.sh

# hook test.sh test 5: exercise the agentprof-absent branch machine-independently

## Goal

Make test 5 reliably reach the hook's agentprof-binary-absent code path on
any machine: the test's restricted PATH must still resolve `jq` — via a
committed fake-jq fixture placed on the test PATH — so the hook cannot
short-circuit at its earlier `command -v jq` guard, while `agentprof`
remains unresolvable. TDD: first demonstrate the current short-circuit (or
its machine-dependence) with a failing/inconclusive check, then wire the
fixture.

## Acceptance

- [x] `test -x hooks/session-refresh/fixtures/fake-jq.sh` exits 0 (new committed executable fixture; path absent today). Evidence: verifier ran it → rc=0 (evidence/06-hook-test5-path-robustness.md).
- [x] `grep -c "fake-jq" hooks/session-refresh/test.sh` returns ≥ 1 (the fixture is wired into test 5's PATH; literal absent from the file today). Evidence: grep returned 2 (evidence/06-hook-test5-path-robustness.md).
- [x] `bash hooks/session-refresh/test.sh 2>&1 | grep -q "missing agentprof binary produces empty stdout"` exits 0 (test 5's existing assertion still present and reported). Evidence: rc=0 (evidence/06-hook-test5-path-robustness.md).
- [x] `bash hooks/session-refresh/test.sh` exits 0 (full suite green; the script exits nonzero on any failed check — test count may grow beyond today's 10). Evidence: 10 passed, 0 failed, rc=0 (evidence/06-hook-test5-path-robustness.md).
