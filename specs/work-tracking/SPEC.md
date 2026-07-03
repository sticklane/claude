# Work tracking: discovered work, immutable acceptance, stopping points

## Problem

Removing the beads backend (maintainer decision, recorded in
docs/external-playbooks.md "Considered and rejected") orphaned the one
capability it carried that the markdown queue lacks: capturing work an
agent DISCOVERS mid-task. Today a drain worker that finds a bug, a
missing test, or a spec gap can only mention it in a report that gets
summarized away — nothing lands in the queue. Two adjacent gaps came
out of the same cross-vendor research (recorded by this spec, R6):
nothing forbids a worker from editing its own task's acceptance
criteria (Anthropic's long-running-harness discipline makes state
files effectively append-only — agents flip `passes` and nothing
else, "it is unacceptable to remove or edit tests"; our only guard is
the verifier's judgment-based overfitting check), and partial progress
at a failed or interrupted stopping point survives only in discarded
worker transcripts (OpenAI's ExecPlans require every stopping point
documented, splitting work into done-vs-remaining, restartable from
the plan alone). No vendor has agents autonomously filing follow-up
work items — Anthropic's task-tool prompt ("after completing a task,
add any new follow-up tasks; check the list first to avoid
duplicates") is the closest signal — so the capture design below is
ahead of published guidance and must stay conservative: humans gate
what enters the queue.

## Solution

Four decisions, recommended options adopted (non-interactive fallback,
each reversible before implementation), all riding the existing
"workers report, drain records" single-writer state model: (1)
discovered work flows worker-report → drain-materialized DRAFT stubs —
workers gain a fixed `Discovered:` report section; drain (the sole
queue writer) turns each item into a header-only task stub with
`Status: draft` in the reporting task's spec, deduplicating against
existing title lines first; `draft` is never dispatchable — only a
human promotes it to `pending`, after vetting the quoted Goal, keeping
new-work spend behind the human gate (docs/human-gates.md reason 1);
(2) task files become append-only for workers: a worker may flip only
its own task's `Status:` line, tick checkboxes, keep its plan block,
and append to designated sections (`## Progress`, `## Deferred
questions`) — never edit Goal/Steps/criterion text of any task —
enforced mechanically by the verifier via `git diff` against a defined
base, not just by prose; (3) non-done stopping points get recorded: drain appends a
`## Progress` entry (done vs remaining, from the worker's report) to
the task file before relaunch/tournament, so the next attempt starts
from evidence instead of zero; (4) done-item archiving is explicitly
declined for now (Kiro's clear-finished and Backlog.md archiving solve
a scale problem this queue doesn't have; evidence dirs and git history
already preserve the record). Marker phrases ("Status: draft",
"Discovered:", "## Progress", "done vs remaining", "only on the
user's yes", "never dispatchable", "only a human") do not exist in
the implementation targets today, so the acceptance greps below
cannot pass vacuously.

## Requirements

- R1 (worker report contract): the drain worker prompt
  (`.claude/skills/drain/reference.md`) and `/build`'s report step
  (`.claude/skills/build/SKILL.md`) gain a fixed report section
  `Discovered:` — zero or more single-line items, each "what + where +
  why it matters", for work found but out of the task's scope. Workers
  NEVER create or edit task files for discoveries (the unattended path
  especially — report only). An empty section means none. For non-DONE
  verdicts the final message also carries one fixed `Done vs
  remaining:` line summarizing partial progress — the worker prompt's
  DEFERRED sentence ("the questions verbatim ... all the orchestrator
  will ever see") is amended to admit these two fixed sections
  alongside the verdict.
- R2 (drain materializes drafts): drain's bookkeeping
  (`.claude/skills/drain/SKILL.md`) gains a step containing "Status:
  draft": for each reported discovery, drain first compares against
  the TITLE lines of existing task files in the owning spec's tasks/
  dir — owning spec = the REPORTING task's spec — (dedupe: the vendor
  pattern is check-the-list-first); if new, it writes a header-only
  stub `NN-<kebab-slug>.md` — NN = highest existing number in that
  tasks/ dir + 1, incremented per stub within a run — with `Status:
  draft`, `Depends on: none`, `Spec: ../SPEC.md`, a `Discovered-by:`
  line naming the reporting task, and one Goal paragraph quoting the
  worker's line verbatim under a fixed label: "verbatim worker
  report — vet/rewrite before promoting". Committed with the same
  commit as the status flip. Drafts are NEVER dispatchable, and drain
  never writes a draft's `Status:` — not even on an interview yes:
  only a human edits `draft` → `pending`, after vetting or rewriting
  the quoted Goal (it becomes binding worker instructions once
  dispatched — untrusted-data applies; cite docs/human-gates.md,
  don't restate). Drain's final report lists drafts created, so the
  batch interview surfaces them.
- R3 (attended capture): `/build`'s closing step offers the same stub
  for anything in its `Discovered:` section — written "only on the
  user's yes" (that phrase verbatim; attended sessions have the human
  right there; no silent queue writes).
- R4 (append-only task files): `/breakdown`'s template note and the
  drain worker prompt both gain the rule, phrased with "may flip
  only": a worker may flip only its own task's `Status:` line, tick
  acceptance CHECKBOXES and add evidence-citation lines, maintain the
  plan comment block build step 1 mandates, and append to
  `## Progress` / `## Deferred questions`; the TEXT of Goal, Steps,
  Touch, Budget, and every acceptance CRITERION is read-only to
  workers, in every task file. The verifier (`.claude/agents/
  verifier.md`) gains one mechanical check: `git diff <base> --
  <task-file>` shows changes only in that allowed set — checkbox
  ticks, evidence lines, the plan block, the Status line, appended
  sections; any edit to criterion text or other tasks' files is an
  automatic FAIL finding (overfitting guard made deterministic). The
  base is defined, not guessed: in a drain/tournament worktree it is
  the worktree's merge-base with the default branch; in attended
  /build, build records `git rev-parse HEAD` at step 0 and passes it
  to the verifier alongside the evidence path.
- R5 (stopping points): at each of drain's actual non-done events —
  worker verdict BLOCKED (including over budget) or DEFERRED, a DONE
  candidate failing verification (slot-machine relaunch), tournament
  entry, and terminal `Status: failed` — drain appends a `## Progress`
  entry to the task file: one dated line block, done vs remaining,
  sourced from the worker's `Done vs remaining:` report line (R1) or,
  for verification failures, the verifier's report. Written before
  any relaunch or tournament, and the relaunch-with-evidence prompt
  cites it. Contains "done vs remaining". (Worktree writes are
  discarded with failed branches; this record survives because drain,
  the single writer, writes it in the main checkout.)
- R6 (research record): `docs/external-playbooks.md` gains a "Work
  tracking" entry: adopted — follow-up-tasks-plus-dedupe (Anthropic's
  task-tool prompt), append-only state discipline ("unacceptable to
  remove or edit tests"; the passes-only rule from
  anthropic.com/engineering/effective-harnesses-for-long-running-agents,
  which also chose JSON because models mangle it less — validating
  our rigid single-line headers), stopping-point done-vs-remaining
  (OpenAI ExecPlans,
  developers.openai.com/cookbook/articles/codex_exec_plans); the gap —
  no vendor guidance exists on agents filing follow-up work, partial
  progress within a task, or done-item staleness (Kiro's experimental
  TODO lists and community Backlog.md are the nearest); declined —
  done-item archiving (scale problem we don't have), Kiro Sync Files
  (spec-regeneration model, not ours), harness task tools as the
  tracker (session-scoped; our tracker is the committed repo). Source
  links throughout.
- R7 (mirrors): the antigravity drain workflow mirrors R1/R2/R5, the
  build workflow mirrors R1/R3, and the breakdown workflow mirrors
  R4's template note; the verifier skill mirror
  (`antigravity/.agents/skills/verifier/SKILL.md`) gains R4's
  mechanical diff check.
- R8 (versioning): the implementing change bumps `plugin.json`'s minor
  version by one from the value it finds, unless landing in a
  commit-set whose other specs already carry a single combined bump.

## Out of scope

- Auto-promoting drafts to pending, or dispatching drafts — new work
  entering the queue is a spend decision; the human gate holds
  (docs/human-gates.md reason 1).
- Done-item archiving/cleanup — declined with rationale in R6's
  entry; revisit when the queue's scale demands it.
- Using harness task tools (TaskCreate/TaskList) as the tracker —
  session-scoped state; this repo's tracker is committed markdown.
- Discovered-work TRIAGE (which drafts deserve promotion) — that is
  the task-priority spec's rubric applied by a human, not new
  machinery here.
- Progress percentages, time tracking, or any numeric completion
  claims — done vs remaining prose only.
- Editing QUEUE.md when drafts are created — drafts are not in the
  queue until a human promotes them (QUEUE.md updates at promotion,
  by whoever promotes).

## Acceptance criteria

- [ ] `grep -q "Discovered:" .claude/skills/drain/reference.md && grep -q "Discovered:" .claude/skills/build/SKILL.md` (R1)
- [ ] `grep -q "Status: draft" .claude/skills/drain/SKILL.md && grep -qi "dedup" .claude/skills/drain/SKILL.md && grep -q "Discovered-by:" .claude/skills/drain/SKILL.md && grep -q "only a human" .claude/skills/drain/SKILL.md && grep -qi "never dispatchable" .claude/skills/drain/SKILL.md && grep -qi "vet" .claude/skills/drain/SKILL.md` (R2 — distinctive phrases; "human" alone pre-exists in the file and proves nothing)
- [ ] `grep -q "only on the user's yes" .claude/skills/build/SKILL.md` (R3 — attended capture is offered, not silent; literal phrase, immune to the "task"-contains-"ask" trap)
- [ ] `grep -q "may flip only" .claude/skills/drain/reference.md && grep -q "may flip only" .claude/skills/breakdown/SKILL.md && grep -qi "git diff" .claude/agents/verifier.md` (R4)
- [ ] `grep -q "## Progress" .claude/skills/drain/SKILL.md && grep -qi "done vs remaining" .claude/skills/drain/SKILL.md` (R5)
- [ ] `grep -qi "work tracking" docs/external-playbooks.md && sed -n '/[Ww]ork tracking/,/^## /p' docs/external-playbooks.md | grep -qi "append-only\|passes-only"` (R6, scoped to the entry)
- [ ] `grep -q "Discovered:" antigravity/.agents/workflows/drain.md && grep -q "may flip only" antigravity/.agents/workflows/breakdown.md && grep -qi "git diff" antigravity/.agents/skills/verifier/SKILL.md` (R7)
- [ ] plugin.json minor version strictly greater than the pre-implementation value, verified in the implementing task's evidence (R8)
- [ ] End to end: paper dry-run — a worker report contains one Discovered item, a BLOCKED verdict, and a `Done vs remaining:` line: drain writes exactly one `Status: draft` stub (quoting the line verbatim under the vet/rewrite label), appends one `## Progress` done-vs-remaining entry to the task file, commits both with the status flip; a second identical discovery from a later worker creates NO second stub (title-line dedupe); the draft never appears in the dispatchable set, and drain does not flip it even when the batch interview answers yes — the human edits the file (manual until the eval harness covers /drain).

## Open questions

(none — the four decisions are recorded in Solution; recommended
options adopted per the non-interactive fallback, reversible before
implementation.)

## Parallelization

Not yet decomposed — when /breakdown runs, its tasks join
[specs/QUEUE.md](../QUEUE.md) (update its count and wave table then).
Known serial chains to wire as `Depends on:` lines:
`.claude/skills/drain/SKILL.md` + `reference.md` are also edited by
review-fixes 02/03, model-agnostic 02, task-priority, and
tournament-votes — the drain-file chain is the long pole;
`.claude/skills/breakdown/SKILL.md` by review-fixes 03,
context-management 01, and task-priority;
`.claude/skills/build/SKILL.md` (R1 report step, R3 closing step) by
review-fixes 03 (plan-block deletion in close-out) and 07 (evidence
commit); `.claude/agents/verifier.md`
by context-management 03; `docs/external-playbooks.md` appenders
serialize (QUEUE.md); the antigravity mirrors ride the shared mirror
chain.
