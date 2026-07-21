# agentic: a tested CLI that runs the agent work pipeline

Breakdown-ready: false
Rigor: production

## The design in plain statements

What we are building:

1. One command-line program, `agentic` (Python), tested like any
   other production code.
2. Tasks, their dependencies, and their status live in beads (`bd`),
   a pinned third-party issue tracker. Agents and people use
   `agentic`; nothing else calls `bd`.
3. `agentic ready` lists tasks whose blockers are done and whose
   declared file paths do not overlap another claimed task.
4. `agentic claim <id>` marks one task in progress; claims are
   atomic.
5. Workers write one JSON result to a file that compose names.
   `agentic verdict` checks it against a schema, updates the task,
   and files discovered work as new tasks linked to their origin.
6. `agentic compose <id>` prints everything a worker run needs: the
   task, this repo's worker instructions (how to build, test, and
   report here), a code map of the files the task touches, the
   allowed tools, the model to use, the result schema, and the
   verdict file path. It refuses if the task text fails the
   injection screen or the run is out of budget.
7. The code-structure index is part of the same program:
   `agentic ctx tree|sig|refs|deps|map` answers structure questions,
   and compose's code map comes from it. One program to install,
   grant, inject from, and measure.
8. A short script is the work loop: ready → claim → compose → run
   worker → verdict → repeat.
9. `agentic resume` prints where things stand. There are no handoff
   files, batons, or lease files.
10. Spending has a cap enforced at dispatch: hitting the cap stops
    new work. Staying under it never needs a human approval.
11. Tracker state is exported to one JSONL file committed to git. A
    fresh clone runs `agentic init` and has everything.
12. Each agent runtime (Claude Code, Antigravity, Codex) gets a
    small folder of prompts that call `agentic`. Nothing is copied
    by hand between runtimes.
13. `agentic inbox` prints the one list a human needs: questions to
    answer, recent auto-promotions to undo, spending, priorities.
14. A scheduled job measures whether agents actually use these tools
    and files failures as tasks.

Why:

1. Today's work loop is English that a model re-reads every run, and
   models skip steps in it — every drain incident so far was a
   skipped prose step. Code does not skip steps.
2. Task state has no defined format: four scripts parse it with
   their own regexes, the rules are restated six times across three
   hand-copied directory trees, and the copies drift.
3. Resuming today needs five files because a prose loop loses its
   place. A code loop's position is a query.
4. Human approvals sit in front of cheap reversible actions (24
   ready drafts are parked on manual promotion), while the actual
   money leaks happened with every rule in place. A cap stops
   spending; an approval only stops work.
5. Any agent runtime with shell access must be able to run all of
   this. That is why the core is a CLI and not a feature of one
   runtime.

Boiling the previous draft down to these statements exposed soft
spots, each now resolved: who may write the tracker and when (D8 and
D9's sync rules), what the composer's "framing" concretely is (the
repo's worker instructions), what the inbox concretely is (a
command, not an app), and a claimed benefit nothing consumed
(memory compaction — cut).

## Design decisions

Each: the decision, why, what it costs.

- **D1 — Caps, not approvals.** Why: solo operator; approvals
  blocked the queue without preventing the measured leaks.
  Drafts that pass the critic are promoted immediately and listed in
  the inbox; `agentic demote <id>` reverts one. No timer-based veto
  window — nothing would run the timer. Cost: a mis-set cap can
  overspend before anyone looks; defaults are conservative and the
  inbox shows spend.
- **D2 — Procedure is code; prose is for judgment and context
  habits.** Why: 0% compliance with "prefer X" prose; skipped prose
  steps caused every drain incident. Cost: a bug in shared code hits
  every run — accepted because such bugs are testable and fixed
  once; the mechanical paths get unit and integration tests in CI,
  the same discipline that already covers `drain_frontier.py` and
  `admission.py`.
- **D3 — Use beads; do not build a tracker.** Why: it already does
  ready-work computation, atomic claims, and typed dependencies
  including discovered-from, and our own record maintaining this
  layer is worse than upstream's. "bd-lite" is dead, including as a
  named fallback; the insurance is the wrapper interface plus the
  JSONL in git. Cost: upstream churn (storage changed twice in five
  months), contained by version pinning (R-V).
- **D4 — Adoption is built in, never requested.** Context is
  injected, tools are granted, results are schema-checked; no
  "please prefer" prose. Why: ctx — a finished tool at near-zero use
  because every default said grep. Cost: the composer must exist
  before the prose habits it replaces can be deleted.
- **D5 — The CLI is the source of truth; runtime folders are thin.**
  Why: three hand-copied prose trees drift, and the checking gate
  admits it cannot catch the failure modes. Cost: the mirror chain,
  its gates, and CLAUDE.md's port-chain authoring conventions are
  deleted and rewritten; `.claude/` loses its special status.
- **D6 — One session, one task is the default.** The multi-worker
  loop is opt-in for genuinely parallel queues. Why: multi-agent
  work costs ~15× the tokens and most work is coupled.
- **D7 — Machine-read artifacts get schemas; the human gets the
  inbox.** Why: models read these files tens of times per human
  read.
- **D8 — Tracker writes are serialized by a lock, not by
  convention.** Every `agentic` write command takes a repo-level
  lock file first, so a human running `agentic verdict` by hand
  during a loop is safe, and two concurrent processes cannot lose an
  export. Workers never write: they return JSON, and `bd` resolves
  worktrees to the primary checkout's store anyway (verified,
  battery F12), so worker worktrees carry no tracker changes into
  their diffs. Cost: a stale-lock recovery path must exist.
