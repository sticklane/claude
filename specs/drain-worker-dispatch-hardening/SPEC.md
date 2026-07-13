Status: open
Priority: P1

## Problem

A cross-session research sweep of real drain usage (3 different repos)
found two recurring, independent classes of dispatch waste that this
repo's own doctrine already names in principle but does not yet enforce
mechanically:

**Headless/permission allowlist gaps discovered live, never pre-checked.**
Drain's headless fallback and baton self-relaunch (`.claude/skills/drain/
reference.md` "Headless fallback" and "Baton pass (self-relaunch)") pass a
fixed `--allowedTools` list built ad hoc per session, then dispatch. When
the list is missing a tool a pending task's acceptance criteria actually
need, the gap surfaces only as a live BLOCKED verdict from a dispatched
worker — after the wasted run:

- A relaunched headless generation carried an allowlist of only
  `git`/`python3`/`ls`; the worker correctly refused to launder compute
  through `python3` and returned BLOCKED — only then did the orchestrator
  discover every remaining task needed `go`/`bash`/npm too, having already
  burned one full worker dispatch to find out.
- A detached headless run's allowlist denied `go`/`bash`, spuriously
  blocking a sibling spec on environment rather than substance — a later
  session hand-widened its own relaunch's allowlist, but the sibling stayed
  broken because the fix wasn't shared anywhere durable.
- A narrow `--allowedTools` list omitted a pending task's acceptance
  command (`launchctl`), leaving a verifier-passed task BLOCKED for a whole
  generation.
- The sandbox denies `launchctl`/install scripts outright — hit twice, in
  two different sessions, both launchd-class tasks — with no classifier
  anywhere flagging such tasks as unattended-incompatible before dispatch.
- The mandatory stub-screen step (`screen-stub.sh`, SKILL.md:367,
  reference.md:1205) is invoked with a bare script path — but the
  Touch-enforcement check two hundred lines earlier
  (`.claude/skills/drain/SKILL.md:205`) already reaches for `git diff
  $(git merge-base <default-branch> <branch>)..<branch> --` — exactly the
  command-substitution shape a restrictive permission mode denies (see next
  finding), showing the allowlist-incompatible-Bash-shape problem is not
  confined to worker prompts; it reaches drain's own orchestrator-side
  commands too.
- Detached/headless generational relaunch is reported as unreliable or
  outright broken on at least one machine, forcing every drain run there
  into one giant single session that hands off "in-session" at baton
  checkpoints instead of ever refreshing across fresh generations — raised
  6-8 times each across 5 of 7 sessions sampled in that repo. This directly
  works against `.claude/rules/token-discipline.md`'s "Session refresh"
  budget (3 re-primes or 250k tokens before a session must refresh) — a
  mega-session that can never baton-relaunch never gets the intended
  refresh, and re-primes its fat context repeatedly instead.

**Worker shell-pattern pitfalls rediscovered fresh, independently, per
generation.** The Worker prompt (`reference.md:506-631`) already carries a
*reactive* rule for Bash denials — "retry it ONCE as a bare single command
… if it is still denied, stop and report" (reference.md:570-572) — but
states no *proactive* guidance on which shapes get denied in the first
place. Evidence from real sessions:

- Shell permission-mode denials on command substitution (`$(...)`), a
  `for` loop, and multi-verb `&&`-chained commands — hit 5 separate times
  in one session, each requiring a rewritten flatter retry (the reactive
  "retry once bare" rule burned a turn each time before landing on the fix
  the worker then had to re-derive).
  Same shape as the Touch-enforcement `$(git merge-base …)` example above.
- `cmd | ! grep` (invalid negation placement) and `grep -c` exiting 1 on
  zero matches breaking a chained commit — hit independently in two more
  sessions.

Both classes share the same root defect: the dispatch mechanism defers
discovery to a live, wasted worker/generation run instead of checking a
knowable-in-advance fact (the queue's actual required tools; the
permission-mode-safe shell shapes) before dispatch.

## Solution

Four mechanical fixes plus one documented-gap item, scoped to the actual
current structure of `.claude/skills/drain/SKILL.md` and
`.claude/skills/drain/reference.md`:

1. Add an allowlist pre-flight to drain's headless-dispatch and baton
   self-relaunch steps (reference.md "Headless fallback" and "Baton pass
   (self-relaunch)"): before the first `claude -p` invocation of a
   generation, scan the pending tasks' acceptance-criteria commands for
   the tool/command names they invoke and confirm each is covered by the
   `--allowedTools` string about to be used; widen the list (per the
   canonical template from R2) before dispatching rather than after a
   BLOCKED verdict reveals the gap.
2. Add one canonical, tool-complete allowlist template for compute-heavy
   specs (`go`, `bash`, `npm`, `python3`, `git` at minimum, following the
   existing `Bash(<verified test/lint/build cmds>)` placeholder
   convention) to `runtimes/claude-code.md`'s `## Headless` section (the
   file that already defines `<allowlist>`'s shape), and have
   `reference.md`'s Headless fallback and Relaunch command template
   sections reference it by name instead of each session reconstructing
   an allowlist ad hoc.
