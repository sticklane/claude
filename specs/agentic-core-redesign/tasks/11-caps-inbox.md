# Task 11: caps replace approvals; the inbox and demote land

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 10
Priority: P2
Budget: 24 turns
Spec: ../SPEC.md (statements 10, 13; D1; Migration step 6)
Touch: .claude/skills/build/SKILL.md, .claude/skills/drain/SKILL.md, .claude/skills/prioritize/SKILL.md, docs/human-gates.md

## Goal

PIVOTED SCOPE (2026-07-22 addendum, ../SPEC.md): the caps/inbox BUILD
is superseded — promotion/demotion are bd status flips, the inbox is
`bd ready` plus deferred-question issues, and the pre-flight budget
guard belongs to specs/beads-daily-skill. What remains here is the
deletion half: the launch-authorization contract prose in
build/drain/prioritize SKILL.md files is removed (the untrusted-data
rule stays), and docs/human-gates.md gains a short header noting the
caps decision supersedes its framework, kept as history.

## Steps

1. Delete the launch-contract blocks from the three SKILL.md files.
2. Annotate docs/human-gates.md with the supersession header.

## Acceptance

- [x] `grep -rn "launch-authorization\|launch authorization contract" .claude/skills/build/ .claude/skills/drain/ .claude/skills/prioritize/ | wc -l` → `0`
- [x] `grep -c "superseded" docs/human-gates.md` → ≥ 1 (history annotated, not deleted)
- [x] `bash scripts/check.sh` → green
