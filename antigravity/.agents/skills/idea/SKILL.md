---
name: idea
description: Transforms a raw idea into an agent-ready spec. Interviews the user, scouts the codebase, and writes specs/<slug>/SPEC.md with runnable acceptance criteria. Use when the user pitches a feature, describes something they want built, or says "I have an idea" / "I want to add X".
---

Turn the user's idea into a spec precise enough that a fresh conversation
can implement and verify it without this one.

**Right-size first.** If the change is describable as a one-sentence diff
(typo, log line, rename, config tweak), say so and just do it. And if the
change is a mechanical transform a deterministic tool can perform (codemod,
bulk rename, formatting sweep), it gets a script, not a spec — write and run
the script instead. Continue only for work with real uncertainty or multiple
files.

## 1. Scout before you ask

Fan out 2-4 scout agents in parallel (one focused question each) to learn
what the idea touches: relevant modules, existing similar features, test
conventions, constraints. Keep conclusions (`path:line`), not file dumps.
Informed questions beat generic ones.

## 2. Interview the user

Ask in small numbered batches, waiting for answers. Cover, as relevant:

- Problem and user: who needs this, what breaks or annoys them today?
- Behavior: happy path, then edge cases (empty, error, concurrent, permission).
- Technical approach: integration points the scouting surfaced; where two
  designs are defensible, present options with your recommendation first.
  For features involving generative AI, ask which parts are code — which
  parts need model judgment and which are rules — defaulting per /design's
  ladder, and record the split in the spec's Solution.
- Scope: what is explicitly OUT. Push for at least one exclusion.
- Verification: what command, test, or observable behavior proves each
  requirement?

Keep interviewing until you could defend every design decision; don't pad
with questions whose answers you can infer or scouting already answered.

## 3. Write the spec

Create `specs/<kebab-slug>/SPEC.md`:

```markdown
# <Title>

## Problem

One paragraph. Who, what, why now.

## Solution

The approach in a few sentences, naming real files/interfaces from the
scout findings (path:line where useful).

## Requirements

Numbered. Each one testable — "R3: POST /api/x returns 422 when body lacks
`name`" not "handle errors gracefully".

## Out of scope

Explicit exclusions, so an agent doesn't wander into them.

## Acceptance criteria

Runnable checks, one per requirement where possible:

- [ ] `npm test -- x.test.ts` passes (covers R1–R3)
- [ ] `curl -s localhost:3000/api/x | jq .status` → "ok"
      End with one end-to-end check that exercises the feature as a user would.

## Open questions

Must be EMPTY before implementation starts.
```

**Anchor every grep/count-based acceptance criterion.** Apply the
anchored-acceptance-criteria check (doctrine in
`docs/memory/anchored-acceptance-criteria.md`, cited not restated) to each
grep- or count-based criterion the moment you draft it — before that
criterion is written into the SPEC.md above, never deferred to
`/breakdown`:

1. Run `grep -ci '<phrase>'` (or the equivalent count check) against the
   target file's CURRENT on-disk state, and confirm the criterion's expected
   result actually differs from today's — a criterion whose phrase is already
   present (or whose count already satisfies the bound) passes vacuously.
2. Reject and rewrite any criterion whose target phrase is itself an
   incidental byproduct of this same spec's own Requirements — the
   self-referential trap, where a worker satisfies the check by writing only
   the literal search string without implementing the requirement's actual
   behavior. The rewrite must depend on genuine implementation: an observable
   behavior, a runnable test, or a phrase tied to functional content.
3. Record the check's outcome inline next to the criterion in the SPEC.md
   draft, matching the memory file's convention — e.g. "phrase absent today,
   verified <date>".

## 4. Adversarial pass

Apply the critique workflow's procedure (`.agents/workflows/critique.md`) to
the spec, rather than the critic skill directly — the critique workflow is
what stamps the spec's `Breakdown-ready: true` header once it reaches READY,
the token step 5's hand-off and drain's auto-breakdown phase both rely on
(ideally in a fresh Agent Manager conversation for unbiased eyes). Fix what
it finds; repeat until READY. This costs ~1% of what implementing an
ambiguous spec costs.

## 5. Hand off

Tell the user: if the spec leaves a technology or architecture choice open,
run `/design specs/<slug>/SPEC.md` first; then `/breakdown
specs/<slug>/SPEC.md` for multi-session work, or `/build
specs/<slug>/SPEC.md` for single-session work — in a NEW conversation. The
spec is the handoff artifact; this conversation's context should not be
needed again.

## Ultra path

Antigravity has no Workflow tool and no runtime profile, so the ultra
scouting path is permanently closed here — the ordinary step-1 scouting
above is always the path. (For reference: in the Claude Code toolkit, an
opted-in ultracode run over a multi-repo idea replaces the ad-hoc scouts
with a four-scout multi-modal sweep — by-structure, by-convention,
by-history, by-dependency — plus a completeness critic before the
interview. That gate never opens in this mirror.)

`Next stage: /breakdown specs/<slug>/SPEC.md (human-launched)`.
