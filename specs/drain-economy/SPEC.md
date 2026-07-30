# Drain economy, feature-focus scheduling, and per-spec proximity accounting

Status: open
Priority: P1
Breakdown-ready: false

## Problem

A drain run is a stateless pump over a **global, dependency-gated task frontier**: priority attaches at task granularity (`bd ready` is priority-sorted per issue), so priority is fungible across features and the scheduler cannot represent "finish this one." The run owns no state (`.claude/skills/drain/SKILL.md:12-15`, "no baton files... the queue itself is the state"), files every discovered item straight into the queue ("Discovered out-of-scope work is filed, never dropped", SKILL.md:163-164), and ends without reporting a delta. Four user-facing failures follow, all live:

1. **Feature-boundary crossing.** Drain interleaves features by construction — `specs/QUEUE.md`'s Queue 6 combined three specs into one repo-wide drain with hand-woven cross-spec `Depends on:` edges and waves mixing all three. Interleaving N features stretches each one's completion latency ~N× while keeping workers fully busy: task throughput up, finished features down. And since every open feature is a discovery generator, interleaving *funds* multiplication — each revisit of a 60%-done spec files more work (Queue 6's own residue: two discovered stubs "not yet triaged").
2. **Opacity.** The rolling top-up loop (SKILL.md:166-167) never pauses, so it never narrates. `/fleet` shows liveness and `/workboard` shows inventory; nothing shows what this run has accomplished, for which feature.
3. **Work multiplication.** Filed-never-dropped is a ratchet with no admission step, no budget, no severity floor. The repo's history documents the cost: 10-13 draft specs stuck across sessions, a headless generation burned on 5 NOT-READY intakes with zero dispatch progress, queues hitting the retired 10-generation cap without finishing (`specs/critique-findings-loop-closure/SPEC.md`, Problem).
4. **No proximity answer, and silent blocking.** "How close is feature X" has no honest number — task-count denominators inflate exactly when the system works, and remaining count is not remaining distance (the CSS `@layer` case: one task, three failed attempts across two sessions). Worse, on a global frontier a blocked top feature is *silent*: workers stay busy on feature #5 while the most important thing sits stuck, which is exactly the 10-13-stuck-specs incident.

## Solution

Lift priority to the feature and give the run an accounting identity. A human-owned `specs/NOW.md` names the focus (WIP = 1); bare `/drain` drains that feature's dependency closure until done, spilling down the Now list only when the focus frontier is entirely blocked — after attempting mechanical unblocks — and returning to it the moment it unblocks. Featureless `chore` work gets one bounded slot. Discovered work splits into *blocking* (files as today, uncapped — it is scope truth) and *adjacent* (files to a `triage` label, admitted only at the batch interview, capped per run). Every run opens and closes a run bead carrying a computed report (adopting only the run-issue *convention* from parked `specs/agentic-dynamic-workflows/` item 7). Feature side: each spec's `## Acceptance criteria

Every criterion is read-only per D12: nothing here mutates bd, the working
tree, or any live surface — state a criterion needs, it builds under
`mktemp -d` inside the test it names. `cheap` criteria run unattended under
D11; the one `expensive` criterion is a paid eval only a human launches, whose
result a human records in `acceptance-status.json`.

- [ ] A1 (cheap): `bash tests/test_command_policy.sh` — the D11 policy accepts an allowlisted argv-0, refuses a shell metacharacter, refuses an unresolvable name, and its rejection path leaves no sentinel (D11, task 00)
- [ ] A2 (cheap): `grep -c 'blocking iff' .claude/skills/drain/SKILL.md` — ≥ 1; the discriminator wording is present in the filing step (EP1)
- [ ] A3 (cheap): `bash tests/test_drain_triage_economy.sh` — a `triage`-labeled fixture issue never appears in the ready set, an unlabeled one does, and stripping the label returns it (EP2)
- [ ] A4 (cheap): `grep -c 'DRAIN_TRIAGE_CAP' .claude/skills/drain/reference.md` — ≥ 1 with default 5 stated (EP3)
- [ ] A5 (cheap): `grep -c 'severity floor' .claude/skills/drain/SKILL.md` — ≥ 1 with the rule-citation requirement adjacent (EP4)
- [ ] A6 (cheap): `bash tests/test_drain_run_bead.sh` — the run-log grammar parses into per-closure records, a malformed line is rejected, and the 24h bead-reuse boundary resolves as documented (EP5, EP7)
- [ ] A7 (cheap): `bash tests/test_drain_report.sh` — report sections render in the documented order with focus status first, and the two-run fixture's `net burn` and `passes-to-done` match hand-computed values while the one-run fixture prints neither (EP6)
- [ ] A8 (cheap): `bin/drain-report tests/fixtures/drain-report/imported | grep -c 'imported blocking work'` — 1, with the donor slug named (EP17 reporting half)
- [ ] A9 (cheap): `bash tests/test_drain_watch.sh` — one row per in-flight bd id with the six documented fields, a focus header, exit 0 on run-log-only input, and an unchanged fixture sha256 (EP8)
- [ ] A10 (cheap): `python3 -m pytest tests/test_agentic_audit.py -q` — 3 net-positive fixture runs of one focus file exactly one net-burn finding; mixed runs file none (EP9)
- [ ] A11 (cheap): `bash tests/test_janitor_triage.sh` — a 15-day-old fixture triage bead is listed and a 5-day-old one skipped, with `--dry-run` leaving the fixture sha256 unchanged (EP10)
- [ ] A12 (cheap): `bash tests/test_acceptance_block_grammar.sh` — a conforming block recovers every id and tier; missing id, unknown tier, absent command, and duplicate ids each fail (EP11)
- [ ] A13 (cheap): `bash tests/test_spec_gate.sh` — a mixed fixture writes `pass` and `fail` and exits 1, exits 0 once repaired, records `skip` for out-of-tier and policy-rejected criteria, and leaves no partial status file on a non-parsing block (EP12)
- [ ] A14 (cheap): `bash tests/test_spec_status.sh` — thrash names the ≥2-claim fixture issue, `blocked-on-you` counts, a missing source suppresses its own segment rather than zeroing it, and NOW.md order heads the no-slug listing (EP13, EP14)
- [ ] A15 (cheap): `bin/spec-status tests/fixtures/spec-status/bug --json | jq -e '.phase == "localized" and (has("acceptance_fraction")|not)'` — true; a pre-`fix-verified` bug shows its phase and no fraction (EP15)
- [ ] A16 (cheap): `python3 -m pytest .claude/skills/workboard/test_workboard.py -q` — the blocked-on-human fixture sorts first with the input pair swapped, and NOW.md order heads the listing (EP14 workboard half)
- [ ] A17 (cheap): `bash evals/lint-eval-coverage.sh` — passes with the focus-select, spillover, run-bead, ceremony, critique, and end-to-end scenarios all registered (EP0, EP16, EP18, EP19, EP20)
- [ ] A18 (cheap): `grep -c 'focus-drain' .claude/skills/drain/SKILL.md` — ≥ 1, and `grep -c -- '--all' .claude/skills/drain/SKILL.md` — ≥ 1; both launch forms documented (EP0)
- [ ] A19 (cheap): `bash tests/test_drain_spillover.sh` — the `Unblock:` line parse, the policy demotion of a rejected `run:` to `ask:`, and the absence of a sentinel proving the demoted command never executed (EP18)
- [ ] A20 (cheap): `grep -c 'CHORE_SLOTS' .claude/skills/drain/reference.md` — ≥ 1 with default 1 and the underfill condition stated (EP19)
- [ ] A21 (cheap): `awk '/^## Archive on completion/{f=1} f&&/^## The batch interview/{exit} f' .claude/skills/drain/SKILL.md | grep -c 'spec-gate'` — ≥ 1; the ceremony's gate step is present in the completion section (EP20)
- [ ] A22 (expensive): `bash evals/run.sh drain` — the `07-focus-e2e` scenario passes all seven assertions: triage holds 2, the imported dep is worked and attributed, one spillover-and-return is recorded, the chore appears in its own section, feat-a's ceremony completes, acceptance moves 0/2 → 2/2, and feat-b is untouched for burnup. Human-launched; the result is recorded in `acceptance-status.json` (all requirements, end to end)

## Open questions

None. All three were resolved by Steven on 2026-07-30:

- Defaults accepted as written: `DRAIN_TRIAGE_CAP=5`, `TRIAGE_DECAY_DAYS=14`, `CHORE_SLOTS=1`, thrash threshold at 2 claims. Each stays an overridable knob, retunable once real runs produce data.
- Tokens-per-closure reads the workflow journal only; the agentic meter is never consulted, and the metric is omitted rather than estimated when no journal exists (folded into EP6).
- Declined triage and decayed triage share one convention — close the bead, label why (`declined-at-triage` / `triage-archived`) — so one query surfaces both (folded into EP2).

Two more were raised by the 2026-07-30 critique and resolved the same day:

- The command policy gating EP18's `run:` unblocks and EP12's criteria is pinned as D11, modeled on `.claude/rules/human-blockers.md`'s probe contract, with exactly one implementation owned by task 00 and consumed by tasks 02 and 08.
- The completion ceremony gates on `--tier cheap` plus a human-recorded `expensive` result rather than launching `--tier all` unattended (folded into EP11, EP12, EP20).

## Parallelization map

Wave 1 — "drain core" as one serialized group (shared Touch on drain SKILL/reference): EP0, EP1-EP4, EP17, EP18 ∥ EP11 (grammar + idea template) ∥ EP5 (run bead). Wave 2: EP6-EP7 (need EP5, EP18 wording) ∥ EP12 (needs EP11). Wave 3: EP9-EP10 (need EP5/EP2) ∥ EP13-EP14 (need EP6/EP12) ∥ EP8 ∥ EP15 ∥ EP19. EP20 after EP12+EP18; EP16 last (touches `/critique`, needs EP11 landed).

## Parallelization

Prose for a human reader; the machine contract is each task's `Touch:` header
and dependency edges as registered into bd.

Task 00 lands first and alone: it owns the D11 command policy, and tasks 02 and
08 — the two consumers, one in each chain — both depend on it. It exists as its
own task precisely so neither consumer invents a second policy.

After it, two chains run independently. The **drain-prose chain** — tasks
01 → 02 → 03 → 04 → 12 — is serialized not by logic but by file: all five edit
`.claude/skills/drain/SKILL.md`, and two workers in that file collide no matter
how disjoint their requirements are. Task 12 additionally waits on 08. The
**proximity chain** — 07 → 08 → 09 → 10 — is a genuine data dependency: the
grammar defines what the gate parses, the gate writes what the status line
reads, and the workboard renders what the status line derives.

The two chains share no *source* file, but they did share two registries until
this revision: `tests/inventory/` and
`specs/toolkit-core-simplification/surface-inventory/` each took one fragment
per spec, which put one file in a dozen tasks' `Touch` with nothing serializing
the writes — concurrent workers would have conflicted or silently dropped
registrations. Each task now writes its own numbered fragment
(`drain-economy-NN.json` in both directories), so the registries are
append-by-new-file and no two tasks ever open the same one.

Three tasks branch off and run concurrently with everything else once their
input lands: 05 (`bin/drain-report`) and 06 (`bin/drain-watch`) after 04, each
owning its own new script; 11 (audit class + janitor scope) after 04, touching
only `agentic/audit.py` and `bin/janitor`; 13 (`/critique`) after 07. Task 14
is last by construction — it asserts the whole mechanism end to end.

Two shared-decision hazards, both resolved in the spec rather than left to a
worker: the run-log line grammar and the run-bead body are fixed by task 04 and
merely parsed by 05 and 06, so those two never negotiate a format between
themselves; and the close-plus-label lifecycle for dead triage items is one
convention, written by 03 for declines and extended by 11 for decay. A worker
that finds either under-specified files blocking work against the owning task
rather than choosing for itself.

Task 01 carries one extra duty for the whole spec: it registers the
surface-inventory fragment classifying every *existing* path later tasks edit —
`.claude/skills/drain/reference.md`, `agentic/ready.py`, `agentic/audit.py`,
`bin/janitor`, `.claude/skills/workboard/workboard.py`,
`.claude/skills/workboard/reference.md`,
`.claude/skills/workboard/test_workboard.py`, and `specs/QUEUE.md`. Until it
lands, `/breakdown`'s acceptance pre-flight refuses those paths — which is why
it is P0 even though the selector could otherwise wait. Later tasks classify
only the new files they create.

Every task touching `.claude/skills/drain/SKILL.md` carries a `wc -l` < 500
criterion. The file is 272 lines today and this spec adds ten mechanisms to it;
without that ceiling the last task in the chain inherits a file over the
authoring budget and a refactor nobody scoped.