3. Add a privileged/OS-level task classifier: a task whose acceptance
   commands require `launchctl`, a system installer, or interactive OAuth
   is flagged MANUAL / human-pending at breakdown or drain-intake time
   (mirroring the existing manual-pending escape in
   `docs/memory/unattended-worker-tool-limits.md`), never dispatched to
   fail as BLOCKED inside a generation.
4. Extend the Worker prompt (reference.md:506-631, and the Headless
   fallback's inline prompt at reference.md:892-918, which restates the
   same contract) with proactive known-safe shell-pattern guidance,
   stated once and referenced from both: avoid command substitution
   (`$(...)`), `for` loops, and multi-verb `&&`-chained commands in
   permission-gated Bash calls; use `! cmd | grep -q` rather than `cmd |
   ! grep`; and handle `grep -c`'s exit-1-on-zero-matches explicitly
   (e.g. `grep -c … || true` when zero is an expected outcome) rather
   than letting it break a chained command. This sits alongside, not in
   place of, the existing reactive retry-once-bare-command rule.
5. Document the known headless/detached-relaunch reliability gap. Root
   cause requires live debugging on the affected machine(s), which is out
   of scope for spec-authoring — see Open questions.

### Mirror obligations

Requirement 4 touches the Worker prompt in `.claude/skills/drain/
reference.md`, which is restated (not merely referenced) in the headless
fallback template and is itself the source drain's dispatch machinery
ports across runtimes. Any task breaking this spec down must carry, in
its own `Touch:`:

- a matching update to `antigravity/.agents/skills/drain/` (the mirrored
  copy of the touched drain files — locate the exact mirrored file(s) at
  breakdown time; per CLAUDE.md's port-chain convention, `.claude/` →
  `antigravity/` → `codex/`), and
- since `codex/.agents/skills/drain` is a symlink to the `antigravity/`
  directory (not real content — CLAUDE.md's mirror-obligations bullet),
  no separate codex edit is needed for drain itself; only the four
  explicit-invocation wrapper skills (`drain`/`build`/`autopilot`/`evals`)
  carry real content under `codex/.agents/skills/`, and this spec's
  Requirements do not touch those four wrapper files directly, and
- a `.claude-plugin/plugin.json` `version` bump (current `0.8.63` per
  live check at spec-authoring time — bump per semver; this spec's
  changes are behavior-affecting skill-body edits, so at minimum a patch
  bump).

## Research grounding

Verbatim from the current repo, confirming the gap each requirement
closes:

- Worker prompt's only existing shell-safety guidance (reactive, not
  proactive): "If a Bash call is denied ('don't ask mode'), retry it ONCE
  as a bare single command (no chaining, no `&&`/pipe/redirection
  tricks); if it is still denied, stop and report the blocked command in
  your verdict, never iterate syntax variants." (reference.md:570-572)
