# Deterministic task prioritization for the queue

## Problem

When several tasks are dispatchable at once, the toolkit has no rule
for which goes first. Drain's contract stops at eligibility — "a task
is dispatchable when `Status: pending` and every dependency is `done`"
(.claude/skills/drain/SKILL.md:28) — with no tie-break among
simultaneously-ready tasks; QUEUE.md's wave table is a human-curated
plan view that nothing enforces; task headers (Status, Depends on,
Budget, Spec) carry no priority. The cross-vendor research this spec
records in docs/external-playbooks.md (R4) found the industry converges
on exactly the mechanism we have — dependency graph → ready set →
waves (Kiro, Copilot fleet, ADK, Jules) — and universally leaves
within-ready-set ordering unspecified. The only vendor statements
beyond it: Anthropic's long-running-harness guidance ("choose the
highest-priority feature that's not yet done", one at a time, priority
pre-assigned) and OpenAI's PLANS.md pattern (proof-of-concept
milestones first — implicit risk-first ordering). So the gap is real,
the fix is small, and it must stay mechanical: dispatch ordering is
deterministic control flow, not model judgment.

## Solution

Four decisions, recommended options adopted (non-interactive fallback,
each reversible before implementation): (1) an OPTIONAL `Priority:`
header on task files — values `P0` (highest) through `P3`, absent
means `P2` — a single-line machine-readable header per the
context-management spec's header convention; (2) drain gains a
deterministic tie-break among dispatchable tasks: Priority first, then
unblocking-power (the count of still-pending tasks whose `Depends on:`
names this task — computable from headers, no judgment), then
lexicographic task-file path as the total-order backstop; (3)
/breakdown assigns priorities at decomposition with a four-line
rubric — P0 repairs or unblocks files other tasks edit, or proves the
spec's riskiest assumption (the OpenAI PoC-first finding, and exactly
the review-fixes-first rationale QUEUE.md already states as prose);
P1 sits on the longest remaining dependency chain; P2 default; P3
cleanup — and the human edits values freely afterward (Anthropic:
priority is pre-assigned, the agent just honors it); (4) QUEUE.md
stays the human plan view, unchanged — ordering state lives in task
headers (single source), and existing tasks are NOT backfilled
(absent = P2 keeps today's dependency-driven order intact). Marker
phrases ("Priority:", "tie-break", "unblocking-power") do not exist in
the implementation targets today, so the acceptance greps below cannot
pass vacuously.

## Requirements

- R1 (header convention): `/breakdown`'s task-file template gains a
  `Priority: P2` line among the header lines (Status, Depends on,
  Budget, Spec), with values P0–P3 and one comment line stating absent
  means P2. Single-line `Key: value` header above the first `##`,
  per the machine-state convention.
- R2 (drain tie-break): `.claude/skills/drain/SKILL.md`'s dispatch
  section gains one sentence containing "tie-break" and "Priority":
  when several tasks are dispatchable at once, dispatch lowest
  Priority value first (absent = P2), then greatest unblocking-power —
  the count of still-`pending` tasks whose `Depends on:` names this
  task, counted over the task files inventoried this run and resolving
  `Depends on:` exactly as the dispatchability check does (numbers
  within a spec, task-file-relative paths across specs) — then
  lexicographic task-file path. Deterministic and drain-computed; the
  model never reorders the queue mid-run. Sequential one-at-a-time
  dispatch stays the default (unchanged). Drain's inventory header
  list must include `Priority` — this spec already amended
  review-fixes 03 (which owns that list) and context-management 01
  (the CLAUDE.md machine-state bullet) to the five-field form, so
  whichever lands first, the contract agrees and review-fixes 99's
  acceptance sweep stays green.
- R3 (breakdown rubric): `.claude/skills/breakdown/SKILL.md`'s
  ordering step gains the four-line rubric containing "unblocking"
  and "P0": P0 = repairs/unblocks files other tasks edit, or proves
  the spec's riskiest assumption; P1 = on the longest remaining
  dependency chain; P2 = default; P3 = cleanup/nice-to-have. One
  sentence notes the human may re-prioritize by editing headers at
  any time.
- R4 (research record): `docs/external-playbooks.md` gains a "Task
  prioritization" entry containing "ready set": the convergence
  (dependency graph → ready set → waves: Kiro dependency-grouped
  waves, kiro.dev/docs/specs/best-practices; Copilot fleet
  wave-dispatch,
  github.blog/ai-and-ml/github-copilot/run-multiple-agents-at-once-with-fleet-in-copilot-cli/;
  ADK provides ordering mechanisms not heuristics,
  adk.dev/agents/workflow-agents/; Jules concurrency caps only, queue
  prioritization "planned", jules.google/docs/usage-limits/); the gap
  — no vendor publishes
  within-ready-set ranking, this toolkit's tie-break is ahead of
  published guidance; the two vendor signals adopted (Anthropic
  effective-harnesses "highest-priority not yet done, one at a time",
  anthropic.com/engineering/effective-harnesses-for-long-running-agents;
  OpenAI PLANS.md PoC-milestones-first as risk-first ordering,
  developers.openai.com/cookbook/articles/codex_exec_plans), with
  source links.
- R5 (mirrors): `antigravity/.agents/skills/breakdown/SKILL.md`
  mirrors R1+R3 (Priority line and rubric — the template lives in the
  SKILL; `antigravity/.agents/workflows/breakdown.md` is a 5-line
  shim and is NOT edited); `antigravity/.agents/workflows/drain.md`
  mirrors R2's tie-break sentence.
- R6 (versioning): the implementing change bumps `plugin.json`'s minor
  version by one from the value it finds, unless landing in a
  commit-set whose other specs already carry a single combined bump.

## Out of scope

- Backfilling `Priority:` onto the existing queue's task files —
  absent = P2 preserves today's dependency-driven order; humans add
  pins where they care.
- Value/cost scoring (WSJF and kin) — no vendor supports it, the
  inputs don't exist in task headers, and a wrong number is worse
  than a stable default.
- LLM-based dynamic reprioritization mid-drain — ordering is
  deterministic code by design (code-vs-LLM rung 0); the human edits
  headers between runs instead.
- Starvation aging — with P2 default and human-set pins, a queue this
  size cannot starve; revisit only with evidence.
- External issue trackers as the queue backend — removed by maintainer
  decision (recorded in docs/external-playbooks.md, Considered and
  rejected); work tracking stays in markdown task files.
- A `Priority` column in `specs/status.sh` — owned by the
  repo-orientation spec's dashboard if both land; noted at
  decomposition, not required here.

## Acceptance criteria

- [ ] `grep -q "Priority: P2" .claude/skills/breakdown/SKILL.md && grep -q "P0" .claude/skills/breakdown/SKILL.md && grep -qi "unblocking" .claude/skills/breakdown/SKILL.md` (R1+R3)
- [ ] `grep -q "tie-break" .claude/skills/drain/SKILL.md && grep -q "Priority" .claude/skills/drain/SKILL.md && grep -qi "unblocking" .claude/skills/drain/SKILL.md` (R2)
- [ ] `grep -qi "task prioritization" docs/external-playbooks.md && sed -n '/[Tt]ask prioritization/,/^## /p' docs/external-playbooks.md | grep -qi "ready set"` (R4, scoped to the entry)
- [ ] `grep -q "Priority" antigravity/.agents/skills/breakdown/SKILL.md && grep -qi "tie-break" antigravity/.agents/workflows/drain.md` (R5)
- [ ] plugin.json minor version strictly greater than the pre-implementation value, verified in the implementing task's evidence (R6)
- [ ] End to end: paper dry-run — three simultaneously dispatchable tasks: A (P1, 0 dependents), B (no Priority header, 3 pending dependents), C (no Priority header, 0 dependents, path sorts first). Order must be A (P1 beats default P2), then B (more unblocking-power), then C; and with A absent, B beats C despite C's earlier path (manual until the eval harness covers /drain).

## Open questions

(none — the four decisions are recorded in Solution; recommended
options adopted per the non-interactive fallback, reversible before
implementation.)

## Parallelization

Not yet decomposed — when /breakdown runs, its tasks join
[specs/QUEUE.md](../QUEUE.md) (update its count and wave table then).
Known serial chains to wire as `Depends on:` lines:
`.claude/skills/drain/SKILL.md` is also edited by review-fixes 02 and
03 — the R2 edit lands AFTER review-fixes 03 (whose five-field
inventory tuple this spec pre-amended); `.claude/skills/breakdown/
SKILL.md` by review-fixes 03 and context-management 01;
`antigravity/.agents/skills/breakdown/SKILL.md` (the R5 mirror) is
also edited by review-fixes 03 and context-management 01;
`docs/external-playbooks.md` appenders serialize (QUEUE.md); the
antigravity drain-workflow mirror rides the same chain as
tournament-votes R4 and review-fixes 02's mirror edits.
