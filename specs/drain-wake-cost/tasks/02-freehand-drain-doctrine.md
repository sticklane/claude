# Task 02: Freehand-drain doctrine line + proposed global one-liner

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: pending
Depends on: none
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirement R5)
Touch: .claude/rules/token-discipline.md, specs/drain-wake-cost/global-claude-line.md

## Goal

Sessions in this repo that receive a freehand drain-shaped request
("drain the …", "work through the remaining tasks in specs/…") are
instructed to recommend the human launch `/drain` instead of improvising an
unstructured dispatch loop. Because the measured freehand spend is
cross-repo and this repo's rules load only in-repo, the task also delivers
the proposed one-liner for the user's global `~/.claude/CLAUDE.md` as a
small artifact file — applying it there is a MANUAL (attended) step for the
human, not this task.

## Touch

Only the rules file and the new proposal artifact. Do NOT edit this repo's
CLAUDE.md (cite-don't-restate: the rules doc is the doctrine home), do NOT
edit `~/.claude/CLAUDE.md` (user-private, outside the repo), and do NOT
touch the drain skill files (task 01 owns them).

## Steps

1. Read ../SPEC.md R5 and `.claude/rules/token-discipline.md` (the
   "Session hygiene" and "Delegation defaults" sections are the natural
   neighborhoods).
2. Add a short block (2–4 lines) to token-discipline.md: when a freehand
   request is drain-shaped, recommend the human launch `/drain` — the
   skill's window/baton/verdict machinery is what keeps a dispatch loop
   cheap and safe; improvised loops are how the measured $1,406/week of
   unstructured orchestration happened (cite ../EVIDENCE.md path, don't
   restate numbers beyond one figure). Drain stays human-gated; this is a
   recommend, never an auto-invoke.
3. Write `specs/drain-wake-cost/global-claude-line.md`: the proposed
   one-liner for `~/.claude/CLAUDE.md`, plus one sentence of placement
   advice, clearly marked "MANUAL (attended): for Steven to apply".
4. Run the acceptance checks.

## Acceptance

- [ ] `grep -qi 'drain-shaped' /Users/sjaconette/claude/.claude/rules/token-discipline.md` → exit 0 (bare "drain" already appears in the file — the new block must use the "drain-shaped" phrasing), and the block recommends launching /drain for such freehand requests (quote it as evidence)
- [ ] `test -f /Users/sjaconette/claude/specs/drain-wake-cost/global-claude-line.md` → exit 0, and the file is marked MANUAL (attended)
- [ ] `grep -qiE 'auto-?invoke|auto-?trigger' /Users/sjaconette/claude/.claude/rules/token-discipline.md || true` — MANUAL sanity: the new block must NOT instruct auto-invoking drain (it is disable-model-invocation)
