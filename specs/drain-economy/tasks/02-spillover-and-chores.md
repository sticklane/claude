# Task 02: mechanical unblocks, loud spillover, and the chores lane

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 00, 01
Priority: P1
Budget: 35 turns
Spec: ../SPEC.md (requirements EP18, EP19, decisions D8, D9, D10, D11)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, tests/test_drain_spillover.sh, tests/inventory/drain-economy-02.json, evals/drain/04-spillover/setup.sh, evals/drain/04-spillover/prompt.txt, evals/drain/04-spillover/assert.sh, evals/drain/04-spillover/allowed-tools.txt, evals/drain/04-spillover/skill-deps.txt, evals/drain/04-spillover/timeout-seconds.txt

## Goal

A fully blocked focus no longer stalls the run and no longer goes quiet.
Drain first attempts mechanical unblocks — `Unblock: run:` commands executed
only when they pass the same command policy that gates acceptance commands (a
rejected command demotes to `ask:`), `Unblock: agent:` prompts dispatched as
scoped one-attempt workers, `ask:` items queued for the batch interview — then
re-reads the frontier. Still dead, it announces the spillover, records the
event, and advances down NOW.md, returning to the focus at the next dispatch
that finds it ready. Separately, `chore`-labeled beads fill idle capacity
under a bounded slot count without becoming a second focus.

## Touch

The selector and NOW.md parsing are task 01's and already landed; this task
adds the blocked-frontier branch and the chores lane to the same loop. It must
NOT touch the filing/triage economy (task 03) or the completion ceremony
(task 12).

Two boundaries matter here because both were live ambiguities before this
revision:

- **The command policy is task 00's, whole.** This task calls
  `bin/command-policy` and acts on its verdict; it never decides what makes a
  command acceptable and never adds a second check of its own. A policy gap
  found here is filed as blocking work against task 00.
- **The spillover-event record is task 04's.** Task 04 defines the run bead,
  and it lands after this one, so this task writes the *narration* line and the
  branch logic only. It must not invent a recording surface, and must not
  write "record the event" as an unresolved instruction — task 04 adds the
  record where the bead exists.

## Steps

1. Write the failing test first: `tests/test_drain_spillover.sh` over
   `mktemp -d` fixtures, asserting the parts a script can own — the
   `Unblock:` line parse (`run:` / `agent:` / `ask:`), and the demotion
   *wiring*: a `run:` whose `bin/command-policy` verdict is reject becomes an
   `ask:` carrying the policy's reason code, and the command never reaches
   execution (assert by observation: the fixture's sentinel file is absent
   afterward, the same technique `tests/test_human_blockers.sh` uses). The
   policy's own accept/reject cases belong to task 00's suite, not this one —
   assert that the verdict is *honored*, not that it is correct.
2. Add the blocked-frontier branch to `.claude/skills/drain/SKILL.md`: the
   ordered attempt sequence, the re-read, the narration line
   `focus <slug> blocked (ask: <n> items) → spilling to <next>`, and the walk
   down NOW.md ending at the batch interview when the list is exhausted.
3. State D9's re-focus rule where the dispatch decision lives: every *new*
   dispatch re-evaluates from the top of NOW.md; in-flight tasks are never
   preempted; a transiently mixed window is expected.
4. Add the chores lane: `chore`-labeled beads dispatch only when the
   focus/spillover frontier underfills the window, at most `CHORE_SLOTS`
   (default 1) concurrent, excluded from feature accounting, never a spillover
   trigger, never a completion blocker. Document the knob and its default in
   `.claude/skills/drain/reference.md`.
5. Put the long-form unblock-policy detail in `reference.md`; keep SKILL.md
   under its size budget.
6. Author `evals/drain/04-spillover/`: a fixture with a focus blocked by one
   policy-passing `run:` and one `ask:`, plus a second NOW.md entry with ready
   work, asserting both the unblock-then-return path and the spill path.

## Acceptance

- [ ] `bash tests/test_drain_spillover.sh` → exits 0, reports 0 failures, and
      its output contains no `SENTINEL` line (a demoted `run:` that executed
      anyway would create one). **L2**
- [ ] The demotion carries the policy's reason code through to the `ask:` item
      — asserted in the test by matching the reason code
      `bin/command-policy` returned, not by matching prose. **L2**
- [ ] `grep -c 'command-policy' .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md | grep -c ':0$'`
      → 0, proving both files name the single policy implementation rather
      than describing a check of their own. **L1**
- [ ] `awk '/^## The loop/{f=1} f&&/^## Auto-breakdown/{exit} f' .claude/skills/drain/SKILL.md | grep -c 'spilling to'` → ≥ 1
      (verified 0 in the whole file today, 2026-07-30). **L0** — Depth
      ceiling: skill prose is not executable; the behavioral complement is the
      `evals/drain/04-spillover` scenario below.
- [ ] `grep -c 'CHORE_SLOTS' .claude/skills/drain/reference.md` → ≥ 1 with
      the default 1 stated on the same or an adjacent line (verified 0 in both
      drain files today, 2026-07-30). **L0** — Depth ceiling: as above; the
      eval's chore assertion is task 14's end-to-end scenario.
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → < 500. **L1**
- [ ] `grep -c 'ask:' evals/drain/04-spillover/setup.sh` → ≥ 1. **L1**
- [ ] `bash evals/run.sh drain` → the new scenario passes. **L3** —
      `manual-pending`: paid headless session; a human runs it and records the
      result (`docs/memory/unattended-worker-tool-limits.md`).
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
