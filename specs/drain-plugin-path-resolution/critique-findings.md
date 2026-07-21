# Critique findings — drain-plugin-path-resolution

SPEC.md hash: 5c8c3e7df7182d82b6c3c94709698d53e8742a5a8880803b368a81e81cd88447
Verdict: READY WITH NITS

## 2026-07-21

Round 1: NOT READY (5 findings — 3 mechanical stale line-number
references, a vacuous R7 version criterion, a gameable R1 positive
check). All mechanical findings and both substantive judgment findings
fixed; re-critiqued.

Round 2 (settled): READY WITH NITS — two low-severity findings left
open, both explicitly non-blocking and naturally resolved at breakdown
time:

1. [JUDGMENT, conf 62] R7's acceptance criterion (`git show
<task-base-commit>:...`) leaves how a verifier derives
   `<task-base-commit>` unresolved, and "parse both as dotted integers
   and confirm greater" is prose, not a runnable command. Breakdown
   should pin the concrete `git merge-base HEAD main` form (or
   equivalent) and a one-line dotted-int comparison in the generated
   task file.
2. [JUDGMENT, conf 60] R6's acceptance criterion has a `<phrase>` hole
   only filled "at breakdown time" — normal for the mirror-manifest
   pattern, but breakdown must record the chosen runtime-neutral phrase
   back into the generated task file so verification has a literal to
   grep, not "or a close paraphrase" left open-ended.
