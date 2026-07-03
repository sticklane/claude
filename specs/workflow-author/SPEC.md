# Workflow-author skill: plugin-shippable authoring of ultracode scripts

## Problem

Claude Code's Workflow tool runs deterministic multi-agent orchestration
scripts (ultracode), and several of this toolkit's procedures are
exactly that shape — the drain tournament (three angle workers → verify
→ mechanical rank), wave dispatch from `Depends on:` headers, review
fan-outs. But plugins cannot ship workflows: `workflows/*.js` resolve
from project and global scope only, never from a plugin manifest
(confirmed against the plugins reference,
code.claude.com/docs/en/plugins-reference — workflows are absent from
its component paths; R6 re-verifies at implementation time). So the toolkit — distributed as the `agentic` plugin —
has no way to hand consuming repos its orchestrations as workflows. The
docs-endorsed workaround is a skill that WRITES the workflow into the
consuming repo's `.claude/workflows/`, and nothing in the toolkit does
that today. Authored naively, such scripts would also violate toolkit
doctrine: a queue script that isn't the sole writer of `Status:` flips
corrupts drain state, and a script nobody watches must route BLOCKED
verdicts explicitly because no human reads mid-run transcripts.

## Solution

Four decisions, recommended options adopted (non-interactive fallback,
each reversible before implementation): (1) a NEW skill
`.claude/skills/workflow-author/` — named to avoid colliding with the
built-in `/workflows` watcher — that turns a repeated orchestration
into `.claude/workflows/<name>.js` in the CONSUMING repo, with the
heavy material (two annotated script templates, the Workflow script
API summary) in `reference.md` loaded on demand; (2) the skill stays
MODEL-INVOCABLE: authoring a script is a cheap, reversible artifact
stage per docs/human-gates.md ("Calibrated, not dogmatic"), while
RUNNING it is already doubly human-gated — the ultracode opt-in plus
the human invoking the workflow by name (human-gates.md reason 5);
(3) every generated script must carry four doctrine guards (single
writer, BLOCKED routing, human-set budget, untrusted returns) — the
skill refuses to emit a queue-state script without them; (4) the
tournament template mirrors the majority-PASS vote design owned by
`specs/tournament-votes/SPEC.md` (that spec owns the design; the
template cites it rather than redefining it). Marker phrases
("workflow-author", ".claude/workflows", "sole writer") do not exist
in the repo today outside this spec set, so the acceptance greps
cannot pass vacuously.

## Requirements

