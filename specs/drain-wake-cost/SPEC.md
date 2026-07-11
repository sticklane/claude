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
attributed skill:drain cost — without any of the skill's structure. Drain is
human-gated (`disable-model-invocation: true`, mandated by CLAUDE.md), so
the model can never auto-route these into the skill; the only permissible
lever is having the session *recommend* `/drain` to the human.

The rolling window itself is NOT in question: keep per-verdict admission,
keep serial merges. Make each wake cheap instead of making wakes rare.

## Solution

Amend `.claude/skills/drain/SKILL.md` and the worker final-message contract
in `.claude/skills/drain/reference.md` so the orchestrator context stays
small enough that per-verdict re-caching is noise: an explicit
context-budget baton trigger alongside the verdict-count one, a hard cap on
what a verdict may carry into the hub (enforced in the worker prompt, not
just described), a ban on pulling worker code diffs and check output into
the hub, and a short "wake economics" doctrine paragraph so future edits
don't regress it. Add a doctrine line so sessions receiving freehand
drain-shaped requests recommend `/drain` to the human. Ship through the
repo's mirror + plugin-bump gate.

## Requirements

- R1 **Context-budget baton trigger.** The generation boundary becomes
  "after ~4 verdicts OR when the orchestrator's context is heavy, whichever
  comes first". Heaviness must be checkable by the model from inside the
  session (mechanism is an open question below; candidates: harness context
  warnings, cumulative-verdict count × size bookkeeping in DRAIN-BATON.md,
  or a fixed lower verdict count when W ≥ 3). The chosen rule and its
  rationale get one sentence in the SKILL.md baton section.
- R2 **Lean verdict contract, enforced in the worker prompt.** The verdict
  a worker returns to the hub is capped (target ≤ 2k tokens): status,
  merged-commit/branch, per-criterion pass/fail with one-line evidence,
  deferred items. The cap lands in BOTH places: the worker final-message
  contract in `reference.md` (~lines 522–538 — this is what workers
  actually obey) and the "structured verdict + evidence, never its
  transcript" line in SKILL.md.
- R3 **No worker-output re-reads at merge time.** At merge/verdict time the
  hub must not pull the worker's *code diffs* or the *worker's own
  check/test output* into its own context — `git diff --stat` (path-scoped)
  plus the verdict is the ceiling; when the hub genuinely needs file
  contents it dispatches a scout. Explicitly EXEMPT (shipped machinery this
  spec must not weaken): the append-only whitelist content diff over
  `tasks/` (SKILL.md ~200–208), CAS re-reads of `Status:` header lines
  (SKILL.md ~170–178), `## Progress`/`## Deferred`/`## Decisions` append
  edits, and the hub's OWN post-merge project-gate run — its pass/fail plus
  the bounded output tail already specified for relaunch evidence
  (reference.md ~609). Stated as an explicit MUST NOT with the exemption
  list in the merge step.
- R4 **Wake-economics doctrine paragraph.** One short paragraph in SKILL.md
  (near the rolling-window section) stating the mechanism: awaited workers
  outlive the 5-minute cache TTL, so every verdict wake re-caches the whole
  hub context at 1.25× input rate — the hub's size, not the wake count, is
  the cost lever. Include the one-line cost model (context_tokens ×
  input_rate × 1.25 per wake).
