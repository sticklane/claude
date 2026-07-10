# Task 01: drain fetches and checks for remote divergence before trusting its local view

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R5, R6, R7, R8)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, antigravity/.agents/workflows/drain.md, .claude-plugin/plugin.json

## Goal

Before step 1's Status-header read, drain runs `git fetch <remote>` and
compares local `main` against `<remote>/main`: no remote configured or a
transient fetch failure both degrade to today's behavior (skip / warn and
continue); new remote commits with no local unpushed commits fast-forward
local `main` before the header read; true divergence (both sides have
commits the other lacks) halts this invocation and reports it as a
final-message blocker, never a live interactive prompt. `SKILL.md` gains
only a single pointer line for this, paired with an unconditional
compensating trim so the file keeps genuine headroom under 500 lines; the
full procedure lives in `reference.md`'s "Owner lease" section. The
antigravity mirror carries the equivalent contract in its own voice, and
`plugin.json`'s version is bumped — all in this one commit.

## Touch

Do not touch `.claude/skills/drain/screen-stub.sh` or any stub-intake /
critique-intake procedure text — this task only changes step 1's
Status-header-read entry point, per the spec's Out of scope (closing the
3b/critique-intake/stub-intake ordering gap is explicitly out of scope;
document it as an accepted gap in reference.md if not already covered by
the spec's own Out-of-scope text, do not attempt to fix it). Do not touch
the existing push guard's own text/behavior — only reuse its no-remote
and fetch-failure handling as a model. Do not touch
`.claude/rules/concurrent-sessions.md` — this task cites it, not edits it.

## Steps

1. Read `.claude/skills/drain/SKILL.md` in full (current line count via
   `wc -l`) to find step 1's current Status-header-read entry point (the
   spec's Solution describes it as preceding the owner-lease claim) and
   the existing push guard's exact no-remote/fetch-failure wording
   (reused as the model for R1's two branches).
2. Read `.claude/skills/drain/reference.md`'s "Owner lease" section in
   full to find the right insertion point for the new procedure.
3. Write the full fetch/compare/fast-forward/halt procedure into
   reference.md's "Owner lease" section per R1-R5: the two skip/warn
   branches (no remote vs. fetch failure), the no-new-commits pass-through,
   the fast-forward-only path, and the halt-and-report-as-final-message
   path for true divergence (never a live AskUserQuestion in the
   unattended default — an attended session may choose to ask instead, at
   its own discretion, not mandated by this text).
4. Add a single pointer line to SKILL.md's step 1, before the
   Status-header read, naming the check and pointing to reference.md.
   Measure the file's new line count; if it does not leave genuine
   headroom under 500 (per R6, unconditional trim — do not land at
   exactly 500), trim an equal-or-greater number of lines elsewhere in
   SKILL.md (tightening existing prose, not deleting content) in this
   same commit.
5. Port the equivalent contract into
   `antigravity/.agents/workflows/drain.md` in that mirror's own
   paraphrased voice (per docs/memory/workboard-mirror-verbatim.md —
   prose-skill mirrors are paraphrased ports, not byte-identical copies).
6. Bump `.claude-plugin/plugin.json`'s version.
7. Verify: read back the edited reference.md section and confirm it
   states all of R1's two branches, R3's fast-forward, and R4's
   halt-not-live-prompt mechanism explicitly — these are prose-consistency
   checks on the text you wrote, not runtime behavior to execute live.
8. If practical within budget, exercise the fast-forward path (R3) against
   a scratch git repo (two clones of a throwaway repo, one ahead of the
   other, no local unpushed commits on the behind side) to confirm the
   documented `git fetch` + `git merge --ff-only` sequence actually
   fast-forwards cleanly. If impractical within budget, rely on the
   prose-inspection checks and say so in Done vs remaining.

## Acceptance

- [ ] `.claude/skills/drain/SKILL.md`'s step 1, before the Status-header
      read, names the remote divergence check in a single pointer line to
      reference.md.
- [ ] `wc -l .claude/skills/drain/SKILL.md` stays strictly below 500 —
      confirm the commit paired the addition with an unconditional
      compensating trim (not landing at exactly 500).
- [ ] `grep -c 'fetch' .claude/skills/drain/reference.md` → at least one
      match in the Owner lease section referencing this check.
- [ ] reference.md's Owner lease section states, in prose, all of: the
      no-remote-configured skip, the fetch-failure-with-configured-remote
      warn-and-continue (as two DISTINCT branches, not conflated), the
      fast-forward-before-the-header-read path, and the
      halt-and-report-as-final-message path for true divergence (never a
      live interactive prompt in the unattended default).
- [ ] `git diff HEAD~1 -- antigravity/` → shows `antigravity/.agents/workflows/drain.md`
      changed, carrying the same core concepts (fetch before the header
      read, fast-forward-if-clean, halt-if-diverged) in its own paraphrased
      voice — a content-coverage grep, not a byte-identical diff.
- [ ] `git diff HEAD~1 -- .claude-plugin/plugin.json | grep '"version"'`
      shows the version increased.
- [ ] `git diff HEAD~1 -- .claude/skills/drain/screen-stub.sh` → empty (not
      touched).
