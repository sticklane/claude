# Verification: Task 02 — workflow-author both-or-neither stage-tiering rule

Verdict: PASS

## Criterion 1 — rule states mechanical=model+effort, judgment=omit model, one-line comment

Command: `grep -qi 'model' .claude/skills/workflow-author/SKILL.md`
Result: HIT (exit 0).

Evidence (SKILL.md, new "## Stage tiering" section, lines 42-60):
- Mechanical stages (search, fetch, extract, grep-like scouting, conformance
  checks) "pass BOTH `model` (a cheap-tier alias, e.g. `haiku`) AND
  `effort: 'low'`" — explicitly both-or-neither, with rationale that
  `effort` alone still bills the session's frontier model.
- Judgment stages (implementation, verification, judging, synthesis) "omit
  `model` deliberately so they inherit the session model — never pin them
  to a cheap tier."
- Requires "Give every `agent()` call a one-line comment naming which kind
  it is (e.g. `// Mechanical stage: pin model + effort` / `// Judgment
  stage: inherit session model`)."

STATUS: PASS.

## Criterion 2 — rule sits OUTSIDE the queue-state-scoped Doctrine guards block

Read full SKILL.md (lines 1-88). Section order:
- Line 19: `## Procedure` (steps 1-5, step 2 references "Stage tiering below
  — this applies to every script, queue-state or not")
- Line 42: `## Stage tiering` (new section, standalone, before Doctrine guards)
- Line 62: `## Doctrine guards` — preamble at line 64: "Every generated
  script that touches queue state carries all four" (scopes only the four
  bullets that follow: Single writer / BLOCKED routing / Budget / Untrusted
  returns).

"Stage tiering" is a sibling `##` section preceding "Doctrine guards", not
nested inside it, and its own text states it applies to "EVERY generated
script, not just queue-state ones." Confirmed NOT under the queue-state
preamble.

STATUS: PASS.

## Criterion 3 — example/template snippets updated, mechanical stage shows model+effort together

Command: `grep -riq 'effort' .claude/skills/workflow-author/`
Result: HIT (exit 0).

Command: `grep -n "model: 'haiku', effort: 'low'" .claude/skills/workflow-author/reference.md`
Result:
```
168:    model: 'haiku', effort: 'low',
```
This sits in the `queue-wave.js` template's inventory-scan `agent()` call,
annotated two lines above (166-167): "// Mechanical stage (grep-like
scouting): pin BOTH model and effort so it bills at cheap-tier rates, not
the session model's (Stage tiering)." — a mechanical stage carrying both
`model` and `effort` together, plus the required stage-kind comment.

reference.md also annotates two judgment stages (the `tournament.js` build
fan-out at line ~62-63, and the `queue-wave.js` per-task implementation
call) with comments explaining `model` is deliberately omitted.

STATUS: PASS.

## Scope discipline

Command: `git diff de56e03b4fd3d3398368c0a84dde981923886b30 --stat`
```
 .claude/skills/workflow-author/SKILL.md     | 23 ++++++++++++++++++++++-
 .claude/skills/workflow-author/reference.md |  7 +++++++
 2 files changed, 29 insertions(+), 1 deletion(-)
```
Only the two workflow-author skill files changed. No touch to
`.claude/workflows/deep-research.js` (task 01), `.claude-plugin/plugin.json`
(task 03), or any `antigravity/` files. `git status --porcelain` confirms
no other tracked/untracked changes in the working tree.

Task file `specs/workflow-model-pins/tasks/02-workflow-author-rule.md` is
unmodified (diff against base shows zero task-file changes) — Status still
reads `in-progress` and acceptance checkboxes are unticked, i.e. the worker
did not self-report completion. This is a process gap (task should be
updated to Status: done with checkboxes ticked once verified) but is not
itself an acceptance-criteria failure, and is not scope creep.

## Overall verdict: PASS

All three functional criteria verified by direct command execution and
file inspection; scope is clean (diff touches only the two intended
files); no evidence of overfitting (the rule and examples are general,
not keyed to any specific grep string beyond what the criteria require).
