# Task 05: Final gate verification across the whole spec

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: 01, 02, 03, 04
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (all requirements — closing verification)
Touch: none (verification only; fix forward in a follow-up task if this fails rather than editing files here)

## Goal

Confirm the full spec's acceptance criteria hold now that the gate script
(01), the 7 non-drain reference.md TOC edits (02), and the drain
shrink+TOC+checklist+mirror remediation (03, 04) have all landed:
`evals/lint-skill-size-gate.sh` exits 0 repo-wide. This task makes no
source edits — it is a read-only confirmation pass. If anything fails,
do not patch it here; report the specific failing check so a follow-up
task (or the orchestrator) can fix it — this task's job is to catch a
regression between tasks, not to silently repair one.

## Steps

1. Run `bash evals/lint-skill-size-gate.sh` and confirm exit 0 with the
   `lint-skill-size-gate: OK` line.
2. Re-run every acceptance criterion listed in `../SPEC.md`'s "Acceptance
   criteria" section and record the result of each.
3. For the one MANUAL criterion (antigravity workflow procedural
   equivalence), if task 04 already confirmed it, cite that task's
   evidence rather than re-doing the live sweep; if task 04 left it
   manual-pending, attempt the live sweep now — if this session also has
   no way to exercise antigravity interactively, leave it manual-pending
   with the reason stated (per `.claude/rules/mirror-verification.md`)
   rather than guessing.

## Acceptance

- [x] `bash evals/lint-skill-size-gate.sh; echo "exit:$?"` → `exit:0`.
      EVIDENCE (2026-07-13, task/05 branch off main dc24a32): output
      `lint-skill-size-gate: OK — all skill docs within size/TOC conventions`,
      exit:0.
- [x] `wc -l < .claude/skills/drain/SKILL.md` → ≤ 500.
      EVIDENCE: `wc -l` → 489 (≤ 500).
- [x] `grep -qiE '^## (Table of [Cc]ontents|Contents)\b' <(head -20 .claude/skills/drain/reference.md)`
      → match.
      EVIDENCE: TOC heading `## Table of contents` at line 3 of
      drain/reference.md; criterion exits 0 under bash (`bash -c` re-run).
      NOTE: under the harness's zsh, the `<(head -20 …)` + `grep -q` form
      exits 1 due to a SIGPIPE/process-substitution race, not a content
      gap — direct grep and a temp-file grep both match, and C1's gate
      script (which C1 runs under `bash`) confirms all TOCs conform.
- [x] `for f in factcheck evals prose-review gate workflow-author fleet autopilot; do grep -qiE '^## (Table of [Cc]ontents|Contents)\b' <(head -20 .claude/skills/$f/reference.md) || echo "MISSING:$f"; done`
      → empty output.
      EVIDENCE: all 7 reference.md files carry `## Table of contents` at
      line 3; loop prints no MISSING lines under bash (`bash -c` re-run).
      Same zsh process-substitution caveat as the C3 criterion above.
- [x] `grep -q "lint-skill-size-gate" .claude/skills/drain/reference.md` →
      match.
      EVIDENCE: match (drain/reference.md references the gate script).
- [x] `grep '"version"' .claude-plugin/plugin.json` → differs from
      `0.8.63` (the value at spec-authoring time).
      EVIDENCE: `"version": "0.9.1"` — differs from 0.8.63.
- [x] `diff <(git show 6511460f8e6586c6436a029f18d974352f179aa9:codex/.agents/skills/drain/SKILL.md 2>/dev/null) codex/.agents/skills/drain/SKILL.md`
      → non-empty diff (pinned against this spec's breakdown-authoring
      commit as a stable base, since by task 05's turn other commits may
      already sit between HEAD and task 04's own commit — a relative
      `HEAD~1` would not reliably land on task 04's diff).
      EVIDENCE: diff against pinned base 6511460 is non-empty (113 lines) —
      codex drain/SKILL.md mirror carries task 04's changes.
- [ ] MANUAL: antigravity workflow procedural-equivalence sweep confirmed
      or explicitly left manual-pending with a reason.
      MANUAL-PENDING (cites task 04, per `.claude/rules/mirror-verification.md`
      manual-pending escape): task 04 ran the static
      `.claude/rules/mirror-procedure-discipline.md` classification and
      found the gate step added to `antigravity/.agents/workflows/drain.md`
      is a faithful procedural port of the reference.md + codex additions
      (same condition, command, consequence, and decision point). Left
      manual-pending because this session also has no way to exercise
      antigravity interactively; a human/orchestrator confirms the live
      sweep post-merge. Does not block this task's DONE verdict.