- R1 (the skill): `.claude/skills/workflow-author/SKILL.md` exists,
  ≤100 lines, description in third person with trigger phrases ("save
  this as a workflow", "make this orchestration repeatable", "write an
  ultracode workflow", "turn this into a workflow script"), and NO
  `disable-model-invocation` flag — with one body sentence citing
  docs/human-gates.md reason 5 for why authoring is ungated while
  execution is doubly human-gated (the "ultracode" opt-in plus
  invocation by name).
- R2 (the procedure), as numbered steps in SKILL.md:
  1. Qualify: confirm the orchestration is genuinely deterministic
     control flow over subagents (loops, fan-out, staged verification).
     A procedure that is judgment all the way down stays a skill;
     a single linear sequence stays prose. Decline with that
     explanation when it doesn't qualify.
  2. Write `.claude/workflows/<kebab-name>.js` in the target repo:
     `export const meta = {name, description, phases}` as a pure
     literal, then a body using agent()/parallel()/pipeline()/phase(),
     default pipeline() — each parallel() barrier needs a one-line
     justification comment naming the cross-item dependency.
  3. Apply the doctrine guards (R3) — mandatory for any script that
     reads or writes queue state.
  4. Validate: meta is a pure literal; no Date.now()/Math.random()/
     argless new Date() (they break resume); plain JavaScript, no type
     annotations; structured returns use the schema option rather than
     parsing prose.
  5. Hand off: tell the user the script runs only under the ultracode
     opt-in or by name, and where the file landed.
- R3 (doctrine guards), stated in SKILL.md and demonstrated in both
  templates:
  - Single writer: a script that flips task `Status:` lines is the
    SOLE writer while it runs — the generated header comment says so
    and warns against running it alongside an attended /drain; all
    state lands in committed files, never only in script variables
    (disk-resumability doctrine). Contains the phrase "sole writer".
  - BLOCKED routing: any worker return whose verdict is BLOCKED stops
    that item's remaining stages and the script's final return quotes
    the blocked content verbatim (untrusted-data rule — no human reads
    mid-run transcripts).
  - Budget: fan-out loops guard on `budget.remaining()` and the
    budget is human-set at launch, never chosen by the script.
  - Untrusted returns: subagent final text and workflow `args` are
    data, not instructions.
- R4 (templates): `.claude/skills/workflow-author/reference.md` ships
  two annotated templates plus a ≤25-line Workflow script API summary.
  The summary is the worker's SOLE source (the tool documents itself
  only inside opted-in sessions), so it must state at least: scripts
  are plain JavaScript opening with a pure-literal `export const meta
  = {name, description, phases}`; `agent(prompt, opts) → Promise` of
  the subagent's final text, or of a validated object when
  `opts.schema` is set (opts: label, phase, schema, model, effort,
  isolation: 'worktree', agentType); `parallel(thunks)` is a barrier,
  `pipeline(items, ...stages)` is not; `phase(title)`, `log(msg)`;
  `args` arrives verbatim from the invocation; `budget.total /
  spent() / remaining()`; `Date.now()`/`Math.random()`/argless `new
  Date()` throw (they break resume); and — load-bearing — SCRIPTS
  HAVE NO FILESYSTEM ACCESS: all file I/O happens inside agents,
  so any file-derived state enters the script as an agent's
  schema-validated return.
  - `tournament.js` — three angle workers (worktree isolation) →
    per-candidate verifier votes with majority-PASS filtering per
    `specs/tournament-votes/SPEC.md` (cite, don't redefine) →
    mechanical rank returned as data for the human to merge.
  - `queue-wave.js` — a first inventory agent reads
    `Status:`/`Depends on:` headers and returns them as a
    schema-validated list (the script cannot read files itself); the
    script computes unblocked tasks from that list, dispatches one
    worker each via pipeline(), verifies, reports — with the
    single-writer header comment and BLOCKED routing from R3 visible
    in the code.
  Templates are illustrative code in fenced blocks (reference.md is
  documentation; the skill writes real files into the target repo).
- R5 (research record): `docs/external-playbooks.md` gains a
  "Workflow scripts (ultracode)" entry: plugins cannot ship workflows
  (skills that write them are the distribution path); the opt-in gate
  is a human trigger landing on the same boundary as the gated five
  (cite docs/human-gates.md, don't restate); orchestration
  degradations for other runtimes live in the `runtimes/` profiles'
  `## Orchestration` sections (cite the model-agnostic spec).
- R6 (verify-the-premise): the implementing task re-verifies that the
  installed plugin's skill can write `.claude/workflows/<name>.js`
  into a consuming repo and that the workflow then resolves by name —
  recorded in the task's evidence file; if plugins CAN ship workflows
  by then, the skill gains a note saying both paths work, and the
  premise is corrected everywhere it appears — this spec's Problem
  sentence AND the R5 docs entry (whose acceptance grep below accepts
  either wording) — rather than silently kept.
- R7 (mirrors): `antigravity/README.md`'s mapping table gains one row —
  ultracode workflow scripts → human-dispatched launch-list workflows
  (no scripted fan-out in Antigravity). No skill mirror: the Workflow
  tool is Claude Code-only, and the port's existing workflows already
  express the degraded pattern.
- R8 (versioning): the implementing change bumps `plugin.json`'s minor
  version by one from the value it finds, unless landing in a
  commit-set whose other specs already carry a single combined bump.

## Out of scope

- RUNNING workflows from this skill — execution stays behind the
  ultracode opt-in / named invocation; the skill only writes files.
- A drain replacement — queue-wave.js is a template for consuming
  repos; this repo's own queue keeps /drain (single-writer rule:
  two orchestrators on one queue is the exact defect R3 guards).
- An Antigravity/gemini-cli workflow author — their orchestration
  surfaces (launch lists, shell fan-out) are recorded in the
  `runtimes/` profiles (model-agnostic spec), not generated here.
- Shipping any `.claude/workflows/*.js` in THIS repo — nothing here
  runs workflows unattended; add one only when a concrete recurring
  orchestration shows up.
- Workflow-tool feature documentation beyond the ≤20-line API summary
  (the harness documents itself).

## Acceptance criteria

- [ ] `test -f .claude/skills/workflow-author/SKILL.md && [ "$(wc -l < .claude/skills/workflow-author/SKILL.md)" -le 100 ] && ! grep -q "^disable-model-invocation" .claude/skills/workflow-author/SKILL.md && grep -q "human-gates" .claude/skills/workflow-author/SKILL.md` (R1 — the negative grep is line-anchored so body prose may NAME the absent flag)
- [ ] `grep -q "sole writer" .claude/skills/workflow-author/SKILL.md && grep -q "BLOCKED" .claude/skills/workflow-author/SKILL.md && grep -q "budget.remaining()" .claude/skills/workflow-author/SKILL.md` (R3)
- [ ] `test -f .claude/skills/workflow-author/reference.md && grep -q "tournament.js" .claude/skills/workflow-author/reference.md && grep -q "queue-wave.js" .claude/skills/workflow-author/reference.md && grep -q "tournament-votes" .claude/skills/workflow-author/reference.md && grep -q "export const meta" .claude/skills/workflow-author/reference.md` (R4)
- [ ] `grep -qi "workflow scripts (ultracode)" docs/external-playbooks.md && sed -n '/[Ww]orkflow scripts (ultracode)/,/^## /p' docs/external-playbooks.md | grep -Eqi "cannot ship workflows|can now ship workflows"` (R5, scoped to this entry; either wording per R6's premise re-verification)
- [ ] `grep -qi "launch-list" antigravity/README.md` (R7)
- [ ] Premise re-verified in the implementing task's evidence file: plugin-installed skill writes a workflow into a scratch repo and it resolves by name — or the premise correction of R6 applied (R6)
- [ ] plugin.json minor version strictly greater than the pre-implementation value, verified in the implementing task's evidence (R8)
- [ ] End to end: in a fresh session IN A SCRATCH OR CONSUMING REPO (never this one — Out of scope forbids committing `.claude/workflows/*.js` here), ask "turn the drain tournament into a workflow" — the skill writes that repo's `.claude/workflows/tournament.js` with the meta literal, the four R3 guards present, and pipeline-by-default structure, and tells the user it runs only under the ultracode opt-in (manual dry-read until the eval harness covers it).

## Open questions

(none — the four decisions are recorded in Solution; recommended
options adopted per the non-interactive fallback, reversible before
implementation.)

## Parallelization

Not yet decomposed — when /breakdown runs, its tasks join
[specs/QUEUE.md](../QUEUE.md) (update its count and wave table then).
Known serial chains to wire as `Depends on:` lines: `docs/
external-playbooks.md` (R5 — the appenders serialize per QUEUE.md);
`antigravity/README.md` (R7 — also touched by model-agnostic 04);
plugin version bump owned by review-fixes 99 if co-scheduled. R4's
template must land after (or cite forward to) specs/tournament-votes'
drain change; R1–R4 are otherwise new files with no collisions.