- **D9 — Git is the only transport, with explicit sync rules.** A
  tracker write is: take the lock, `git pull`, import the JSONL if
  it changed, apply the operation to bd, export, commit, push. If
  the push is rejected, pull and re-apply. Operations are semantic
  (claim X, record verdict on Y), so re-applying after a sync either
  succeeds or fails cleanly ("already claimed"); the generated JSONL
  is never hand-merged — on conflict, take the remote version,
  import, re-apply, re-export. The loop batches one
  export-commit-push per iteration, about the same commit rate as
  today's prose drain (~3 per task). bd's own remote-sync feature
  (Dolt remotes, `bd dolt push`, `bd bootstrap`) is not used. Why:
  one transport, and it is the one every clone already has. Cost:
  tracker commits appear on the primary branch; two clones writing
  at once serialize on push order.
- **D10 — No pilot; we tested the real binary.** Same-day battery
  results below; anything they falsify amends these decisions.
  Write-race behavior gets its tests at loop integration (R-C), not
  day one.
- **D11 — Runtime-native features (Claude Code teams, the Workflow
  tool) are optional add-ons in adapters, never the core.** Why:
  they fail the any-runtime requirement.

## Component details

Only what the statements above don't already say.

**The composer** (`agentic compose`). The spend check needs a live
spend number on every runtime, so the signal is layered: harness
telemetry where the runtime exposes it, otherwise the composer's own
conservative estimate — it produces every prompt and receives every
verdict, so it meters ceil(bytes/4) per dispatch, over-counting by
design (R-M). Tool grants are enforced where the runtime has a
permission system; where it has none they degrade to prompt text and
are marked UNENFORCED in the output. What holds on every runtime is
what the composer itself controls: injection, schema checks, and
budget refusal. The scheduled audit tracks how often unenforced
grants are ignored.

**The loop.** Runs where the tracker lives (the primary checkout).
Deferred worker questions become tracker records shown by
`agentic inbox`.

**Verdict transport: a file, not stdout.** compose names a verdict
file path (and sets it as an environment variable where the runtime
allows); the worker's last step writes its JSON there; the loop runs
`agentic verdict <id> --file <path>`. A missing or schema-invalid
file marks the attempt failed and returns the task to ready with the
failure recorded. Chosen because agent runtimes mix logs into their
output, while a file works on every runtime with a filesystem and
stays inspectable after a failure — the same reason GitHub Actions
replaced stdout parsing (`set-output`) with the $GITHUB_OUTPUT file.

**ctx.** `agentic ctx …` fronts the existing ctx binary the same way
the tracker verbs front bd: one interface, engines underneath.
compose calls it for the code map; agents answer structure questions
through the same program they already hold a grant for. Whether the
Rust engine is later merged into the Python package is an
implementation choice, not a design question.

**Runtime adapters.** Per runtime: prompts that call `agentic`,
native hook wiring, an onboarding snippet. The mirror-procedure
manifest, parity gates, verification sweeps, and both mirror rules
files (mirror-procedure-discipline.md, mirror-verification.md) are
deleted with the prose they guarded.

**The inbox.** `agentic inbox` is a command over tracker state, not
a new app. The existing workboard can render the same data later.

