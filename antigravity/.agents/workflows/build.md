---
description: Execute one task file (or a small SPEC.md) end to end - scout, plan proportionally, implement test-first, verify independently, commit. Run in a fresh conversation per task.
---

Execute the task file given after the command. This is the pipeline's inner
loop; it assumes an agent-ready task/spec with runnable acceptance criteria.

1. **Load only the task.** Read the task file (and its spec's Requirements
   section if referenced). Mark Status `in-progress` (a bare SPEC.md has no
   Status field — skip the bookkeeping and work from its acceptance
   criteria directly). Do NOT preload the codebase: for anything unclear,
   apply the scout skill and work from `path:line` conclusions. Read a file
   in full only when about to edit it. If the task has no runnable
   acceptance criteria, STOP and say it isn't agent-ready — don't improvise
   weaker criteria.

2. **Plan proportionally.** Diff describable in one sentence → implement
   directly. Otherwise write the implementation plan (files to change, in
   what order, what could go wrong) as a comment block in the task file,
   placed below the header lines (never between them — dispatchers parse
   the headers and the block must not break them), and pause for review
   before executing — unless launched unattended by a workflow, in which
   case plan as a comment block and proceed.
   If the plan contradicts the task or reveals a missing decision, surface
   it rather than guessing.

3. **Implement, verification-first.** Where acceptance criteria are
   test-shaped: write the failing tests FIRST, run them, confirm they fail
   for the right reason, commit the tests, then implement until green —
   without modifying the tests. Match the surrounding code's style; no
   drive-by refactors. Run the narrowest relevant test after each
   meaningful change.

4. **Verify with fresh eyes.** Run every acceptance command; fix until all
   pass. Run the project's standard gates (per AGENTS.md). Then apply the
   verifier skill against the task file, passing an evidence file path
   derived from the task file's location: `specs/<slug>/tasks/<name>.md` →
   `specs/<slug>/evidence/<name>.md`; a bare `specs/<slug>/SPEC.md` →
   `specs/<slug>/evidence/spec.md`; any other layout → no path (nothing is
   written; note at close-out that evidence was not persisted). The full
   report goes in that file; a re-verify overwrites it. Put the actual
   command output in the walkthrough artifact too — the native walkthrough
   complements the committed file, it doesn't replace it. On FAIL: fix and
   re-verify. After two failed fix attempts on the same issue, stop:
   write findings into the task file and end with a verdict — DONE
   (all acceptance passing), DEFERRED (a question a human must
   answer), or BLOCKED (stuck after the fix attempts) — rather than
   thrashing.

5. **Close out.** Simplification pass over the code touched: never change
   what the code does, only how; remove comments describing obvious code,
   redundant abstractions, and defensive handling for impossible cases;
   re-run the acceptance commands after. Update the task file (Status
   `done`, ticked boxes, one line of evidence each rather than
   duplicating output — citing the `evidence/` file when an evidence
   path was passed in step 4; delete the plan comment block from
   step 2). Commit code + task file referencing the task — plus the
   `evidence/` file when an evidence path was passed; otherwise note
   that evidence was not persisted and keep the one-line evidence
   inline in the task file as the artifact. Push/PR only if asked. The
   close-out report ends with a fixed `Discovered:` section — zero or
   more single-line items, each "what + where + why it matters", for
   work found but out of the task's scope (an empty section means none;
   never create or edit task files for discoveries as part of the
   report) — and for non-DONE outcomes one fixed `Done vs remaining:`
   line summarizing partial progress. For items in `Discovered:`, offer
   to write each as a header-only `Status: draft` stub in the owning
   spec's tasks/ dir (the format in the drain workflow's step 3) —
   written only on the user's yes; no silent queue writes. If anything was
   learned the hard way, apply the distill skill. Tell the user to start
   the next task in a NEW conversation.
