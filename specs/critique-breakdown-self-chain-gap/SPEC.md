# critique doesn't self-chain into breakdown on a READY verdict

Priority: P2

Status: obsolete
Subsumed: recorded in specs/agentic-core-redesign/TRIAGE.md — delivered by the agentic redesign

## Problem

A live session ran `/critique` against three `SPEC.md` files, got READY on
all three (each marked `Breakdown-ready: true`), and then stopped to ask
the human for permission before running `/breakdown`:

> All three are Status: open, Breakdown-ready: true, sitting in specs/.
> Next step per this repo's pipeline is /breakdown on each, but that's an
> execution-adjacent stage I won't launch without you naming it
> explicitly — let me know if you want any of them broken down and
> drained now, or if you'd like to review the SPEC.md files first.

This is wrong per this repo's own doctrine. Root `CLAUDE.md`'s "Authoring
conventions" section gates only `/build`, `/drain`, and `/prioritize` on
explicit live-user authorization; `/breakdown` is not in that list and is
model-invocable. The same section's self-chain rule says a skill may
invoke the next pipeline stage via the Skill tool once (a) the artifact
passed its adversarial gate (critic READY — satisfied here), (b) the
target is model-invocable (`/breakdown` qualifies — it's not `/evals` and
not a gated execution stage), and (c) the user hasn't scoped the request
to the current stage. `docs/human-gates.md` confirms the same list and
adds "everything else in the pipeline is model-invocable, and light
artifact stages may self-chain." Nothing documents `/breakdown` as
"execution-adjacent" — that phrase does not appear anywhere in `.claude/`
or `docs/`; the session invented the gate.

The root cause is a gap in `.claude/skills/critique/SKILL.md`. Step 3
(around line 36-39) writes the `Breakdown-ready: true` marker on READY and
describes it only as "the token `/drain` reads to auto-invoke
`/breakdown` on specs with no `tasks/` yet" — i.e. it documents drain's
3b auto-breakdown consumer of the marker, but never instructs critique
itself to self-chain into `/breakdown` when all three self-chain
conditions are already met in the same turn. `critique/SKILL.md` also
never closes with the `Next stage:` line CLAUDE.md's authoring
conventions require every artifact-producing skill to end with ("Every
skill that produces an artifact must say where the file goes and what the
next pipeline step is, and closes with a `Next stage:` line naming the
next skill and the artifact path, marked '(self-chains per conventions)'
or '(human-launched)'"). Left silent on both points, a session facing a
READY verdict has nothing telling it self-chaining is not only allowed
but expected, and falls back to an overly conservative gate that doesn't
exist in the doctrine it's supposed to be following.

## Solution

Close the gap in `.claude/skills/critique/SKILL.md`:

1. In step 3, immediately after writing `Breakdown-ready: true` on a
   READY verdict for a `SPEC.md` target, add the self-chain instruction:
   when the user's live request for this `/critique` invocation did not
   scope the ask to critique alone (condition (c) of CLAUDE.md's
   self-chain rule), invoke `/breakdown` on the just-critiqued spec via
   the Skill tool, announcing the invocation in one line first, per
   CLAUDE.md's "Skills may self-chain" bullet (cited, not restated). This
   applies per-spec: a run that critiques multiple specs self-chains
   breakdown independently for each one that comes back READY, not only
   when every target in the batch is READY.
2. Add the closing `Next stage:` line CLAUDE.md's format requires,
   pointing at `/breakdown` for a READY `SPEC.md` target (marked
   "(self-chains per conventions)" per point 1) and stating the terminal
   case for a NOT READY verdict or a non-`SPEC.md` target (plan/diff)
   explicitly, since those never produce a `Breakdown-ready` marker and
   have no next stage to name.
3. Correct the existing step-3 sentence so it no longer reads as though
   drain is the marker's only consumer — state plainly that critique
   itself acts on the marker first (self-chain), and that drain's 3b
   auto-breakdown remains the fallback for a spec that reaches the queue
   with `Breakdown-ready: true` already set from an earlier, separate
   critique run (e.g. one where condition (c) held and self-chaining was
   correctly skipped).

## Out of scope

- Any change to `.claude/skills/breakdown/SKILL.md` itself — it already
  has no incorrect gating language (confirmed: it is silent on
  authorization, which is correct for a model-invocable stage).
- Any change to the gated-stage list (`/build`, `/drain`, `/prioritize`)
  in `CLAUDE.md` or `docs/human-gates.md` — both already state the
  correct list; this spec fixes critique's failure to act on doctrine
  that already exists, not the doctrine itself.
- Retrofitting the same self-chain + `Next stage:` fix onto the
  `antigravity/` and `codex/` mirrors of critique — do it if the task
  author scopes it in, per this repo's usual mirror-parity convention,
  but the bug report and root cause here are `.claude/`-only.

## Acceptance criteria

- [ ] `grep -n "self-chain" .claude/skills/critique/SKILL.md | grep -qi breakdown` — critique's SKILL.md now explicitly instructs self-chaining into `/breakdown` on a READY `SPEC.md` verdict.
- [ ] `tail -5 .claude/skills/critique/SKILL.md | grep -q "^Next stage:"` — critique's SKILL.md closes with the required `Next stage:` line.
- [ ] `grep -c "execution-adjacent" .claude/skills/critique/SKILL.md` → 0 both before and after (confirms the fix doesn't introduce the same wrong phrasing it's correcting).
- [ ] A fresh read of updated `.claude/skills/critique/SKILL.md` step 3, done by an agent with no memory of this spec, correctly identifies that a READY `SPEC.md` verdict should self-chain into `/breakdown` in the same turn (manual/agent-verified — no single grep can prove comprehension, only presence of the instruction).
