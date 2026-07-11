# Task 07: End-to-end verification sweep and plugin.json version bump

Status: done
Depends on: 01, 02, 03, 04, 05, 06
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (all requirements — acceptance criteria; CLAUDE.md authoring conventions on plugin.json version bumps)
Touch: .claude-plugin/plugin.json

## Goal

All six preceding tasks are merged. This task runs the full spec-level
acceptance sweep (every checkbox in `../SPEC.md`'s Acceptance criteria
section) against the merged state, fixes any gap it finds, and bumps
`.claude-plugin/plugin.json`'s `version` once — per this repo's CLAUDE.md
authoring convention that a spec touching `.claude/skills/` files carries
the mirror + plugin.json bump in one closing task's `Touch:`, rather than
in every task that touches a mirror.

## Touch

This task's only content edit is the `version` field bump in
`.claude-plugin/plugin.json`. It may read (not edit) any other file in the
repo while running the verification sweep; if the sweep finds a genuine gap
in a prior task's work, fix it in the file that task owns, not here — flag
it in Progress instead if the fix is nontrivial.

## Steps

1. Confirm tasks 01-06 are all merged (Status: done) before starting.
2. Run each acceptance-criteria command from `../SPEC.md`'s Acceptance
   criteria section against the current repo state:
   - The `rg -Un --pcre2` git-command-span detector across every R1-scope
     file.
   - The evals/reference.md untouched-diff check (decision 6).
   - The concurrent-sessions.md, gate/SKILL.md, gate/reference.md,
     critic.md/scout.md grep checks (R2, R4, R5).
   - The R6 mirror-mapping check (each listed counterpart has a non-empty
     diff; each "no counterpart" row has no mirror file created) —
     **except** the three rows verified in the spec's own inventory to be
     correctly unchanged: `workflows/critique.md` (0 git hits, no edit
     needed unless the Claude-side edit introduced a mismatch — verify
     still 0, don't require a diff), `antigravity/.agents/skills/gate/SKILL.md`
     (decision 3: no git-hook callout needed there, different mechanism),
     and `skills/scout/SKILL.md` (0 git hits, R4's frontmatter-note doesn't
     apply). For these three, a non-empty diff is not required — confirm
     "still correctly 0 hits" instead of "diff is non-empty".
   - `python3 antigravity/.agents/skills/workboard/test_workboard.py` (R7).
   - The global-file and antigravity/README.md grep checks (R8, R9).
3. If any check fails, note it in Progress rather than silently patching
   another task's Touch scope — this task's own edit budget is the
   version bump only.
4. Bump `.claude-plugin/plugin.json`'s `version` field (patch or minor bump,
   matching this repo's existing versioning convention).

## Acceptance

- [x] All Acceptance-criteria commands from `../SPEC.md` pass against the
      merged repo state (paste each command's pass/fail into Progress).
- [x] `git show <base-commit>:.claude-plugin/plugin.json | grep version`
      differs from the current `version` value in
      `.claude-plugin/plugin.json` (version was bumped from this task's own
      base commit, not compared to a hard-coded literal).

## Progress

Verification sweep run against merged state (base commit
`bcd5953`); all six preceding tasks confirmed Status: done. SPEC.md
Acceptance-criteria results:

- **R1 git-command-span detector** (`rg -Un --pcre2 '`git[^`]*`'` over every
  R1-scope file) — PASS. Every flagged span in drain/SKILL.md,
  drain/reference.md, autopilot/reference.md, build/SKILL.md,
  breakdown/SKILL.md, onboard/SKILL.md, fleet/SKILL.md, critique/SKILL.md
  carries an "e.g., under git:" label on its starting line, or is the named
  decision-4 exempt line (drain/reference.md:161 `git update-ref`, labeled
  "a git-specific mechanic, kept literal on purpose"). gate/SKILL.md and
  gate/reference.md: 0 hits. The two workboard/reference.md hits
  (`gitBranch` at :21, `git` field at :57) are data-structure field names,
  not shell-executable `git <subcommand>` command spans — outside R1's
  bright line (VCS nouns retained as vocabulary); the actual `git -C` /
  `git rev-parse` command spans the addendum flagged were already rewritten
  by task 05.
- **Decision-6 evals/reference.md untouched** — PASS.
  `diff <(git show HEAD:...evals/reference.md) ...evals/reference.md` empty.
- **R2 concurrent-sessions.md** — PASS. Only remaining `git status` hit
  (line 16) is inside a labeled "e.g., under git:" example with intent-level
  phrasing preceding.
- **R4 critic.md/scout.md deferred-gap note** — PASS. Both carry `jj` +
  `git-specific` notes outside the unchanged `tools:` frontmatter.
- **R5 gate callouts** — PASS. gate/SKILL.md has the "pre-commit hook
  mechanism is git-specific" callout (lines 40-43); gate/reference.md and
  its antigravity mirror both carry the `git-specific` pattern-string note.
- **R6 mirror mapping** — PASS. All 8 counterpart rows requiring a diff
  (workflows/drain.md, autopilot.md, build.md; skills/breakdown, onboard,
  gate/reference.md, verifier, critic) have non-empty diffs vs the
  pre-spec baseline (`4ce7916^`). The three exempt rows
  (workflows/critique.md, antigravity gate/SKILL.md, antigravity
  scout/SKILL.md) confirmed still correctly 0 git-command spans. The three
  no-counterpart rows (fleet, rules/, evals reference.md) confirmed no
  mirror file/dir exists.
- **R7 workboard test** — PASS. `python3 ...workboard/test_workboard.py`:
  104 tests OK, including `test_jj_only_directory_is_detected_as_repo_root`.
- **R8 global CLAUDE.md files** — PASS. `grep 'git pre-commit hook'` returns
  no hits in either global file.
- **R9 antigravity/README.md** — PASS. `grep 'git add .agents\|git commit
  -m'` returns no hits.
- **E2E narrative criterion** — satisfied by inspection: gate/SKILL.md
  states the hook mechanism is a git-specific known gap; drain/reference.md
  labels the update-ref plumbing line; drain/SKILL.md uses intent-level
  "e.g., under git:" framing for commit/push/worktree actions.

Version bump: `.claude-plugin/plugin.json` `version` 0.8.41 → 0.8.42 (patch
bump per repo convention). Base value read from this task's own base commit,
not hard-coded. No gaps found; no other task's Touch scope edited.
