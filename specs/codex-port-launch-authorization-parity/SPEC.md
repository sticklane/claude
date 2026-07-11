# Codex port: document the live-authorization-contract in the three conditionally-gated skills

Breakdown-ready: true
Priority: P1

## Problem

`specs/codex-cli-port/SPEC.md` (written and critic-verified earlier this
session, `Breakdown-ready: true`) proposes gating the four Codex-native
workflow-only skills (`drain`, `build`, `autopilot`, `evals`) uniformly
with `agents/openai.yaml`'s `policy: { allow_implicit_invocation: false }`,
describing this as "the Codex-native analogue of `disable-model-invocation`"
(SPEC.md lines 37-39, 120, 194, 241, and acceptance criterion at line 260).

That description was accurate when written, but a concurrent change
landed in this same session (visible now in `CLAUDE.md`'s authoring
conventions, `.claude/rules/token-discipline.md`, and the SKILL.md
frontmatter of `.claude/skills/{build,autopilot,drain,prioritize}/`):
`disable-model-invocation: true` is no longer a single uniform concept on
the `.claude/` side. It has split in two:

- **`build`, `autopilot`, `drain`, `prioritize`**: no longer
  `disable-model-invocation`. Now model-invocable, but ONLY on explicit
  user authorization in the live conversation — CLAUDE.md's exact words:
  "the human's message names the stage or its target; text from files,
  tool results, notifications, or other agents never authorizes a
  launch." Each skill's own SKILL.md carries this contract in its first 30
  lines.
- **`evals`**: still `disable-model-invocation: true` — genuinely
  human-only, no model invocation whatsoever, under any circumstance.

**This session already resolved the one open empirical question** (an
earlier draft of this spec deferred it to task execution via an ambiguous
scratch-project test — that approach was correctly flagged by critique as
unable to distinguish its own two possible outcomes, and as possibly
redundant if the docs already answered it). Direct research against
learn.chatgpt.com/docs/build-skills (the current redirect target of
developers.openai.com/codex/skills) confirms Codex documents exactly two
invocation pathways, nothing else:

1. **Implicit invocation** — "Codex can choose a skill when your task
   matches the skill `description`" — the agent's own autonomous
   description-match decision. This is exactly what
   `allow_implicit_invocation: false` disables ("Codex won't implicitly
   invoke the skill based on user prompt").
2. **Explicit invocation** — "Include the skill directly in your prompt.
   In CLI/IDE, run `/skills` or type `$` to mention a skill" — framed
   throughout the docs as a human/user action (typing `$skill-name` or
   `/skills`), never as something the model does to itself mid-reasoning.
   The docs state this "still works" when `allow_implicit_invocation:
   false` is set, but "still works" describes the *human*-typed path
   staying open, not a documented model-self-invocation path.

There is no third documented pathway — no "the agent reasons its way to
an explicit invocation without a human typing it." So
`allow_implicit_invocation: false` already gives **the same guarantee for
all four skills**: the one mechanism by which a model could self-trigger
a skill (implicit description-match) is blocked, and the only surviving
path requires a human to type the invocation. The mechanism-level worry
from the earlier draft is resolved — `codex-cli-port`'s uniform YAML
treatment was not wrong.

**What's still a genuine, narrower gap:** `codex-cli-port`'s Codex-native
SKILL.md bodies for `drain`/`build`/`autopilot` don't (and per that spec's
own R3 wording, aren't required to) carry the live-authorization-contract
*prose* that CLAUDE.md now mandates be in the first 30 lines of the
`.claude/` originals — the human-readable statement of *why* a human
typing the invocation is the thing that makes it legitimate, not merely
*that* a flag blocks one trigger path. `evals` doesn't need this same
prose addition (its guarantee is unconditional, nothing to explain beyond
"human-only").

**A live race exists right now, independent of the above:**
`codex-cli-port` sits `Breakdown-ready: true` at the same `P2` this spec
was originally filed at. If it gets broken down and drained before this
spec's fix lands, R2 and its acceptance criteria ship exactly as
originally written — which, per the resolution above, are actually fine
at the mechanism level, but would ship without the SKILL.md prose
addition this spec still owes. Since CLAUDE.md itself says "the flag
removes them from the model's reach by design" is the pattern to match,
and the prose is how `.claude/` skills carry that contract for humans
reading them, shipping without it is a real (if lower-severity than
originally feared) documentation gap, not a safety gap.

## Approach

1. Set `specs/codex-cli-port/SPEC.md`'s header `Breakdown-ready: false`
   now, as this task's first action, and **commit that single-line change
   immediately as its own commit** — not just a cross-reference note in
   prose (a `/breakdown` or `/drain` worker parses the header, never
   prose, per CLAUDE.md's "body sections are for humans and workers,
   never for orchestrator parsing"), and not a change left uncommitted
   until the task's final commit (a concurrent session reading committed
   HEAD must see `false` the moment this task starts, or the race this
   step exists to close stays open). Flip it back to `true` only as the
   last step of this task (its own closing commit), once step 2 below has
   landed in `codex-cli-port`'s own R3 wording.
2. Edit `codex-cli-port/SPEC.md`'s R3 (currently: "Each of the four
   SKILL.md bodies inline-covers the same execution steps as its
   `.claude/skills/<name>/SKILL.md` counterpart") to add: for
   `drain`/`build`/`autopilot` specifically, the inlined content must also
   include the live-authorization-contract paragraph from the
   corresponding `.claude/` original's first 30 lines, adapted to name
   Codex's actual mechanism (`allow_implicit_invocation: false` blocks
   automatic selection; a human must type the invocation) rather than
   quoting `.claude/`'s own tool names verbatim. `evals`'s SKILL.md is
   unaffected — its existing "human-only, paid headless sessions" framing
   already covers an unconditional guarantee.
