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

Every one of those was decidable by a check costing under a second: run
`specs/status.sh`, look for a bd queue in four repos, run the inventory
checker. Nobody ran them because no entry says what to run. The staleness is
not carelessness; it is a missing field.

## Solution

Give each blocker a runnable probe and a checker that runs them.

Extend the entry grammar in `.claude/rules/human-blockers.md` with a mandatory
final `Still-blocked:` clause. A new `bin/check-human-blockers` resolves and
runs each probe, then sorts entries into still-blocked, stale, unknown,
unprobed, and violation. `/drain`'s batch interview — the stage that already
surfaces blockers to the human — runs it first and withholds stale entries, so
the fix arrives at the moment a human is about to spend attention on the list.

**A probe selects reviewed code; it never supplies a command.** The clause
names a script in `scripts/blocker-probes/` plus literal arguments — not a
command line. This is the load-bearing design decision, and it is a correction:
an earlier draft allowlisted leading binaries (`git`, `bash`, `python3`, `bd`),
which is not a boundary at all. Verified on this machine, no shell and no
metacharacter: `git -c alias.p='!touch PWNED' p` exits 0 and creates the file.
`git` is an arbitrary-code-execution primitive, as are `bash` and `python3`,
so any design that lets an entry name a binary is escapable by construction.

That matters because `.claude/rules/untrusted-data.md` binds here: `HUMAN.md`
is file content, its entries are composed from critique findings, other repos'
docs, and bd issue text, and a `git pull` can introduce an entry no local agent
wrote — which `/drain` would then execute. Under the probe-script model the
executable surface is code that lives in the repo and passed review; a hostile
entry can at worst select a reviewed probe or name one that does not exist.

The polarity is fixed by the same decision. The contract is that a probe
**exits 0 while the blocker still holds**, and the natural commands run the
other way: `bd list` in `~/automation` exits 0 precisely because the queue
exists, which is what makes that blocker stale. Probe scripts exist to carry
that inversion, and R2 requires it rather than leaving each author to discover
it.

The checker deliberately does not join `scripts/check.sh`'s default path: that
gate already runs 5m10s (`agentic-7c7`), and probes may reach other checkouts.

## Requirements

R1. `.claude/rules/human-blockers.md` defines a mandatory `Still-blocked:`
clause as the final element of the entry line and states the three-value
exit-code contract: **0 = still blocked**, **3 = cannot determine**, any other
nonzero = stale. The third value exists because "I could not tell" must not
collapse into "the blocker dissolved" — R7 withholds stale entries, so mapping
an unreachable checkout onto stale would hide a live blocker from the human,
which is this spec's own failure mode inverted. The parse rule is explicit: the
clause is the text following the **last** occurrence of ` — Still-blocked: `
on the line, through end of line — the existing `<plain-language action>` prose
already contains ` — ` internally, so position alone is not a parse rule.
`Still-blocked: none — <reason>` is the only legal escape. Adding a missing
clause to an existing entry is the one sanctioned exception to the rule's
"existing entries are not rewritten or reordered" mandate — without it, R9's
migration and any clause-less entry arriving by merge would be unrepairable
violations. The clause requirement is retroactive: every unchecked entry needs
one, whenever it was filed.

R2. A probe clause is `<name> [arg …]`, never a command line:

- `<name>` matches `^[a-z0-9][a-z0-9-]*$` and resolves to
  `scripts/blocker-probes/<name>`, **relative to the git root containing the
  `HUMAN.md` being parsed** — the same directory used as the probe's cwd — so
  each repository supplies its own probes. A name containing `/`, `.`, or any
  other character is a violation. `none` is reserved and is not a legal probe
  name; the escape is recognized by matching the clause exactly as `none`
  followed by ` — `. There is no allowlist of binaries, because a binary
  allowlist is not a boundary — see Solution.
- Arguments are split with POSIX shell-word lexing (`shlex.split(posix=True)`:
  single and double quotes, backslash escapes, no expansion of any kind). An
  unbalanced quote is a violation. Arguments are passed as argv to the script
  and are never re-interpreted; the script is executed directly, **never
  through a shell** — no `sh -c`, no `eval`.
- The raw clause must contain no ASCII control characters and no newline. No
  metacharacter ban is needed beyond that: with no shell anywhere in the path,
  `;` and `|` inside an argument are inert bytes handed to a reviewed script.
- The probe runs with cwd set to the git root containing the `HUMAN.md` being
  parsed, inheriting the caller's environment, under a timeout (default 20s,
  overridable by `HUMAN_BLOCKER_PROBE_TIMEOUT`).

R3. Probe scripts under `scripts/blocker-probes/` are ordinary reviewed code
and carry the contract the clause cannot express: they exit 0 while the
blocker holds, so a condition whose natural command has inverted polarity
(`bd list` succeeding *because* the blocker dissolved), or whose signal lives
in stdout rather than an exit code (`specs/status.sh`), is inverted or parsed
inside the script. Each script is read-only, self-guards any path it does not
control — a probe whose target checkout is absent exits 3 (cannot determine),
never 0 or 1 — and is usable from any clone of this repository.

