# Task 03: Antipattern guards, antigravity mirrors, research record

Status: in-progress
Depends on: 01, 02
Budget: 50 turns
Spec: ../SPEC.md (requirements R5, R6, R7, R8, R9, R10)

## Goal

The vendor-named antipatterns get guards: /breakdown's parallelization
gains the "decision coupling" test and an explicit must-NOT-touch
boundary sentence, /parallel cites the test in one line,
token-discipline gains the "scale the fleet" rule with the ~15× cost
named, and /critique's description routes neighbors away. The
antigravity port mirrors the guards and the precedence block, its README
records the no-chaining divergence, and docs/external-playbooks.md gains
the "Skill chaining" and "Antipatterns" research entries.

## Touch

- `.claude/skills/breakdown/SKILL.md` (Parallelization step + task
  template `## Touch` text). Cross-spec: also edited by
  context-management, review-fixes — see specs/QUEUE.md; also edited by
  task 02 in this spec (hence the dependency)
- `.claude/skills/parallel/SKILL.md` (independence check, one line).
  Cross-spec: also edited by review-fixes — see specs/QUEUE.md
- `.claude/rules/token-discipline.md` (delegation section). Cross-spec:
  also edited by context-management, model-agnostic — see specs/QUEUE.md;
  also edited by task 01 in this spec
- `.claude/skills/critique/SKILL.md` (frontmatter description only)
- `docs/external-playbooks.md`. Cross-spec: also edited by all feature
  queues — see specs/QUEUE.md
- `antigravity/AGENTS.md` (Precedence mirror + token-discipline
  section), `antigravity/.agents/skills/breakdown/SKILL.md`,
  `antigravity/.agents/workflows/parallel.md`, `antigravity/README.md`
  (mapping-table row) — ag files follow their sources

Must NOT touch: any other skill's description (R8: no other
descriptions change); `.claude/skills/idea/SKILL.md`; `CLAUDE.md`;
`plugin.json` (see note below). No port of the chain to antigravity.

## Steps

1. R5: add the "decision coupling" test to /breakdown's Parallelization
   step — tasks are parallel-safe only if disjoint in Touch AND free of
   shared undecided design (naming, schema, interface, architectural
   choices the spec leaves open; if two tasks would each pick, the
   choice moves into the spec or the tasks serialize). Cite the same
   test in one line in /parallel's independence check.
2. R6: extend /breakdown's task-template `## Touch` text with the
   boundary sentence: list adjacent files/modules the task must NOT
   touch when overlap with a sibling is plausible ("Anything else is
   scope creep" stays).
3. R7: add the scaling rule to token-discipline's delegation section,
   containing "scale the fleet": one worker default; parallel workers
   only for genuinely divisible groups (the decision-coupling test);
   fleet size follows the task map, never a default maximum — naming
   the ~15× token cost of multi-agent work as the reason.
4. R8: add one routing clause to /critique's description: working-diff
   bug hunts → /code-review; GitHub PRs → /review; exercising runtime
   behavior → the `verifier` agent. Then check the CLAUDE.md trigger
   test: fires on its own phrases, not neighbors'.
5. R9: add to docs/external-playbooks.md a "Skill chaining" entry
   (Skill-tool invocation semantics; context-fork and Stop-hook
   primitives as available-but-unadopted; ADK/OpenAI chaining models one
   line each) and an "Antipatterns" entry (seven findings with sources,
   mapped to R4–R8 or already-covered; Cognition attributed as
   non-vendor; Agents Companion flagged as secondary-verified).
6. R10 mirrors: `## Precedence` block into antigravity/AGENTS.md
   (mirroring task 01's R4 text); R5+R6 into the antigravity breakdown
   skill; R5's one-line citation into the antigravity parallel workflow;
   R7's scaling rule into AGENTS.md's token-discipline section. Add one
   row to antigravity/README.md's mapping table: workflows are
   human-launched in the Agent Manager, so the port keeps printed
   pointers — no port of the chain.
7. R11 note: do NOT bump plugin.json — owned by specs/review-fixes
   global task 99; record the pre-implementation version in evidence.

## Acceptance

- [ ] `grep -q "decision coupling" .claude/skills/breakdown/SKILL.md && grep -q "decision coupling" .claude/skills/parallel/SKILL.md` (R5, from SPEC)
- [ ] `grep -qi "must NOT touch" .claude/skills/breakdown/SKILL.md` (R6, from SPEC)
- [ ] `grep -q "scale the fleet" .claude/rules/token-discipline.md && grep -q "15×\|15x" .claude/rules/token-discipline.md` (R7, from SPEC)
- [ ] `grep -q "code-review" .claude/skills/critique/SKILL.md` (R8, from SPEC; also verify the description still passes the trigger test — fires on its own phrases, not neighbors')
- [ ] `grep -qi "skill chaining" docs/external-playbooks.md && grep -qi "antipattern" docs/external-playbooks.md` (R9, from SPEC)
- [ ] `grep -q "## Precedence" antigravity/AGENTS.md && grep -q "decision coupling" antigravity/.agents/skills/breakdown/SKILL.md && grep -qi "must NOT touch" antigravity/.agents/skills/breakdown/SKILL.md && grep -q "decision coupling" antigravity/.agents/workflows/parallel.md && grep -q "scale the fleet" antigravity/AGENTS.md && grep -qi "human-launched" antigravity/README.md` (R10, from SPEC, complete)
