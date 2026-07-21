# Verification: task 02 — drain reference.md Blocks: derivation

Verdict: PASS

## Per-criterion

1. Command: `grep -c 'promotion of this stub to a dispatchable task' .claude/skills/drain/reference.md`
   Result: `1` — matches expected. PASS.

2. Command: `grep -c 'breakdown of this spec into dispatchable tasks' .claude/skills/drain/reference.md`
   Result: `1` — matches expected. PASS.

3. Command: `sed -n '/^## HUMAN.md filing (R2)/,/^## /p' .claude/skills/drain/reference.md | grep -n 'unblocking-power'`
   Result: one match at relative line 40 ("from the SAME **unblocking-power** lookup ..."). Confirmed the
   "## HUMAN.md filing (R2)" heading is at reference.md:1890 and there is no other `## ` heading before the
   match (checked `grep -n '^## '`), so the match falls inside the section, not a stray hit elsewhere in the
   file. Count = 1 ≥ 1. PASS.

## Behavioral complement (depth-ceiling)

Read the new "Deriving each entry's `Blocks:` clause" guidance (reference.md:1919-1944). It correctly:

- Splits the six mapping-table rows into 4 dependency-bearing + 2 fixed-phrase, matching SPEC.md's Solution
  section split verbatim.
- Cites the "unblocking-power" computation by name and quotes the same definition already present at
  reference.md:1731-1733 ("the count of still-`pending` tasks whose `Depends on:` names this task, resolved
  as the dispatchability check does") and cross-references `.claude/skills/drain/SKILL.md:130`, where line
  130 ("the tie-break is computed by drain_frontier ... Priority → unblocking-power → lexicographic-path
  triple") does reference "unblocking-power" as claimed — citation verified accurate, not fabricated.
- Fixed-phrase table renders each literal phrase next to its own row (two separate rows, not merged into a
  shared sentence).

Searched for a real, live case to apply the derivation to:

```
grep -rn '^Status: blocked' specs/*/tasks/*.md specs/archive/*/tasks/*.md
```

→ no output. No task file anywhere in `specs/` (including `specs/archive/`) currently carries a
`Status: blocked` header field (all `grep -rln 'Unblock:'` hits are prose references inside SPEC.md files or
archived narrative, not live task headers). The behavioral check is therefore VACUOUS per the task's own
depth-ceiling note ("If no blocked task with such an Unblock line exists in specs/, say so and note the
check is vacuous — still a PASS for the doc's coherence, judged by reading the derivation rule against the
SKILL.md:130 computation it cites"). Judged by reading: the derivation rule is coherent and its citation
checks out. PASS (vacuous case, doc-coherence judged directly).

## Append-only task-file check

`git diff --stat 504c032 -- 'specs/**/tasks/*.md'` shows only
`specs/human-blocker-impact-clarity/tasks/02-drain-reference-derivation.md` changed (1 line). The diff of
that file is exactly `Status: pending` → `Status: in-progress` — no checkbox ticks, no other text changed.
No other spec's task file was touched. PASS.

## Six-row table / fixed-phrase placement / R3-R4 scope

- `git diff 504c032 -- .claude/skills/drain/reference.md` shows the original six-row mapping table (lines
  ~1904-1911, "Checklist source | HUMAN.md type | Checklist section") is untouched — diff starts after it,
  at the entry-grammar bullet. Six rows, same `ask|run|provision|decide` type mapping, confirmed unchanged.
- The two fixed phrases each appear in their own row of a newly added 2-row table (reference.md:1941-1944),
  not merged into one shared sentence.
- `git diff 504c032 -- .claude/rules/human-blockers.md HUMAN.md antigravity/ .claude-plugin/plugin.json` →
  empty output. None of the R1/R2/R6 (task 01), R5 (task 03), or R7/R8 (task 04) scoped files were touched
  by this branch. PASS.

## Scope-creep note (not disqualifying)

`git diff 504c032 -- .claude/skills/drain/reference.md` also updates the entry-grammar copy line inside the
"HUMAN.md filing (R2)" section — from `- <one-line action>` to `- <plain-language action> — Blocks:
<impact>` — bringing reference.md's copy of the grammar in sync with task 01's already-landed
`.claude/rules/human-blockers.md` change. This isn't explicitly listed in task 02's numbered Steps (which
only mention adding derivation guidance), but it: (a) stays entirely inside the Touch-scoped file
(`.claude/skills/drain/reference.md`), (b) is a necessary consistency fix now that task 01 landed the new
grammar (reference.md previously quoted the pre-`Blocks:` grammar, which would otherwise be stale/wrong),
and (c) doesn't touch any file outside Touch. Flagging for visibility, not treating as a FAIL-worthy
scope-creep finding.

## Gates

`bash evals/lint-ultra-gate.sh` → "lint-ultra-gate: OK — all ultra mentions gated in 4 files". PASS (no
regression).

## Overall verdict: PASS