**The audit job.** Scheduled, cheap-tier: reads transcripts and
tracker data; measures index-vs-grep ratio, model-tier violations,
verdict-schema conformance, spend vs caps; files findings as tasks
linked discovered-from.

## Requirements

- **R-G (hard):** every workflow runnable by any agent runtime with
  shell access; runtime-native features optional.
- **R-C:** no lost tracker writes under the concurrency we actually
  have: (a) two concurrent `agentic` write commands on one machine —
  serialized by the D8 lock; (b) two clones writing — serialized by
  D9 push order, loser re-applies or fails cleanly. Worker count
  (5–10) is unaffected because workers do not write.
- **R-L:** per-command tracker latency ceiling 1s. Measured on a
  ~15-issue store: ~0.3s reads, ~0.5s writes; Dolt latency grows
  with size, so acceptance re-measures at ≥500 issues.
- **R-B:** fresh-clone bootstrap is `git clone <url> && agentic
init` — ordinary git only, rebuilt from the committed JSONL.
- **R-E:** all tracker state recoverable from ordinary git alone,
  proven by a round-trip test in CI.
- **R-M:** the spend cap binds on every runtime — telemetry where
  present, the composer's estimate otherwise; a dispatch that cannot
  be metered is refused.
- **R-S:** injection screening at the compose boundary for all
  tracker-sourced text.
- **R-V:** bd is version-pinned; upgrades are deliberate,
  migration-tested events.

## Verified against the real bd (v1.1.0, 2026-07-21)

Live battery in this container, embedded backend. Details in
EVIDENCE.md.

- **Fields: use metadata, not labels.** Labels survive our exact
  strings but silently truncate at 255 chars, comma-split at create,
  and `--label-pattern` is broken. The `--metadata` JSON field
  stores typed structures, filters via `--metadata-field`, and
  round-trips losslessly — Touch/Rigor/Budget live there.
  `acceptance_criteria` is a native field.
- **Graph and ready-work: pass.** `discovered-from` is non-blocking;
  `parent-child` blocking propagates; `bd ready --json` is
  priority-sorted and filterable; `bd ready --claim` is the
  documented atomic claim (race untested — R-C).
- **Worktrees: pass.** `bd` resolves a git worktree to the primary
  checkout's store (F12) — the fact behind D8's "worker worktrees
  carry no tracker changes."
- **Latency: measured** (R-L numbers); `bd init` 3.5s once.
- **Export/import: lossless.** Labels, metadata, acceptance
  criteria, dependency types, closed status, preserved IDs; export →
  fresh init → import → re-export diffs to zero records.
- **Git: tracker state does not ride normal push/clone.** bd's own
  remote sync worked only against a co-located local Dolt remote;
  plain git origins host no Dolt server. Hence D9: committed JSONL
  is the only transport.
- **Ops facts `agentic init` must own:** `bd init` writes and
  auto-commits AGENTS.md/CLAUDE.md/settings files into the host repo
  (curate them); `.beads/interactions.jsonl` is tracked telemetry
  that dirties `git status` (gitignore it); the npm install is 137M.
  No background daemon; no stale locks observed.

## Migration

Ordered; each step leaves the system working. Steps 2–3 run in
shadow mode so nothing flips until step 4.

1. **Re-triage the open queue** against this design: every open
   spec/task marked keep / subsumed / fold-in. Known subsumed: the
   mirror machinery, the drain self-patch cluster,
   ctx-dispatch-adoption's prompt-stanza tasks.
2. **`agentic` v0, shadow mode**: ready/claim/verdict/resume over
   pinned bd; the D8 lock and D9 sync rules; `agentic init`; import
   the ~37 live items. Markdown headers remain the source of truth,
   synced one-way into bd; every existing reader keeps working.
3. **Composer v0**: result schema, verdict-file transport, grants,
   code-map injection via `agentic ctx`, screen, spend metering;
   /build switches to it. Mirror-manifest rows for files being
   replaced are marked retired from here on.
4. **Loop v0 and cutover**: bd becomes the source of truth; headers
   become generated; the markdown-header readers —
   `drain_frontier.py`, `list_specs.py`, `status.sh`,
   `prioritize_scan.py` — re-point into the wrapper or retire;
   baton, lease, and handoff artifacts deleted; evals assert loop
   behavior; the R-C write-race tests land here.
5. **Runtime adapters**: antigravity/ and codex/ become thin
   adapters; the mirror manifest, parity gates, sweeps, both mirror
   rules files, and CLAUDE.md's port-chain authoring conventions are
   deleted or rewritten in the same step.
