# list-specs: quick per-repo spec status + next-command table

## Problem

This repo currently holds several active specs (plus a large `archive/` of
retired ones), each somewhere on the critique → breakdown → build/drain →
distill pipeline. Right now, seeing "what's open and what do I run next"
means either reading task-file headers by hand or launching `/workboard`'s
cross-repo live dashboard (a heavier, port-based tool meant for scanning
every repo on the machine, not a quick single-repo glance). There's no fast
"just tell me, for this repo, right now" command.

## Solution

A new skill, `/list-specs`, backed by a small deterministic Python script
`.claude/skills/list-specs/list_specs.py`. The script:

- Reuses `scan_toolkit_specs` and `read_text` from
  `.claude/skills/workboard/workboard.py`, loaded via
  `importlib.util.spec_from_file_location` on workboard.py's **absolute
  path** (not a bare `import workboard`, which would fail — the module
  isn't on `sys.path`). Loading it this way executes workboard.py's own
  top-level `sys.path.insert(0, .../_shared)` + `import viz`, so `viz.py`
  under `.claude/skills/_shared/` is a transitive dependency that must
  import cleanly; nothing else in workboard.py runs at import time (its
  `if __name__ == "__main__": main()` guard keeps argparse/CLI logic from
  firing).
- Does **not** reuse `CLOSED_TASK_STATUSES` / `OPEN_TASK_STATUSES` — those
  two sets conflate categories this skill must keep separate (see R3/R4).
  Instead it classifies each task's raw `status` string itself, using the
  exact literal categories in R3.
- Adds one new piece of parsing `scan_toolkit_specs` doesn't do: whether a
  spec's `SPEC.md` has unresolved content under its `## Open questions`
  section. This lives in a new shared helper,
  `.claude/skills/_shared/spec_readiness.py`, exporting
  `open_questions_unresolved(spec_md_text: str) -> bool` — see R0 for its
  exact contract — shared because `specs/workboard-auto-triage` (a sibling
  spec) needs the identical check and must not drift from this one.
- Uses `scan_toolkit_specs`'s own `tasks_total` (count of `*.md` files
  under `tasks/`) as the sole "has this spec been decomposed yet" signal —
  `tasks_total == 0` covers both a missing `tasks/` dir and an empty one
  identically, which is all R3/R4 ever need; no separate filesystem stat.
- Classifies each spec into exactly one next-command bucket (R4) and
  renders one markdown table to stdout.

The skill itself (`.claude/skills/list-specs/SKILL.md`) is a thin wrapper:
run the script against the cwd, print its stdout as the response. Unlike
`/drain`/`/build`/`/autopilot`, this skill is read-only and mutates
nothing, so it stays model-invocable (no `disable-model-invocation`).

**Disambiguation from `specs/prioritize`** (a sibling spec, also
read-only-scan-then-report over the same `specs/*/tasks/`): `/list-specs`
answers "what's the next *command* to run, per spec" (a pipeline-stage
glance — critique vs. breakdown vs. build vs. drain vs. distill);
`/prioritize` answers "what *order* should this repo's open work happen
in" (rebalancing `Priority:` headers across pending/blocked/deferred/draft
tasks and not-yet-broken-down specs). Both skills' own
descriptions cross-reference the other as the not-this-one case, so a
user asking "what should I work on" or "what's open" lands on the right
one instead of guessing.

## Requirements

- **R0**: Create `.claude/skills/_shared/spec_readiness.py` exporting
  `open_questions_unresolved(spec_md_text: str) -> bool`. It returns
  `True` only when the `## Open questions` section's body (the text
  between that heading and the next `## ` heading, or EOF), after
  collapsing all internal whitespace (including newlines) to single
  spaces and stripping the ends, is non-empty AND is not *only* a
  resolved-placeholder: case-insensitively, `none`, `(none)`, or
  `(none — ...)` / `(none - ...)` (any trailing free text after the
  em-dash/hyphen inside the parens still counts as resolved). The
  whitespace-collapse step is required because this repo's dominant
  real-world form of this placeholder **spans multiple lines**, e.g.:
  ```
  (none — the four decisions are recorded in Solution; recommended
  options adopted per the non-interactive fallback, reversible before
  implementation.)
  ```
  — a naive single-line/non-DOTALL match on this body must still resolve
  to `False` (resolved). A missing `## Open questions` heading also
  returns `False` (nothing to resolve). Unit tests cover: heading absent;
  body blank; body exactly `(none)`; single-line `(none — ready for
  breakdown)`; the multi-line `(none — ...)` example above; body with
  real unresolved prose; heading is the last thing in the file (EOF, no
  trailing `## `).
