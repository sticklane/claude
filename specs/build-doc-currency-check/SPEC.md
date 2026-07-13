# Documentation-currency check in /build's completion step

## Problem

The original ask was to make documentation updates "part of the code
review phase" — but `/code-review` is provided by the harness/an external
plugin (there is no `.claude/skills/code-review/` in this repo, and
`docs/anthropic-playbook.md`/`build/SKILL.md:86` both treat it as an
external command this repo invokes, not one it defines), so it isn't a
file this repo can edit. What this repo *does* own is `/build`'s completion
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
  currency" section stating: before finishing a task, check whether the
  diff invalidates `AGENTS.md`'s Map (new/moved/removed top-level
  components), Commands (a documented command's behavior or invocation
  changed), or State sections, or anything README.md tells an end user —
  if so, update it in the same commit.
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
  pre-commit review bullet (currently ~line 77, adjacent to the
  `/code-review` invocation R5 touches), cites this new
  quality-discipline.md section (one line, e.g. "check documentation
  currency per quality-discipline.md") rather than restating its content
  — both R4's citation and R5's note land at the same bullet, not
  scattered across section 4's other close-out steps (simplify,
  task-file update, commit).
- **R5**: The nearby `/code-review` invocation (currently
  `.claude/skills/build/SKILL.md:86`, via the Skill tool, args `low`,
  with a documented fallback "where the Skill tool or plugin is
  unavailable") is the one place a reader could plausibly assume this
  repo owns doc-currency checking through that invocation. Add a
  one-line note there: doc currency is checked by the new
  quality-discipline.md section (R1), not by `/code-review` itself —
  `/code-review` stays scoped to what the harness/plugin defines it to
  check.
- **R6**: Per CLAUDE.md's mirroring convention ("when a skill changes
  here, mirror the change there in the same commit"), both edits land in
  their antigravity mirrors too: `antigravity/.agents/workflows/build.md`
  (mirrors `build/SKILL.md`, including its close-out review logic) gets
  the same R4 citation; R5's note attaches differently there, since that
  mirror has no `/code-review` call at all (`workflows/build.md:63`
  already reads "since this mirror has no code-review skill to..." and
  falls back to a subagent reviewer instead) — the R5-equivalent note
  attaches to that sub-reviewer fallback bullet, not to a `/code-review`
  invocation that doesn't exist in this mirror. `antigravity/AGENTS.md`'s
  `## Quality discipline` section (mirrors `quality-discipline.md`) gets
  the same new
  "Documentation currency" content from R1.
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

- [ ] `.claude/rules/quality-discipline.md` contains the new
      "Documentation currency" section with the exact check described in
      R1.
- [ ] `.claude/skills/build/SKILL.md` contains a one-line citation to that
      section in its completion step.
- [ ] `.claude/skills/build/SKILL.md`'s `/code-review` invocation point
      carries the one-line note from R5, stating doc-currency checking
      lives in quality-discipline.md, not in `/code-review`.
- [ ] `antigravity/.agents/workflows/build.md` and `antigravity/AGENTS.md`
      contain the same R4/R5/R1 additions as their `.claude/` counterparts
      (R6).
- [ ] `.claude-plugin/plugin.json`'s `version` is higher than before this
      change (R7).
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

## Critique findings (2026-07-13)

Verdict: **NOT READY**

### 1. R6 omits the mandatory codex mirror leg for a build/SKILL.md change — confidence 88
The spec changes `.claude/skills/build/SKILL.md` (R4 citation, R5 note), but R6 and the acceptance criteria mirror **only** to antigravity. CLAUDE.md's codex-leg convention is explicit and directly applies here:

> "a task whose `Touch:` changes one of the four `.claude/skills/{drain,build,autopilot,evals}/SKILL.md` files must also carry the matching `codex/.agents/skills/<name>/SKILL.md` update in its `Touch:` (those four are real content, not symlinks)"

`codex/.agents/skills/build/SKILL.md` is real content (not a symlink), with its own `$code-review` invocation and close-out procedure at line 146. This spec touches build's close-out step — exactly the region codex mirrors. As written, `/breakdown` will produce a task set that omits codex, silently shipping un-mirrored per CLAUDE.md's own warning.

**Smallest fix:** Add codex to R6 and to the acceptance criteria: `codex/.agents/skills/build/SKILL.md` gets the R4 citation and the R5-equivalent note (it has a `$code-review` call at line 146, so R5 applies there too, unlike the antigravity mirror).

### 2. Codex has no `quality-discipline.md` to cite — R4's citation is unresolvable there — confidence 82
Codex has no `quality-discipline` rule file, and codex build/SKILL.md never cites `.claude/rules/`. The literal R4 citation points at a file that does not exist in codex's discovery root — a broken cross-reference under the target runtime. The spec must decide how the citation translates for codex (inline the reminder? cite antigravity/AGENTS.md's `## Quality discipline`? omit with rationale?).

**Smallest fix:** In R6, state explicitly how the doc-currency reminder lands in codex given it has no quality-discipline.md (recommend: inline one line, since codex build already inlines rather than citing `.claude/rules/`).

### 3. build is an ultra-path skill; the required `lint-ultra-gate.sh` gate isn't named in verification — confidence 62
CLAUDE.md: "The four ultra-path skills (critique, drain, build, idea) also carry a standalone gate check: run `bash evals/lint-ultra-gate.sh` before committing changes to them." No acceptance criterion names this gate. Risk is low in practice (the "ultra"/"active runtime profile" markers sit far from the section-4 close-out edits), but breakdown won't know to include the gate run unless the spec says so.

**Smallest fix:** Add a verification note: "build is an ultra-path skill — `bash evals/lint-ultra-gate.sh` must stay green after the edit."

### 4. Stale antigravity line reference not covered by the sequencing hedge — confidence 60
The sequencing note's line-number disclaimer is scoped to "every `build/SKILL.md` line reference." R6's `antigravity/.agents/workflows/build.md:63` citation is outside that hedge and is stale (the actual line is ~121).

**Smallest fix:** Extend the sequencing note's "snapshot, not a contract" caveat to cover the antigravity line references too, or drop the `:63`/`:86` numbers in favor of the section-content anchors already given.

Findings 1–2 drive the NOT READY verdict. Fix R6 to cover the codex leg and decide the codex citation translation before this goes to `/breakdown`.
