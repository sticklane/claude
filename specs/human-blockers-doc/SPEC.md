# HUMAN.md: one standardized place for human blockers

Status: open
Priority: P1

## Problem

Things only a human can do surface today in four scattered places, none
durable: drain's seven-section exit checklist (a final MESSAGE — it
scrolls away with the session), `Unblock: ask:` lines buried in
individual task files, MANUAL-PENDING acceptance criteria noted in
evidence files, and hand-written notes like ~/automation/HUMAN.md.
Steven's ask (2026-07-12): "standardize how we document human blockers,
in a human.md." Yesterday's runs illustrate the cost: the 2026-07-11
evening sweep ended with one deferred question, one decision-shaped
stub, two manual-pending measurements, and 13 NOT-READY specs — all
reported in a transcript message; anyone resuming later must re-derive
the list from task-file greps. The one existing HUMAN.md
(~/automation's, 79 lines) is excellent hand-written narrative but has
no machine-writable region, so agents cannot maintain it.

## Solution

A repo-root `HUMAN.md` with a machine-owned section, `## Agent-filed
blockers`, appended to by drain and /build under a fixed one-line entry
grammar and cleared on resolution — coexisting with any hand-written
narrative above it (agents never touch prose outside the section).
Workboard's needs-attention inbox reads the section across repos. The
grammar mirrors the existing `Unblock:` types so nothing is invented:

```
- [ ] <ISO date> · <source path> · <ask|run|provision|decide> — <one-line action, self-contained>
```

`ask` = a question needing an answer (maps to `Unblock: ask:` /
deferred questions); `run` = a command a human must run (manual-pending
measurements, `Unblock: run:` display); `provision` = credentials/
access/purchases; `decide` = a decision-shaped item (stub or spec).
Resolution = the resolving actor deletes the entry (or a human checks
the box for a later sweep to delete) in the same commit that resolves
the source — the section lists OPEN items only, it is not a log.

## Requirements

- R1 **Grammar and section contract.** The entry grammar, the
  `## Agent-filed blockers` section marker, the open-items-only rule,
  the agents-never-edit-prose-outside-the-section rule, and the
  same-commit resolution rule are defined once in a new
  `.claude/rules/human-blockers.md` (always-on rule, small); CLAUDE.md
  gets a one-line pointer. The section is created on first append when
  a repo has no HUMAN.md (file bootstrapped with just a title line and
  the section) and appended into an existing HUMAN.md without touching
  content above or below the section.
- R2 **Drain writes and clears.** Drain's exit checklist step ALSO
  files every human-actionable item into the repo's HUMAN.md in the
  same commit wave — deferred questions (`ask`), `Unblock: ask:` blocked
  tasks (`ask`), `Unblock: run:` blocked tasks (`run`), decision-shaped
  or gate-refused stubs (`decide`), manual-pending evidence lines
  (`run`), NOT-READY specs from critique intake (`decide`). The batch
  interview, when an answer flips a deferred task back to pending,
  DELETES the task's entry in the same commit as the `## Answers` write.
  The checklist message itself is unchanged (it summarizes; HUMAN.md
  persists).
- R3 **Build writes on blocked stops.** /build's same-edit blocked rule
  (Status: blocked + Unblock: in one edit) extends to a three-part
  same-edit: the HUMAN.md entry lands in the same commit, typed to match
  the Unblock: line.
- R4 **Workboard surfaces it.** agent-console's needs-attention inbox
  parses `- [ ]` entries under `## Agent-filed blockers` from each
  scanned repo's HUMAN.md and lists them (date, repo, type, ask) above
  spec/task rows; checked (`- [x]`) entries are skipped. Graceful when
  the file or section is absent.
- R5 **Prior-art alignment.** ~/automation/HUMAN.md gains the
  `## Agent-filed blockers` section (empty, below its narrative) so the
  one existing HUMAN.md conforms; its narrative is untouched.
  (Cross-repo task; automation's own commit conventions.)
- R6 **Mirror + plugin closing.** Drain/build SKILL.md changes mirror to
  the antigravity ports and the codex drain/build wrappers per the
  port-chain convention; plugin version bumped in the closing task's own
  commit; `claude plugin validate .` and `bash evals/lint-ultra-gate.sh`
  pass (drain and build are ultra-path).

## Out of scope

- Migrating historical exit-checklist content or old evidence files into
  HUMAN.md (open items only, going forward).
- Rewriting ~/automation/HUMAN.md's narrative (R5 adds the section only).
- A cross-repo aggregated HUMAN.md (workboard IS the aggregation view).
- Non-blocker human notes (docs/ own those); HUMAN.md's machine section
  is strictly actionable open items.
- The 13 currently NOT-READY specs' content (they become entries when a
  future drain's intake re-encounters them, not retroactively).

## Acceptance criteria

- [ ] `test -f .claude/rules/human-blockers.md && grep -qi 'Agent-filed blockers' .claude/rules/human-blockers.md`
  (anchor 0-hit everywhere today — verified 2026-07-12) AND
  `grep -qi 'human-blockers' CLAUDE.md` (pointer line) (R1)
- [ ] `grep -qi 'Agent-filed blockers' .claude/skills/drain/SKILL.md` →
  hit AND MANUAL: exit-checklist step files all six item types and the
  interview deletes entries on answer, same commit (R2)
- [ ] `grep -qi 'Agent-filed blockers' .claude/skills/build/SKILL.md` →
  hit AND MANUAL: blocked stop is a three-part same-edit (R3)
- [ ] `bash agent-console/scripts/check.sh` → green including a fixture
  pair (HUMAN.md with two open + one checked entry → two inbox rows;
  repo without HUMAN.md → no rows, no error) (R4)
- [ ] `grep -qi 'Agent-filed blockers' /Users/sjaconette/automation/HUMAN.md`
  → hit; narrative above unchanged (`git -C ~/automation diff HEAD~1 --stat`
  shows only the section append) (R5)
- [ ] `claude plugin validate .` passes; `bash evals/lint-ultra-gate.sh`
  OK; plugin version bumped in the closing task's own commit;
  `grep -qi 'Agent-filed blockers' antigravity/.agents/workflows/drain.md`
  → hit (0 today) (R6)

## Open questions

(none — grammar reuses the Unblock: types; placement and ownership
decided in Solution)

## Parallelization

Task map (/breakdown owns final shape): 01 = R1 rule + CLAUDE.md pointer;
02 = R2+R3 skill text (drain + build — NOTE cross-spec caution: the live
drain queue may still hold drain-SKILL.md-touching tasks
(drain-wake-cost/04 extraction); Touch-disjoint admission serializes,
and this spec's 02 should dispatch after that extraction merges to avoid
churning a file mid-relocation); 03 = R4 agent-console inbox; 04 = R5
automation cross-repo append; 05 = R6 closing mirror/bump. 01, 03, 04
pairwise-disjoint.

- Group: 01, 03, 04
