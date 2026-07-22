# workflow-author: a concrete Workflow-vs-Agent-dispatch decision rule

Status: open
Priority: P2
Breakdown-ready: true

## Problem

`.claude/skills/workflow-author/SKILL.md`'s step 1 ("Qualify") is the only
gate on whether a repeated orchestration becomes an authored Workflow
script: "Confirm the orchestration is genuinely deterministic control flow
over subagents — loops, fan-out, staged verification. A procedure that is
judgment all the way down stays a skill; a single linear sequence stays
prose." That line distinguishes Workflow-worthy from prose-worthy, but not
Workflow-worthy from **plain Agent-tool dispatch worthy** — the actual
adjacent alternative every dispatch decision that reaches this step faces
(a human has already asked to "save this as a workflow" or equivalent by
the time Qualify runs, per the skill's own trigger phrases, so Qualify's
real job is judging whether that ask targets a standalone artifact or
control flow that belongs inside an existing skill), since `/drain`'s own
tournament dispatch (three concurrent
`implementation-worker` candidates, majority-PASS verifier votes, a
mechanical rank) is itself loop-shaped, multi-agent, fan-out-then-reduce,
and staged-verified — structurally the same shape as this skill's own
`tournament.js` template (`reference.md`'s "Template: tournament.js": a
`parallel()` build fan-out, per-item verify, then a `rank` stage the
file's own comment calls "a true cross-item barrier") — yet drain's
tournament stays plain sequential `Agent`-tool calls, never an authored
Workflow. A structural test alone (fan-out width, barrier count, schema
count) cannot separate these two: they have the *same* barriers, the
*same* schema-typed stages, and would count identically under any purely
structural rule. What actually differs is not their shape but their
**invocation context**.

## Solution

State the qualify test on the axis that actually distinguishes the two
cases, with the structural check kept as a secondary filter rather than
the primary gate:

1. **Primary — invocation context.** Is the orchestration meant to be its
   own standalone artifact — something a human invokes by name, or under
   the ultracode opt-in, repeatably across sessions, independent of any
   particular skill's run? Author it as a Workflow. Or is it control flow
   that already lives inside another skill's own procedure, dispatched as
   one internal step of that skill's own already-active, single-writer
   loop (drain's tournament dispatch is the canonical case — it runs
   *inside* drain's own step 3, sharing drain's task-state writes;
   splitting it into a separately-invoked Workflow artifact would
   fragment drain's single-writer contract across two artifacts for no
   benefit)? Stays plain `Agent`-tool dispatch inside that skill's own
   procedure, regardless of its internal fan-out/barrier/verify shape.
   `tournament.js` and drain's tournament are the worked example: same
   shape, opposite sides, because one is authored for a human to reach
   for on its own and the other is dispatched from inside drain's
   existing loop.
2. **Secondary — genuine orchestration shape.** Even a standalone,
   human-named routine only earns a Workflow's authoring overhead when it
   has at least one real data-dependent barrier — a stage that cannot
   start without the merged or reduced output of a prior fan-out (not
   merely "runs after" it). A single linear one-shot task stays prose or
   direct dispatch even when asked to be "saved as a workflow" — this is
   unchanged from the existing "single linear sequence stays prose" line
   and is kept, not replaced.

This stays inside the existing "first ~30 lines carry execution-critical
contracts" convention (step 1 already sits at line 21).

## Requirements

- R1: `workflow-author/SKILL.md`'s step 1 ("Qualify") states the
  invocation-context test as the primary gate (standalone/human-named/
  repeatable-across-sessions ⇒ author a Workflow; embedded inside another
  skill's own already-active procedure ⇒ stays that skill's plain
  `Agent`-tool dispatch), explicitly reconciling `tournament.js` and
  drain's tournament dispatch as sharing the same fan-out-then-reduce
  shape but landing on opposite sides because of invocation context, not
  barrier count. It keeps the secondary "at least one genuine
  data-dependent barrier" filter and the existing
  deterministic-vs-judgment / single-linear-sequence-stays-prose sentences
  unchanged.
- R2: The extension stays inside step 1's own paragraph or an immediately
  adjacent bullet under it — no new top-level `##` section. The file's
  `## `-heading count stays at its current value (4) after this edit.

## Out of scope

- Retrofitting the decision rule into `token-discipline.md`'s own
  "Freehand fan-out" or "Dispatch authoring" sections — this spec scopes
  the rule to the one place that actually decides "author a Workflow or
  not" (`workflow-author`'s Qualify step); a doctrine-file cross-reference
  is a reasonable follow-up, not required here.
- Any change to `reference.md`'s templates, the `tournament.js` /
  `queue-wave.js` code, or the Stage tiering / Doctrine guards sections —
  unaffected by this spec.
- A precise, general definition of "already-active loop" beyond the
  drain-tournament worked example — future ambiguous cases are resolved
  by analogy to that example, not by a formal taxonomy this spec does not
  attempt.

## Acceptance criteria

All greps below are scoped to step 1's own text (`awk '/^1\. \*\*Qualify/{f=1}
/^2\. \*\*Write the script/{f=0} f' .claude/skills/workflow-author/SKILL.md`) —
confirmed absent from that scope today (`grep -c` → 0 for each), so a pass
means the new content actually landed inside step 1, not that the phrase
already existed elsewhere in the file (e.g. "repeatable" and "tournament"
both already appear outside step 1, in the frontmatter description and the
reference.md pointer respectively — an unscoped grep would pass vacuously).

- [ ] `awk '/^1\. \*\*Qualify/{f=1} /^2\. \*\*Write the script/{f=0} f' .claude/skills/workflow-author/SKILL.md | grep -qiE 'embedded|already[- ]active|already[- ]running'` — the embedded-in-another-skill's-loop case is named inside step 1
- [ ] `awk '/^1\. \*\*Qualify/{f=1} /^2\. \*\*Write the script/{f=0} f' .claude/skills/workflow-author/SKILL.md | grep -qiE 'standalone|repeatable across'` — the standalone/human-named case is named inside step 1
- [ ] `awk '/^1\. \*\*Qualify/{f=1} /^2\. \*\*Write the script/{f=0} f' .claude/skills/workflow-author/SKILL.md | grep -qi 'tournament'` — the worked example (tournament.js vs. drain's tournament) is present inside step 1, not just an abstract rule
- [ ] `test $(grep -c '^## ' .claude/skills/workflow-author/SKILL.md) -eq 4` — no new top-level section added (R2)
- [ ] `awk '/^1\. \*\*Qualify/{f=1} /^2\. \*\*Write the script/{f=0} f' .claude/skills/workflow-author/SKILL.md | grep -qiE 'data-dependent|barrier'` — the secondary "at least one genuine data-dependent barrier" filter (Solution point 2) actually landed inside step 1, not just the primary invocation-context test; without this check a worker could satisfy every other criterion while dropping this half of R1's two-pillar requirement
- [ ] MANUAL: the new text explicitly states that `tournament.js` and
  drain's tournament dispatch share the same barrier/schema shape and are
  separated by invocation context, not structure — a reviewer reading the
  Qualify step should be able to explain why the two land differently
  without re-deriving it
- [ ] MANUAL: the new sentence(s) sit inside or immediately after step 1
  ("Qualify"), before step 2 ("Write the script") begins — confirm by line
  order, not just presence

## Parallelization

Single requirement, single file, single task — no parallelization needed.
