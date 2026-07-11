# Task 03: Ship gate — antigravity mirror, plugin bump, evals scenario

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: done
Depends on: 01, 02
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirement R7)
Touch: antigravity/.agents/workflows/drain.md, .claude-plugin/plugin.json, evals/

## Goal

The drain changes from tasks 01–02 ship complete: the antigravity mirror
carries the new contracts (paraphrased port, not byte-identical), the
plugin version is bumped, the /evals drain scenario reflects the dual
baton trigger, and both gates (`lint-ultra-gate.sh`, `claude plugin
validate .`) are green. Also confirms whether antigravity mirrors
`.claude/rules/` — if it does, port task 02's doctrine block there too.

## Touch

Mirror, manifest, and evals only. Do NOT re-edit `.claude/skills/drain/*`
or `.claude/rules/*` — if the mirror port reveals a defect in task 01/02's
text, report it under ## Deferred questions rather than fixing it here.

## Steps

1. Read the final `.claude/skills/drain/SKILL.md` + `reference.md` diffs
   from tasks 01–02 (`git log -p -- .claude/skills/drain/` for this spec's
   commits) and the existing `antigravity/.agents/workflows/drain.md`.
2. Port the new contracts into the antigravity drain workflow. Per
   docs/memory/workboard-mirror-verbatim.md, prose mirrors are paraphrased
   ports — carry the concepts (dual baton trigger, 2k verdict cap,
   merge-step MUST NOT + exemptions, wake-economics paragraph,
   session-model note), matching the mirror's existing voice; never aim
   for byte-identity.
3. Check whether `antigravity/` carries a rules/doctrine analog for
   token-discipline; if yes, port task 02's freehand-drain block; if no,
   note that in ## Progress and move on.
4. Locate the /evals drain scenario under `evals/` and update it to
   exercise (or at least not contradict) the dual baton trigger — same
   obligation drain-rolling-window R7 carried for window semantics.
5. Bump `version` in `.claude-plugin/plugin.json` (skill behavior
   changed) — race-safe, since other agentprof-spec drains may bump the
   same line concurrently: `git pull --rebase` immediately before the
   bump, read the version from HEAD, set next patch, commit, push; if the
   push is rejected or the rebase conflicts on the version line, resolve
   by taking the highest version present and incrementing once more, then
   retry. Never resolve by reverting another spec's bump.
6. Run both gates; fix only mirror/manifest/evals defects they surface.

## Acceptance

- [x] `grep -qiE '2k tokens' /Users/sjaconette/claude/antigravity/.agents/workflows/drain.md && grep -qiE 'TTL|cache' /Users/sjaconette/claude/antigravity/.agents/workflows/drain.md` → exit 0 (content-coverage, not diff-identity) — verifier PASS, evidence/03-ship-gate.md (both greps exit 0; 5/5 contracts present)
- [x] `bash /Users/sjaconette/claude/evals/lint-ultra-gate.sh` → exit 0 — verifier PASS: "lint-ultra-gate: OK — all ultra mentions gated in 4 files", evidence/03-ship-gate.md
- [x] `cd /Users/sjaconette/claude && claude plugin validate .` → pass — verifier PASS: "✔ Validation passed", evidence/03-ship-gate.md
- [x] `git -C /Users/sjaconette/claude log --oneline -- .claude-plugin/plugin.json` shows a version-bump commit belonging to this spec (match the spec slug in the message; no fixed HEAD~N window) — verifier PASS: commit 0b38a03 "bump plugin version 0.8.33 -> 0.8.34 (drain-wake-cost dw/03)", evidence/03-ship-gate.md
- [x] Evals drain scenario updated for the dual trigger (name the file + quote the changed lines as evidence) — verifier PASS: evals/drain/01-rolling-window/setup.sh documents max(2,6-W)=4; assert.sh Check 5 asserts no DRAIN-BATON.md written + clean lease/baton end state; bash -n clean, evidence/03-ship-gate.md
- [ ] MANUAL (attended, human-launched — /drain is disable-model-invocation, unattended workers cannot run it): a /drain run over a 2-task demo spec completes with hub verdicts each ≤ 2k tokens and no reading of task-file bodies by the hub after dispatch (Status/header lines and the tasks/ whitelist diff are fine) — inspect transcript
