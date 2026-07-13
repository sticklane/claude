# Rigor tier: declared prototype-vs-production gates

Status: open
Priority: P2

## Problem

The pipeline applies production-grade rigor to every spec.
`.claude/rules/quality-discipline.md` mandates TDD unconditionally, and
/build always dispatches the verifier. The only riskiness scaling that
exists today gates _who_ runs work — /autopilot's autonomy-fit
classification and drain's unattended exclusions — never _how heavy the
gates are_. /idea right-sizes only at the threshold ("trivial diff → just
do it; mechanical transform → script"); once a spec exists, rigor is
uniform.

"The New SDLC With Vibe Coding" (Osmani/Saboo/Kartakis; adopted-practice
record in docs/external-playbooks.md) frames rigor as a declared spectrum:
prototype-grade work legitimately skips verification that production-grade
work must pay for, and the failure mode is not choosing a point on the
spectrum but _not declaring one_ — prototypes silently hardening into
production, or production specs paying prototype attention. The toolkit
has no way to declare the point.

## Solution

An optional single-line `Rigor:` header on SPEC.md and task files, read
the same way `Priority:` is (single-line `Key: value` above the first
`##`; absent = `production`):

- `Rigor: production` (or absent) — today's behavior, unchanged.
- `Rigor: prototype` — the verifier is skipped at whichever locus
  dispatches it. On the primary path that is the /build procedure
  itself (attended /build, and drain's attempt-1/relaunch workers, who
  run /build verbatim): the worker skips TDD red-first and its own
  verifier spawn, substituting a mechanical run of the task's
  acceptance commands, and reports DONE/BLOCKED on that signal — so
  drain's verdict-driven routing (relaunch, merge) works unchanged.
  Drain's orchestrator-owned mechanics are untouched on this path (the
  pre-merge whitelist diff and project gates are already mechanical).
  Only in the tournament path, where the orchestrator genuinely owns
  the per-candidate verifier runs, does the ORCHESTRATOR substitute
  acceptance-command runs for those verifier dispatches and rank on
  them. Kept in all cases: commit hygiene, the task's runnable
  acceptance criteria, and the untrusted-data rules. Workers state in
  their close-out that prototype gates applied.

Producers and consumers:

- /idea asks prototype-vs-production during the interview (one
  AskUserQuestion option set) and writes the header.
- /breakdown propagates the spec's `Rigor:` onto every task file it
  generates.
- /build and /drain read it per task and scale gates as above.
- /list-specs shows the tier in its table.

Promotion rule: prototype code never merges into a `Rigor: production`
spec's work without re-running the full gates — promoting a prototype
means flipping the header and treating the existing code as untested
input to a normal production task, not as done work.

## Requirements

- R1: `Rigor:` is an optional single-line header; absent means
  `production`; the only legal values are `prototype` and `production`
  (CLAUDE.md's machine-read-header convention).
- R2: /idea's interview offers the choice and writes the header into the
  spec it produces.
- R3: /breakdown copies the spec's effective `Rigor:` onto each generated
  task file.
- R4: Gate scaling lands at each gate's real locus — the /build
  procedure (attended, and inside drain's attempt-1/relaunch workers)
  skips TDD red-first and its own verifier spawn, substituting a
  mechanical acceptance-command run for the verdict it reports; drain's
  orchestrator substitutes the same only where it actually dispatches
  verifiers (the tournament's per-candidate runs); the orchestrator's
  mechanical pre-merge gate is unchanged. Commit discipline and
  acceptance commands stay mandatory.
- R5: /list-specs displays the tier per spec.
- R6: The promotion rule appears in the skill text that consumes the
  header (/build and /drain), not only in this spec.
- R7: quality-discipline.md gains one line scoping its TDD mandate to
  production-rigor work, citing this mechanism.
- R8: Mirrors receive the equivalent changes in the same commit: the
  idea, breakdown, build, and drain workflow files under
  `antigravity/.agents/workflows/`; the list-specs skill mirror at
  `antigravity/.agents/skills/list-specs/SKILL.md` (list-specs is ported
  under `antigravity/.agents/skills/`, not `workflows/`); and, per
  CLAUDE.md's codex mirroring convention (build and drain are real
  content there, not symlinks), `codex/.agents/skills/build/SKILL.md`
  and `codex/.agents/skills/drain/SKILL.md`. `.claude-plugin/plugin.json`
  is bumped from its current 0.8.58 to 0.8.59. Some task's `Touch:` must
  list all of these paths (CLAUDE.md's mirroring convention).

## Out of scope

- A third tier — two points on the spectrum, chosen explicitly, is the
  whole feature.
- Auto-detecting rigor from spec content — declaration is the point.
- Retroactively tagging existing specs — absent-means-production makes
  the rollout a no-op for them.

## Acceptance criteria

- [ ] `grep -q "Rigor:" .claude/skills/idea/SKILL.md && grep -q "Rigor:" .claude/skills/breakdown/SKILL.md` (R2, R3)
- [ ] `grep -q "Rigor:" .claude/skills/build/SKILL.md && grep -q "Rigor:" .claude/skills/drain/SKILL.md` (R4)
- [ ] `grep -qi "prototype" .claude/skills/list-specs/SKILL.md || grep -qi "Rigor" .claude/skills/list-specs/*` (R5)
- [ ] `grep -qi "rigor" .claude/rules/quality-discipline.md` (R7)
- [ ] `bash evals/lint-ultra-gate.sh` passes (CLAUDE.md's standalone ultra-path
      gate check, required before committing changes to any of
      idea/critique/drain/build SKILL.md; this spec's R2 and R4 edit
      idea/build/drain)
- [ ] `grep -qi "rigor" antigravity/.agents/workflows/idea.md && grep -qi "rigor" antigravity/.agents/workflows/breakdown.md && grep -qi "rigor" antigravity/.agents/workflows/build.md && grep -qi "rigor" antigravity/.agents/workflows/drain.md && grep -qi "rigor" antigravity/.agents/skills/list-specs/SKILL.md && grep -qi "rigor" codex/.agents/skills/build/SKILL.md && grep -qi "rigor" codex/.agents/skills/drain/SKILL.md && grep -q '"version": "0.8.59"' .claude-plugin/plugin.json` (R8)
- [ ] Fresh-session test: /idea a throwaway-tool pitch, answer "prototype";
      the produced SPEC.md carries `Rigor: prototype` above its first `##`
      (manual, per CLAUDE.md's testing convention).

## Open questions

(none)
