#!/usr/bin/env bash
# Hidden grader for the `fixture` selftest task. Runs OUTSIDE both arms' mounts
# (a sibling of repo/, never copied in), invoked by run.sh with the produced
# worktree as the current directory. Trivial by design: the fixture exists to
# exercise the runner's plumbing, not to be a hard task. Exit 0 = pass.
set -eu
[ -f solution.txt ] || { echo "assert: solution.txt missing" >&2; exit 1; }
grep -qx 'fixed' solution.txt || { echo "assert: solution.txt not 'fixed'" >&2; exit 1; }