**A probe treats its argv as untrusted.** The clause's arguments come from the
same hostile-input channel as the rest of the entry, so a script accepts either
no arguments or arguments validated against an explicit fixed set enumerated in
the script itself. It never uses an argument as a path it executes in, as a
repository it runs a VCS command against, or as a string interpolated into a
command. Without this, the round-2 bypass relocates: a probe of the plausible
shape `git -C "$1" …` executes code when pointed at an attacker-planted
directory carrying `core.fsmonitor` or `core.sshCommand` in its `.git/config`,
with no shell anywhere in the path.

R4. `bin/check-human-blockers [path/to/HUMAN.md]` — defaulting to the git
root's `HUMAN.md` — parses only unchecked `- [ ]` entries inside
`## Agent-filed blockers`; `- [x]` entries are skipped entirely, per the
existing "tools skip checked entries" rule. It reports five labelled buckets:
**still-blocked** (exit 0), **stale** (nonzero other than 3, within the
timeout), **unknown** (exit 3 "cannot determine", timed out, or the script
could not be executed), **unprobed**
(`none — <reason>`, always listed with its reason), and **violation** (a
missing or malformed clause, an unresolvable or non-executable probe name, or
an unbalanced quote).

R5. Exit codes: `0` when no entry is stale and none is a violation; `1` when
at least one probe is stale, each named with its date and source path; `2`
when any entry is a violation. Exit 2 outranks exit 1 — a filing violation is
louder than a stale entry. An `unknown` never sets exit 1 and never counts as
still-blocked; it leaves the exit code determined by the other buckets.

R6. The checker never writes to `HUMAN.md`, never creates or modifies any file,
and never touches prose above or below the machine-owned section — it reports,
and a human or a later commit resolves.

R7. `/drain`'s batch interview runs `bin/check-human-blockers` before batching
blockers for the human and routes every bucket explicitly: present
still-blocked, unprobed, and unknown entries; withhold only stale ones, stating
their count and where to re-read them. On exit 2, present the violating entries
verbatim alongside the grammar violation rather than withholding or aborting.

R8. `tests/test_human_blockers.sh` drives the checker against fixture
repositories covering: a probe exiting 0; a probe exiting nonzero; a missing
clause; `none — <reason>`; a probe that hangs past the timeout; a `- [x]`
entry whose clause is absent (must not trip exit 2); an unbalanced quote; a
probe whose target sibling path is deliberately absent, asserted to exit 3 into
the unknown bucket without setting exit 1; and four **hostile clauses**, each
asserted to leave no sentinel file.

Three die at name resolution with exit 2 — `bd list; touch SENTINEL`,
`git -c alias.p=!touch\ SENTINEL p`, and `../../../bin/evil`. The fourth
exercises the **argument** grammar, which none of the first three reach: a real
fixture probe invoked with a hostile argument — a path to a planted directory
whose `.git/config` sets `core.fsmonitor` — asserted to leave no sentinel. That
case is what proves R3's argv rule rather than R2's name rule, and its absence
is what would let the round-2 bypass relocate into the scripts.

Every fixture case additionally asserts the fixture
`HUMAN.md`'s sha256 is unchanged and the fixture directory gained no files,
which is the only observation that can prove R6.

R9. The repository's own 17 entries are migrated: the 6 genuinely-open entries
gain a probe or `none — <reason>`, with any needed scripts added under
`scripts/blocker-probes/`, and the 11 identified in Problem are resolved — the
4 cross-repo entries retyped as agent work and filed in bd, the 1
retired-premise entry deleted, and the 6 retain-versus-repair entries repointed
at `agentic-umqo`, which already owns re-reading them against the supersession
mechanism.

R10. `tests/test_human_blockers.sh` is registered in a new `tests/inventory/`
fragment with `"disposition": "repair"`, and classified in a new
`specs/toolkit-core-simplification/surface-inventory/` fragment — also
`repair`, carrying `git_blob_pin: 1`, a `frozen_sha256` over the canonical
object without that field, and a behavioral pointer of the form
`tests/test_human_blockers.sh#assert:<sha256>`. `repair` is named explicitly:
freezing this test as `retain` on the day it lands would re-create the deadlock
the Problem section documents.

R11. The `/drain` eval scenario proving R7 provisions what `evals/run.sh` does
not — it seeds `.claude/skills/_shared`, `runtimes/`, and agents into each
fixture, but neither `bin/` nor `scripts/` — so the scenario's `setup.sh`
copies `bin/check-human-blockers` and `scripts/blocker-probes/` into the
fixture and authors a hermetic `HUMAN.md` whose probes are deterministic and
local, never reaching a foreign checkout.

## Out of scope

- **Collapsing `HUMAN.md` and bd into one source of truth.** The rule keeps a
  blocked bd issue with its typed `Unblock:` *and* a `HUMAN.md` pointer, which
  is duplication maintained by hand. `agentic-mqyj` owns that reconciliation.
  A probe makes the duplication survivable, which is this spec's whole claim;
  removing it is a separate change.
