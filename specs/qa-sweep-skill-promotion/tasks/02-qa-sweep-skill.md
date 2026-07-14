# Task 02: Create the qa-sweep skill

Status: done
Depends on: none
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R5)
Touch: .claude/skills/qa-sweep/SKILL.md

## Goal

A new skill `.claude/skills/qa-sweep/SKILL.md` exists that captures the
proven "test everything" shape: scout the target surface, check
deployment/migration freshness FIRST, dispatch parallel per-domain test
agents, file specs for confirmed breakage, self-chain into `/critique`,
hand off to (or, when authorized, chain into) `/drain`, then re-verify.
It is model-invocable (not one of the four gated execution-stage skills)
and cites existing repo doctrine (token-discipline.md's dispatch/
delegation guidance, the human-gates self-chaining rules, and the new
`browser-automation-handoffs.md` rule) rather than restating it.

## Touch

Create exactly one new file: `.claude/skills/qa-sweep/SKILL.md`. Do not
create the `antigravity/` mirror or touch `.claude-plugin/plugin.json` — a
later task ports this finished file and bumps the plugin version. Do not
create `.claude/rules/browser-automation-handoffs.md` — a sibling task
owns that file; this task only needs to _cite_ its path, which is safe to
write regardless of whether the sibling has landed yet (both tasks are
independent: this task's citation is just a literal path reference, not a
read of the sibling file's content).

## Steps

1. Read `.claude/skills/critique/SKILL.md` in full — it is this spec's
   named model for frontmatter shape (`name`, `description` third-person
   with concrete trigger phrases, `argument-hint`) and for how a skill
   cites doctrine ("cite it, don't restate it") instead of restating rule
   content inline.
2. Read `.claude/rules/token-discipline.md`'s "Delegation defaults" and
   "Dispatch authoring" sections (for R2a/R2c's scout and per-domain
   dispatch citations, and R3's screenshot-delegation citation).
3. Write `.claude/skills/qa-sweep/SKILL.md` with:
   - Frontmatter: `name: qa-sweep`, a third-person `description` covering
     what it does and trigger phrases including "test the site", "QA
     sweep", "run a smoke test", "test everything end to end"; an
     `argument-hint` for the target (e.g. a repo path or URL).
   - A procedure section, in this exact order (spec R2a-g):
     a. Scout the target surface (routes/pages/MCP tool surfaces) to
     build a test plan — cite `.claude/rules/token-discipline.md` for
     cheap scout-tier dispatch.
     b. Check deployment/migration freshness FIRST, before any functional
     assertion: deploy timestamp vs. latest source commit, required
     secrets/env vars present, database schema/migration state matches
     expected migrations. State that this uses whatever project-
     specific tooling the target repo's own AGENTS.md/CLAUDE.md
     documents — state check categories, not vendor commands. Any
     drift found here is an environment/deploy finding, not a
     functional-bug finding.
     c. Dispatch parallel per-domain test agents (one per domain/surface
     from step a) — cite token-discipline.md's dispatch guidance
     (tier by stage type, capped returns, bounded fan-out). For the
     screenshot/page-check delegation specifically, cite
     token-discipline.md's "Delegation defaults" section by name (the
     literal phrase "Delegation defaults" must appear, or the phrase
     "route each page-check through a subagent" if that bullet has
     already landed there via the sibling `context-blowout-subagent-
guards` spec — check the file's current content and cite
     whichever form is actually present) — do not reimplement the cap/
     externalize-to-disk guidance inline.
     d. File a spec under `specs/<slug>/SPEC.md` for each confirmed piece
     of breakage found in step b or c (not unconfirmed/flaky
     findings).
     e. Self-chain into `/critique` on each filed spec — state this is
     permitted unconditionally since `/critique` is not one of the
     four gated execution-stage skills (cite root CLAUDE.md's
     self-chaining conventions, don't restate them).
     f. Hand off to `/drain` rather than auto-invoking it: present the
     critique-READY specs and tell the human to run `/drain`, UNLESS
     the user's original live request already named draining/fixing as
     part of the ask (e.g. "test everything and fix what's broken") —
     in which case that request IS the authorization and qa-sweep may
     chain into `/drain` directly. Cite docs/human-gates.md rather than
     restating the rationale.
     g. Re-verify: state both control-flow branches explicitly per the
     spec's R2g — (i) human-gated branch: qa-sweep's invocation ends
     at the step-f handoff; re-verification is a separate, later
     invocation the human triggers once `/drain` finishes; (ii)
     authorized auto-chain branch: qa-sweep continues in the same
     invocation after `/drain` completes, re-running the affected
     per-domain checks from step c before reporting final results.
   - A citation to `.claude/rules/browser-automation-handoffs.md` for any
     claude-in-chrome-driven check the skill performs (R5) — a pointer,
     not a restatement of the SSO/One-Tap handoff behavior.
   - A "Next stage" closing line per this repo's authoring conventions
     (see CLAUDE.md's "Authoring conventions" bullet on every
     artifact-producing skill needing one) — qa-sweep's filed specs feed
     `/critique` (self-chains) and then `/drain` (human-launched); phrase
     it accordingly.
4. Keep the SKILL.md body well under 500 lines per this repo's authoring
   convention; put execution-critical contracts (the R2f human-gating
   contract in particular) in the first 30 lines since skill bodies
   truncate on compaction but descriptions don't.

## Acceptance

- [x] `test -f .claude/skills/qa-sweep/SKILL.md` → exists (verifier PASS)
- [x] `grep -c "^name: qa-sweep$" .claude/skills/qa-sweep/SKILL.md` → 1 (verifier PASS)
- [x] `grep -qi "deploy\|migration\|freshness" .claude/skills/qa-sweep/SKILL.md` → match found (verifier PASS)
- [x] `grep -qi "critique" .claude/skills/qa-sweep/SKILL.md` → match found (verifier PASS)
- [x] `grep -qi "drain" .claude/skills/qa-sweep/SKILL.md` → match found (verifier PASS)
- [x] `grep -qi "browser-automation-handoffs" .claude/skills/qa-sweep/SKILL.md` → match found (verifier PASS)
- [x] `grep -qi "re-verify\|re-run" .claude/skills/qa-sweep/SKILL.md` → match found (verifier PASS)
- [x] `grep -qi "Delegation defaults\|route each page-check\|return a path" .claude/skills/qa-sweep/SKILL.md` → match found (verifier PASS)
- [x] MANUAL: browser-automation-handoffs citation reads as a pointer — both references (step c + closing section) name the rule for the login-wall handoff behavior without restating the "at most ONE click strategy"/SSO mechanism (verifier PASS)

Evidence: specs/qa-sweep-skill-promotion/evidence/02-qa-sweep-skill.md
