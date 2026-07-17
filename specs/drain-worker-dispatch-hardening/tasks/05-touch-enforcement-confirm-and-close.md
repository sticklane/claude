# Task 05: Touch-enforcement confirm-don't-fix, mirror sweep, and version bump

Status: done
Depends on: 01, 02, 03, 04
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirement R5, plus closing obligations)
Touch: .claude/skills/drain/SKILL.md, antigravity/.agents/workflows/drain.md, codex/.agents/skills/drain/SKILL.md, .claude-plugin/plugin.json

<!-- plan
1. Confirm (don't take SPEC on faith) that SKILL.md:194's `$(git merge-base …)`
   runs in drain's own orchestrator session (step 3 "Collect the verdict",
   merge/verdict time = hub action), NOT a worker's `dontAsk` dispatch.
   Evidence: reference.md:141-151 ("the hub never pulls the worker's diffs …")
   and Headless-fallback lines 1039-1082 (worker prompt is the impl dispatch;
   line 1080-1082 says workers under dontAsk avoid command substitution).
2. Document the confirm-don't-fix finding as a short note at SKILL.md:194.
3. Port the note into antigravity drain.md (~L451) and codex SKILL.md (~L237).
4. Bump plugin.json version (base 0.9.15 → 0.9.16).
5. Mirror-obligation manual check over all task Touch lines (all pass) +
   task 02 canonical-allowlist antigravity port reads sensibly (no adjust).
6. Commit. FORK TAKEN: confirm, don't fix.
-->

## Goal

R5's `$(git merge-base …)` command-substitution shape at
`.claude/skills/drain/SKILL.md:206` is documented rather than rewritten
(per the spec's Open Questions resolution: this check runs in drain's own
orchestrator session during "Collect the verdict", never inside a
dispatched worker's restrictive `dontAsk` invocation, so it is confirmed
safe as-is). The spec's mirror obligations and plugin version bump land
in this closing task, after every other task's edits are in.

## Touch

Depends on tasks 01-04 all landing first: this is the only task that
touches `.claude/skills/drain/SKILL.md` directly, but every other task in
this spec also writes into `antigravity/.agents/workflows/drain.md` (the
same mirror file, different sections) — running this task last avoids
stacking a fifth concurrent edit onto that file and lets the closing
manual mirror-obligation check (see Acceptance) inspect the finished
state of all four prior tasks at once.

## Steps

