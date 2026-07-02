---
name: idea
description: Transforms a raw idea into an agent-ready spec. Interviews the user with AskUserQuestion, scouts the codebase with cheap subagents, and writes specs/<slug>/SPEC.md with runnable acceptance criteria. Use when the user pitches a feature, describes something they want built, or says "I have an idea" / "I want to add X".
argument-hint: "[one-line idea]"
---

Turn the idea in $ARGUMENTS (ask for it if empty) into a spec precise enough
that a fresh agent session can implement and verify it without you.

**Right-size first.** If the change is describable as a one-sentence diff
(typo, log line, rename, config tweak), say so and just do it — a spec
pipeline for a trivial change wastes more tokens than it saves. Continue only
for work with real uncertainty or multiple files.

## 1. Scout before you ask

Fan out 2–4 `scout` agents in parallel (one focused question each) to learn
what the idea touches: relevant modules, existing similar features, test
conventions, constraints. Do NOT read files into this session — you need
their conclusions, not their contents. Informed questions beat generic ones.

## 2. Interview the user

Use AskUserQuestion in small batches (if the session is non-interactive, ask
in plain prose — or stop and say the interview needs an interactive session
rather than inventing answers). Cover, as relevant:

- Problem and user: who needs this, what breaks or annoys them today?
- Behavior: happy path, then edge cases (empty, error, concurrent, permission).
- Technical approach: integration points the scouts surfaced; tradeoffs where
  two designs are defensible — present options with your recommendation first.
- Scope: what is explicitly OUT. Push for at least one exclusion.
- Verification: how will we know it works — what command, test, or observable
  behavior proves each requirement?

Keep interviewing until you could defend every design decision; don't pad
with questions whose answers you can infer or scouts already answered.

## 3. Write the spec

Create `specs/<kebab-slug>/SPEC.md`:

```markdown
# <Title>

## Problem
One paragraph. Who, what, why now.

## Solution
The approach in a few sentences, naming real files/interfaces from the scout
reports (path:line where useful).

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

Spawn the `critic` agent on the spec file. Fix what it finds; repeat until it
returns READY. This costs ~1% of what implementing an ambiguous spec costs.

## 5. Hand off

Tell the user: if the spec leaves a technology or architecture choice open,
run `/design specs/<slug>/SPEC.md` first; then `/breakdown
specs/<slug>/SPEC.md` for multi-session work, or `/build
specs/<slug>/SPEC.md` for single-session work — in a FRESH session
(`/clear` first). The spec is the handoff artifact; this
conversation's context should not be needed again.
