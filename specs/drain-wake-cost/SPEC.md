# Cheap wakes for drain's rolling window

Status: open
Priority: P1

## Problem

The rolling-window design (specs/drain-rolling-window, shipped) traded wave
barriers for per-verdict wakes to kill wave-tail latency. agentprof now
quantifies what that trade accepted on the other side (see EVIDENCE.md,
2026-07-04→11 window): every verdict-collection wake that lands >5 minutes
after the orchestrator's last call re-caches the entire orchestrator context
at 1.25× input rate — 268 such wakes cost $587 in one week, and drain-shaped
sessions dominate them. Two compounding factors:

1. **The orchestrator context is fat.** Median rewrite is 187k tokens
   (p90 384k). At that size a single verdict wake costs ≈$3.50; at 40k it
   would cost ≈$0.75. Drain's main line holds 51% of the skill's total cost
   — high for a pure dispatcher.
2. **The baton trigger is count-based, not size-based.** The generation
   boundary (~4 verdicts) does not prevent context accumulation: across all
   heavy orchestration sessions, $1,279 (45% of main-line spend) was spent
   *after* the session's context first crossed 200k, where every call costs
   2–4× the early-session rate.

Separately, freehand drain invocations ("drain the recover dark ball…",
"ultracode") ran $1,406 in one week under `(no skill)` — five times the
attributed skill:drain cost — without any of the skill's structure.

The rolling window itself is NOT in question: keep per-verdict admission,
keep serial merges. Make each wake cheap instead of making wakes rare.

## Solution

Amend `.claude/skills/drain/SKILL.md` (and its baton procedure) so the
orchestrator context stays small enough that per-verdict re-caching is
noise: an explicit context-budget baton trigger alongside the verdict-count
one, hard caps on what a verdict may carry into the hub, a ban on re-reading
worker output at merge time, and a short "wake economics" doctrine paragraph
so future edits don't regress it. Broaden the skill's trigger description so
freehand drain requests enter the skill.

## Requirements

- R1 **Context-budget baton trigger.** The generation boundary becomes
  "after ~4 verdicts OR when the orchestrator's context is heavy, whichever
  comes first". Heaviness must be checkable by the model from inside the
  session (mechanism is an open question below; candidates: harness context
  warnings, cumulative-verdict count × size bookkeeping in DRAIN-BATON.md,
  or a fixed lower verdict count when W ≥ 3). The chosen rule and its
  rationale get one sentence in the SKILL.md baton section.
- R2 **Lean verdict contract.** The verdict a worker returns to the hub is
  capped (target ≤ 2k tokens): status, merged-commit/branch, per-criterion
  pass/fail with one-line evidence, deferred items. Worker transcripts,
  full diffs, and test output stay out of the hub; the existing "structured
  verdict + evidence, never its transcript" line gets the explicit cap.
- R3 **No merge-time re-reads.** At merge/verdict time the orchestrator may
  run `git diff --stat` (path-scoped) and read the verdict — it must not
  Read task files, worker diffs, or check output into its own context; when
  it genuinely needs file contents it dispatches a scout. Stated as an
  explicit MUST NOT in the merge step.
- R4 **Wake-economics doctrine paragraph.** One short paragraph in SKILL.md
  (near the rolling-window section) stating the mechanism: awaited workers
  outlive the 5-minute cache TTL, so every verdict wake re-caches the whole
  hub context at 1.25× input rate — the hub's size, not the wake count, is
  the cost lever. Include the one-line cost model (context_tokens ×
  input_rate × 1.25 per wake).
- R5 **Freehand capture.** The skill frontmatter description gains
  natural-language triggers ("drain the …", "work through the remaining
  tasks", "accomplish the tasks in specs/…") so freehand drain requests
  resolve into the skill instead of running unstructured.
- R6 **Session-model note.** One sentence in SKILL.md: a drain hub is a
  dispatch loop whose judgment lives in the task files and pinned worker
  tiers; running the hub session on a frontier model roughly doubles wake
  cost for no quality gain — recommend the default (opus) tier or below for
  dedicated drain sessions.

## Out of scope

- Reverting to wave/barrier dispatch or changing window admission, merge
  order, or the Touch-disjointness rules (drain-rolling-window owns those).
- Harness-level cache-TTL changes or background-worker redesign.
- The <5m prefix-invalidation rewrites ($236/week) — cause unknown, likely
  harness-level (system-reminder/context injection); not addressable from
  skill text.
- /build, /breakdown, /idea restructuring (specs/orchestrator-share-audit).

## Acceptance criteria

- [ ] `grep -qi 'context' /Users/sjaconette/claude/.claude/skills/drain/SKILL.md && grep -qiE 'baton|generation' /Users/sjaconette/claude/.claude/skills/drain/SKILL.md` and the baton section states a context-budget trigger alongside the verdict count (R1)
- [ ] `grep -qiE '2[, ]?000 tokens|2k tokens' /Users/sjaconette/claude/.claude/skills/drain/SKILL.md` — verdict cap present (R2)
- [ ] Merge step contains an explicit MUST NOT about reading task files/diffs/check output into the hub context (R3)
- [ ] `grep -qiE 'cache|TTL|re-?cach' /Users/sjaconette/claude/.claude/skills/drain/SKILL.md` — wake-economics paragraph present with the cost model (R4)
- [ ] Skill description in frontmatter names at least two freehand trigger phrasings (R5)
- [ ] Session-model sentence present (R6)
- [ ] MANUAL (deferred, needs a week of runs): re-run `agentprof claude --days 7`; main-line rewrite cost inside drain-shaped sessions materially down vs the $587 TTL-expiry baseline, and freehand drain turns attribute to skill:drain
- [ ] End-to-end: a /drain run over a 2-task demo spec completes with hub verdicts each ≤ 2k tokens and no task-file Reads by the hub after dispatch (inspect transcript)

## Open questions

- R1 mechanism: what signal can the hub actually check for "context is
  heavy"? If nothing reliable exists in-session, fall back to an adaptive
  verdict count (e.g. baton after max(2, 6−W) verdicts) — pick during
  implementation and record the choice in the spec.
- Should the baton itself be slimmed at the same time (it is re-read by the
  successor generation and grows per generation)? Measure its size in a real
  run before deciding.
