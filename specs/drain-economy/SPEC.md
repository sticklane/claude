# Drain economy, feature-focus scheduling, and per-spec proximity accounting

Status: open
Priority: P1
Breakdown-ready: true

## Problem

A drain run is a stateless pump over a **global, dependency-gated task frontier**: priority attaches at task granularity (`bd ready` is priority-sorted per issue), so priority is fungible across features and the scheduler cannot represent "finish this one." The run owns no state (`.claude/skills/drain/SKILL.md:12-15`, "no baton files... the queue itself is the state"), files every discovered item straight into the queue ("Discovered out-of-scope work is filed, never dropped", SKILL.md:163-164), and ends without reporting a delta. Four user-facing failures follow, all live:

1. **Feature-boundary crossing.** Drain interleaves features by construction — `specs/QUEUE.md`'s Queue 6 combined three specs into one repo-wide drain with hand-woven cross-spec `Depends on:` edges and waves mixing all three. Interleaving N features stretches each one's completion latency ~N× while keeping workers fully busy: task throughput up, finished features down. And since every open feature is a discovery generator, interleaving *funds* multiplication — each revisit of a 60%-done spec files more work (Queue 6's own residue: two discovered stubs "not yet triaged").
2. **Opacity.** The rolling top-up loop (SKILL.md:166-167) never pauses, so it never narrates. `/fleet` shows liveness and `/workboard` shows inventory; nothing shows what this run has accomplished, for which feature.
3. **Work multiplication.** Filed-never-dropped is a ratchet with no admission step, no budget, no severity floor. The repo's history documents the cost: 10-13 draft specs stuck across sessions, a headless generation burned on 5 NOT-READY intakes with zero dispatch progress, queues hitting the retired 10-generation cap without finishing (`specs/critique-findings-loop-closure/SPEC.md`, Problem).
4. **No proximity answer, and silent blocking.** "How close is feature X" has no honest number — task-count denominators inflate exactly when the system works, and remaining count is not remaining distance (the CSS `@layer` case: one task, three failed attempts across two sessions). Worse, on a global frontier a blocked top feature is *silent*: workers stay busy on feature #5 while the most important thing sits stuck, which is exactly the 10-13-stuck-specs incident.

## Solution

Lift priority to the feature and give the run an accounting identity. A human-owned `specs/NOW.md` names the focus (WIP = 1); bare `/drain` drains that feature's dependency closure until done, spilling down the Now list only when the focus frontier is entirely blocked — after attempting mechanical unblocks — and returning to it the moment it unblocks. Featureless `chore` work gets one bounded slot. Discovered work splits into *blocking* (files as today, uncapped — it is scope truth) and *adjacent* (files to a `triage` label, admitted only at the batch interview, capped per run). Every run opens and closes a run bead carrying a computed report (adopting only the run-issue *convention* from parked `specs/agentic-dynamic-workflows/` item 7). Feature side: each spec's `## Acceptance criteria` becomes machine-runnable with stable IDs, scored by `bin/spec-gate` into committed `acceptance-status.json`; `bin/spec-status` and workboard render per-feature proximity — acceptance green-count, blocked-on-you first, thrash flag, estimated passes — and feature completion becomes a mechanical ceremony (frontier empty + full gate green + spec-review filed). Progress is asked of the acceptance surface, never the task list: the plan answers with its size, which inflates; the territory answers with what passes.

## Design decisions

- **D1 — Blocking vs. adjacent discriminator.** An item is *blocking* iff its parent issue's (or the focus feature's) acceptance criteria cannot pass without it; everything else is adjacent. Blocking children are estimation error surfacing (legitimate, uncapped); adjacent items are proposals (capped, triaged). The worker states the failing criterion when filing blocking work.
- **D2 — The acceptance surface is ground truth; the task list is an estimate.** Proximity = criteria passing now, computed by running them.
- **D3 — Reports are computed, not prompted.** Every number derives from bd, `acceptance-status.json`, and the run log by script. Drain may append at most one paragraph of model prose.
- **D4 — Run issue is a convention, not machinery.** `agentic dispatch/run/watch` stays parked under its existing Unblock condition; `bin/drain-watch` (EP8) reads the native harness progress stream and run log, and retires into `agentic watch` if that spec unparks.
- **D5 — Triage is a label, not a status.** Labels exist in bd today; exclusion is a query change plus a conventions entry.
- **D6 — Bugs get a phase pointer, never a fraction.** Pre-`fix-verified`, "how close" is a diagnosis question.
- **D7 — Admission rate = human decision rate.** A queue only functions as a finish line if a human controls what counts as the finish. Agents propose; the batch interview admits; the human writes NOW.md.
- **D8 — Spillover, never silence** *(resolved 2026-07-29: spillover chosen over strict halt)*. When the focus frontier is entirely blocked, drain attempts mechanical unblocks, then advances down the Now list — but the blocked focus stays the loudest fact in the system: narration announces it, the report leads with it, workboard badges it first. Spillover is permission to stay useful, not permission to go quiet.
- **D9 — WIP = 1, re-focus at dispatch granularity** *(resolved 2026-07-29)*. All *new* dispatches go to the highest Now entry with ready work; in-flight tasks are never preempted. The instant the focus unblocks, new work returns to it; mixed in-flight tasks during a transition are expected and momentary.
- **D10 — Featureless chores get one bounded slot** *(resolved 2026-07-29: allowed)*. `chore`-labeled beads may fill idle capacity without becoming a second focus: at most `CHORE_SLOTS` (default 1) concurrent, dispatched only when the focus/spillover frontier underfills the window, excluded from feature accounting, never a spillover trigger, never a completion blocker.
- **D11 — One command policy, modeled on the probe contract** *(resolved 2026-07-30)*. EP18's `run:` unblocks and EP12's acceptance criteria are both file-sourced commands reaching `exec` inside an unattended loop, so they share one policy — and that policy mirrors `.claude/rules/human-blockers.md`'s probe contract, which already solves this problem in this repo. A command executes only if argv-0 resolves to a regular executable under an allowlisted root (the repo's `bin/`, or a named tool list), it runs directly and never through a shell, its arguments survive POSIX shell-word lexing with no ASCII control characters, its cwd is the repo root, and it runs under a bounded timeout with no network grant. A rejected command is never executed and always records its reason: EP18 demotes `run:` to `ask:`, EP12 records the criterion `skip`. The policy has exactly one implementation, owned by task 00; EP12's and EP18's tasks both depend on it and neither may author a second.
- **D12 — Acceptance criteria are read-only** *(resolved 2026-07-30)*. `bin/spec-gate` runs criteria against the live repository on a schedule and commits the result, so a criterion that mutates state pollutes it every pass. Criteria must be read-only or idempotent; anything needing to create state creates it in a fixture under `mktemp -d` or `tests/fixtures/`, never in the live tracker or working tree. The gate does not sandbox a criterion that ignores this — enforcement is EP16's READY bar, at authoring time.

