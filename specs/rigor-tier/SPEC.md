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
- `Rigor: prototype` — /build and /drain workers skip the TDD red-first
  discipline and the verifier dispatch for tasks carrying it; they keep
  commit hygiene, the acceptance-command check (the task's own runnable
  criteria still must pass), and the untrusted-data rules. Workers state
  in their close-out that prototype gates applied.

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
- R4: /build and /drain worker instructions scale gates down for
  `Rigor: prototype` exactly as the Solution defines — skip TDD red-first
  and verifier dispatch; keep commit discipline and acceptance commands.
- R5: /list-specs displays the tier per spec.
- R6: The promotion rule appears in the skill text that consumes the
  header (/build and /drain), not only in this spec.
- R7: quality-discipline.md gains one line scoping its TDD mandate to
  production-rigor work, citing this mechanism.
- R8: Antigravity mirrors (`antigravity/.agents/workflows/{idea,breakdown,
build,drain}.md` and the ported skills they reference) receive the
  equivalent changes in the same commit, and `.claude-plugin/plugin.json`
  is bumped; some task's `Touch:` must list these paths (CLAUDE.md's
  mirroring convention).

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
- [ ] `grep -rql "Rigor" antigravity/.agents/ | grep -q .` and plugin.json version is higher than before (R8)
- [ ] Fresh-session test: /idea a throwaway-tool pitch, answer "prototype";
      the produced SPEC.md carries `Rigor: prototype` above its first `##`
      (manual, per CLAUDE.md's testing convention).

## Open questions

(none)
