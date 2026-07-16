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

## 2. Ground the idea in fresh research

When the idea's framing signals a need for external grounding, first check
`docs/` for a topically-matching `Verified:` stamp within a 90-day freshness
window before dispatching any research agents. Trigger patterns are
illustrative, not exhaustive: phrases like "best practices," "how do
[vendor/tool] do this," "research X," or "backed by research/blogs from ..."

Run `.claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh`
against `docs/` — it (or equivalent logic) decides the fresh/stale/absent
branching:

- **Fresh match** — a `Verified:` stamp within the 90-day window on a
  topically-matching doc section: cite it directly as `docs/<path>:<line>`
  and dispatch no research agents.
- **Stale or absent match**: dispatch research the existing way — factcheck
  vs. deep-research per `.claude/rules/token-discipline.md`'s routing — then
  write or refresh the `Verified: <today>` stamp on the doc section the
  findings land in.

If the framing signals no need for external grounding, skip this step and
proceed to the interview.

## 3. Interview the user

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
- Rigor: prototype or production? Offer this as one AskUserQuestion option set —
  prototype-grade work legitimately skips verification that production-grade
  work must pay for, and the failure mode is not declaring a point on that
  spectrum. On "prototype", step 4 writes a `Rigor: prototype` header; on
  "production" or no answer, write nothing (absent means production).

Keep interviewing until you could defend every design decision; don't pad
with questions whose answers you can infer or scouts already answered.

## 4. Write the spec

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

**Write the `Rigor:` header when prototype was chosen.** If the interview's
prototype-vs-production question answered prototype, write `Rigor: prototype`
as a single-line header above the SPEC.md's first `##` heading — the same
placement convention as `Priority:`. On production or no answer, write nothing:
absent means production (the only legal values are `prototype` and
`production`).

**Anchor every grep/count-based acceptance criterion.** Apply the
anchored-acceptance-criteria check (doctrine in
`docs/memory/anchored-acceptance-criteria.md`, cited not restated) to each
grep- or count-based criterion the moment you draft it — immediately, before
that criterion is written into the SPEC.md above, never deferred to
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

## 5. Resolve open technology/architecture choices

Run this check immediately after writing the spec (step 4), before the first
`/critique` invocation — and re-run the _identical_ check after every
`/critique` fix wave inside step 6's loop, not only once here. It is one file
check re-evaluated at both points, never a separate judgment over critic
findings: **does the spec's `## Open questions` section name a technology or
architecture choice?** A fix wave that adds such an entry to `## Open
questions` is caught by this same re-run — that is what interrupts the loop,
rather than waiting for a READY the critique pass cannot reach by editing
prose.

If `## Open questions` names a technology/architecture choice, self-chain into
`/design` — the same synchronous, in-session Skill-tool mechanism step 7 uses
for `/breakdown`, never `run_in_background` or a detached Agent dispatch:

1. Announce it in one line — "`/design` needed for <the open choice>, chaining
   now" — then invoke the Skill tool for `design` with argument
   `specs/<slug>/SPEC.md`, blocking until it returns.
2. `/design` records its decision directly into the SPEC.md and prints its own
   closing `Next stage: /breakdown ... (human-launched)` line. **Ignore that
   line** — it is written for design's own human-launched entry point, not
   this flow. When control returns, resume step 6: proceed to `/critique` if
   this was the post-step-4 check, or continue the fix loop (without restarting
   from step 4) if this was a mid-loop re-check.
3. **Once per session.** This self-chain fires at most once per `/idea`
   session, whether triggered by the post-step-4 check or a mid-loop re-check.
   If `/design` has already run once this session and `## Open questions` names
   a technology/architecture choice again (a genuinely new one, or the same one
   design could not resolve), do NOT invoke `/design` a second time — take the
   printed-pointer fallback below.
4. **Design left the choice open.** If `/design` returns with `## Open
questions` still non-empty, take the printed-pointer fallback instead of
   proceeding — for the post-step-4 check, do not proceed to the first
   `/critique` invocation; for a mid-loop re-check, abort the fix loop rather
   than continuing it (an unresolved `## Open questions` entry already means
   `/breakdown` would refuse the spec).

The printed-pointer fallback here is step 7's fallback — the same one used when
the user asked for the spec only — stopping the chain and handing the spec to
the user to pick up in a fresh session.

If `## Open questions` names no technology/architecture choice, do nothing here
and proceed to step 6.

## 6. Adversarial pass

Invoke the `/critique` skill on the spec file (via the Skill tool) rather than
spawning the critic agent directly — `/critique` is what stamps the spec's
`Breakdown-ready: true` header once it reaches READY, the token step 7's
self-chain and `/drain`'s auto-breakdown phase both rely on. Fix what it
finds; re-invoke until READY. After each fix wave, re-run step 5's `## Open
questions` design check before re-invoking `/critique` — a fix that introduced
an open technology/architecture choice self-chains into `/design` (once per
session) per that step. This costs ~1% of what implementing an ambiguous spec
costs.

## 7. Hand off

After READY, chain: announce it in one line, then invoke `/breakdown` on the
spec via the Skill tool, per the self-chain bullet in CLAUDE.md's authoring
conventions. Chaining into /breakdown in-session is the sanctioned exception
to the fresh-session hand-off — it is a light artifact stage that works from
the spec file, not from this conversation's context.

Fall back to the printed pointer when the self-chain conditions fail — the
user asked for the spec only, or non-interactive doubt (answers you had to
infer rather than get). The fallback keeps the `/clear`-first advice: tell the
user to run `/breakdown specs/<slug>/SPEC.md` (or `/build specs/<slug>/SPEC.md`
for single-session work) in a FRESH session — the spec is the handoff artifact.

Close with:
`Next stage: /breakdown specs/<slug>/SPEC.md (self-chains per conventions)`.

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
