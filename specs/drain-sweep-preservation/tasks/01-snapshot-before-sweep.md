# Task 01: Snapshot dirty worktrees before every sweep (R1)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P0
Budget: 8 turns
Spec: ../SPEC.md (requirement R1)
Touch: .claude/skills/drain/reference.md, .claude/skills/drain/SKILL.md

## Goal

Drain's rescue procedure never destroys uncommitted work: reference.md's
"Status field semantics" sweep gains a dirty-check + WIP-snapshot step before
the worktree force-remove, SKILL.md step 1's inline sweep sentence defers to
that procedure ("snapshotting uncommitted worktree changes per reference.md's
rescue procedure"), SKILL.md step 3's "(Worktree writes are discarded with
failed branches…)" parenthetical is reworded to say worktree writes are
preserved in the rescue snapshot when a dead run is swept dirty (deliberately
discarded branches — slot-machine losers, non-winning tournament candidates —
remain discarded), and reference.md's "Residual risk (accepted)" note gains
the sentence that a false sweep now also snapshots the live worker's
uncommitted writes, so the accepted risk is losing the RUN, not the work.

## Touch

Only the two drain skill files. Do NOT touch the worker prompts (task 03),
do NOT add an "Environment kill" section (task 02), do NOT bump
`.claude-plugin/plugin.json` (task 03). The antigravity mirror carries no
sweep language today — leave it alone.

## Steps

1. In reference.md "Status field semantics", amend the rescue procedure: before
   `git worktree remove --force --force`, run `git -C <worktree> status
   --porcelain`; if non-empty, commit a WIP snapshot on the run's branch inside
   the worktree — exactly `git add -A` from the worktree root (git excludes
   gitignored files, so `.dev.vars`/`node_modules` never enter the snapshot),
   then `git commit --no-verify -m "wip(rescue): <task> — swept with
   uncommitted work"` — then force-remove and rescue-rename; shortsha is the
   snapshot tip. Collapse-duplicate-tips and already-preserved rules unchanged.
2. Amend SKILL.md step 1's "force-removing each worktree first" sentence with
   the deferral fragment "snapshotting uncommitted worktree changes per
   reference.md's rescue procedure" (or equivalent containing "snapshotting
   uncommitted").
3. Reword SKILL.md step 3's discard parenthetical per the Goal — the new text
   must contain "preserved in the rescue snapshot".
4. Append the false-sweep sentence to reference.md's "Residual risk (accepted)"
   note.
5. Run the acceptance commands from the repo root.

## Acceptance

- [x] `grep -q 'status --porcelain' .claude/skills/drain/reference.md` → match — verifier: match, exit 0 (evidence/01-snapshot-before-sweep.md)
- [x] `grep -q 'wip(rescue)' .claude/skills/drain/reference.md` → match, with `git add -A` pinned in the same procedure — verifier: match; `git add -A` confirmed in same unbroken rescue paragraph
- [x] `grep -qi 'snapshotting uncommitted' .claude/skills/drain/SKILL.md` → match — verifier: match at step 1 sweep sentence, defers to reference.md rescue procedure
- [x] `grep -qi 'preserved in the rescue snapshot' .claude/skills/drain/SKILL.md` → match — verifier: match at step 3 discard parenthetical
- [x] `claude plugin validate .` → green — verifier: "✔ Validation passed", exit 0
- [x] `./specs/status.sh` → parses, no errors — verifier: exit 0, clean TOTAL summary
