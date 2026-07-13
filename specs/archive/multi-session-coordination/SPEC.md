# Multi-session coordination: drains and builds that don't double-dispatch or clobber

## Problem

Nothing stops two Claude sessions from draining the same queue or
interleaving writes on the same checkout. The toolkit's single-writer
invariant is assumed, not enforced: two drains inventorying the same spec
both see `Status: pending` and both dispatch (TaskList is session-local,
so orchestrators cannot see each other's workers); two orchestrators — or
a drain plus an interactive session — interleave commits on one shared
checkout (documented corruption: docs/memory/concurrent-session-collision.md;
a concurrent session's `pull --rebase` once dropped unpushed drain commits
on fooszone). Detection primitives exist (`claude agents --json` +
`~/.claude/sessions/*.json` pid probes, used by workboard.py ≈600–625 and
agent-console.py ≈429–490) but no queue skill consults them.

## Solution

Three tiers, cheapest adequate mechanism each, all doctrine-compatible
(state in committed files; the harness stays dumb; no daemons, no
heartbeat processes). Skill-text changes to `.claude/skills/drain/`
(SKILL.md + reference.md), `.claude/skills/build/SKILL.md`,
`.claude/skills/autopilot/` (startup sweep + owner respect only), one new
rule file, the antigravity mirror, and a plugin bump.

- **Tier 1 — same-queue exclusion (correctness).** A committed per-spec
  owner lease `specs/<slug>/DRAIN-OWNER.md` claimed at drain start,
  released at terminal report. Liveness of an existing owner is judged
  from git evidence, never from a session registry: the newest of
  (a) commits touching `specs/<slug>/` and (b) the existing stale-lock
  activity signals for the spec's `in-progress` tasks (worktree mtimes,
  branch tips — drain/reference.md "Stale-lock liveness check"), against
  the same named grace window. Status flips become compare-and-swap:
  fresh read → exact-match edit of `Status: pending` (fails if another
  session flipped first) → path-scoped commit → post-commit verify.
- **Tier 2 — same-repo write hygiene.** Every orchestrator bookkeeping
  commit is path-scoped (explicit paths to `git add` and `git commit`,
  never `-a` or bare `git commit`) so a concurrent session's staged or
  working-tree changes cannot ride along; every bookkeeping commit is
  pushed immediately under the existing push guard (upstream configured →
  push, never force, failures warn-and-continue), extending the current
  push-on-DONE rule to all drain commits so a concurrent `pull --rebase`
  cannot drop them. Orchestrators never `git checkout` branches in the
  shared checkout (merges happen on the default branch; workers live in
  worktrees).
- **Tier 3 — startup detection (advisory).** Queue skills begin with a
  session sweep: list other live sessions whose cwd resolves into the
  repo (`claude agents --json`; fallback `~/.claude/sessions/*.json` +
  `kill -0` pid probe — the cwd-filtering pattern is
  `agent-console/agent-console.py` ≈429–490 `live_sessions_from_cli`,
  which reads each entry's `cwd`; workboard.py ≈600–625 supplies only
  the liveness set, not cwd), print one advisory line per foreign
  session. Detection is advisory; correctness comes from
  tiers 1–2. The docs/memory manual pre-flight for ad-hoc sessions is
  promoted to `.claude/rules/concurrent-sessions.md` (always-on in the
  toolkit repo), and /onboard's CLAUDE.md template gains one optional
  bullet pointing installing repos at the same pre-flight.

On conflict (live owner exists), the second drain REFUSES and reports:
owner evidence (file contents + freshest activity signal + age), other
dispatchable specs if any, and stops. A stale owner (all signals older
than the window) is reclaimed: the reclaiming drain follows the existing
confirmed-dead sweep (rescue branches, flips to pending), replaces
DRAIN-OWNER.md with its own claim, and commits the takeover as one commit.

**DRAIN-OWNER.md format (pinned):** single-line `Key: value` headers —
`Run-token:` (random hex, e.g. from `openssl rand -hex 8` — no session-id
dependence: a session cannot reliably know its own sid), `Host:`,
`Started:` (ISO 8601), `Generation:` (baton generation number, 1 for a
fresh run), `Spec:` (repo-relative spec dir). Baton passes (drain step 3a)
UPDATE `Generation:` in place — the owner-file update and the baton write
land in the SAME commit, so the two files can never disagree across a
crash — and the fresh-instance ritual (R1a) gains a step: reconcile
DRAIN-OWNER.md against the baton (matching `Run-token:` and
`Generation:`) before any dispatch. The owner file survives across
generations of the same run and is deleted (committed) by the generation
that completes the queue — the same one that deletes the baton.

## Requirements

