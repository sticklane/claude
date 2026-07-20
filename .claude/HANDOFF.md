# Handoff: drain-orchestrator-run merge gap + pending breakdowns

## Task

User's live request this turn (not yet started, session ending per the
wake-budget hook — 0 re-primes, 256996 tokens, over the 250000 threshold —
refresh-over-carry, not a stopping point in the work itself):

> "fix that preexisting gap, breakdown anything that needs breakdown, then
> report back"

Three concrete pieces:

1. **Fix the preexisting gap**: `drain-multi-spec-swarm` task 01's actual
   implementation (the cross-spec admission model in
   `.claude/skills/drain/{SKILL.md,reference.md}`) is merged into the
   `drain-orchestrator-run` branch only — never merged back into `main`.
   Task 01's own `Status:` header on `main` still reads `pending` even
   though the work is done and verified (18/18 acceptance criteria, per an
   earlier session's independent `verifier` re-check). This blocks tasks
   03/06 of `drain-multi-spec-swarm` (both correctly `Depends on: 01`) from
   ever becoming dispatchable on `main` until this lands.
2. **Breakdown anything that needs breakdown**: two specs are
   `Breakdown-ready: true` with no `tasks/` directory yet —
   `specs/drain-hub-context-discipline` (P2) and
   `specs/prompt-tweaking-roi` (P3). Run `/breakdown` on each.
3. **Report back** once both are done.

## State

**This session's actual completed work (already committed, unrelated to
the fix/breakdown above — a separate prior request in this same
conversation)**: authored a round-10 revision to
`specs/drain-multi-spec-swarm/SPEC.md` (the "real concurrency test, no
attended run" the user asked to spec out) — R13-R17, extracting the
lease-claim CAS protocol + cross-spec cap into a live-invoked Python module
`admission.py`, a real-multiprocessing concurrency test (task 05, new),
live-execution rewiring (task 06, new), and amended task 03's mirror scope.
Two critique rounds, settled at **READY WITH NITS**. Commits:
`cab8f83` (spec content) and `25343ed` (folded in round-2 critique fixes
that were made after the first commit's `git add` — a genuine near-miss,
see Gotchas). Findings recorded in
`specs/drain-multi-spec-swarm/critique-findings.md` (round-10 section
prepended above the old round-3 section).

**The merge gap — investigated this session, NOT fixed:**

- `git merge-base main drain-orchestrator-run` → `95a7bd1` (the original
  4-task breakdown commit for `drain-multi-spec-swarm`, common ancestor).
- `main` has 36 commits `drain-orchestrator-run` lacks (including this
  session's two commits above, plus ~34 unrelated commits from other
  specs pulled during this session's earlier `git fetch && merge --ff-only`
  sync).
- `drain-orchestrator-run` has 12 commits `main` lacks — task 01's actual
  landed diff (`575f825` merge commit, `00c1557`, `a3232a2`, `ccc613a`) plus
  older `commit-message-doctrine` queue-exhaustion commits
  (`7bdbb51`..`5b6a9d7` etc.) that also never made it to `main`.
- **`git merge-tree <merge-base> main drain-orchestrator-run` shows ZERO
  actual conflict markers** — only two files "changed in both" that git's
  merge-tree resolves cleanly (`specs/commit-message-doctrine/tasks/02-*.md`
  and `specs/drain-multi-spec-swarm/tasks/01-*.md`, both spec-bookkeeping
  files, not code). This is a strong signal a straightforward merge would
  go clean, but was NOT attempted this session — treat this as "worth
  trying first," not "guaranteed."
- **Still genuinely unresolved** (flagged by an even earlier session too):
  nothing in `.claude/skills/drain/reference.md` states WHEN or HOW the
  `drain-orchestrator-run` branch is supposed to land on `main` — is it a
  PR, a direct merge, a periodic fast-forward? This needs either a fresh
  read of reference.md's "Orchestrator isolation" section for a missed
  answer, or a judgment call to make and then document (e.g. in
  reference.md itself, so this doesn't recur every time an orchestrator
  branch accumulates work).

**Recommended next-session approach for the fix:**

1. Re-read `.claude/skills/drain/reference.md`'s "Orchestrator isolation"
   section in full for any landing-mechanism guidance missed twice now.
2. If none found, the pragmatic move: merge `drain-orchestrator-run` into
   `main` directly (not the reverse — `main` has far more unrelated commits
   ahead; rebasing `drain-orchestrator-run` onto `main` first, THEN
   fast-forwarding or merging, is safer than merging `main`'s divergence
   into the orchestrator branch). Confirm the two "changed in both" files
   resolve as expected (not just "no conflict markers") before trusting the
   auto-merge.
3. After landing, flip `specs/drain-multi-spec-swarm/tasks/01-cross-spec-admission-model.md`'s
   `Status:` header to `done` on `main` (it's already `done` on
   `drain-orchestrator-run` — the flip needs to travel with the merge or be
   applied separately if the merge only carries code, not bookkeeping).
4. Document the landing mechanism in reference.md once decided, so this
   doesn't silently recur for future orchestrator-branch work.

**Breakdown work — not started:**

- `/breakdown specs/drain-hub-context-discipline/SPEC.md`
- `/breakdown specs/prompt-tweaking-roi/SPEC.md`
  Both are simple: run `/breakdown` on each, no known blockers. (Note:
  `/breakdown` is one of the three execution-stage skills requiring live user
  authorization per `.claude/rules/untrusted-data.md` — this handoff file
  itself does NOT authorize it; the user's own "breakdown anything that needs
  breakdown" in their live message to the resuming session IS the
  authorization, same as it was for this session.)

## Files touched this session

- `specs/drain-multi-spec-swarm/SPEC.md`, `critique-findings.md`,
  `tasks/03-mirror-and-version-bump.md` (amended),
  `tasks/04-admission-module.md` (renamed from
  `04-swarm-admission-simulation.md`, rewritten), `tasks/05-*.md` (new),
  `tasks/06-*.md` (new) — all committed (`cab8f83`, `25343ed`).
- `docs/TASKS.md` — added a tech-debt entry for
  `touch_disjoint.py`/`drain_frontier.py` predicate convergence.
- No files touched yet for the merge-gap fix or the two breakdowns — pure
  investigation only.

## Gotchas

- **This repo's edit hooks reformat files after Write/Edit** — a
  PostToolUse hook silently modified files after several edits this
  session. This caused a real near-miss: task 04's round-2 critique fixes
  were applied to the working tree AFTER `git add` had already staged an
  earlier version, so the first commit (`cab8f83`) shipped the stale
  pre-fix content. Caught by re-diffing the committed file against the
  working tree after commit — always do this check before considering a
  commit-after-heavy-editing session done.
- **Primary checkout (`/Users/sjaconette/claude`) still has unrelated,
  uncommitted human WIP**: modified `AGENTS.md`/`README.md`, deleted
  root `HANDOFF.md`, untracked `docs/architecture.md`,
  `docs/task-tracking-design-research-2026-07.md`, and
  `.claude/HANDOFF.md.stale-pathspec-commit-hardening`. Confirmed
  pre-existing across three sessions now — do NOT touch, commit, stage, or
  push over any of these.
- `main` was fast-forwarded from `origin/main` earlier this session (34
  commits, all unrelated spec/task files from other sessions' work) — this
  is why `main`'s divergence from `drain-orchestrator-run` looks large; most
  of it (36 commits) is unrelated churn, not a real design conflict.
- Task 01's `Status: pending` on `main` is NOT a bug in this session's
  work — it accurately reflects that the branch holding the actual
  implementation hasn't merged. Don't "fix" it by just editing the header
  without also landing the actual code.

## Verification

- `drain-multi-spec-swarm`'s round-10 spec content: 2 critique rounds,
  settled READY WITH NITS, findings recorded in
  `specs/drain-multi-spec-swarm/critique-findings.md`. Not independently
  re-verified beyond the critic's own re-check — this is spec authoring,
  no code to verifier-check yet.
- Merge-gap fix: NOT started, NOT verified.
- Breakdowns: NOT started, NOT verified.

Next stage: resume this exact task — fix the drain-orchestrator-run →
main merge gap (see recommended approach above), then run `/breakdown` on
`specs/drain-hub-context-discipline/SPEC.md` and
`specs/prompt-tweaking-roi/SPEC.md`, then report back to the user, per
their live request that opened this handoff.