- **Rendering `HUMAN.md` from bd.** Same reason.
- **Other repositories' `HUMAN.md` files.** `~/hub` and `~/fooszone` carry
  their own; rolling the grammar out is a follow-on once it has run here, and
  it inherits R2's execution model unchanged.
- **Letting a clause name a binary.** Settled against in Solution; reopening it
  is a spec change, not a worker's call.
- **Answering any of the 17 blockers on the human's behalf.** R9 migrates and
  resolves only the entries whose staleness is already demonstrated in Problem.

## Acceptance criteria

- [ ] `bash tests/test_human_blockers.sh` exits 0 reporting 0 failures, and
      its cases cover every R8 fixture — covers R1, R2, R4, R5, R6, R8.
      **L2**: behavioral, driven against fixture repositories.
- [ ] Within that suite, each of the three name-grammar hostile clauses yields
      exit 2 and `test ! -e "$FIXTURE/SENTINEL"` passes — refused, not merely
      reported. The `git -c alias` case is the one that matters: it is the
      bypass that defeated the previous binary-allowlist design — covers R2.
      **L2**.
- [ ] Within that suite, the argument-grammar hostile case — a real fixture
      probe handed a planted `.git/config` directory — leaves no sentinel,
      whatever exit code it produces — covers R3's argv rule. **L2**; the three
      criteria above all die at name resolution and prove nothing about
      arguments.
- [ ] Within that suite, the absent-sibling-path probe lands in the unknown
      bucket with exit 0, and no probe returning 3 is ever reported stale —
      covers R1's three-value contract and R3's self-guard. **L2**; without
      this, an unreachable checkout reads as "dissolved" and R7 withholds a
      live blocker.
- [ ] Within that suite, every case asserts the fixture `HUMAN.md`'s sha256 is
      byte-identical before and after the run and that the fixture directory
      gained no files, including on the exit-2 and timeout cases — covers R6.
      **L2**; this is the only observation that distinguishes a reporting
      checker from a rewriting one.
- [ ] Within that suite: a probe exiting nonzero yields exit 1 naming the
      entry's date and source path; a missing clause yields exit 2; a probe
      sleeping past `HUMAN_BLOCKER_PROBE_TIMEOUT=1` lands in unknown with exit
      0; a `- [x]` entry lacking a clause does not trip exit 2; an unbalanced
      quote yields exit 2 — covers R4, R5. **L2**.
- [ ] `grep -c 'Still-blocked:' .claude/rules/human-blockers.md` → ≥ 3
      (verified 0 today, 2026-07-29) — covers R1. **L0**, gameable by typing
      the literal; its behavioral complement is the missing-clause fixture,
      which proves the grammar is enforced rather than merely written.
- [ ] `ls scripts/blocker-probes/` lists at least one executable script, and
      each one exits 0 and nonzero on inputs the suite fixes — covers R3.
      **L2**; a probe script with no test is a probe nobody has run.
- [ ] `grep -c 'check-human-blockers' .claude/skills/drain/SKILL.md` → ≥ 1
      (verified 0 today, 2026-07-29) — covers R7 at **L0**; behavioral
      complement is the eval scenario below.
- [ ] `bash evals/run.sh drain` passes for the single new scenario, whose
      fixture seeds five entries — still-blocked, stale, `none —`, one timing
      out, and one with no clause — asserting the interview presents the
      still-blocked, unprobed, and unknown entries, names the stale one as
      withheld, and surfaces the clause-less one verbatim as a violation —
      covers R7, R11 at **L2**. `manual-pending`: an unattended worker must not
      launch a paid nondeterministic eval
      (`docs/memory/unattended-worker-tool-limits.md`), so a human runs this
      one and records the result on the task.
- [ ] `grep -c '^- \[ \]' HUMAN.md` → ≤ 6 (17 today, 2026-07-29), and
      `bin/check-human-blockers` against the real file exits 0 with its
      still-blocked plus unprobed buckets together listing exactly the
      surviving entries and its stale and violation buckets empty, **on a
      fresh clone of this repository with no sibling checkouts present** —
      covers R3's self-guarding requirement and R9. **L1**; a bare "exits 0"
      would pass on a parser that found nothing, so bucket contents are
      asserted, and the fresh-clone condition is what proves the probes are
      portable rather than machine-specific.
- [ ] `bash tests/test_check_manual_inventory.sh` reports OK and
      `python3 scripts/inventory-core-surface.py --root . --check
      specs/toolkit-core-simplification/BASELINE.json` prints no diagnostic
      lines, with both new fragments carrying `"disposition": "repair"` —
      covers R10. **L2**.
- [ ] End to end: file a new blocker through the rule's grammar, make its
      probe start **failing (nonzero)**, and confirm `/drain`'s batch interview
      withholds it and names it as withheld — the full loop this spec exists to
      close. `manual-pending`: drives `/drain` interactively; a human runs it
      and records the outcome on the task.

## Open questions

None.
