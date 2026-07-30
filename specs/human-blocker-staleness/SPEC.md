# Human blockers carry a staleness probe

Priority: P1

## Problem

`HUMAN.md`'s `## Agent-filed blockers` section is the durable queue of things
only a human can do. It is append-only prose: an agent files an entry, and
nothing ever re-reads it against the world. `.claude/rules/human-blockers.md`
asks for the one discipline that would help — "File and resolve in the same
commit" — but that only works when the resolving change happens in this repo,
in that commit, by an agent that knows the entry exists. It cannot work when
the condition dissolves somewhere else.

A triage of the 17 live entries on 2026-07-29 found **11 of them (65%) were no
longer human decisions**, in three distinct classes:

- **Unanswerable as written (6).** The six 2026-07-26 entries each ask whether
  a `retain`-class test may move to `repair`. Until commit `3bc58f87` the
  inventory checker rejected a fragment re-declaring a baseline identity as a
  duplicate, and `BASELINE.json` is pinned to its first committed blob, so no
  answer the human gave could have been executed. Six bd issues
  (`agentic-00w`, `-5dw`, `-7c7`, `-cz8`, `-pvl`, `-3pj`) sat blocked behind a
  question with no legal answer.
- **Answered by fact (4).** The four 2026-07-22 entries ask whether
  `~/automation`, `~/fooszone`, `~/interview-prep`, and `~/portfolio-tracker`
  should adopt bd. All four already run live bd queues — 24, 251, 29, and 20
  issues respectively. The decision was settled in practice; only the
  contradictory docs remain, which is agent work.
- **Premise retired (1).** The 2026-07-19 `Status: obsolete` entry rests on
  "the scanner flags them as unrecognized". `specs/status.sh` is bd-backed now
  and reports clean, and `CLAUDE.md:201` states `Status:` headers are frozen
  display that no live procedure reads.

Every one of those was detectable by a command that costs under a second:
run `specs/status.sh`, run `bd list` in four repos, run the inventory checker.
Nobody ran them because no entry says what to run. The staleness is not
carelessness; it is a missing field.

## Solution

Give each blocker a runnable probe and a checker that runs them.

Extend the entry grammar in `.claude/rules/human-blockers.md` with a mandatory
final `Still-blocked:` clause naming a command that **exits 0 while the
blocker genuinely still holds**. A nonzero exit means the world moved and the
entry must be re-read. Blockers with no machine-observable condition take the
one legal escape, `Still-blocked: none — <reason>`, which mirrors the
`Depth ceiling:` annotation grammar in
`docs/memory/anchored-acceptance-criteria.md`: it legalizes the gap explicitly
rather than letting an unprobed entry pass as a probed one.

A new `bin/check-human-blockers` parses the section, runs every probe under a
bounded timeout, and sorts entries into still-blocked, stale, and unprobed.
`/drain`'s batch interview — the stage that already surfaces blockers to the
human — runs it first and excludes stale entries from what it presents, so the
fix arrives at the moment a human is about to spend attention on the list.

The checker deliberately does not join `scripts/check.sh`'s default path: that
gate already runs 5m10s (`agentic-7c7`), and probes may reach other repos.

## Requirements

R1. `.claude/rules/human-blockers.md` defines a mandatory `Still-blocked:`
clause as the final element of the entry line, states the exit-code contract
(0 = still blocked, nonzero = stale), and defines `none — <reason>` as the
only legal escape.

R2. A probe is read-only and bounded: it may not write to any repository, and
the checker runs it under a timeout (default 20s, overridable by
`HUMAN_BLOCKER_PROBE_TIMEOUT`). A probe that times out is reported as
`unknown`, never silently treated as still-blocked.

R3. `bin/check-human-blockers` parses `## Agent-filed blockers`, runs each
entry's probe, and prints three labelled buckets — still-blocked, stale,
unprobed — always listing the unprobed ones with their stated reasons.

R4. The checker's exit code is `0` when every probed entry is still blocked,
`1` when at least one probe exits nonzero (stale entries named with their date
and source path), and `2` when any entry is missing or malforms its
`Still-blocked:` clause. A filing violation is therefore louder than a stale
entry, not quieter.

