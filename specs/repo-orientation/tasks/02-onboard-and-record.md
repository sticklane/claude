# Task 02: Onboard encodes the practices; research record; mirror

Status: done
Depends on: 01, ../../chaining-antipatterns/tasks/02-chain-implementation.md, ../../context-management/tasks/04-reference-tocs-research-record.md, ../../code-vs-llm/tasks/01-ladder.md
Priority: P2
Budget: 25 turns
Spec: ../SPEC.md (requirements R4, R5, R6)

## Goal

Teach /onboard the four vendor practices (repo-map bullet,
per-directory CLAUDE.md for monorepos, AGENTS.md interop offer,
where-open-work-lives pointer), write the "Repo orientation for
agents" research entry, and mirror the onboard changes into the
antigravity port. Spec R4-R6 carry the exact content and sources.

## Touch

- .claude/skills/onboard/SKILL.md (also edited by chaining-antipatterns 02 — dep above serializes)
- docs/external-playbooks.md (appenders serialize — deps above cover the prior appenders)
- antigravity/.agents/skills/onboard/SKILL.md

## Steps

1. Onboard additions per R4 (four bullets/offers, exact marker phrases).
2. external-playbooks entry per R5 (convergences, divergences, llms.txt line, URLs).
3. Antigravity onboard mirror per R6 (AGENTS.md is its native context file — interop offer becomes that one sentence).
4. No plugin.json bump (review-fixes 99 owns it).

## Acceptance

- [x] `grep -qi "repo map" .claude/skills/onboard/SKILL.md && grep -q "per-directory CLAUDE.md" .claude/skills/onboard/SKILL.md && grep -q "AGENTS.md" .claude/skills/onboard/SKILL.md && grep -qi "open work" .claude/skills/onboard/SKILL.md` -> exit 0 (R4) — verifier ran it, exit 0; ../evidence/02-onboard-and-record.md
- [x] `sed -n '/[Rr]epo orientation for agents/,/^## /p' docs/external-playbooks.md | grep -qi "agents.md" && sed -n '/[Rr]epo orientation for agents/,/^## /p' docs/external-playbooks.md | grep -qi "kiro" && sed -n '/[Rr]epo orientation for agents/,/^## /p' docs/external-playbooks.md | grep -qi "llms.txt"` -> exit 0 (R5) — verifier ran it, exit 0; ../evidence/02-onboard-and-record.md
- [x] `grep -qi "repo map" antigravity/.agents/skills/onboard/SKILL.md && grep -q "per-directory" antigravity/.agents/skills/onboard/SKILL.md` -> exit 0 (R6) — verifier ran it, exit 0; ../evidence/02-onboard-and-record.md
