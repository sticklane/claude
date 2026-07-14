# Documentation-currency check in /build's completion step

## Problem

The original ask was to make documentation updates "part of the code
review phase" — but `/code-review` is provided by the harness/an external
plugin (there is no `.claude/skills/code-review/` in this repo, and
`docs/anthropic-playbook.md`/`build/SKILL.md:86` both treat it as an
external command this repo invokes, not one it defines), so it isn't a
file this repo can edit. What this repo _does_ own is `/build`'s completion
step and `.claude/rules/quality-discipline.md`. Today, documentation
staying in sync with code (AGENTS.md's Map/Commands/State, README.md) is
entirely decentralized: it happens only when a task's own `Touch:` header
and acceptance criteria explicitly call it out
(`specs/absorb-agent-tools/tasks/03-repo-wiring-and-pointers.md` is the
existing example). There's no last-mile check for the case a task's
author didn't anticipate — a diff that adds a new top-level component, or
changes a documented command, with no `Touch:` line mentioning `AGENTS.md`
at all.

**Sequencing note**: `specs/narrow-autopilot` also edits `build/SKILL.md`,
inserting a classification gate "near its start" — that shifts every
line number after it. This spec must land **after** `narrow-autopilot`
(or its implementer must re-locate the anchors below by section content,
not by re-reading stale line numbers) — every `build/SKILL.md` line
reference below is a snapshot, not a contract; find the actual
pre-commit-review bullet in section 4 ("Close out") at implementation
time.

## Solution

Add a "Documentation currency" section to
`.claude/rules/quality-discipline.md` (alongside its existing TDD/Commits/
Checks sections): before calling any task done, check whether the diff
invalidates anything `AGENTS.md`'s Map, Commands, or State sections claim,
or anything README.md documents for end users — if so, update it in the
same commit, not a follow-up task. `.claude/skills/build/SKILL.md` cites
this new section in its own completion step (one line, per this repo's
own citation convention — "cite, don't restate").

## Requirements

- **R1**: `.claude/rules/quality-discipline.md` gains a "## Documentation
  currency" section scoped explicitly to `/build`'s attended completion
  step — not to "any code change, attended or unattended" the way this
  file's opening line otherwise frames it, and matching the Out-of-scope
  exclusion below rather than contradicting it: before `/build` finishes
  a task, check whether the diff invalidates `AGENTS.md`'s Map
  (new/moved/removed top-level components), Commands (a documented
  command's behavior or invocation changed), or State sections, or
  anything README.md tells an end user — if so, update it in the same
  commit.
- **R2**: This is explicitly a discipline reminder, not a new mechanical
  gate — no automated check is added that tries to diff AGENTS.md's
  prose against the codebase (verified by the repo-navigability scout:
  no such rule exists today, and file/command drift is judgment-based,
  not mechanically verifiable the way a link or a plugin name is).
- **R3**: This does not replace or weaken the existing decentralized
  pattern (a task's own `Touch:` header + acceptance criteria explicitly
  scoping doc updates) — it's a safety net for what that pattern misses,
  applying to every task regardless of whether its author thought to add
  `AGENTS.md`/README to `Touch:`.
- **R4**: `.claude/skills/build/SKILL.md`'s section 4 ("Close out"), at its
  pre-commit review bullet (find it by section content — the "## 4. Close
  out" heading, then the "Pre-commit review" bullet adjacent to the
  `/code-review` invocation R5 touches — not by a numbered line, per the
  sequencing note above), cites this new quality-discipline.md section by
  name (one line, e.g. "see quality-discipline.md's Documentation
  currency section") rather than restating its content — both R4's
  citation and R5's note land at the same bullet, not scattered across
  section 4's other close-out steps (simplify, task-file update, commit).
- **R5**: The nearby `/code-review` invocation (via the Skill tool, args
  `low`, with a documented fallback "where the Skill tool or plugin is
  unavailable" — found by the literal text `/code-review` in the same
  close-out section, not by a numbered line) is the one place a reader
  could plausibly assume this
  repo owns doc-currency checking through that invocation. Add a
  one-line note there, worded distinctly from R4's citation so the two
  edits are independently verifiable: doc currency is checked by the new
  quality-discipline.md section (R1), **not by `/code-review` itself** —
  `/code-review` stays scoped to what the harness/plugin defines it to
  check.
- **R6**: Per CLAUDE.md's mirroring convention ("when a skill changes
  here, mirror the change there in the same commit"), both edits land in
  their mirrors too — antigravity and codex:
  - `antigravity/.agents/workflows/build.md` (mirrors `build/SKILL.md`,
    including its close-out review logic) gets an R4-equivalent citation
    — but antigravity has no `quality-discipline.md` file to name (its
    equivalent lives inline as `antigravity/AGENTS.md`'s Quality
    discipline section), so this mirror's citation reads "see AGENTS.md's
    Quality discipline section" instead of naming a file that doesn't
    exist there. R5's note attaches differently too, since this mirror has
    no `/code-review` call at all (its close-out step already falls back
    to a subagent reviewer instead, worded along the lines of "since this
    mirror has no code-review skill to..." — a content snapshot, not a
    line-numbered anchor) — the R5-equivalent note attaches to that
    sub-reviewer fallback bullet, not to a `/code-review` invocation
    that doesn't exist in this mirror. `antigravity/AGENTS.md`'s
    `## Quality discipline` section (mirrors `quality-discipline.md`)
    gets the same new "Documentation currency" content from R1.
  - Per CLAUDE.md's codex-leg convention ("a task whose `Touch:` changes
    one of the four `.claude/skills/{drain,build,autopilot,evals}/SKILL.md`
    files must also carry the matching
    `codex/.agents/skills/<name>/SKILL.md` update"),
    `codex/.agents/skills/build/SKILL.md` — real content, not a symlink —
    gets both edits too. Codex has no `quality-discipline.md` (and no
    convention of citing `.claude/rules/`) for R4's citation to point at,
    so the codex leg inlines the reminder instead of citing it: one line
    at the close-out step's pre-commit-review bullet stating the check
    directly (e.g. "before committing, check whether the diff invalidates
    AGENTS.md's Map/Commands/State or anything README.md documents for
    end users — update it in the same commit"), not a citation to a file
    codex can't resolve. Codex's close-out step does invoke `$code-review`
    (unlike the antigravity mirror), so the R5-equivalent note attaches
    there the same way it does in `.claude/skills/build/SKILL.md` — but
    using the distinct literal phrase "not by $code-review itself" (codex's
    own invocation syntax, not the main repo's slash-command phrasing), so
    this edit is independently verifiable from the inlined reminder above
    rather than sharing its anchor.
- **R7**: `.claude-plugin/plugin.json`'s `version` is bumped (skill
  behavior changed in `/build`).

## Out of scope

- Any change to the harness's built-in `/code-review`, `/review`, or
  `/security-review` — not files this repo can edit.
- A mechanical CI gate that verifies AGENTS.md accuracy against the
  codebase — explicitly rejected per R2; this stays a human/agent
  judgment call at task-completion time.
- Retrofitting this check onto `/drain`'s unattended workers — `/build`
  is attended, so a human is present to judge "does this diff invalidate
  documented state"; `/drain`'s unattended workers are out of scope for
  this spec (a worker misjudging doc relevance unattended is a different,
  bigger risk than this spec's small addition should take on).

## Acceptance criteria

Every grep below is anchored on a literal phrase confirmed absent
(`grep -c` → 0) from its target file as of 2026-07-13; each criterion
passes when the count is 1 or more after the edit.

- [ ] `grep -c "Documentation currency" .claude/rules/quality-discipline.md`
      → 1 or more (R1's new section heading/content).
- [ ] `grep -c "Documentation currency" .claude/skills/build/SKILL.md`
      → 1 or more (R4's citation, landed at the close-out section's
      pre-commit-review bullet per R4's section-content anchor, not a
      line number).
- [ ] `grep -c "not by /code-review itself" .claude/skills/build/SKILL.md`
      → 1 or more (confirmed absent today; R5's note that doc-currency
      checking lives in quality-discipline.md, not in `/code-review` —
      anchored on wording distinct from R4's citation so the two edits
      verify independently).
- [ ] `grep -c "Documentation currency" antigravity/AGENTS.md` → 1 or more
      (R6's antigravity mirror of R1's new section; deliberately NOT
      checked against `antigravity/.agents/workflows/build.md` — R6
      specifies that mirror's citation reads "see AGENTS.md's Quality
      discipline section," not the literal phrase "Documentation
      currency", so this AC only targets the file that actually gains it).
- [ ] `grep -c "Quality discipline section" antigravity/.agents/workflows/build.md`
      → 1 or more (confirmed absent today; R6's antigravity citation
      names `AGENTS.md`'s `## Quality discipline` section, since
      antigravity has no standalone `quality-discipline.md` file to cite).
- [ ] `grep -c "not by the sub-reviewer fallback" antigravity/.agents/workflows/build.md`
      → 1 or more (confirmed absent today; R6's antigravity mirror of
      R5's note, attached to the sub-reviewer fallback bullet — anchored
      distinctly from the R4-equivalent citation above).
- [ ] `grep -c "Documentation currency\|AGENTS.md's Map" codex/.agents/skills/build/SKILL.md`
      → 1 or more (R6's codex leg: the inlined reminder, since codex has
      no `quality-discipline.md` to cite).
- [ ] `grep -c "not by \$code-review itself" codex/.agents/skills/build/SKILL.md`
      → 1 or more (confirmed absent today; R6's codex leg equivalent of
      R5's note, attached to the `$code-review` invocation — anchored on
      codex's own invocation phrasing so this AC verifies independently
      of the inlined-reminder AC above, rather than sharing its anchor).
- [ ] `.claude-plugin/plugin.json`'s `version` (currently `"0.9.1"` as of
      2026-07-13, confirmed via `grep -n '"version"' .claude-plugin/plugin.json`
      — re-check at implementation time, this drifts often) is higher
      after this change (R7).
- [ ] `build` is one of the four ultra-path skills (critique, drain, build,
      idea) — `bash evals/lint-ultra-gate.sh` must stay green after this
      edit (the "ultra"/"active runtime profile" markers this gate checks
      sit far from the close-out edits above, but the gate must be run,
      not assumed).
- [ ] **Manual-pending** (cannot be verified by an unattended
      worker/verifier, since `/build` is `disable-model-invocation` —
      per CLAUDE.md, acceptance must not gate on a skill unattended
      workers can't invoke): a human runs `/build` on a fixture task that
      adds a new top-level directory with no `AGENTS.md` mention in the
      task's `Touch:` header, and confirms the completed task's commit
      includes an `AGENTS.md` Map update — because the new
      quality-discipline.md check fired at completion time, not because
      the task file asked for it. Record the observation in the task's
      evidence, not as an automated check.

## Open questions

(none)
