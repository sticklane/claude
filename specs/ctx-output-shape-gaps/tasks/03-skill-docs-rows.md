# Task 03: skill command-table rows for --files + empty-vs-no-match note

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: blocked
Unblock: run: grep -q 'ctx-output-shape-gaps' specs/ctx-skill-token-doctrine/SPEC.md || echo "BLOCKED: registry slot absent — an attended/breakdown session must land the atomic registry commit (SPEC.md R3 (a)+(b)+(c)) once the specs/ctx-cujs/DRAIN-OWNER.md lease clears"
Depends on: 01, 02
Priority: P3
Budget: 6 turns
Spec: ../SPEC.md (requirement R3)
Touch: .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md, .claude-plugin/plugin.json

## Goal

The ctx skill's command table documents `tree --files`, and a one-line
note explains that empty-vs-no-match outputs mean different things
(pointing at the emitted stderr tails). Skill + antigravity mirror in
the same commit, plus the plugin.json bump (this spec's only
skill-editing task carries it).

## Touch

REGISTRY-GOVERNED: runs only after this spec's slot exists in
specs/ctx-skill-token-doctrine's Landing order registry (the Unblock
check); lands serialized per that registry, never parallel with another
SKILL.md-editing task from any spec. NOTHING auto-flips this task —
/drain does not re-run `Unblock: run:` on pre-existing blocked tasks; a
human or later session re-checks and flips to pending after the
registry commit lands. The registry commit itself (SPEC R3 (a)+(b)+(c),
including the cujs/02 count amendments) is a breakdown/attended-session
obligation, deferred 2026-07-21 under a live cujs drain lease — not
this task's work. Depends on 01+02 so the documented behavior exists.

## Steps

1. Verify the registry slot exists (the Unblock command) and tasks
   01/02 are done.
2. Add the `--files` row to the command table and the empty-vs-no-match
   note; mirror to `antigravity/.agents/skills/ctx/SKILL.md` in the
   same commit; bump plugin.json.

## Acceptance

- [ ] `grep -c -- '--files' .claude/skills/ctx/SKILL.md` → ≥1
- [ ] `grep -c -- '--files' antigravity/.agents/skills/ctx/SKILL.md` → ≥1
- [ ] `git show $(git merge-base HEAD origin/main):.claude-plugin/plugin.json | grep '"version"'` differs from current (base-commit comparison, never a pinned literal)
- [ ] `cd context-tree && cargo test --test doc_conformance` → exit 0 IF specs/ctx-doc-drift-gate task 01 has landed (the new row validates against the binary); otherwise mark this criterion manual-pending with that reason

Depth ceiling: L0/L1 doc greps — the behavioral halves live in tasks
01/02's goldens; this task is documentation currency only.
