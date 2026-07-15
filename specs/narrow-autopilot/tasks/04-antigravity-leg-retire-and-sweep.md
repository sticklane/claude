# Task 04: Retire antigravity's autopilot workflow, fold into build.md, sweep doctrine mentions

Status: in-progress
Depends on: 01
Priority: P1
Budget: 6 turns
Spec: ../SPEC.md (requirements R7, R6 antigravity portion)
Touch: antigravity/.agents/workflows/autopilot.md, antigravity/.agents/workflows/build.md, antigravity/README.md, antigravity/.agents/skills/gate/SKILL.md, antigravity/.agents/skills/resume-handoff/SKILL.md, antigravity/.agents/workflows/drain.md, antigravity/.agents/skills/qa-sweep/SKILL.md

## Goal

`antigravity/.agents/workflows/autopilot.md` no longer exists; its
classification-gate and escalation-trigger content — only what actually
applies under antigravity's own human-gate model (per
`antigravity/README.md`'s gotchas) — is folded into
`antigravity/.agents/workflows/build.md`, mirroring Task 01's `.claude`-leg
treatment. Every other antigravity file referencing `/autopilot` is
updated the same way its `.claude`-leg counterpart was in Tasks 01-03.

## Touch

Exactly the files listed above. Do not touch `.claude/` or `codex/` (other
tasks own those trees).

## Steps

1. Read `antigravity/.agents/workflows/autopilot.md` in full (confirmed
   real content: ~90 lines — classification gate, containment ladder,
   escalation triggers) and `antigravity/README.md`'s gotchas section for
   antigravity's own human-gate model.
2. Fold the classification-gate and escalation-trigger content that
   actually applies under that model into
   `antigravity/.agents/workflows/build.md`, mirroring how Task 01 folded
   the same content into `.claude/skills/build/SKILL.md`. Preserve the
   literal sentence "Two triggers escalate to a human" verbatim — it is
   confirmed present, unwrapped, in the source
   (`antigravity/.agents/workflows/autopilot.md`) today, and Task 06's
   mirror-manifest canary line requires this exact phrase in this file's
   destination, so dropping or paraphrasing it here is not an option even
   under antigravity's own human-gate model.
3. Delete `antigravity/.agents/workflows/autopilot.md`.
4. `antigravity/README.md` (2 mentions), `antigravity/.agents/skills/gate/SKILL.md`'s
   `Next stage:` line, `antigravity/.agents/skills/resume-handoff/SKILL.md`'s
   stage enumeration, `antigravity/.agents/workflows/drain.md`, and
   `antigravity/.agents/skills/qa-sweep/SKILL.md` (its
   "(build/autopilot/drain/prioritize)" parenthetical) — each reference to
   `/autopilot` is updated the same way its `.claude`-leg counterpart was
   (drop to the three-stage set, or reword to describe `/build`'s bounded
   mode, matching Tasks 01-03's treatment of the equivalent `.claude`-leg
   file).

## Acceptance

- [ ] `[ ! -f antigravity/.agents/workflows/autopilot.md ]`
- [ ] `antigravity/.agents/workflows/build.md` contains the folded-in
      classification-gate and escalation-trigger content that applies
      under antigravity's own human-gate model.
- [ ] `grep -qF 'Two triggers escalate to a human' antigravity/.agents/workflows/build.md`
      (the literal sentence, confirmed present in the source today, must
      survive the fold-in verbatim — Task 06's mirror-manifest AC depends
      on it).
- [ ] `! grep -rq '/autopilot' antigravity/README.md antigravity/.agents/skills/gate/SKILL.md antigravity/.agents/skills/resume-handoff/SKILL.md antigravity/.agents/workflows/drain.md antigravity/.agents/skills/qa-sweep/SKILL.md`
