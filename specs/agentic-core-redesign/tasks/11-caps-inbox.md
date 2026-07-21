# Task 11: caps replace approvals; the inbox and demote land

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 10
Priority: P2
Budget: 24 turns
Spec: ../SPEC.md (statements 10, 13; D1; Migration step 6)
Touch: agentic/inbox.py, agentic/promote.py, agentic/config/caps.toml, .claude/skills/build/SKILL.md, .claude/skills/drain/SKILL.md, .claude/skills/prioritize/SKILL.md, docs/human-gates.md, tests/test_agentic_inbox.py

## Goal

`agentic inbox` prints the one human list — open questions, recent
auto-promotions (undoable), spend against caps, priority calls.
`agentic demote <id>` reverts a promotion. Drafts that pass the critic
promote automatically. Cap defaults live in `agentic/config/caps.toml`
and the composer reads them. The launch-authorization contract prose in
build/drain/prioritize SKILL.md files is deleted (the untrusted-data
rule stays); docs/human-gates.md gains a short header noting D1
supersedes its framework, kept as history.

## Touch

Depends on task 10 because it edits the same SKILL.md files task 10
rewrites — serialized to avoid collision, per the spec's ordering.

## Steps

1. Write `tests/test_agentic_inbox.py` failing first: fixture store with
   a deferred question, a fresh promotion, and metered spend → inbox
   output contains all three sections; demote flips the promotion back
   to draft and the inbox reflects it.
2. Implement inbox.py, promote.py (auto-promote on critic READY
   recorded in tracker metadata), caps.toml wiring into the meter.
3. Delete the launch-contract blocks; annotate human-gates.md.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_inbox.py -q` → passes
- [ ] `grep -rn "launch-authorization\|launch authorization contract" .claude/skills/build/ .claude/skills/drain/ .claude/skills/prioritize/ | wc -l` → `0`
- [ ] `bash scripts/check.sh` → green
