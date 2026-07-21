# Task 01: docs/guides/ctx-cujs.md — the CUJ playbook + gap table

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 18 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: docs/guides/ctx-cujs.md

## Goal

`docs/guides/ctx-cujs.md` exists: 8 CUJ sections (ORIENT, LOCATE, DIG IN,
VERIFY ABSENCE, IMPACT, SURVEY, DEDUP/DEAD CODE, KNOWLEDGE) each with
trigger/sequence/token-shape/failure-modes, plus a final Gap table section
mapping each CUJ to its serving spec(s) and status, evidence-cited.

## Touch

Only this one new file. Do not edit `.claude/skills/ctx/SKILL.md` or any
spec's SPEC.md — those are tasks 02 and 03.

## Steps

1. Write the 8 CUJ sections using the SPEC's own Solution section content
   as source material (it already names each CUJ's trigger, query
   sequence, and failure modes with their owning specs — don't invent new
   content, transcribe and lightly expand into the four-field shape: `##
<N>. <NAME>` heading, then trigger / query sequence / expected token
   shape / known failure modes as sub-bullets or short paragraphs).
2. Write the final `## Gap table` section: one row per CUJ, columns
   CUJ → serving spec(s) → status (shipped / specced / gap). Every
   "shipped" cell cites the code path proving it (e.g. ctxignore-git-overlay
   → `context-tree/src/vcs/mod.rs` overlay — confirm this path exists
   before citing it). Every "specced" cell cites the spec path. A status
   without its citation is not acceptable (R2's anti-gaming requirement).
   Use "gap" + a one-line proposed next step for anything with no shipped
   code and no existing spec.
3. Keep the whole file ≤180 lines. Confirm exactly 9 `## ` headings (8
   CUJs + Gap table) and that the Gap table is the LAST heading.
4. Verify every cited spec path actually resolves (`ls specs/<slug>/`
   for each one named in a citation) before finalizing.

## Acceptance

- [ ] `grep -c '^## ' docs/guides/ctx-cujs.md` → 9.
- [ ] `grep '^## ' docs/guides/ctx-cujs.md | tail -1` → `## Gap table`.
- [ ] `wc -l < docs/guides/ctx-cujs.md` → ≤180.
- [ ] For every spec path cited in the file (extract with
      `grep -oE 'specs/[a-z0-9-]+' docs/guides/ctx-cujs.md | sort -u`),
      `ls specs/<slug>/` succeeds — every citation resolves to a real spec
      directory.
- [ ] Every "shipped" row in the Gap table has a code-path citation, and
      every "specced" row has a spec-path citation (read the table and
      confirm — no status-without-citation row).
