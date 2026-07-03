# Evidence: Task 04 — Reference-file TOCs + context-management research record

Verdict: PASS
Verified: 2026-07-03, branch task/04-reference-tocs-research-record,
HEAD 72895fc (changes in working tree, uncommitted).

## Acceptance criteria

### ✓ R2 — every >100-line reference file opens with a TOC

Command (from repo root):

```
for f in .claude/skills/*/reference.md; do [ "$(wc -l < "$f")" -le 100 ] || head -5 "$f" | grep -qi "contents\|TOC" || exit 1; done; echo $?
```

Output: `acceptance1 exit=0`

### ✓ R7 — external-playbooks greps

```
grep -qi "context management" docs/external-playbooks.md && grep -qi "tool-result size" docs/external-playbooks.md; echo $?
```

Output: `acceptance2 exit=0`

## Goal-section substantive checks

### ✓ Five reference files: Contents line directly under H1, within first 5 lines

All five files are >100 lines and place a `Contents:` line at line 3
(directly under the H1 + blank line):

- drain: 230 lines — Contents at lines 3–5
- fleet: 184 lines — Contents at line 3
- gate: 195 lines — Contents at lines 3–4
- autopilot: 132 lines — Contents at lines 3–4
- evals: 113 lines — Contents at line 3

TOC accuracy checked against `grep -n "^## "` in each file: entries
match the real H2 sections. Apparent omissions are inside code fences,
verified by reading the surrounding lines:

- drain line 100 `## Deferred questions` — inside a ```markdown example
  block under "Deferred question format".
- evals lines 33–70 (`## Problem`, `## Solution`, etc.) — inside the
  setup.sh heredoc that writes the fixture SPEC.md.

### ✓ Content otherwise unchanged

`git diff main -- .claude/skills/` shows insertions only (2–4 TOC lines
per file, 14 lines total across the five files); no deletions or other
modifications.

### ✓ docs/external-playbooks.md "Context management" section (R7)

`git diff main -- docs/external-playbooks.md` = +50 lines, one new
`## Context management` section containing:

- Adopted: R1 (compaction steering), R2 (survival conventions/TOCs),
  R3 (agent-written memory), R4 (static-first cache economics),
  R5 (tool-call ceilings + INCOMPLETE verdict), R6 (Key: value
  headers) — each mapped to a named source (Anthropic
  context-engineering post, Claude Code docs, ADK sessions/memory,
  OpenAI prompt-caching guide, GPT-5 prompting guide).
- Already covered: attention budget, JIT retrieval, subagent isolation
  with the 1,000–2,000-token summary validating the scout's ≤300-word
  budget, progressive disclosure.
- Where the toolkit leads: contains the exact phrase "tool-result
  size" ("Tool-result size discipline... No vendor guidance found").
- Deliberately skipped with one-line reasons: ADK scope tiers
  (harness-level machinery), ADK artifact versioning (git already
  versions), OpenAI verbatim-minus-tools handoffs (harness-level
  transfer).
- Source links: Anthropic context-engineering post, Claude Code docs,
  ADK sessions & memory, OpenAI prompt caching, GPT-5 prompting guide.

Follows the file's convention (rule pointers up front: "Those files
state the rules; the research stays here").

### ✓ plugin.json NOT bumped

`grep '"version"' .claude-plugin/plugin.json` → `0.6.2`;
`git show main:.claude-plugin/plugin.json | grep version` → `0.6.2`.
(Repo convention says bump on skill change; task file explicitly
assigns the combined bump to global task 99 — correctly deferred.)

### ✓ No antigravity/ or other out-of-scope edits

`git diff main --name-only` lists exactly the six Touch files:
the five reference.md files + docs/external-playbooks.md.
`git diff main -- .claude-plugin/ antigravity/ | wc -l` → 0.

## Project gates

- `bash tests/test_hook_templates.sh` → exit 0, pass: 77, fail: 0
- `bash tests/test_install_gates.sh` → exit 0, pass: 156 fail: 0
- `bash tests/test_sync_skills.sh` → exit 0, passed: 24, failed: 0

(/evals full skill-eval runs launch live agent sessions; not run as
part of this verification.)

## Scope creep / overfitting

None found. Diff is insertions-only in exactly the Touch list. The TOC
lines are real section indexes, not grep-bait: each entry corresponds
to an actual `##` heading. No test files were modified.
