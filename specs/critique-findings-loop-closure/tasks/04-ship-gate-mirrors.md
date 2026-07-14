# Task 04: Ship gate — mirrors and plugin version bump (R8)

Status: in-progress
Depends on: 01, 02, 03
Priority: P1
Budget: 14 turns
Spec: ../SPEC.md (requirement R8)
Touch: antigravity/.agents/workflows/critique.md, antigravity/.agents/workflows/drain.md, codex/.agents/skills/drain/SKILL.md, .claude-plugin/plugin.json

## Goal

Every skill-body change tasks 01-03 landed in `.claude/skills/critique/
SKILL.md` and `.claude/skills/drain/{SKILL.md,reference.md}` is reflected
in this repo's mirrors, and `.claude-plugin/plugin.json`'s version is
bumped once for the whole spec. This is the closing task that carries the
mirror + version-bump obligation CLAUDE.md's authoring conventions assign
to "typically one closing task" rather than splitting it across 01-03.

Per this spec's "Design decision" (R8), no task in this spec touches
`.claude/agents/critic.md` — the MECHANICAL/JUDGMENT split is a
`/critique`-side heuristic, not critic-authored metadata — so
`.claude/agents/critic.md` and its `antigravity/.agents/skills/critic/`
mirror are out of scope here.

## Touch

`antigravity/.agents/workflows/critique.md` (mirrors `.claude/skills/
critique/SKILL.md`'s R1 + R5 changes — the actual mirror path; `critique`
ports as a workflow, not a skills-dir entry). `antigravity/.agents/
workflows/drain.md` and `codex/.agents/skills/drain/SKILL.md` (both fold
in `.claude/skills/drain/SKILL.md` and `.claude/skills/drain/reference.md`
content today — mirror R2, R3, R4, R5, R6's drain-side changes into both).
`.claude-plugin/plugin.json` (version bump only — no `agents` or `skills`
array edit needed, since no new skill or agent was added).

## Steps

1. Confirm tasks 01, 02, and 03 have landed (their branches merged, or
   their diffs available) so the mirror content reflects the final state
   of `.claude/skills/critique/SKILL.md`, `.claude/skills/drain/SKILL.md`,
   and `.claude/skills/drain/reference.md`.
2. Read `.claude/skills/critique/SKILL.md`'s current state (post 01+02)
   and `antigravity/.agents/workflows/critique.md`. Port the MECHANICAL/
   JUDGMENT triage, the 2-4 cycle re-run bound, and the content-hash skip
   into the antigravity workflow's own prose (a paraphrased port per
   `docs/memory/workboard-mirror-verbatim.md` — most prose-skill mirrors
   are NOT byte-identical; write it in the workflow's own voice, don't
   diff-and-copy).
3. Read `.claude/skills/drain/SKILL.md` and `.claude/skills/drain/
reference.md`'s current state (post 02+03) and both
   `antigravity/.agents/workflows/drain.md` and `codex/.agents/skills/
drain/SKILL.md`. Port: the removed "cheap-before-expensive
   short-circuit" (delete the equivalent short-circuit text from both
   mirrors — confirmed present in both today, see Acceptance), and the new
   `Contradicts-premise` flag + blocked re-dispatch gate (R3/R4).
4. Run `bash evals/lint-ultra-gate.sh` and fix any marker-proximity
   violation the ported text introduces (antigravity/codex mirrors are not
   in the gate's `FILES` list today — confirm via `evals/lint-ultra-gate.sh`'s
   own file list before assuming mirrors need the marker too; if they're
   out of scope for the gate, this step only needs to keep the `.claude/`
   sources green, which 01-03 should have already left green).
5. Bump `.claude-plugin/plugin.json`'s `"version"` field by one patch
   level from its value at this task's own base commit (read the value
   fresh — a sibling task may have bumped it first; never hard-code
   "0.8.63 → 0.8.64" as a literal old/new pair in the diff).
6. Run `claude plugin validate .` and fix any reported issue.

## Acceptance

- [ ] `grep -c "Cheap-before-expensive short-circuit" antigravity/.agents/workflows/drain.md codex/.agents/skills/drain/SKILL.md | awk -F: '{s+=$2} END {print s}'`
      → 0 (today: 2 combined — confirmed present, one occurrence per file
      at `antigravity/.agents/workflows/drain.md:694` and
      `codex/.agents/skills/drain/SKILL.md:310` — this proves removal)
- [ ] `grep -c "Contradicts-premise" antigravity/.agents/workflows/drain.md codex/.agents/skills/drain/SKILL.md`
      → ≥ 1 combined
- [ ] `grep -c "MECHANICAL\|hash" antigravity/.agents/workflows/critique.md`
      → ≥ 1 (the triage and skip concepts landed in the mirror, in its own
      words)
- [ ] `bash evals/lint-ultra-gate.sh` → exits 0
- [ ] `claude plugin validate .` → exits 0
- [ ] `for t in tests/test_*.sh; do bash "$t"; done` → every test exits 0,
      in particular `tests/test_mirror_procedure_coverage.sh` (its
      manifest requires the verbatim phrase "Relay the verdict and
      findings verbatim" to survive in both `.claude/skills/critique/SKILL.md`
      and `antigravity/.agents/workflows/critique.md` — a paraphrased port
      of step 2 must keep that exact phrase, not just its meaning)
- [ ] Version bump check: `git show <this-task's-base-commit>:.claude-plugin/plugin.json | grep version`
      differs from the current `grep version .claude-plugin/plugin.json`
      (compare against the base commit's value, never a hard-coded
      "0.8.63" literal — a sibling task may have already bumped it)