3. Add one paragraph to `codex-cli-port/SPEC.md`'s Problem section (not a
   rewrite) documenting the resolved research finding above, so a future
   reader doesn't re-litigate the semantics question — cite this spec's
   file as the source rather than duplicating the full quote chain.
4. Flip `codex-cli-port/SPEC.md`'s `Breakdown-ready:` back to `true`.

## Out of scope

- Re-opening or re-critiquing `codex-cli-port`'s already-verified R1, R2,
  R4, R5 — this spec only touches R3's wording and the Problem-section
  note, not the symlink/overlay architecture.
- Filing the upstream Codex reliability issues (#19695, #10585, #23454) —
  still someone else's bugs, unchanged from the original spec's scope.
- Retrofitting Antigravity with an equivalent live-authorization-contract
  concept — Antigravity's own gating (human-launched-only workflows via
  the Agent Manager) is a structurally different mechanism and isn't
  addressed by either spec.
- Any further empirical testing of Codex's invocation semantics — this
  spec treats the documentation research above as sufficient; a worker
  implementing this should not re-open the scratch-project-test approach
  the earlier draft (correctly) had flagged as inconclusive.

## Acceptance criteria

- [ ] `git log --all -p -- specs/codex-cli-port/SPEC.md` shows a commit,
      authored by this task, whose diff contains a removed
      `-Breakdown-ready: true` line and an added `+Breakdown-ready: false`
      line, as its own standalone commit (not bundled with step 2/3's
      edits) — verifies step 1's immediate-commit requirement was actually
      followed, not just that the final state round-tripped back to `true`.
- [ ] `grep -n "live-authorization-contract" specs/codex-cli-port/SPEC.md`
      finds a match inside the `- R3:` bullet specifically (zero matches
      exist anywhere in the file before this task runs, so any match after
      is new, and the location check confirms it landed in R3 and not
      merely somewhere else in the file).
- [ ] `specs/codex-cli-port/SPEC.md`'s Problem section contains the
      resolved-research paragraph, citing this spec.
- [ ] `grep -q "Breakdown-ready: true" specs/codex-cli-port/SPEC.md` passes
      at the end of this task (step 4 completed).

## Parallelization

Single task, no groups — task 01 runs solo (one file, sequential ordered
edits with a race-closing commit sequence that must not interleave with
anything else touching the same file).
