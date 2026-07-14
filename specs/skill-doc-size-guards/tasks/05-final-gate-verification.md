# Task 05: Final gate verification across the whole spec

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
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

- [ ] `bash evals/lint-skill-size-gate.sh; echo "exit:$?"` → `exit:0`.
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → ≤ 500.
- [ ] `grep -qiE '^## (Table of [Cc]ontents|Contents)\b' <(head -20 .claude/skills/drain/reference.md)`
      → match.
- [ ] `for f in factcheck evals prose-review gate workflow-author fleet autopilot; do grep -qiE '^## (Table of [Cc]ontents|Contents)\b' <(head -20 .claude/skills/$f/reference.md) || echo "MISSING:$f"; done`
      → empty output.
- [ ] `grep -q "lint-skill-size-gate" .claude/skills/drain/reference.md` →
      match.
- [ ] `grep '"version"' .claude-plugin/plugin.json` → differs from
      `0.8.63` (the value at spec-authoring time).
- [ ] `diff <(git show 6511460f8e6586c6436a029f18d974352f179aa9:codex/.agents/skills/drain/SKILL.md 2>/dev/null) codex/.agents/skills/drain/SKILL.md`
      → non-empty diff (pinned against this spec's breakdown-authoring
      commit as a stable base, since by task 05's turn other commits may
      already sit between HEAD and task 04's own commit — a relative
      `HEAD~1` would not reliably land on task 04's diff).
- [ ] MANUAL: antigravity workflow procedural-equivalence sweep confirmed
      or explicitly left manual-pending with a reason.
