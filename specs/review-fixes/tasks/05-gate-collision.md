# Task 05: Gate Stop hook — verdict-line bypass for unattended workers' contractual stops

Status: pending
Depends on: 02, 04
Budget: 24 turns
Spec: ../SPEC.md (cluster 05)

## Goal

Gate's Stop hook blocks any finish while checks are red — but unattended
workers are contractually REQUIRED to stop mid-red with verdict
DEFERRED/BLOCKED (and the verifier with INCOMPLETE). In a gated repo the
hook would trap them in a loop. Gate's reference gains a bypass contract:
a final message beginning with a verdict line (DEFERRED, BLOCKED, or
INCOMPLETE) is a sanctioned stop the hook must not block, with the exact
mechanism documented (the installed hook greps the transcript tail for
the verdict line before exiting 2). Autopilot and drain references note
the interaction. (Depends on task 02: it rewrites drain's
BLOCKED/DEFERRED bullets — apply on top.)

## Touch

- `.claude/skills/gate/SKILL.md` (one sentence naming the bypass)
- `.claude/skills/gate/reference.md` (hook script + description,
  Stop-gate section starting ~line 17)
- `.claude/skills/autopilot/reference.md` (interaction note)
- `.claude/skills/drain/reference.md` (interaction note)
- `antigravity/.agents/skills/gate/SKILL.md` and
  `antigravity/.agents/skills/gate/reference.md` (mirror)

## Steps

1. In gate reference's Stop-gate section, amend the hook script and its
   description: before exiting 2, the hook inspects the transcript tail
   (the hook's stdin JSON carries `transcript_path`; read the last
   assistant message) and, if the final message begins with a verdict
   line `DEFERRED`, `BLOCKED`, or `INCOMPLETE`, exits 0 — call this a
   "sanctioned stop". Document the exact grep the installed hook uses.
2. Add one sentence to gate's SKILL.md noting the bypass exists and why
   (unattended workers stop mid-red by contract).
3. Add an interaction note to autopilot's reference (walk-away sessions in
   gated repos rely on the sanctioned-stop bypass) and to drain's
   reference (worker verdicts DEFERRED/BLOCKED pass the gate hook).
4. Mirror 1-2 into the antigravity gate skill + reference (Antigravity
   hook JSON shape).

## Acceptance

- [ ] `grep -q "sanctioned stop" .claude/skills/gate/reference.md && grep -q "DEFERRED" .claude/skills/gate/reference.md && grep -q "INCOMPLETE" .claude/skills/gate/reference.md` → exit 0 (bypass contract documented)
- [ ] `grep -q "transcript" .claude/skills/gate/reference.md` → exit 0 (mechanism named — hook reads the transcript tail before exiting 2)
- [ ] `grep -qi "sanctioned" .claude/skills/gate/SKILL.md` → exit 0
- [ ] `grep -qi "sanctioned stop\|gate.*hook" .claude/skills/autopilot/reference.md && grep -qi "sanctioned stop\|gate.*hook" .claude/skills/drain/reference.md` → exit 0 (interaction noted both places; confirm by reading, greps alone can pass on unrelated text)
- [ ] `grep -q "sanctioned stop" antigravity/.agents/skills/gate/reference.md` → exit 0 (mirror)
