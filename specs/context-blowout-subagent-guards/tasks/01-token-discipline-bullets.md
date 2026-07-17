# Task 01: Add browser-delegation and deferred-tool-schema bullets to token-discipline.md

Status: in-progress
Depends on: none
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4)
Touch: .claude/rules/token-discipline.md

## Goal

`.claude/rules/token-discipline.md` gains two new bullets — one in
"Delegation defaults", one in "Dispatch authoring" — that promote two
already-proven-but-unmandated safety practices to required doctrine, per
../SPEC.md's Problem/Solution sections. No other file changes; no new
section headers.

## Touch

Only `.claude/rules/token-discipline.md` is touched by this task. Do not
touch `.claude/agents/scout.md`, any `.claude/skills/` file, or any
`antigravity/`/`codex/` mirror path — per R4, this repo's `.claude/rules/`
directory has no mirrored counterpart under `antigravity/`, so no mirror
step applies here.

## Steps

1. Read `.claude/rules/token-discipline.md` in full, noting the exact text
   of the "Delegation defaults" section's existing `ToolSearch`/code-search
   bullet (spec calls out lines 42–50) and the "Dispatch authoring"
   section's existing bullets (loop bounds, tier choice, return-size caps).
2. In "Delegation defaults", insert a new bullet immediately after the
   existing `ToolSearch` code-search-MCP bullet and before the
   `## Model and effort matching` header. The bullet must, in the section's
   existing style (bold lead-in, explanation, citation):
   - (a) require multi-page/multi-step browser-automation walks to route
     each page-check through a subagent that returns a short structured
     verdict, rather than accumulating raw screenshots in the orchestrating
     session's context — the literal phrase "route each page-check through
     a subagent" must appear;
   - (b) state a concrete cap of 2 direct-context screenshots per turn,
     with anything beyond the cap required to go through a subagent — the
     literal phrase "2 direct-context screenshots" must appear;
   - (c) cite the RETRY-succeeded-via-delegation evidence (SPEC.md's
     Problem section / Research grounding quotes) as the proven pattern to
     follow, without restating the quotes verbatim;
   - cite `scout` (this section's own opening bullet) as the delegation
     vehicle for pure existence/state-check pages, and note `scout` has no
     MCP tool grant (per `.claude/agents/scout.md`'s frontmatter — do not
     claim it is "Read/Grep/Glob-only"; it also carries scoped
     `Bash(git log *)`, `Bash(git show *)`, `Bash(ls *)`, `Bash(wc *)`) and
     so cannot drive `mcp__claude-in-chrome__*` tools, reserving
     `general-purpose` or a purpose-built agent for pages needing an
     interaction sequence.
3. In "Dispatch authoring", insert a new bullet (anywhere consistent with
   the section's existing bullet style) that requires dispatch prompts for
   workers likely to call a deferred tool (naming `Monitor` explicitly as
   the evidenced case, plus the general class of deferred tools) to
   explicitly remind the worker to batch-load the tool's schema via
   `ToolSearch` before calling it — the literal phrase "batch-load the
   tool's schema via" must appear — rather than relying solely on the
   harness's own system-reminder. Cite the harness-system-reminder
   insufficiency (the guessed-parameter `InputValidationError` evidence)
   rather than restating it at length.
4. Do not add, rename, or duplicate any `## ` section header — both bullets
   land inside the two existing sections named above.
5. Do not restate content already present elsewhere in the file (R3): cite
   the RETRY evidence and the harness system-reminder rather than
   re-describing them in full, and cite the `scout` tool-grant fact rather
   than re-deriving it.

## Acceptance

- [x] `grep -c "route each page-check through a subagent" .claude/rules/token-discipline.md` → 1 (verified: 1)
- [x] `grep -c "2 direct-context screenshots" .claude/rules/token-discipline.md` → 1 (verified: 1)
- [x] `grep -c "batch-load the tool's schema via" .claude/rules/token-discipline.md` → 1 (verified: 1)
- [x] `grep -n "^## Delegation defaults" .claude/rules/token-discipline.md` → exactly one match (verified: 1)
- [x] `grep -n "^## Dispatch authoring" .claude/rules/token-discipline.md` → exactly one match (verified: 1)
- [x] `grep -c "^## " .claude/rules/token-discipline.md` → same count as `git show HEAD:.claude/rules/token-discipline.md | grep -c '^## '` (no new section headers added) (verified: 8 == 8)
- [x] MANUAL: a human or reviewing agent reads both new bullets in context and confirms they cite rather than restate the RETRY evidence and the `scout` tool-grant constraint, per R3. (verified: both bullets point to specs/context-blowout-subagent-guards' Problem/Research-grounding sections and to `.claude/agents/scout.md`'s frontmatter rather than restating the quotes; scout grant listed per task step 2's explicit requirement, not claimed "Read/Grep/Glob-only")
