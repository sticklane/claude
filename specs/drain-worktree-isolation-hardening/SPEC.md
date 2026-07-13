# Drain worktree isolation hardening: default isolation, mid-run owner re-checks, preflight sweep, cleanup ordering

Status: open
Priority: P1

## Problem

`specs/multi-session-coordination` shipped (all 6 tasks `Status: done`) the
owner-lease protocol — `DRAIN-OWNER.md`, compare-and-swap claim, stale-lock
reclaim, path-scoped/pushed commits, and a startup session sweep. A later
2026-07-08/09 incident (`specs/drain-remote-divergence-check`, also shipped)
closed the specific gap where a rejected push was the only concurrency
signal, by adding a pre-lease-claim fetch/compare/halt check. Both are done
and working as designed.

A fresh cross-session research sweep of real drain/build usage since then
surfaced four failure shapes that neither shipped spec covers:

1. **Two concurrent drain sessions left a shared tree on a wrongly-named
   branch carrying 5 stranded commits from the other session**, forcing an
   interrupt and manual rescue-branch surgery (merge-conflict resolution,
   renumbering) — a collision in drain's OWN checkout, not a worker's. A
   parallel drain migrated a shared DB mid-investigation in another repo,
   losing a round of spec drafting. The owner-lease protocol makes a second
   drain REFUSE once it reads a fresh `DRAIN-OWNER.md` — but nothing stops
   the orchestrator itself from operating in a shared, non-isolated checkout
   in the window before that read, or from two sessions racing to become
   the first writer. Worker dispatch already runs `isolation: worktree`
   (drain/SKILL.md step 2); the orchestrator's own working tree does not.

2. **A lease reclaim fired on stale liveness signals while the real owner
   was still alive**, immediately followed by a push from the real owner,
   forcing a full revert — happened twice in near-duplicate sessions. A
   near-miss reclaim was caused by an uncommitted flip appearing uncommitted
   between two reads. Drain lost an owner-lease race entirely, self-
   diagnosed as having "skipped the CAS re-read of the owner file at HEAD
   immediately before dispatch." The shipped protocol's CAS re-read
   (multi-session-coordination R1) covers the INITIAL claim only — nothing
   re-confirms the session is still the fresh owner immediately before each
   SUBSEQUENT status-flip commit later in the same spec's dispatch/collect
   cycle, where a stale-vs-hung liveness heuristic can still race a real,
   still-alive owner.

