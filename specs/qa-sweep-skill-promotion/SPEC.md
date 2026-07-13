Status: open
Priority: P2

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
   `.claude/rules/token-discipline.md`'s "Write invariant procedural content
   once and carry it faithfully" pattern — see
   `.claude/rules/mirror-procedure-discipline.md` for the same discipline
   applied to mirrored procedure).

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
    g. Re-verify: after fixes land (via drain or manual fix), re-run the
       affected per-domain checks from R2c to confirm the finding is
       resolved.

R3. The skill's page-check/screenshot steps must follow whatever
    screenshot/subagent-delegation guidance the sibling
    `context-blowout-subagent-guards` spec establishes, cited rather than
    reimplemented, IF that spec exists by the time this spec reaches
    `/breakdown`. As of this spec's authoring, `context-blowout-subagent-guards`
    does NOT exist anywhere in `specs/` (checked open and archived) — see
    Open questions. Until it exists, R2c's per-domain test agents must at
    minimum follow the existing baseline already in
    `.claude/rules/token-discipline.md`: cap subagent returns at 1-2k
    tokens, externalize large artifacts (e.g. a batch of screenshots) to
    disk and return a path rather than pasting them inline, and never
    accumulate raw screenshot bytes in the orchestrating skill's own
    context — each page check is delegated to a fresh subagent that returns
    a verdict, not the screenshot.

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

## Out of scope

- Editing `/Users/sjaconette/automation/skills/health-admin/SKILL.md` or any
  other file outside `/Users/sjaconette/claude` — out of this repo's spec
  pipeline entirely (see R6).
- Building or modifying `context-blowout-subagent-guards` — that spec, if
  and when it is authored, is independent work; this spec only cites its
  eventual guidance (R3).
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
11. `grep -qi "browser-automation-handoffs" .claude/rules/token-discipline.md .claude/skills/qa-sweep/SKILL.md`
    — MANUAL: confirm at breakdown/build time that the citation reads as a
    pointer ("cite it, don't restate it") and not a full restatement of the
    SSO handoff behavior, per this repo's authoring conventions — not
    mechanically checkable by grep alone.
12. `.claude-plugin/plugin.json`'s `agents` array is unchanged by this
    spec's work (`git diff --stat .claude-plugin/plugin.json` shows no
    changes after implementation) — confirms qa-sweep, as a skill and not
    an agent, needed no manifest edit, per root CLAUDE.md's
    manifest-free-for-skills convention.

## Open questions

- `context-blowout-subagent-guards` does not exist in `specs/` (open or
  archived) as of this spec's authoring (2026-07-13) — confirmed by direct
  search. The task brief that produced this spec assumed it either existed
  as an open spec or had already merged. A human should confirm: was this
  spec authored under a different name, is it still pending authorship
  elsewhere, or was the sibling-spec assumption simply wrong? R3 gives
  qa-sweep a working fallback either way, but the citation in R3 should be
  updated to the real spec name once one exists.
- Propagating the Google SSO/One-Tap handoff rule (R4) into
  `/Users/sjaconette/automation/skills/health-admin/SKILL.md` is a
  cross-repo change this spec cannot make. Recommend filing a task in that
  repo's own tracking (or its `HUMAN.md` if it uses the same convention)
  once R4 lands here.
