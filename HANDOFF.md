# HANDOFF: /drain — whole-`specs/` queue (no-argument launch)

## Task

Continuing an unattended `/drain` run over the whole `specs/` queue (no
argument = whole-queue scope, per drain's exhaustion contract). This
session (gen 1, attended) hit the session-refresh wake budget
(273k-token p90 context, over the 250k threshold) after 5 recorded
verdicts and wrote a baton mid-run rather than continuing in a bloated
context. **A fresh session should just run `/drain` again** — it reads
the baton below and resumes automatically; this file exists only because
the session-refresh hook fires independently of drain's own baton
mechanism.

**Primary resume artifact:** `specs/codebase-context-tree/DRAIN-BATON.md`
(generation 2, `Run-token: 11896f4100a365e6`) — this is the authoritative
state, more detailed than this file. Read it first.

**Orchestrator isolation:** this run works from an isolated worktree at
`.claude/worktrees/drain-orchestrator` on branch `drain-orchestrator-run`
(default-ON orchestrator isolation), NOT the primary checkout at
`/Users/sjaconette/claude`. A fresh `/drain` invocation should re-establish
or reuse this isolated worktree per its own "Orchestrator isolation"
procedure — don't work directly in the primary checkout.

## State

**Fully drained this run (lease released, spec review recorded):**

- `specs/drain-worker-dispatch-hardening` — 5/5 tasks done, spec review
  skipped (docs-only), lease released.
- `specs/context-blowout-subagent-guards` — 1/1 task done, spec review
  skipped (docs-only), lease released.

**In progress, lease held:**

- `specs/codebase-context-tree` — was a draft spec (no `tasks/`),
  auto-broken-down (3b) into 14 tasks this run (commit `0aef7f3`, critic
  fixes in `30ab01f`). Task 01 (Rust crate scaffold, CLI, `ctx init`,
  Python extractor) is DONE (commit `2c47bf0`, all gates green). **13
  tasks remain (02-14).** Lease `Run-token: 11896f4100a365e6` still held
  — do not re-claim, just continue dispatching under it.

**Deferred to later (never reached — dispatchable work always took
priority, per 3b's "never preempt" rule):**

- 3b auto-breakdown: `specs/drain-hub-context-discipline` (P2),
  `specs/prompt-tweaking-roi` (P3) — both `Breakdown-ready: true`, no
  `tasks/` yet.
- Stub intake: 6 draft stubs — `narrow-autopilot/tasks/07`,
  `shared-viz-renderer/tasks/{05,06}`,
  `trajectory-evals/tasks/{05,06,07}`.

Next dispatchable task: `specs/codebase-context-tree/tasks/02-*.md` (P1,
dep 01 done). Re-read the current `Depends on:`/`Touch:`/`## Parallelization`
state fresh rather than trusting any prior summary — the Parallelization
section was rewritten mid-run during the critic-fix pass.

## Files touched (paths only, see baton for full detail)

- `specs/drain-worker-dispatch-hardening/tasks/{03,05}-*.md`,
  `evidence/spec-review.md` — landed.
- `specs/context-blowout-subagent-guards/tasks/01-*.md`,
  `.claude/rules/token-discipline.md`, `evidence/spec-review.md` — landed
  (two new bullets in token-discipline.md: browser-delegation subagent
  routing, deferred-tool-schema ToolSearch reminder).
- `specs/codebase-context-tree/` — `SPEC.md` (+Parallelization section),
  `tasks/01-14-*.md`, `DRAIN-BATON.md`.
- `context-tree/` — new Rust crate (task 01's output): `Cargo.toml`,
  `src/{main,lib,cli,facts,path,hash,extract,project}.rs`,
  `src/lang/{mod,python}.rs`, `tests/*.rs`,
  `tests/fixtures/languages/python/sample.py`, `scripts/check.sh`.

## Gotchas

- **Rust toolchain**: this machine had none before task 01. `rustup`
  stable 1.97.1 (minimal + rustfmt + clippy) is now installed at
  `~/.cargo`, but **not on every shell's default `$PATH`** — export
  `PATH="$HOME/.cargo/bin:$PATH"` before running
  `context-tree/scripts/check.sh` at merge time, every time.
- **Local `refs/heads/main` goes stale and can't be force-moved**: the
  primary checkout at `/Users/sjaconette/claude` has its own live,
  uncommitted/unpushed work (a human session working on an unrelated
  `workboard-kanban-view` spec) — `git branch -f main origin/main` fails
  because git refuses to move a checked-out branch with a dirty tree.
  **Always target `origin/main` directly** (fetch + reset --hard
  origin/main) when syncing worker dispatch worktrees — never local
  `main`, which several early dispatches this session cut from
  incorrectly (harmless so far since Touch paths never overlapped, but
  don't repeat it).
- **Primary checkout has unrelated concurrent human work** — before every
  push, `git fetch && git log origin/main` and check for new commits; if
  disjoint from `specs/codebase-context-tree/` and this run's other
  touched paths, `git rebase origin/main` and push again. This happened
  repeatedly this session with no real collision.
- A worker (context-blowout-subagent-guards task 01) delivered a fully
  evidenced DONE verdict but its own build procedure forgot to flip
  `Status: done` on its task file — drain corrected it directly before
  merging. Worth a glance if it recurs.

## Verification

Work landed this session was verified via drain's own mechanical merge
gates each time (not a separate post-hoc verifier pass, to conserve the
budget that triggered this handoff — each DONE verdict already ran an
independent verifier and/or full acceptance-command re-run before I
recorded it):

- `drain-worker-dispatch-hardening` tasks 03/05: `specs/status.sh`,
  `claude plugin validate .`, all `tests/test_*.sh`,
  `./bin/check-agent-model-pins`, `evals/lint-ultra-gate.sh` — all green,
  re-run by me at merge time (not just self-reported by the worker).
- `context-blowout-subagent-guards` task 01: same gate set, green;
  in-dispatch independent verifier also PASSed.
- `codebase-context-tree` task 01: same repo-wide gate set green, PLUS
  `context-tree/scripts/check.sh` (cargo fmt/clippy/test) independently
  re-run by me at merge time — green (11 tests passed). The worker's own
  dispatch also ran an independent verifier sub-pass.

Nothing landed this session is unverified. The 13 remaining
codebase-context-tree tasks are still `Status: pending` — no verification
owed on those.