R5. Checked entries above and below the machine-owned section are untouched,
and the checker never writes to `HUMAN.md` — it reports, a human or a later
commit resolves. This preserves the section-scoped-edits rule already in
`.claude/rules/human-blockers.md`.

R6. `/drain`'s batch interview runs `bin/check-human-blockers` before batching
blockers for the human, presents only entries whose probes still hold, and
states the count of stale entries it withheld and where to re-read them.

R7. `tests/test_human_blockers.sh` drives the checker against fixture
`HUMAN.md` files covering: an entry whose probe exits 0, one whose probe exits
nonzero, one missing the clause, one using `none — <reason>`, and one whose
probe hangs past the timeout.

R8. The repository's own 17 entries are migrated: the 6 genuinely-open entries
gain probes, and the 11 identified in Problem are resolved — the 4 cross-repo
entries retyped as agent work and filed in bd, the 1 retired-premise entry
deleted, and the 6 retain-versus-repair entries repointed at `agentic-umqo`,
which already owns re-reading them against the supersession mechanism.

R9. `tests/test_human_blockers.sh` is registered in `tests/inventory/` so the
runner executes it, and classified in a `specs/toolkit-core-simplification/
surface-inventory/` fragment so the surface check passes.

## Out of scope

- **Collapsing `HUMAN.md` and bd into one source of truth.** The rule keeps a
  blocked bd issue with its typed `Unblock:` *and* a `HUMAN.md` pointer, which
  is duplication maintained by hand. `agentic-mqyj` owns that reconciliation.
  A probe makes the duplication survivable, which is this spec's whole claim;
  removing it is a separate change.
- **Rendering `HUMAN.md` from bd.** Same reason.
- **Other repositories' `HUMAN.md` files.** `~/hub` and `~/fooszone` carry
  their own; rolling the grammar out is a follow-on once it has run here.
- **Answering any of the 17 blockers on the human's behalf.** R8 migrates and
  resolves only the entries whose staleness is already demonstrated in
  Problem.

## Acceptance criteria

- [ ] `grep -c 'Still-blocked:' .claude/rules/human-blockers.md` → ≥ 3
      (verified 0 today, 2026-07-29) — covers R1. L1: artifact structure.
- [ ] `grep -c 'HUMAN_BLOCKER_PROBE_TIMEOUT' bin/check-human-blockers` → ≥ 1
      (file absent today, 2026-07-29) — covers R2.
- [ ] `bash tests/test_human_blockers.sh` exits 0 and reports 0 failures —
      covers R3, R4, R5, R7. L2: behavioral, driven against fixtures.
- [ ] In that suite, a fixture whose single entry probes `false` makes the
      checker exit 1 and print that entry's date and source path; a fixture
      whose entry omits the clause makes it exit 2; a fixture whose probe
      sleeps past a 1s `HUMAN_BLOCKER_PROBE_TIMEOUT` reports `unknown` and
      does not report still-blocked — covers R2, R4.
- [ ] `grep -c 'check-human-blockers' .claude/skills/drain/SKILL.md` → ≥ 1
      (verified 0 today, 2026-07-29) — covers R6. L1; the behavioral
      complement is the eval scenario below.
- [ ] `bash evals/run.sh drain` passes with a scenario seeding one still-blocked
      and one stale entry, asserting the batch interview presents the first and
      names the second as withheld — covers R6 at L2.
- [ ] `grep -c '^- \[ \]' HUMAN.md` → ≤ 6 (17 today, 2026-07-29) and
      `bin/check-human-blockers` exits 0 against the real file — covers R8.
- [ ] `bash tests/test_check_manual_inventory.sh` and
      `python3 scripts/inventory-core-surface.py --root . --check
      specs/toolkit-core-simplification/BASELINE.json` both report no
      diagnostics — covers R9.
- [ ] End to end: file a new blocker through the rule's grammar, make its
      probe start passing, and confirm `/drain`'s batch interview withholds it
      and names it — the full loop this spec exists to close.

## Open questions

None.
