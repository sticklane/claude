Status: open
Priority: P1

## Problem

Three related gaps let already-decided or already-derived work sit stuck or
get silently re-done, burning whole headless generations along the way.

**Approved findings never get applied mechanically.** `/critique` and
drain's critique-intake step (`.claude/skills/drain/SKILL.md`, "Critique
intake") only know two routes for a critic verdict: READY writes
`Breakdown-ready: true`; NOT READY records findings in
`specs/<slug>/critique-findings.md` and routes the spec to the exit
checklist's §4, which drain's HUMAN.md filing (R2) files as a `decide`
blocker (`.claude/skills/drain/reference.md`, "HUMAN.md filing (R2)":
"NOT-READY specs (critique intake) | `decide` | §4"). Nothing distinguishes
a finding that is pure agent work — a stale line anchor, a
non-deterministic grep needing `--exclude-dir`, a missing runnable
acceptance command — from a finding that genuinely needs a human tradeoff
call. In this repo's own recent history, that gap is worked around by hand:
commits `2af860a` and `4570f88` are titled "apply approved REVISE edit
list", each a human-reviewed, human-approved pass that mechanically edited
`SPEC.md` per `critique-findings.md` and re-ran critique (still NOT READY,
new findings each time) — real agent-shaped work currently requiring a
human to notice the stale `decide` item and do the edit by hand. Across
three separate sessions on two different days, 10-13 draft specs sat stuck
this way. One session added a dedup guard so drain stops *re-critiquing*
the same spec repeatedly (see Requirement 3's grounding below) but never
closed the mechanical-application gap. A related cost: a whole headless
generation (full cold-start reprime) got burned on 5 intake attempts that
were all NOT READY — zero real dispatch progress — and other queues hit
drain's 10-generation hard cap without finishing, directly caused by
stuck-in-`decide` draft specs recurring every cycle.

**A contradicted DEFER gets redispatched and re-derived from scratch.** The
same incorrect spec root-cause (a CSS `@layer` ordering fix) burned three
separate worker attempts across two sessions in one repo: one task
DEFERRED after finding the SPEC's prescribed fix breaks two e2e tests; a
LATER, independent session re-derived from scratch — redoing the same
CSS-bundling forensics — that the SPEC's stated fix is a byte-identical
no-op. Drain's DEFERRED handling (`.claude/skills/drain/SKILL.md`, step 3)
treats every DEFERRED verdict uniformly: "the verdict carries the
question. Drain writes it into the task file under `## Deferred
questions`... Dependents simply never become dispatchable" — and the batch
interview's answer flow (step 4) flips `Status: deferred` straight back to
`pending` on any human answer, with no check that the SPEC's stated premise
actually changed. A finding that empirically refutes the SPEC's stated
root cause is not the same shape as an open question awaiting information —
answering it wrong (or answering a *different*, later-arrived question
without re-reading the earlier contradiction) re-admits the exact same
false premise for another worker to re-derive.

**Redundant critic re-runs on unchanged specs.** A drain critique-intake
pass ran the critic (~40k tokens each) FOUR times redundantly on a
NOT-READY spec before a session noticed `SPEC.md` hadn't changed since the
last findings file and switched to a cheap timestamp/hash-diff check
instead. That fix is written down in
`docs/memory/drain-dispatch-lessons.md` ("Critique intake: skip the critic
when SPEC.md is unchanged since a recorded NOT READY") only AFTER ~160k
tokens were wasted — and a memory file is local to this repo, so it does
not help any other install of this toolkit running the same `critique`/
`drain` skills. This lesson has never been promoted into the actual
SKILL.md mechanism.

## Solution

Close all three gaps at the mechanism level — in the skills themselves, not
in a memory file only this repo's future sessions might rediscover:

1. Give the critic's findings a triage step, shared by `/critique` (attended)
   and drain's critique-intake (unattended): findings split into MECHANICAL
   (an edit an agent can make with no judgment call) and JUDGMENT (a real
   tradeoff, ambiguity, or missing decision). MECHANICAL findings get
   applied to `SPEC.md` directly, committed, and the critic re-run
   (bounded, per `.claude/rules/token-discipline.md`'s evaluator-optimizer
   loop cap). Only a spec whose remaining findings are JUDGMENT-shaped (or
   whose triage pass made zero mechanical progress) is legitimately a
   HUMAN.md `decide` item under `.claude/rules/human-blockers.md`'s
   grammar.
2. Give a worker's DEFERRED verdict a distinct flag for "this finding
   empirically contradicts the SPEC's stated premise" versus "this is an
   open question." Drain records the distinction, and blocks re-dispatch of
   that exact premise until `SPEC.md`'s stated root-cause/fix section
   actually changes (a human edit or `/distill`) — not merely until a human
   answers a question.
3. Promote the memory-file timestamp/hash-diff lesson into `/critique` and
   drain's critique-intake mechanism itself: before dispatching the critic,
   compare `SPEC.md`'s current state against the state recorded in
   `critique-findings.md`; skip the critic and reuse the recorded verdict
   when unchanged.

Requirement 4 from the originating research pass (drain's generation-count
threshold miscounting NOT-READY critique/stub-intake attempts as dispatch
progress) is investigated below and found **already shipped** — see
Requirement 4 and Out of scope.

## Research grounding

`.claude/skills/drain/SKILL.md`, "Critique intake": "**NOT READY** →
findings recorded, spec to step 4's checklist, lease released."

`.claude/skills/drain/reference.md`, "HUMAN.md filing (R2)": "NOT-READY
specs (critique intake) | `decide` | §4."

`.claude/rules/human-blockers.md`: "`decide` = a decision-shaped item (a
stub or spec)" — the grammar this spec's Requirement 1 narrows: a
NOT-READY verdict is only legitimately `decide` once mechanical findings
are exhausted.

`.claude/skills/drain/SKILL.md`, step 3 DEFERRED handling: "the verdict
carries the question. Drain writes it into the task file under `##
Deferred questions`, sets `Status: deferred`... Dependents simply never
become dispatchable." Step 4: "`Status: deferred` tasks exist: collect
their `## Deferred questions` blocks, ask them all in one round..., write
each answer under `## Answers`, flip to `pending`, commit, return to step
1."

`docs/memory/drain-dispatch-lessons.md`, "Critique intake: skip the critic
when SPEC.md is unchanged since a recorded NOT READY": "Before dispatching
a critic at a spec, compare `git log -1 --format=%ct` of `SPEC.md` against
its `critique-findings.md`: findings newer than the spec + a recorded NOT
READY verdict decide the outcome deterministically — append nothing,
dispatch nothing, checklist it. Four fresh critic runs on 2026-07-13
(~40k subagent tokens each) confirmed exactly this: unchanged spec →
identical verdict."

`.claude/skills/drain/SKILL.md`, 3a Baton pass (already shipped, confirms
Requirement 4 is resolved): "**Critique-intake and stub-intake attempts
never count toward this threshold** — they already carry their own per-run
at-most-once bookkeeping (`Intake-failed:` / `Stub-intake-failed:` below),
and counting them pays a full reprime for zero dispatch progress: a
fooszone drain queue batoned gen 5→6 on 5 intake attempts that were all NOT
READY, then exhausted the 10-generation cap without finishing the queue
(specs/drain-wake-cost/EVIDENCE.md, "Follow-up (2026-07-13)")."

Repo evidence of the manual workaround this spec automates: `git log
--oneline` commits `2af860a` ("merge: idea-research-freshness — apply
approved REVISE edit list (still NOT READY, new finding)") and `4570f88`
("merge: narrow-autopilot — apply approved REVISE edit list (still NOT
READY, new findings)").

## Requirements

- R1 **Findings triage in `/critique`.** After the critic returns NOT READY
  or READY WITH NITS, `/critique` classifies each finding as MECHANICAL
  (stale path/line references, a non-deterministic or under-scoped
  acceptance command, a missing runnable check, a format/header contract
  violation — an edit with no judgment call) or JUDGMENT (ambiguity, scope,
  a missing design decision, a contested tradeoff). Apply every MECHANICAL
  finding directly to the target `SPEC.md` (or plan/diff target), commit,
  and re-run the critic — bounded to the 2-4 cycle cap in
  `.claude/rules/token-discipline.md`'s "Dispatch authoring" (cited, not
  restated). Findings still open after the bound, or JUDGMENT findings
  from the first pass, are what gets relayed/recorded — never silently
  dropped.
- R2 **Same triage reused by drain's critique intake, before HUMAN.md
  filing.** Drain's critique-intake step (`.claude/skills/drain/SKILL.md`,
  "Critique intake") runs R1's triage on a NOT READY verdict before routing
  to step 4's checklist: MECHANICAL findings are applied and committed
  in-run (same as R1, lease already held), the critic re-run once per the
  bound above, and only a spec whose remaining findings are JUDGMENT-shaped
  reaches the exit checklist's §4 / HUMAN.md's `decide` filing
  (`.claude/skills/drain/reference.md`, "HUMAN.md filing (R2)"). This
  narrows — but does not remove — the `decide` grammar in
  `.claude/rules/human-blockers.md`: a spec whose findings are genuinely
  judgment-shaped is still filed exactly as today.
