# Task 01: Enforce section-bounded reference.md reads and by-path Worker prompt delivery

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: .claude/skills/drain/reference.md, .claude/skills/drain/SKILL.md

## Goal

Two hub anti-patterns found in a live `/drain` run get closed at the source:
(1) reference.md's own "load only the named section" note becomes an
enforced Grep-then-offset-Read procedure stated once, prominently, near its
table of contents, with SKILL.md's existing "load only the named section"
pointers citing it instead of repeating it; (2) the Worker prompt template
is delivered to dispatched workers by path-pointer (the same pattern
`<build-skill-path>` already uses), not pasted in full on every `Agent`
call — with only genuinely task-specific pieces (task file path, branch
name, budget, `## Answers` notes) inlined in the dispatch call.

## Touch

This task owns `.claude/skills/drain/reference.md` and
`.claude/skills/drain/SKILL.md` only — do not touch the mirror files
(`antigravity/.agents/workflows/drain.md`,
`codex/.agents/skills/drain/SKILL.md`); task 02 (depends on this one) ports
the equivalent tightening there. Do not touch
`tests/mirror-procedure-manifest.txt` — also task 02's scope.

## Steps

1. Near reference.md's table of contents / opening "Loaded on demand" note
   (~line 15), add a short, prominent procedure: before any reference.md
   read, `Grep -n '^## '` the file for its section headers, find the
   target section's line range, then `Read` with `offset`/`limit` bounded
   to that range — never a bare sequential `Read` of the whole file. Use
   the literal phrase "Grep-then-offset" somewhere in this addition (it is
   the anchor task 02's manifest-seeding and this spec's acceptance
   signals key off).
2. Update SKILL.md's existing "load only the named section" pointers (grep
   for the phrase to find every call site) to cite the new reference.md
   procedure rather than repeating instructions inline.
3. In reference.md's "Worker prompt" section (~line 615), state the
   delivery contract explicitly: the hub resolves this section to a
   concrete path (the same way `<build-skill-path>` is already resolved a
   few lines above it) and tells the dispatched worker to read and follow
   it verbatim, substituting only task-specific pieces (task file path,
   branch name, budget, any task-specific `## Answers` notes) directly in
   the dispatch call — never pasting the section's ~700-word body into the
   `Agent` prompt. Use the literal phrase "path-pointer" somewhere in this
   addition (the second manifest/acceptance anchor).
4. Update SKILL.md step 2's dispatch instructions (the "Worker prompt in"
   reference around line 167) to match: the dispatch call points at the
   resolved reference.md path rather than inlining the template.
5. Run the acceptance commands below; tick each box with one line of
   evidence.

## Acceptance

- [ ] `grep -c "Grep-then-offset" .claude/skills/drain/reference.md` → ≥ 1
      (count 0 today, verified 2026-07-19)
- [ ] `grep -c "path-pointer" .claude/skills/drain/reference.md` → ≥ 1
      (count 0 today, verified 2026-07-19)
- [ ] A human/manual-pending read confirms SKILL.md's "load only the named
      section" call sites (`grep -n "load only the named section"
    .claude/skills/drain/SKILL.md`) now cite the new reference.md
      procedure rather than only repeating the passive note — this is a
      prose-quality judgment, not a mechanical grep; mark manual-pending if
      dispatched unattended.
- [ ] `bash evals/lint-ultra-gate.sh` → exits 0
- [ ] `bash evals/lint-skill-size-gate.sh` → exits 0 (current state is a
      clean pass — `.claude/skills/drain/SKILL.md` is 495 lines, under the
      500-line budget, verified 2026-07-19 after the drain-orchestrator-run
      merge landed a prior relocation; this task's own edits must not push
      it back over 500 — `wc -l < .claude/skills/drain/SKILL.md` → ≤ 500)
- [ ] `wc -l < .claude/skills/drain/reference.md` — no numeric ceiling on
      this file (reference docs are loaded on demand), recorded only so a
      reviewer can see the size delta
