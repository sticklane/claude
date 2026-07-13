Status: open
Priority: P2
Breakdown-ready: true

## Problem

"Thoroughly test the site and MCPs" has been run as a bespoke, un-skilled
instruction 3 separate times in this repo's history. Quality varied wildly:
one run crashed entirely from unbounded screenshot capture (context
blowout). Two runs succeeded, and the best of the three self-chained a
clear, effective shape on its own initiative: scout the target surface →
dispatch parallel per-domain test agents → file specs for anything broken →
critique → drain → re-verify. That successful shape isn't captured as a
reusable skill anywhere, so the next "test everything" request will likely
either reinvent it from scratch or repeat the crash.

Two further patterns showed up across these same sessions:

1. Deployment/environment drift repeatedly masqueraded as application bugs.
   A missing required secret, a 6-day-stale service deploy, and a database
   schema-drift error were each independently rediscovered fresh, with no
   shared memory carrying the lesson between sessions — costing real
   debugging time before anyone thought to check the environment instead of
   the code.
2. Google SSO/One-Tap login is a recurring dead end for browser-driven
   testing. In an unrelated session touching the same claude-in-chrome
   tooling, four distinct click strategies were tried against a Google
   SSO/One-Tap chip before handing off to a human — wasted effort a fast
   detect-and-handoff rule would have avoided.

## Solution

