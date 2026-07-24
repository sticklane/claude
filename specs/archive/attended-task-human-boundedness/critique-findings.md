<!-- content-hash: c9f6730fded9f0f5d62a3e2f9d310303f3594daae9dd3c7feec92c9461bae9c9 -->
<!-- verdict: NOT READY -->

# Critique findings: attended-task-human-boundedness

verdict: NOT READY (5-lens panel, unanimous — correctness, security,
verification-gaps, scope, cost-if-missed; ultra path per runtimes/
claude-code.md, drain's critique-intake self-chain, 2026-07-21)

## Convergent finding (4 of 5 lenses, independently): R3's sweep pattern over-matches ~27:1

`grep -rl 'MANUAL\|attended session only\|Unblock: decide' specs/*/tasks/`
returns 27 files; only ONE (`specs/ctx-dispatch-adoption/tasks/05-repo-allowlist-rollout.md`,
`Status: blocked` + `Unblock: decide:`) is a genuine attended-only task.
The other 26 are `Status: done` (or similar) tasks that merely contain the
substring "MANUAL" in body prose or a per-criterion acceptance marker.
R3's acceptance ("every remaining attended-only task file greps a
`HUMAN.md` reference in its `Unblock:` line, `grep -L` over the hit list
→ empty") is then either unsatisfiable (26 legitimate non-attended files
never get a HUMAN.md ref) or forces spurious HUMAN.md/Unblock edits into
two dozen unrelated, already-done tasks.

Fix (mechanical, not applied this pass): narrow the sweep to header-level
markers only — e.g. `grep -rlE '^(Status: blocked)' specs/*/tasks/` AND-ed
with `^Unblock: decide` in the same file, never a body-text "MANUAL"
match — and exclude `Status: done`.

## R3's grep -L runs against the PRE-retrofit hit list

A task correctly rewritten out of attended-only (R1) no longer needs a
HUMAN.md reference, but the acceptance check still evaluates it against
the original (pre-retrofit) hit list — so a correctly-fixed task reads as
a failure. Fix: re-run the sweep post-retrofit and check the new hit set,
not the original.

## R1/R2 acceptance checks are gameable-by-literal

`grep -q 'human-bounded' .claude/skills/breakdown/SKILL.md` (R1) and
`grep -q 'HUMAN.md' ... in the manual-flag rule's context` (R2) both pass
the moment the literal string appears anywhere in the file — neither
verifies the actual behavioral change (the launchctl/OAuth sentence
routing on the boundedness test; HUMAN.md appearing IN the manual-flag
rule's context specifically, not just somewhere in the file). Fix:
proximity/range-anchored greps (the pattern `evals/lint-ultra-gate.sh`
already uses in this repo), or a scenario check.

## "isolation" mislabeled as an author-settable task header

R1 lists "isolation" among guards "stated in its headers," but no task
header carries isolation — it's an Agent/Workflow dispatch parameter set
by the orchestrator, not something a task author can write to protect
the task. An author could believe they've guarded a task when nothing
enforces it.

## JUDGMENT — the deepest gap: no surfacing channel for the reclassified category (correctness + scope lenses)

R1 sorts every task into exactly two bins: human-bounded → HUMAN.md
entry (R2), or everything else → an ordinary agent task, explicitly
never a HUMAN.md entry. But the archetype this spec was written to fix
(task 05: machine-doable, but unsafe/impossible for an UNATTENDED
worker specifically — cross-repo mutation, launchctl) doesn't fit either
bin cleanly: it's `Status: blocked` with no HUMAN.md linkage and no
drain-dispatch path, so it still has no surfacing channel and still
"just sits" — the exact "worst of both worlds" failure the Problem
section describes. The Problem's own stated principle ("agent-bounded
work always proceeds") is false for this category: it cannot proceed
unattended, and per R1/R2 it's barred from HUMAN.md too.

## JUDGMENT — R1's "a named attended-session dispatch" category likely conflicts with your own standing directive (scope lens)

R1 sanctions filing a task with "a named attended-session dispatch" as a
structural guard, and R3's retrofit of task 05 makes it "a home-cwd
attended-or-supervised session" task. This toolkit's own recorded
guidance (a prior session's saved feedback: "~/claude toolkit: never
file/route an 'attended task'; core work raises the verification bar
instead of routing to a human-watched lane") reads as a standing
rejection of exactly this category. The spec doesn't acknowledge or
reconcile the tension — it should either justify why an attended-session
task is legitimate here, or route this class through HUMAN.md `run:`
items instead of inventing a new attended-task category.

## JUDGMENT — undefined terminal states after retrofit

R3's retrofit of task 05 leaves it "never-drain-dispatchable" +
"attended-or-supervised" — phrasing that may still match R3's own sweep
pattern, so whether the retrofitted task 05 itself still needs a
HUMAN.md reference is unresolved; two implementers would read this
differently. Fix: enumerate the exact terminal states a task may end in
(drain-agent / attended-agent-with-a-defined-surfacing-path /
human-bounded-with-HUMAN.md) and state which the R3 `grep -L` check
applies to.

## Minor / nits

- R1's antigravity-mirror requirement has no manifest entry
  (`tests/mirror-procedure-manifest.txt`) and no mirror-side grep, so
  `test_mirror_procedure_coverage.sh` won't catch drift.
- R1's "plugin.json bump per conventions" has no acceptance check.

## Not applied this pass

The mechanical fixes above (R3 sweep narrowing, post-retrofit re-check,
proximity-anchored R1/R2 greps, dropping "isolation" from the header
list, mirror-manifest + plugin.json checks) were identified but NOT
applied to SPEC.md this pass — the two JUDGMENT findings above (no
surfacing channel for the reclassified category; likely conflict with
your standing no-attended-tasks directive) look premise-level enough
that patching the mechanics first risked committing to an approach you
may want to reconsider. Recommend resolving those two before another
critique/breakdown pass.
