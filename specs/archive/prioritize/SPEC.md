# /prioritize: interview-driven reprioritization of a repo's pending work

## Problem

The `Priority:` task-file header (`P0`-`P3`, default `P2`) is the only
dispatch tie-break `/drain` honors (`.claude/skills/drain/SKILL.md`), and
`/breakdown` assigns it once at decomposition time — but nothing lets a
human revisit and rebalance it later without hand-editing task files one
at a time. `/workboard` doesn't surface Priority at all, and no skill
presents "here's everything open in this repo, tell me what to reorder" in
one pass. Per Anthropic's own published guidance
(`docs/external-playbooks.md`'s Task prioritization section: "priority
assigned ahead of the run, agent honors it, doesn't invent it"), the human
pre-assigns priority and the agent just honors it — this skill is the
missing on-ramp for that human step.

## Solution

A new skill, `/prioritize`, scoped to the current repo (per the user's own
framing, "reprioritize ... in a repo"), invoked only by a human
(`disable-model-invocation: true`) since it mutates task files and commits
— consistent with `/build`/`/drain`/`/autopilot` (mutating,
commit-producing skills stay human-launched), and distinct from
`/list-specs` (read-only, stays model-invocable). Its deterministic half is
a script, `.claude/skills/prioritize/prioritize_scan.py`, that reuses
`scan_toolkit_specs` from `.claude/skills/workboard/workboard.py` (same
`importlib.util.spec_from_file_location`-on-absolute-path loading
`specs/list-specs` established) for the task list and each task's `abs`
path — `scan_toolkit_specs` does **not** parse `Priority:` at all (grep
confirms no such field on its returned dict), so `prioritize_scan.py` adds
its own `Priority:` regex parse over each task's `abs` file content: it
enumerates every task across every spec in `specs/` (excluding `archive/`,
excluded the same way `scan_toolkit_specs` already excludes it) whose
`status` is `pending`, `blocked`, `deferred`, or `draft`, plus one row per
spec with no `tasks/` breakdown yet (its `SPEC.md` stands in, since it's
the only file in that spec carrying a `Status:`/`Priority:` header pair),
and prints a markdown table. Its interactive half is `/prioritize`'s own
SKILL.md prose: present that table, take one free-form reply describing
the desired changes, apply them by editing each named file's (task or
`SPEC.md`) `Priority:` header, and commit.

## Requirements

- **R1**: `prioritize_scan.py` collects every task (across every non-archive
  spec in `specs/`) whose status is `pending`, `blocked`, `deferred`, or
  `draft` — `done`, `skipped`, and `in-progress`/`in_progress`/`claimed`/
  `failed` tasks are never listed. It also emits one row per spec whose
  `tasks/` list is empty (no breakdown yet), using that spec's `SPEC.md` as
  the row: `ref` is `<slug>/SPEC.md`, `status` is the SPEC's own `Status:`
  header value (lowercased) or `open` when absent, `priority` follows the
  same rule as task rows — except a task-less spec whose own `Status:` is
  `done` or `skipped` gets no row at all (it isn't reorderable work; the
  fallback row exists only to represent specs still open). If nothing
  qualifies at all, it prints "nothing to reprioritize" and the skill
  stops there (no interview).
- **R2**: The table has columns `Ref | Title | Status | Priority`, sorted
  by spec slug then task number (a spec's `SPEC.md` fallback row is its
  only row, so its position among task numbers is moot). `Ref` is
  `<spec-slug>/<task-filename>` or `<spec-slug>/SPEC.md`
  (e.g. `drain-sweep-preservation/03-worker-commits.md`) — the exact
  string the user can echo back unambiguously, since a bare task filename
  like `03-foo.md` could collide across specs. `Priority` shows the
  row's actual header value, or `P2 (default)` when the header is absent.
