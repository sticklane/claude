# Head-to-head evaluation: this repo's skills vs ultracode, on Claude Code CLI

Breakdown-ready: true
Rigor: prototype

## The question

On the same mid-sized coding tasks, same model, same container: which
configuration finishes more tasks correctly, and at what cost —
Claude Code CLI with **ultracode orchestration and none of our skills**,
or Claude Code CLI with **our skills toolkit and no ultracode**?

This is the first direct measurement of whether the toolkit earns its
keep against the platform's own multi-agent mode. Either answer is
useful: a loss on cost or correctness tells us which parts to keep.

Scope, stated up front so the finding cannot be over-read: arm S is
the toolkit's ALWAYS-ON tier — rules plus auto-triggering skills. The
launch-gated execution stages (/build, /drain, /prioritize) are out
of frame, because a headless brief is untrusted data that cannot
authorize a launch, and this eval does not weaken that design to win
a comparison. The finding therefore answers: does the toolkit's
ambient layer beat fully-activated ultracode? A second measurement
becomes possible once the agentic redesign's caps replace launch
gates (specs/agentic-core-redesign, decision D1, migration step 6):
arm S′ = plugin + `agentic loop` under the same spend cap, headless
by design. That follow-up is named here so this spec's result is
never mistaken for the full-toolkit verdict; it is not part of this
spec's runs.

## The design in plain statements

1. Two arms. **Arm U**: bare Claude Code CLI, no plugin, no custom
   skills or rules; each task brief carries the documented ultracode
   opt-in keyword. **Arm S**: this repo's `agentic` plugin installed
   (skills, agents, rules); ultracode never opted in; no other
   difference.
2. Everything else pinned and identical: model ID, effort, container
   image, network policy, repo snapshot per task (a git ref), the
   Claude Code CLI version, the agentic plugin commit (both recorded
   in the config dump), and the task brief text (identical except the
   arm-U opt-in keyword — each arm's mechanism is activated exactly
   the way its documentation says to activate it, and nothing else is
   added).
3. No arm-specific coaching. Arm S's brief does not name any skill;
   whether skills trigger is part of what is measured — a toolkit that
   only works when the human invokes it by name has an adoption
   problem, which is a finding, not noise.
4. The corpus is 3 purpose-built fixture tasks (multi-file, roughly
   30–90 minutes at human scale, each a small codebase with a green
   test suite, bundled in-repo so snapshots are exactly repeatable).
   Each task ships as: a fixture repo snapshot, a ≤6-sentence brief,
   and a **hidden acceptance script** (held out of both arms'
   filesystems) that runs the repo's tests plus task-specific checks.
   Hidden because a visible script invites teaching-to-the-test in
   both arms.
5. Each arm runs each task **3 times** — 18 headless sessions total.
   Variance across the 3 seeds is reported alongside the mean; a
   configuration that passes 3/3 cheaply but occasionally is worse
   than one that passes 2/3 predictably, and the numbers must show
   that.
6. Measured per run, recorded as one JSONL row: hidden-script
   pass/fail (primary); total cost in USD and tokens summed across
   the root session AND every spawned workflow/subagent session,
   computed identically for both arms (single-transcript accounting
   would undercount whichever arm spawns more); wall-clock; turn
   count; subagent/workflow spawn count; diff line count; and a
   single-call rubric-judge score (1–5, correctness-independent
   maintainability), with the judge blinded — its prompt contains the
   diff and the canonical keyword-stripped brief, never the arm or
   either arm's as-run brief text.
