Status: draft
Discovered-from: specs/codequality-shared-header-parsing/tasks/02-mirror-and-bump.md
Spec: ../SPEC.md
Blocking: no

# Reconcile the antigravity Run-path docstring adaptation across mirrored test files

Task 02's acceptance criterion required `diff -r` emptiness for every
touched `.py` mirror except `prioritize_scan.py`'s docstring (the one
divergence SPEC.md names as sanctioned). To satisfy that literal
criterion, task 02 made `antigravity/.agents/skills/workboard/test_workboard.py`
and `antigravity/.agents/skills/prioritize/test_prioritize_scan.py` fully
byte-identical to their `.claude/skills/` counterparts — which dropped a
`Run:` docstring comment adapting the standalone-run path from
`.claude/skills/...` to `.agents/skills/...`.

A sibling spec (`codequality-antigravity-content-parity`, task 01, same
drain run) independently discovered and preserved this exact class of
adaptation on `workboard/test_workboard.py`, treating it as sanctioned
(the same category as `list-specs/test_list_specs.py`'s already-excluded
run-path adaptation) and excluding it from that spec's content-parity
gate's include-list for this reason.

These two outcomes are now inconsistent: one spec's task preserved the
`Run:` path adaptation as sanctioned; this spec's task erased it (in
files the content-parity gate doesn't check, so no gate caught the
inconsistency). Impact is cosmetic only — a comment, not executable
behavior — but worth a human/spec decision on which reading is
authoritative going forward: (a) re-apply the `.agents/skills/` `Run:`
path adaptation to these two test files' docstrings, treating it as a
standing sanctioned-divergence category, or (b) treat plain byte-parity
as the default for test-file docstrings too, and let sibling specs know
this class of adaptation is not exempt.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