- **R0-note (drain scheduling)**: `specs/workboard-auto-triage`'s own R0
  can also create this same file, coordinated by "whichever spec's
  implementation lands first authors it, the other imports it." That
  coordination only holds for **sequential** landing — if a queue
  dispatches this spec's task and `workboard-auto-triage`'s task to two
  workers in the *same* parallel wave, both may try to create
  `_shared/spec_readiness.py` simultaneously. When these two specs are
  broken down, their tasks must not be marked independently
  parallel-dispatchable with each other (a `Depends on:` header between
  them, or explicit sequencing note in both task files) — this is a
  drain-scheduling constraint this spec's Requirements can't enforce by
  themselves, but must not be silently ignored at breakdown time.
- **R1**: Running the script against a repo with no `specs/` directory
  prints a one-line "no specs/ directory found" message and exits 0 (not
  an error).
- **R2**: `specs/archive/` (or any spec dir without a `SPEC.md` directly
  inside it) never appears in the output. (`scan_toolkit_specs` already
  requires `spec_dir/SPEC.md` to be a file, so nested archive dirs are
  excluded for free — verified against workboard.py:220.)
- **R3**: For each remaining spec, the script buckets every task by its
  raw `status` string into exactly one of these **disjoint** categories
  (a status matching none of them falls into `unrecognized`):
  - `pending_like`: `pending`, `open`, `todo`, `ready`, or **no `Status:`
    header at all** (task files with a missing header are treated as
    `pending`, matching `scan_toolkit_specs`'s own default at
    workboard.py:232 — this is a deliberate inherited default, not a new
    behavior list_specs.py invents).
  - `in_progress_like`: `in-progress`, `in_progress`, `claimed`.
  - `deferred`: `deferred`.
  - `blocked_or_failed`: `blocked`, `failed`.
  - `draft`: `draft`.
  - `done_like`: `done`, `skipped`.
  - `unrecognized`: any other literal string.
  If the spec has no `tasks/` dir (per `tasks_total == 0` in Solution —
  there is no separate filesystem stat), skip this bucketing — the status
  summary is `"no tasks/"`.
  A `tasks/` dir that exists but contains zero `.md` files is treated
  identically to "no `tasks/` dir" throughout R3/R4 (decomposition hasn't
  produced anything yet).
