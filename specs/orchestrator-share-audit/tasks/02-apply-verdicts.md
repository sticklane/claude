# Task 02: Act on the verdicts — targeted fixes and/or pre-approved restructure

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: pending
Depends on: 01
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirements R2 fix half, R3, R5)
Touch: .claude/skills/breakdown/SKILL.md, .claude/skills/build/SKILL.md, .claude/skills/idea/SKILL.md, antigravity/.agents/workflows/, antigravity/.agents/skills/, .claude-plugin/plugin.json, docs/orchestrator-share-findings.md

## Goal

Every verdict in `docs/orchestrator-share-findings.md` has its matching
outcome landed: doctrine-violation verdicts get a targeted skill-text fix
at the violating step; a /breakdown "restructure" verdict that met the
spec's routing rule gets the pre-approved drafter restructure (main
session owns all coupling decisions — Status, Depends-on, Touch, Group —
and authors every Acceptance command; drafters produce Goal/Steps prose
only); anything else lands as an explicit deferral with reason. The R5
no-op guard is satisfied: at least one concrete outcome exists, or an
"already optimal" certification backed by the task-01 numbers is appended
to the findings doc. Any skill-file edit ships mirrored + version-bumped.

## Touch

The three audited skill files, their antigravity mirrors, the plugin
manifest, and the findings doc (append outcomes only). Do NOT touch
`.claude/skills/drain/*` (the drain-wake-cost spec owns it) or
`.claude/skills/parallel/*` (out of scope). Restructures for /build or
/idea are NOT pre-approved — if a verdict calls for one, write the
proposal into ## Deferred questions for a /critique pass instead of
implementing it here.

## Steps

1. Read `docs/orchestrator-share-findings.md` and ../SPEC.md's routing
   rule. Map each verdict to its outcome branch before editing anything;
   record the mapping in your plan block.
2. Land doctrine-violation fixes: a targeted instruction at the exact
   violating step the findings name — never general exhortation.
3. If /breakdown's verdict is "restructure" under the routing rule, apply
   the pre-approved shape to its SKILL.md dispatch steps. Keep the
   existing decomposition procedure, machine-read field contracts, and
   the "Dispatch authoring" citations intact; drafters get pinned
   headers + acceptance-command contract handed TO them, and write task
   files directly.
4. Append the outcome per skill to the findings doc (one line each:
   landed / deferred+reason / certified-optimal).
5. For any `.claude/skills/*` edit: port the change to the antigravity
   mirror (paraphrased port — content-coverage, not byte-identity), bump
   `version` in `.claude-plugin/plugin.json`, and run the gates. The bump
   is race-safe against the other agentprof-spec drains: `git pull
   --rebase` immediately before bumping, read the version from HEAD, set
   next patch, commit, push; on a rejected push or version-line conflict,
   take the highest version present and increment once more, then retry.
   Never resolve by reverting another spec's bump.

## Acceptance

- [ ] Each verdict in the findings doc has an appended outcome line (landed / deferred with reason / certified-optimal backed by task-01 numbers) — quote them as evidence (R3, R5)
- [ ] For each doctrine violation the findings named, `git -C /Users/sjaconette/claude log -p` shows a skill-text diff at that step, or the findings state none were found (R2)
- [ ] If any `.claude/skills/*` file changed: `bash /Users/sjaconette/claude/evals/lint-ultra-gate.sh` → exit 0, `cd /Users/sjaconette/claude && claude plugin validate .` → pass, mirror updated (content-coverage grep for the new concepts) and plugin.json version bumped in the same commit
- [ ] MANUAL (deferred, needs post-change runs): next 7-day profile shows /breakdown orchestrator share materially below the 84% baseline, or the findings doc justified keeping it