6. **Caps and inbox**: launch-contract prose deleted, cap config
   added, `agentic inbox` and `agentic demote` land, drafts
   auto-promote on critic pass.
7. **Audit job v0**: scheduled measurement, findings filed as tasks.
8. **Rules shrinkage**: every rules line classified per D2 —
   mechanized, kept as judgment/context guidance, or deleted.

## Acceptance criteria

One runnable check per requirement; breakdown tasks derive theirs
from these. Anchors verified against current state: no `agentic`
entrypoint and no `tests/test_agentic_*` file exists today, so none
can pass vacuously.

- [ ] R-G: `tests/test_agentic_generic.sh` runs
      ready→claim→compose→verdict→resume end-to-end in a bare shell
      (no MCP, no runtime-native tools); exit 0.
- [ ] R-C: `tests/test_agentic_write_lock.sh` runs two concurrent
      `agentic verdict` commands; both recorded, no lost JSONL
      export. `tests/test_agentic_clone_race.sh` writes from two
      clones of one remote; both operations land (or the loser fails
      with a clean "already claimed"), and the final committed JSONL
      contains both. Land with step 4.
- [ ] R-L: `tests/test_agentic_latency.sh` seeds ≥500 issues; median
      `agentic ready` over 5 runs < 1s.
- [ ] R-B: `tests/test_agentic_bootstrap.sh` clones to a temp dir,
      runs `agentic init`, asserts `agentic ready` exits 0 with the
      imported issue count.
- [ ] R-E: `tests/test_agentic_roundtrip.sh` rebuilds the tracker
      from the committed JSONL alone; re-export diffs to zero
      records.
- [ ] R-M: unit test — with no harness telemetry, the estimate meter
      accumulates and `agentic compose` refuses past the cap.
- [ ] R-S: `tests/test_agentic_screen.sh` composes a task whose
      description embeds a screen-stub fixture injection string;
      compose refuses or neutralizes it, asserted on output.
- [ ] R-V: unit test — the wrapper refuses to run against any bd
      version but the pin, with an upgrade pointer.

## Risks

- **Upstream churn (beads).** Storage changed twice in five months.
  Contained by the pin (R-V), the wrapper, and the JSONL in git
  (R-E). Residual: a forced migration someday costs a bounded
  integration effort.
- **A composer bug hits every dispatch.** Accepted per D2; the
  composer path gets tests and evals first, not last.
- **`agentic` could suffer ctx's fate** (built, unused). The
  mitigation is structural: the composer is the only dispatch path,
  grants are composed in, and the audit job measures bypass from
  day one.
- **Cap errors.** A mis-set cap overspends; estimates drift from
  true cost. Conservative defaults, over-counting meters, spend in
  the inbox, hard refusal at cap.
- **Stale write lock.** The D8 lock needs timeout-and-takeover
  handling; specified at implementation, tested with R-C.

## Breakdown requirements

Binding on the breakdown stage, whenever it runs:

- **Coverage is proven, not assumed.** Every plain statement (1–14),
  every decision cost (D1–D11), and every migration step maps to at
  least one task, shown in a coverage table shipped with the
  breakdown. A statement with no task is a breakdown defect.
  Deletion work — mirrors, baton, lease and handoff files, retired
  readers, rules prose — gets tasks exactly like construction work.
- **The unglamorous work is enumerated explicitly:** packaging and
  install; the write lock and its stale-lock recovery; the
  shadow-mode markdown→bd sync; importing the ~37 live items;
  curating `bd init`'s side effects; grants derivation per runtime;
  the three adapter folders; eval updates; AGENTS.md and README
  updates; CI wiring for every new test.
- **Acceptance must require the behavior, not the artifact.** Each
  task's acceptance is a command whose pass requires the feature to
  work — a test that runs against the real binary — never "file
  exists", "line count under N", or a phrase-grep a worker can
  satisfy by pasting the phrase. Tests are shown failing before the
  implementation lands, and the verifier re-runs the commands itself
  rather than trusting the worker's transcript
  (docs/memory/anchored-acceptance-criteria.md).
- **No task verifies itself.** Criteria live in the task file, are
  runnable by a fresh session with no conversation context, and a
  worker editing its own acceptance criterion is a failed task.

Next stage: /breakdown specs/agentic-core-redesign/SPEC.md
(human-launched, after Breakdown-ready flips on review).
