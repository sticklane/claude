# Task 02: real probe scripts and the migration of the 17 entries

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 01
Priority: P1
Budget: 30 turns
Spec: ../SPEC.md (requirements R3, R9)
Touch: scripts/blocker-probes, HUMAN.md, tests/test_blocker_probes.sh, tests/inventory/08-blocker-probe-scripts.json, specs/toolkit-core-simplification/surface-inventory/08-blocker-probe-scripts.json

## Goal

`scripts/blocker-probes/` holds reviewed probe scripts that carry the exit
contract, treat their argv as untrusted, and return 3 rather than guessing when
a target checkout is absent. `HUMAN.md` drops from 17 open entries to at most
7, each carrying a probe or `none — <reason>`, and
`bin/check-human-blockers` exits 0 against it on a fresh clone.

## Touch

Owns `scripts/blocker-probes/` and `HUMAN.md`. Must NOT edit
`bin/check-human-blockers`, `.claude/rules/human-blockers.md`, or
`tests/test_human_blockers.sh` — task 01 owns the mechanism and its suite, and
a bug found in them is reported to the orchestrator, not fixed here. Probe
tests go in a separate `tests/test_blocker_probes.sh` for that reason. Must NOT
edit `.claude/skills/drain/SKILL.md` (task 03).

## Steps

1. Write the failing test first: `tests/test_blocker_probes.sh` drives each
   shipped probe and asserts it returns 0, nonzero, and 3 on inputs the test
   constructs, and that a probe handed an unexpected argument refuses rather
   than acting on it.
2. Author the probes the 6 surviving entries need. Each inverts polarity where
   the natural command runs the other way — `bd list` in a foreign checkout
   exits 0 precisely *because* that blocker dissolved — and parses stdout where
   the signal is not an exit code, as with `specs/status.sh`.
3. Each probe takes no arguments or validates them against a fixed set
   enumerated in the script. No probe uses an argument as a path it executes
   in, a repository it runs a VCS command against, or a string interpolated
   into a command.
4. Migrate the 11 resolved entries per the spec's Problem section: retype the
   4 cross-repo bd-adoption entries as agent work and file them in bd (all four
   repos already run live bd queues, so what remains is doc reconciliation);
   delete the 1 `Status: obsolete` entry whose scanner premise retired; and
   repoint the 6 retain-versus-repair entries at `agentic-umqo`.
5. Give each of the 6 survivors a probe or `none — <reason>`. Three are not
   mechanically probeable — the agentprof live-history run, the OTel capture,
   and the two agentprof scope decisions — so `none` with a stated reason is
   the honest answer there, not a contrived probe.
6. Register `tests/test_blocker_probes.sh` in both inventories with
   `"disposition": "repair"`, same fragment shape as task 01's.

## Acceptance

- [ ] `bash tests/test_blocker_probes.sh` → exits 0, reports 0 failures. **L2**
- [ ] `grep -c '^- \[ \]' HUMAN.md` → ≤ 7 (17 today, 2026-07-29). **L1** — the
      bound was 6 when authored; that number predated commit `6440f60e`, which
      filed four Mardi Gras manual-pending entries after this spec's triage.
      Collapsing the two duplicate Mardi Gras pairs into one entry each leaves
      7, and deleting live blockers to reach 6 was declined (2026-07-30).
- [ ] `bin/check-human-blockers` → exits 0, with its stale and violation
      buckets empty and its still-blocked, unprobed, and unknown buckets
      together listing exactly the surviving entries. **L2**
- [ ] Run in a fresh clone with no sibling checkouts —
      `git clone -q . "$T/c" && cd "$T/c" && bin/check-human-blockers` → exits
      0. This is what proves the probes self-guard rather than assuming this
      machine's layout. **L2**
- [ ] `for p in scripts/blocker-probes/*; do test -x "$p" || exit 1; done` →
      exits 0. **L1**
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
- [ ] Every entry the migration resolves is either deleted from `HUMAN.md` or
      filed in bd with its new type, and no entry is left both in `HUMAN.md`
      and closed in bd. **L1** — Depth ceiling: cross-surface consistency
      between a markdown list and a tracker has no runnable check here;
      the verifier is instructed to read both and report any entry present in
      one and resolved in the other.
