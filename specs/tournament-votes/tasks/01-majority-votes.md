# Task 01: Majority-PASS verifier votes in the tournament

Status: pending
Depends on: ../../review-fixes/tasks/02-drain-state-machine.md, ../../model-agnostic/tasks/02-core-tier-language.md, ../../repo-orientation/tasks/02-onboard-and-record.md
Priority: P1
Budget: 25 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R6)

## Goal

Replace the tournament filter's single verifier run with three
independent runs and majority-PASS (2/3); verifier-BLOCKED
disqualifies outright with the quote recorded; PASS-vote count becomes
the first mechanical rank key with the angle-index final tiebreak;
one cost sentence citing docs/human-gates.md; mirror the FULL new
semantics into the antigravity drain workflow; append the N-vote line
to the AlphaCode 2 entry. Spec R1/R2/R3/R4/R6 are exact.

## Touch

- .claude/skills/drain/reference.md (Filter/Rank paragraphs; also edited by review-fixes 02/04, model-agnostic 02 — deps serialize)
- antigravity/.agents/workflows/drain.md
- docs/external-playbooks.md (appender — dep on repo-orientation 02 serializes the chain)

## Steps

1. Filter rewrite per R1 (vote values PASS/FAIL/INCOMPLETE; BLOCKED run disqualifies; worker-verdict handling unchanged).
2. Rank rewrite per R2 (PASS votes first, summed gate findings, diff stat, t1 before t2 before t3).
3. Cost sentence per R3 inside the Tournament section.
4. Mirror per R4 (full semantics; old single-run line replaced).
5. N-vote line per R6. No plugin.json bump (rf-99 owns it).

## Acceptance

- [ ] `grep -q "majority PASS" .claude/skills/drain/reference.md && grep -q "three independent verifier" .claude/skills/drain/reference.md` -> exit 0 (R1)
- [ ] `sed -n '/^\*\*Rank\./,/^$/p' .claude/skills/drain/reference.md | grep -q "PASS votes" && grep -q "Drain, not the verifier" .claude/skills/drain/reference.md && sed -n '/^\*\*Rank\./,/^$/p' .claude/skills/drain/reference.md | grep -q "t1 before t2"` -> exit 0 (R2)
- [ ] `! grep -qi "one verifier run per candidate" .claude/skills/drain/reference.md` -> exit 0 (R1)
- [ ] `sed -n '/^## Tournament/,/^## /p' .claude/skills/drain/reference.md | grep -qi "human-gates"` -> exit 0 (R3)
- [ ] `grep -q "majority PASS" antigravity/.agents/workflows/drain.md && grep -q "PASS votes" antigravity/.agents/workflows/drain.md && ! grep -qi "one verifier-skill run per candidate" antigravity/.agents/workflows/drain.md` -> exit 0 (R4)
- [ ] `grep -q "N-vote" docs/external-playbooks.md` -> exit 0 (R6)