- R3 **Deferred-verdict premise-contradiction flag.** The worker defer
  contract (`.claude/skills/drain/reference.md`'s worker prompt) gains an
  optional `Contradicts-premise: true` marker a worker sets alongside its
  DEFERRED question when its finding empirically refutes the SPEC's or
  task's stated root cause (not merely an open information gap). Drain
  records this distinctly under `## Deferred questions` (the flag plus the
  contradicting evidence, verbatim from the verdict).
- R4 **Blocked re-dispatch until the premise is corrected.** For a task
  flagged `Contradicts-premise: true`, drain's batch-interview answer flow
  (`.claude/skills/drain/SKILL.md`, step 4) must not flip `Status: deferred`
  back to `pending` on a plain human answer alone — it additionally
  requires `SPEC.md`'s stated root-cause/fix content to have actually
  changed since the defer (a commit-hash or content diff over the cited
  section) before re-dispatch is permitted. Until that diff is observed,
  the task (and any dependent) stays non-dispatchable, and its HUMAN.md
  entry types as `decide` ("spec amendment needed") rather than `ask`
  (`.claude/rules/human-blockers.md` grammar).
- R5 **Critique re-run skip, mechanized in `/critique` itself.** Before
  dispatching the critic agent, `/critique` compares `SPEC.md`'s current
  commit hash (or content hash) against the hash recorded in
  `critique-findings.md` at its last write. If unchanged and a verdict is
  already recorded, skip the critic and relay the recorded verdict instead
  of re-running it. `critique-findings.md`'s header gains the recorded
  hash so the comparison is self-contained (no dependency on `git log`
  history surviving a squash or rebase).
- R6 **Same skip reused by drain's critique intake.** Drain's
  critique-intake step invokes `/critique` (SKILL.md: "invoke **/critique**
  via the Skill tool"), so R5's skip applies automatically once R5 ships;
  this requirement exists only to make the reuse explicit and to update
  `docs/memory/drain-dispatch-lessons.md`'s entry to note the lesson is now
  mechanized in `/critique` itself, not merely documented — a future
  session reading that memory file should be pointed at the shipped
  mechanism rather than re-deriving it.
- R7 (informational, not implementation work) **Generation-count
  miscounting is already fixed.** The originating research pass's fourth
  candidate requirement — drain's baton-pass relaunch/generation-count
  threshold counting NOT-READY critique/stub-intake attempts as dispatch
  progress — is confirmed already shipped in
  `.claude/skills/drain/SKILL.md`'s 3a Baton pass section ("Critique-intake
  and stub-intake attempts never count toward this threshold"), landed
  under specs/drain-wake-cost's 2026-07-13 follow-up citing the identical
  incident shape (a fooszone queue batoning on 5 all-NOT-READY intake
  attempts and exhausting the generation cap). No task should re-implement
  this; breakdown should not create a task for R7.
- R8 **Ship gate.** Any task whose Touch includes `.claude/skills/critique/
  SKILL.md` carries a matching `antigravity/` mirror update and a
  `.claude-plugin/plugin.json` version bump (current: 0.8.63) in its
  Touch — no `codex/` mirror requirement, since `critique` is not one of
  the four explicit-invocation skills codex mirrors (CLAUDE.md). Any task
  whose Touch includes `.claude/skills/drain/SKILL.md` or
  `.claude/skills/drain/reference.md` carries the `antigravity/` mirror
  update, the matching `codex/.agents/skills/drain/SKILL.md` update, and
  the same plugin.json bump. `bash evals/lint-ultra-gate.sh` must stay
  green for both (`critique` and `drain` are both ultra-path skills per
  CLAUDE.md's "Testing changes" section).

## Out of scope

- Requirement 4/R7's generation-count fix — already shipped; see R7 above.
  This spec does not touch the baton-pass trigger logic.
- A general-purpose "is this finding mechanical" classifier reusable
  outside `/critique` — scoped to the critic-findings triage only.
- Retroactively re-triaging the 10-13 already-stuck draft specs mentioned
  in the Problem section; once this spec ships, the next drain/critique
  pass over each naturally re-triages them under the new mechanism.
- Changing the critic agent's verdict vocabulary (READY / READY WITH NITS /
  NOT READY stays as-is) — the triage is a post-verdict step `/critique`
  and drain perform on the findings, not a new critic-side verdict type.
- Any change to `.claude/skills/build/SKILL.md` or `.claude/skills/idea/
  SKILL.md` — neither owns findings-application or DEFERRED handling.

## Acceptance criteria

- `grep -c "MECHANICAL" .claude/skills/critique/SKILL.md` returns 0 today
  (confirmed absent) and ≥ 1 after R1 ships.
- `grep -c "Contradicts-premise" .claude/skills/drain/SKILL.md
  .claude/skills/drain/reference.md` returns 0 today (confirmed absent in
  both) and ≥ 1 in at least one of the two files after R3/R4 ship.
- `grep -c "hash" .claude/skills/critique/SKILL.md` returns 0 today
  (confirmed absent) and ≥ 1 after R5 ships.
- `grep -rn "NOT-READY specs (critique intake) | \`decide\` | §4"
  .claude/skills/drain/reference.md` still matches after R2 ships (the
  routing table entry is narrowed by, not deleted by, this spec — a
  genuinely judgment-shaped NOT READY spec is still filed exactly this
  way).
- `bash evals/lint-ultra-gate.sh` exits 0 after all requirements land.
- `claude plugin validate .` exits 0 after all requirements land.
- MANUAL: exercise R1/R2 end to end on a real NOT-READY spec with at least
  one findable mechanical finding (e.g. re-run critique intake on
  `specs/narrow-autopilot` or a similar spec with a live
  `critique-findings.md`) and confirm the mechanical findings from that
  spec's most recent findings file (stale line anchors, the
  non-deterministic grep) get applied without a human touching SPEC.md by
  hand.
- MANUAL: exercise R3/R4 with a synthetic DEFERRED verdict carrying
  `Contradicts-premise: true` and confirm the batch interview's plain-answer
  flow refuses to flip the task back to `pending` until `SPEC.md`'s cited
  section is actually edited.

## Open questions

- Should a MECHANICAL/JUDGMENT split live as critic-authored metadata
  (the critic agent itself tags each finding) or as a `/critique`-side
  heuristic applied to the critic's plain-text findings? The critic
  agent's `tools:` grant and output format
  (`.claude/agents/critic.md`) currently has no structured-tag concept —
  adding one is a larger interface change than a task drained unattended
  should decide alone; flagging for the breakdown pass or a human call.
- R4's "content actually changed" check needs a precise diff scope (whole
  `SPEC.md` vs. just the section the worker's `Contradicts-premise` finding
  cited) — too broad and an unrelated edit falsely unblocks; too narrow and
  a legitimate rewrite that moved the section falsely stays blocked. Left
  for the breakdown pass to pin down against a concrete example.
