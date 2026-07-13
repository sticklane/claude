Status: open
Priority: P1
Breakdown-ready: true

## Problem

Three related gaps let already-decided or already-derived work sit stuck or
get silently re-done, burning whole headless generations along the way.

**Approved findings never get applied mechanically.** `/critique` and
drain's critique-intake step (`.claude/skills/drain/SKILL.md`, "Critique
intake") only know two routes for a critic verdict: READY writes
`Breakdown-ready: true`; NOT READY relays the findings verbatim (`/critique`
itself persists nothing today — it only relays the verdict and findings to
its caller and writes/removes the `Breakdown-ready:` marker; drain's
critique-intake step is the one that records them in
`specs/<slug>/critique-findings.md`) and routes the spec to the exit
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
this way. One session added a dedup guard so drain stops _re-critiquing_
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
answering it wrong (or answering a _different_, later-arrived question
without re-reading the earlier contradiction) re-admits the exact same
false premise for another worker to re-derive.

**Redundant critic re-runs on unchanged specs.** A drain critique-intake
pass ran the critic (~40k tokens each) FOUR times redundantly on a
NOT-READY spec before a session noticed `SPEC.md` hadn't changed since the
last findings file and switched to a cheap timestamp/hash-diff check
instead. That fix is written down in
`docs/memory/drain-dispatch-lessons.md` ("Critique intake: skip the critic
when SPEC.md is unchanged since a recorded NOT READY") and has since been
partially promoted into drain's own mechanism: `.claude/skills/drain/
reference.md`'s Critique intake section now runs a "cheap-before-expensive
short-circuit" comparing `git log -1 --format=%H` for `SPEC.md` against the
commit that produced the last recorded NOT READY verdict, skipping the
critic dispatch entirely when unchanged (confirmed on 9 of 10 draft specs
in one 2026-07-13 pass). Two gaps remain in that promotion: it is
**drain-only** — an attended `/critique` invocation on an unchanged spec
has no such skip and still pays full critic cost — and it keys on a
**commit hash**, which stops resolving across a squash or rebase (the same
self-containment failure mode R5 below is designed to avoid by keying on
content instead). The lesson is real and partially shipped, but the
mechanism lives in the wrong place and in a fragile form, duplicated
rather than shared by both callers.

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
  a missing design decision, a contested tradeoff). MECHANICAL findings are
  applied unconditionally — no user-ask or pipeline gate applies to them,
  unlike existing step 4's "apply fixes only if the user asks or the
  pipeline step requires READY" (that gate still governs JUDGMENT
  findings, unchanged). Apply every MECHANICAL finding directly to the
  target `SPEC.md` (or, when `/critique` was invoked against a plan
  document instead of a spec, that plan file — scoped to prose-only
  targets; a code-diff target is out of scope, see "Out of scope"), commit,
  and re-run the critic — bounded to the 2-4 cycle cap in
  `.claude/rules/token-discipline.md`'s "Dispatch authoring" (cited, not
  restated). Findings still open after the bound, or JUDGMENT findings
  from the first pass, are what gets relayed/recorded — never silently
  dropped.
- R2 **Same triage reused automatically by drain's critique intake, before
  HUMAN.md filing — no drain/SKILL.md invocation-logic edit required.**
  Drain's critique-intake step already invokes `/critique` via the Skill
  tool (`.claude/skills/drain/SKILL.md`, "Critique intake"), so R1's
  triage-apply-recheck loop runs automatically inside that call — the same
  automatic-once-R1-ships relationship R6 states for R5. `/critique`'s
  returned verdict already reflects the triage outcome: only a spec whose
  remaining findings are JUDGMENT-shaped still comes back NOT READY and
  reaches the exit checklist's §4 / HUMAN.md's `decide` filing
  (`.claude/skills/drain/reference.md`, "HUMAN.md filing (R2)"), narrowing
  — but not removing — the `decide` grammar in
  `.claude/rules/human-blockers.md`. This requirement exists to make that
  automatic reuse explicit and to add the MANUAL acceptance check below
  confirming a MECHANICAL finding surfaced via drain's critique-intake path
  gets applied without a human touching `SPEC.md` — not to change
  drain/SKILL.md's routing text itself.
- R3 **Deferred-verdict premise-contradiction flag.** The worker defer
  contract (`.claude/skills/drain/reference.md`'s worker prompt) gains an
  optional `Contradicts-premise: true` marker a worker sets alongside its
  DEFERRED question when its finding empirically refutes the SPEC's or
  task's stated root cause (not merely an open information gap). The
  marker must name which artifact it contradicts — `SPEC.md` or the task
  file itself — and quote the exact contradicted excerpt verbatim, as a
  single clause or sentence (not a multi-paragraph span — the excerpt must
  be short enough to substring-match reliably). Drain records this
  distinctly under `## Deferred questions` (the flag, the named artifact,
  the quoted excerpt, and the contradicting evidence, verbatim from the
  verdict).
