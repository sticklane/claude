# Spec: Routing + drain-merge hardening (critic findings)

Status: ready for /breakdown
Tier: quick-fix
Effort: ~30 min
Rollback: single revert

**Context:** Critic review (opus, 2026-07-04) of branch
`claude/model-routing-native-config-tgn9d7` returned NOT READY with four
findings and one flagged follow-up. This spec fixes all five. Findings
F1–F5 below map 1:1 to the critic's report.

## Problem

The model-routing spec and the /parallel→/drain merge shipped with gaps:
the headless fallback never got the routing ladder, one antigravity file
still cites the deleted parallel workflow, drain's group mode is ambiguous
about status-flip/commit sequencing, a push-guard parenthetical cites the
retired skill, and group mode silently dropped /parallel's stop-on-gate-
failure behavior.

## Changes

**F1 — Headless fallback joins the routing ladder.** The headless worker
template (`.claude/skills/drain/reference.md` headless section, mirrored
in `runtimes/claude-code.md` "Headless") gains `--model <alias>`, threaded
with the same three rungs as Task-tool dispatch: `sonnet` attempt 1,
`opus` relaunch, `fable` tournament. Update the one-line scope note in
`.claude/rules/token-discipline.md` ("headless fallback templates run
their profile's default in v1") to match: pins now pass through `--model`
on the headless path too.

**F2 — Antigravity autopilot stale reference.** Reword
`antigravity/.agents/workflows/autopilot.md`'s "build prompt from the
parallel workflow" to point at the build workflow directly (matching the
Claude-side autopilot wording).

**F3 — Group dispatch sequencing made explicit.** In drain SKILL.md's
group throughput mode (and the antigravity drain mirror): flip every
member's `Status: in-progress` and commit them in ONE commit; cut all
member worktrees from that commit; launch all workers in one message;
then wait for all completions — collecting each verdict via step 3 as it
arrives — before dispatching anything else. Retitle step 2 so the heading
no longer says "one worker" while describing group dispatch.

**F4 — Push-guard parenthetical.** "(canonical; build and parallel cite
this)" → build cites it; drain's own group mode follows it. Both the
Claude skill and the antigravity drain mirror.

**F5 — Restore the gate-failure stop in group mode.** The retired
/parallel stopped on a merge conflict OR a post-merge gate failure; the
folded text only carved out merge conflicts. Extend the group-mode
carve-out: a post-merge gate failure during group integration also stops
the remaining merges and reports (interaction effects between members are
indistinguishable from the task's own failure at that point; a fresh
attempt can't fix an interaction). Claude skill + antigravity mirror.

## Non-goals

No new routing rungs, no changes to sequential drain semantics, no
gemini-cli headless template change beyond what its profile already
documents (its Role pins table already carries the tier mapping; its
`-m` flag is already documented in the profile).

## Verification

```yaml
verify:
  - run: "grep -q -- '--model' .claude/skills/drain/reference.md && grep -q -- '--model <' runtimes/claude-code.md"
    expect: exit0 # F1: headless template carries a model flag
  - run: "grep -q 'model' .claude/rules/token-discipline.md && ! grep -q 'default in v1' .claude/rules/token-discipline.md"
    expect: exit0 # F1: v1 scope note updated
  - run: "! grep -q 'parallel workflow' antigravity/.agents/workflows/autopilot.md"
    expect: exit0 # F2
  - run: "grep -q 'one commit' .claude/skills/drain/SKILL.md && grep -q 'one commit' antigravity/.agents/workflows/drain.md"
    expect: exit0 # F3
  - run: "! grep -rq 'build and parallel cite this' .claude antigravity"
    expect: exit0 # F4
  - run: "grep -q 'post-merge gate failure' .claude/skills/drain/SKILL.md && grep -q 'post-merge gate failure' antigravity/.agents/workflows/drain.md"
    expect: exit0 # F5
  - run: "bash evals/lint-ultra-gate.sh && ./bin/check-token-discipline && ./bin/check-agent-model-pins"
    expect: exit0 # existing gates still green
  - run: "bash tests/test_check_token_discipline.sh"
    expect: exit0
```

## Notes

All five findings touch drain's files or their mirrors; F2 is the only
independent file. A critic re-run on the amended diff closes the loop
(critique skill step 4).

## Parallelization

All three tasks are one parallel group: disjoint `Touch` lists
(01: drain/reference.md + runtimes/claude-code.md + token-discipline rule;
02: drain/SKILL.md + antigravity drain workflow + plugin.json;
03: antigravity autopilot workflow), no `Depends on` edges, and no shared
undecided design choice — the spec fixes every wording decision (the
decision-coupling test passes). Sequential /build order 01 → 02 → 03 is
equally valid; each task leaves the tree green independently.
