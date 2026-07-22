# Task 03: critic ctx grant + prompt line; onboard allowlist entry

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirements R3a, R3b)
Touch: .claude/agents/critic.md, antigravity/.agents/skills/critic/SKILL.md, .claude/skills/onboard/SKILL.md, antigravity/.agents/workflows/onboard.md

## Goal

The critic agent can and will run ctx: `.claude/agents/critic.md` gains
`Bash(ctx *)` in its `tools:` frontmatter plus one prompt line containing
the exact phrase "index-first: prefer ctx" (run ctx queries for structure
questions when the repo is indexed). The antigravity critic mirror gains
ONLY the prompt line — skill mirrors have no `tools:` mechanism; the
grant is a load-bearing divergence per
`.claude/rules/mirror-procedure-discipline.md`, never faked as prose.
/onboard's §4 "Permissions" allowlist step recommends `Bash(ctx *)` when
the target repo is indexed.

## Touch

SEAM: specs/ctx-skill-token-doctrine R6a also edits
`.claude/skills/onboard/SKILL.md` (a different section — the CLAUDE.md
doctrine-section instruction). That spec has no tasks/ yet; if its
breakdown lands while this task is open, the two onboard edits land
serialized, whichever is second rebasing on the first (SPEC seam note).
Do NOT touch `.claude-plugin/plugin.json` (task 06) or the scout agent
(token-doctrine R5 owns it).

## Steps

1. `.claude/agents/critic.md`: add `Bash(ctx *)` to the `tools:` line;
   add the prompt line with the exact literal "index-first: prefer ctx".
2. `antigravity/.agents/skills/critic/SKILL.md`: add the prompt line
   only (same literal). No tools/grant text of any kind.
3. `.claude/skills/onboard/SKILL.md` §4 "Permissions": add `Bash(ctx *)`
   to the recommended allowlist, conditional on the repo being indexed
   (`.context/` present or `ctx` resolving). Port to
   `antigravity/.agents/workflows/onboard.md`.

## Acceptance

- [x] `grep -q 'Bash(ctx' .claude/agents/critic.md && echo ok` → ok (tools line gains `Bash(ctx *)`)
- [x] `grep -q 'index-first: prefer ctx' .claude/agents/critic.md && echo ok` → ok (prompt line added after intro)
- [x] `grep -q 'index-first: prefer ctx' antigravity/.agents/skills/critic/SKILL.md && echo ok` → ok (mirror prompt line only)
- [x] `grep -c 'Bash(ctx' antigravity/.agents/skills/critic/SKILL.md` → 0 (no faked grant in the mirror; confirmed 0)
- [x] `grep -q 'Bash(ctx' .claude/skills/onboard/SKILL.md && echo ok` → ok (§4 Permissions indexed-repo recommendation)
- [x] `grep -q 'Bash(ctx' antigravity/.agents/workflows/onboard.md && echo ok` → ok (runtime-honest guardrail note)
- [x] `bash tests/test_mirror_procedure_coverage.sh` → exit 0 (confirmed exit=0)

Depth ceiling: L0/L1 greps — frontmatter grants and prompt prose have no
runnable behavior in-repo; the behavioral complement is task 04's
telemetry (critic-session ctx invocations) and a future critic evalset
scenario in an indexed fixture repo.

## Decisions

- 2026-07-21: `antigravity/.agents/workflows/onboard.md` is a thin
  pointer wrapper; the real antigravity onboard content (including §4
  Permissions/Guardrails) lives in `antigravity/.agents/skills/onboard/SKILL.md`
  (out of this task's Touch). Satisfied criterion c6 by adding the
  ctx-guardrail note to the permitted wrapper file, framed in
  antigravity's own Terminal Execution Policy guardrail terms rather than
  a faked settings.json allowlist mechanism. Reversible: delete the added
  paragraph.
- 2026-07-21: `tests/mirror-procedure-manifest.txt` left unseeded for the
  new "index-first: prefer ctx" critic phrase — not in Touch, and no
  existing manifest phrase broke. Reversible: n/a (no change made).

## Discovered

- The new critic "index-first: prefer ctx" phrase is present in both
  critic legs (`.claude/agents/critic.md`,
  `antigravity/.agents/skills/critic/SKILL.md`) but not seeded in
  `tests/mirror-procedure-manifest.txt`, leaving it unprotected from a
  silent re-drop. See task 08.
- `antigravity/.agents/workflows/onboard.md`'s ctx-guardrail note now sits
  in the thin pointer wrapper rather than beside the actual §4 Guardrails
  step in `antigravity/.agents/skills/onboard/SKILL.md` — a future
  consolidation could move it there for coherence. See task 09.