- Headless fallback's allowlist is a bare placeholder with no canonical
  tool-complete form: `--allowedTools "Read,Edit,Write,Glob,Grep,
  Bash(<verified test/lint/build cmds>),Bash(git add *),Bash(git commit
  *)"` (reference.md:915, restated in runtimes/claude-code.md:67-68).
- The Touch-enforcement check's own command-substitution shape:
  `` git diff $(git merge-base <default-branch> <branch>)..<branch> -- ``
  (SKILL.md:205) — the exact pattern class the shell-pattern evidence says
  gets denied under restrictive permission modes.
- `docs/memory/unattended-worker-tool-limits.md`'s existing manual-pending
  precedent this spec's R3 classifier follows: "OR let the worker mark
  that one criterion **manual-pending with the reason**" (line 41).

## Requirements

R1. Drain's headless-dispatch and baton self-relaunch steps
(`reference.md` "Headless fallback" and "Baton pass (self-relaunch)")
must validate the `--allowedTools` string against the actual pending
tasks' acceptance-criteria commands before dispatching the generation's
first worker — not discover a gap via a live BLOCKED verdict. State this
as an explicit pre-flight step in both sections (they currently share the
allowlist mechanism but are documented separately).

R2. Document one canonical, tool-complete allowlist template for
compute-heavy specs (`go`, `bash`, `npm`, `python3`, `git` at minimum) in
`runtimes/claude-code.md`'s `## Headless` section, and have
`reference.md`'s Headless fallback (reference.md:915) and Relaunch
command template (reference.md:1069-1076) sections reference it by name
rather than each restate or reconstruct an allowlist ad hoc.

R3. Add a privileged/OS-level task classifier at breakdown or drain-intake
time: a task whose acceptance commands require `launchctl`, a system
installer/package manager install step, or interactive OAuth is flagged
MANUAL / human-pending (per the existing manual-pending precedent in
`docs/memory/unattended-worker-tool-limits.md`) rather than dispatched to
a worker that can only fail BLOCKED on a sandbox denial.

R4. Extend the Worker prompt (reference.md:506-631) and the Headless
fallback's inline prompt (reference.md:892-918) with known-safe
shell-pattern guidance, stated once and cross-referenced rather than
duplicated between the two: no command substitution (`$(...)`), no `for`
loops, no multi-verb `&&`-chained commands in permission-gated Bash
calls; `! cmd | grep -q` instead of `cmd | ! grep`; and explicit handling
of `grep -c`'s exit-1-on-zero-matches (e.g. `grep -c … || true` where
zero is a valid outcome). This is additive to the existing reactive
retry-once-bare-command rule (reference.md:570-572), not a replacement
for it.

R5. Fix or document the SKILL.md:205 Touch-enforcement check's own
`$(git merge-base …)` command-substitution shape if a permission-mode-safe
rewrite is identifiable without live debugging (e.g. a two-step form that
avoids inline substitution); otherwise leave it and note in Open questions
that this specific instance needs a live permission-mode probe to confirm
whether it is actually denied in practice (it is orchestrator-side, run
under drain's own session, not necessarily under the same restrictive
`dontAsk` mode a headless worker runs under) before rewriting it blind.

## Out of scope

- Fixing the headless/detached-relaunch reliability gap itself (Problem's
  last bullet) — root cause requires live debugging on the affected
  machine(s), which this spec cannot do from static analysis. See Open
  questions.
- Any change to drain's overlapping-but-distinct concerns already covered
  by sibling specs: `specs/drain-forward-progress` (screen-stub.sh
  false-positives on descriptive path mentions — a different defect class
  than this spec's allowlist/shell-safety focus, though both touch
  `screen-stub.sh`-adjacent machinery), `specs/drain-sweep-preservation`
  (worktree/branch loss on crash), `specs/drain-wake-cost` and
  `specs/drain-rolling-window` (orchestrator wake economics and dispatch
  concurrency), `specs/drain-remote-divergence-check` (concurrent-session
  detection), `specs/drain-hub-economics` (hub model-tier checks),
  `specs/drain-terminal-distill` (auto-distill on terminal states),
  `specs/drain-eval-merge-commit-assertion` (eval fixture assertion bug).
  None of these seven existing drain-* specs' Problem sections cover
  allowlist pre-flight, canonical allowlist templates, privileged-task
  classification, or proactive shell-pattern guidance — confirmed by
  reading each at spec-authoring time.
