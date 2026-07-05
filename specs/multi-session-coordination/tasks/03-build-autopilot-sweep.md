# Task 03: build + autopilot — startup sweep and owner respect

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R7 build/autopilot parts)
Touch: .claude/skills/build/SKILL.md, .claude/skills/autopilot/SKILL.md

## Goal

/build and /autopilot open with the same advisory session sweep drain
gets (enumerate other live sessions with cwd inside the repo via
`claude agents --json`, pid-record fallback, one line per foreign
session, "sweep unavailable" line on failure, never blocking). /build
additionally warns — and, being attended, may ask the user — before
editing a task in a spec whose `specs/<slug>/DRAIN-OWNER.md` shows fresh
liveness evidence (cite drain's reference for the liveness definition;
do not restate it).

## Touch

Only the two SKILL.md files. Do NOT touch drain's files (task 02 owns
them — including the liveness definition you cite), rules, antigravity,
or plugin.json. Both skills are ultra-gated: keep every "ultra" mention
within ±3 lines of the "active runtime profile" marker
(`bash evals/lint-ultra-gate.sh` green). Cite, don't restate: the sweep
mechanism details live in drain's text per R7 — build/autopilot carry
the instruction and the pointer.

## Steps

1. Add the sweep opening to each skill (2–5 lines each, citing drain's
   reference for mechanism detail).
2. Add /build's owner-warn clause near its start-of-work step.
3. `bash evals/lint-ultra-gate.sh` green; acceptance greps; full test
   sweep; commit.

## Acceptance

- [ ] `grep -c "claude agents --json" .claude/skills/build/SKILL.md` → ≥ 1
- [ ] `grep -c "claude agents --json" .claude/skills/autopilot/SKILL.md` → ≥ 1
- [ ] `grep -c "DRAIN-OWNER" .claude/skills/build/SKILL.md` → ≥ 1
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
- [ ] `for t in tests/test_*.sh; do bash "$t" || exit 1; done && claude plugin validate .` → exit 0
