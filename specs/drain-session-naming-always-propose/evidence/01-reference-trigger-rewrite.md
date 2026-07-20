# Verification evidence — task 01: reference.md trigger rewrite

Verdict: PASS

## Environment

- Worktree root: /home/user/claude/.claude/worktrees/agent-a99ba38e6d76f8a35
- Base commit for diff: f9778021fffd610c79304d445ab9cf463de2d7ec
- Implementation commit found: 5a689b9 "docs: drain naming advisory fires per-session, not per-generation"

## Criterion 1

Command: `grep -c "regardless of the adopted owner lease's" .claude/skills/drain/reference.md`
Result: 1 (≥ 1 required) — PASS
Match is in the "Name the shell" closing sentence (line ~82): "Fires once per
session — the first time THIS conversation reaches step 1, regardless of the
adopted owner lease's `Generation:` number..."

## Criterion 2

Command: `grep -c "states its own more precise trigger" .claude/skills/drain/reference.md`
Result: 1 (≥ 1 required) — PASS
Match is in the "Gen-1 startup advisories" opening paragraph (line ~58):
"**Name the shell** below states its own more precise trigger, independent
of this paragraph's `Generation:`-based gate — read its closing sentence,
not this one, for when it fires."

## Criterion 3

Command: `grep -c 'never re-set on baton generations' .claude/skills/drain/reference.md`
Result: 0 (0 required) — PASS
The old unqualified clause ("Once, never re-set on baton generations (they
inherit it), skip silently with no TTY.") is gone, replaced by the new
closing sentence quoted above.

## Criterion 4 (semantic, end-to-end)

Read ONLY the "Gen-1 startup advisories" opening paragraph (lines 50-60) and
the "Name the shell (best-effort)" sub-section (lines 62-88) as a fresh
reader with no other context.

Text derived rule: the opening paragraph states the four advisories run at
gen-1 startup ONLY (never on baton generations) as the DEFAULT gate, but
explicitly carves out Name the shell as having "its own more precise
trigger" and directs the reader to Name the shell's own closing sentence.
That closing sentence states: fires once per session, the first time THIS
conversation reaches step 1, "regardless of the adopted owner lease's
`Generation:` number (a session-refreshed drain that adopts a mid-flight
lease at `Generation: 3` still proposes on its first pass)." It skips only
if (a) the tab already has a custesponding custom name this session, or
(b) there is no TTY — explicitly listing "a detached headless baton
self-relaunch (`nohup`) or an awaited subagent spawn" as the no-TTY cases.

(a) Scenario: human opens a new terminal, starts a /drain session that
adopts an existing in-progress owner lease at `Generation: 3` left by an
earlier session-refreshed session.
Classification derived from text: PROPOSES a name — this is a human-driven
new conversation reaching step 1 for the first time, with a TTY and no
custom name yet set this session; the text's own worked example
("a session-refreshed drain that adopts a mid-flight lease at
`Generation: 3` still proposes on its first pass") maps directly onto this
scenario.
Matches expected outcome (proposes a name): YES.

(b) Scenario: drain's own baton mechanism self-relaunches a successor
generation headlessly via `nohup`.
Classification derived from text: DOES NOT PROPOSE — explicitly named in
the no-TTY skip clause: "a detached headless baton self-relaunch (`nohup`)
... has neither [a custom name nor a TTY], so the no-TTY check alone
already excludes every relaunch path."
Matches expected outcome (does not propose, no TTY): YES.

No ambiguity found: both the opening-paragraph pointer clause and the
closing sentence's worked examples map unambiguously onto both test
scenarios without requiring outside context.

## Touch discipline

Command: `git diff --numstat f9778021fffd610c79304d445ab9cf463de2d7ec -- .`
Result:

```
14	3	.claude/skills/drain/reference.md
```

Only .claude/skills/drain/reference.md is modified — matches the task's
Touch line exactly. `git status --short` shows a clean tree (change is
already committed as 5a689b9). `git diff f9778021... -- '*/tasks/*.md'`
shows no diff at all — the task file's own Status/checkbox bookkeeping has
not been touched, and no other spec's task file was modified either
(append-only discipline intact).

## Sanity check on surrounding prose

Read lines 50-90 in full. The opening paragraph reads coherently with the
new pointer clause appended as a final sentence ("**Name the shell** below
states its own more precise trigger... read its closing sentence, not this
one, for when it fires."). The "Name the shell" sub-section's mechanism
paragraph (custom OSC escape / `/rename` discussion, lines 62-81) is
unchanged and flows directly into the new closing sentence ("Fires once per
session...") without any dangling fragment or broken reference. No orphaned
half-sentences found from the edit.

## Gates

No repo-wide build/lint/test gate applies to a single markdown reference
file edit beyond the mirror-procedure-coverage heuristic, which is out of
this task's Touch (task explicitly restricts to reference.md only per its
own Touch section, disjoint from SKILL.md/antigravity mirror tasks 02/03).
Not run, as those files are unmodified and unrelated to this task's scope.

## Scope-creep check

Diff is limited to the "Gen-1 startup advisories" section text described in
the task's Steps; no other section of reference.md, and no other file, was
touched.
