# Task 03: Document isolation-worktree CLAUDE.md/rules re-injection as an accepted wake-economics tax

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirement R3)
Touch: .claude/skills/drain/reference.md

## Goal

reference.md's "Wake economics" section gains one documented line noting
that entering a fresh `git worktree` and then `Read`/`Edit`-ing a file
under it causes the harness to reprint the full `CLAUDE.md` +
`.claude/rules/*.md` stack (byte-identical to what the hub already carries
for the main checkout) — an accepted, budgeted-for tax on
`isolation: worktree` dispatch, not a bug and not something to route
around, so a hub session sizing its own context growth isn't surprised by
it.

## Touch

Depends on task 01 only to avoid a same-file edit collision in
reference.md (both tasks touch it); this task's addition is otherwise
independent of task 01's content — do not touch task 01's
Grep-then-offset or Worker-prompt sections, and do not touch SKILL.md or
any mirror file (this is documentation-only, local to `.claude/`'s
reference.md, per the spec's R4 note: port only if a mirror already
carries an equivalent wake-economics discussion — antigravity/codex do
not, so nothing to port here).

## Steps

1. Locate reference.md's "Wake economics" section (`grep -n "^## Wake
economics" .claude/skills/drain/reference.md`).
2. Add one short, clearly-labeled paragraph or bullet stating the
   isolation-worktree CLAUDE.md/rules re-injection cost as described in
   the Goal above — an accepted tax, not a bug, not something to fix. Use
   the literal phrase "worktree re-injection" somewhere in the addition
   (the mechanical anchor the acceptance check below keys off).
3. Run the acceptance commands below; tick each box with one line of
   evidence.

## Acceptance

- [x] `grep -c "worktree re-injection" .claude/skills/drain/reference.md` → ≥ 1
      (count 0 today, verified 2026-07-19)
      Evidence: grep -c returns 1 after edit (was 0).
- [~] A human/manual-pending read of the "Wake economics" section confirms
  the addition reads as an accepted, budgeted-for tax — not a bug, not
  something to route around — matching the Goal's framing. Mark
  manual-pending if dispatched unattended.
  manual-pending: dispatched unattended. New bold-led paragraph
  "Worktree re-injection is a budgeted tax, not a bug." states it is
  "expected and accepted, not something to route around or 'fix'".
- [x] `bash evals/lint-ultra-gate.sh` → exits 0
      Evidence: "lint-ultra-gate: OK — all ultra mentions gated in 4 files", exit 0.
- [x] `bash evals/lint-skill-size-gate.sh` → exits 0
      Evidence: "lint-skill-size-gate: OK — all skill docs within size/TOC conventions", exit 0.
