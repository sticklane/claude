---
name: build
description: Executes one task file (or a small SPEC.md) end to end - explore via scouts, plan proportionally, implement test-first, verify with an independent agent, commit. The interactive, foreground way to work a task with a human at the keyboard; run it in a fresh session per task. Trigger phrases - "/build", "build this task", "work this task file", or a pipeline chain the user's live message requested ("spec, critique, breakdown, then build").
argument-hint: "[path/to/task.md or SPEC.md]"
---

Execute the task at $ARGUMENTS. This skill assumes an agent-ready task/spec
with runnable acceptance criteria and is designed to run in a fresh session.

## Bounded, walk-away runs (/goal)

`/build`'s default is unbounded and attended. To run it unattended — the
human wraps this skill's own procedure in the runtime's built-in `/goal`
transcript-evaluator so it stops at a bounded condition (`/goal "<criteria>,
or stop after N turns"`; `/build` parses no new flag and needs no code
change) — first clear this go/no-go gate.

**Classification (go/no-go).** A peripheral feature, prototype, or migration
with mechanical, runnable verification is fine for a `/goal`-bounded run.
Core business logic, security-sensitive code, or verification that is
inherently "looks right" is not — those don't disqualify the task, they
raise the bar it must clear first: tighten acceptance criteria to runnable
commands and confirm worktree isolation covers every side effect, or stay on
unbounded attended `/build`, today's default. A task whose "correct" is a
judgment call no test can settle is an unresolved spec question, not a
walk-away run — file it and resolve the spec instead of launching.

**Escalation triggers.** Two triggers escalate to a human instead of pressing
on: the same step failing twice (a third attempt in a degraded context won't
do better), and reaching a high-risk action — push, deploy, data deletion,
publishing, spending — which the run must never take on its own.

For long `/goal`-bounded runs that grow heavy before finishing, write a
`/handoff` file and end rather than pressing on in a degraded context. The
scoped-permissions template, containment ladder, headless template, and
failure-recovery doctrine for unattended runs live in
[reference.md](reference.md).

## 0. Load only the task

Emit `<!-- agentprof:stage=load -->` verbatim as this step's opening line
every time you enter it — agentprof reads it from this session's transcript
to attribute cost/tokens/time to this stage until the next stage marker.

**Startup session sweep (advisory).** Before reading the task, list other
live sessions whose cwd resolves into this repo (the pre-flight in
`.claude/rules/concurrent-sessions.md`, cited not restated: `claude agents
--json`, worktree list, unexplained working-tree changes): one line per
foreign live session, a "sweep unavailable" line on failure, never
blocking.

Read the task file (and its spec's Requirements section if referenced). Mark
the task's Status as `in-progress` (a bare SPEC.md has no Status field — skip
the bookkeeping steps for it and work from its acceptance criteria directly).
Claim the task in bd as well: its issue's title is the task file's
repo-relative path (shadow-sync's upsert key), and `/work`'s SKILL.md owns
the claim commands and the `.beads/session-claims` bookkeeping — cite it,
don't restate it. Skip the claim only when the issue is already claimed (a
drain dispatch claims before launching its worker) or bd is unavailable on
this machine; note either case in one line rather than silently working
untracked.
Record the current revision identifier now — the base the verifier's
append-only task-file diff runs against in step 3 (e.g., under git: `git rev-parse HEAD`). Do NOT preload the codebase: for anything
unclear about existing code, fan out `scout` agents and work from their
reports. Read a file directly only when you're about to edit it.