- R5 **Freehand → /drain recommendation.** Drain stays human-gated; the
  model can never auto-enter it. The doctrine line: when a freehand request
  is drain-shaped ("drain the …", "work through the remaining tasks in
  specs/…"), recommend the human launch `/drain` rather than improvising an
  unstructured dispatch loop, and say why (the skill's window/baton/verdict
  machinery is what keeps the loop cheap and safe). Scope caveat: the
  measured freehand spend is cross-repo, and this repo's CLAUDE.md/rules
  load only in-repo — so the deliverable is (i) the line in this repo's
  doctrine (covers toolkit-repo sessions) plus (ii) a proposed one-liner
  for the user's global `~/.claude/CLAUDE.md`, applied as a MANUAL
  (attended) step since that file is user-private and outside this repo.
- R6 **Session-model note.** One sentence in SKILL.md: a drain hub is a
  dispatch loop whose judgment lives in the task files and pinned worker
  tiers; running the hub session on a frontier model roughly doubles wake
  cost for no quality gain — recommend the default (opus) tier or below for
  dedicated drain sessions.
- R7 **Ship gate.** Tasks that change `.claude/skills/drain/*` carry in
  their `Touch:`: the antigravity mirror
  (`antigravity/.agents/workflows/drain.md` — regenerate for both SKILL.md
  and reference.md changes), the `.claude-plugin/plugin.json` version bump,
  `bash evals/lint-ultra-gate.sh` green, and `claude plugin validate .`
  passing. R1 changes baton-trigger semantics, so the /evals drain
  scenario is updated to exercise (or at least not contradict) the dual
  trigger — same obligation drain-rolling-window R7 carried for window
  semantics.

## Out of scope

- Reverting to wave/barrier dispatch or changing window admission, merge
  order, or the Touch-disjointness rules (drain-rolling-window owns those).
- Harness-level cache-TTL changes or background-worker redesign.
- The <5m prefix-invalidation rewrites ($236/week) — cause unknown, likely
  harness-level (system-reminder/context injection); not addressable from
  skill text.
- /build, /breakdown, /idea restructuring (specs/orchestrator-share-audit).

## Acceptance criteria

- [ ] `grep -qiE 'context.{0,40}(budget|heavy|trigger)' /Users/sjaconette/claude/.claude/skills/drain/SKILL.md` AND MANUAL: the baton section states the dual trigger (verdict count OR context budget) as one rule a hub can evaluate (R1)
- [ ] `grep -qiE 'final message.{0,120}2k tokens|verdict.{0,120}2k tokens|2k tokens.{0,120}(final message|verdict)' /Users/sjaconette/claude/.claude/skills/drain/reference.md` — cap attached to the worker final-message/verdict contract specifically (an unrelated pre-existing "1–2k tokens" assessor line must not satisfy this) — and the same cap named in SKILL.md (R2)
- [ ] MANUAL: merge step contains the MUST NOT (worker code diffs, worker's check/test output) with the explicit exemption list (whitelist content diff, CAS/status-header re-reads, section appends, hub's own gate run + bounded output tail) (R3)
- [ ] `grep -q '1\.25' /Users/sjaconette/claude/.claude/skills/drain/SKILL.md && grep -qiE 'TTL' /Users/sjaconette/claude/.claude/skills/drain/SKILL.md` — wake-economics paragraph with the cost model (R4)
- [ ] Doctrine line recommending /drain for drain-shaped freehand requests present in this repo's CLAUDE.md or cited rules doc (MANUAL confirm the recommend-the-skill context), and the proposed global `~/.claude/CLAUDE.md` one-liner delivered as a MANUAL (attended) step (R5)
- [ ] Session-model sentence present in SKILL.md (R6)
- [ ] `bash /Users/sjaconette/claude/evals/lint-ultra-gate.sh` → exit 0; `claude plugin validate .` → pass; antigravity mirror regenerated, `.claude-plugin/plugin.json` version bumped, and /evals drain scenario updated for the dual baton trigger in the shipping commits (R7)
- [ ] MANUAL (deferred, needs a week of runs): re-run `agentprof claude --days 7`; main-line rewrite cost inside drain-shaped sessions materially down vs the $587 TTL-expiry baseline
- [ ] End-to-end: a /drain run over a 2-task demo spec completes with hub verdicts each ≤ 2k tokens and no reading of task-file *bodies* by the hub after dispatch (Status/header lines and the tasks/ whitelist diff are fine) — inspect transcript

## Open questions

- R1 mechanism: what signal can the hub actually check for "context is
  heavy"? If nothing reliable exists in-session, fall back to an adaptive
  verdict count (e.g. baton after max(2, 6−W) verdicts) — pick during
  implementation and record the choice in the spec.
- Should the baton itself be slimmed at the same time (it is re-read by the
  successor generation and grows per generation)? Measure its size in a real
  run before deciding.
