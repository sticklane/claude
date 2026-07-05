# Task 02: the review step in build's close-out

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P1
Budget: 14 turns
Spec: ../SPEC.md (requirements R1–R5; every contract pinned in Solution)
Touch: .claude/skills/build/SKILL.md

## Goal

Build's close-out carries the pre-commit review step, positioned after
the simplification pass (+ its acceptance re-run) and before the final
commit: (R2) the deterministic skip gate first — the pinned single
command against the step-0 recorded base, the pinned NON-product pattern
list, the <25 product-line threshold, skip → record reason and proceed
to commit; (R3) reviewer selection — `/code-review` via the Skill tool
with args `low` when available (bare when args can't pass), else ONE
fallback subagent (high-confidence correctness findings only, return
≤1k tokens), run inline / read directly, never block on a background
notification (cite drain's clause); (R4) the fix policy — correctness
findings fixed iff inside `Touch:` (no-Touch fallback: files touched
this session), acceptance re-run after fixes, out-of-Touch/uncertain →
user (attended) / `Discovered:` (unattended), style dropped; (R1)
explicit single-pass language, no re-review after fixes; (R5) the
outcome line (`review: N findings, M fixed, K discovered` /
`review skipped: <reason>`) written into the evidence the close-out
already produces.

## Touch

Only build's SKILL.md. Do NOT touch tests/ (task 01), antigravity or
plugin.json (task 03), drain, or critique. Constraints: build is
ultra-gated — keep every case-insensitive "ultra" mention within ±3
lines of the "active runtime profile" marker
(`bash evals/lint-ultra-gate.sh` green); SKILL.md stays well under 500
lines and keeps execution-critical contracts in its first 30 lines
(CLAUDE.md authoring conventions).

## Steps

1. Read ../SPEC.md Solution fully; read build's close-out (≈lines
   70–99) to place the step between simplification and commit.
2. Write the step: skip gate first (exact command + patterns), reviewer
   selection, fix policy, single-pass bound, outcome line.
3. `bash evals/lint-ultra-gate.sh`; acceptance greps; full test sweep;
   commit.

## Acceptance

- [ ] `grep -c "code-review" .claude/skills/build/SKILL.md` → ≥ 1 and `grep -ci "one pass" .claude/skills/build/SKILL.md` → ≥ 1
- [ ] `grep -c "numstat" .claude/skills/build/SKILL.md` → ≥ 1 and `grep -c "review skipped" .claude/skills/build/SKILL.md` → ≥ 1 and `grep -c "git add -A" .claude/skills/build/SKILL.md` → ≥ 1
- [ ] `grep -qE "review: N findings|review:.*fixed.*discovered" .claude/skills/build/SKILL.md` → exit 0
- [ ] `grep -c "touched this session" .claude/skills/build/SKILL.md` → ≥ 2 (simplification scope + the review step's no-Touch fallback)
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
- [ ] `for t in tests/test_*.sh; do bash "$t" || exit 1; done && claude plugin validate .` → exit 0