- R1: drain claims ownership before any inventory-driven write: if
  `specs/<slug>/DRAIN-OWNER.md` is absent, write it (pinned format) and
  commit it as drain's first bookkeeping commit — and the claim is
  itself compare-and-swap: after committing, re-read the file at HEAD
  and confirm YOUR `Run-token` is the one present; a different token
  means you lost a simultaneous-start race — take the R2 path (treat
  the winner as the existing owner), never proceed as owner. The
  terminal report (queue empty / only blocked / interview handoff to
  human) deletes the owner file in a committed cleanup. drain/SKILL.md
  carries the claim step before step 1's dispatch plan and the release
  in step 4.
- R2: an existing DRAIN-OWNER.md whose liveness evidence is FRESH
  (any signal younger than the grace window) makes drain refuse: no
  queue writes, a report naming the owner file's headers, the freshest
  signal and its age, and any other specs with dispatchable tasks.
  EXCEPTION — baton lineage: a generation launched via the baton
  relaunch command adopts the existing owner iff the baton's
  `Run-token:` matches DRAIN-OWNER.md's (the baton grammar gains a
  `Run-token:` line; the token is the lineage proof a fresh process
  has — argv carries only the generation number). Token mismatch means
  the predecessor died and a foreign drain claimed: apply R2 on the
  evidence like any other startup. An existing owner with ALL signals
  stale is reclaimed: existing stale-lock sweep for each of the spec's
  in-progress tasks — with the foreign-reclaim tightening that a task
  is swept only when its activity signals are stale AND
  `git worktree list` shows no worktree checked out on its
  `task/NN-<slug>` branch — then owner replacement, all committed.
- R3: owner liveness is defined in drain/reference.md as: newest of
  (a) the committer timestamp of the last commit touching
  `specs/<slug>/`, (b) each in-progress task's stale-lock activity
  signals, compared to the grace window (same named 15-min default,
  same overridability). The definition explicitly states TaskList is
  session-local and MUST NOT be treated as evidence about other
  sessions' workers.
- R4: the pending→in-progress flip is specified as compare-and-swap:
  re-read the task file immediately before flipping; the flip edit
  matches the literal `Status: pending` line (an already-flipped file
  fails the edit and sends drain back to inventory); the commit is
  path-scoped to that task file; after committing, drain re-reads the
  file at HEAD and confirms its own flip is present before dispatching.
- R5: every queue-state commit drain makes (flips, Progress entries,
  Deferred questions, draft stubs, owner claim/release, evidence) is
  path-scoped: `git add <explicit paths>` + `git commit` limited to
  those paths; drain/SKILL.md states the rule once and forbids `-a`,
  bare `git add .`, and unscoped commits in the shared checkout.
- R6: the existing push guard extends to every drain bookkeeping
  commit, not only DONE merges: upstream configured → `git push`
  immediately after each commit (never `--force`; rejected/offline
  pushes warn and continue). The rationale line names the dropped-
  commit `pull --rebase` failure mode.
- R7: drain, build, and autopilot startup includes the session sweep:
  enumerate other live sessions with cwd inside the repo via
  `claude agents --json`, falling back to `~/.claude/sessions/*.json`
  pid records probed with `kill -0`; print one line per foreign live
  session (sid or pid, cwd, last activity). Sweep failure (CLI absent,
  no session files) prints one "sweep unavailable" line and continues —
  advisory only, never blocking. /build additionally warns (attended:
  may ask the user) before editing a spec whose DRAIN-OWNER.md is live.
