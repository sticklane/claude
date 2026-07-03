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

Apply the scout skill to learn what the idea touches: relevant modules,
existing similar features, test conventions, constraints. Keep conclusions
(`path:line`), not file dumps. Informed questions beat generic ones.

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

## 4. Adversarial pass

Apply the critic skill to the spec (ideally in a fresh Agent Manager
conversation for unbiased eyes). Fix what it finds; repeat until READY.
This costs ~1% of what implementing an ambiguous spec costs.

## 5. Hand off

Tell the user: if the spec leaves a technology or architecture choice open,
run `/design specs/<slug>/SPEC.md` first; then `/breakdown
specs/<slug>/SPEC.md` for multi-session work, or `/build
specs/<slug>/SPEC.md` for single-session work — in a NEW conversation. The
spec is the handoff artifact; this conversation's context should not be
needed again.
