# Task 01: Code-vs-LLM ladder — design reference, framing/ranking gates, idea interview line, antigravity mirrors

Status: done
Depends on: ../../review-fixes/tasks/08-mirrors-and-docs.md
Budget: 30 turns
Spec: ../SPEC.md (requirements R1–R7; R8 noted under Acceptance)

## Goal

A new `.claude/skills/design/reference.md` carries the five-rung
code-vs-LLM ladder (0 pure code → 1 single structured-output call → 2
workflow patterns → 3 single agent → 4 multi-agent), the per-part tests,
and the seam rules, with the scope-separation sentence (product
architecture only; toolkit economics stay in token-discipline; process
work stays behind /idea's "a script, not a spec" gate). /design step 1
gains the code-vs-LLM classification gate, step 3 gains the lowest-rung
tiebreak and the chosen-rung-per-component appendix bullet, /idea's
interview gains the "which parts are code" line, docs/external-playbooks.md
gains the research entry (three-vendor agreement, named disagreements,
~4×/~15× cost anchors, source links, Agents Companion secondary-verified),
and the antigravity port mirrors all skill changes including a new
antigravity design reference.md.

## Touch

- `.claude/skills/design/reference.md` (new — R1, R5)
- `.claude/skills/design/SKILL.md` (step 1 sentence, step 3 sentence + appendix bullet — R2, R3)
- `.claude/skills/idea/SKILL.md` (one interview line — R4). Cross-spec: also edited by chaining-antipatterns — see specs/QUEUE.md
- `docs/external-playbooks.md` (one "Code-vs-LLM ladder" entry — R6). Cross-spec: also edited by all feature queues — see specs/QUEUE.md
- `antigravity/.agents/skills/design/reference.md` (new), `antigravity/.agents/skills/design/SKILL.md`, `antigravity/.agents/skills/idea/SKILL.md` (mirrors — R7). Cross-spec: the antigravity idea skill is also edited by chaining-antipatterns — see specs/QUEUE.md
- NOT `plugin.json` — the single combined version bump is owned by specs/review-fixes global task 99 (satisfies R8's commit-set clause)

## Steps

1. Write `.claude/skills/design/reference.md` (R1): sections `## The
   ladder` (five rungs, each with its escalation trigger; rung 2 names
   prompt-chaining, routing, parallelization, orchestrator-workers,
   evaluator-optimizer with each pattern's trigger; rung 3 carries
   OpenAI's three criteria; rung 4 breadth-first parallelizable only),
   `## Per-part tests` (rule-expressible, nuanced judgment, ruleset
   maintainability, unstructured input, failure tolerance, latency/cost,
   eval-ability — escalate only when evals show the lower rung failing),
   `## Seam rules` (structured output at every code/LLM boundary AND
   validated in application code, recording the OpenAI-vs-Gemini
   disagreement and siding with validation; side effects and loop exits
   in code; the model emits arguments only). Intro carries the R5
   scope-separation sentence cross-referencing
   `.claude/rules/token-discipline.md` and /idea's "a script, not a
   spec" gate — cross-references only, no restated content. Target well
   under 100 lines; if it exceeds 100, open with a TOC in the first 5
   lines.
2. Edit `.claude/skills/design/SKILL.md` step 1 (R2): one sentence
   containing "code-vs-LLM" — when the decision embeds generative AI in
   the product, classify each part with the ladder in reference.md
   BEFORE framing candidates; lowest rung meeting requirements is the
   default candidate, higher-rung candidates must name the failing test
   justifying escalation.
3. Edit step 3 (R3): extend the ranking sentence — for LLM-embedding
   decisions "simplicity" means the lowest rung (phrase "lowest rung");
   extend the SPEC.md-appendix bullet with "and, when the ladder
   applied, the chosen rung per component".
4. Edit `.claude/skills/idea/SKILL.md`'s Technical approach interview
   bullet (R4): one line containing "which parts are code" — for
   generative-AI features ask which parts need model judgment and which
   are rules, defaulting per /design's ladder, recording the split in
   the spec's Solution.
5. Add the "Code-vs-LLM ladder" entry to `docs/external-playbooks.md`
   (R6): three-vendor agreement (default deterministic, incremental
   escalation, code owns orchestration and side effects, structured
   output at seams, smallest capable model), named disagreements
   (Google's multi-agent lean; structured-output validation), ~4× agent
   / ~15× multi-agent token-cost anchors, source links, Agents
   Companion marked secondary-verified.
6. Mirror to antigravity (R7), same commit: port R2/R3 edits into
   `antigravity/.agents/skills/design/SKILL.md`, create
   `antigravity/.agents/skills/design/reference.md` mirroring R1
   (near-identical per convention), port the R4 line into
   `antigravity/.agents/skills/idea/SKILL.md`.
7. Run every Acceptance command from the repo root; fix until green.

## Acceptance

- [x] `test -f .claude/skills/design/reference.md && grep -q "^## The ladder" .claude/skills/design/reference.md && grep -q "^## Per-part tests" .claude/skills/design/reference.md && grep -q "^## Seam rules" .claude/skills/design/reference.md` (R1) — rc=0, verified in ../evidence/01-ladder.md
- [x] `for n in 0 1 2 3 4; do grep -qi "rung $n" .claude/skills/design/reference.md || exit 1; done && grep -qi "evaluator-optimizer" .claude/skills/design/reference.md && grep -qi "validated in application code\|validate.*application code" .claude/skills/design/reference.md` (R1 — all five rungs present + seam rule) — rc=0, verified in ../evidence/01-ladder.md
- [x] `[ "$(wc -l < .claude/skills/design/reference.md)" -le 100 ] || head -5 .claude/skills/design/reference.md | grep -qi "contents\|TOC"` (R1 size/TOC) — 65 lines, no TOC needed (../evidence/01-ladder.md)
- [x] `grep -q "code-vs-LLM" .claude/skills/design/SKILL.md` (R2) — rc=0 (../evidence/01-ladder.md)
- [x] `grep -q "lowest rung" .claude/skills/design/SKILL.md` (R3) — rc=0, appendix bullet extended too (../evidence/01-ladder.md)
- [x] `grep -q "which parts are code" .claude/skills/idea/SKILL.md` (R4) — rc=0 (../evidence/01-ladder.md)
- [x] `grep -q "token-discipline" .claude/skills/design/reference.md && grep -qi "script, not a spec" .claude/skills/design/reference.md` (R5) — rc=0, cross-references only (../evidence/01-ladder.md)
- [x] `grep -qi "code-vs-LLM ladder" docs/external-playbooks.md && sed -n '/[Cc]ode-vs-LLM ladder/,/^## /p' docs/external-playbooks.md | grep -qi "4×\|4x"` (R6 — scoped to this spec's entry so the sibling spec's 15× elsewhere in the file can't satisfy it) — rc=0, entry complete per verifier (../evidence/01-ladder.md)
- [x] `grep -q "code-vs-LLM" antigravity/.agents/skills/design/SKILL.md && test -f antigravity/.agents/skills/design/reference.md && grep -q "which parts are code" antigravity/.agents/skills/idea/SKILL.md` (R7) — rc=0, mirrors near-identical (../evidence/01-ladder.md)
- [x] R8 note (no command here): this task does NOT bump `plugin.json` — the single combined minor bump for the commit-set is owned by specs/review-fixes global task 99, which satisfies R8's "single combined bump" clause. Pre-implementation version recorded: 0.6.2; plugin.json unchanged vs main (../evidence/01-ladder.md).
- [ ] Manual (post-merge dry-read, from the SPEC): in a fresh session run /design on "add an email-triage feature: parse sender/date, categorize intent, draft replies" — the recorded decision classifies parsing as rung 0, categorization as rung 1, and names a failing test before any candidate proposes an agent. (Deferred to post-merge; not runnable pre-merge.)
