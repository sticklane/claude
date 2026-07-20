Status: open
Priority: P2
Breakdown-ready: true

## Problem

A live `/drain` run on this repo's own `specs/rigor-tier` (2026-07-16, no-arg
launch, W=1, 5 verdicts before the baton fired) was reviewed for why its hub
context grew as large as it did before the baton-pass trigger. Two concrete,
fixable anti-patterns were found in how the hub itself behaved — both are the
same shape as the sibling `context-blowout-subagent-guards` spec: a
documented safety practice already exists in this repo's own doctrine, but
isn't enforced procedurally at the point the hub actually acts, so it gets
skipped under the pressure of running a live dispatch loop.

**1. A reference doc marked "load only the named section" got a full
sequential read instead.** `.claude/skills/drain/reference.md` is 1744
lines and its own table of contents says "Loaded on demand... load only the
named section" (drain SKILL.md repeats this instruction at every section
pointer: "load only the named section"). Mid-run, the hub needed the Worker
prompt, Owner lease, and Spec-completion review sections and ran a bare
`Read` on the file from the top instead of `Grep`-locating each section
first — a single tool call that pulled in ~25,000 tokens (the harness's own
truncation cap; the file is larger) of unrelated content (Tournament,
HUMAN.md filing, etc.) that was never used. The doctrine already says what
to do; nothing forces the hub to actually do it.

**2. The Worker prompt template was hand-copied into every dispatch instead
of referenced by path.** reference.md's own "Worker prompt" section already
establishes the pattern of pointing a dispatched worker at a file instead of
inlining its content — the `<build-skill-path>` substitution tells the
worker "follow the build skill's procedure exactly, as written in
`<build-skill-path>`" rather than pasting the whole build SKILL.md into the
dispatch prompt. But the worker prompt's OWN ~700-word body (the defer
contract, the Contradicts-premise marker, the final-message shape, etc.) is
not treated the same way — SKILL.md step 2 has the hub paste that entire
template into every single `Agent` call. Across the rigor-tier run's 6
worker dispatches this reproduced near-identical boilerplate 6 times in the
hub's own turn output, which itself counts toward the hub's context (a
session's own prior turns are replayed on every subsequent turn same as
tool results).

## Non-goals

- **The isolation-worktree CLAUDE.md/rules re-injection is not something
  this spec attempts to eliminate.** Entering a fresh `git worktree` and
  then `Read`/`Edit`-ing a file under it causes the harness to treat that
  path as a new project root and reprint the full `CLAUDE.md` +
  `.claude/rules/*.md` stack, byte-identical to what the hub already
  carries for the main checkout. This is harness behavior tied to
  `isolation: worktree`, not something an in-repo doctrine change can route
  around. It is documented here (folded into task 03 below) purely so
  future sessions budget for it instead of being surprised by it.
- **The hub's own post-merge gate output (test tails, `git diff --stat`,
  etc.) staying in the hub's context is correct, not a bug.**
  reference.md's "Wake economics" section already carves this out
  explicitly: the merge-time re-read ban is EXEMPT for "the hub's OWN
  post-merge project-gate run (its pass/fail plus the bounded output tail
  specified for relaunch evidence)". Nothing to fix here.
- **The `prompt-improver` community plugin (severity1-marketplace, v0.6.1,
  user scope) is explicitly out of scope for this spec.** It was found to
  wrap every `UserPromptSubmit` event — including system-generated
  background-agent task-notifications, which are not prompts needing
  clarity evaluation — in up to five stacked nudge blocks, and its
  `improve` nudge duplicates the full original event text inside an
  `Original user request: "..."` wrapper. This roughly doubles the token
  cost of every background-agent verdict landing in any session on this
  machine, not just this repo's drain runs. It is a global, user-scope
  plugin outside this repo's version control (installed 2026-07-11,
  `~/.claude/plugins/cache/severity1-marketplace/prompt-improver/0.6.1`) —
  fixing, reconfiguring, or disabling it is a direct user action (`/plugin`
  management or hand-editing its `nudges/UserPromptSubmit/*.json` rules),
  not a task this repo's task queue can drain. Recorded here only so the
  finding isn't lost, and so nobody reopens it as an in-repo task by
  mistake.

## Solution

1. Turn reference.md's passive "loaded on demand... load only the named
   section" note into an enforced procedure at the two places SKILL.md
   sends the hub to reference.md mid-run: before any reference.md read,
   `Grep -n '^## '` the file for its section headers, find the target
   section's line range, then `Read` with `offset`/`limit` bounded to that
   range — never a bare sequential `Read` of the whole file. State this
   once, prominently, near reference.md's own table of contents (where
   "load only the named section" already lives) rather than at each of the
   ~15 call sites, and have SKILL.md's existing "load only the named
   section" pointers cite it.