**Structure lookups (ctx).** When `.context/` exists at the repo root, this
repo carries a `ctx` structure index. For a definition, caller, signature,
or outline question, run the ctx query BEFORE any Grep/Read: `ctx tree
<path>` (a file's or module's symbol outline), `ctx sig <symbol>` (a
symbol's signature), `ctx refs <symbol>` (its callers/references), `ctx deps
<path>` (a file's import graph). Fall back to Grep for content/text
questions (bodies, literals, patterns) and Read a file only when about to
edit it. Brief every scout you dispatch the same way.

If the task file has no runnable acceptance criteria, stop and say the task
isn't agent-ready — improvising weaker criteria silently is how "looks done"
replaces "is done".

**Rigor tier (gate scaling).** Read the task's effective `Rigor:` header (the
task's own, else its spec's; absent = `production`). `production` (or absent)
is today's full procedure below, unchanged. `Rigor: prototype` scales the
gates at steps 2–3: skip TDD red-first (step 2) and skip this run's own
`verifier` spawn (step 3), substituting a mechanical run of the task's
acceptance commands as the reported signal. Never scaled at any tier: commit
hygiene, the task's runnable acceptance criteria, and the untrusted-data
rules. State in close-out (step 4) that prototype gates applied. This is the
primary path — it applies to attended /build AND to drain's
attempt-1/relaunch workers, who run this procedure verbatim.

## 1. Plan proportionally

Emit `<!-- agentprof:stage=plan -->` verbatim as this step's opening line
every time you enter it.

- Diff describable in one sentence → skip planning, implement.
- Otherwise → write a short plan (files to change, in what order, what could
  go wrong) as a comment block in the task file, placed below the header lines
  (never between them — dispatchers parse the headers and the block must not
  break them). Think hard on genuinely tricky design points; don't burn
  extended thinking on mechanical steps.
- Plan contradicts the task or reveals a missing decision → stop and surface
  it rather than guessing.
- A mid-task decision with a **reversible default** (the attended parallel to
  the worker's decision-deferral rule): take the default and keep working
  rather than interrupting — record each (decision, default taken, how to
  reverse) and log them to the task file's `## Decisions` section at close-out
  (step 4). A decision with NO reversible default, or any on the human-gates
  list (irreversible, blast-radius, spend, authority), still stops and
  surfaces to the user — being attended, it asks rather than parks.

## 2. Implement, verification-first

Emit `<!-- agentprof:stage=implement -->` verbatim as this step's opening
line every time you enter it.

- On `Rigor: prototype` (step 0): skip TDD red-first — implement directly
  against the acceptance criteria; commit hygiene still holds. The
  `production` default keeps the test-first rule below.
- Where acceptance criteria are test-shaped (production rigor): write the
  failing tests FIRST, run them, confirm they fail for the right reason,
  commit the tests, then implement until green — without modifying the tests.
- Match the surrounding code's style and idiom; no drive-by refactors (that's
  scope creep the verifier will flag).
- Run the narrowest relevant test after each meaningful change, not the whole
  suite every time.

## 3. Verify with fresh eyes

Emit `<!-- agentprof:stage=verify -->` verbatim as this step's opening line
every time you enter it.

**`Rigor: prototype` (gate scaling, step 0).** On a prototype-rigor task,
skip sub-step 3's `verifier` spawn entirely: sub-step 1's acceptance-command
run is the reported signal — report DONE when every acceptance command passes
and sub-step 2's project gates are green, BLOCKED otherwise, so drain's
verdict-driven routing (relaunch, merge) works unchanged. Sub-steps 1
(acceptance commands) and 2 (project gates) still run mechanically and are
never skipped. `production` (or absent) runs the full step 3 including the
verifier below.

**Promotion rule.** Prototype code never merges into a `Rigor: production`
spec's work without re-running the full gates — promoting a prototype means
flipping the `Rigor:` header and treating the existing code as untested input
to a normal production task, not as done work.

1. Run every acceptance command yourself; fix until all pass.
2. Run the project's standard gates. Run `scripts/check.sh`, the
   sole required check entrypoint — never a hand-derived list of steps read
   out of CLAUDE.md prose (repos without it fall back to their own
   build/lint/test commands).
3. Spawn the `verifier` agent with the task file path and instruct it to
   verify the working tree against the acceptance criteria. It has no memory
   of your implementation and won't rationalize shortcuts. Pass it the base
   commit recorded in step 0 for its append-only task-file diff, alongside an
   evidence file path derived from the task file's location:
   `specs/<slug>/tasks/<name>.md` → `specs/<slug>/evidence/<name>.md`; a
   bare `specs/<slug>/SPEC.md` → `specs/<slug>/evidence/spec.md`; any other
   layout → pass no path (the verifier then writes nothing; note at
   close-out that evidence was not persisted). The verifier writes its full
   report there; a re-verify overwrites it.
4. Collect every subagent's result within your current turn — ending a
   turn while a verifier or monitor is still pending orphans its report
   (the observed stall mode in drained runs). If a subagent goes silent,
   respawn it once and continue.
5. On FAIL: fix and re-verify. After two failed fix attempts on the same
   issue, stop and report — repeated correction in a degraded context is the
   known failure mode; a fresh session with a better task file beats a long
   session of thrashing.
6. Heavy-context escape: when the session itself has grown heavy — not just
   one stuck fix — write a `/handoff` file and lead the report with its resume
   command instead of continuing degraded.
