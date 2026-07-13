# Task 01: Default orchestrator-level isolation for drain (R1)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: in-progress
Depends on: none
Priority: P0
Budget: 20 turns
Spec: ../SPEC.md (requirement R1)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

`/drain`'s own dispatch loop — not just each dispatched worker — defaults to
running the ORCHESTRATOR's own bookkeeping inside a VCS-level isolated
checkout/worktree of the target repo, rather than relying on lease-file
discipline alone. The default is ON (no opt-in step required); a documented
header opts a repo OUT, falling back to today's shared-checkout + lease-only
behavior. A VCS-neutral fallback is documented for a repo or hosting
environment that cannot provide isolated checkouts. This requirement is
drain-only — build/autopilot orchestrator isolation is explicitly out of
scope (see ../SPEC.md's Out of scope section).

## Touch

Edit `.claude/skills/drain/SKILL.md` (primary — where the orchestrator's own
dispatch/working-tree setup is described, near the top before step 1's
"Claim the owner lease") and `.claude/skills/drain/reference.md` only if the
fallback/opt-out mechanics need more detail than SKILL.md's line budget
allows (SKILL.md is already at 517 lines against a 500-line convention —
keep this addition to a pointer plus the required anchor phrase, with detail
pushed to reference.md where reasonable). Do NOT touch the Owner-lease
re-read section (R2, task 02), the preflight-sweep section (R3, task 03), or
the branch-deletion ordering (R4, task 04) — those are separate tasks' scope
even though they share these same two files. This task runs before 02–05 in
the queue; later tasks build on top of whatever you land here, so keep your
diff to R1 only.

## Steps

1. Read `../SPEC.md`'s R1 requirement and Problem-section incident #1 in
   full.
2. Confirm the "failing test": `grep -c "orchestrator's own working tree"
.claude/skills/drain/SKILL.md` currently returns 0.
3. Read `.claude/skills/drain/SKILL.md` end to end to locate (a) where the
   orchestrator's own dispatch/working-tree setup is currently described,
   and (b) the existing `isolation: worktree` hits for dispatched WORKERS
   (step 2/3/Tournament), so your new orchestrator-isolation text is clearly
   distinguished from worker-dispatch isolation and doesn't get confused
   with it.
4. Add text describing: default-ON VCS-level isolation of the
   orchestrator's own working tree (using the literal phrase "orchestrator's
   own working tree" so the acceptance grep matches), stated VCS-neutral
   first (e.g., under git: `git worktree add` for the orchestrator's own
   working directory), matching `.claude/rules/concurrent-sessions.md`'s
   existing phrasing pattern; the opt-out header mechanism (name a header,
   e.g. `Isolation: off`, that disables the default); and the fallback for a
   VCS/hosting environment that cannot provide isolated checkouts, stating
   literally that it "falls back to today's lease-only discipline"
   (advisory-only, matching multi-session-coordination's existing
   "Enforcement on interactive/ad-hoc sessions" carve-out) — this exact
   phrase is required, the acceptance grep below is not lenient to
   paraphrase.
5. Check `.claude/skills/drain/SKILL.md`'s line count (`wc -l`). Your net
   addition to SKILL.md (new lines minus any you trim in the same edit)
   must not exceed 8 lines — push anything beyond a short pointer plus the
   two required anchor phrases into reference.md instead. This keeps task
   05's closing line-budget trim (which must land SKILL.md genuinely below
   500 with headroom) achievable.
6. Run `bash evals/lint-ultra-gate.sh` and fix any drift (drain is an
   ultra-gated skill per CLAUDE.md's "Testing changes" section).
7. Confirm the "green test": re-run the grep from step 2 and check it now
   returns ≥ 1.

## Acceptance

- [ ] `grep -c "orchestrator's own working tree" .claude/skills/drain/SKILL.md` → ≥ 1
- [ ] `grep -ci "opt.out\|opts out" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md` → ≥ 1 (documents the opt-out mechanism; baseline at task start is 0)
- [ ] `grep -c "falls back to today's lease-only discipline" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md` → ≥ 1 (documents the fallback for a VCS/hosting environment without isolated-checkout support; baseline at task start is 0 in both files — this is a NEW anchor phrase, not the pre-existing generic "fallback" hits already in these files)
- [ ] Net new lines added to `.claude/skills/drain/SKILL.md` by this task's diff ≤ 8 (`git diff HEAD~1 -- .claude/skills/drain/SKILL.md | grep -c '^+'` minus `grep -c '^-'`, or eyeball the diff)
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