- **R3**: After printing the table, `/prioritize` asks exactly one
  free-form question (not AskUserQuestion, which caps at 4 options and
  can't represent an arbitrary re-ranking): "What changes should I make?
  Reference tasks by their `Ref` (e.g. 'make
  drain-sweep-preservation/03-worker-commits.md P0'). Say 'none' if
  you're done looking." This is deliberately conversational, not a rigid
  grammar — the executing session itself interprets the reply the way it
  would interpret any natural-language instruction.
- **R4**: For each task the reply identifies with a target priority, the
  skill validates the target is one of `P0`/`P1`/`P2`/`P3` (case
  insensitive, normalized to uppercase) and that the `Ref` matches a row
  from R2's table. A `Ref` not in the table, or a target outside
  `P0`-`P3`, is **not applied**; it is listed back to the user as "not
  applied: <reason>" rather than guessed at or silently skipped.
- **R5**: For every validated change, edit that file's (task or `SPEC.md`)
  `Priority:` header line to the new value: if the file already has a
  `Priority:` line, replace it in place; otherwise add one immediately
  below `Status:` when a `Status:` line exists. Otherwise the insertion
  point depends on the file kind: a headerless task file gets it as the
  first header line, above the first `#`/`##` heading (matching a
  drain-discovered task file's header-before-title shape) — R1 already
  includes header-less tasks (their status defaults to `pending`, per
  `scan_toolkit_specs`'s own default), so this fallback is reachable, not
  hypothetical; a headerless `SPEC.md` instead gets it immediately below
  the `# Title` line, since every real `SPEC.md` in this repo puts its
  title first. No other line in the file is touched.
- **R6**: If at least one change was applied, commit every edited task
  file in one commit: `chore: reprioritize <N> task(s) across <M> spec(s)
  per interview` — never leave the edits uncommitted (per this repo's own
  commit-discipline convention). If the reply was "none" or every proposed
  change failed R4 validation, make no commit.
- **R7**: A reply of "none" (or equivalent — "no changes", "looks fine")
  ends the skill cleanly with no edits and no commit.
- **R8**: `.claude/skills/prioritize/SKILL.md` carries
  `disable-model-invocation: true` in its frontmatter (per the Solution
  section's reasoning) and closes with `Next stage: none — the human
  decides what to /build or /drain next` (this skill doesn't feed a
  downstream pipeline stage the way `/breakdown` or `/design` do).
- **R9 (disambiguation from `/list-specs`)**: Both skills scan the same
  `specs/*/tasks/` and render a table, so `/prioritize`'s own
  frontmatter `description` explicitly distinguishes itself — reordering
  `Priority:` headers, not reporting the next pipeline command — and
  names `/list-specs` as the "just tell me what to run next" alternative
  (and `specs/list-specs`'s own description reciprocally names
  `/prioritize` as the "reorder, don't just report" alternative), so a
  user asking "what should I work on" or "what's open in this repo" is
  pointed at the right one instead of guessing.

## Out of scope

- Promoting a `draft` task to `pending` (or any other status transition) —
  `/prioritize` only ever rewrites `Priority:`; `Status:` stays a human
  editing it directly (or a decision for `/workboard`'s inbox).
- Cross-repo prioritization — single repo only, matching `/list-specs`'
  scope, not `/workboard`'s cross-repo scan.
- Any automatic re-ordering/suggestion of priorities by the skill itself
  (e.g. inferring unblocking-power) — this skill only applies what the
  human explicitly states; it never invents an ordering.
- A rigid command grammar for R3's reply — free-form natural language,
  interpreted by the executing session, is the only supported input.

## Acceptance criteria

- [ ] `python3 .claude/skills/prioritize/prioritize_scan.py` against a
      fixture repo with zero pending/blocked/deferred/draft tasks and no
      task-less specs prints "nothing to reprioritize" and produces no
      table.
- [ ] Same script against a fixture with 2 specs, each having a mix of
      pending/blocked/deferred/done/draft tasks: the table lists the
      pending/blocked/deferred/draft ones (not `done`/`in-progress`/etc.),
      with `Ref` values in `<slug>/<filename>` form, sorted by spec then
      task number.
- [ ] A fixture spec with no `tasks/` dir at all gets exactly one row,
      `<slug>/SPEC.md`, whose status/priority come from the SPEC.md's own
      `Status:`/`Priority:` headers (or their documented defaults). A
      fixture spec with no `tasks/` dir whose `SPEC.md` reads `Status: done`
      or `Status: skipped` gets no row at all.
- [ ] Fixture task with no `Priority:` header shows `P2 (default)` in the
      table.
- [ ] A fresh agent running `/prioritize` against that fixture, given the
      reply "make <spec>/<task> P0, everything else stays" — where
      `<spec>/<task>` names a fixture task whose current priority is NOT
      already `P0` (so the edit is guaranteed to produce a diff): edits
      exactly that one task file's `Priority:` header to `P0`, no other
      task file changes, and `git log` shows one commit touching only
      that file.
- [ ] Same fixture, reply referencing a `Ref` not in the table (e.g. a
      typo'd filename): that change is reported as "not applied", no file
      is edited for it, and any OTHER valid changes in the same reply are
      still applied and committed.
- [ ] Same fixture, reply "none": no files change, no commit is made.
- [ ] End-to-end: running `/prioritize` in this repo (`/Users/sjaconette/claude`)
      produces a table of its current pending/blocked/deferred/draft tasks
      plus task-less-spec rows (excluding `archive/`) and, given at least
      one valid reprioritization instruction, produces exactly one commit
      reflecting it.

## Authoring note

Acceptance criteria in this repo cite the real per-subproject checks that
were actually run (e.g. `python3 -m pytest .claude/skills/workboard/ -q`),
never a top-level `bash scripts/check.sh` — this repo has no such gate.

## Open questions

(none)

## Parallelization

None — strictly serial. Task 02 depends on 01 (its SKILL.md invokes the
script and its mirror byte-copies task 01's files), so there is no group
with disjoint Touch and no dependency edge. Dispatch 01, then 02.

## Closure (2026-07-13 verification sweep)

Verified. Disable-model-invocation criterion obsoleted by the
launch-authorization contract (c139218); mirror docstring divergence sanctioned
by e835f5a. Closed verified.
