# Task 02: Drain SKILL.md and reference.md consume the scanner

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: done
Depends on: 01
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirement R3)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

Every point where the frontier is currently model-derived defers to the
scanner: the inventory step invokes `drain_frontier.py` per spec dir;
step 2's tie-break paragraph carries the mandated verbatim sentence
"tie-break is computed by drain_frontier"; reference.md's Rolling-window
admission section defers to scanner output for structure while drain
keeps the live-window gate and admit count. The fallback is explicit:
script missing or non-zero → today's header-reading procedure verbatim,
with scanner stderr quoted in the fallback log line.

## Touch

Do NOT touch the mirrors (task 04) or evals/ (task 03). Keep additions
minimal — drain/SKILL.md already exceeds the size budget (a separate
spec owns that overage); do not restructure unrelated sections.

## Steps

1. Read SPEC.md R3, then the three target regions (inventory step,
   step 2 tie-break, reference.md Rolling-window admission).
2. Edit each to defer to the scanner per R3, including the verbatim
   tie-break sentence and the stderr-quoting fallback.
3. drain/SKILL.md is ultra-gated: run `bash evals/lint-ultra-gate.sh`
   before committing.

## Acceptance

- [x] `grep -c 'drain_frontier' .claude/skills/drain/SKILL.md` → ≥ 2
      and `grep -c 'tie-break is computed by drain_frontier'
  .claude/skills/drain/SKILL.md` → ≥ 1 and `grep -c
  'drain_frontier' .claude/skills/drain/reference.md` → ≥ 1 (all
      anchors 0 today, verified 2026-07-19). Depth ceiling: procedure
      prose — behavioral complement is task 03's trajectory assertion
      plus task 01's unit tests.
      Evidence: counts 2 / 1 / 1 observed; verifier PASS
      (evidence/02-drain-consumes-scanner.md).
- [x] `bash evals/lint-ultra-gate.sh` → exit 0
      Evidence: exit 0, "all ultra mentions gated in 4 files"; size gate
      also green at exactly 500 lines (evidence/02-drain-consumes-scanner.md).

## Progress

- [2026-07-20 /drain] Attempt 1 (opus): implementation DONE, verifier PASS
  on all acceptance criteria and mirror-coverage gate, but the merge failed
  drain's own project gate: `bash evals/lint-skill-size-gate.sh` →
  ".claude/skills/drain/SKILL.md:515: exceeds 500-line SKILL.md budget"
  (515 lines, 15 over the 500-line cap; the task added 27 net lines to
  SKILL.md). Branch task/02-drain-consumes-scanner discarded (merge reset,
  never pushed). Relaunching one tier up per the slot machine.
- [2026-07-20 /drain] Attempt 2 (fable): implementation DONE, SKILL.md
  landed at exactly 500 lines. Worker spawned its own verifier as a
  background child (`isolation: worktree` worker prompt's "awaited
  children" clause) but its own turn ended before collecting that child's
  result — an orphaned-child violation, not the sanctioned drain-baton
  carve-out. Drain (this session) discovered the orphaned verifier via its
  own delayed task-notification (routed to the hub since its immediate
  parent had already exited), independently re-verified all 7 criteria
  from scratch rather than trusting either the worker's unverified
  "verifier PASS" claim in its own checkbox evidence or the verifier's
  first (stale FAIL, since-fixed) evidence file, then committed the
  close-out and merged. See `## Discovered` below.

## Discovered

- Worker-spawned verifier orphaning (this task, attempt 2): an
  `implementation-worker` that spawns its own verifier sub-agent per
  build's procedure can have its own turn end (budget/turns exhausted)
  before awaiting that child's result, leaving the verifier to notify the
  ORCHESTRATOR directly once it finishes — bypassing the worker's own
  close-out entirely. The task file was left with an accurate diff but an
  uncommitted, unclosed state and an unverified "verifier PASS" claim
  baked into its own acceptance evidence text. `.claude/rules/
token-discipline.md`'s "a worker that spawns its own verifier awaits it
  inline the same way" clause states the requirement but nothing enforces
  it structurally — worth a durable guard (e.g. the build procedure's
  worker-verifier dispatch made synchronous/foreground-only, or a
  post-hoc drain check that treats an uncommitted worktree with a
  present-but-uncited evidence file as its own BLOCKED-shaped verdict
  rather than trusting a stale task-notification's prose). Not fixed
  here — out of this task's Touch scope.
