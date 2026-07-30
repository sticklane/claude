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

A new `bin/check-human-blockers` parses the section, runs every probe, and
sorts entries into still-blocked, stale, unknown, and unprobed. `/drain`'s
batch interview — the stage that already surfaces blockers to the human — runs
it first and withholds stale entries, so the fix arrives at the moment a human
is about to spend attention on the list.

**The probe field is executable configuration, and this spec treats it as
hostile input.** `.claude/rules/untrusted-data.md` binds: `HUMAN.md` is file
content, its entries are composed from critique findings, other repos' docs,
and bd issue text, and a `git pull` can introduce an entry no local agent
wrote. So the surface is bounded by construction rather than by a promise —
R2 defines a closed grammar the checker enforces before any execution, and a
probe outside that grammar is refused as a filing violation, never run. That
constraint is enforced at execution time, not at authoring time, so it holds
for entries that arrive by merge.

The checker deliberately does not join `scripts/check.sh`'s default path: that
gate already runs 5m10s (`agentic-7c7`), and probes may reach other
checkouts.

## Requirements

R1. `.claude/rules/human-blockers.md` defines a mandatory `Still-blocked:`
clause as the final element of the entry line and states the exit-code
contract (0 = still blocked, nonzero = stale). The parse rule is explicit: the
probe is the text following the **last** occurrence of ` — Still-blocked: ` on
the line, through end of line — the existing `<plain-language action>` prose
already contains ` — ` internally, so position alone is not a parse rule.
`Still-blocked: none — <reason>` is the only legal escape.

R2. A probe is a closed grammar the checker validates **before** executing
anything:

- It is split into an argv vector on unquoted whitespace and executed
  directly, **never through a shell** — no `sh -c`, no `eval`.
- Its leading token must appear in a stated allowlist: `bd`, `git`, `grep`,
  `test`, `ls`, `python3`, `bash`, and repo-relative script paths beginning
  `./` or `specs/` or `scripts/` or `bin/`.