3. **Three separate sessions in one repo independently rediscovered dead
   leases and orphaned worktrees from prior crashed generations** — one
   needed a ~105-branch audit of accumulated worktree debris, with one
   specific zombie worktree re-flagged by two different drain generations
   without ever being resolved. Another session opened with the user
   literally saying "kill any zombie drains" — six dead lease files across
   unrelated specs, an orphaned worktree, and a stale lock file had all
   accumulated from prior crashed/detached generations; this ritual
   recurred in the large majority of drain-invoking sessions sampled. The
   shipped protocol only reclaims a lease REACTIVELY, at the moment a drain
   run tries to claim that SPECIFIC spec (SKILL.md step 1, "Claim the owner
   lease"); nothing sweeps every spec's dead lease and every orphaned
   worktree/checkout mechanically at drain start, so each session re-
   narrates the same manual cleanup ritual.

4. **A branch-deletion-before-worktree-removal ordering bug** — attempting
   to delete a branch while it is still checked out in a worktree fails
   ("branch is used by worktree" or equivalent) — hit in the same shape in
   two separate sessions, each self-correcting by reversing the order.
   drain/reference.md's Tournament section already gets this order right
   for the winner's non-surviving branches (`rescue/…` renaming: "force-
   remove each worktree FIRST — a checked-out branch cannot be renamed away
   safely — then rename," line ~279) but states the SURVIVOR-branch cleanup
   without pinning an order: "Delete survivor branches and worktrees only
   after some merge passes gates" (Tournament, "Merge") names no sequence,
   and the DONE-merge path's "delete this task's `rescue/NN-<slug>-*`
   branches" (SKILL.md step 3) is silent on it too.

A fifth gap from the same sweep — the remote-push-divergence collision
shape (two generations both merging to a shared remote before either
notices, a push rejected with dozens of divergent commits from a sibling
that already redid the same work) — is a near-exact match for the
2026-07-08/09 incident that `specs/drain-remote-divergence-check` was
built from and closed (its Problem section cites the same ~90-commit
rejected-push shape). That gap is NOT included below; it is already
shipped.

## Solution

`specs/multi-session-coordination` has all six of its tasks `Status: done`
— its tasks/ directory is a completed breakdown, not an in-progress one —
so this is a new, complementary spec rather than an edit to that closed
spec. It builds directly on the shipped owner-lease mechanism (DRAIN-OWNER.md,
CAS claim, Stale-lock liveness check, rescue-branch procedure — all in
`.claude/skills/drain/reference.md`'s "Owner lease" and "Status field
semantics" sections) rather than replacing any of it. Four requirements,
one per uncovered gap:

- **Default the ORCHESTRATOR's own working tree to VCS-level isolation**
  for drain (and, where the same shared-checkout risk applies, build/
  autopilot), not merely lease-file discipline — a structural fix
  layered on top of, not instead of, the existing lease protocol.
- **Re-read the owner-lease file at HEAD immediately before every
  status-flip commit**, not only at the initial claim — extending the
  existing claim-time CAS re-read (multi-session-coordination R1) to
  every subsequent flip within the same claimed dispatch/collect cycle.
- **A mechanical preflight sweep at drain start** that reclaims every
  dead lease and prunes every orphaned worktree/checkout across the
  WHOLE scope being drained (not just the one spec about to be claimed),
  replacing the manual "kill any zombie drains" ritual with a scripted
  pass.
- **Pin worktree-removal-before-branch-deletion ordering** unconditionally
  in every drain cleanup step that deletes a branch, mirroring the
  ordering the rescue-rename path already gets right.

Scope: `.claude/skills/drain/SKILL.md`, `.claude/skills/drain/reference.md`,
and (per this repo's mirror obligations, CLAUDE.md "Authoring conventions")
`antigravity/.agents/workflows/drain.md` + `antigravity/.agents/skills/drain/`
+ `codex/.agents/skills/drain/SKILL.md` (drain is one of the four explicit-
invocation skills codex mirrors as real content, not a symlink) + a
`.claude-plugin/plugin.json` version bump. Whoever breaks this spec down
must carry the antigravity mirror, the codex mirror, and the plugin bump in
the `Touch:` of whichever task(s) change the drain skill files — CLAUDE.md's
existing rule that an unlisted mirror silently ships un-mirrored applies
here unchanged; this SPEC.md states the obligation, it does not assign it
to a specific task.

## Research grounding

> "two independent drain sessions worked `/Users/sjaconette/claude`
> concurrently... By the time the direct-push session's `git push` was
> finally rejected, ~90 commits had landed on `origin/main`, including
> independent, duplicate implementations of the same two tasks" —
> `specs/drain-remote-divergence-check/SPEC.md` (the shipped spec that
> already closes the remote-divergence gap; cited here only to show it is
> NOT re-covered below).

> "force-remove each worktree FIRST — a checked-out branch cannot be
> renamed away safely — then rename." — `.claude/skills/drain/reference.md`
> (Status field semantics, the rescue-branch procedure), showing the
> correct ordering already exists for one cleanup path but is not stated
> as a general rule.

> "Delete survivor branches and worktrees only after some merge passes
> gates." — `.claude/skills/drain/reference.md` (Tournament, "Merge"),
> showing the survivor-cleanup path names no ordering.

## Requirements

- **R1 — Default orchestrator-level isolation.** Drain's own dispatch
  loop (and build/autopilot where the same shared-checkout risk applies)
  defaults to running the ORCHESTRATOR's bookkeeping — not just each
  worker — inside a VCS-level isolated checkout/worktree of the target
  repo, rather than relying on lease-file discipline alone to keep two
  concurrent drain sessions from interleaving commits in one shared
  tree. State this in VCS-neutral terms first (e.g., under git: `git
  worktree add` for the orchestrator's own working directory, analogous
  to how `isolation: worktree` already isolates each dispatched worker),
  matching the existing pattern in `.claude/rules/concurrent-sessions.md`
  ("the VCS's checkouts/worktrees... e.g., under git: `git worktree
  list`"). Document the fallback for a repo whose VCS or hosting
  environment cannot provide isolated checkouts (falls back to today's
  lease-only discipline, advisory-only, per the existing rule's
  "Enforcement on interactive/ad-hoc sessions" carve-out in
  multi-session-coordination's Out of scope).
- **R2 — Owner-lease re-read before every status-flip commit.** Extend
  the existing claim-time CAS re-read (multi-session-coordination R1,
  "after committing, re-read the file at HEAD and confirm YOUR
  `Run-token` is the one present") so the SAME re-read-and-confirm check
  runs immediately before EVERY subsequent status-flip commit within
  the claimed spec's dispatch/collect cycle — not only at the initial
  claim. A mismatched `Run-token:` at any of these re-reads means the
  session has lost ownership mid-cycle (a crossed-yield race, a
  liveness-based reclaim by another session) and the flip is aborted,
  never committed, with drain treating the spec as lost per the existing
  R2 refuse path (multi-session-coordination). Document in
  `.claude/skills/drain/reference.md`'s "Owner lease" section, cited by
  a pointer from SKILL.md step 2's existing "flip is compare-and-swap"
  paragraph.
- **R3 — Mechanical preflight sweep.** At drain startup (gen-1, before
  step 1's spec-scoped work begins), run one mechanical pass that: (a)
  identifies every `DRAIN-OWNER.md` under the drained scope whose owner
  liveness (the existing definition: newest of the last commit touching
  that spec's `specs/<slug>/` path, or its in-progress tasks' stale-lock
  signals) is ALL STALE, and reclaims each exactly as the existing
  per-spec reclaim does (foreign-reclaim tightening: stale signals AND
  no worktree/checkout on the task's branch); (b) enumerates every
  checkout/worktree of the repo the VCS reports (state this in VCS-
  neutral terms first — "the VCS's checkouts/worktrees," e.g., under
  git: `git worktree list` — matching `.claude/rules/concurrent-
  sessions.md`'s existing pattern) and prunes any with no corresponding
  live `in-progress` task or live session. This sweep is scoped to
  EVERY spec in the drain run's launched scope (a no-argument launch
  means the whole `specs/` queue, per the existing exhaustion contract),
  not only the one spec about to be claimed — the mechanical replacement
  for the manual "kill any zombie drains" ritual. Report a one-line
  summary (leases reclaimed, worktrees pruned) in the gen-1 startup
  advisories alongside the existing session-sweep/hub-economics
  advisories (SKILL.md, "Gen-1 startup advisories" — best-effort, never
  blocking).
- **R4 — Worktree-removal-before-branch-deletion ordering, pinned
  unconditionally.** Every drain cleanup step that deletes a branch
  (survivor-branch cleanup after a tournament merge, `rescue/NN-<slug>-*`
  branch deletion after a DONE merge, or any other branch-deletion path)
  states the VCS-neutral rule first — remove the checkout/worktree
  before deleting the branch it was checked out on, since deleting a
  branch still checked out in a worktree/checkout fails under the same
  VCS mechanism `git worktree list`/`git branch -d` already illustrates
  elsewhere in this repo's rules — then gives the git-specific command
  sequence as an "e.g." illustration only, mirroring
  `.claude/rules/concurrent-sessions.md`'s existing phrasing pattern.
  Apply this ordering to the Tournament "Merge" step's survivor cleanup
  and to SKILL.md step 3's DONE-merge rescue-branch deletion, both
  currently silent on ordering.
- **R5 — Mirror obligations.** Every changed `.claude/skills/drain/`
  file's antigravity mirror (`antigravity/.agents/workflows/drain.md`,
  `antigravity/.agents/skills/drain/`) is updated in the same commit, in
  that mirror's own paraphrased voice (prose-skill mirrors are
  paraphrased ports, not byte-identical, per
  `docs/memory/workboard-mirror-verbatim.md`), and — because drain is
  one of the four explicit-invocation skills codex mirrors as real
  content — `codex/.agents/skills/drain/SKILL.md` carries the matching
  update too. `.claude-plugin/plugin.json`'s version is bumped once
  (current: 0.8.63; this spec adds new capability — R1's default
  isolation, R3's preflight sweep — so a minor bump is appropriate per
  CLAUDE.md's semver convention, not a patch).

## Out of scope

- The remote-push-divergence collision shape (two generations merging to
  a shared remote before either notices) — already closed by the shipped
  `specs/drain-remote-divergence-check`. No requirement here duplicates
  it.
- Re-litigating the owner-lease claim/CAS/reclaim mechanism itself
  (`DRAIN-OWNER.md` format, `Run-token:`, baton-lineage adoption) —
  shipped by `specs/multi-session-coordination`; R2 above extends its
  re-read discipline to later commits, it does not redesign the format.
- Cross-HOST coordination (two machines on one remote) — carried over
  from multi-session-coordination's Out of scope; unchanged here.
- A central lock service or hook-enforced repo locks — rejected for the
  same reason multi-session-coordination rejected them (stale leases
  would lock a human out of their own repo; breaks files-are-the-
  checkpoint resumability).
- Group-throughput / rolling-window scheduling changes — member workers
  already run `isolation: worktree` (drain/SKILL.md step 2); this spec's
  R1 is about the ORCHESTRATOR's own tree, not worker dispatch, which is
  unchanged.
- Enforcement on interactive/ad-hoc sessions — R1's default isolation
  and R3's sweep are drain/build/autopilot behaviors; a human's own
  ad-hoc session stays advisory-only per `.claude/rules/concurrent-
  sessions.md`, unchanged.

## Acceptance criteria

- [ ] `grep -c "re-read.*DRAIN-OWNER\|DRAIN-OWNER.*re-read" .claude/skills/drain/reference.md`
      currently → 0 (confirmed at authoring time: the only existing
      claim-time re-read language is SKILL.md:83's "CAS re-read
      confirming YOUR `Run-token:` at HEAD," which names the initial
      claim, not `DRAIN-OWNER.md` by name, and reference.md has no
      DRAIN-OWNER-specific re-read text at all); after this spec's
      implementation, `grep -n "before every.*status-flip\|before every
      subsequent.*commit" .claude/skills/drain/reference.md` → ≥ 1 hit
      in the "Owner lease" section (R2)
- [ ] `grep -n "isolation.*worktree\|VCS.*checkout" .claude/skills/drain/SKILL.md`
      shows a hit describing the ORCHESTRATOR's own working tree
      (distinct from the existing worker-dispatch `isolation: worktree`
      hits at SKILL.md's step 2/3/Tournament, all of which name a
      dispatched agent, never the orchestrator itself — confirmed absent
      at authoring time by inspection of every current `isolation:
      worktree` occurrence) (R1)
- [ ] `grep -n "preflight\|mechanical.*sweep" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md`
      shows a hit describing a scope-wide (every spec, not one) dead-
      lease-and-orphaned-worktree sweep at drain startup — confirmed
      absent at authoring time (the only existing "preflight"-adjacent
      hits are the reactive per-spec reclaim in "Owner lease" and the
      unrelated "repo-wide status" Touch-enforcement phrase, neither of
      which sweeps every spec at startup) (R3)
- [ ] `grep -n "worktree" .claude/skills/drain/reference.md` in the
      Tournament "Merge" step and SKILL.md step 3's rescue-branch
      deletion both show worktree removal stated to precede branch
      deletion — currently neither location states an order (confirmed
      absent at authoring time: "Delete survivor branches and worktrees
      only after some merge passes gates" names no sequence) (R4)
- [ ] `diff` (or this repo's mirror-conformance check) shows
      `antigravity/.agents/workflows/drain.md`,
      `antigravity/.agents/skills/drain/`, and
      `codex/.agents/skills/drain/SKILL.md` updated in step with every
      changed `.claude/skills/drain/` file (R5)
- [ ] `git diff <base>..HEAD -- .claude-plugin/plugin.json | grep -c version`
      → 1, and the new version is a minor bump over 0.8.63 (R5)
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0 (drain is an ultra-gated
      skill; its edits must keep the gate lint green)
- [ ] `wc -l < .claude/skills/drain/SKILL.md` stays genuinely below the
      repo's 500-line convention with headroom (currently 517 lines —
      already over; any task touching SKILL.md under this spec pairs its
      addition with a compensating trim, per the same discipline
      `specs/drain-remote-divergence-check` R6 already applied)
- [ ] Full gate suite green: `for t in tests/test_*.sh; do bash "$t"; done`,
      `./bin/check-agent-model-pins`, `./evals/runner-selftest.sh`,
      `./specs/status.sh`, `claude plugin validate .`
- [ ] MANUAL-PENDING (human-run; /drain is disable-model-invocation, so
      no unattended worker can execute this; per
      `docs/memory/unattended-worker-tool-limits.md`): in an attended
      terminal, stage two decoy `DRAIN-OWNER.md` leases (one FRESH, one
      backdated stale) plus one orphaned worktree with no corresponding
      task, invoke `/drain` with no argument, and observe the preflight
      sweep (R3) reclaim the stale lease and prune the orphaned worktree
      while leaving the fresh one alone; separately, force a branch-
      still-checked-out-in-a-worktree deletion attempt on a survivor
      branch and confirm the ordering fix (R4) removes the worktree
      first without erroring; record transcripts in
      `specs/drain-worktree-isolation-hardening/evidence/`

## Open questions

- R1's orchestrator-isolation default changes where drain's own
  bookkeeping commits land relative to today's shared-checkout model —
  whoever breaks this down should confirm with a human whether R1
  should be opt-out (default ON, a header disables it) or opt-in
  (default OFF, a header enables it) before authoring task 01; the
  evidence favors default-ON (every collision incident happened under
  today's default-OFF shared-checkout model) but this spec does not
  pin that choice.
- Whether R3's preflight sweep should also run at build/autopilot
  startup (not just drain) is unresolved; the research evidence for R3
  is drain-specific (all "zombie drain" narration was inside drain
  sessions), so this spec scopes R3 to drain only — a human or the
  breakdown author should confirm this is the right boundary before
  widening it.
