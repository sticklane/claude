# agentic-z7b.2 — is drain's count-based-baton wake-cost gap still real?

Date: 2026-07-25. Scope: step-1 answer plus the audit of every live
(non-`specs/archive/`) `drain-wake-cost` citation.

## Step-1 answer: the gap is structurally gone

No per-verdict orchestrator wake, baton, lease, or generation counter
survives in drain. Verbatim from `.claude/skills/drain/SKILL.md`:

> After the agentic-core-redesign cutover **bd is the source of truth** …
> There are no baton files, no lease files, no generation counters, and no
> drain-owned handoff files — the queue itself is the state, so drain is
> resumable by definition: `/clear` any time and re-run `/drain`; "where it
> stopped" is a `bd ready` query, not a parked file.
> — `.claude/skills/drain/SKILL.md` lines 8–14

> 4. **Loop.** Re-read `bd ready` after each collected verdict (rolling
> top-up, not a wave barrier) and keep the window full until the queue
> drains.
> — `.claude/skills/drain/SKILL.md` lines 95–96

`.claude/skills/drain/reference.md` carries only the worker prompt, the
skill-path recipe, the deferred-question format, the push guard, and the
HUMAN.md rule; grep for baton/lease/generation returns nothing in it.
`.claude/rules/token-discipline.md`'s Session refresh section agrees:

> Drain has no baton or generation-counter mechanism of its own to carve out
> here — it runs to `bd ready` exhaustion within a single session.

The archived spec's fix (a size-based baton trigger replacing a count-based
one, `specs/archive/drain-wake-cost/SPEC.md` Problem factor 2) therefore has
nothing left to replace. It is retired unimplemented, not deferred.

## Residual risk — real, and NOT closed by the pivot

Within one run the drain orchestrator still accumulates context across every
collected verdict (each capped at ≤2k tokens, but unbounded in count), so the
"fat orchestrator context" cost driver the archived spec measured survives
even though the wake pattern does not. Nothing in drain bounds it; the only
bound is the wake budget in `.claude/rules/token-discipline.md`'s Session
refresh section (250k main-session context, context-size arm). That section
now says so explicitly rather than leaving the reader to infer the cause was
fully eliminated.

## Live citation audit

`grep -rln 'drain-wake-cost' --include='*.md' .` returns 34 files; 25 are
inside `specs/archive/`. The 9 live ones:

| File | Verdict |
|---|---|
| `.claude/rules/token-discipline.md` (Delegation defaults, ~$1,406/week) | Accurate — cost history, correct `specs/archive/` path, no open-gap claim. |
| `.claude/rules/token-discipline.md` (Freehand fan-out, $0.067 vs $0.057) | Accurate — cost history, correct `specs/archive/` path. |
| `.claude/rules/token-discipline.md` (Session refresh) | Corrected by this task — now names the archived spec as history and records the residual accumulation. |
| `specs/drain-frontier-scanner/SPEC.md:17` | Accurate — cites `specs/archive/drain-wake-cost/EVIDENCE.md` for the 57%/$3.50 cost figures; measurement history, still valid. |
| `specs/agentprof-attribution-gaps/SPEC.md:54` | Accurate — "the drain-wake-cost precedent" for pinning a profile artifact in-repo; unrelated to the baton. |
| `specs/agentprof-attribution-gaps/EVIDENCE.md:62` | Content accurate (profile-pinning precedent); path stale (`specs/drain-wake-cost`, now under `specs/archive/`). |
| `specs/drain-worker-dispatch-hardening/SPEC.md:278` | Content accurate (prior-art list, "orchestrator wake economics"); path stale. |
| `specs/critique-findings-loop-closure/SPEC.md:147,279` | Content accurate in past tense (a 2026-07-13 incident where a queue exhausted the then-existing 10-generation cap); path stale, and a reader may not realize that cap no longer exists. |
| `specs/agentic-core-redesign/EVIDENCE.md:19,101` | Content accurate as history ("the baton trigger did not fire because the model never emitted it"); path stale. |
| `specs/orchestrator-share-audit/SPEC.md:112` and `tasks/02-apply-verdicts.md:30` | Misleading: both say the drain-wake-cost spec "owns" `.claude/skills/drain/*` / drain's hub cost, i.e. present an archived spec as a live owner. Path also stale. |

No live document claims drain currently HAS a count-based baton or a
generation counter — the mechanism claim the task worried about does not
exist anywhere live (`grep -rn 'count-based'` over the tree returns only
acceptance-criteria authoring text, unrelated to drain).

## What was changed, and what was deliberately not

Changed (inside this task's `Touch:` scope): the archived spec's
`Status: open` → `Status: superseded` plus a `## Supersession` section, and
the Session refresh paragraph in `.claude/rules/token-discipline.md`.
Six of the stale citations write the pre-archive path `specs/drain-wake-cost`,
which no longer resolves; a reader following them hits nothing and never
reaches the supersession header, so they must be redirected by a follow-up.
That follow-up is filed in bd.

Not changed: the six stale-path citations and the two owner-claim citations
listed above all live in specs outside this task's `Touch:` list. They are
reported as discovered work rather than edited here, and tracked by the bd
follow-up named above.
