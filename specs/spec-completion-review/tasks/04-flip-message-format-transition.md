Status: obsolete
Closed: 2026-07-12 — stub-intake gate-confirmed OBSOLETE. Drain SKILL.md step-2 already directs the pinned flip format: SKILL.md line 227 reads "using the pinned flip-message contract `drain: <spec-slug> task NN in-progress` (this exact format is a contract, not an example …)". The earlier "e.g." hedge was removed by task 01 (done); no stale example shapes remain.
Discovered-from: specs/spec-completion-review/tasks/01-drain-step.md
Spec: ../SPEC.md
Blocking: no

# Align drain's own step-2 flip-message emission to the newly-pinned recovery-grep contract

Task 01 pinned the recovery grep `^drain: <slug> task .* in-progress`, but
drain's historical/in-flight flip messages use other shapes (`drain: task
scr/01 in-progress`, `drain: task 03 in-progress` — no slug or swapped
slug/NN order), so they miss the recovery grep and hit the "no pinned flip
commit" skip path. Intentional and self-healing for specs drained before
this ships, but confirm drain SKILL.md step 2's flip INSTRUCTION now directs
the pinned `drain: <spec-slug> task NN in-progress` format so future
generations emit matching messages; verify no stale examples remain.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