7. Verdict rule, pre-registered before any run so thresholds cannot
   be tuned after results exist. Per task: an arm wins only on a
   pass-count gap ≥2 of 3 (3/3 vs ≤1/3, or 2/3 vs 0/3). A gap of 1
   is "no distinguishable difference" on correctness — n=3 cannot
   separate it from seed noise — with costs reported descriptively.
   At a gap of 0 where both arms pass, median cost among passing
   runs decides only when the medians differ by ≥25%; inside that
   band the task is indistinguishable, and a gap of 0 where NEITHER
   arm passes is likewise indistinguishable — both failed. Aggregate: the report is the
   per-task verdicts plus each arm's total cost across all its runs;
   an overall winner is claimed only when one arm wins ≥2 tasks and
   loses none — any other pattern is reported as "mixed", and that
   word is the finding. No single blended scalar. The bands are
   acknowledged as judgment calls; their value is that they are
   fixed here, in advance.
8. The runner extends the existing evals machinery
   (`evals/headtohead/run.sh` + per-task `setup.sh`/hidden
   `assert.sh`), and is launched only via `/evals` — paid headless
   sessions stay human-launched.
9. The first full run's results land in this spec's `EVIDENCE.md` as
   the finding; the harness, not the finding, is what the tasks below
   build.

## The corpus (decided 2026-07-21)

Selection bar (unchanged): green test suite at the snapshot; work
spans ≥3 files; brief ≤6 sentences with no hidden requirements;
correctness checkable by tests, not prose; container-fit (no
privileged setup, no interactive auth, no network installs —
docs/memory/unattended-worker-tool-limits.md).

Decision: maintainer direction (2026-07-21 live session) chose
purpose-built fixture tasks over mining real repos — exactly
repeatable snapshots, no private-repo coupling, stdlib-only in both
languages so nothing is fetched at run time. The three deliberately
span the coupling spectrum so neither arm gets a corpus-shaped
advantage: T1 is tightly coupled (favors careful single-context
reasoning), T3 is breadth-first mechanical (the fan-out shape
multi-agent orchestration claims), T2 sits between.

**T1 — `ledger` (Python, coupled bug-fix).** A small expense-tracker
CLI (storage.py / report.py / cli.py + tests) whose monthly totals
drift by cents on some ledgers: amounts flow as binary floats across
all three modules, so the fix requires reasoning across boundaries,
not a print-time patch. Brief: "The monthly report in this expense
tracker drifts by a few cents on some ledgers. Find the cause and fix
it so every report total is exact to the cent for any input ledger.
All existing tests must stay green. Add regression coverage for the
failure you found. Do not change the CLI's output format." Hidden
checks: full suite; three held-out ledgers (including
float-pathological amounts) whose report totals must match exact
expected values; the shipped repro ledger now exact.

**T2 — `notes-api` (Python stdlib HTTP, additive feature).** A small
JSON notes service (router.py / handlers.py / store.py /
validation.py / API.md + tests) whose list endpoint returns
everything at once. Brief: "This notes service's GET /notes endpoint
returns every note at once, which is unusable for large stores. Add
limit/offset pagination and an optional tag filter as query
parameters, with input validation returning HTTP 400 in the API's
standard error shape for bad values. The response must include enough
metadata for a client to page through all notes. Update API.md to
document the new parameters. All existing tests must stay green; add
tests for the new behavior." Hidden checks: full suite; black-box
HTTP sequences against the running server — page math on a seeded
store, tag filter alone and combined, limit=0 / negative /
non-numeric → 400 in the standard shape, offset past the end → empty
page with metadata; API.md names both parameters.

**T3 — `sitegen` (Node, stdlib + node:test, breadth-first
refactor).** A small static-site generator whose date-formatting
logic is duplicated with drift across several modules (render.js,
feed.js, archive.js, meta.js), one copy wrong for certain dates.
Brief: "This static-site generator has date-formatting logic
duplicated across several modules, and the copies have drifted — at
least one renders certain dates wrong. Unify the duplicates into a
single shared module and migrate every call site to it. Rendered
output for the bundled sample site must stay identical, except where
the buggy copy produced wrong dates — those must now be correct. All
tests must stay green; add coverage pinning the corrected behavior."
Hidden checks: full suite; build the sample site and diff against a
golden output tree (correct dates baked in); exactly one
date-format definition remains across src/ (structural count); the
known-bad dates render correctly.

