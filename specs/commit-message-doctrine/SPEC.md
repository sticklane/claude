# Commit-message doctrine: canonical rules, subject-length discipline

Breakdown-ready: true

## Problem

A cross-repo audit (2026-07-16, ~300 recent commits each in claude/hub/fooszone
plus six smaller repos) found 20–35% of agent-authored commits exceed 72-char
subjects, with fooszone merge commits reaching 200–300 chars—ratification
notes, verifier evidence, and audit notes packed into the subject line, making
`git log --oneline` and terminal history unreadable. Bodies are already healthy
(~70–75% of commits carry informative why/context bodies), so the detail has a
home; the toolkit just never says to put it there. The guidance is scattered
and incomplete: `.claude/rules/quality-discipline.md` pins `<type>: <subject>`
and the type list but no length or body rule; the drain skill pins only the
in-progress flip message (`drain: <spec-slug> task NN in-progress`,
SKILL.md:166—regex-load-bearing for diff-base recovery) and is silent on
merge, baton-pass, and bookkeeping commit wording, so workers default to
detail-in-subject; the build skill's commit step (SKILL.md:247) prescribes no
format at all; and the orchestration prefixes that dominate agent-heavy repos
(`drain:` is 59–72% of commits in ~/automation and ~/specs) appear nowhere in
the canonical rules.

## Solution

Make the `## Commits` section of `.claude/rules/quality-discipline.md` (line
33, file is 64 lines) the single canonical commit doctrine: add the
subject-length rule (72 target, hard cap 100), the detail-goes-in-body rule
(named throughout as the "subject/body split"), the sanctioned orchestration
prefixes with the regex-pinned flip contract called out, and the trailer
expectation. Mirror the new rules compactly into `antigravity/AGENTS.md`'s
commits bullet (line 126, file is 185 lines, ≤200 cap). Add explicit
subject/body-split guidance where drain is currently silent: the step-3 merge
instruction in `.claude/skills/drain/SKILL.md` (~line 207), the baton-pass
step (SKILL.md §3a, ~line 290), and the bookkeeping-commit guidance in
`.claude/skills/drain/reference.md`. Point the build skill's commit bullet
(`.claude/skills/build/SKILL.md:247`) at the doctrine. Per CLAUDE.md's mirror
mandate, the drain/build skill edits are mirrored in the same task into
`antigravity/.agents/workflows/{drain,build}.md` and
`codex/.agents/skills/{drain,build}/SKILL.md`, with a `plugin.json` version
bump (currently 0.9.16); the task carrying those edits lists every mirror
path plus `.claude-plugin/plugin.json` in its `Touch:`. Docs and templates
only—no hook or lint machinery.

## Requirements

R1: The `## Commits` section of `.claude/rules/quality-discipline.md` states
the subject-length rule—target ≤72 characters, hard cap 100—and the
subject/body split: the subject states what changed; ratification notes,
verifier evidence, audit notes, acceptance detail, and multi-clause context
go in the commit body, never the subject.

R2: The same section lists the sanctioned orchestration prefixes (`drain:`,
`merge:`, `spec:`, `breakdown:`) as legitimate alongside the conventional
types, and marks `drain: <spec-slug> task NN in-progress` as a regex-pinned
machinery contract (singular "task", literal wording—drain's diff-base
recovery greps for it) that the length rule must never cause an agent to
reword.

R3: The same section states the trailer expectation: agent-authored commits
keep the harness-provided `Co-Authored-By` trailer; trailer wording follows
the repo/harness, and agents never strip it.

R4: The commits bullet in `antigravity/AGENTS.md` mirrors R1's length rule
and subject/body split and R2's prefix sanction in compact form, and the
file stays ≤200 lines.

R5: Drain's step-3 merge instruction in `.claude/skills/drain/SKILL.md`
prescribes an explicit merge-commit format: subject
`merge: <spec-slug> task NN — <short what>` within the cap, with ratified
riders, audit notes, and acceptance evidence in the body (the subject/body
split).

R6: Both `.claude/skills/drain/SKILL.md` (the §3a baton-pass step) and
`.claude/skills/drain/reference.md` (its bookkeeping-commit guidance) state
the subject/body split for baton-pass and bookkeeping commits—short subject,
verdict/lease detail in the body—while leaving the pinned flip contract
(SKILL.md:166) and the auto-breakdown message
(`drain: auto-breakdown specs/<slug> (N tasks)`, reference.md:1570) verbatim.

R7: The build skill's commit bullet in `.claude/skills/build/SKILL.md`
references the canonical doctrine: a type-prefixed subject per
quality-discipline.md's `## Commits`, subject/body split for detail.

R8: Every example commit message prescribed in the files this spec touches
(including `reference.md` and all four mirror files) has a subject ≤100
characters.

R9: The drain/build skill edits from R5–R7 are mirrored into
`antigravity/.agents/workflows/drain.md`,
`antigravity/.agents/workflows/build.md`,
`codex/.agents/skills/drain/SKILL.md`, and
`codex/.agents/skills/build/SKILL.md`, and `.claude-plugin/plugin.json`'s
version is bumped above 0.9.16; the task carrying these edits lists all five
paths in its `Touch:` alongside the skill files they mirror.

