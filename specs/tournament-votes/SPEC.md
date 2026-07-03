# Majority-PASS verifier votes in the drain tournament

## Problem

The drain tournament's filter stage rests on a single judgment: "Each
DONE candidate gets one verifier run per candidate"
(.claude/skills/drain/reference.md, Filter). One verifier vote decides
whether a candidate survives, and the rank stage then orders survivors
by that lone report's gate findings. A tournament only runs after two
failed attempts — precisely when the task has proven tricky and a
plausible-but-wrong candidate is most likely — yet that is where a
single verifier's false PASS or false FAIL is decisive. The
generate–filter–rank shape came from the AlphaCode 2 entry in
docs/external-playbooks.md; this session's ultracode research
surfaced N-vote adversarial verification (independent skeptics,
majority decides) as the standard cure for single-judge error — a
harness-observed Workflow quality pattern, recorded by this spec in
docs/external-playbooks.md (R6). The toolkit's verifier already
returns independent per-run verdicts; nothing aggregates them.

## Solution

Three decisions, recommended options adopted (non-interactive fallback,
each reversible before implementation): (1) three independent verifier
runs per DONE candidate — not five; a tournament already triples
worker spend, and votes triple verifier spend only inside tournaments
(at most one per task per drain run), keeping the cost bounded; (2) a
candidate survives the filter only on majority PASS (two of three)
over verifier verdicts — FAIL and INCOMPLETE are non-PASS votes, a
verifier-BLOCKED run disqualifies outright with its quote recorded,
and verifiers never DEFER — no new verifier output mode, consistent
with the context-management spec's R5 (INCOMPLETE is non-PASS by
construction); (3) aggregation
stays drain's mechanical job ("Drain, not the verifier"): PASS-vote
count becomes the first rank key, ahead of the existing keys. The
tournament template in specs/workflow-author (R4 there) cites this
spec as the design owner. Marker phrases ("majority PASS", "PASS
votes") do not exist in the implementation targets today, so the
acceptance greps cannot pass vacuously.

## Requirements

- R1 (filter): `.claude/skills/drain/reference.md`'s Filter paragraph
  replaces the single run with three independent verifier runs per
  DONE candidate — same verifier agent, same no-evidence-path rule,
  each inside that candidate's worktree, fresh eyes per run (no shared
  transcript). Vote values are the VERIFIER's verdicts only —
  PASS/FAIL (plus INCOMPLETE once the context-management spec lands);
  verifiers never DEFER. A candidate survives only on majority PASS
  (contains the phrase "majority PASS"); FAIL and INCOMPLETE count as
  non-PASS votes. A verifier run returning BLOCKED (the untrusted-data
  rule on a redirection attempt in the candidate's content) is NOT a
  vote: it DISQUALIFIES the candidate outright regardless of other
  votes, and the verifier's quoted content goes into the recorded
  evidence — survivors must be injection-clean, and the quote must
  never be droppable by two PASS votes. Candidates whose WORKER
  verdict was BLOCKED or DEFERRED never reach the verifier at all —
  that handling (reasons into evidence, questions collected for
  verdict routing) is unchanged.
- R2 (rank): the Rank paragraph keeps "Drain, not the verifier ...
  mechanically" and its existing keys, but PASS-vote count (3 ahead
  of 2) becomes the FIRST key (the phrase "PASS votes" appears in the
  Rank paragraph itself); gate-finding counts are summed across the
  candidate's three verifier reports for the second key; smallest
  `git diff --stat` total third; and a NEW final tiebreak — lowest
  angle index (t1 before t2 before t3) — so the mechanical ranker
  always terminates with an order. Still no new verifier output mode.