- Building a mechanical/scripted allowlist scanner (a tool that parses
  acceptance commands and auto-generates `--allowedTools`) — R1 requires
  the pre-flight step exist and be followed, not that it be fully
  automated; a scripted scanner is a reasonable follow-up but not required
  here.
- Changing the reactive retry-once-bare-command rule (reference.md:
  570-572) — R4 adds proactive guidance alongside it, not a replacement.

## Acceptance criteria

- `grep -c "validate its allowlist against" /Users/sjaconette/claude/.claude/skills/drain/reference.md` → at least 1 (R1; phrase absent today, verified at spec-authoring time via `grep -rc` returning 0 in both SKILL.md and reference.md).
- `grep -c "canonical worker allowlist" /Users/sjaconette/claude/runtimes/claude-code.md` → at least 1, AND `grep -c "canonical worker allowlist" /Users/sjaconette/claude/.claude/skills/drain/reference.md` → at least 1 (R2; phrase absent today in both files, verified via `grep -rc` returning 0).
- `grep -c "never drain-completable unattended" /Users/sjaconette/claude/.claude/skills/drain/SKILL.md /Users/sjaconette/claude/.claude/skills/drain/reference.md /Users/sjaconette/claude/.claude/skills/breakdown/SKILL.md` → at least 1 across the three files combined (R3; phrase absent today in all three, verified via `grep -rc` returning 0 in each).
- `grep -c "known-safe shell patterns" /Users/sjaconette/claude/.claude/skills/drain/reference.md` → at least 1 (R4; phrase absent today, verified via `grep -rc` returning 0).
- `grep -c '\$(git merge-base' /Users/sjaconette/claude/.claude/skills/drain/SKILL.md` → either 0 (rewritten) with a corresponding note in the same task's commit message explaining the safe replacement, OR the phrase persists AND an Open Questions entry documents the manual-pending live-probe reason (R5; this criterion is a fork resolved by the closing task's own commit, not a fixed literal — record which branch was taken in the task's evidence).
- Mirror obligation check: any task whose `Touch:` includes
  `.claude/skills/drain/reference.md` and/or
  `.claude/skills/drain/SKILL.md` must also list a matching path under
  `antigravity/.agents/skills/drain/` in its own `Touch:` — verify with
  `grep -l "drain/reference.md\|drain/SKILL.md" specs/drain-worker-dispatch-hardening/tasks/*.md` cross-checked by hand against each matching task's `Touch:` list at breakdown time (MANUAL: breakdown-time review, not a standalone runnable command, since it depends on tasks/ files that don't exist until /breakdown runs).
- `git show <version-bump-commit> -- /Users/sjaconette/claude/.claude-plugin/plugin.json | grep -q '^+.*"version"'` → match, on whichever task's commit performs the version bump (per anchored-acceptance-criteria.md's version-bump-criteria pattern — never a pinned literal, since the current `0.8.63` may have moved by drain time).

## Open questions

- Headless/detached-relaunch reliability gap (Problem's last bullet, Out
  of scope): is this a bug in a specific harness version, a
  machine-local environment issue, or a structural limitation of
  detached headless generations on some platforms? Needs a human (or a
  live-debugging session on the affected machine) to reproduce and
  isolate before a fix requirement can be written — flagging here per
  the topic brief's instruction to surface this as an explicit
  manual-pending item rather than guess at a root cause from static
  analysis.
- R5's `$(git merge-base …)` fix: is SKILL.md:205's Touch-enforcement
  check actually run under the same restrictive `dontAsk` permission mode
  that denies command substitution in worker prompts, or does it run
  under drain's own (typically less restrictive) orchestrator session? If
  the latter, R5 may be a non-issue and the requirement should be
  downgraded to "confirm, don't fix" at breakdown time.
