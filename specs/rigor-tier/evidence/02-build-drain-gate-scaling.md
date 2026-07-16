# Verification evidence: task 02 build-drain-gate-scaling

Verified against branch `task/02-build-drain-gate-scaling` at repo root
`/Users/sjaconette/claude/.claude/worktrees/agent-a59f7a5c663d9a900`.

## Verdict: PASS

## Per-criterion results

1. `grep -q "Rigor:" .claude/skills/build/SKILL.md && grep -q "Rigor:" .claude/skills/drain/SKILL.md`
   - Exit: 0 — PASS

2. `grep -qi "re-running the full gates" .claude/skills/build/SKILL.md && grep -qi "re-running the full gates" .claude/skills/drain/SKILL.md`
   - Exit: 0 — PASS

3. `bash evals/lint-ultra-gate.sh`
   - Output: `lint-ultra-gate: OK — all ultra mentions gated in 4 files`
   - Exit: 0 — PASS

4. `grep -qi "rigor" antigravity/.agents/workflows/build.md && grep -qi "rigor" antigravity/.agents/workflows/drain.md`
   - Exit: 0 — PASS

5. `grep -qi "rigor" codex/.agents/skills/build/SKILL.md && grep -qi "rigor" codex/.agents/skills/drain/SKILL.md`
   - Exit: 0 — PASS

## Merge-time blocker gate

`bash evals/lint-skill-size-gate.sh`

- Output: `lint-skill-size-gate: OK — all skill docs within size/TOC conventions`
- Exit: 0 — PASS

## Semantic fidelity (fresh-eyes read, not mechanical)

### .claude/skills/build/SKILL.md

Lines 71-80 ("Rigor tier (gate scaling)") and lines 113-141 confirm:
(a) skips TDD red-first on `Rigor: prototype` (line 74, 113-115); (b) skips
the verifier-agent spawn (line 75, 129-136); (c) substitutes a mechanical
acceptance-command run for the reported DONE/BLOCKED verdict (lines 130-136:
"report DONE when every acceptance command passes ... BLOCKED otherwise").
Explicitly states primary-path scope: "applies to attended /build AND to
drain's attempt-1/relaunch workers, who run this procedure verbatim" (lines
79-80). Promotion rule present verbatim in concept at lines 138-141. PASS.

### .claude/skills/drain/SKILL.md

Lines 223-229: the substitution is scoped explicitly to "a prototype-rigor
tournament" — the per-candidate `verifier` dispatch swap ("swap a mechanical
acceptance-command run for each per-candidate `verifier` dispatch and rank on
that"), and explicitly states "the pre-merge whitelist diff and gates stay
mechanical, unchanged." Promotion rule present at lines 226-229. Matches the
task's Goal requirement that the orchestrator-side substitution applies ONLY
in the tournament path. PASS.

### Mirror fidelity (antigravity + codex)

- `antigravity/.agents/workflows/build.md` (lines 56-65, 89-111): equivalent
  three-part branch (skip TDD red-first, skip verifier-skill application,
  mechanical acceptance-command substitute) plus promotion rule and
  primary-path scope statement ("attended runs AND to the drain workflow's
  attempt-1/relaunch workers"). Equivalent behavior, not just keyword match.
- `antigravity/.agents/workflows/drain.md` (lines 778-796): tournament-scoped
  substitution ("the ONLY orchestrator-owned locus that scales is this
  tournament's per-candidate verifier dispatch"), explicit statement that
  pre-merge whitelist diff + `scripts/check.sh` stay mechanical/unchanged,
  plus promotion rule. Equivalent.
- `codex/.agents/skills/build/SKILL.md` (lines 134-143, 174-202): same
  three-part branch, primary-path scope, and promotion rule as
  `.claude/skills/build/SKILL.md`. Equivalent.
- `codex/.agents/skills/drain/SKILL.md` (lines 296-313): same
  tournament-only scoping, mechanical-pre-merge-gate statement, and
  promotion rule as `.claude/skills/drain/SKILL.md`. Equivalent.

All four mirrors carry the equivalent PROCEDURE (per
`.claude/rules/mirror-procedure-discipline.md`), not merely the literal word
"rigor."

## Scope check

`git diff --name-only 4055e36..task/02-build-drain-gate-scaling`:

```
.claude/skills/build/SKILL.md
.claude/skills/drain/SKILL.md
antigravity/.agents/workflows/build.md
antigravity/.agents/workflows/drain.md
codex/.agents/skills/build/SKILL.md
codex/.agents/skills/drain/SKILL.md
```

Exactly matches the task's Touch list (6 files). No out-of-scope edits.
Confirms task 02 did not touch `.claude/skills/idea/SKILL.md`,
`.claude/skills/breakdown/SKILL.md`, `.claude/skills/list-specs/SKILL.md`,
`.claude/rules/quality-discipline.md`, or `.claude-plugin/plugin.json` (all
correctly excluded per the task's own Touch section).

## Append-only task-file check

`git diff 4055e36..task/02-build-drain-gate-scaling -- '*/tasks/*.md'`
produced empty output — the task file has not yet been edited (worker has
not performed close-out: Status still `pending`, checkboxes unticked). No
disallowed edits to Goal/Steps/Touch/Budget/acceptance-criterion text —
trivially true since the file is byte-identical to base. This is expected
pre-close-out state, not a defect.

## Scope-creep findings

None found. No files outside Touch list changed; no task-file body-text
edits.

## Gate summary

- Acceptance criteria 1-5: all PASS (exit 0)
- `evals/lint-skill-size-gate.sh`: PASS (exit 0)
- Semantic fidelity: build.md and drain.md each implement the exact
  three-part gate-scaling branch and promotion rule described in the task's
  Goal/Steps; drain's substitution is correctly confined to the tournament
  path with pre-merge/gates left mechanical in all cases; all four mirrors
  carry equivalent (not just keyword-matching) procedure content per
  mirror-procedure-discipline.md.
- No scope creep, no disallowed task-file edits (file unchanged, as expected
  pre-close-out).