- R8: `.claude/rules/concurrent-sessions.md` exists (≤40 lines): the
  pre-flight from docs/memory/concurrent-session-collision.md (check
  `claude agents --json` / recent foreign mtimes / `git worktree list`
  before multi-file edits in a shared checkout; on collision STOP and
  surface, never revert the other session's work). The docs/memory file
  gains a pointer to the rule instead of duplicating it. /onboard's
  template offers one optional bullet linking the pattern.
- R9: a model-free protocol test `tests/test_drain_owner_protocol.sh`
  exercises the git mechanics in a throwaway repo: (a) CAS — after a
  simulated foreign flip, an exact-match replacement of
  `Status: pending` fails (grep confirms single in-progress writer);
  (b) owner lifecycle — claim commit, generation update, release
  commit leave the expected file states; (c) path-scoped commit — a
  staged foreign file does not ride along with a path-scoped queue
  commit; (d) losing claim — two sequential claim commits with
  different Run-tokens, then the read-back at HEAD identifies exactly
  one winner and the loser's token is absent; (e) baton adoption — a
  fixture baton + owner pair with MATCHING Run-tokens passes the
  adoption predicate and a MISMATCHED pair fails it (the predicate is
  a documented one-liner comparing the two `Run-token:` lines, so the
  test exercises exactly what the skill text prescribes). Rides the
  existing `for t in tests/test_*.sh` gate.
- R10: antigravity mirror updated for every changed skill file in the
  same commit(s), and `.claude-plugin/plugin.json` version bumped once
  (CLAUDE.md authoring conventions; some task's Touch carries both).

## Out of scope

- Hook-enforced repo locks (PreToolUse blocking) — rejected: stale
  leases would lock a human out of their own repo.
- A central lock service (agent-console HTTP arbitration) — breaks
  files-are-the-checkpoint resumability.
- Worker-side heartbeats — already rejected by the drain spec; the
  residual false-sweep risk remains accepted, and its blast radius is
  knowingly LARGER here than single-drain (a foreign drain can sweep
  another session's live-but-silent worker, which then exits via the
  existing sweep-race BLOCKED path); the R2 worktree-list tightening
  and rescue branches bound the damage.
- Enforcement on interactive/ad-hoc sessions — the rule is advisory;
  humans stay unblocked.
- Automatic distribution of the rule to non-toolkit repos (beyond the
  one optional /onboard template bullet).
- Cross-HOST coordination (two machines on one remote) — the push
  guard's warn-and-continue already bounds the damage; a lease that
  works offline for multiple hosts does not exist in git.
- Group-throughput-mode changes: member workers already run in
  isolated worktrees; this spec touches orchestrator behavior only.

## Acceptance criteria

- [ ] `bash tests/test_drain_owner_protocol.sh` → exit 0 (covers R4, R5
      mechanics, R1 owner lifecycle grammar; R9)
- [ ] `grep -c "DRAIN-OWNER" .claude/skills/drain/SKILL.md` → ≥ 2 (claim
      + release) and `grep -c "DRAIN-OWNER" .claude/skills/drain/reference.md`
      → ≥ 1 (format + liveness rule) (R1–R3)
- [ ] `grep -n "compare-and-swap\|exact-match" .claude/skills/drain/SKILL.md`
      → ≥ 1 hit in the dispatch step (R4)
- [ ] `grep -n "path-scoped" .claude/skills/drain/SKILL.md | wc -l` → ≥ 1,
      and `grep -c "pull --rebase" .claude/skills/drain/SKILL.md` → ≥ 1
      (push-guard rationale names the dropped-commit failure mode; R5, R6)
- [ ] `grep -c "Run-token" .claude/skills/drain/reference.md` → ≥ 2 (owner
      format + baton grammar both carry it; R2 exception is testable)
- [ ] `grep -ln "claude agents --json" .claude/skills/drain/SKILL.md .claude/skills/build/SKILL.md .claude/skills/autopilot/SKILL.md | wc -l` → 3 (R7)
- [ ] `test -f .claude/rules/concurrent-sessions.md && wc -l < .claude/rules/concurrent-sessions.md` → ≤ 40; docs/memory/concurrent-session-collision.md contains a pointer to it (R8)
- [ ] `diff -r` (or the repo's mirror-conformance check) shows the
      changed skill files byte-mirrored under antigravity/, and
      `git diff <base>..HEAD -- .claude-plugin/plugin.json | grep -c version`
      → 2 (R10)
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0 (drain and build are
      ultra-gated skills; their edits must keep the gate lint green)
- [ ] Full gate suite green: `for t in tests/test_*.sh; do bash "$t"; done`,
      `./bin/check-agent-model-pins`, `./evals/runner-selftest.sh`,
      `./specs/status.sh`, `claude plugin validate .`
- [ ] MANUAL-PENDING (human-run; excluded from any unattended worker's
      gate — /drain is disable-model-invocation, so no worker can
      execute this; per docs/memory/unattended-worker-tool-limits.md):
      End-to-end in an attended terminal: stage a decoy claim — commit
      a DRAIN-OWNER.md with a fresh `Started:` and touch a file under a
      fixture spec's worktree — invoke /drain on that spec and observe
      it REFUSE with the owner evidence; then backdate the decoy's
      signals and observe reclaim; additionally exercise baton lineage
      once — a relaunch with MATCHING Run-token adopts and proceeds, a
      MISMATCHED token refuses on evidence; record all transcripts' key
      lines in `specs/multi-session-coordination/evidence/`

## Open questions

(none)

## Parallelization

- Group A (concurrent-safe): tasks 01, 02, 03, 04 — pairwise-disjoint
  Touch (`tests/` · drain's two files · build+autopilot SKILL.md ·
  rules/docs-memory/onboard), no dependency edges, and no shared
  undecided design: the owner-file grammar, baton `Run-token:` line,
  liveness definition, and sweep mechanism are all pinned in this
  spec's Solution/R1–R8, so tasks reference the same pinned contract
  rather than each inventing one (task 03 CITES drain's liveness text
  it doesn't own — a doc reference, not a compile dependency, safe
  even if 03 merges first).
- Task 05 (mirror + bump) serializes after 02, 03, 04 — it copies
  their final file states.
- The spec's MANUAL-PENDING e2e criterion is human-run after the queue
  completes; no task carries it.

## Closure (2026-07-13 verification sweep)

All task work verified correct at merge. 'pull --rebase' and 'claude agents
--json' strings moved from drain SKILL.md to reference.md by d51ce4b9.
Done-with-drift.
