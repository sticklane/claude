# Verification evidence — Task 01: Plugin manifest validates

Verified: 2026-07-03
Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a9354d37879a99b78 (branch task/01-plugin-manifest, HEAD 161a250, changes uncommitted in working tree)
Verifier: independent (did not write this code)

## Verdict: PASS

One criterion (version pin `0.3.0`) fails literally due to a stale pin, but
its stated intent — version untouched, task 99 owns the bump — is satisfied
and task 99 explicitly treats the pin as stale-adjustable. Details below.

## Per-criterion results

### 1. `claude plugin validate .` → exit 0 — ✓ PASS

Command (from worktree root):
```
claude plugin validate . ; echo "EXIT=$?"
```
Output:
```
Validating marketplace manifest: /Users/sjaconette/claude/.claude/worktrees/agent-a9354d37879a99b78/.claude-plugin/marketplace.json

✔ Validation passed
EXIT=0
```
Note: the validator reports validating the marketplace manifest (which
references the plugin at repo root). Exit code 0 as required.

### 2. agents array matches the three .md paths — ✓ PASS

Command:
```
python3 -c "import json; a=json.load(open('.claude-plugin/plugin.json'))['agents']; assert isinstance(a, list) and set(a)=={'./.claude/agents/scout.md','./.claude/agents/critic.md','./.claude/agents/verifier.md'}"
```
Exit code: 0.

Cross-check against reality: `ls .claude/agents/` → `critic.md scout.md
verifier.md` — exactly the three files enumerated, no more, no fewer.

### 3. marketplace.json has non-empty top-level `description` — ✓ PASS

Command:
```
python3 -c "import json; m=json.load(open('.claude-plugin/marketplace.json')); assert isinstance(m.get('description'), str) and m['description']"
```
Exit code: 0.

Description text: "Marketplace for the agentic toolkit: a spec-driven
development pipeline with cheap review subagents and dashboards, distributed
as a single plugin." — non-enumerating: names no individual skill or agent
(generic category words only), satisfying CLAUDE.md's convention.

### 4. version == '0.3.0' — ✗ literal FAIL / ✓ intent PASS

Command:
```
python3 -c "import json; assert json.load(open('.claude-plugin/plugin.json'))['version']=='0.3.0'"
```
Exit code: 1 (AssertionError). Actual version: `0.6.0`.

Intent check (criterion's stated intent: "version untouched — 99 owns the bump"):
- `git diff -- .claude-plugin/plugin.json | grep version` → no match (exit 1):
  the version line is NOT touched by this task's diff.
- `git show HEAD:.claude-plugin/plugin.json` version = 0.6.0; working tree
  version = 0.6.0. Identical — this task did not change version.
- specs/review-fixes/tasks/99-version-bump-and-sweep.md step 2: "if an
  intervening bump landed, bump minor from whatever is current and adjust
  the acceptance pin below to match" — the spec explicitly treats version
  pins as stale-adjustable placeholders; the 0.3.0 pin predates intervening
  batches that bumped to 0.6.0.

Judgment: the criterion's purpose is to prove this task left `version`
alone. That is proven. The literal command failure is a stale pin, not an
implementation defect. Counted as satisfied-by-intent; recommend task 99's
sweep annotate this pin as superseded (as it already plans to do for the
analogous hardening-04 pin).

### 5. `grep -q "enumerated" CLAUDE.md` → exit 0 — ✓ PASS

Exit code: 0. The caveat lives in the `.claude-plugin/` bullet and is
coherent: skills manifest points at the directory (no manifest edit for new
skills), "but agents ARE enumerated in plugin.json by schema requirement, so
a new agent DOES need a manifest edit; only skills stay manifest-free."
This accurately matches the new plugin.json structure.

## Scope creep

None. `git diff HEAD --stat`:
```
.claude-plugin/marketplace.json                | 1 +
.claude-plugin/plugin.json                     | 6 +++++-
CLAUDE.md                                      | 8 +++++---
specs/review-fixes/tasks/01-plugin-manifest.md | 2 +-
```
All four files are in the allowed set (Touch list + task file). The task-file
change is only `Status: pending` → `Status: in-progress`. plugin.json diff
touches only the `agents` field; no version bump smuggled in.

## Standard gates

- `bash tests/test_hook_templates.sh` → exit 0
- `bash tests/test_install_gates.sh` → exit 0
- `bash tests/test_sync_skills.sh` → exit 0

## Overfitting check

No test files modified; the agents array reflects the actual contents of
`.claude/agents/`, not a hardcoded gaming of the check. Marketplace
description is generic prose, not tailored to grep patterns.

## Notes for orchestrator

- Working-tree changes are uncommitted on branch task/01-plugin-manifest.
- Task file still says `Status: in-progress` and acceptance boxes unticked —
  expected if verification precedes completion bookkeeping.
- The stale `0.3.0` pin in this task's acceptance list will read as red in
  task 99's mechanical sweep; 99 should annotate it (its step 5 pattern).