1. Promote the proven shape into a new skill,
   `.claude/skills/qa-sweep/SKILL.md`, with an `antigravity/` mirror
   (`antigravity/.agents/skills/qa-sweep/SKILL.md`) per this repo's port-chain
   convention (cited, not restated, in root CLAUDE.md's "Authoring
   conventions" section) — no `codex/` mirror, since codex only mirrors the
   four explicit-invocation skills (drain/build/autopilot/evals) and
   qa-sweep is not one of them.
2. Order the skill's procedure so deployment/migration freshness is checked
   BEFORE functional assertions, so drift-caused false bug reports are
   caught at the top of the run instead of chased as application bugs.
3. Add a new rule, `.claude/rules/browser-automation-handoffs.md`, stating
   the Google SSO/One-Tap detect-and-handoff behavior, so it is written once
   and cited by every claude-in-chrome-driven skill rather than
   reimplemented per skill (this repo's rule-citation convention, per
   `.claude/rules/mirror-procedure-discipline.md`'s "Write invariant
   procedural content once and carry it faithfully" pattern).

## Research grounding

> "one run crashed entirely from unbounded screenshot capture (context
> blowout)" — task evidence, this session.

> "the BEST of the three self-chained a clear, effective shape: scout →
> parallel per-domain test agents → file specs for anything broken →
> critique → drain → re-verify" — task evidence, this session.

> "a missing required secret, a 6-day-stale service deploy, and a database
> schema-drift error each independently masqueraded as application bugs,
> each rediscovered fresh with no shared memory across sessions" — task
> evidence, this session.

> "four distinct click strategies were tried against a Google SSO/One-Tap
> login chip before handing off to a human" — task evidence, this session.

## Requirements

R1. Create `.claude/skills/qa-sweep/SKILL.md` following this repo's
established frontmatter shape (`name`, `description` written third
person with concrete trigger phrases, optional `argument-hint`) — model
it on `.claude/skills/critique/SKILL.md`'s frontmatter shape. Propose
`qa-sweep` as the directory/command name; description must cover what it
does and trigger phrases such as "test the site", "QA sweep", "run a
smoke test", "test everything end to end". It is NOT one of the four
explicit-invocation-only skills (drain/build/autopilot/evals), so it
stays model-invocable under the repo's normal self-chaining rules.

R2. The skill's procedure, in order:
a. Scout the target surface (routes/pages/MCP tool surfaces) to build a
test plan, using cheap scout-tier dispatch per
`.claude/rules/token-discipline.md`.
b. Check deployment/migration freshness FIRST, before any functional
assertion: verify each target service's deploy is current (e.g. last
deploy timestamp vs. latest source commit), required secrets/env vars
are present, and database schema/migration state matches the
codebase's expected migrations. Use whatever project-specific
tooling the target repo's own AGENTS.md/CLAUDE.md documents for these
checks; the skill states the check categories, not vendor-specific
commands. Any drift found here is reported as an environment/deploy
finding, not routed through the functional-bug path in R2d.
c. Dispatch parallel per-domain test agents (one per functional
domain/surface identified in R2a) to exercise the target and report
findings — sized per `.claude/rules/token-discipline.md`'s dispatch
guidance (tier by stage type, capped returns, bounded fan-out).
d. File a spec under `specs/<slug>/SPEC.md` for each confirmed piece of
breakage found in R2b or R2c (not for unconfirmed/flaky findings).
e. Self-chain into `/critique` on each filed spec — permitted
unconditionally per root CLAUDE.md's self-chaining conventions since
`/critique` is not one of the four gated execution-stage skills
(cited, not restated).
f. Hand off to `/drain` for fixes rather than auto-invoking it: per root
CLAUDE.md's self-chaining conventions, `/drain` is one of the four
execution-stage skills that are model-invocable ONLY on the user's
live-message authorization (docs/human-gates.md, cited not
restated). qa-sweep therefore presents the critique-READY specs and
tells the human to run `/drain`, unless the user's original live
request already named draining/fixing as part of the ask (e.g. "test
everything and fix what's broken"), in which case that request IS
the authorization and qa-sweep may chain into `/drain` directly.
g. Re-verify: after fixes land, re-run the affected per-domain checks
from R2c to confirm the finding is resolved. This step's control flow
depends on which R2f branch fired:

- Human-gated branch (the default): qa-sweep's own invocation ends at
  the R2f handoff — it does not block waiting for a human to run
  `/drain`. Re-verification in this branch is a separate, later
  qa-sweep invocation (or a targeted re-run of just the affected
  per-domain check) that the human triggers once `/drain` has
  finished, not a continuation of the original run.
- Authorized auto-chain branch (the user's live request already named
  draining/fixing): qa-sweep chains into `/drain` and, once `/drain`
  completes, continues in the same invocation to re-run the affected
  per-domain checks before reporting final results.

R3. The skill's page-check/screenshot steps must cite
`.claude/rules/token-discipline.md`'s "Delegation defaults" section for
their screenshot/subagent-delegation guidance, rather than reimplementing
it. `specs/context-blowout-subagent-guards/SPEC.md` (open as of this
spec's authoring) lands its fix as new bullets inside that same section —
specifically a bullet requiring each page-check to route through a
subagent returning a short verdict (anchored on the literal phrase "route
each page-check through a subagent") — not as a standalone spec artifact
qa-sweep could point to by name. So R3's citation target is
`.claude/rules/token-discipline.md`'s "Delegation defaults" section,
whether or not `context-blowout-subagent-guards` has merged by the time
this spec reaches `/breakdown`:

- If it has already merged, cite the section as-is (it will contain the
  "route each page-check through a subagent" bullet).
- If it has not yet merged, R2c's per-domain test agents must at minimum
  follow the section's existing baseline: cap subagent returns at 1-2k
  tokens, externalize large artifacts (e.g. a batch of screenshots) to
  disk and return a path rather than pasting them inline, and never
  accumulate raw screenshot bytes in the orchestrating skill's own
  context — each page check is delegated to a fresh subagent that returns
  a verdict, not the screenshot. This is the same behavior the sibling
  spec's bullet will make explicit; qa-sweep's citation of the section
  stays correct either way, so no rework is needed once the sibling
  merges.

R4. Add `.claude/rules/browser-automation-handoffs.md`: any
claude-in-chrome-driven flow that encounters a Google SSO/One-Tap login
surface attempts at most ONE click strategy against it, then hands off
to the human rather than retrying alternate strategies. State this once
as canonical doctrine, in the same "cite it, don't restate it" shape
this repo already uses for its other rule files.

R5. `.claude/skills/qa-sweep/SKILL.md` cites
`.claude/rules/browser-automation-handoffs.md` for its own
claude-in-chrome-driven checks rather than restating the SSO handoff
behavior inline.

R6. Note for whoever breaks this spec down: the personal skill
`health-admin` referenced in the task evidence as another
claude-in-chrome-driven flow that should eventually cite R4's rule
lives OUTSIDE this repo, at `/Users/sjaconette/automation/skills/health-admin`
(confirmed by scout — it is symlinked into `~/.claude/skills/`, not
part of `/Users/sjaconette/claude`). This spec's own acceptance
criteria cannot reach that file. R4's rule text is the deliverable this
repo owns; propagating a citation into `health-admin`'s SKILL.md is a
cross-repo follow-up, filed per Open questions below, not a requirement
of this spec.

R7. `.claude-plugin/plugin.json`'s `version` field is bumped (per root
CLAUDE.md's "Bump `version` in `plugin.json` whenever skill behavior
changes") as part of adding the new `qa-sweep` skill; its `agents` array
is left untouched, since qa-sweep is a skill, not an agent, and skills
are manifest-free.

## Out of scope

- Editing `/Users/sjaconette/automation/skills/health-admin/SKILL.md` or any
  other file outside `/Users/sjaconette/claude` — out of this repo's spec
  pipeline entirely (see R6).
- Building or modifying `specs/context-blowout-subagent-guards/SPEC.md` or
  its own tasks — that spec is independent work with its own pipeline;
  this spec only cites the `.claude/rules/token-discipline.md` section its
  fix lands in (R3).
- A `codex/` mirror for `qa-sweep` — codex only mirrors the four
  explicit-invocation skills (drain/build/autopilot/evals), per root
  CLAUDE.md's mirror-obligations bullet.
- Implementing the actual deployment-freshness check logic for any specific
  target project/vendor (Cloud Build, Cloudflare, etc.) — R2b states the
  check categories qa-sweep must perform; the concrete commands are
  necessarily project-specific and belong in the target project's own
  AGENTS.md, not in this toolkit skill.

## Acceptance criteria

1. `test -f .claude/skills/qa-sweep/SKILL.md` — new skill file exists.
2. `grep -c "^name: qa-sweep$" .claude/skills/qa-sweep/SKILL.md` → 1 —
   frontmatter name field set correctly.
3. `grep -qi "deploy\|migration\|freshness" .claude/skills/qa-sweep/SKILL.md`
   → match found — the deployment/migration freshness check step (R2b) is
   present in the skill body.
4. `grep -qi "critique" .claude/skills/qa-sweep/SKILL.md` → match found —
   the self-chain into `/critique` (R2e) is documented.
5. `grep -qi "drain" .claude/skills/qa-sweep/SKILL.md` → match found — the
   hand-off-not-auto-chain behavior for `/drain` (R2f) is documented.
6. `test -f antigravity/.agents/skills/qa-sweep/SKILL.md` — antigravity
   mirror exists per the port-chain convention.
7. `test ! -e codex/.agents/skills/qa-sweep` — confirms no codex mirror was
   created (qa-sweep is not one of the four codex-mirrored skills).
8. `test -f .claude/rules/browser-automation-handoffs.md` — new rule file
   exists.
9. `grep -qi "one-tap\|single sign-on\|sso" .claude/rules/browser-automation-handoffs.md`
   → match found — the rule names the Google SSO/One-Tap surface.
10. `grep -qi "browser-automation-handoffs" .claude/skills/qa-sweep/SKILL.md`
    → match found — qa-sweep cites the new rule (R5) rather than restating
    it.
11. `grep -qi "browser-automation-handoffs" .claude/skills/qa-sweep/SKILL.md`
    — MANUAL: confirm at breakdown/build time that the citation reads as a
    pointer ("cite it, don't restate it") and not a full restatement of the
    SSO handoff behavior, per this repo's authoring conventions — not
    mechanically checkable by grep alone.
12. `git diff .claude-plugin/plugin.json` touches only the `version` line
    (no lines inside the `agents` array change) — confirms qa-sweep, as a
    skill and not an agent, needed no manifest edit for the `agents` array
    (root CLAUDE.md's manifest-free-for-skills convention), while `version`
    is still bumped per R7.
13. `grep -qi "re-verify\|re-run" .claude/skills/qa-sweep/SKILL.md` → match
    found — the re-verification step (R2g) is documented, including its
    two branches (human-gated vs. authorized auto-chain).
14. `grep -qi "Delegation defaults\|route each page-check\|return a path" .claude/skills/qa-sweep/SKILL.md`
    → match found — the skill's page-check/screenshot steps cite the
    token-discipline.md delegation guidance (R3) rather than omitting it.

## Open questions

- Propagating the Google SSO/One-Tap handoff rule (R4) into
  `/Users/sjaconette/automation/skills/health-admin/SKILL.md` is a
  cross-repo change this spec cannot make. Recommend filing a task in that
  repo's own tracking (or its `HUMAN.md` if it uses the same convention)
  once R4 lands here.
