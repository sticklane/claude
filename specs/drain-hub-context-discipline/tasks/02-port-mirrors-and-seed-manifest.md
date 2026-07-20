# Task 02: Port section-read/worker-prompt tightening into mirrors, seed the coverage manifest

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: 01
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R4)
Touch: antigravity/.agents/workflows/drain.md, codex/.agents/skills/drain/SKILL.md, tests/mirror-procedure-manifest.txt

## Goal

Per `.claude/rules/mirror-procedure-discipline.md`, task 01's two changes
are PROCEDURE (not incidental prose), so the equivalent behavioral
tightening — the Grep-then-offset-Read discipline and the by-path Worker
prompt delivery contract — lands in `antigravity/.agents/workflows/drain.md`
(paraphrased port, own voice) and `codex/.agents/skills/drain/SKILL.md`
(real content). The mirror-procedure-coverage manifest gains entries so the
gate actually verifies this landed, rather than passing vacuously.

## Touch

Do not touch `.claude/skills/drain/reference.md` or
`.claude/skills/drain/SKILL.md` — task 01's scope, already landed and
merged as this task's dependency. Port the CONCEPTS task 01 added
(section-bounded reads before a reference/procedure-doc lookup; worker
prompts delivered by path, not pasted in full), adapted to each mirror's
own structure — mirrors are paraphrased ports, never byte-copies
(`.claude/rules/mirror-procedure-discipline.md`;
docs/memory/workboard-mirror-verbatim.md). **Exception, narrowly scoped:**
the two literal anchor tokens "Grep-then-offset" and "path-pointer" must
appear verbatim (not paraphrased) in both mirrors — they are the shared
coverage-manifest anchors step 4 seeds, and the manifest test requires the
exact phrase present in both the source and the mirror; a paraphrased
"equivalent" phrase fails the source-presence check task 01 already
satisfies only with the literal tokens.

## Steps

1. Read task 01's landed diff in `.claude/skills/drain/reference.md` and
   `.claude/skills/drain/SKILL.md` (`git log` / `git show` on task 01's
   merge commit) to see the exact procedural tightening to port.
2. In `antigravity/.agents/workflows/drain.md`, add the equivalent
   Grep-then-offset-Read discipline wherever that file instructs loading a
   reference/procedure doc section, and the equivalent by-path Worker
   prompt delivery contract wherever it instructs dispatching a worker —
   in Antigravity's own voice and structure, not a verbatim copy, EXCEPT
   the literal tokens "Grep-then-offset" and "path-pointer" must each
   appear verbatim somewhere in the ported text (the Touch section's
   narrow exception).
3. In `codex/.agents/skills/drain/SKILL.md` (real content, not a symlink —
   see root CLAUDE.md's port-chain note), make the same two changes,
   with the same verbatim-token requirement.
4. Add new `<source>|<mirror>|<phrase>` lines to
   `tests/mirror-procedure-manifest.txt`, using the literal phrase
   "Grep-then-offset" and the literal phrase "path-pointer" — never a
   paraphrased substitute, since the manifest test requires the exact
   phrase present in both the source and mirror file:
   `.claude/skills/drain/reference.md|antigravity/.agents/workflows/drain.md|Grep-then-offset`,
   `.claude/skills/drain/reference.md|antigravity/.agents/workflows/drain.md|path-pointer`,
   `.claude/skills/drain/reference.md|codex/.agents/skills/drain/SKILL.md|Grep-then-offset`,
   `.claude/skills/drain/reference.md|codex/.agents/skills/drain/SKILL.md|path-pointer`
   — four new lines total. Confirm each phrase is present in
   `.claude/skills/drain/reference.md` (already true from task 01) and in
   its stated mirror (`grep -c <phrase> <mirror>` ≥ 1) before adding the
   line — the manifest format's own skip rule silently passes a phrase the
   source lacks, so an unverified line proves nothing.
5. Run the acceptance commands below; tick each box with one line of
   evidence.

## Acceptance

- [ ] `bash tests/test_mirror_procedure_coverage.sh` → exits 0
- [ ] `grep -c '^\.claude/skills/drain/reference\.md|antigravity' tests/mirror-procedure-manifest.txt` → ≥ 2
      (the two new lines for the antigravity mirror)
- [ ] `grep -c '^\.claude/skills/drain/reference\.md|codex' tests/mirror-procedure-manifest.txt` → ≥ 2
      (the two new lines for the codex mirror)
- [ ] `grep -c "Grep-then-offset" antigravity/.agents/workflows/drain.md` → ≥ 1
      and `grep -c "path-pointer" antigravity/.agents/workflows/drain.md` → ≥ 1
- [ ] `grep -c "Grep-then-offset" codex/.agents/skills/drain/SKILL.md` → ≥ 1
      and `grep -c "path-pointer" codex/.agents/skills/drain/SKILL.md` → ≥ 1
- [ ] A human/manual-pending read confirms both mirror edits carry the same
      procedure task 01 added (Grep-then-offset section reads, by-path
      Worker prompt delivery) in each runtime's own voice —
      `.claude/rules/mirror-procedure-discipline.md`'s classify-every-
      divergence discipline, not a mechanical check; mark manual-pending if
      dispatched unattended.
- [ ] `bash evals/lint-ultra-gate.sh` → exits 0
- [ ] `bash evals/lint-skill-size-gate.sh` → exits 0
