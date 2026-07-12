# Verification evidence: 01-write-guide-and-rule-bullet

Verdict: PASS

Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a81adca1b0280bbdc
Base commit: c00f5bb1db1a00c42a6c4a7710e581b49284cf5e

## Acceptance criteria

1. `test -f docs/guides/large-codebase-context.md`
   Result: PASS — file exists.

2. Five-URL grep chain (anthropic post, aider repomap, claude-context,
   code-index-mcp, mcp servers repo)
   Result: PASS — exit 0, all five citations present.

3. `grep -cE '^\s*```mermaid' docs/guides/large-codebase-context.md`
   Result: `1` (>= 1 required). PASS.

4. `grep -Fq 'large-codebase-context' .claude/rules/token-discipline.md`
   Result: PASS — new bullet found under "Delegation defaults":
   "Large codebase, scout not converging → the orchestrating session (never
   `scout`) may `ToolSearch`..." with a link to
   docs/guides/large-codebase-context.md.

5. `git diff --quiet HEAD -- .claude/agents/scout.md` → exit 0
   Result: PASS (no diff against working HEAD).
   Additional R4 check: `git diff c00f5bb...HEAD -- .claude/agents/scout.md`
   is also empty; `tools:` frontmatter line byte-identical at base vs now:
   `tools: Read, Grep, Glob, Bash(git log *), Bash(git show *), Bash(ls *), Bash(wc *)`
   in both. PASS.

6. `bash tests/test_doc_links.sh`
   Result: `pass: 16 fail: 0`, exit 0. PASS.

## Manual-content checks (read, not grepped)

- Decision table (## Decision table: which one, if any) has exactly the
  three required rows: (a) semantic/fuzzy large repo -> claude-context,
  (b) fast literal/regex -> code-index-mcp, (c) small/medium/scout-enough
  -> neither. PASS (R2).
- Install instructions present for both servers (JSON MCP config snippets
  for claude-context and code-index-mcp, each followed by a pointer to the
  upstream README for exact env vars / flags). PASS.
- Token-discipline bullet names the orchestrating session (explicitly
  "never `scout`, which cannot `ToolSearch`" in the guide's own
  cross-reference paragraph, and "the orchestrating session (never
  `scout`)" in the rule bullet itself) as the ToolSearch actor, and defers
  server-choice detail ("when each choice fits, and how to install... is
  in docs/guides/large-codebase-context.md") rather than restating the
  decision table or install steps. PASS (R3).
- No runtime dependency introduced: diff vs base touches only
  `docs/guides/large-codebase-context.md` (new) and
  `.claude/rules/token-discipline.md` (+9 lines); no code, no MCP
  config file, no plugin.json/manifest change. PASS (R5).

## Standard gates

- `bash tests/test_doc_links.sh` → pass: 16 fail: 0 (exit 0). Included above.
- `bash tests/test_antigravity_parity.sh` at current worktree HEAD → exit 1,
  output `prose-review`.
  Checked against base commit c00f5bb1db1a00c42a6c4a7710e581b49284cf5e via a
  detached `git worktree add` copy (never mutated the working tree under
  test): same command produces the same output (`prose-review`, exit 1) at
  base, before this task's changes. Confirmed PRE-EXISTING and unrelated to
  the touched files (docs/guides and .claude/rules are not part of the
  antigravity mirror chain per this task's own Touch note). Not counted
  against this task.

## Scope-creep / diff check

`git diff --stat c00f5bb1db1a00c42a6c4a7710e581b49284cf5e`:
```
 .claude/rules/token-discipline.md     |   9 ++
 docs/guides/large-codebase-context.md | 149 ++++++++++++++++++++++++++++++++++
 2 files changed, 158 insertions(+)
```
Matches the task's Touch list exactly (docs/guides/large-codebase-context.md
new file; token-discipline.md one appended bullet). No scope creep.

## Append-only task-file check

`git diff c00f5bb1db1a00c42a6c4a7710e581b49284cf5e -- 'specs/large-codebase-context-guide/tasks/*.md'`
→ empty (no diff at all). The task file has not been modified since base —
acceptable per instructions (Status/checkboxes may remain un-updated at this
point; this is not a violation since nothing outside the allowed set
changed — nothing changed at all).

## Overall

All six scripted acceptance criteria PASS. All manually-verified R2/R3/R5
content requirements PASS. Standard doc-link gate green. Pre-existing
unrelated antigravity-parity failure confirmed identical at base commit, not
attributable to this task. No scope creep. Task file diff is empty (append-only
constraint trivially satisfied).

Remaining AC6 ("Manual-pending... human, post-merge") is explicitly a
human-only manual-pending item per the task file itself — not
mechanically checkable and correctly left unautomated by the task author.

VERDICT: PASS