2. Change the Worker prompt's delivery contract to match its own
   `<build-skill-path>` pattern: instead of the hub pasting the full
   template text into every `Agent` call, the dispatch prompt tells the
   worker to read reference.md's "Worker prompt" section itself (resolved
   to a concrete path the same way `<build-skill-path>` already is) and
   follow it verbatim, with only the genuinely task-specific pieces inlined
   directly in the dispatch call (task file path, branch name, budget,
   any task-specific `## Answers` notes). Update SKILL.md step 2's dispatch
   instructions and reference.md's Worker prompt intro to state this
   contract explicitly.
3. Add one documented line to reference.md's "Wake economics" section
   noting the isolation-worktree CLAUDE.md/rules re-injection cost (the
   Non-goals item above) as an accepted, budgeted-for tax on
   `isolation: worktree` dispatch — not a bug, not something to route
   around, just something a hub session should expect and not be surprised
   by when sizing its own context growth.

Per `.claude/rules/mirror-procedure-discipline.md`, items 1 and 2 change
drain's PROCEDURE (not incidental prose), so the equivalent behavioral
tightening carries into `antigravity/.agents/workflows/drain.md` (paraphrased
port, matching the behavior) and `codex/.agents/skills/drain/SKILL.md` (real
content) in the same task — the same three-file shape
`specs/rigor-tier/tasks/02-build-drain-gate-scaling.md` already used for a
`.claude/skills/drain/SKILL.md` change.

## Requirements

- **R1**: `.claude/skills/drain/reference.md`'s table of contents / opening
  note states the Grep-then-offset-Read procedure explicitly (not just "load
  only the named section" as a passive aside), and `.claude/skills/drain/SKILL.md`'s
  existing "load only the named section" pointers cite it rather than
  repeating it.
- **R2**: `.claude/skills/drain/reference.md`'s "Worker prompt" section states
  that the hub delivers it to a dispatched worker by path-pointer (resolved
  the same way `<build-skill-path>` already is), not by inlining the full
  template text into the dispatch prompt; `.claude/skills/drain/SKILL.md`
  step 2's dispatch instructions are updated to match.
- **R3**: `.claude/skills/drain/reference.md`'s "Wake economics" section
  documents the isolation-worktree CLAUDE.md/rules re-injection cost as an
  accepted, budgeted-for tax.
- **R4**: `antigravity/.agents/workflows/drain.md` and
  `codex/.agents/skills/drain/SKILL.md` carry the equivalent procedural
  tightening from R1 and R2 (R3 is a documentation-only note local to
  `.claude/`'s reference.md; port only if the antigravity/codex mirrors
  carry an equivalent wake-economics discussion already — do not invent one
  if they don't).

## Acceptance signals

- A fresh session executing `/drain` against a spec whose tasks require
  reading multiple reference.md sections issues `Grep`/offset-bounded
  `Read` calls, never a bare full-file `Read` of reference.md, observable
  in its own tool-call transcript.
- A fresh session's worker-dispatch `Agent` calls are short (task-specific
  substitutions only) and point at reference.md's Worker prompt section by
  path rather than reproducing its body text.
- `bash evals/lint-ultra-gate.sh` still exits 0 after the edits (passes
  today, verified 2026-07-19; drain is an ultra-path skill).
- `bash evals/lint-skill-size-gate.sh` exits 0 (the earlier pre-existing
  505-line `.claude/skills/drain/SKILL.md` overage this section originally
  cited was cleared by the `drain-orchestrator-run` merge landing
  2026-07-19 — the gate is a clean pass today at 495 lines; superseded
  note kept only as history). `wc -l < .claude/skills/drain/SKILL.md`
  stays ≤ 500 — this spec's edits must not grow the file back over budget.
- `tests/mirror-procedure-manifest.txt` gains new
  `<source>|<mirror>|<phrase>` entries seeding R1's section-bounded-read
  procedure and R2's Worker-prompt delivery contract into BOTH mirrors
  (`antigravity/.agents/workflows/drain.md` and
  `codex/.agents/skills/drain/SKILL.md` — one line per mirror, per the
  memory doc's multi-file rule), each seeded phrase also confirmed present
  in its `.claude/skills/drain/` source file (`grep -c` ≥ 1 — the test's
  skip rule silently passes a phrase the source lacks); then
  `tests/test_mirror_procedure_coverage.sh` still exits 0. The bare
  "still passes" check was vacuous — it exits 0 today with zero new work,
  verified 2026-07-19; the new manifest lines are what make it bite.
  Candidate anchors "Grep-then-offset" and "path-pointer" verified absent
  from all four drain files (0 matches each) 2026-07-19 — adjust during
  breakdown if wording changes, keeping the anchors in sync.

## Parallelization

Task 01 (R1+R2 core changes to reference.md/SKILL.md) lands first — tasks
02 and 03 both depend on it to avoid same-file edit collisions (02 reads
its landed diff to port; 03 shares reference.md as an edit target). Tasks
02 and 03 are disjoint in `Touch` (mirrors + manifest vs. reference.md's
Wake economics section) and free of shared undecided design, so they run
concurrently once 01 is done.

- Group: 02, 03

Next stage: /critique specs/drain-hub-context-discipline/SPEC.md
(human-launched, or self-chain if the live request explicitly asks for it).
