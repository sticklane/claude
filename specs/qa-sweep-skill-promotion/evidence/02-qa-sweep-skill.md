# Verification: task 02-qa-sweep-skill

Verdict: PASS

## Acceptance commands (all run from worktree root)

1. `test -f .claude/skills/qa-sweep/SKILL.md` → PASS (exit 0, file exists)
2. `grep -c "^name: qa-sweep$" .claude/skills/qa-sweep/SKILL.md` → PASS, output `1`
3. `grep -qi "deploy\|migration\|freshness" .claude/skills/qa-sweep/SKILL.md` → PASS (match found; section "b. Check deploy/migration freshness FIRST")
4. `grep -qi "critique" .claude/skills/qa-sweep/SKILL.md` → PASS (match found; section "e. Self-chain into /critique...")
5. `grep -qi "drain" .claude/skills/qa-sweep/SKILL.md` → PASS (match found; section "f. Hand off to /drain...")
6. `grep -qi "browser-automation-handoffs" .claude/skills/qa-sweep/SKILL.md` → PASS (match found, x2: step c and closing "Browser-driven checks" section)
7. `grep -qi "re-verify\|re-run" .claude/skills/qa-sweep/SKILL.md` → PASS (match found; section "g. Re-verify — two explicit branches")
8. `grep -qi "Delegation defaults\|route each page-check\|return a path" .claude/skills/qa-sweep/SKILL.md` → PASS (both "Delegation defaults" (step a and step c) and "return a path" (step c) present)

## MANUAL criterion: pointer vs restatement

Compared `.claude/rules/browser-automation-handoffs.md`'s stated mechanism
("Any claude-in-chrome-driven flow that detects a Google SSO/One-Tap ...
login surface attempts **at most ONE** click strategy against it, then hands
off to the human") against `.claude/skills/qa-sweep/SKILL.md`'s two
citations:

- Step c (lines 64-66): "For any check driven through claude-in-chrome,
  follow `.claude/rules/browser-automation-handoffs.md` for the login-wall
  handoff behavior (cited, not restated — see the closing note below)."
- Closing "Browser-driven checks" section (lines 106-111): "Any
  claude-in-chrome-driven check this skill performs follows
  `.claude/rules/browser-automation-handoffs.md` for detecting a login wall
  and handing off to the human fast — a pointer to that rule, not a
  restatement of its SSO/One-Tap handoff behavior."

Neither citation restates the "at most ONE click strategy" mechanism, the
cross-origin-iframe rationale, or the SSO/One-Tap-specific scope carve-out —
they name the rule file and the general behavior category ("login-wall
handoff") and defer the mechanism to the rule. This reads as a POINTER, not
a restatement. PASS.

## Step 3 structure conformance

- Frontmatter present: `name: qa-sweep`, third-person `description` with
  trigger phrases ("test the site", "QA sweep", "run a smoke test", "test
  everything end to end", plus an extra "shake out what's broken"),
  `argument-hint: "[repo path or URL to sweep]"`. Matches critique/SKILL.md
  shape.
- Procedure steps a–g present in exact order matching the spec's R2a-g
  wording (scout → freshness-first → parallel dispatch → file specs →
  self-chain critique → hand off to /drain → re-verify two branches).
- R2f human-gating contract: present as the first body block after
  frontmatter, lines 7-16 — well within the first 30 lines.
- browser-automation-handoffs pointer: present (step c and closing section,
  see MANUAL check above).
- "Next stage" closing line: present, last line of file (line 113-115),
  names `/critique` (self-chains) then `/drain` (human-launched or
  authorized auto-chain).
- Body length: `wc -l` → 115 lines, well under 500.

All structural sub-checks PASS.

## Diff scope

`git diff --name-status 3a0086d HEAD`:

```
A	.claude/skills/qa-sweep/SKILL.md
M	specs/qa-sweep-skill-promotion/tasks/02-qa-sweep-skill.md
```

- New file `.claude/skills/qa-sweep/SKILL.md` — matches Touch.
- Task file diff (`git diff 3a0086d -- specs/.../02-qa-sweep-skill.md`) is
  exactly one added block: the `<!-- PLAN (build step 1) ... -->` HTML
  comment inserted above `## Goal`. No Status-line flip, no checkbox ticks,
  no other content changed. This is within the append-only allowed set
  (plan comment block) — PASS, no scope creep. (Note: Status line still
  reads "in-progress" and acceptance checkboxes are still unticked; the
  worker did not close out the task file, but that is a completeness gap,
  not a violation of the append-only constraint.)
- No `antigravity/` mirror changes, no `.claude-plugin/plugin.json` changes
  — confirmed via `git diff 3a0086d --name-only -- '*antigravity*'
'.claude-plugin/plugin.json'` → empty output. Matches the task's Touch
  section deferring the mirror/plugin bump to a later task.
- `.claude/rules/browser-automation-handoffs.md` was NOT created by this
  diff — `git log --oneline -1` on that path shows it landed in a prior
  commit (89d7b61, sibling task), confirming this task only cited an
  already-existing path per its Touch section note.

## antigravity parity gate (expected failure)

`bash tests/test_antigravity_parity.sh` → exit 1, output: `qa-sweep`
(single line). This is the ONLY skill flagged — no other skill regressed.
Matches the task's stated expectation that the antigravity mirror is
deferred to a later task, so this failure is EXPECTED and not a defect of
this task.

## Overall verdict: PASS

All 8 acceptance commands pass, the MANUAL pointer-vs-restatement check
passes, Step 3 structural requirements are met, the diff is scoped to
exactly the Touch file plus an append-only task-file plan-block addition,
and the antigravity parity failure is the expected, task-acknowledged one.