Fixture repos and hidden scripts live under
`evals/headtohead/tasks/<name>/` (repo snapshot + brief committed;
`assert.sh` stored outside the arms' mounts per the harness design).
Authoring them — with each fixture's suite green and each hidden
script failing against the unmodified snapshot and passing against a
COMMITTED reference solution per task — is harness build work for the
breakdown; the calibration acceptance criterion below is what proves
the instrument.

## Controls and honesty rules

- Arm isolation is verified, not assumed: the runner dumps each
  session's effective config, and the dry-run asserts arm U mounts no
  plugin/skills directory and arm S carries no ultracode opt-in.
- The hidden acceptance script never enters either arm's filesystem
  or prompt; it runs post-session against the produced worktree.
- One results schema, validated per row; a run that crashes or hits
  the session cap records as fail with its partial cost — dropped
  runs would silently flatter the crashier arm.
- Caps: per-session turn cap and USD cap, identical across arms,
  recorded in the config dump.
- The judge never sees cost, wall-clock, or arm; correctness comes
  only from the hidden script.

## Acceptance criteria

For building the harness (the corpus decision gates running it, not
building it):

- [ ] `bash evals/headtohead/run.sh --dry-run` → lists 18 planned
      sessions (2 arms × 3 tasks × 3 seeds) with full command lines,
      and exits 0 without launching anything
- [ ] `bash evals/headtohead/run.sh --dry-run --dump-config` → arm U's
      config shows no plugin/skills mount and contains the ultracode
      keyword in its brief; arm S's shows the plugin mount and no
      ultracode keyword; both arms pin identical CLI version and
      plugin commit; every hidden `assert.sh` path AND every committed
      reference-solution path resolves OUTSIDE both arms' mounts — the
      answer key is as hidden as the grader (all asserted by the
      script, printed as evidence)
- [ ] `bash evals/headtohead/run.sh --task fixture --arm S --seeds 1`
      → completes end-to-end against a bundled toy fixture task and
      emits a results row that validates against
      `evals/headtohead/result.schema.json`
- [ ] `bash evals/headtohead/run.sh --task fixture --arm U --seeds 1
      --dump-judge-input` → the ASSEMBLED judge input for the run (not
      the template) contains no word-boundary match for the ultracode
      keyword, arm names, or this plugin's name (asserted by the
      script)
- [ ] `bash evals/headtohead/calibrate.sh` → for each of T1/T2/T3
      prints `<task> RED OK` (hidden script fails against the
      untouched snapshot) and `<task> GREEN OK` (passes against the
      committed reference solution); exits 0 only when all six hold
- [ ] `bash evals/headtohead/run.sh --task crashfixture --arm U
      --seeds 1` → the bundled crash fixture (session dies mid-run /
      hits the cap) emits a schema-valid row with `pass: false` and
      non-null partial `usd`/`tokens` — crashed runs are recorded,
      never dropped
- [ ] fixture run's results row contains non-null `usd`, `tokens`,
      `turns`, `wall_s`, and its `tokens` EXCEEDS the root
      transcript's own total when the fixture's stub work spawns a
      child session (spawned work is summed, both arms' mechanisms)

Next stage: /critique specs/skills-vs-ultracode-eval/SPEC.md, then
/breakdown (human-launched) — the corpus Unblock is resolved above.

## Parallelization

Tasks 01→02→03 serialize: all three edit `run.sh`, and 02 needs 01's schema
and 03 needs a run 02 produces. Tasks 04/05/06 each own a disjoint
`tasks/<name>/` fixture directory and share no undecided design once 01 fixes
the out-of-mount path layout, so they are concurrent-safe; 03 is disjoint from
them too. Task 07 (calibration) depends on all three fixtures.

- Group: 03, 04, 05, 06
