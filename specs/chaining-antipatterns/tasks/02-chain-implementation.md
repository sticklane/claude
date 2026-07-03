# Task 02: Chain implementation — idea→breakdown self-chain and Next-stage lines

Status: pending
Depends on: 01
Budget: 40 turns
Spec: ../SPEC.md (requirements R2, R3)

## Goal

/idea actually chains: after critic READY it announces and invokes
/breakdown via the Skill tool (falling back to the printed pointer when
R1's conditions fail), /breakdown ends with a printed pointer because its
successors are launch-gated, and every artifact-producing skill closes
with a `Next stage:` line per the extended CLAUDE.md convention —
including the terminal none-form for distill and handoff.

## Touch

- `CLAUDE.md` (artifact-location convention extension only — the
  `Next stage:` closing-line rule per R3). Cross-spec: also edited by
  context-management, model-agnostic — see specs/QUEUE.md; also edited
  by task 01 in this spec (hence the dependency)
- `.claude/skills/idea/SKILL.md` (step 5 + fresh-session hand-off
  sentence). Cross-spec: also edited by code-vs-llm — see specs/QUEUE.md
- `.claude/skills/breakdown/SKILL.md` (hand-off sentence + `Next stage:`
  line only). Cross-spec: also edited by context-management,
  review-fixes — see specs/QUEUE.md
- `.claude/skills/design/SKILL.md`, `.claude/skills/gate/SKILL.md`,
  `.claude/skills/onboard/SKILL.md`, `.claude/skills/distill/SKILL.md`,
  `.claude/skills/handoff/SKILL.md`, `.claude/skills/evals/SKILL.md`
  (`Next stage:` closing lines only)

Must NOT touch: any skill's frontmatter description (R8's routing change
is task 03, critique only); `.claude/rules/`; antigravity files
(chaining is deliberately NOT ported — task 03 documents the divergence).

## Steps

1. Extend the artifact-location convention in CLAUDE.md per R3: the
   closing line of an artifact-producing skill is a `Next stage:` line
   naming the next skill and the artifact path, marked either
   "(self-chains per conventions)" or "(human-launched)"; terminal
   skills write `Next stage: none — <user action>`.
2. Rewrite `.claude/skills/idea/SKILL.md` step 5 from pointer-only to
   the "Next stage:" contract: after READY, announce in one line and
   invoke `/breakdown` on the spec via the Skill tool per R1's CLAUDE.md
   bullet (cite it, don't restate); fall back to today's printed pointer
   when conditions fail — spec-only request, non-interactive doubt, or
   /design needed first (open /design choices stop the chain).
3. Rewrite /idea's fresh-session hand-off sentence so the chain path is
   exempt (chaining into /breakdown in-session is the sanctioned
   exception for light artifact stages) while the fallback pointer keeps
   the `/clear`-first advice.
4. Add one sentence to `.claude/skills/breakdown/SKILL.md`'s hand-off:
   its next stages are launch-gated ("launch-gated" or "human-launched"
   verbatim), so it always ends with the printed pointer, citing R1's
   CLAUDE.md bullet rather than restating it.
5. Add `Next stage:` closing lines to all eight artifact skills (idea,
   design, breakdown, gate, onboard, distill, handoff, evals), each
   marked self-chains/human-launched; terminal none-forms: distill —
   "none — lessons land in CLAUDE.md/rules"; handoff — "none — /clear
   and resume from the handoff file". Invent no stage to satisfy the
   format.
6. R11 note: do NOT bump plugin.json — owned by specs/review-fixes
   global task 99; record the pre-implementation version in evidence.

## Acceptance

- [ ] `grep -q "Next stage:" .claude/skills/idea/SKILL.md && grep -qi "Skill tool" .claude/skills/idea/SKILL.md` (R2, from SPEC)
- [ ] `grep -qi "launch-gated\|human-launched" .claude/skills/breakdown/SKILL.md` (R2, from SPEC)
- [ ] `for f in idea design breakdown gate onboard distill handoff evals; do grep -q 'Next stage:' .claude/skills/$f/SKILL.md || exit 1; done` (R3, from SPEC, enumerated)
- [ ] Manual (from SPEC, end-to-end): in a fresh session, run /idea on a
      small toy feature and answer its interview; after the critic
      returns READY, the session announces and invokes /breakdown
      without a human typing it, task files appear under the spec's
      directory, and the session STOPS with printed pointers to the
      gated stages (manual until the eval harness covers /idea).
