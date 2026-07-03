# Task 02: Escalation triggers and tool risk-rating in /autopilot

Status: pending
Depends on: none
Budget: 30 turns
Spec: ../SPEC.md (requirements R3, R8 autopilot part)

## Goal

/autopilot's walk-away contract names the two escalation triggers (same
step failing twice; reaching a high-risk action: push, deploy, data
deletion, publishing, spending), and its permissions step tells the user
to risk-rate tools by reversibility and "blast radius" when scoping the
allowlist. The antigravity autopilot workflow mirrors both.

## Touch

- `.claude/skills/autopilot/SKILL.md` (step 2 and step 4 only)
- `antigravity/.agents/workflows/autopilot.md` (its permissions and
  walk-away steps)

## Steps

1. In `.claude/skills/autopilot/SKILL.md` step 2 (preconditions /
   permissions), add the risk-rating sentence using the phrase
   "blast radius".
2. In step 4 (walk-away contract), add the two escalation triggers,
   including the "failing twice" retry threshold.
3. Mirror both additions into `antigravity/.agents/workflows/autopilot.md`
   at its equivalent steps.

## Acceptance

- [ ] `grep -q "blast radius" .claude/skills/autopilot/SKILL.md && grep -qi "failing twice\|fails twice\|failed twice" .claude/skills/autopilot/SKILL.md` → pass
- [ ] `grep -q "blast radius" antigravity/.agents/workflows/autopilot.md` → pass
