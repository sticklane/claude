Status: done
Promotion-ready: true
Promoted-by-run: bc1c30ae8ac43971
Discovered-from: specs/mirror-procedure-discipline/tasks/05-audit-factcheck.md
Spec: ../SPEC.md
Depends on: 01
Priority: P2
Budget: 7 turns
Touch: antigravity/.agents/skills/factcheck/reference.md, tests/mirror-procedure-manifest.txt

## Goal

Audit `antigravity/.agents/skills/factcheck/reference.md` for procedural
divergence against its source `.claude/skills/factcheck/reference.md` and
record the finding in the audit manifest, per
`.claude/rules/mirror-procedure-discipline.md`'s load-bearing-vs-incidental
classification (read that rule first — task 01 must be done before this one
starts). Task 05 audited factcheck's `SKILL.md` but this `reference.md` (the
worker-prompt template) was outside that task's Touch scope and has never
been read side-by-side against its source.

A stub-intake assessor pass this run already did a preliminary side-by-side
read and found ALL divergences either load-bearing (worker-type naming —
`general-purpose` agent vs. "web-capable Agent Manager conversation";
cross-reference target — `.claude/rules/token-discipline.md` vs. `AGENTS.md`;
tier language — "Haiku / `effort: low`" vs. "scout-tier / low effort") or
incidental prose-only synonyms (LLM→model, Launch→Open, "inside this task"→
"inside this conversation") with no dropped step, condition, count, or
reordered decision. Confirm this holds with your own fresh full read — do
not assume it without checking — and record it; a zero-fix audit is a valid
outcome here, same as several other tasks in this spec.

## Touch

Only the two files listed in the header. Do not touch any other skill's
mirror files, `.claude/skills/factcheck/` (the source — reconcile the mirror
TO it, never edit the source), or the rule/gate files from task 01.

## Steps

1. Read `.claude/rules/mirror-procedure-discipline.md` (task 01's output)
   for the divergence classification.
2. Read `.claude/skills/factcheck/reference.md` in full as the source of
   truth.
3. Read `antigravity/.agents/skills/factcheck/reference.md` in full.
4. Compare procedure, not prose: for each step/decision point in the
   source, confirm the mirror expresses the same behavior unless the
   divergence is load-bearing.
5. Fix any incidental divergence found — small, targeted edits.
6. Append a `# checked: factcheck — reference.md — <summary>` comment line
   to `tests/mirror-procedure-manifest.txt` (or a phrase-expressible
   manifest line if any incidental fix was made).
7. Run the acceptance commands yourself before marking done.

## Acceptance

- [x] `bash tests/test_mirror_procedure_coverage.sh` → exit 0 (no output) — verifier PASS (2026-07-16 sweep)
- [x] `grep -c "checked: factcheck — reference.md" tests/mirror-procedure-manifest.txt` → 1 — verifier PASS (2026-07-16 sweep)
- [x] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → all 15 tests pass, no FAIL lines — verifier PASS (2026-07-16 sweep)
- [x] `bash evals/lint-ultra-gate.sh` → exit 0 ("OK — all ultra mentions gated in 4 files") — verifier PASS (2026-07-16 sweep)