- The string must contain none of `;`, `|`, `&`, `` ` ``, `$(`, `>`, `<`,
  `\n`. A probe containing any of them, or a leading token outside the
  allowlist, is a **filing violation** (R4's exit 2) and is not executed.
- `bash` and `python3` are allowlisted only with a repo-relative script path
  as their first argument; `bash -c` and `python3 -c` are refused by the
  metacharacter and argument rules above.
- Absolute paths are permitted as arguments — without a shell they are inert
  strings, and cross-checkout probes need them (`git -C /path/to/repo …`,
  `bd --db …`). `~` does not expand and must not be used.

The probe runs with cwd set to the repository root containing the `HUMAN.md`
being parsed, inheriting the caller's environment, under a timeout (default
20s, overridable by `HUMAN_BLOCKER_PROBE_TIMEOUT`).

R3. `bin/check-human-blockers` parses only unchecked `- [ ]` entries inside
`## Agent-filed blockers` — `- [x]` entries are skipped entirely, per the
existing "tools skip checked entries" rule — and reports four labelled
buckets: **still-blocked** (probe exited 0), **stale** (probe exited nonzero
within the timeout), **unknown** (probe timed out or could not be launched),
and **unprobed** (`none — <reason>`, always listed with its reason).

R4. Exit codes: `0` when no entry is stale and none violates the grammar; `1`
when at least one probe is stale, each named with its date and source path;
`2` when any entry is missing or malforms its `Still-blocked:` clause, or
carries a probe R2 refuses. Exit 2 outranks exit 1 — a filing violation is
louder than a stale entry. An `unknown` never sets exit 1 and never counts as
still-blocked; it leaves the exit code determined by the other buckets.

R5. The checker never writes to `HUMAN.md` or to any repository, and never
touches prose above or below the machine-owned section — it reports, and a
human or a later commit resolves.

R6. `/drain`'s batch interview runs `bin/check-human-blockers` before batching
blockers for the human and routes every bucket explicitly: present
still-blocked, unprobed, and unknown entries; withhold only stale ones, stating
their count and where to re-read them. On exit 2, present the malformed entries
verbatim alongside the grammar violation rather than withholding or aborting.

R7. `tests/test_human_blockers.sh` drives the checker against fixture
`HUMAN.md` files covering: a probe exiting 0; a probe exiting nonzero; a
missing clause; `none — <reason>`; a probe that hangs past the timeout; a
`- [x]` entry whose clause is absent (must not trip exit 2); and a **hostile
probe** — `Still-blocked: bd list; touch SENTINEL` — asserted refused with
exit 2 **and not executed**, proven by the sentinel file's absence.

R8. The repository's own 17 entries are migrated: the 6 genuinely-open entries
gain probes or `none — <reason>`, and the 11 identified in Problem are
resolved — the 4 cross-repo entries retyped as agent work and filed in bd, the
1 retired-premise entry deleted, and the 6 retain-versus-repair entries
repointed at `agentic-umqo`, which already owns re-reading them against the
supersession mechanism.

R9. `tests/test_human_blockers.sh` is registered in a new
`tests/inventory/` fragment with `"disposition": "repair"`, and classified in a
new `specs/toolkit-core-simplification/surface-inventory/` fragment — also
`repair`, carrying `git_blob_pin: 1`, a `frozen_sha256` over the canonical
object without that field, and a behavioral pointer of the form
`tests/test_human_blockers.sh#assert:<sha256>`. `repair` is named explicitly:
freezing this test as `retain` on the day it lands would re-create the deadlock
the Problem section documents.

R10. The `/drain` eval scenario proving R6 provisions what `evals/run.sh` does
not — `evals/run.sh` seeds `.claude/skills/_shared`, `runtimes/`, and agents
into each fixture, but not `bin/` — so the scenario's `setup.sh` copies
`bin/check-human-blockers` into the fixture and authors a hermetic `HUMAN.md`
whose probes are deterministic and local (`test -f …`), never reaching a
foreign checkout.

## Out of scope

- **Collapsing `HUMAN.md` and bd into one source of truth.** The rule keeps a
  blocked bd issue with its typed `Unblock:` *and* a `HUMAN.md` pointer, which
  is duplication maintained by hand. `agentic-mqyj` owns that reconciliation.
  A probe makes the duplication survivable, which is this spec's whole claim;
  removing it is a separate change.
- **Rendering `HUMAN.md` from bd.** Same reason.
- **Other repositories' `HUMAN.md` files.** `~/hub` and `~/fooszone` carry
  their own; rolling the grammar out is a follow-on once it has run here, and
  it inherits R2's execution grammar unchanged.
- **Widening R2's allowlist.** Adding a command to it is a spec change, not a
  worker's call.
- **Answering any of the 17 blockers on the human's behalf.** R8 migrates and
  resolves only the entries whose staleness is already demonstrated in
  Problem.

## Acceptance criteria

- [ ] `bash tests/test_human_blockers.sh` exits 0 reporting 0 failures, and
      its cases cover every R7 fixture — covers R1, R3, R4, R5, R7. **L2**:
      behavioral, driven against fixture repositories.
- [ ] Within that suite, the hostile-probe case asserts the checker exits 2
      and `test ! -e "$FIXTURE/SENTINEL"` passes — the probe was refused, not
      merely reported — covers R2's enforcement and R4's precedence. **L2**.
- [ ] Within that suite: a probe exiting nonzero yields exit 1 with the
      entry's date and source path in the output; a missing clause yields exit
      2; a probe sleeping past `HUMAN_BLOCKER_PROBE_TIMEOUT=1` is reported in
      the unknown bucket with exit 0; a `- [x]` entry lacking a clause does not
      trip exit 2 — covers R3, R4, R8's parse safety. **L2**.
- [ ] `grep -c 'Still-blocked:' .claude/rules/human-blockers.md` → ≥ 3
      (verified 0 today, 2026-07-29) — covers R1. **L0**, gameable by typing
      the literal; its behavioral complement is the missing-clause fixture
      above, which proves the grammar is enforced rather than merely written.
- [ ] `bin/check-human-blockers` run against a fixture whose probe is
      `bash -c 'touch X'` exits 2 and leaves no `X` — covers R2's
      shell-refusal rule specifically. **L2**.
- [ ] `grep -c 'check-human-blockers' .claude/skills/drain/SKILL.md` → ≥ 1
      (verified 0 today, 2026-07-29) — covers R6 at **L0**; behavioral
      complement is the eval scenario below.
- [ ] `bash evals/run.sh drain` passes for the single new scenario seeding one
      still-blocked, one stale, and one `none —` entry, asserting the batch
      interview presents the first and third and names the second as withheld
      — covers R6, R10 at **L2**. `manual-pending`: an unattended worker must
      not launch a paid nondeterministic eval
      (`docs/memory/unattended-worker-tool-limits.md`), so a human runs this
      one and records the result.
- [ ] `grep -c '^- \[ \]' HUMAN.md` → ≤ 6 (17 today, 2026-07-29), and
      `bin/check-human-blockers` against the real file exits 0 with its
      still-blocked plus unprobed buckets together listing exactly the
      surviving entries and its stale bucket empty — covers R8. **L1**; a bare
      "exits 0" would pass on a parser that found nothing, so the bucket
      contents are asserted, not just the code. A probe reaching a checkout
      absent on the verifying machine reports `unknown`, which by R4 does not
      fail this criterion.
- [ ] `bash tests/test_check_manual_inventory.sh` reports OK and
      `python3 scripts/inventory-core-surface.py --root . --check
      specs/toolkit-core-simplification/BASELINE.json` prints no diagnostic
      lines, with both new fragments carrying `"disposition": "repair"` —
      covers R9. **L2**.
- [ ] End to end: file a new blocker through the rule's grammar, make its
      probe start **failing (nonzero)**, and confirm `/drain`'s batch interview
      withholds it and names it as withheld — the full loop this spec exists to
      close. `manual-pending`: drives `/drain` interactively; a human runs it
      and records the outcome on the task.

## Open questions

None.
