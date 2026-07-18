---
description: Execute one task file (or a small SPEC.md) end to end - scout, plan proportionally, implement test-first, verify independently, commit. Run in a fresh conversation per task.
---

Execute the task file given after the command. It assumes an agent-ready
task/spec with runnable acceptance criteria.

## Bounded, walk-away runs

This workflow's default is unbounded and attended. Antigravity has no
`/goal` transcript-evaluator, so an unattended run means either staying at
the keyboard with an explicit stop condition stated up front ("<criteria>
pass, or stop after ~N turns") or a background Agent Manager agent on a
worktree running the drain workflow's worker prompt. Either way set the
Terminal Execution Policy deny list (push, deploy, rm) first, then clear
this go/no-go gate.

**Classification (go/no-go).** A peripheral feature, prototype, or migration
with mechanical, runnable verification fits a bounded run. Core business
logic or security-sensitive code doesn't disqualify a task — it raises the
bar it must clear first: tighten acceptance criteria to runnable commands
and confirm worktree isolation covers every side effect, or stay on
unbounded attended execution. A task whose "correct" is a judgment call no
test can settle is an unresolved spec question, not a walk-away run — file
it and resolve the spec instead of launching.

**Escalation triggers.** Two triggers escalate to a human instead of
pressing on: the same step failing twice (a third attempt in a degraded
context won't do better), and reaching a high-risk action — push, deploy,
data deletion, publishing, spending — which the run must never take on its
own.

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
   **Rigor tier (gate scaling).** Read the task's effective `Rigor:` header
   (the task's own, else its spec's; absent = `production`). `production` (or
   absent) is the full procedure below, unchanged. `Rigor: prototype` scales
   steps 3–4: skip TDD red-first (step 3) and skip this run's own
   verifier-skill application (step 4), substituting a mechanical run of the
   task's acceptance commands as the reported signal. Never scaled at any
   tier: commit hygiene, the task's runnable acceptance criteria, and the
   untrusted-data rules. State in close-out (step 5) that prototype gates
   applied. This primary path applies to attended runs AND to the drain
   workflow's attempt-1/relaunch workers, who run this procedure verbatim.

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
   On `Rigor: prototype` (step 1), skip TDD red-first: implement directly
   against the acceptance criteria (commit hygiene still holds); the
   `production` default keeps the test-first rule that follows. Where
   acceptance criteria are
   test-shaped (production rigor): write the failing tests FIRST, run them, confirm they fail
   for the right reason, commit the tests, then implement until green —
   without modifying the tests. Match the surrounding code's style; no
   drive-by refactors. Run the narrowest relevant test after each
   meaningful change.

4. **Verify with fresh eyes.** Open this step by emitting
   `<!-- agentprof:stage=verify -->` verbatim each time you enter it.
   **`Rigor: prototype` (gate scaling, step 1).** On a prototype-rigor task,
   skip the verifier-skill application below: the acceptance-command run is
   the reported signal — end with DONE when every acceptance command passes
   and the project gates are green, BLOCKED otherwise, so the drain
   workflow's verdict-driven routing works unchanged. The acceptance commands
   and project gates still run mechanically and are never skipped.
   **Promotion rule:** prototype code never merges into a `Rigor: production`
   spec's work without re-running the full gates — promoting a prototype
   means flipping the `Rigor:` header and treating the existing code as
   untested input to a normal production task, not as done work. `production`
   (or absent) runs the full verification below.
   Run every acceptance command; fix until all
   pass. Run the project's standard gates: run `scripts/check.sh`, the
   sole required check entrypoint — never a hand-derived list of steps read
   out of AGENTS.md prose (repos without it fall back to their own
   build/lint/test commands). Then apply the
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
   Stopping blocked (the **same-edit** rule): when the session must stop on
   an external blocker it cannot clear (missing creds, an undeployed
   dependency, a product decision only the user can make), write
   `Status: blocked` AND its `Unblock:` line into the task file in the SAME
   edit, never a bare `blocked` with no recorded move. Pick the narrowest
   type: `Unblock: run: <cmd>` when a command checks or clears it,
   `Unblock: agent: <prompt>` when clearing needs an agent's judgment,
   `Unblock: ask: <exact question>` only for a genuine human decision. The
   `Unblock:` line sits on the line immediately after `Status:`.
   **HUMAN.md pair (R3), this attended workflow only:** that intra-file
   `Status:`+`Unblock:` atomicity is UNCHANGED, and the SAME COMMIT also adds
   a matching entry to the repo-root `HUMAN.md`'s `## Agent-filed blockers`
   section, typed to the `Unblock:` line (`run`→`run`, `ask`→`ask`, a
   credentials/access blocker → `provision`; grammar in
   `.claude/rules/human-blockers.md`). An `Unblock: agent:` stop is
   agent-clearable, not a human blocker, so it files no entry. This is
   attended-scope only: a drained/unattended worker NEVER writes `HUMAN.md` —
   it returns its BLOCKED verdict and the orchestrator (not the worker) files
   the entry.

5. **Close out.** Open this step by emitting
   `<!-- agentprof:stage=close-out -->` verbatim each time you enter it.
   Simplification pass over the code touched: never change
   what the code does, only how; remove comments describing obvious code,
   redundant abstractions, and defensive handling for impossible cases;
   re-run the acceptance commands after. Pre-commit review, one pass with
   no re-review after fixes: compute the skip gate first by staging all
   changes and diffing against the base revision for per-path line counts
   (staging first surfaces new untracked files; `<base>` is the revision
   recorded when the task started;
   e.g., under git: `git add -A && git diff <base> --numstat`),
   classifying each path NON-product when it matches `docs/**`,
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
   clause, cited not restated). The doc-currency check is a separate
   close-out step the worker runs directly, not by the sub-reviewer fallback,
   which stays scoped to correctness/behavior findings. Fix a finding immediately iff it is a
   correctness/behavior defect AND the fix stays inside the task's
   `Touch:` — or, with no `Touch:` header, inside the files touched this
   session — then re-run the acceptance commands; findings needing
   out-of-Touch edits, or judged uncertain, are never fixed here: surface
   them, or add to `Discovered:` when unattended. Style findings are
   dropped since the simplification pass already ran. Record the outcome
   as evidence: `review: N findings, M fixed, K discovered` or
   `review skipped: <reason>`. When this /build run's target was a bare
   SPEC.md (no `tasks/`), additionally run the spec-completion review
   (specs/spec-completion-review) over the run's whole diff through this
   same pre-commit review machinery — a bare-SPEC run has no per-task pass
   to catch spec-level gaps; task-file /build runs are unchanged, their
   per-task pass already covers them. Before committing, also run the
   doc-currency check — see AGENTS.md's Quality discipline section (cited, not
   restated). Log any reversible-default decisions taken
   this session (step 2's rule) to the task file's `## Decisions` section —
   one line each: decision, default taken, how to reverse. Append; never
   overwrite prior entries. No decisions taken → no section needed. Update
   the task file (Status
   `done`, ticked boxes, one line of evidence each rather than
   duplicating output — citing the `evidence/` file when an evidence
   path was passed in step 4; delete the plan comment block from
   step 2). Commit code + task file referencing the task, following
   AGENTS.md's commit-hygiene rules — a type-prefixed subject (≤72 target,
   hard cap 100) with a **subject/body** split putting detail in the body —
   plus the
   `evidence/` file when an evidence path was passed; otherwise note
   that evidence was not persisted and keep the one-line evidence
   inline in the task file as the artifact. Then **publish the default
   branch on completion** (e.g., under git: `git push`) — subject to the drain workflow's canonical push guard
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
   the next task in a NEW conversation. Then, only when the just-completed
   task file sits at a `specs/<slug>/tasks/*.md` path AND a sibling
   `tasks/*.md` in that directory carries a `Status: pending` header, add
   one line pointing the user at the drain workflow over `specs/<slug>` for
   continuous work through the remaining tasks — alongside, not replacing,
   the new-conversation instruction. When the path is not that layout, or
   the only siblings are `Status: blocked` (or there are none), add no such
   line — it is a printed pointer, not a loop, so do not over-fire it.

## Ultra path

Antigravity has no Workflow tool and no runtime profile, so the ultra
verification path is permanently closed here — the single-verifier step 4
above is always the path. (For reference: in the Claude Code toolkit, an
opted-in ultracode run runs acceptance commands first as a deterministic
gate, gives each un-runnable criterion a 3-verifier refute-majority vote,
and bounds the fix-reverify loop at 4 cycles before flipping to blocked.
That gate never opens in this mirror.)