7. Stopping blocked (the **same-edit** rule): when the session must stop on
   an external blocker it cannot clear — missing creds, an undeployed
   dependency, a product decision only the user can make — write
   `Status: blocked` AND its `Unblock:` line into the task file in the **same
   edit**, never a bare `blocked` with no recorded move. Pick the narrowest
   type (breakdown's grammar): `Unblock: run: <cmd>` when a shell command can
   check or clear it, `Unblock: agent: <prompt>` when clearing needs an
   agent's judgment, `Unblock: ask: <exact question>` only for a genuine human
   decision, quoting the exact question. The `Unblock:` line goes on the line
   immediately after `Status:`. **HUMAN.md pair (R3), ATTENDED `/build` only:**
   that intra-file `Status:`+`Unblock:` atomicity is UNCHANGED, and the SAME
   COMMIT also makes a second edit adding a matching entry to the repo-root
   `HUMAN.md`'s `## Agent-filed blockers` section, typed to the `Unblock:` line
   (`run`→`run`, `ask`→`ask`, a credentials/access blocker → `provision`;
   grammar in `.claude/rules/human-blockers.md`). An `Unblock: agent:` stop is
   agent-clearable, not a human blocker, so it files no entry. This is
   attended-scope only: a DRAINED/unattended worker NEVER writes `HUMAN.md` — it
   returns its BLOCKED verdict and drain's orchestrator (not the worker) files
   the entry; a worker that wrote `HUMAN.md` would fail drain's merge-time Touch
   whitelist.

## 4. Close out

Emit `<!-- agentprof:stage=close-out -->` verbatim as this step's opening
line every time you enter it.

- Simplification pass over the code touched this session: run the bundled
  `/simplify` if available, otherwise apply its principles yourself — never
  change what the code does, only how; remove comments that describe obvious
  code, redundant abstractions, and defensive handling for cases that can't
  happen. Hold comments to quality-discipline.md's self-documenting-code
  section (public surface only; calibration pairs in
  `.claude/skills/example-corpus/code-examples.md`). Re-run the acceptance
  commands after.
- Pre-commit review (one pass, no re-review after fixes): compute the skip
  gate first — stage all changes and diff against the step-0 base revision
  for per-path line counts; staging first surfaces brand-new untracked
  files, and `<step0-base>` is the base revision recorded in step 0
  (e.g., under git: `git add -A && git diff <step0-base> --numstat`). Classify each path NON-product
  when it matches `docs/**`, `**/*.md`, `tests/**`, `test/**`, `**/test_*`,
  `**/*_test.*`, `**/*.test.*`, `**/*.spec.*`, `**/*.json`, `**/*.yaml`,
  `**/*.yml`, `**/*.toml`, `**/*.lock`. Skip the review — record
  `review skipped: <docs-only|tests-only|tiny-diff (<lines>)>` and go
  straight to commit — when there are no product paths, or total
  added+deleted product lines is < 25. Otherwise invoke `/code-review` via
  the Skill tool with args `low` when the runtime can pass them (bare
  invocation when it can't); where the Skill tool or plugin is unavailable,
  fall back to ONE subagent on the diff, prompted for high-confidence
  correctness/behavior findings only, capped at ≤1k tokens returned — run
  it as an AWAITED child (synchronous dispatch, per token-discipline's
  awaited-children rule): spawn it, wait for its result, collect it before
  close-out; never fire-and-forget, never leave a child running past your
  own finish (drain reference.md's sub-reviewer clause, cited not
  restated). For each finding: fix immediately iff it's a
  correctness/behavior defect AND the fix stays inside the task's `Touch:`
  — or, with no `Touch:` header, inside the files touched this session (the
  simplification pass's scope) — then re-run the acceptance commands;
  findings needing out-of-Touch edits, or judged uncertain, are never fixed
  here: surface to the user when attended, or add to `Discovered:` when
  unattended. Style findings are dropped (the simplification pass already
  ran). This is one pass — no re-review after fixes. Record the outcome as
  evidence: `review: N findings, M fixed, K discovered` or
  `review skipped: <reason>`. When this /build run's target was a bare
  SPEC.md (no `tasks/`), additionally run the spec-completion review
  (specs/spec-completion-review) over the run's whole diff through this same
  pre-commit review machinery — a bare-SPEC run has no per-task pass to catch
  spec-level gaps; task-file /build runs are unchanged, their per-task pass
  already covers them. Before committing, also run the doc-currency check in
  quality-discipline.md's Documentation currency section (cited, not
  restated). That check lives there, not by /code-review itself —
  `/code-review` stays scoped to what the harness/plugin defines it to check.
- Log any reversible-default decisions taken this session (step 1's rule) to
  the task file's `## Decisions` section — one line each: decision, default
  taken, how to reverse. Append; never overwrite prior entries. No decisions
  taken → no section needed.
- Persist a durable structure note (indexed repo only): when `.context/`
  exists at the repo root and this task surfaced a symbol-anchored fact that
  meets the code-comment bar — a gotcha, invariant, rationale, or todo tied
  to a specific symbol, not a restatement of what the code plainly shows —
  offer to record it with `ctx notes add <symbol> "<text>" --kind
gotcha|invariant|rationale|todo` before finishing (the note is committed;
  it survives refactors the code comment would not).
- Update the task file: Status `done`, tick acceptance boxes, one line of
  evidence each (from the verifier's report, not your own claim) rather
  than duplicating output — citing the `evidence/` file when an evidence
  path was passed in step 3; delete the plan comment block from step 1.
  Close the task's bd issue and clear its `.beads/session-claims` line in
  the same breath (`/work`'s close flow, cited not restated) — unless the
  claim was the dispatching orchestrator's (drain closes what it claimed)
  or bd is unavailable, noted in one line either way.
- Commit code + task file with a message referencing the task, following
  quality-discipline.md's `## Commits` doctrine — a type-prefixed subject
  (≤72 target, hard cap 100) with detail in the body — plus the
  verifier's `evidence/` file when an evidence path was passed; otherwise
  note that evidence was not persisted and keep the one-line evidence
  inline in the task file as the artifact. Then **publish the default branch
  on completion** (e.g., under git: `git push`) — subject to drain/SKILL.md's canonical push guard
  (upstream-configured only, non-fatal, never `--force`; a failed push
  warns and continues since the commit already landed locally). Open a PR
  only if the user asked.
- Report: what shipped, evidence summary, anything learned the hard way — and
  if there WAS such a learning, run /distill before ending. The report ends
  with a fixed `Discovered:` section — zero or more single-line items, each
  "what + where + why it matters", for work found but out of the task's scope
  (an empty section means none; never create or edit task files for
  discoveries as part of the report). Each `Discovered:` item is ALSO filed
  in bd the moment it's reported — `bd create` with a `discovered-from`
  link to this task's issue (CLAUDE.md's Beads section, cited not
  restated); a bd issue is a tracker record, not a task file, so this
  doesn't touch the no-queue-writes rule. Same dispatch carve-out as the
  claim and close bullets: a drain-dispatched worker only REPORTS
  `Discovered:` lines and never runs `bd create` — drain files them
  (drain reference.md's worker prompt). Skip with a one-line note when
  bd is unavailable. For non-DONE outcomes the report also carries
  one fixed `Done vs remaining:` line summarizing partial progress.
- For items in `Discovered:`, offer to write each as a header-only
  `Status: draft` stub in the owning spec's tasks/ dir (the format in drain's
  bookkeeping step) — written only on the user's yes; no silent queue writes.
- Tell the user to `/clear` before starting the next task. Then, only if
  the just-completed task file resolves to a `specs/<slug>/tasks/*.md` path
  AND at least one sibling `tasks/*.md` in that same directory has a
  `Status: pending` header line — checked with `grep -l '^Status: pending'
specs/<slug>/tasks/*.md` (a header-only match, never a full `Read` of each
  sibling file) — print one additional line pointing the user
  at `/drain specs/<slug>` for continuous work across the remaining tasks
  (alongside, not replacing, the `/clear` line). If the path is not under a
  `specs/<slug>/tasks/` layout, or the only siblings are `Status: blocked`
  (or there are no siblings — the `grep -l` prints nothing), print no nudge
  line — this is a printed pointer, not a loop, so do not over-fire it.

## Ultra path

When ultracode is opted in and build runs top-level (an attended `/build`,
not a drain worker), build's verification runs as a workflow instead of one
verifier. A build worker dispatched by drain always uses the single-verifier
step 3 above — `Workflow` nesting is one level only, so a worker inside
drain's workflow cannot compile its own; this is not a gate, it's the nesting
rule. This skill only names the shape.

Acceptance commands run FIRST as the deterministic gate. Each criterion with
no runnable command then gets a refute-majority vote — 3 verifiers on distinct
lenses, the criterion failing on a majority refute. The fix-reverify loop is
script-owned and bounded at 4 cycles; on the 4th unresolved cycle build flips
to blocked with the failure evidence rather than thrashing. Everything else —
scouts, test-first implementation, close-out — is unchanged.