- R3 (cost note): one sentence in the Tournament section states the
  spend shape: votes triple verifier cost inside tournaments only —
  bounded by the at-most-one-tournament-per-task rule — and the
  tournament remains inside the human-authorized /drain launch
  (cite docs/human-gates.md, don't restate).
- R4 (mirrors): the antigravity port's drain workflow adopts the same
  majority-PASS wording for its tournament step (its verifier runs are
  launch-list dispatched, but the two-of-three rule and vote-count
  rank key are runtime-neutral prose).
- R5 (versioning): the implementing change bumps `plugin.json`'s minor
  version by one from the value it finds, unless landing in a
  commit-set whose other specs already carry a single combined bump.
- R6 (research record): the AlphaCode 2 entry in
  `docs/external-playbooks.md` gains a follow-on line (or adjacent
  bullet) containing "N-vote": N-vote adjudication — multiple
  independent verifier votes with majority rule — is the standard
  cure for single-judge error in generate–filter–rank pipelines
  (harness-observed Workflow quality pattern: adversarial verify
  votes; adopted here for the tournament filter). Marked
  harness-observed, no public URL.

## Out of scope

- Any verifier agent change — verdicts stay PASS/FAIL (plus
  INCOMPLETE once the context-management spec lands); aggregation is
  drain arithmetic, never a verifier mode.
- N-vote verification outside tournaments — /build's single verifier
  run per task is the right default cost; votes are for the
  proven-tricky path only.
- Changing the Generate stage (three angle workers), the slot-machine,
  Merge, or Verdict routing — the filter and rank sentences are the
  entire surface.
- Making N configurable — three is fixed in v1; a `.claude/runtime.md`
  knob would be premature configurability.

## Acceptance criteria

- [ ] `grep -q "majority PASS" .claude/skills/drain/reference.md && grep -q "three independent verifier" .claude/skills/drain/reference.md` (R1)
- [ ] `sed -n '/^\*\*Rank\./,/^$/p' .claude/skills/drain/reference.md | grep -q "PASS votes" && grep -q "Drain, not the verifier" .claude/skills/drain/reference.md && sed -n '/^\*\*Rank\./,/^$/p' .claude/skills/drain/reference.md | grep -q "t1 before t2"` (R2 — vote key and final tiebreak in the Rank paragraph itself, mechanical-rank sentence intact; scoped so R1's Filter wording cannot satisfy it)
- [ ] `! grep -qi "one verifier run per candidate" .claude/skills/drain/reference.md` (R1 — the single-run sentence is actually replaced)
- [ ] `sed -n '/^## Tournament/,/^## /p' .claude/skills/drain/reference.md | grep -qi "human-gates"` (R3, scoped to the Tournament section)
- [ ] `grep -q "majority PASS" antigravity/.agents/workflows/drain.md && grep -q "PASS votes" antigravity/.agents/workflows/drain.md && ! grep -qi "one verifier-skill run per candidate" antigravity/.agents/workflows/drain.md` (R4 — mirror adopts both changes AND the old single-run line is actually replaced, not appended-around)
- [ ] plugin.json minor version strictly greater than the pre-implementation value, verified in the implementing task's evidence (R5)
- [ ] `grep -q "N-vote" docs/external-playbooks.md` (R6)
- [ ] End to end: dry-run the tournament procedure on paper against a 3-candidate example (votes 3/2/1 PASS) — the 1-PASS candidate is filtered, the 3-PASS candidate outranks the 2-PASS one regardless of gate-finding counts, a 2-2 tie on votes falls through to summed gate findings, and a full tie on all three keys resolves by angle index (t1 first); separately, a 2-PASS+1-BLOCKED candidate is DISQUALIFIED with the quote recorded (manual dry-read until the eval harness covers /drain).

## Open questions

(none — the three decisions are recorded in Solution; recommended
options adopted per the non-interactive fallback, reversible before
implementation.)

## Parallelization

Not yet decomposed — when /breakdown runs, its tasks join
[specs/QUEUE.md](../QUEUE.md) (update its count and wave table then).
Known serial chains to wire as `Depends on:` lines:
`.claude/skills/drain/reference.md` is also edited by review-fixes 02
(drain state machine) and model-agnostic 02 (active-runtime-profile
framing) — this spec's edit serializes after both; the
workflow-author spec's tournament template cites this design and
should land after it. The antigravity mirror (R4) rides the same
mirror chain as review-fixes 08 / model-agnostic 04.
