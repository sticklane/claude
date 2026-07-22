#!/usr/bin/env bash
# Hidden grader for the `crashfixture` selftest task. Structurally identical to
# fixture's grader (checks for a completed solution.txt). It is never expected
# to reach a pass here: the stub session crashes before finishing, so run.sh
# forces pass:false without consulting this script. It exists so the task is a
# well-formed, scoreable member of the manifest. Exit 0 = pass.
set -eu
[ -f solution.txt ] || { echo "assert: solution.txt missing" >&2; exit 1; }
grep -qx 'fixed' solution.txt || { echo "assert: solution.txt not 'fixed'" >&2; exit 1; }
