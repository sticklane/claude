# Task 04: doctrine guide docs + link checker gate

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirements R6, R7, R8)
Touch: docs/guides/, tests/test_doc_links.sh

## Goal

Three guide pages exist — `docs/guides/context-management.md`,
`docs/guides/correctness.md`, `docs/guides/model-routing.md` — each a
readable synthesis (not a dump) with ≥1 mermaid diagram, ≥1 link into the
in-repo research docs (`docs/anthropic-playbook.md`,
`docs/orchestration-research-2026-07.md`,
`docs/context-management-research-2026-07.md`), ≥2 links to primary
sources (e.g. Anthropic engineering posts the research docs cite), and an
explicit list of the toolkit skills/rules the page explains (e.g.
model-routing names `.claude/rules/token-discipline.md`'s tier ladder and
the skills that pin dispatch tiers; correctness names the verifier/critic
agents, /gate, and drain's whitelist-diff; context-management names
scouts, /handoff, /distill, and cache economics). A link checker at
`tests/test_doc_links.sh` verifies every relative link in `docs/guides/`
resolves and every mermaid fence has a non-empty body; it rides the
existing `for t in tests/test_*.sh` gate automatically.

## Touch

Only `docs/guides/` (new dir) and `tests/test_doc_links.sh` (new file).
R8 is binding: do NOT add anything to `CLAUDE.md`, `.claude/rules/`, or
any `.claude/skills/*/SKILL.md` — the guides are informational and must
not grow session context. Do NOT edit the research docs themselves.

## Steps

1. Write the failing gate first: `tests/test_doc_links.sh` (checks
   relative links resolve from each file's own dir; checks each
   ```mermaid fence has a non-empty body; fails when docs/guides/ is
   missing) — confirm it fails, then write the docs to green.
2. Write the three guides. Diagram suggestions: context-management — the
   scout/delegate flow and cache-window economics; correctness — the
   spec → critic → build → verifier → gate pipeline; model-routing — the
   four-rung tier ladder with dispatch points.
3. Verify every primary-source URL cited actually appears in (or is
   consistent with) the research docs — no invented links.
4. Gate suite green; commit.

## Acceptance

- [ ] `bash tests/test_doc_links.sh` → exit 0
- [ ] `ls docs/guides/context-management.md docs/guides/correctness.md docs/guides/model-routing.md` → all exist
- [ ] `for f in docs/guides/*.md; do grep -c '^```mermaid' "$f"; done` → ≥ 1 per file
- [ ] `grep -l 'anthropic-playbook\|orchestration-research\|context-management-research' docs/guides/*.md | wc -l` → 3
- [ ] `git diff --stat main -- CLAUDE.md .claude/rules/` → empty, and no `.claude/skills/*/SKILL.md` in `git diff --name-only main` (R8)
