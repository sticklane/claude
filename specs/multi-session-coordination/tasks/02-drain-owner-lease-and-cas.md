# Task 02: drain skill — owner lease, CAS flips, write hygiene, sweep

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirements R1–R7 drain parts; format + exception pinned in Solution)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

The drain skill text carries the full coordination protocol: (R1) the
owner-lease claim (CAS with post-commit Run-token read-back; loser takes
the refuse path) before step 1's dispatch plan, and release at the
terminal report; (R2) refuse-on-live-owner with evidence report, the
baton-lineage exception (adopt iff baton `Run-token:` matches the owner's;
the baton grammar in reference.md gains a `Run-token:` line, and the
owner-file update lands in the SAME commit as each baton write, with R1a
reconciliation), and stale-owner reclaim with the foreign-reclaim
tightening (sweep only when activity signals are stale AND
`git worktree list` shows no checkout of the task branch); (R3) the
owner-liveness definition in reference.md (newest of spec-dir commit
recency and per-task stale-lock signals vs the named grace window;
TaskList explicitly session-local, never evidence about other sessions);
(R4) the pending→in-progress flip specified as CAS (fresh read,
exact-match edit, path-scoped commit, post-commit verify at HEAD);
(R5) the path-scoped-commit rule stated once (explicit paths, never
`-a`/`git add .`); (R6) the push guard extended to every bookkeeping
commit with the `pull --rebase` dropped-commit rationale; (R7) drain's
startup session sweep (advisory, `claude agents --json` with the
agent-console cwd pattern, pid-record fallback, never blocking).

## Touch

Only drain's two files. Do NOT touch build/autopilot (task 03), the
rules dir (task 04), antigravity or plugin.json (task 05), or workboard
code. Editing constraints: keep every case-insensitive "ultra" mention
within ±3 lines of the "active runtime profile" marker
(`bash evals/lint-ultra-gate.sh` must stay green), and keep SKILL.md's
execution-critical contracts in its first 30 lines per CLAUDE.md
authoring conventions. SKILL.md stays well under 500 lines; push detail
into reference.md.

## Steps

1. Read the spec's Solution + R1–R7 fully; sketch where each clause
   lands (claim → before step 1; CAS flip → step 2; push/path-scope →
   step 2/3; liveness + owner format + baton Run-token → reference.md
   Status-field/liveness/baton sections; sweep → skill opening).
2. Make the edits; run `bash evals/lint-ultra-gate.sh` after touching
   SKILL.md.
3. Run the acceptance greps and the full test sweep; commit.

## Acceptance

- [x] `grep -c "DRAIN-OWNER" .claude/skills/drain/SKILL.md` → ≥ 2 and `grep -c "DRAIN-OWNER" .claude/skills/drain/reference.md` → ≥ 1 — evidence: SKILL.md 5, reference.md 5
- [x] `grep -c "Run-token" .claude/skills/drain/reference.md` → ≥ 2 (owner format + baton grammar) — evidence: reference.md 5
- [x] `grep -ciE "compare-and-swap|exact-match" .claude/skills/drain/SKILL.md` → ≥ 1 — evidence: 3
- [x] `grep -c "path-scoped" .claude/skills/drain/SKILL.md` → ≥ 1 and `grep -c "pull --rebase" .claude/skills/drain/SKILL.md` → ≥ 1 — evidence: 8 and 1
- [x] `grep -c "claude agents --json" .claude/skills/drain/SKILL.md` → ≥ 1 — evidence: 1
- [x] `bash evals/lint-ultra-gate.sh` → exit 0 — evidence: "lint-ultra-gate: OK — all ultra mentions gated in 4 files"
- [x] `for t in tests/test_*.sh; do bash "$t" || exit 1; done && ./specs/status.sh && claude plugin validate .` → exit 0 — evidence: all 9 test_*.sh files passed (0 fail each), status.sh listed queue, `claude plugin validate .` → "✔ Validation passed"

Verifier: PASS — full report in ../evidence/02-drain-owner-lease-and-cas.md
