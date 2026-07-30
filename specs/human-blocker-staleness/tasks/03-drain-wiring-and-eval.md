# Task 03: wire the checker into drain's batch interview

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 01, 02
Priority: P2
Budget: 24 turns
Spec: ../SPEC.md (requirements R7, R11)
Touch: .claude/skills/drain/SKILL.md, evals/drain

## Goal

`/drain`'s batch interview runs `bin/check-human-blockers` before batching
blockers for the human and routes all five buckets explicitly — presenting
still-blocked, unprobed, and unknown entries, withholding only stale ones with
a count and a re-read pointer, and surfacing violations verbatim on exit 2. An
eval scenario proves the routing against a hermetic fixture.

## Touch

Owns the drain skill's batch-interview section and the new eval scenario
directory. Must NOT edit `bin/check-human-blockers`, `scripts/blocker-probes/`,
or either test suite — this task consumes what tasks 01 and 02 built. Must NOT
edit `HUMAN.md`.

## Steps

1. Edit `.claude/skills/drain/SKILL.md`'s "The batch interview" section: run
   the checker first, then route every bucket. Keep the edit inside that
   section — the file is near its size budget, so add the routing rule, do not
   restate the checker's contract, and cite the rule file for the grammar.
2. Build the eval scenario under `evals/drain/`. Its `setup.sh` copies
   `bin/check-human-blockers` and `scripts/blocker-probes/` into the fixture —
   `evals/run.sh` seeds `.claude/skills/_shared`, `runtimes/`, agents, rules,
   and `hooks/`, but neither `bin/` nor `scripts/`, so without this the
   scenario silently tests nothing.
3. Author the fixture `HUMAN.md` with five entries: still-blocked, stale,
   `none — <reason>`, one whose probe times out, and one with no clause. Every
   probe is deterministic and local; none reaches a foreign checkout.
4. Assert the interview presents the still-blocked, unprobed, and unknown
   entries, names the stale one as withheld with its count, and surfaces the
   clause-less one verbatim as a violation.

## Acceptance

- [ ] `awk '/^## The batch interview/{f=1;next} f&&/^## /{exit} f' .claude/skills/drain/SKILL.md | grep -c 'check-human-blockers'` → ≥ 1
      (verified 0 in the whole file today, 2026-07-29; the range form matters —
      a `/^## The batch interview/,/^## /` range terminates on its own start
      line and matches 1 line, so it would false-fail forever). **L0** —
      Depth ceiling: skill prose is
      not executable; the behavioral complement is the eval scenario below.
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → < 500, the SKILL.md size
      budget in the repository's authoring conventions. **L1**
- [ ] `grep -c 'blocker-probes' evals/drain/*/setup.sh` → ≥ 1, proving the
      fixture provisions what `evals/run.sh` does not. **L1**
- [ ] `bash evals/run.sh drain` → the new scenario passes. **L2** —
      `manual-pending`: every scenario is a paid headless session against a
      live CLI, and an unattended worker must not launch a paid
      nondeterministic eval (`docs/memory/unattended-worker-tool-limits.md`).
      A human runs this and records the result on this task.
- [ ] End to end: file a blocker through the rule's grammar, make its probe
      start returning nonzero, and confirm the batch interview withholds it and
      names it. **L3** — `manual-pending`: drives `/drain` interactively; a
      human runs it and records the outcome.
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