- R4 **Blocked re-dispatch until the premise is corrected.** For a task
  flagged `Contradicts-premise: true`, drain's batch-interview answer flow
  (`.claude/skills/drain/SKILL.md`, step 4) must not flip `Status: deferred`
  back to `pending` on a plain human answer alone. It additionally requires
  the named artifact from R3 — `SPEC.md` when the contradiction targets the
  spec, or the task file itself when it targets the task's own stated root
  cause — to no longer contain the quoted excerpt unchanged before
  re-dispatch is permitted. The check is a whitespace-normalized substring
  match: collapse runs of whitespace and newlines in both the recorded
  excerpt and the artifact's current full text before comparing, so a
  human reflow of untouched prose doesn't spuriously register as a change,
  and a genuinely edited excerpt doesn't survive a naive line-based grep.
  Until the excerpt is observed absent (post-normalization) from the
  artifact's current content, the task (and any dependent) stays
  non-dispatchable, and its HUMAN.md entry types as `decide` ("spec
  amendment needed" or "task amendment needed", matching the named
  artifact) rather than `ask` (`.claude/rules/human-blockers.md` grammar).
- R5 **Critique re-run skip, mechanized in `/critique` itself, replacing
  drain's existing commit-hash short-circuit.** Today `/critique` persists
  nothing — it only relays the verdict and findings to its caller
  (`.claude/skills/critique/SKILL.md` step 2); `critique-findings.md` is
  currently authored solely by drain's critique-intake step
  (`.claude/skills/drain/reference.md`'s "Cheap-before-expensive
  short-circuit" and NOT-READY handling). R5 **introduces** a new write:
  `/critique` becomes the sole owner of `critique-findings.md`, and drain's
  critique-intake step stops writing it (that write is removed from
  `reference.md` along with the short-circuit it supported). On every NOT
  READY or READY WITH NITS verdict against a `SPEC.md` target, `/critique`
  writes (creating the file if absent) or updates a header recording the
  content hash of the exact `SPEC.md` content that verdict was produced
  from, together with the verdict, then appends the findings in a dated
  section (the format `specs/build-doc-currency-check/critique-findings.md`
  already establishes) — header and findings written atomically in the
  same step, so the recorded hash never desyncs from the findings it
  accompanies. Before dispatching the critic agent, `/critique` first
  compares `SPEC.md`'s current content hash against that recorded header
  hash (content hash only — a commit hash is rejected because R5's own
  self-containment goal, no dependency on `git log` history surviving a
  squash or rebase, rules it out: a squashed commit's hash no longer
  resolves). If unchanged and a verdict is already recorded, skip the
  critic and relay the recorded verdict instead of re-running it. If
  `critique-findings.md` has no recorded hash (every file written before
  this requirement shipped, or a hash that fails to parse), treat it as
  changed and always run the critic — never treat a missing hash as a
  match. This skip applies only to `SPEC.md` targets, which are the only
  targets `critique-findings.md` is written for; a plan or diff invocation
  of `/critique` has no findings file to compare against and always runs
  the critic. **This requirement replaces** the "cheap-before-expensive
  short-circuit" currently in `.claude/skills/drain/reference.md`'s
  Critique intake section (the `git log -1 --format=%H` comparison against
  `critique-findings.md`'s last dated section, and the NOT-READY step's
  findings write): both are removed from `reference.md`, and drain's
  critique intake goes back to unconditionally invoking `/critique` (R6),
  which now performs the equivalent skip and the findings write internally
  via content hash. `reference.md` is therefore in this requirement's
  Touch.
- R6 **Same skip reused by drain's critique intake.** Drain's
  critique-intake step invokes `/critique` (SKILL.md: "invoke **/critique**
  via the Skill tool") unconditionally once R5 removes the pre-empting
  short-circuit, so R5's skip applies automatically inside that call; this
  requirement exists only to make the reuse explicit and to update
  `docs/memory/drain-dispatch-lessons.md`'s entry to note the lesson is now
  mechanized in `/critique` itself, not merely documented — a future
  session reading that memory file should be pointed at the shipped
  mechanism rather than re-deriving it. Concretely: replace that entry's
  text so it no longer reads as a standalone lesson but instead points at
  `/critique`'s R5 mechanism (e.g. the entry gains the literal phrase
  "mechanized in /critique" in place of the manual `git log -1` recipe it
  currently documents).
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
SKILL.md` carries a matching `antigravity/.agents/workflows/critique.md`
  mirror update (this is the actual mirror path — `critique` ports as a
  workflow, not a skill directory) and a `.claude-plugin/plugin.json`
  version bump (current: 0.8.63) in its Touch — no `codex/` mirror
  requirement, since `critique` is not one of the four
  explicit-invocation skills codex mirrors (CLAUDE.md). Any task whose
  Touch includes `.claude/skills/drain/SKILL.md` or
  `.claude/skills/drain/reference.md` carries the `antigravity/` mirror
  update, the matching `codex/.agents/skills/drain/SKILL.md` update, and
  the same plugin.json bump. `bash evals/lint-ultra-gate.sh` must stay
  green for both (`critique` and `drain` are both ultra-path skills per
  CLAUDE.md's "Testing changes" section). No task under this spec touches
  `.claude/agents/critic.md` — R1's MECHANICAL/JUDGMENT split is resolved
  (see "Design decision" below) as a `/critique`-side heuristic, not
  critic-authored metadata, so `critic.md` and its
  `antigravity/.agents/skills/critic/` mirror are out of this spec's Touch
  entirely.

**Design decision (resolves the prior Open Question).** The
MECHANICAL/JUDGMENT split is a `/critique`-side heuristic applied to the
critic's plain-text findings, not critic-authored metadata. R1 already
states this ("`/critique` classifies each finding"), and Out-of-scope
already commits to the same shape ("the triage is a post-verdict step
`/critique` and drain perform on the findings, not a new critic-side
verdict type"). Adding a structured-tag concept to the critic agent's
output format would be a larger interface change than this spec's
findings-triage scope calls for, and would touch `.claude/agents/critic.md`
plus its mirror and `plugin.json`'s `agents` enumeration for no behavioral
gain over a `/critique`-side classification pass over the same plain-text
findings. No task should edit `.claude/agents/critic.md`.

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
- `grep -c "mechanized in /critique" docs/memory/drain-dispatch-lessons.md`
  returns 0 today (confirmed absent) and ≥ 1 after R6 ships (the entry
  points at the shipped mechanism instead of the manual `git log -1`
  recipe it documents today).
- `grep -c "Cheap-before-expensive short-circuit" .claude/skills/drain/
reference.md` returns 1 today (confirmed present) and 0 after R5 ships
  (the commit-hash short-circuit is removed, not merely supplemented).
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
  `Contradicts-premise: true` (naming `SPEC.md` as the contradicted
  artifact and quoting a real excerpt from it) and confirm the batch
  interview's plain-answer flow refuses to flip the task back to `pending`
  until that exact quoted excerpt is no longer present unchanged in
  `SPEC.md`.
- MANUAL: run `/critique` twice in a row on the same unchanged `SPEC.md`
  with a recorded NOT READY or READY WITH NITS verdict and confirm the
  second run skips the critic dispatch entirely and relays the recorded
  verdict from `critique-findings.md` instead — then edit `SPEC.md` and
  confirm a third run dispatches the critic for real.

## Open questions

None. The prior open question (MECHANICAL/JUDGMENT split: critic-authored
metadata vs. `/critique`-side heuristic) is resolved under R8's "Design
decision" above.

## Parallelization

Task 01 (`.claude/skills/critique/SKILL.md` only) and task 03
(`.claude/skills/drain/reference.md` + `.claude/skills/drain/SKILL.md`)
are disjoint in Touch and free of shared undecided design — R1's
findings-triage-in-critique and R3/R4's deferred-premise-contradiction
flag are independent features with no overlapping design choice — so they
run concurrently. Task 02 depends on task 01 (same file, and R5's
hash-check/write logic is built on top of task 01's triage loop) and also
touches `.claude/skills/drain/reference.md`, which task 03 touches too —
it stays out of the group and runs after both. Task 04 depends on all
three and runs last.

- Group: 01, 03
