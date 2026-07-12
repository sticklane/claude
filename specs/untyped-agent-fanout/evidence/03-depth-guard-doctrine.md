# Verification: 03-depth-guard-doctrine

Verdict: PASS

Branch: task/03-depth-guard-doctrine, HEAD dfd9179 ("docs: untyped-agent
no-nesting doctrine (untyped-agent-fanout R3)"), base 83d60e4.

## Criterion 1 — literal "untyped" in Dispatch authoring section

Command:
```
sed -n '/## Dispatch authoring/,/^## /p' .claude/rules/token-discipline.md | grep -ci 'untyped'
```
Output: `6` (≥ 1). PASS.

## Criterion 2 — hook OR limitation-note branch

Command A:
```
bash hooks/untyped-dispatch-warn/test.sh
```
`hooks/untyped-dispatch-warn/` does not exist (`ls hooks/` shows only
`session-refresh`; `test -d hooks/untyped-dispatch-warn` fails). Branch A
not taken — no hook shipped.

Command B:
```
sed -n '/## Dispatch authoring/,/^## /p' .claude/rules/token-discipline.md | grep -ci 'hook'
```
Output: `4` (≥ 1).

Genuine-limitation check: read the rule text. The new "no-nesting" bullet
ends with:

> **Feasibility, decided 2026-07-12 — doctrine-only, no hook:** a
> PreToolUse warn-hook on Agent calls was scoped and NOT shipped because
> the hook input schema exposes no dispatch-depth field and no reliable
> running-agent tier marker (`agent_type` surfaces only inside a subagent
> and is undocumented for the main session), so a correct
> untyped-under-untyped warn cannot be built from it; this stays a
> doctrine line, warn-only in spirit, until the hook API exposes caller
> type or depth.

This cites a specific, checkable technical reason (missing depth field,
undocumented main-session `agent_type`), not an incidental use of the word
"hook". PASS.

## Criterion 3 — no hook shipped ⇒ vacuous

`hooks/untyped-dispatch-warn/` confirmed absent (see above).
`.claude-plugin/plugin.json` version confirmed unchanged:
```
git show $(git merge-base HEAD main):.claude-plugin/plugin.json | grep '"version"'
  "version": "0.8.55",
grep '"version"' .claude-plugin/plugin.json
  "version": "0.8.55",
```
Identical — not bumped, consistent with a doctrine-only outcome.
`git diff 83d60e4..HEAD -- antigravity/ .claude-plugin/ hooks/` → empty (0
lines). Criterion vacuously satisfied. PASS.

## Additional checks requested

(a) Doctrine text uses literal "untyped" (6 hits, above) and cites the
SPEC's exact-match set verbatim:
```
`agent:claude` / `agent:agentic:claude` / `agent:general-purpose` /
`agent:agentic:general-purpose` (specs/untyped-agent-fanout/SPEC.md R4; ...)
```
Cross-checked against `specs/untyped-agent-fanout/SPEC.md` R4:
```
The untyped set is an EXACT-match enumeration — `agent:claude`,
`agent:agentic:claude`, `agent:general-purpose`,
`agent:agentic:general-purpose` — never a prefix match.
```
Same four identifiers, same semantics. PASS.

(b) Scope confinement:
```
git diff 83d60e4..HEAD --stat
 .claude/rules/token-discipline.md | 21 +++++++++++++++++++++
 1 file changed, 21 insertions(+)
```
Exactly one file changed, +21/-0. The task file
(`specs/untyped-agent-fanout/tasks/03-depth-guard-doctrine.md`) has NOT
been touched yet (`git diff 83d60e4..HEAD -- .../03-depth-guard-doctrine.md`
is empty) — close-out has not run. Per instructions this is not a failure;
reporting current state only. No scope creep found.

(c) Append-only task-file invariant: N/A at this point — the task file is
byte-identical to base (Status still reads `in-progress`, no acceptance
boxes ticked, no Decisions/evidence section added). Since close-out has not
run, there is nothing yet to violate the append-only invariant; this must
be re-checked once Status flips to `done`.

## Gates

No repo-wide `scripts/check.sh` run was required by this task's Acceptance
section beyond the three criteria above; none of the three criteria depend
on it. Not run (out of scope for this task's doctrine-only change, and no
code/tests were added).

## Scope-creep findings

None. Touch list allowed `.claude/rules/token-discipline.md,
hooks/untyped-dispatch-warn/, antigravity/, .claude-plugin/plugin.json`;
only the first was touched, consistent with the Touch note explaining the
latter three apply "ONLY if a hook ships."

## Summary

All three acceptance criteria PASS as literally written. The doctrine-only
branch was taken deliberately and is well-justified in the rule text
itself (specific hook-schema limitation cited, not hand-waved). Task file
close-out has not yet run (Status still `in-progress`) — re-verify the
append-only invariant once it does.
