# Verification: 01-verifier-leak-trace

Verdict: PASS

## Scope / diff check

```
cd /Users/sjaconette/claude/.claude/worktrees/agent-a325a4332adf9fe72
git status --porcelain
```
Output:
```
 M specs/agent-tier-leaks/tasks/01-verifier-leak-trace.md
?? docs/memory/verifier-tier-leak.md
```
Only the new memory note plus the task file itself changed. `git diff 0a5bcf3 --
specs/agent-tier-leaks/tasks/01-verifier-leak-trace.md` shows the sole change
is the `<!-- PLAN ... -->` comment block inserted above `## Goal`; Status line
unchanged ("in-progress"), no checkboxes ticked, no evidence lines added yet
— all within the append-only allowance (plan comment block). No edit to
`.claude/agents/verifier.md` (task explicitly says skip it for outcome (a) to
avoid triggering task-03's mirror/bump obligation — correctly honored). No
edit to `docs/memory.md` (task flagged the index pointer as outside Touch and
skipped it — correct, matches Touch: `.claude/agents/verifier.md,
docs/memory/verifier-tier-leak.md`). No files touched under
`.claude/rules/` or `agentprof/`. **No scope creep.**

## AC1 — Mechanism named with transcript evidence (session IDs + plugin version)

Command (independent re-derivation):
```
grep -oE 'cache/agentic-toolkit/agentic/[0-9.]+' \
  ~/.claude/projects/-Users-sjaconette-fooszone/5dcdc5c4-7776-4ac7-a064-8ed03a36fbd8.jsonl | sort -u
grep -m1 '^model:' ~/.claude/plugins/cache/agentic-toolkit/agentic/0.6.2/.claude/agents/verifier.md
```
Output:
```
cache/agentic-toolkit/agentic/0.6.2
model: inherit
```
Confirms the note's central claim: session `5dcdc5c4` was served by plugin
snapshot `0.6.2`, whose `verifier.md` pins `model: inherit`. The note
(`docs/memory/verifier-tier-leak.md`) names four plugin-served leak sessions
(`5dcdc5c4`, `b5cd2c76`, `7e277508`, `ee0f4482`) plus two pre-pin repo-local
sessions (`cd09d9e5`, `61ec4803`), states the served plugin path
(`cache/agentic-toolkit/agentic/0.6.2/`), and states no explicit `model`
override was found at the dispatch site ("The 5 verifier dispatches in
5dcdc5c4 carried no explicit `model` override — the leak is the pin, not the
dispatch site"). **PASS** — mechanism named with concrete transcript
evidence, independently reproduced.

## AC2 — Exactly one R1 outcome landed; note exists and names version boundary + immutable-cache mechanism

Literal command from the task file:
```
test -f /Users/sjaconette/claude/docs/memory/verifier-tier-leak.md
```
Result: **exit 1** (file does not exist at that path). Reason: this task ran
in an `isolation:worktree` build (`.claude/worktrees/agent-a325a4332adf9fe72`,
branch `task/01-verifier-leak-trace`) that has not yet been merged into the
main checkout at `/Users/sjaconette/claude` (still on `main` @ `0a5bcf3`). The
task file hardcodes the absolute main-checkout path rather than a
worktree-relative one, so the literal command cannot pass pre-merge — this is
a task-authoring/harness mismatch (worth flagging to whoever drains this
task), not a content defect.

Checked the deliverable in the tree actually under verification:
```
test -f /Users/sjaconette/claude/.claude/worktrees/agent-a325a4332adf9fe72/docs/memory/verifier-tier-leak.md
```
Result: exit 0. Content review confirms it names:
- the version boundary: "`model: inherit` through 0.7.x, `model: sonnet`
  from 0.8.3" in the task's own framing, and the note's own precise wording:
  "observable boundary is `inherit` ≤ 0.7.0 → `sonnet` ≥ 0.8.3" plus the repo
  fix landing at commit `01062e9` / plugin version 0.7.15.
- the immutable-cache mechanism: "Installed plugins are served from
  immutable, per-version snapshots ... A snapshot is frozen at the version it
  was cut from ... The cache snapshots are immutable: the fix is a forward
  version bump + `claude plugin update`, never an edit to a cached snapshot."
- a check command block reproducing the pin-check and transcript grep.

Exactly one outcome (a) is landed — no (b)/(c) content, and `verifier.md`
correctly left untouched per the task's own instruction.

**Substance PASS** (content fully satisfies the criterion); **literal-command
caveat**: the exact `test -f` command in the task file only resolves after
this worktree is merged to `/Users/sjaconette/claude` main. Flagging as a
process note, not treating as a content failure, since the deliverable is
present, correctly placed within the repo layout, and correctly worded, and
the mismatch is purely a pre-merge worktree-path artifact common to this
repo's `isolation:worktree` build flow.

## AC3 — No files modified under `~/.claude/plugins/cache/`

Command (exact, from task file):
```
find ~/.claude/plugins/cache/agentic-toolkit -newer /Users/sjaconette/claude/specs/agent-tier-leaks/SPEC.md -type f | wc -l
```
Raw output: `1` — one hit:
```
/Users/sjaconette/.claude/plugins/cache/agentic-toolkit/agentic/0.8.13/.in_use/25950
```
Per the known-false-positive note, re-ran excluding `.in_use/`:
```
find ~/.claude/plugins/cache/agentic-toolkit -newer /Users/sjaconette/claude/specs/agent-tier-leaks/SPEC.md -type f -not -path '*/.in_use/*' | wc -l
```
Output: `0`. Confirmed the one raw hit is a live PID marker, not content:
```
ps -p 25950
  PID TTY           TIME CMD
25950 ttys002    2:48.50 claude --dangerously-skip-permissions
```
PID 25950 is a live `claude` process — the `.in_use/25950` file is transient
runtime churn from a plugin version currently in use, exactly as described in
the known-false-positive note. Zero actual cache **content** files were
modified. **PASS**.

## Gates

No repo-wide build/lint/test gate applies to a docs-only memory-note
deliverable; `scripts/check.sh` does not exist in this repo per the
`agentprof` memory note (mirror test basenames collide) — none run, none
expected for this task.

## Overall verdict: PASS

- AC1: PASS (transcript-verified independently).
- AC2: PASS on substance (correct, complete content in the worktree under
  test); literal task-file path only resolves post-merge — flagged as a
  process note, not a fail.
- AC3: PASS (zero content files modified; one `.in_use/` PID marker is
  runtime churn, confirmed live).
- No scope creep; task-file diff is append-only (plan comment block only).
