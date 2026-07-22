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
rewritten so its PROCEDURE authors host-language scripts under
`scripts/workflows/` — including the tier-selection teaching
(mechanical stages dispatch scout-tier, judgment stages
session/deep, per DW9's amended defaults) — with the native
Workflow-tool JS path demoted to a documented DW12 accelerator
alternative, never the default; the bundled `deep-research.js` gains
a header note naming it a DW12-boundary accelerator; and the fleet
skill directs run-shaped fan-out at `agentic dispatch`/`run` with
concurrency numbers deferred to the profile caps, keeping fleet as
the viewer for Agent-tool work and `agentic watch` for runs.

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
- [ ] `bash -c 'first=$(grep -n "scripts/workflows\|\.claude/workflows" .claude/skills/workflow-author/SKILL.md | head -1); echo "$first" | grep -c "scripts/workflows"'` → `1` (the FIRST workflow-location the skill's procedure names is the host-language dir — ordering, not phrase presence; the native path may appear only later, as the accelerator)
- [ ] `grep -c "dispatch\|agentic run" .claude/skills/fleet/SKILL.md` → ≥ 1 AND `grep -c "agentic watch" .claude/skills/fleet/SKILL.md` → ≥ 1 (fleet directs run-shaped fan-out at the CLI and names the run viewer)
- [ ] `bash scripts/check.sh` → green

Depth ceiling: L1 for the skill-teaching criteria — ordering and
content-coverage greps bound what a command can verify about prose
that instructs a model; the behavioral complement is a
workflow-author eval scenario asserting the authored artifact is a
host-language script under scripts/workflows/, named here as the
follow-up eval addition rather than pretended into a grep.

Depth ceiling: L1 for the doc-currency criteria — the behavioral
complement is the verifier running each documented command verbatim.
