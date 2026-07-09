---
description: Execute one task file (or a small SPEC.md) end to end - scout, plan proportionally, implement test-first, verify independently, commit. Run in a fresh conversation per task.
---

Execute the task file given after the command. This is the pipeline's inner
loop; it assumes an agent-ready task/spec with runnable acceptance criteria.

1. **Load only the task.** Open this step by emitting
   `<!-- agentprof:stage=load -->` verbatim each time you enter it —
   agentprof reads it from this session's transcript to attribute
   cost/tokens/time to the stage until the next stage marker.
   Before reading the task, run a startup session
   sweep (advisory): check whether another live session's working
   directory is this same repo — the Agent Manager's session list, or
   whatever runtime session record is available; unavailable → one
   "sweep unavailable" line and continue. Print one line per foreign live
   session found; this never blocks the run, it only surfaces a possible
   concurrent editor before you touch anything (concurrent-sessions rule,
   folded into AGENTS.md, cited not restated). If the task's spec has a
   `specs/<slug>/DRAIN-OWNER.md` showing FRESH liveness (the drain
   workflow's Owner lease liveness definition, cited not restated), warn
   before editing the task — ask the user whether to proceed rather than
   risk racing a live drain run. Read the task file (and its spec's
   Requirements section if referenced). Mark Status `in-progress` (a bare
   SPEC.md has no Status field — skip the bookkeeping and work from its
   acceptance criteria directly). Do NOT preload the codebase: for
   anything unclear, apply the scout skill and work from `path:line`
   conclusions. Read a file in full only when about to edit it. If the
   task has no runnable acceptance criteria, STOP and say it isn't
   agent-ready — don't improvise weaker criteria.

2. **Plan proportionally.** Open this step by emitting
   `<!-- agentprof:stage=plan -->` verbatim each time you enter it.
   Diff describable in one sentence → implement
   directly. Otherwise write the implementation plan (files to change, in
   what order, what could go wrong) as a comment block in the task file,
   placed below the header lines (never between them — dispatchers parse
   the headers and the block must not break them), and pause for review
   before executing — unless launched unattended by a workflow, in which
   case plan as a comment block and proceed.
   If the plan contradicts the task or reveals a missing decision, surface
   it rather than guessing.
   A mid-task decision with a **reversible default** (the attended parallel
   to the worker's decision-deferral rule): take the default and keep
   working rather than interrupting — record each (decision, default taken,
   how to reverse) and log them to the task file's `## Decisions` section at
   close-out (step 5). A decision with NO reversible default, or any on the
   human-gates list (irreversible, blast-radius, spend, authority), still
   stops and surfaces to the user — being attended, it asks rather than
   parks.

3. **Implement, verification-first.** Open this step by emitting
   `<!-- agentprof:stage=implement -->` verbatim each time you enter it.
   Where acceptance criteria are
   test-shaped: write the failing tests FIRST, run them, confirm they fail
   for the right reason, commit the tests, then implement until green —
   without modifying the tests. Match the surrounding code's style; no
   drive-by refactors. Run the narrowest relevant test after each
   meaningful change.

4. **Verify with fresh eyes.** Open this step by emitting
   `<!-- agentprof:stage=verify -->` verbatim each time you enter it.
   Run every acceptance command; fix until all
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
   Heavy-context escape: attended build has no baton (that is the drain
   workflow's degradation response); when the session itself has grown
   heavy — not just one stuck fix — apply the handoff skill to write a
   handoff file and lead the report with its resume command instead of
   continuing degraded. This is the escape available to an attended run
   where the baton cannot apply.

5. **Close out.** Open this step by emitting
   `<!-- agentprof:stage=close-out -->` verbatim each time you enter it.
   Simplification pass over the code touched: never change
   what the code does, only how; remove comments describing obvious code,
   redundant abstractions, and defensive handling for impossible cases;
   re-run the acceptance commands after. Pre-commit review, one pass with
   no re-review after fixes: compute the skip gate first with
   `git add -A && git diff <base> --numstat` (staging first surfaces new
   untracked files; `<base>` is the commit HEAD was at when the task
   started), classifying each path NON-product when it matches `docs/**`,
   `**/*.md`, `tests/**`, `test/**`, `**/test_*`, `**/*_test.*`,
   `**/*.test.*`, `**/*.spec.*`, `**/*.json`, `**/*.yaml`, `**/*.yml`,
   `**/*.toml`, `**/*.lock`; skip straight to commit — recording
   `review skipped: <docs-only|tests-only|tiny-diff (<lines>)>` — when
   there are no product paths or total added+deleted product lines is
   under 25; otherwise, since this mirror has no code-review skill to
   invoke directly, run ONE subagent on the diff prompted for
   high-confidence correctness/behavior findings only and capped at ≤1k
   tokens returned — run it as an awaited child (start it, wait for it,
   collect its result before close-out; never fire-and-forget, never
   leave a child conversation running past your own finish — the
   awaited-children dispatch rule; the drain workflow's sub-reviewer
   clause, cited not restated). Fix a finding immediately iff it is a
   correctness/behavior defect AND the fix stays inside the task's
   `Touch:` — or, with no `Touch:` header, inside the files touched this
   session — then re-run the acceptance commands; findings needing
   out-of-Touch edits, or judged uncertain, are never fixed here: surface
   them, or add to `Discovered:` when unattended. Style findings are
   dropped since the simplification pass already ran. Record the outcome
   as evidence: `review: N findings, M fixed, K discovered` or
   `review skipped: <reason>`. Log any reversible-default decisions taken
   this session (step 2's rule) to the task file's `## Decisions` section —
   one line each: decision, default taken, how to reverse. Append; never
   overwrite prior entries. No decisions taken → no section needed. Update
   the task file (Status
   `done`, ticked boxes, one line of evidence each rather than
   duplicating output — citing the `evidence/` file when an evidence
   path was passed in step 4; delete the plan comment block from
   step 2). Commit code + task file referencing the task — plus the
   `evidence/` file when an evidence path was passed; otherwise note
   that evidence was not persisted and keep the one-line evidence
   inline in the task file as the artifact. Then **push `main` on
   completion** (`git push`) — subject to the drain workflow's canonical push guard
   (upstream-configured only, non-fatal, never `--force`; a failed push
   warns and continues since the commit already landed locally). Open a
   PR only if asked. The
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

## Ultra path

Antigravity has no Workflow tool and no runtime profile, so the ultra
verification path is permanently closed here — the single-verifier step 4
above is always the path. (For reference: in the Claude Code toolkit, an
opted-in ultracode run runs acceptance commands first as a deterministic
gate, gives each un-runnable criterion a 3-verifier refute-majority vote,
and bounds the fix-reverify loop at 4 cycles before flipping to blocked.
That gate never opens in this mirror.)
