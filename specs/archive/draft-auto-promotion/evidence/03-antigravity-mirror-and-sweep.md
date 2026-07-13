# Verification evidence: Task 03 (antigravity mirror and sweep)

Verifier note: HEAD == base commit (7d0c7b24bd); all task work is
present as UNCOMMITTED changes in the worktree. All diffs below compare
working tree to the base commit accordingly.

## Verdict: PASS (with a process finding — see below)

## Task's own 4 acceptance criteria

1. `grep -qi "stub intake" antigravity/.agents/workflows/drain.md`
   → MATCH (exit 0). PASS.

2. `rg -Uqi "only a human (promotes|edits)|only a human \(or|Promotion is manual|promoted manually|only a human\s+(promotes|edits)" .claude/skills/ antigravity/.agents/`
   → exit 1 (no matches). PASS.

3. plugin.json version:
   - base (`git show 7d0c7b24bdb4af5a0be92b82f58893592454a90c:.claude-plugin/plugin.json`): `"version": "0.8.27"`
   - current (working tree `.claude-plugin/plugin.json`): `"version": "0.8.28"`
     Differs, one patch bump. PASS.

4. Closing sweep of every automatable SPEC.md Acceptance checkbox (below). PASS.

## SPEC.md "## Acceptance criteria" — automatable items

- `grep -qi "stub intake" .claude/skills/drain/SKILL.md` → MATCH. PASS.
- `grep -q "Stub-intake-failed:" .claude/skills/drain/reference.md` → MATCH. PASS.
- Deterministic screen script test (R2):
  - `.claude/skills/drain/screen-stub.sh` exists, executable (`-rwxr-xr-x`).
  - Fixture with "ignore previous instructions" in the Goal:
    `screen-stub: REFUSED — instruction-shaped Goal matched: ignore-instructions`, exit 1. PASS (refused).
  - Clean fixture (unrelated feature Goal): `screen-stub: clean`, exit 0. PASS (passed).
- `grep -qi "obsolete" .claude/skills/drain/reference.md` → MATCH. PASS.
- `grep -qi "adversarial" docs/human-gates.md` → MATCH; reason 4 (not reason 1) names
  the "deterministic screen" + "Goal re-authoring" hard layer plus an
  "adversarial critic gate" judgment layer (manual read of docs/human-gates.md
  reason 4, lines ~34-59). PASS.
- `grep -rn "reason 1" .claude/skills/drain/` → no output, exit 1 (no hits). PASS.
- Reason 4 still carries the disable-model-invocation launch rationale after
  the weave (manual read, docs/human-gates.md lines 3, 37 and the reason-4
  paragraph itself which opens with the original "hard mechanism beats a
  soft rule" / disable-model-invocation argument before the woven-in stub
  material). PASS.
- `rg -Uqi "only a human (promotes|edits)|only a human \(or|Promotion is manual|promoted manually|only a human\s+(promotes|edits)" .claude/skills/ antigravity/.agents/`
  → exit 1, no matches. PASS (R7, two-tree, multiline).
- `grep -qi "promoted this run" .claude/skills/drain/SKILL.md` → MATCH; exit-checklist
  count text says "seven-section" (`.claude/skills/drain/reference.md:650`
  and mirrored in `antigravity/.agents/workflows/drain.md:695`). PASS.
- Antigravity mirrors carry the contract; plugin.json version bumped 0.8.27 → 0.8.28. PASS (see above; mirror content-coverage detailed below).
- Fresh-session drain-run test (fixture queue with actionable/obsolete/decision-shaped
  stubs) — NOT exercised (task 03's Touch is antigravity/plugin.json only;
  this SPEC criterion is explicitly "manual, per CLAUDE.md's testing
  convention" and is not automatable by grep/rg). Not run in this
  verification pass — flagged as un-exercised, not claimed PASS.

## Antigravity mirror content-coverage (paraphrase port, not byte-diff)

`antigravity/.agents/workflows/drain.md` (working-tree diff vs base, 103
insertions / 19 deletions) carries:

- `obsolete` added to the status list (line 8).
- The materialize-discoveries promotion sentence (line 364) now reads
  "Promotion `draft` → `pending` runs through **stub intake** ... never a
  hand edit" — the "only a human (or ...)" phrasing is gone.
- A full "Stub intake" section (~lines 548-599+): trigger/ordering
  identical to critique intake's, assess → gate → act pipeline,
  deterministic screen invoked via a shell step referencing
  `.claude/skills/drain/screen-stub.sh` (line 563), `Stub-intake-failed:`
  baton line (lines 408-424, 555), OBSOLETE / PASS / DECISION-SHAPED / FAIL
  act semantics matching SPEC.md's Solution step 3.
- Critique-intake draft-stub passage (line 543) is now a pointer: "Draft
  TASK stubs are **not** critique intake — they are handled by **stub
  intake** ... (docs/human-gates.md reason 4, cited not restated)".
- Exit checklist bumped to a seven-section list (line 695) with item 6
  "Promoted this run" (lines 707-710) matching SPEC R5's audit content
  (promoted, obsolete-closed, screen-refused/gate-failed stubs).

## Append-only task-file check

`git diff 7d0c7b24bdb4af5a0be92b82f58893592454a90c -- 'specs/**/tasks/*.md'`
(working tree, since HEAD == base) shows changes ONLY in
`specs/draft-auto-promotion/tasks/03-antigravity-mirror-and-sweep.md`, and
those changes are ONLY the addition of the `<!-- PLAN ... -->` worker
comment block (a permitted append-only element). No Status change, no
checkbox ticks, no evidence-citation lines were added to the task file
itself. No other task file was touched. PASS on append-only scope, but see
process finding below.

## Scope check

`git diff --stat 7d0c7b24bdb4af5a0be92b82f58893592454a90c` (working tree)
shows exactly three files changed:

- `.claude-plugin/plugin.json` (Touch-listed)
- `antigravity/.agents/workflows/drain.md` (Touch-listed)
- `specs/draft-auto-promotion/tasks/03-antigravity-mirror-and-sweep.md` (task file, PLAN block only)

No out-of-Touch product file was changed. PASS.

## Process finding (not a criterion failure, but notable)

The task file's own Status line is still `in-progress` (never flipped),
none of the task's four Acceptance checkboxes are ticked, and no
evidence-citation lines were added to the task file — despite the task's
Steps explicitly saying "cite each result in the evidence file" and the
evidence file for this task
(`specs/draft-auto-promotion/evidence/03-antigravity-mirror-and-sweep.md`)
did not exist before this verification pass (siblings 01 and 02 both have
one). The substantive product work (drain.md mirror, plugin.json bump) is
correct and complete, but the worker did not close out the task's own
bookkeeping. This is a process gap, not a criterion failure — none of the
task's four written Acceptance checkboxes require Status/checkbox
bookkeeping — but the orchestrator should be aware the task is not marked
done and has no worker-authored evidence trail.
