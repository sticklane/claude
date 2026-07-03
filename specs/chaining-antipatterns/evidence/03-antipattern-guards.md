# Evidence: Task 03 — antipattern guards (chaining-antipatterns)

Verdict: PASS
Verified: 2026-07-03, branch task/03-antipattern-guards, worktree
/Users/sjaconette/claude/.claude/worktrees/agent-a242426d1d34d91fc
Verifier: independent (did not write the code); all commands run from the
worktree root.

## Acceptance criteria

### R5 — decision-coupling test in /breakdown, cited in /parallel
Command:
`grep -q "decision coupling" .claude/skills/breakdown/SKILL.md && grep -q "decision coupling" .claude/skills/parallel/SKILL.md`
Result: exit 0 (PASS).
Substance check (diff): breakdown step 5 now defines the test (disjoint
Touch AND no shared undecided design — naming/schema/interface/architecture;
open choice moves to spec or tasks serialize). parallel's independence check
adds one clause: "The group must also pass /breakdown's 'decision coupling'
test — members sharing an undecided design choice serialize even with
disjoint `Touch` lists."

### R6 — must-NOT-touch boundary sentence in task template
Command: `grep -qi "must NOT touch" .claude/skills/breakdown/SKILL.md`
Result: exit 0 (PASS).
Substance: template `## Touch` prose now reads "When overlap with a sibling
task is plausible, list the adjacent files/modules this task must NOT
touch." and retains "anything not listed there is scope creep."

### R7 — scale-the-fleet rule with ~15x cost
Command:
`grep -q "scale the fleet" .claude/rules/token-discipline.md && grep -q "15×\|15x" .claude/rules/token-discipline.md`
Result: exit 0 (PASS).
Substance: new Delegation-defaults bullet — one worker default; fleet only
for genuinely divisible groups (decision-coupling test); size by task map,
never a default maximum; "Multi-agent work costs ~15× the tokens of a
single session."

### R8 — critique description routing clause + trigger test
Command: `grep -q "code-review" .claude/skills/critique/SKILL.md`
Result: exit 0 (PASS).
Non-grep clause (inspected, git diff main -- .claude/skills/critique/SKILL.md):
- Only the frontmatter description changed; the skill body is untouched.
- Own trigger phrases retained verbatim as positives: "review this",
  "poke holes", "is this ready?".
- New clause is negation-framed: "Not the tool for working-diff bug hunts
  (/code-review), GitHub pull requests (/review), or exercising runtime
  behavior (the verifier agent)." Neighbor names appear only inside the
  "Not the tool for" negation; no neighbor trigger phrase is adopted as a
  positive.
- No other skill description changed: `git diff main --name-only` under
  .claude/skills/ shows only breakdown, critique, parallel; breakdown and
  parallel diffs are body-only (no frontmatter hunks). .claude/agents/ has
  no diff. /code-review and /review are not repo skills (Claude Code
  built-ins), so no in-repo description collision is possible.
- Note: the trigger test is behavioral per CLAUDE.md; verified here by
  static inspection of the description (phrases present/negated as above),
  not by live fresh-session triggering.

### R9 — external-playbooks research entries
Command:
`grep -qi "skill chaining" docs/external-playbooks.md && grep -qi "antipattern" docs/external-playbooks.md`
Result: exit 0 (PASS).
Substance (diff, +82 lines): "## Skill chaining" covers Skill-tool
invocation semantics (adopted), context-fork and Stop-hook chain
enforcement (both explicitly available-but-unadopted), ADK workflow agents
and OpenAI Agents SDK handoffs one line each with links. "## Antipatterns"
lists seven numbered findings with sources, mapped 1→R5, 2→R6, 3→R7, 4→R4,
5→R8, 6–7 marked already covered; Cognition attributed as "a lab's
engineering post, not one of the three vendors this file tracks"; Agents
Companion flagged "secondary-verified — Kaggle mirror, not a Google
primary".

### R10 — antigravity mirrors (complete)
Command:
`grep -q "## Precedence" antigravity/AGENTS.md && grep -q "decision coupling" antigravity/.agents/skills/breakdown/SKILL.md && grep -qi "must NOT touch" antigravity/.agents/skills/breakdown/SKILL.md && grep -q "decision coupling" antigravity/.agents/workflows/parallel.md && grep -q "scale the fleet" antigravity/AGENTS.md && grep -qi "human-launched" antigravity/README.md`
Result: exit 0 (PASS).
Substance (diff): AGENTS.md gains a `## Precedence` block (R4 text adapted
to the port: AGENTS.md in place of rules/CLAUDE.md) and the scaling rule
("~15× the tokens of a single conversation") in its token-discipline
section; ag breakdown mirrors R5+R6 with port-appropriate wording ("critic
skill"); ag parallel workflow mirrors the one-line citation; README mapping
table gains one row: skill self-chaining "Not ported — workflows are
human-launched in the Agent Manager, so the port keeps printed pointers
between stages."

### R11 note — plugin.json unchanged
Commands: `grep -n '"version"' .claude-plugin/plugin.json`;
`git diff main -- .claude-plugin/plugin.json`
Result: version "0.6.2"; diff empty. Pre-implementation version 0.6.2
recorded; bump correctly deferred to specs/review-fixes global task 99 per
the task file.

## Gates

- Breakdown evalset (skill body changed): `bash evals/run.sh breakdown`
  Output tail:
  ```
  assert: all checks passed (2 task files)
  PASS  breakdown/01-small-spec
  ----
  1/1 scenarios passed
  ```
- No other build/lint/test runner exists in the repo.

## Scope

`git diff main --stat`: exactly 10 files, 143 insertions / 13 deletions —
the 9 Touch-list files plus the task file itself (plan comment only, per
the repo's record-plans convention). Must-NOT-touch check: no diff on
`.claude/skills/idea/SKILL.md`, `CLAUDE.md`, `.claude-plugin/plugin.json`,
or any other skill/agent. No scope creep found.

## Overfitting check

Acceptance-grep strings all appear inside substantive prose (real test
definitions, rule text, routing clause, research entries), not as inert
markers; the evalset was not modified (evals/ has no diff). No gaming
observed.
