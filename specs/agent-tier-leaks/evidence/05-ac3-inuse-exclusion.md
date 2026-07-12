# Verification: 05-ac3-inuse-exclusion

Verdict: PASS

## Criteria

1. PASS — `grep -q 'in_use' specs/agent-tier-leaks/SPEC.md` (from worktree root)
   exit 0. Match found at SPEC.md lines 62-68 note block.

2. PASS — `grep -q "not -path '\*/.in_use" specs/agent-tier-leaks/SPEC.md`
   exit 0. Match: "filter those markers out with `-not -path '*/.in_use/*'`"
   (line 68).

3. PASS (manual) — Note is inserted directly under R1's requirement bullet
   (SPEC.md lines 48-61), immediately before R2 begins (line 70), explicitly
   labeled "Note (AC3 plugin-cache-untouched false positive)". Content
   accurately describes: the R1 AC3 mtime scan
   (`find ~/.claude/plugins/cache/agentic-toolkit -newer <SPEC.md> -type f |
   wc -l` → 0), the false-positive mechanism (transient `.in_use/<pid>`
   runtime markers written by any live `claude` process inflate the count
   even with no content change), and the fix (`-not -path '*/.in_use/*'`
   exclusion). This matches task-01's evidence line for its third acceptance
   criterion (`0.8.13/.in_use/25950` false hit, resolved with the same
   exclusion) — a reader checking task-01's AC3 would find this note
   adjacent to the R1 text it documents.

## Diff scope check

`git diff b612acbd622643d9bb4e89d035322edca928b98d --stat` (worktree root):
only `specs/agent-tier-leaks/SPEC.md | 8 ++++++++` (8 insertions, 0
deletions, 1 file changed). No other files touched — task file
`specs/agent-tier-leaks/tasks/05-ac3-inuse-exclusion.md` itself shows no
diff against base, consistent with the task's Status not yet being flipped
(per caller's note, this is fine and expected at this point). No scope
creep detected.

## Gates

No repo-wide build/lint/test gate applies to a docs-only SPEC.md content
addition; none run (not applicable — this is a pure prose/spec change with
no code touched).
