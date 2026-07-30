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

## Requirements

**Focus scheduling (drain core)**

- **EP0 — Now line, selector, default flip.** `specs/NOW.md` is a human-edited-only ordered list of spec slugs (one line each, optional one-line why); `specs/QUEUE.md` stays historical per its own banner. Bare `/drain` means "focus-drain the top NOW.md entry with ready work"; `/drain specs/<slug>` is an explicit focus; `/drain --all` preserves today's whole-queue behavior and says so at launch. Empty NOW.md: drain states it and stops (suggesting `--all` or a slug); it never invents a focus.
- **EP17 — Dependency-closure scope.** Focus scope = the spec's open beads ∪ the transitive closure of their *blocking* dependencies wherever those live (other specs or featureless), recomputed at every frontier read. Imported cross-spec deps are worked but reported under "imported blocking work (from `<slug>`)" and never mark the donor spec as in-progress for burnup.
- **EP18 — Mechanical unblocks, then spillover, loudly.** When the focus frontier is entirely blocked: first attempt mechanical unblocks — execute `Unblock: run:` commands **only if** they pass the same command policy that gates acceptance commands (a rejected command demotes to `ask:`); dispatch `Unblock: agent:` prompts as scoped one-attempt workers; queue `ask:` items for the interview — then re-read the frontier. Still dead: emit narration `focus <slug> blocked (ask: <n> items) → spilling to <next>`, record the spillover event on the run bead, and proceed to the next NOW.md entry (walking the whole list; list exhausted → batch interview). The selector re-evaluates from NOW.md top at every dispatch (D9).
- **EP19 — Chores lane.** Beads labeled `chore` dispatch per D10. Chore discoveries follow the same EP1-EP4 economy; chore results appear in a separate report section.
- **EP20 — Feature completion ceremony.** When the focus frontier is empty with no open blocked/deferred items in scope: run `bin/spec-gate <slug> --tier all`; on green, dispatch the spec-completion review (existing practice — the Queue 6 evidence files), file its evidence, append the historical entry to QUEUE.md, remove the slug from NOW.md, set the spec `Status: done`, and close the run bead with the ceremony recorded. On red, each failing criterion files a blocking child per EP1 and the run continues — the gate failures *are* the new frontier.

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

- **EP11 — Machine-readable acceptance blocks.** `/idea`'s SPEC.md template criteria gain stable IDs and a grammar: `- [ ] A<k> (<cheap|expensive>): \`<command>\` — <expected>`. Grammar documented as a sibling of `docs/memory/anchored-acceptance-criteria.md`. Backfill is lazy: when a focus spec's block does not parse, drain files one blocking child "conform acceptance block to grammar" instead of guessing.
- **EP12 — spec-gate.** `bin/spec-gate <slug> [--tier cheap|all]` parses the block, runs each criterion, writes `specs/<slug>/acceptance-status.json` (`{id, tier, pass|fail|skip, ts}`), exit 0 iff all executed criteria pass. Drain runs `--tier cheap` once per pass on the focus; `all` runs at the EP20 ceremony or by operator/scheduler. The JSON is committed so trend is a `git log` away.
- **EP13 — Convergence and thrash derivation.** `bin/spec-status` derives per spec, degrading gracefully per missing source: tasks with ≥2 claims (bd history), DEFERRED-then-redispatched pairs, critique NOT-READY streak (`specs/<slug>/critique-findings.md` history), net frontier delta last pass. Thrash flag names the specific issues.
- **EP14 — Status line and workboard surface.** `bin/spec-status [slug]` prints `slug · acceptance g/n · open k (b blocked-on-you) · last pass +Δgreen, net±m · thrash: <ids|none> · est <p> passes`; no slug: one line per spec with open work, NOW.md order first. agent-console's `/workboard` renders NOW.md at the top with the current focus, badges blocked-on-human strictly first, and shows a per-spec burnup (admitted vs closed cumulative).
- **EP15 — Bug phase pointer.** Bug-labeled beads carry `phase:` metadata (`reproduced|localized|fix-proposed|fix-verified|regressions-green`); build/drain worker verdicts set it; EP14 shows the phase and suppresses fractions for bugs before `fix-verified`.
- **EP16 — Critique READY bar and contraction.** `/critique`'s READY verdict additionally requires the acceptance block to parse under EP11's grammar with each criterion mapping to ≥1 requirement. On re-critique of the same spec, the verdict evaluates resolution of prior findings only; net-new findings route to the run report digest, not the loop. Boundary: mechanical application and dedup of findings remain `specs/critique-findings-loop-closure/` scope.