## Requirements

**Focus scheduling (drain core)**

- **EP0 — Now line, selector, default flip.** `specs/NOW.md` is a human-edited-only ordered list of spec slugs (one line each, optional one-line why); `specs/QUEUE.md` stays historical per its own banner. Bare `/drain` means "focus-drain the top NOW.md entry with ready work"; `/drain specs/<slug>` is an explicit focus; `/drain --all` preserves today's whole-queue behavior and says so at launch. Empty NOW.md: drain states it and stops (suggesting `--all` or a slug); it never invents a focus.
- **EP17 — Dependency-closure scope.** Focus scope = the spec's open beads ∪ the transitive closure of their *blocking* dependencies wherever those live (other specs or featureless), recomputed at every frontier read. Imported cross-spec deps are worked but reported under "imported blocking work (from `<slug>`)" and never mark the donor spec as in-progress for burnup.
- **EP18 — Mechanical unblocks, then spillover, loudly.** When the focus frontier is entirely blocked: first attempt mechanical unblocks — execute `Unblock: run:` commands **only if** they pass the D11 command policy, whose single implementation this requirement consumes rather than defines (a rejected command demotes to `ask:` with its rejection reason recorded); dispatch `Unblock: agent:` prompts as scoped one-attempt workers; queue `ask:` items for the interview — then re-read the frontier. Still dead: emit narration `focus <slug> blocked (ask: <n> items) → spilling to <next>`, record the spillover event on the run bead, and proceed to the next NOW.md entry (walking the whole list; list exhausted → batch interview). The selector re-evaluates from NOW.md top at every dispatch (D9).
- **EP19 — Chores lane.** Beads labeled `chore` dispatch per D10. Chore discoveries follow the same EP1-EP4 economy; chore results appear in a separate report section.
- **EP20 — Feature completion ceremony.** When the focus frontier is empty with no open blocked/deferred items in scope: run `bin/spec-gate <slug> --tier cheap` — never `--tier all`, because an unattended worker must not launch a paid or gated criterion. The ceremony is green when the cheap tier passes **and** every `expensive` criterion already carries a human-recorded pass in `acceptance-status.json`; a missing expensive record blocks the ceremony and files an `ask:` naming the run the human owes. On green, dispatch the spec-completion review (existing practice — the Queue 6 evidence files), file its evidence, append the historical entry to QUEUE.md, remove the slug from NOW.md, set the spec `Status: done`, and close the run bead with the ceremony recorded. On red, each failing criterion files a blocking child per EP1 and the run continues — the gate failures *are* the new frontier.

