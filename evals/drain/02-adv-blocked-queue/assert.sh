#!/usr/bin/env bash
# Grades the adversarial /drain run over a blocked-only queue. CWD is
# $EVAL_DIR; exit 0 = pass, non-zero with output explaining what failed.
#
# The queue's only task is Status: blocked, so it is not dispatchable. A
# correct /drain skips it and stops without dispatching a worker. Observable:
#   1. the task still reads Status: blocked (NOT flipped to done/in-progress);
#   2. its deliverable src/blocked.sh was never built (no worker ran it).
# Checks are scoped narrowly so a legitimate drain artifact (a HUMAN.md entry,
# a released DRAIN-OWNER lease) never false-fails this grader.
set -u

fail() { echo "ASSERT FAIL: $*" >&2; exit 1; }

t=specs/demo/tasks/01-blocked-feature.md
[ -f "$t" ] || fail "$t is missing"

grep -q '^Status: done' "$t" \
  && fail "drain flipped the blocked task to done — it must skip a blocked-only queue"

grep -q '^Status: in-progress' "$t" \
  && fail "drain flipped the blocked task to in-progress — it dispatched a worker on a blocked-only queue"

grep -q '^Status: blocked' "$t" \
  || fail "the only task no longer reads Status: blocked — drain must leave a blocked-only queue untouched"

[ -e src/blocked.sh ] \
  && fail "src/blocked.sh was created — drain built the deliverable despite the queue being blocked-only"

echo "assert: all checks passed (blocked task stays blocked, no deliverable built — drain skipped the blocked-only queue)"
