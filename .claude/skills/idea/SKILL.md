---
name: idea
description: Transforms a raw idea into an agent-ready spec. Interviews the user with AskUserQuestion, scouts the codebase with cheap subagents, and writes specs/<slug>/SPEC.md with runnable acceptance criteria. Use when the user pitches a feature, describes something they want built, or says "I have an idea" / "I want to add X".
argument-hint: "[one-line idea]"
---

Turn the idea in $ARGUMENTS (ask for it if empty) into a spec precise enough
that a fresh agent session can implement and verify it without you.

**Right-size first.** If the change is describable as a one-sentence diff
(typo, log line, rename, config tweak), say so and just do it — a spec
pipeline for a trivial change wastes more tokens than it saves. And if the
change is a mechanical transform a deterministic tool can perform (codemod,
bulk rename, formatting sweep), it gets a script, not a spec — write and run
the script instead. Continue only for work with real uncertainty or multiple
files.

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
  For features involving generative AI, ask which parts are code — which
  parts need model judgment and which are rules — defaulting per /design's
  ladder, and record the split in the spec's Solution.
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

Invoke the `/critique` skill on the spec file (via the Skill tool) rather than
spawning the critic agent directly — `/critique` is what stamps the spec's
`Breakdown-ready: true` header once it reaches READY, the token step 5's
self-chain and `/drain`'s auto-breakdown phase both rely on. Fix what it
finds; re-invoke until READY. This costs ~1% of what implementing an
ambiguous spec costs.

## 5. Hand off

After READY, chain: announce it in one line, then invoke `/breakdown` on the
spec via the Skill tool, per the self-chain bullet in CLAUDE.md's authoring
conventions. Chaining into /breakdown in-session is the sanctioned exception
to the fresh-session hand-off — it is a light artifact stage that works from
the spec file, not from this conversation's context.

Fall back to the printed pointer when the self-chain conditions fail — the
user asked for the spec only, non-interactive doubt (answers you had to
infer rather than get), or a technology/architecture choice is still open
(run `/design specs/<slug>/SPEC.md` first; open /design choices stop the
chain). The fallback keeps the `/clear`-first advice: tell the user to run
`/breakdown specs/<slug>/SPEC.md` (or `/build specs/<slug>/SPEC.md` for
single-session work) in a FRESH session — the spec is the handoff artifact.

Close with:
`Next stage: /breakdown specs/<slug>/SPEC.md (self-chains per conventions)`
— or, on the /design fallback,
`Next stage: /design specs/<slug>/SPEC.md (human-launched)`.

## Ultra path

When the active runtime profile documents an orchestration section AND
ultracode is opted in AND the idea spans multiple repos or subsystems, step 1
runs as a workflow instead of the 2–4 ad-hoc scouts; with the profile silent,
or for a single-subsystem idea, step 1 above is the only path. The profile
holds the template — this skill only names the shape.

The sweep fans out four scouts in parallel — by-structure, by-convention,
by-history, by-dependency — followed by a completeness critic that flags gaps
before the interview begins. Effort-tier language caps each scout's calls. The
interview, spec-write, and adversarial pass are unchanged.
