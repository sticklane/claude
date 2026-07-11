# Task 02: Doctrine blocks in token-discipline.md (freehand-drain + tier-dispatch) + proposed global one-liner

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: pending
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R5) + ../../agent-tier-leaks/SPEC.md (requirement R2 — delivered here so token-discipline.md has a single writer and the specs can drain concurrently)
Touch: .claude/rules/token-discipline.md, specs/drain-wake-cost/global-claude-line.md

## Goal

Two short doctrine blocks land in `.claude/rules/token-discipline.md`.
(1) Freehand-drain: sessions receiving a drain-shaped request ("drain the
…", "work through the remaining tasks in specs/…") recommend the human
launch `/drain` instead of improvising an unstructured dispatch loop.
(2) Tier-dispatch (agent-tier-leaks R2): mechanical fan-out work dispatched
outside a skill uses the typed pinned agents
(scout/verifier/implementation-worker) or passes an explicit cheap-tier
`model` override to general-purpose; bare general-purpose at session model
is reserved for judgment work — citing the measured $/call inversion
(general-purpose $0.067 vs opus-pinned implementation-worker $0.057, from
the 2026-07 agentprof week). Because the measured freehand spend is
cross-repo and this repo's rules load only in-repo, the task also delivers
the proposed one-liner for the user's global `~/.claude/CLAUDE.md` as a
small artifact file — applying it there is a MANUAL (attended) step for the
human, not this task.

## Touch

Only the rules file and the new proposal artifact. This task is the ONLY
writer of token-discipline.md across all three agentprof specs — that
exclusivity is what makes concurrent drains safe; never move either block
to another task. Do NOT edit this repo's CLAUDE.md (cite-don't-restate:
the rules doc is the doctrine home), do NOT edit `~/.claude/CLAUDE.md`
(user-private, outside the repo), and do NOT touch the drain skill files
(task 01 owns them).

## Steps

1. Read ../SPEC.md R5 and `.claude/rules/token-discipline.md` (the
   "Session hygiene" and "Delegation defaults" sections are the natural
   neighborhoods).
2. Add the freehand-drain block (2–4 lines) to token-discipline.md: when a
   freehand request is drain-shaped, recommend the human launch `/drain` —
   the skill's window/baton/verdict machinery is what keeps a dispatch
   loop cheap and safe; improvised loops are how the measured $1,406/week
   of unstructured orchestration happened (cite ../EVIDENCE.md path, don't
   restate numbers beyond one figure). Drain stays human-gated; this is a
   recommend, never an auto-invoke.
3. Add the tier-dispatch block (3–6 lines) inside "Model and effort
   matching" or "Dispatch authoring" — extend, don't duplicate: those
   sections already teach tier-by-stage for SKILL-authored dispatch; this
   block covers freehand dispatch specifically. Cite the $/call figures
   ($0.067 vs $0.057) and point at ../EVIDENCE.md for provenance. Confirm
   it doesn't contradict the existing tier rungs — it applies them to
   freehand dispatch, nothing more. (Requirement text:
   ../../agent-tier-leaks/SPEC.md R2.)
4. Write `specs/drain-wake-cost/global-claude-line.md`: the proposed
   one-liner for `~/.claude/CLAUDE.md`, plus one sentence of placement
   advice, clearly marked "MANUAL (attended): for Steven to apply".
5. Run the acceptance checks.

## Acceptance

- [ ] `grep -qi 'drain-shaped' /Users/sjaconette/claude/.claude/rules/token-discipline.md` → exit 0 (bare "drain" already appears in the file — the new block must use the "drain-shaped" phrasing), and the block recommends launching /drain for such freehand requests (quote it as evidence)
- [ ] `grep -q '0\.067' /Users/sjaconette/claude/.claude/rules/token-discipline.md` → exit 0, and MANUAL: the tier-dispatch block names the pinned agents as the default for mechanical fan-outs and reserves session-model general-purpose for judgment work (quote it as evidence)
- [ ] `test -f /Users/sjaconette/claude/specs/drain-wake-cost/global-claude-line.md` → exit 0, and the file is marked MANUAL (attended)
- [ ] `grep -qiE 'auto-?invoke|auto-?trigger' /Users/sjaconette/claude/.claude/rules/token-discipline.md || true` — MANUAL sanity: the new block must NOT instruct auto-invoking drain (it is disable-model-invocation)