- **R4**: Next-command classification, in this precedence order (first
  match wins — every task's status falls into exactly one R3 category, so
  every spec matches exactly one rule below; there is no fall-through):
  1. No `tasks/` dir (or an empty one) AND `open_questions_unresolved()`
     is true → `/critique specs/<slug>/SPEC.md`
  2. No `tasks/` dir (or an empty one) AND `open_questions_unresolved()`
     is false → `/breakdown specs/<slug>/SPEC.md`
  3. `tasks/` has ≥1 file AND `deferred` count > 0 → `/drain specs/<slug>`
     (surfaces the batch interview)
  4. `tasks/` has ≥1 file AND `deferred` count == 0 AND
     `blocked_or_failed` count > 0 → flagged `blocked/failed — needs
     attention (amend spec or attended /build)`, no command
  5. `deferred` == 0 AND `blocked_or_failed` == 0 AND `pending_like` ≥ 2
     → `/drain specs/<slug>`
  6. `deferred` == 0 AND `blocked_or_failed` == 0 AND `pending_like` == 1
     → `/build specs/<slug>/tasks/<that task's filename>`
  7. `deferred` == 0 AND `blocked_or_failed` == 0 AND `pending_like` == 0
     AND `in_progress_like` > 0 → flagged `in-progress/awaiting — check
     /fleet or a drain may be running`, no command (covers specs mid-drain
     with only `claimed`/`in-progress` tasks left)
  8. All of `deferred`, `blocked_or_failed`, `pending_like`,
     `in_progress_like`, `unrecognized` == 0 AND `draft` > 0 → flagged
     `drafts ready for promotion (human: draft → pending)`, no command
     (an `unrecognized` status anywhere in the spec always outranks a
     draft-promotion flag — rule 10 catches that combination instead)
  9. All of `deferred`, `blocked_or_failed`, `pending_like`,
     `in_progress_like`, `draft`, `unrecognized` == 0 (every task is
     `done_like`) → `/distill` (per drain's own next-stage convention)
  10. Anything left over (any state with `unrecognized` > 0 that rules
      3–9 didn't already match, including `unrecognized` coexisting with
      `draft`) → flagged `unrecognized task status — needs manual check`,
      no command
  Pending counts in rules 5/6 count every `pending_like` task regardless
  of whether its dependencies are currently satisfied — this reflects
  total remaining queue work, not just what's dispatchable this second.
- **R5**: Output is one markdown table with columns `Spec | Status | Next
  command`, rows sorted alphabetically by spec slug, printed to stdout
  with no other output.
- **R6**: The skill takes no arguments — it always scans `specs/` under
  the current working directory.

## Out of scope

- Cross-repo scanning (that's `/workboard`).
- HTML/artifact output — stdout markdown table only.
- Stale-lock / dead-worker liveness detection (that's `/drain`'s job when
  it runs).
- Auto-invoking the suggested next command — this skill only prints
  suggestions (`specs/workboard-auto-triage` covers actual auto-dispatch).
- An optional repo-path argument — always the cwd, per the chosen scope.

## Acceptance criteria

- [ ] `.claude/skills/list-specs/SKILL.md`'s frontmatter `description`
      names `/prioritize` as the reorder-work alternative (the reciprocal
      half of the disambiguation above — verifiable independent of
      whether `specs/prioritize` has landed yet).
- [ ] `pytest .claude/skills/_shared/test_spec_readiness.py` covers all
      seven R0 cases: heading absent → `False`; body blank → `False`;
      body exactly `(none)` → `False`; body single-line
      `(none — ready for breakdown)` → `False`; body the multi-line
      `(none — ...)` example spanning 3 lines → `False`; body with real
      unresolved prose → `True`; heading is the last line in the file
      (EOF) → `False`.
- [ ] `python3 .claude/skills/list-specs/list_specs.py` run against a
      fixture repo (tmp dir, no `specs/`) prints the no-specs message and
      exits 0.
- [ ] Fixture repo with `specs/archive/old-one/SPEC.md` and no other specs
      → output table has zero data rows.
- [ ] Fixture spec with no `tasks/` and a non-empty `## Open questions`
      section → row suggests `/critique`.
- [ ] Fixture spec with no `tasks/` and an empty/absent `## Open
      questions` section → row suggests `/breakdown`.
- [ ] Fixture spec with a `tasks/` dir present but containing zero `.md`
      files → row suggests `/breakdown` (same as no `tasks/` dir).
- [ ] Fixture spec with 2 pending, 1 done task → row suggests `/drain`.
- [ ] Fixture spec with exactly 1 pending task (e.g. `03-foo.md`) → row
      suggests `/build specs/<slug>/tasks/03-foo.md`.
- [ ] Fixture spec with a deferred task plus 2 other pending tasks → row
      suggests `/drain` (deferred takes precedence over a pending count
      that would otherwise also say `/drain`, and over what would
      otherwise say `/build`).
- [ ] Fixture spec with a blocked task plus 2 pending tasks → row flags
      `blocked/failed — needs attention` (rule 4 wins over the pending
      count that would otherwise say `/drain`), no command.
- [ ] Fixture spec with a deferred task plus a blocked task (no pending)
      → row suggests `/drain` (rule 3 — deferred — wins over rule 4 —
      blocked/failed).
- [ ] Fixture spec with all tasks `claimed`/`in-progress` (zero pending)
      → row flags `in-progress/awaiting`, no command (covers the
      mid-drain fall-through state).
- [ ] Fixture spec with all tasks done plus one draft → row flags `drafts
      ready for promotion`, no command.
- [ ] Fixture spec with all tasks done, no drafts → row suggests
      `/distill`.
- [ ] Fixture spec with one task whose `Status:` header is missing
      entirely → that task counts as `pending_like` (matches
      `scan_toolkit_specs`'s own default).
- [ ] Fixture spec with one task carrying an unrecognized status string
      (e.g. `Status: wat`) and no other tasks → row flags `unrecognized
      task status`, no command.
- [ ] Fixture spec with one `draft` task and one task carrying an
      unrecognized status (no pending/deferred/blocked/in-progress) → row
      flags `unrecognized task status`, NOT `drafts ready for promotion`
      (rule 10 wins over rule 8 per R4).
- [ ] Fixture spec with no `tasks/` dir and `## Open questions` body
      exactly `(none)` → row suggests `/breakdown`, not `/critique` (the
      R0 placeholder case).
- [ ] `pytest .claude/skills/list-specs/` passes, covering every branch
      above.
- [ ] End-to-end: running `/list-specs` in this repo (`/Users/sjaconette/claude`)
      produces a table covering its current active specs (excluding
      `archive/`) with no crash and no `archive/` rows present.

## Open questions

(none)

## Parallelization

All three tasks are strictly sequential: 01 → 02 → 03 (02 imports Task
01's module; 03 wraps Task 02's script and closes the spec's antigravity
mirror). No parallel-dispatchable groups within this spec.

Cross-spec caution (R0-note): Task 01 creates
`.claude/skills/_shared/spec_readiness.py`, which `specs/workboard-auto-triage`'s
own R0 may also create. That spec has no `tasks/` dir yet (not broken
down as of this writing). If it is later broken down and drained, its
file-creating task must carry a `Depends on` edge against this spec's
Task 01 (or explicit sequencing note) rather than being scheduled in the
same parallel wave — whichever spec's task lands second should import the
existing module and verify it against R0's test cases rather than
recreating it.
