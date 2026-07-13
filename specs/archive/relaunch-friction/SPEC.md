# Close the remaining relaunch/re-invocation friction gaps

Status: open
Priority: P2

## Problem

Three friction points were raised against the gated pipeline (drain's
generation-budget relaunch, breakdown→build/drain handoff, build's
one-task-per-invocation scoping). Two same-day commits already resolved most
of this ground while this spec was being drafted:

- **Handoff friction is resolved.** c139218 replaced `disable-model-invocation`
  with a launch-authorization contract on build/autopilot/drain/prioritize
  (docs/human-gates.md:3-14): each now carries a "Launch authorization (hard
  rule)" block in its first 30 lines (verified: build/SKILL.md:7,
  autopilot/SKILL.md:7, drain/SKILL.md:7, prioritize/SKILL.md:6) requiring
  live-conversation authorization rather than blocking model-invocation
  outright. /evals alone keeps the hard flag. This already lets a spec's
  originating request ("critique, breakdown, and drain") carry authorization
  through the chain without a second manual command.
- **Generation-relaunch friction is resolved, but its documentation is not.**
  a524797 ("feat: drain autonomy — restore self-relaunch baton, same-run stub
  promotion") explicitly reverted 935e835's attended-only tightening: "Maintainer
  decision 2026-07-11 (explicit, supersedes this morning's attended-only
  tightening): no pipeline step forces a human." drain/SKILL.md:342-380
  (current) restores default self-relaunch — "spawn the successor generation
  (awaited where a parent can supervise; else headless)" (SKILL.md:361-362) —
  with the `attended` flag as the sole opt-in manual checkpoint (SKILL.md:370-372,
  "Gen 1 is always attended; passing `attended`... makes every trigger OFFER
  the baton + relaunch command instead of self-relaunching"). This is exactly
  the shape originally wanted: continuous-by-default, periodic-checkpoint
  opt-in.

  But a524797 touched only `.claude-plugin/plugin.json`,
  `.claude/skills/drain/{SKILL,reference}.md`, and the antigravity mirror — it
  did **not** touch `.claude/rules/token-discipline.md:93-100`, whose "Awaited
  children, never detached (maintainer policy, 2026-07-09)" bullet still reads
  as an unconditional ban — specifically its "no orphaned children outliving
  the step that spawned them" clause, which drain's headless fallback breaks
  outright regardless of the separate "where an attended parent can supervise
  instead" qualifier a few words later (that qualifier arguably already
  excuses the no-parent-available case, making it the wrong clause to anchor
  an exception to). 935e835's commit message cites this rule and reports it
  was a "maintainer correction... after a gen-2 headless relaunch"; that a
  headless hub running unsupervised merges/pushes was the concern is this
  spec's inference from that context, not a verbatim quote from the commit.
  a524797 reintroduced that headless fallback without editing the rule that
  was used to ban it, so
  the repo now contains two files in direct, unreconciled conflict: the rule
  says never-detached, the shipped skill does the opposite by design. Anyone
  (human or agent) reading token-discipline.md today has no way to know
  drain's headless case is a deliberate, dated exception rather than a
  violation of standing policy.

  (Checked and found NOT a gap: the antigravity mirror,
  antigravity/.agents/workflows/drain.md:509, still says "an Antigravity run
  cannot self-relaunch `claude`" — this is a correct, load-bearing statement
  of an actual Antigravity harness limitation, not staleness, and needs no
  change.)

- **Build's one-task-per-invocation friction is still open.** build/SKILL.md
  has no queue concept — it executes exactly the task file passed via
  `$ARGUMENTS` and ends with "Tell the user to `/clear` before starting the
  next task" (build/SKILL.md:187). Nothing in the skill points at `/drain` as
  the tool for multi-task specs, so a human working a multi-task spec has to
  either know to reach for `/drain` unprompted or manually re-invoke `/build`
  per task.

## Solution

1. **Reconcile the rule with the shipped behavior (documentation only).**
   Add a dated, scoped exception to token-discipline.md's "Awaited children,
   never detached" bullet naming drain's generation-boundary self-relaunch
   specifically, citing a524797's rationale and the launch-vs-continuation
   framing docs/human-gates.md already uses for its own 2026-07-11 note
   (human-gates.md:115-131: "the human gates govern the _launch_ of an
   autonomous run, not its _continuation_"). No behavior change to drain
   itself — a524797's decision stands; this closes the gap between what the
   rule says and what the shipped skill does, the same kind of gap
   human-gates.md's own "2026-07-11 note" pattern already closes elsewhere in
   this repo.
2. **Give build a sibling-task nudge, not a loop mode.** At build/SKILL.md's
   end-of-run step (build/SKILL.md:187, the "/clear before starting the next
   task" line), when the just-completed task file resolves to a
   `specs/<slug>/tasks/*.md` path AND that directory contains other
   `tasks/*.md` files with `Status: pending`, print one line naming
   `/drain specs/<slug>` as the tool for continuous work across the remaining
   tasks. `Status: blocked` siblings alone do not trigger the nudge — blocked
   work isn't necessarily actionable by `/drain` either, so nudging toward it
   for blocked-only remainders would be misleading. Task files outside a
   `specs/<slug>/tasks/` layout (no derivable slug) never trigger the nudge.
   This is informational only — build gains no
   loop/continuation logic of its own. An in-build loop was considered and
   rejected: it would fight the "one task per session, `/clear` between
   tasks" session-hygiene rule (token-discipline.md, "Session hygiene") that
   `/drain` already satisfies correctly via fresh per-task subagent dispatch;
   duplicating that inside build would just build a worse `/drain`.

## Requirements

R1: `.claude/rules/token-discipline.md`'s "Awaited children, never detached"
bullet (currently line 93) carries a dated exception sentence anchored
specifically to its "no orphaned children outliving the step that spawned
them" clause — the clause drain's headless fallback actually breaks, not the
separate "where an attended parent can supervise instead" qualifier, which
already reads as conditioned on supervision being available. The exception
names drain's generation-boundary self-relaunch (headless fallback included),
citing a524797 and docs/human-gates.md's launch-vs-continuation framing —
worded so a future reader of the rule alone (without archaeology through git
log) can tell this is a deliberate, dated exception and not policy drift.

R2: `build/SKILL.md`'s end-of-run reporting step checks whether the
just-completed task file resolves to a `specs/<slug>/tasks/*.md` path, and if
so, whether any sibling `tasks/*.md` file in that directory has
`Status: pending` (blocked-only remainders do not count). If both hold, its
final output prints one line pointing at `/drain specs/<slug>` for continuous
multi-task work, alongside (not replacing) the existing `/clear`-before-next-
task instruction. If the task isn't under a `specs/<slug>/tasks/` path, or no
pending siblings remain, no nudge line appears.

R3: No change in this spec re-tightens a524797's explicit decision — the
`attended` flag in `/drain` remains the only opt-in manual-relaunch
checkpoint; default behavior stays self-relaunching through queue-empty or
the 10-generation cap.

## Out of scope

- Any change to drain's actual self-relaunch dispatch logic (awaited vs.
  headless decision, the `max(2, 6-W)` budget formula, the 10-generation cap)
  — a524797 already made this call explicitly and this spec does not
  re-litigate it.
- Adding a "continue to next task automatically" mode inside `/build` —
  rejected in Solution #2.
- The antigravity mirror's "cannot self-relaunch" line — confirmed correct
  as-is (Problem section), not touched.
- Re-auditing /evals or /autopilot's autonomy-classification gate — untouched
  by any of the commits this spec responds to.

## Acceptance criteria

- [ ] `grep -n "2026-07-11" .claude/rules/token-discipline.md` shows the new
      exception sentence adjacent to the "Awaited children, never detached"
      bullet, and it names drain's generation relaunch specifically (not a
      generic carve-out).
- [ ] `grep -n "drain specs/<slug>" .claude/skills/build/SKILL.md` (or the
      exact chosen wording) is present in the end-of-run section, guarded by
      a sibling-`Status:` check rather than unconditional.
- [ ] Manual run: `/build` on one task from a 2+ task spec under
      `specs/<slug>/tasks/` where a sibling task is still `Status: pending` —
      final output includes the `/drain` nudge line.
- [ ] Manual run: `/build` on a single-task spec (no pending siblings) — final
      output does NOT include the nudge line (confirms the guard isn't
      unconditional).
- [ ] Manual run: `/build` on a task whose only sibling is `Status: blocked`
      (no `pending` siblings) — final output does NOT include the nudge line.
- [ ] Manual run: `/build` on a task file outside any `specs/<slug>/tasks/`
      layout — final output does NOT include the nudge line (no derivable
      slug).
- [ ] `bash evals/lint-ultra-gate.sh` still passes (build/SKILL.md is not one
      of the four ultra-path skills, but the gate is cheap to confirm
      unaffected since it scans broadly).
- [ ] End-to-end: a fresh session reads token-discipline.md's awaited-children
      bullet alone (no git-log archaeology) and can correctly state whether
      drain's headless self-relaunch is policy-compliant or a violation.

## Open questions

(none)

## Parallelization

Two tasks, fully disjoint `Touch` sets (task 01: only
`.claude/rules/token-discipline.md`; task 02: `.claude/skills/build/SKILL.md`,
its antigravity mirror, and `.claude-plugin/plugin.json`) and no shared
undecided design — each requirement's exact anchor text and guard condition
is fully specified in Requirements R1/R2, so neither task makes an open
choice the other could collide with. Both pass the decision-coupling test.

- Group: 01, 02