## Out of scope

- Changing the `drain:` prefix, the pinned flip-message regex contract, or
  the auto-breakdown message wording.
- Retrofitting existing commit history in any repo.
- Hook or lint enforcement (e.g., a /gate commit-msg subject-length check)—
  deliberately excluded per interview; may be a future spec.
- Vault/personal-skill auto-commit noise (daily-sync, shutdown)—not toolkit.
- The user's global `~/.claude/CLAUDE.md` commit section (dotfiles repo, not
  this one).

## Acceptance criteria

- [ ] `grep -c 'hard cap 100' .claude/rules/quality-discipline.md` ≥ 1 and
      `grep -ci 'body' .claude/rules/quality-discipline.md` ≥ 1 (covers R1;
      both phrases absent today—`hard cap` count 0, `body` count 0—verified
      2026-07-17).
- [ ] `grep -c 'drain: <spec-slug> task NN in-progress' .claude/rules/quality-discipline.md` ≥ 1,
      `grep -c 'regex' .claude/rules/quality-discipline.md` ≥ 1, and
      `grep -c 'breakdown:' .claude/rules/quality-discipline.md` ≥ 1 — the
      prefix list actually landed (covers R2; `drain:` and `breakdown:` both
      absent from the file today, verified 2026-07-17).
- [ ] `grep -ci 'Co-Authored' .claude/rules/quality-discipline.md` ≥ 1
      (covers R3; absent today, verified 2026-07-17).
- [ ] `grep -c 'hard cap 100' antigravity/AGENTS.md` ≥ 1,
      `grep -c 'subject/body' antigravity/AGENTS.md` ≥ 1, and
      `wc -l < antigravity/AGENTS.md` ≤ 200 (covers R4; `hard cap` and
      `subject/body` counts both 0 today, verified 2026-07-17).
- [ ] `grep -c 'merge: <spec' .claude/skills/drain/SKILL.md` ≥ 1 (covers R5;
      absent today, verified 2026-07-17).
- [ ] `grep -ci 'subject/body' .claude/skills/drain/SKILL.md` ≥ 2 (one hit
      in R5's merge step, one in R6's §3a baton-pass step—a single hit means
      one of the two edits was skipped) and
      `grep -ci 'subject/body' .claude/skills/drain/reference.md` ≥ 1
      (positive check for R5+R6's content; phrase absent from both files
      today, verified 2026-07-17).
- [ ] `grep -c 'drain: <spec-slug> task NN in-progress' .claude/skills/drain/SKILL.md` ≥ 1
      and `grep -c 'drain: auto-breakdown specs/<slug>' .claude/skills/drain/reference.md` ≥ 1
      still hold after the edits—both pinned contracts survive verbatim
      (covers R6's guard; both present today: SKILL.md:166,
      reference.md:1570).
- [ ] `grep -A3 'Commit code' .claude/skills/build/SKILL.md | grep -c 'quality-discipline'` ≥ 1
      — the doctrine reference sits inside the commit bullet itself, not
      elsewhere in the file (covers R7; `Commit code` anchors the bullet at
      line 247 today and the piped count is 0 today, verified 2026-07-17).
- [ ] Each of the four mirror files contains the ported guidance:
      `grep -cil 'subject/body' antigravity/.agents/workflows/drain.md antigravity/.agents/workflows/build.md codex/.agents/skills/drain/SKILL.md codex/.agents/skills/build/SKILL.md | wc -l` — all
      four match, i.e. `grep -li` lists 4 files (covers R9; phrase absent
      from all four today, verified 2026-07-17). And
      `grep -o '"version": "[^"]*"' .claude-plugin/plugin.json` shows a
      version greater than 0.9.16 (0.9.16 today, verified 2026-07-17).
- [ ] End-to-end: extracting every backtick-quoted example commit message
      whose text matches `^(drain|merge|feat|fix|test|refactor|docs|style|perf|chore|spec|breakdown): `
      from all touched files shows no subject over 100 characters (covers
      R8). The following command exits 0 (copy-paste runnable from the repo
      root; the 102 threshold accounts for the two captured backticks):

      ```sh
      grep -rhoE '`(drain|merge|feat|fix|test|refactor|docs|style|perf|chore|spec|breakdown): [^`]+`' \
        .claude/rules/quality-discipline.md antigravity/AGENTS.md \
        .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md \
        .claude/skills/build/SKILL.md \
        antigravity/.agents/workflows/drain.md \
        antigravity/.agents/workflows/build.md \
        codex/.agents/skills/drain/SKILL.md \
        codex/.agents/skills/build/SKILL.md \
        | awk '{ if (length($0) > 102) { print; bad=1 } } END { exit bad }'
      ```

## Open questions

(none)

## Parallelization

Two tasks, strictly serial: task 02 depends on task 01 (the skill edits
reference the doctrine section task 01 writes, and both use its terms).
No concurrent-safe groups (format per
`specs/drain-rolling-window/SPEC.md`'s `## Parallelization` section — no
`- Group:` lines means every task runs solo).
