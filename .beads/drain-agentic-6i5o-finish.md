Depends on: none
Priority: P1
Budget: 30 turns
Touch: HUMAN.md, specs/human-blocker-staleness/tasks/02-probes-and-migration.md
Rigor: production

# agentic-6i5o (completion) — collapse the duplicate blocker pairs, re-baseline the bound

## Situation

The branch `drain/agentic-6i5o` already carries this task's real deliverable:
`scripts/blocker-probes/` with its contract suite, and the `Still-blocked:`
clause migration. All of that is committed and its targeted tests are green.
It returned DEFERRED for one reason only — its acceptance bound says `HUMAN.md`
must hold at most 6 open entries, and it holds more.

The bound was authored against a `HUMAN.md` that no longer exists. Of the open
entries, some are survivors of the spec's 17-entry triage; four are Mardi Gras
manual-pending entries filed by commit `6440f60e` AFTER that triage, each
already carrying a compliant `Still-blocked:` clause. Reaching 6 would mean
deleting live human blockers the spec puts out of scope.

## Human decision, 2026-07-30

Collapse the duplicate pairs first, then re-baseline the bound. Deleting live
blockers was declined.

Tasks 26 and 27 are the repair-wave re-runs of tasks 07 and 12. Each pair asks
a human for the same thing twice:

    26-prove-final-installed-native-facades.md   pairs with  07-prove-installed-native-facades.md
    27-certify-production-cutover-repair.md      pairs with  12-certify-production-cutover.md

Merge each pair into ONE entry that covers both source tasks, so no distinct
blocker is lost. The surviving entry must name both source paths and state the
combined ask in plain language, per `.claude/rules/human-blockers.md`'s entry
grammar — including a `Blocks:` clause and a `Still-blocked:` clause as the
final element.

## Scope and order

1. Sync this branch onto current main FIRST. `HUMAN.md` differs between main
   and the branch (main has more open entries), so any count taken before the
   sync is meaningless. Resolve conflicts preserving BOTH main's entries and
   this branch's clause migration; if a conflict is not mechanically obvious,
   stop with verdict BLOCKED and describe it.
2. Record the post-sync open-entry count before changing anything:
   `grep -c '^- \[ \]' HUMAN.md`. Call this N. State N in your return.
3. Collapse the two Mardi Gras pairs. This removes exactly 2 entries.
4. Re-baseline the task file's bound to the resulting count.

Touch only the `## Agent-filed blockers` section — prose outside it is
human-owned. Do not delete, reword, or reorder any entry other than the four
Mardi Gras ones named above.

## Acceptance

- [ ] A1 (cheap): `git merge-base --is-ancestor main HEAD` succeeds — the
      branch carries current main.
- [ ] A2 (cheap): `grep -c '^- \[ \]' HUMAN.md` equals **N − 2**, where N is
      the post-sync count you recorded in step 2. State both numbers in your
      return. The bound is pinned to the collapse, not fitted to whatever the
      file happens to contain — if the result is not exactly N − 2, report
      that rather than adjusting the expected value.
- [ ] A3 (cheap): exactly one open entry references
      `26-prove-final-installed-native-facades.md`, and that same entry also
      references `07-prove-installed-native-facades.md`. Same for
      `27-certify-production-cutover-repair.md` paired with
      `12-certify-production-cutover.md`. Show the two surviving lines.
- [ ] A4 (cheap): every open entry still carries a `Still-blocked:` clause as
      the final element of its line — the two merged entries included.
      `grep -c '^- \[ \]' HUMAN.md` equals
      `grep -c 'Still-blocked:' HUMAN.md` restricted to those same lines.
- [ ] A5 (cheap): every open entry carries a `Blocks:` clause, the merged ones
      included.
- [ ] A6 (cheap): `bin/check-human-blockers` runs and reports zero violations.
      Include its summary output in your return.
- [ ] A7 (cheap): the task file's re-baselined bound now matches the actual
      count, and the task file records in one line WHY it moved — that the
      original 6 predated commit `6440f60e`. Do not silently change the
      number.
- [ ] A8 (cheap): `bash tests/test_blocker_probes.sh` exits 0 with 0 failures
      — the probe work already on this branch does not regress.
- [ ] A9 (cheap): no entry outside the four Mardi Gras ones changed:
      `git diff main...HEAD -- HUMAN.md` shows removals only for those four
      source lines and additions only for the two merged replacements.

## Notes

Do not run `scripts/check.sh`; drain runs the canonical gate once after an
independent review barrier.

`grep` here is a shell function wrapping ugrep 7.5.0, which omits the leading
`./` that GNU and BSD grep emit when recursing `.`; a `grep -v '^\./…'`
exclusion silently matches nothing
(docs/memory/anchored-acceptance-criteria.md).
