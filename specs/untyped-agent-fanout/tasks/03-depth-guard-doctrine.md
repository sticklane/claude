# Task 03: Depth-guard doctrine, hook if feasible

Status: done
Depends on: ../../session-refresh-automation/tasks/01-wake-budget-doctrine.md
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R3)
Touch: .claude/rules/token-discipline.md, hooks/untyped-dispatch-warn/, antigravity/, .claude-plugin/plugin.json

## Goal

The "Dispatch authoring" section of token-discipline.md states: an
untyped agent (exact-match set per ../SPEC.md R4) must not spawn another
untyped agent without an explicit model override. Plus, IF a PreToolUse
hook on Agent calls can observe the running agent's own type or depth, a
warn-only hook under `hooks/untyped-dispatch-warn/` with a runnable test;
if not, a one-line limitation note beside the doctrine and no hook — the
task never stalls on the harness.

## Touch

The token-discipline.md collision with
`specs/session-refresh-automation/tasks/01-*` is expressed as the
cross-spec `Depends on:` path above (drain grammar per specs/QUEUE.md) —
this task admits only after that one lands, so one repo-wide drain
serializes them; its "Session refresh" subsection will already exist
when this task edits the same file. `antigravity/` and the plugin bump apply ONLY if a
hook ships (hooks are mirrored in Antigravity's JSON shape per
CLAUDE.md); a doctrine-only outcome touches just the rule file.

## Steps

1. Add the no-nesting line inside "## Dispatch authoring" using the
   literal word "untyped" and citing ../SPEC.md's exact-match set.
2. Feasibility check: inspect the hook API's PreToolUse input for agent
   type/depth visibility (harness docs / a disposable test hook). Decide
   hook vs limitation-note; record the decision in one sentence in the
   rule text.
3. If feasible: write the failing hook test first (untyped→untyped Agent
   input without model override → warning on stdout; typed target or
   explicit model → silent), then the hook; mirror + bump.

## Acceptance

- [x] `sed -n '/## Dispatch authoring/,/^## /p' .claude/rules/token-discipline.md | grep -ci 'untyped'` → ≥ 1 — verifier: → 6 (evidence/03-depth-guard-doctrine.md)
- [x] Either `bash hooks/untyped-dispatch-warn/test.sh` → passes (warn case + both silent cases), or `sed -n '/## Dispatch authoring/,/^## /p' .claude/rules/token-discipline.md | grep -ci 'hook'` → ≥ 1 (limitation recorded) — limitation path taken: → 4, genuine one-sentence feasibility limitation confirmed (evidence/03-depth-guard-doctrine.md)
- [x] If the hook shipped: mirror updated and `git show $(git merge-base HEAD main):.claude-plugin/plugin.json | grep '"version"'` differs from the working-tree value; `claude plugin validate .` → passes — vacuous: no hook shipped, plugin.json unchanged (0.8.55), no antigravity mirror touched (evidence/03-depth-guard-doctrine.md)

## Decisions

- R3 hook-vs-limitation feasibility: chose doctrine-only, no PreToolUse warn-hook. Default taken because the PreToolUse hook input schema exposes no dispatch-depth field and no reliable running-agent tier marker (`agent_type` surfaces only inside a subagent, undocumented for the main session), so a correct untyped-under-untyped warn cannot be built from it; R3's own clause says ship doctrine-only when the API cannot see type/depth. Reverse by adding `hooks/untyped-dispatch-warn/` with its test plus the antigravity mirror and a plugin.json bump if a future harness release exposes caller type or depth.