## Out of scope

- Unparking `agentic dispatch/run/watch` — its Unblock condition stands; EP5/EP8 adopt one convention and one viewer.
- LLM-estimated effort or calendar ETAs — only pass-count projection from measured net burn.
- Mid-task preemption on re-focus (D9); a second concurrent focus (WIP stays 1); auto-editing NOW.md except the EP20 completion removal.
- Modifying `critique-findings-loop-closure` requirements; cross-repo aggregation beyond workboard's existing scan; Codex/Antigravity parity for the watch stream (report and status are runtime-neutral via bd).
- **Janitor's worktree-sweep rules.** EP10 adds one scope to `janitor`; the broader gap — that janitor sweeps only issue-owned `drain/` tuples, does not encode the branch-is-the-archive identity or the detached-HEAD exception, and cannot see foreign-runtime worktrees — is `agentic-zz3k`, filed from the 2026-07-29 manual sweep (29 worktrees → 7). Land EP10 with that issue rather than as a competing edit to the same SKILL.md.

## Acceptance criteria

- [ ] A1 (cheap): `grep -n "blocking iff" .claude/skills/drain/SKILL.md` — discriminator wording present in filing step (EP1)
- [ ] A2 (cheap): `bd create "x" --labels triage && bd ready --json | jq -e '[.[]|select(.labels|index("triage"))]|length==0'` — triage excluded from ready (EP2)
- [ ] A3 (cheap): `grep -n "DRAIN_TRIAGE_CAP" .claude/skills/drain/reference.md` — budget knob documented with default 5 (EP3)
- [ ] A4 (cheap): `grep -n "severity floor" .claude/skills/drain/SKILL.md` — floor stated with rule-citation requirement (EP4)
- [ ] A5 (cheap): fixture focus-drain in `evals/` opens a `drain-run` bead naming the focus and closes it with a report containing all EP6 sections in order, focus status first — `jq` checks on the closing comment (EP5, EP6)
- [ ] A6 (cheap): `bin/drain-report` on a fixture with 2 runs of known deltas prints `net burn` and `passes-to-done` matching hand-computed values; with 1 run prints neither (EP6)
- [ ] A7 (cheap): fixture run log contains ≥1 line matching `closed .* ([0-9]+/[0-9]+ in focus)` per closure and one `focus .* blocked .* spilling` line in the spillover fixture (EP7, EP18)
- [ ] A8 (cheap): `bin/drain-watch --once <fixture>` renders the focus header and one row per in-flight agent keyed by bd id; exits 0 with run-log-only input (EP8)
- [ ] A9 (cheap): `agentic audit --dry-run` over 3 fixture net-positive runs of one focus reports exactly one net-burn finding; over mixed runs reports zero (EP9)
- [ ] A10 (cheap): `janitor --scope triage --dry-run` lists a 15-day-old fixture triage bead and skips a 5-day-old one (EP10)
- [ ] A11 (cheap): `bin/spec-gate` on a fixture spec with one passing and one failing criterion writes acceptance-status.json with `pass` and `fail` and exits 1; after fixing, exits 0 (EP11, EP12)
- [ ] A12 (cheap): `bin/spec-status <fixture>` prints the status line with `blocked-on-you` count and `thrash:` naming a ≥2-claim fixture issue (EP13, EP14)
- [ ] A13 (cheap): workboard JSON for two fixture specs sorts the blocked-on-human spec first regardless of other fields, and NOW.md order heads the listing (EP14)
- [ ] A14 (cheap): a fixture bug bead at `phase: localized` renders the phase and no fraction in `bin/spec-status` (EP15)
- [ ] A15 (cheap): `/critique` fixture with a non-parsing acceptance block returns NOT READY citing the grammar; re-critique fixture routes a net-new finding to digest not findings file (EP16)
- [ ] A16 (cheap): NOW.md fixture with two slugs — bare `/drain` selects slug[0]; empty NOW.md fixture stops with the stated message; `grep -n '\-\-all' .claude/skills/drain/SKILL.md` shows the legacy flag documented (EP0)
- [ ] A17 (cheap): closure fixture — focus spec with one blocking dep bead homed in another spec: the selector's frontier includes it and the report lists it under imported blocking work (EP17)
- [ ] A18 (cheap): spillover fixture — focus fully blocked with one `run:` unblock (policy-passing) and one `ask:`: the `run:` executes and re-focus occurs without spillover; with only `ask:` items, drain spills to Now[1], and the report leads with the blocked-on-you item (EP18)
- [ ] A19 (cheap): a policy-failing `run:` unblock fixture is demoted to `ask:` and never executed — `grep` the run log for the demotion line (EP18)
- [ ] A20 (cheap): chores fixture — a `chore` bead dispatches only when the focus frontier underfills the window, never >`CHORE_SLOTS` concurrent, and appears only in the report's Chores section (EP19)
- [ ] A21 (cheap): completion fixture — frontier empty + `spec-gate --tier all` green → spec-review evidence filed, QUEUE.md history appended, slug removed from NOW.md, spec `Status: done`, run bead closed with ceremony recorded; a red-gate fixture instead files blocking children per failing criterion and keeps the run open (EP20)
- [ ] A22 (expensive, end-to-end): on a fixture repo with NOW.md = [feat-a, feat-b], feat-a holding 4 issues (one with a cross-spec blocking dep in feat-b, one `ask:`-blocked), 2 adjacent discoveries seeded, and 1 chore bead: bare `/drain` completes with triage holding 2, the imported dep worked and attributed, one spillover-and-return recorded, the chore in its own section, feat-a's ceremony executed with acceptance 0/2→2/2, and `bin/spec-status` showing feat-b untouched for burnup

