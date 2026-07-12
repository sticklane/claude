# Task 03: Depth-guard doctrine, hook if feasible

Status: pending
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

- [ ] `sed -n '/## Dispatch authoring/,/^## /p' .claude/rules/token-discipline.md | grep -ci 'untyped'` → ≥ 1
- [ ] Either `bash hooks/untyped-dispatch-warn/test.sh` → passes (warn case + both silent cases), or `sed -n '/## Dispatch authoring/,/^## /p' .claude/rules/token-discipline.md | grep -ci 'hook'` → ≥ 1 (limitation recorded)
- [ ] If the hook shipped: mirror updated and `git show $(git merge-base HEAD main):.claude-plugin/plugin.json | grep '"version"'` differs from the working-tree value; `claude plugin validate .` → passes