**Queue economy (drain edits)**

- **EP1 — Discriminate discovered work.** Drain's filing step (SKILL.md step 3 and the workflow-compile bullet at SKILL.md:247) classifies each discovered item per D1. Blocking: `bd create --deps discovered-from:<id>` as today, citing the parent criterion it unblocks. Adjacent: EP2 path. The worker prompt (reference.md) carries the discriminator wording.
- **EP2 — Triage admission.** Adjacent items file with label `triage`. Every ready query drain and `/work` issue excludes `triage`. The batch interview lists triage items with three verbs — promote (strip label), decline (close with label `declined-at-triage`), defer (leave). Decline and EP10 decay share one convention: both close the bead and both label why it died (`declined-at-triage` for a human decline, `triage-archived` for decay), so a single closed-plus-label query surfaces every dead triage item. Conventions doc gains both label entries.
- **EP3 — Discovery budget.** At most `DRAIN_TRIAGE_CAP` (default 5) adjacent filings reach bd per run; overflow lands in the run report's "Discovered digest" with enough context to re-file by hand. Blocking children are exempt.
- **EP4 — Severity floor.** Auto-filing (even to triage) requires the item to (a) block acceptance somewhere, or (b) violate a named rule in `.claude/rules/` or a repo invariant. Style and opportunity findings are digest-only. Mirrors the critic's high-signal doctrine (README.md:122-125).
- **EP5 — Run issue.** Drain opens a run bead at launch — title `drain <focus-or-all> <ISO-date>`, label `drain-run`, body: NOW.md snapshot, launch argument, session id — and closes it at exit with the EP6 report. Interruption leaves it open; the next drain of the same focus reuses an open run bead younger than 24h.
- **EP6 — Computed run report.** `bin/drain-report <run-bead-id>` emits, from bd and the run log only, leading with focus status: focus feature and its acceptance delta, blocked-on-you items first, spillover events with reasons; then closed (list), opened-blocking, opened-triage, declined, deferred, imported blocking work, chores section, discovered digest, net focus delta, tokens-per-closure read from the workflow journal only (the agentic meter is never consulted; no journal → the metric is omitted, never estimated), trailing net burn over the last 3 runs of this focus, and projected passes-to-done (suppressed below 2 data points). Zero model calls.
- **EP7 — Loop narration.** After each collected verdict, one line to the session and the run log: `closed <id> (<i>/<n> in focus) · opened <b>b+<t>t · in-flight: <id> <role> attempt-<a>`, plus a line at every focus transition (EP18's wording) and at re-focus.
- **EP8 — drain-watch.** `bin/drain-watch [run-bead-id]` tails the run log and the native workflow progress stream, one row per in-flight agent grouped by bd id: label, tier, state, attempt, tokens, elapsed; header row names the current focus. Read-only; degrades to run-log-only when no workflow stream exists.
- **EP9 — Net-burn audit class.** `agentic audit` gains a class computed from `drain-run` beads: opened-admitted (blocking + promoted) minus closed per run; when the sum over 3 consecutive runs of one focus is positive, file one deduplicated bead naming the focus and ratio.
- **EP10 — Janitor triage decay.** `janitor --scope triage` closes `triage` items untouched ≥ `TRIAGE_DECAY_DAYS` (default 14) with label `triage-archived`; honors `--dry-run`; counts in janitor's summary.

**Per-spec proximity**

- **EP11 — Machine-readable acceptance blocks.** `/idea`'s SPEC.md template criteria gain stable IDs and a grammar: `- [ ] A<k> (<cheap|expensive>): \`<command>\` — <expected>`. Grammar documented as a sibling of `docs/memory/anchored-acceptance-criteria.md`. The tiers name who may run a criterion, not merely how long it takes: `cheap` is anything an unattended worker may execute under D11; `expensive` is a paid or gated run — an eval scenario, a human-driven walk — that only a human launches, whose result a human records in `acceptance-status.json`. Every criterion of either tier obeys D12. Backfill is lazy: when a focus spec's block does not parse, drain files one blocking child "conform acceptance block to grammar" instead of guessing.
- **EP12 — spec-gate.** `bin/spec-gate <slug> [--tier cheap|all]` parses the block, runs each criterion under the D11 policy — consuming its single implementation, never authoring a second — writes `specs/<slug>/acceptance-status.json` (`{id, tier, pass|fail|skip, ts}`), exit 0 iff all executed criteria pass. A policy-rejected criterion records `skip` with its reason and is never executed. Criteria are read-only per D12. Drain runs `--tier cheap` once per pass on the focus; `--tier all` is an operator or scheduler invocation only — never the unattended ceremony's (EP20). The JSON is committed so trend is a `git log` away.
- **EP13 — Convergence and thrash derivation.** `bin/spec-status` derives per spec, degrading gracefully per missing source: tasks with ≥2 claims (bd history), DEFERRED-then-redispatched pairs, critique NOT-READY streak (`specs/<slug>/critique-findings.md` history), net frontier delta last pass. Thrash flag names the specific issues.
- **EP14 — Status line and workboard surface.** `bin/spec-status [slug]` prints `slug · acceptance g/n · open k (b blocked-on-you) · last pass +Δgreen, net±m · thrash: <ids|none> · est <p> passes`; no slug: one line per spec with open work, NOW.md order first. agent-console's `/workboard` renders NOW.md at the top with the current focus, badges blocked-on-human strictly first, and shows a per-spec burnup (admitted vs closed cumulative).
- **EP15 — Bug phase pointer.** Bug-labeled beads carry `phase:` metadata (`reproduced|localized|fix-proposed|fix-verified|regressions-green`); build/drain worker verdicts set it; EP14 shows the phase and suppresses fractions for bugs before `fix-verified`.
- **EP16 — Critique READY bar and contraction.** `/critique`'s READY verdict additionally requires the acceptance block to parse under EP11's grammar, each criterion to map to ≥1 requirement, and each criterion to be read-only per D12 — the authoring-time gate that keeps a state-mutating criterion out of the committed gate loop, since `bin/spec-gate` executes what it is given. On re-critique of the same spec, the verdict evaluates resolution of prior findings only; net-new findings route to the run report digest, not the loop. Boundary: mechanical application and dedup of findings remain `specs/critique-findings-loop-closure/` scope.

## Out of scope

- Unparking `agentic dispatch/run/watch` — its Unblock condition stands; EP5/EP8 adopt one convention and one viewer.
- LLM-estimated effort or calendar ETAs — only pass-count projection from measured net burn.
- Mid-task preemption on re-focus (D9); a second concurrent focus (WIP stays 1); auto-editing NOW.md except the EP20 completion removal.
- Modifying `critique-findings-loop-closure` requirements; cross-repo aggregation beyond workboard's existing scan; Codex/Antigravity parity for the watch stream (report and status are runtime-neutral via bd).
- **Janitor's worktree-sweep rules.** EP10 adds one scope to `janitor`; the broader gap — that janitor sweeps only issue-owned `drain/` tuples, does not encode the branch-is-the-archive identity or the detached-HEAD exception, and cannot see foreign-runtime worktrees — is `agentic-zz3k`, filed from the 2026-07-29 manual sweep (29 worktrees → 7). Land EP10 with that issue rather than as a competing edit to the same SKILL.md.

## Acceptance criteria

Every criterion is read-only per D12: nothing here mutates bd, the working tree, or any live surface — state a criterion needs, it builds under `mktemp -d` inside the test it names. `cheap` criteria run unattended under D11; the one `expensive` criterion is a paid eval only a human launches, whose result a human records in `acceptance-status.json`.

- [ ] A1 (cheap): `bash tests/test_command_policy.sh` — the D11 policy accepts an allowlisted argv-0, refuses a shell metacharacter, refuses an unresolvable name, and its rejection path leaves no sentinel (D11)
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

Three more were raised by the 2026-07-30 critique and resolved the same day:

- The command policy gating EP18's `run:` unblocks and EP12's criteria is pinned as D11, with exactly one implementation owned by task 00 and consumed by tasks 02 and 08.
- The completion ceremony gates on `--tier cheap` plus a human-recorded `expensive` result rather than launching `--tier all` unattended (folded into EP11, EP12, EP20).
- Acceptance criteria are read-only (D12), enforced at authoring time by EP16's READY bar.

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