## Open questions

None. All three were resolved by Steven on 2026-07-30:

- Defaults accepted as written: `DRAIN_TRIAGE_CAP=5`, `TRIAGE_DECAY_DAYS=14`, `CHORE_SLOTS=1`, thrash threshold at 2 claims. Each stays an overridable knob, retunable once real runs produce data.
- Tokens-per-closure reads the workflow journal only; the agentic meter is never consulted, and the metric is omitted rather than estimated when no journal exists (folded into EP6).
- Declined triage and decayed triage share one convention — close the bead, label why (`declined-at-triage` / `triage-archived`) — so one query surfaces both (folded into EP2).

## Parallelization map

Wave 1 — "drain core" as one serialized group (shared Touch on drain SKILL/reference): EP0, EP1-EP4, EP17, EP18 ∥ EP11 (grammar + idea template) ∥ EP5 (run bead). Wave 2: EP6-EP7 (need EP5, EP18 wording) ∥ EP12 (needs EP11). Wave 3: EP9-EP10 (need EP5/EP2) ∥ EP13-EP14 (need EP6/EP12) ∥ EP8 ∥ EP15 ∥ EP19. EP20 after EP12+EP18; EP16 last (touches `/critique`, needs EP11 landed).

## Parallelization

Prose for a human reader; the machine contract is each task's `Touch:` header
and dependency edges as registered into bd.

Two chains run independently from the start. The **drain-prose chain** — tasks
01 → 02 → 03 → 04 → 12 — is serialized not by logic but by file: all five edit
`.claude/skills/drain/SKILL.md`, and two workers in that file collide no matter
how disjoint their requirements are. Task 12 additionally waits on 08. The
**proximity chain** — 07 → 08 → 09 → 10 — is a genuine data dependency: the
grammar defines what the gate parses, the gate writes what the status line
reads, and the workboard renders what the status line derives. Nothing in
either chain shares a file with the other, so both can be in flight at once
from the moment work starts.

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
surface-inventory fragment covering the existing unclassified paths later tasks
edit (`drain/reference.md`, `agentic/ready.py`, `agentic/audit.py`,
`bin/janitor`, `workboard.py`, `specs/QUEUE.md`). Until it lands, `/breakdown`'s
acceptance pre-flight refuses those paths — which is why it is P0 even though
the selector could otherwise wait.

Every task touching `.claude/skills/drain/SKILL.md` carries a `wc -l` < 500
criterion. The file is 272 lines today and this spec adds ten mechanisms to it;
without that ceiling the last task in the chain inherits a file over the
authoring budget and a refactor nobody scoped.
