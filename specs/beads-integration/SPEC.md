# Discovered-work capture now, optional beads-backed queue for /drain

## Problem

Two gaps surfaced by the beads research (Steve Yegge's git-backed agent
work-memory; see docs/external-playbooks.md "Beads" entry added by this
spec). First, universal: when a drain/build worker finds NEW work mid-task
("this module also has X broken"), the toolkit has nowhere to put it — it
becomes a deferred question (wrong channel: nothing to ask) or vanishes
with the worker's context. Beads names this edge `discovered-from`; we
can steal the concept at zero dependency cost. Second, conditional: our
hand-rolled queue bookkeeping (grep-parsed Status lines) is the layer a
code review found six defects in, and beads industrializes exactly that
layer — but it is three months past a breaking rewrite, adds a Go-binary
dependency, and trades human-diffable committed state for an embedded
Dolt DB. So: capture discovered work now; make the beads queue backend
an optional, feature-detected integration rather than a default.

## Solution

Three interview decisions, recommended options adopted (picker
unavailable; reversible before implementation): (1) when beads is
active, **bd owns the queue lifecycle** — drain reads/writes queue state
via the bd CLI only, and task files carry a one-time
`Status: tracked-in-beads` stamp plus terminal stamps (done/failed) for
the PR record; (2) activation is **feature-detection** — `.beads/`
exists and `bd` is on PATH, with a documented one-line opt-out; (3)
discovered work travels **in the worker's verdict and drain records
it** — preserving the "workers report, drain records" state model —
as a `## Discovered` entry in the source task file plus a `draft` stub
task file (or a `discovered-from` edge when beads is active). Files:
`.claude/skills/drain/SKILL.md`, `.claude/skills/drain/reference.md`,
`antigravity/.agents/workflows/drain.md`, `docs/external-playbooks.md`.

## Requirements

- R1 (discovered, verdict contract): both drain worker prompts in
  `.claude/skills/drain/reference.md` (background and headless) extend
  the final-message contract with an optional block: `Discovered:` —
  zero or more entries, each "title — one-line rationale — blocking or
  non-blocking". Workers never write discoveries to files (the existing
  queue-state and untrusted-data clauses stand unchanged).
- R2 (discovered, drain records): drain's step-3 collect handles a
  verdict's Discovered entries for every verdict type — but only from
  the verdict drain finally routes (the merged tournament winner or the
  final attempt; discarded candidates' and superseded attempts'
  discoveries are dropped), deduplicating by title against the source
  task's existing `## Discovered` entries: append each to a
  `## Discovered` section in the source task file (main checkout,
  committed like all drain bookkeeping), and for each entry scaffold a
  stub task file `specs/<slug>/tasks/NN-<short-slug>.md` with
  `Status: draft`, `Discovered-from: <source task file>`, the rationale
  as Goal, and an `## Acceptance` section containing only
  `<!-- draft: needs runnable criteria before promotion -->`. A
  discovery's blocking-or-not is recorded in the stub header only (no
  edits to the source task's `Depends on:` — a human decides at
  promotion time whether anything should depend on the new task). Stub
  numbering: NN = highest task number already present in that tasks
  directory + 1, chosen at collect time. Convention, stated where
  drain's inventory defines dependencies: `Depends on:` entries may be
  task numbers (within-spec) or repo-relative task-file paths
  (cross-spec); drain inventory and the R5 bd import accept both.
- R3 (draft status): the status table in drain reference.md gains a
  `draft` row: never dispatchable, excluded from the batch interview
  and from "queue empty" (a queue with only draft+done reports drained,
  listing drafts for human promotion; a `pending` task whose
  dependencies are all drafts reports the same way — "drained pending
  promotion" — rather than leaving step 4 without a terminal
  condition). Promotion is manual: a human (or
  an /idea / /breakdown pass) replaces the placeholder Acceptance with
  runnable criteria and flips `draft` → `pending`.
- R4 (beads activation): drain SKILL.md step 1 gains the backend check,
  containing the phrase "queue backend": if `.beads/` exists at the repo
  root AND `bd` is on PATH, queue state lives in beads per reference.md's
  `## Beads backend` section; otherwise markdown Status lines exactly as
  today. Opt-out: a repo that uses beads for other purposes disables the
  backend with a one-line note in its CLAUDE.md — "drain: markdown
  queue" — which drain checks before feature-detecting.