1. Read `.claude/skills/drain/SKILL.md` around line 206 (the
   Touch-enforcement check, step 3 "Collect the verdict") and confirm
   directly — do not take the SPEC.md's Open Questions resolution on
   faith — that this check executes in drain's own orchestrator session
   and not inside a worker's `claude -p --permission-mode dontAsk`
   dispatch (`reference.md`'s Headless fallback section).
2. Add a short note at or near SKILL.md:206 documenting this finding:
   the command-substitution shape is confirmed to run under drain's own
   (non-restrictive) session, not a worker's `dontAsk` mode, so it is
   intentionally left as-is rather than rewritten. Record in this task's
   own commit message (and its `## Progress` evidence) that the
   "confirm, don't fix" branch was taken — this is the fork the spec's
   acceptance criteria track, not a fixed literal outcome.
3. Port this note into `antigravity/.agents/workflows/drain.md` at its
   corresponding `$(git merge-base …)` line (confirmed by the spec's
   Mirror obligations research at drain.md:369), and into
   `codex/.agents/skills/drain/SKILL.md` at its corresponding line
   (confirmed at codex/.agents/skills/drain/SKILL.md:188) — both are
   mandatory since this task touches `.claude/skills/drain/SKILL.md`
   directly.
4. Bump `.claude-plugin/plugin.json`'s `version` (patch bump at minimum;
   this spec's changes are behavior-affecting skill-body edits). Compare
   against the value at this task's own base commit, not a hardcoded
   literal — a sibling task elsewhere in the repo may have already bumped
   it past whatever value you observe first.
5. Perform the spec's mirror-obligation manual check: for every task file
   under `specs/drain-worker-dispatch-hardening/tasks/*.md` whose `Touch:`
   includes `.claude/skills/drain/reference.md` or
   `.claude/skills/drain/SKILL.md`, confirm its `Touch:` also lists
   `antigravity/.agents/workflows/drain.md`; for any whose `Touch:`
   includes `.claude/skills/drain/SKILL.md`, confirm it also lists
   `codex/.agents/skills/drain/SKILL.md`; for task 04 specifically,
   confirm its `Touch:` lists `antigravity/.agents/skills/breakdown/SKILL.md`.
   Record the result of this manual check in this task's `## Progress`.
   Also confirm task 02's "canonical worker allowlist" phrase ported into
   `antigravity/.agents/workflows/drain.md` resolves sensibly there (it
   references a template that lives only in `runtimes/claude-code.md`,
   a Claude-runtime file) rather than merely passing its phrase-grep — if
   it reads as a dangling reference for an antigravity reader, adjust the
   wording in this task rather than leaving it.
6. Commit.

## Acceptance

- [x] `grep -c '\$(git merge-base' .claude/skills/drain/SKILL.md` → 1 (the check persists, confirm-don't-fix branch), and a nearby note documents the orchestrator-session finding — inspect by hand, not a single grep — evidence: SKILL.md:194 note added, grep → 1
- [x] `git show <this-task's-commit> -- .claude-plugin/plugin.json | grep -q '^+.*"version"'` → match — evidence: version 0.9.15 → 0.9.16
- [x] `grep -l "drain/reference.md\|drain/SKILL.md\|breakdown/SKILL.md" specs/drain-worker-dispatch-hardening/tasks/*.md` cross-checked by hand against each matching task's `Touch:` list → every match satisfies the mirror-obligation rule above (MANUAL: breakdown-time/closing-time review, not a standalone runnable command) — evidence: see ## Progress
- [x] `grep -c '\$(git merge-base' antigravity/.agents/workflows/drain.md codex/.agents/skills/drain/SKILL.md` → at least 1 in each, with the same documenting note ported — evidence: both → 1, identical note ported

## Progress

Fork taken: **confirm, don't fix** (per SPEC Open Questions resolution).

Confirmation (step 1, not taken on faith): SKILL.md:194's `$(git merge-base …)`
sits in `## 3. Collect the verdict` → DONE bullet, a merge/verdict-time HUB
action. reference.md:141-151 pins this as "at merge/verdict time the hub never
pulls the worker's diffs" — the hub runs the diff, not a worker. The worker's
own dispatch is the Headless-fallback `claude -p … --permission-mode dontAsk`
prompt (reference.md:1039-1061); reference.md:1080-1082 states workers under
`dontAsk` avoid command substitution via the known-safe shell-pattern guidance.
Therefore the command substitution is safe as-is; left unrewritten by design.

Mirror-obligation manual check (step 5) — all matching tasks satisfy the rule:

- 01: Touch has drain/reference.md → lists antigravity drain.md ✓ (no SKILL.md → no codex req)
- 02: Touch has drain/reference.md → lists antigravity drain.md ✓ (no drain/SKILL.md → no codex req)
- 03: Touch has drain/reference.md → lists antigravity drain.md ✓ (no SKILL.md → no codex req)
- 04: matches on breakdown/SKILL.md → lists antigravity/.agents/skills/breakdown/SKILL.md ✓ (breakdown≠drain, no codex-drain req)
- 05: Touch has drain/SKILL.md → lists antigravity drain.md ✓ AND codex drain/SKILL.md ✓

Task 02 "canonical worker allowlist" antigravity port (drain.md:279-284) reads
sensibly: frames `runtimes/claude-code.md`'s template as "a cross-runtime
reference point only" and states Antigravity grants tools per-launch via the
Agent Manager (no template to port verbatim). Not dangling — no adjustment made.
