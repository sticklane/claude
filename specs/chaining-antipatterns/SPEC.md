# Skill self-chaining and vendor antipattern guards

## Problem

Two research threads (recorded by this spec in docs/external-playbooks.md).
First: Claude Code has merged commands into skills and made the Skill tool
model-invocable by default — a finishing skill can now invoke the next
pipeline stage itself, while `disable-model-invocation: true` still hard
removes human-gated skills from the model's reach. Our pipeline still
chains by prose pointers a human must act on: this session hand-drove the
idea→critique→breakdown seam five times. Second: vendor-named antipatterns
we don't yet guard — dispersed decision-making across parallel workers
(Cognition's Flappy-Bird-vs-Mario failure), vague delegation producing
duplicate work, effort-complexity mismatch (~15× token multi-agent cost on
barely-parallel work), contradictory instructions across our stacked
prompt sources with no precedence order, and overlapping trigger surfaces
among critique/code-review/review/verify.

## Solution

Four decisions, recommended options adopted (interview picker failed 3/3
this session; non-interactive fallback, reversible): (1) self-chaining is
allowed only between light artifact stages — /idea, once its spec is
critic-READY, announces and invokes /breakdown via the Skill tool unless
the user asked for spec-only; gated stages (/build, /parallel, /autopilot,
/drain, /evals) are never chained, and one canonical explanation of the
gating semantics lives in CLAUDE.md's conventions, cited by skills; (2)
an instruction-precedence block lives in CLAUDE.md; (3) trigger-surface
disambiguation is done in the critique skill's description only; (4)
/breakdown's parallelization gains a decision-coupling test beyond
disjoint Touch. Marker phrases ("self-chain", "decision coupling",
"## Precedence", "Next stage:") do not exist in the repo today.

## Requirements

- R1 (chaining semantics, canonical statement): CLAUDE.md's authoring
  conventions gain a bullet containing the word "self-chain": skills may
  invoke the next pipeline stage via the Skill tool only when (a) the
  produced artifact has passed its adversarial gate (critic READY), (b)
  the target skill is model-invocable (never `disable-model-invocation`
  targets — the flag removes them from the model's reach by design), and
  (c) the user has not scoped the request to the current stage. The
  invocation is announced in one line before it happens.
- R2 (idea→breakdown chain): `.claude/skills/idea/SKILL.md` step 5
  changes from pointer-only to a "Next stage:" contract: after READY,
  announce and invoke `/breakdown` on the spec via the Skill tool per
  R1's conditions, falling back to today's printed pointer when the
  conditions fail (spec-only request, non-interactive doubt, or
  /design needed first — /design open choices still stop the chain).
  `.claude/skills/breakdown/SKILL.md`'s hand-off gains one sentence: its
  next stages are launch-gated, so it always ends with the printed
  pointer, citing R1's CLAUDE.md bullet rather than restating it.
- R3 (every artifact skill states Next): the artifact-location
  convention in CLAUDE.md is extended: the closing line of an
  artifact-producing skill is a `Next stage:` line naming the next skill
  and the artifact path, marked either "(self-chains per conventions)"
  or "(human-launched)". The skills that produce pipeline artifacts
  (idea, design, breakdown, gate, onboard, distill, handoff, evals)
  comply.
- R4 (precedence): CLAUDE.md gains a `## Precedence` block (≤6 lines):
  when assembled instructions conflict, the order is — the user's live
  request; the executing task file plus its `## Answers`; the SKILL.md
  being executed; `.claude/rules/`; CLAUDE.md conventions; README/docs.
  Conflicts an agent cannot resolve by this order are surfaced, not
  guessed (consistent with the untrusted-data rule's authority list,
  which governs what binds at all; this block orders the legitimate
  sources).
- R5 (dispersed decisions): `.claude/skills/breakdown/SKILL.md`'s
  Parallelization step gains the "decision coupling" test: tasks are
  parallel-safe only if disjoint in Touch AND free of shared undecided
  design (naming, schema, interface, or architectural choices the spec
  leaves open — if two tasks would each pick, the choice moves into the
  spec or the tasks serialize). `.claude/skills/parallel/SKILL.md`'s
  independence check cites the same test in one line.
- R6 (vague-delegation boundaries): /breakdown's task template `## Touch`
  section text is extended with an explicit boundary sentence: list
  adjacent files/modules the task must NOT touch when overlap with a
  sibling task is plausible ("Anything else is scope creep" stays; the
  addition makes the boundary explicit where collision risk exists).
- R7 (effort-complexity scaling): `.claude/rules/token-discipline.md`'s
  delegation section gains a scaling rule containing the phrase
  "scale the fleet": one worker is the default; parallel workers only
  for genuinely divisible groups (the decision-coupling test); fleet
  size follows the task map, never a default maximum — with the ~15×
  token cost of multi-agent work named as the reason.
- R8 (trigger disambiguation): `.claude/skills/critique/SKILL.md`'s
  description gains one clause routing neighbors away: working-diff bug
  hunts → /code-review; GitHub PRs → /review; runtime behavior → /verify.
  No other skill descriptions change.
- R9 (research record): `docs/external-playbooks.md` gains a "Skill
  chaining" entry (the Skill-tool invocation semantics, context-fork and
  Stop-hook primitives recorded as available-but-unadopted, ADK/OpenAI
  chaining models one line each) and an "Antipatterns" entry (the seven
  findings with sources, mapped to R4–R8 or to already-covered items;
  Cognition attributed as non-vendor; Agents Companion flagged as
  secondary-verified).
- R10 (mirrors): `antigravity/AGENTS.md` mirrors R4's precedence block;
  the antigravity breakdown skill mirrors R5/R6; the antigravity parallel
  workflow mirrors R5's one-line citation and R7's scaling rule lands in
  AGENTS.md's token-discipline section. Chaining (R1–R3) is documented
  as a divergence in `antigravity/README.md`'s mapping table: Antigravity
  workflows are human-launched in the Agent Manager, so the port keeps
  printed pointers — one row, no port of the chain.
- R11 (versioning): the implementing change bumps `plugin.json`'s minor
  version by one from the value it finds, unless landing in a commit-set
  whose other specs already carry a single combined bump.

## Out of scope

- Chaining into or out of gated stages (/build, /parallel, /autopilot,
  /drain, /evals launch human-only, unchanged).
- Adopting `context: fork` / `agent:` frontmatter or Stop-hook chain
  enforcement — recorded in R9 as available primitives; each is its own
  future spec if wanted.
- Consolidating or renaming any skill (tool-overlap guidance lands as
  description routing only, per decision 3).
- Numeric tool-call budgets (owned by specs/context-management R5) and
  long-drain handoff discipline (already in /drain).
- ADK workflow-agents or OpenAI handoff mechanics (recorded only).

## Acceptance criteria

- [ ] `grep -q "self-chain" CLAUDE.md` (R1)
- [ ] `grep -q "Next stage:" .claude/skills/idea/SKILL.md && grep -qi "Skill tool" .claude/skills/idea/SKILL.md` (R2)
- [ ] `grep -qi "launch-gated\|human-launched" .claude/skills/breakdown/SKILL.md` (R2)
- [ ] `test "$(grep -l 'Next stage:' .claude/skills/*/SKILL.md | wc -l)" -ge 8` (R3)
- [ ] `grep -q "^## Precedence" CLAUDE.md && test "$(wc -l < CLAUDE.md)" -le 200` (R4)
- [ ] `grep -q "decision coupling" .claude/skills/breakdown/SKILL.md && grep -q "decision coupling" .claude/skills/parallel/SKILL.md` (R5)
- [ ] `grep -qi "must NOT touch" .claude/skills/breakdown/SKILL.md` (R6)
- [ ] `grep -q "scale the fleet" .claude/rules/token-discipline.md && grep -q "15×\|15x" .claude/rules/token-discipline.md` (R7)
- [ ] `grep -q "code-review" .claude/skills/critique/SKILL.md` (R8)
- [ ] `grep -qi "skill chaining" docs/external-playbooks.md && grep -qi "antipattern" docs/external-playbooks.md` (R9)
- [ ] `grep -q "## Precedence" antigravity/AGENTS.md && grep -q "decision coupling" antigravity/.agents/skills/breakdown/SKILL.md && grep -q "scale the fleet" antigravity/AGENTS.md && grep -qi "human-launched" antigravity/README.md` (R10)
- [ ] plugin.json minor version strictly greater than the pre-implementation value, verified in the implementing task's evidence (R11)
- [ ] End to end: in a fresh session, run /idea on a small toy feature and answer its interview; after the critic returns READY, the session announces and invokes /breakdown without a human typing it, task files appear under the spec's directory, and the session then STOPS with printed pointers to the gated stages (manual until the eval harness covers /idea).

## Open questions

(none — the four decisions are recorded in Solution; recommended options
adopted per the non-interactive fallback, reversible before
implementation.)