- R5 (beads backend mapping): reference.md gains a `## Beads backend`
  section defining the full lifecycle mapping, CLI-verified at
  implementation time (record the bd version checked, mirroring the
  gemini-cli verification-note pattern):
  - first bd-mode run imports task files (see non-terminal coverage
    below): one `bd create`
    per task (title from the task header, description = repo-relative
    task-file path), dependency edges from `Depends on:` lines; each
    imported file is stamped `Status: tracked-in-beads` in one commit;
  - inventory/dispatch: `bd ready --json` replaces the header scan;
    claiming is `bd update <id> --claim` (replaces the in-progress
    flip); worker prompts are unchanged in both modes;
  - collect: DONE → merge + gates → `bd close <id>` + terminal
    `Status: done` stamp in the task file; DEFERRED → bd blocked/
    deferred status, questions still written to the task file's
    `## Deferred questions` (the batch interview reads files in both
    modes); failed → bd close-with-reason + `Status: failed` stamp;
  - discovered: `bd create` with a `discovered-from` dependency edge on
    the source issue, created in a blocked/draft state so it NEVER
    appears in `bd ready` output (R3's never-dispatchable invariant
    holds in both modes); promotion = a human writes the real task file
    with runnable acceptance and unblocks the issue. The `## Discovered`
    append still happens — it is the human-readable record;
  - DEFERRED cycle and BLOCKED verdict: the batch-interview trigger in
    bd mode is the set of bd issues in the deferred-equivalent state
    (resolved back to task files via the description path) — never the
    presence of a questions block, preserving the anti-re-ask guard;
    once answers are written under `## Answers`, drain flips the issue
    back to ready (exact bd command verified and recorded alongside the
    bd version). A BLOCKED verdict maps to bd's blocked state with the
    reason, labeled distinctly from deferred so the two remain
    separable;
  - first import covers every non-terminal task file (`pending`,
    `deferred`, `blocked`), stamping each `tracked-in-beads`, so no
    task is stranded half-markdown half-bd;
  - stale claims: bd has no lease mechanism, so drain's stale-lock rule
    maps to "claimed issue, no live worker → clear the claim, discard
    the branch/worktree" — same slot-machine semantics;
  - Touch-based independence for concurrent dispatch still comes from
    the task files (beads does not model Touch).
- R6 (mirrors): `antigravity/.agents/workflows/drain.md` mirrors R1–R3
  fully (Discovered verdict contract, drain-records collect, draft
  status) and mirrors R4/R5 as a short paragraph noting bd is a
  runtime-neutral CLI usable from Agent Manager sessions, pointing at
  the Claude Code reference for the mapping rather than restating it.
- R7 (research record): `docs/external-playbooks.md` gains a "Beads"
  entry: what was adopted now (discovered-from as R1–R3), what is
  optional (the queue backend and why — Dolt rewrite churn, binary
  dependency, loss of diffable state), and the adoption triggers
  under the literal heading-phrase "adoption triggers" (queues ≫ 10
  tasks or multi-repo; genuinely parallel claiming; recurring
  queue-state defects), with source links.
- R8 (versioning): the implementing change bumps `plugin.json`'s minor
  version by exactly one from whatever value it finds (skill behavior
  changes); if another spec's implementation lands in the same
  commit-set with its own mandated bump, one combined single-minor bump
  satisfies both.

## Out of scope

- Making beads the default, bundling the bd binary, or adding beads to
  the plugin/install instructions — the backend activates only by
  feature-detection in repos that already chose beads.
- Gas Town / multi-repo ("rig") integration.
- Migrating existing markdown queues to beads (the import in R5 covers
  pending tasks at first bd-mode run; historical done tasks stay in
  markdown).
- Using bd memories / `bd prime` (session-context injection is the
  harness's job; out of scope regardless of backend).
- Auto-promotion of draft stubs (human/idea-pass judgment by design).
- Touch/Budget modeling inside beads (task files remain the spec layer).

## Acceptance criteria

- [ ] `test "$(grep -c 'Discovered:' .claude/skills/drain/reference.md)" -ge 2` — both worker prompts carry the verdict block (R1)
- [ ] `grep -q "## Discovered" .claude/skills/drain/SKILL.md && grep -q "Discovered-from:" .claude/skills/drain/reference.md` — collect mechanics + stub header defined (R2)
- [ ] `grep -q '| \`draft\` |' .claude/skills/drain/reference.md && grep -qi "promotion" .claude/skills/drain/reference.md` (R3)
- [ ] `grep -q "queue backend" .claude/skills/drain/SKILL.md && grep -q "markdown queue" .claude/skills/drain/SKILL.md` — feature-detect + opt-out (R4)
- [ ] `grep -q "^## Beads backend" .claude/skills/drain/reference.md && awk '/^## Beads backend/,0' .claude/skills/drain/reference.md | grep -q "bd ready" && awk '/^## Beads backend/,0' .claude/skills/drain/reference.md | grep -qi "discovered-from"` (R5)
- [ ] `grep -q "Discovered" antigravity/.agents/workflows/drain.md && grep -qi "beads" antigravity/.agents/workflows/drain.md` (R6)
- [ ] `grep -qi "beads" docs/external-playbooks.md && grep -qi "adoption triggers" docs/external-playbooks.md` (R7)
- [ ] plugin.json minor version strictly greater than the pre-implementation value, verified in the implementing task's evidence (R8)
- [ ] End to end (markdown mode, no bd install needed): a fresh session executing drain's collect against a mock DONE verdict containing one non-blocking Discovered entry produces the `## Discovered` append plus a `draft` stub with `Discovered-from:` and placeholder acceptance, and a subsequent inventory pass does NOT dispatch the draft (manual dry-read until the eval harness covers /drain).
- [ ] End to end (beads mode, requires bd installed): in a scratch repo with `bd init` run, drain's import + `bd ready --json` + claim/close cycle round-trips one task per the `## Beads backend` mapping, with the bd version recorded in reference.md (manual until then).

## Open questions

(none — the three interview decisions are recorded in Solution;
recommended options adopted, reversible before implementation.)
