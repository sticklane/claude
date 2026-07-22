# Task 08: bare-shell end-to-end, the example workflow, and docs

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 04, 05, 06, 07
Priority: P1
Budget: 28 turns
Spec: ../SPEC.md (statements 2, 8, 9, 10; DW1, DW8, DW12; RW-G)
Touch: scripts/workflows/, tests/test_agentic_dynamic_generic.sh, AGENTS.md, README.md, .claude/skills/workflow-author/, .claude/skills/fleet/SKILL.md, .claude/workflows/deep-research.js

## Goal

The whole surface proves itself end to end with no harness anywhere:
`tests/test_agentic_dynamic_generic.sh` runs a 3-dispatch fixture
workflow through `agentic run` in a bare shell (stub workers, PATH
restricted to system + agentic + bd), exits 0, and all three result
files exist and validate against their schemas. The first real saved
workflow lands in `scripts/workflows/` — a find-verify-synthesize
example that derives its work list from `agentic ctx tree --json`,
carries the determinism note in its header, and files kept findings
through the tracker bridge. AGENTS.md and README document the verbs,
the DW12 boundary (native ultracode only for runs that file nothing,
claim nothing, keep nothing), and the scheduling one-liner.

Skill consistency lands here too: the workflow-author skill is
rewritten to author host-language scripts under `scripts/workflows/`
(the native Workflow-tool JS path becomes its documented DW12
accelerator alternative, never the default); the bundled
`deep-research.js` gains a header note naming it a DW12-boundary
accelerator; and the fleet skill points at `agentic watch` for
run-shaped work so the two progress views name each other instead of
competing.

## Steps

1. Write the failing end-to-end test first (RW-G, result-file
   validation included).
2. Author the example workflow; run it against a fixture repo with
   stub workers; confirm its findings land `discovered-from` its run
   issue.
3. Update AGENTS.md (Map + Commands) and README; note the DW12
   boundary in the adapter docs.

## Acceptance

- [ ] `bash tests/test_agentic_dynamic_generic.sh` → prints `GENERIC OK`; exit 0 AND three schema-valid result files (RW-G)
- [ ] `bash -c 'head -20 scripts/workflows/*.sh | grep -c "determinism"'` → ≥ 1 (the example carries the replay-determinism note)
- [ ] `grep -c "agentic run" AGENTS.md README.md | grep -vc ":0"` → `2` (both docs document the verb)
- [ ] `grep -c "scripts/workflows" .claude/skills/workflow-author/SKILL.md` → ≥ 1 AND `grep -ci "accelerator" .claude/skills/workflow-author/SKILL.md` → ≥ 1 (the skill authors host-language scripts; native JS demoted to the DW12 alternative)
- [ ] `grep -c "agentic watch" .claude/skills/fleet/SKILL.md` → ≥ 1 (the two progress views cross-reference)
- [ ] `bash scripts/check.sh` → green

Depth ceiling: L1 for the doc-currency criteria — the behavioral
complement is the verifier running each documented command verbatim.
