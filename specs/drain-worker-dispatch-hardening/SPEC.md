Status: open
Priority: P1
Breakdown-ready: true

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
_reactive_ rule for Bash denials — "retry it ONCE as a bare single command
… if it is still denied, stop and report" (reference.md:570-572) — but
states no _proactive_ guidance on which shapes get denied in the first
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

1. Add an allowlist pre-flight to drain's headless-dispatch step
   (reference.md "Headless fallback", the per-task WORKER allowlist at
   reference.md:915): before the first `claude -p` invocation of a
   generation's worker, scan the pending tasks' acceptance-criteria
   commands for the tool/command names they invoke and confirm each is
   covered by the `--allowedTools` string about to be used; widen the
   list (per the canonical template from R2) before dispatching rather
   than after a BLOCKED verdict reveals the gap. Separately, add a
   pre-flight to the baton self-relaunch step (reference.md "Baton pass
   (self-relaunch)", the distinct ORCHESTRATOR allowlist at
   reference.md:1069-1076, which reference.md already documents as
   `Task`-inclusive and NOT the worker's): before self-relaunching,
   confirm that allowlist still carries `Task`, `Bash(git *)`, and the
   repo's actual project gate/lint/test command(s) — a fixed, repo-level
   check, not a per-task tool scan, since the orchestrator dispatches
   workers rather than running their acceptance commands itself.
2. Add one canonical, tool-complete WORKER allowlist template for
   compute-heavy specs (`go`, `bash`, `npm`, `python3`, `git` at minimum,
   following the existing `Bash(<verified test/lint/build cmds>)`
   placeholder convention) to `runtimes/claude-code.md`'s `## Headless`
   section (the file that already defines `<allowlist>`'s shape), and
   have `reference.md`'s Headless fallback section reference it by name
   instead of each session reconstructing a worker allowlist ad hoc. The
   Relaunch command template's ORCHESTRATOR allowlist
   (reference.md:1069-1076) is deliberately distinct — it grants `Task`,
   not build/test tools — and is out of scope for this canonical worker
   template; item 1's baton-self-relaunch pre-flight covers that
   allowlist separately.
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

Requirements 1, 2, and 4 touch `.claude/skills/drain/reference.md`
(Headless fallback, Baton pass, and the Worker prompt); R5 may touch
`.claude/skills/drain/SKILL.md` (the Touch-enforcement line at
SKILL.md:205); R3's classifier may land in `.claude/skills/drain/
reference.md`, `.claude/skills/drain/SKILL.md`, or `.claude/skills/
breakdown/SKILL.md` (its acceptance criterion permits any of the three).
Confirmed live at spec-authoring time via `ls -la antigravity/.agents/
skills/drain/`, `ls -la codex/.agents/skills/`, and `grep -n
'$(git merge-base' antigravity/.agents/workflows/drain.md
codex/.agents/skills/drain/SKILL.md`:

- BOTH `.claude/skills/drain/reference.md` and `.claude/skills/drain/
SKILL.md` port into the SAME antigravity file:
  `antigravity/.agents/workflows/drain.md` (confirmed: it carries the
  reference.md worker-prompt/retry-rule/Baton-pass content AND the
  SKILL.md:205 `$(git merge-base …)` line, at drain.md:368) —
  `antigravity/.agents/skills/drain/` deliberately holds no
  `SKILL.md`/`reference.md` of its own (only `README.md` and
  `screen-stub.sh`, a script bundle), because drain is human-launched and
  therefore ports to a _workflow_, not a skill. Any task whose `Touch:`
  includes EITHER `.claude/skills/drain/reference.md` OR
  `.claude/skills/drain/SKILL.md` must also list
  `antigravity/.agents/workflows/drain.md` in its own `Touch:`, and locate
  the exact corresponding section inside `drain.md` at breakdown time.
- `codex/.agents/skills/drain/` is real content, NOT a symlink (confirmed:
  every other entry under `codex/.agents/skills/` is a symlink into
  `antigravity/.agents/skills/`, but `drain`, `build`, `autopilot`, and
  `evals` are real directories — CLAUDE.md's port-chain bullet names these
  four as the exception). Per CLAUDE.md's codex-leg rule (which triggers on
  `SKILL.md` changes specifically), any task whose `Touch:` includes
  `.claude/skills/drain/SKILL.md` must also list
  `codex/.agents/skills/drain/SKILL.md` in its own `Touch:` (confirmed:
  that file already carries the same `$(git merge-base …)` line at
  codex/.agents/skills/drain/SKILL.md:187, plus an equivalent of the
  retry-once-bare-command rule in its own Codex-adapted "Dispatch"
  section). A task whose `Touch:` is `reference.md`-only (R1, R2, R4) is
  not required by that literal rule to also touch codex — but should note
  in its commit if it restates a rule codex's SKILL.md also carries (e.g.
  R4's shell-pattern guidance), so the two don't silently drift.
- if R3's classifier lands in `.claude/skills/breakdown/SKILL.md`, the
  task must also list `antigravity/.agents/skills/breakdown/SKILL.md` in
  its own `Touch:` (confirmed a real, non-stub mirrored file); per the
  codex-leg rule, `codex/.agents/skills/breakdown` is a symlink to that
  same file (confirmed), so no separate codex edit is needed for that
  path.
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
  `git diff $(git merge-base <default-branch> <branch>)..<branch> --`
  (SKILL.md:205) — the exact pattern class the shell-pattern evidence says
  gets denied under restrictive permission modes.
- `docs/memory/unattended-worker-tool-limits.md`'s existing manual-pending
  precedent this spec's R3 classifier follows: "OR let the worker mark
  that one criterion **manual-pending with the reason**" (line 41).

## Requirements

R1. Drain's headless-dispatch step (`reference.md` "Headless fallback",
the per-task WORKER allowlist at reference.md:915) must validate its
allowlist against the actual pending tasks' acceptance-criteria commands
before dispatching the generation's first worker — not discover a gap via
a live BLOCKED verdict. State this as an explicit pre-flight step in that
section. Separately — because reference.md:1069-1076 explicitly documents
the baton self-relaunch step's allowlist as a distinct ORCHESTRATOR
allowlist (`Task`-inclusive, not per-task-tool-scoped) — the baton
self-relaunch step (`reference.md` "Baton pass (self-relaunch)") must,
before self-relaunching, confirm that separate allowlist still carries
`Task`, `Bash(git *)`, and the repo's actual project gate/lint/test
command(s): a fixed, repo-level check, not a per-task tool scan, since the
orchestrator dispatches workers rather than running their acceptance
commands itself. These are two pre-flights over two allowlists that serve
different purposes; neither substitutes for the other.

R2. Document one canonical, tool-complete WORKER allowlist template for
compute-heavy specs (`go`, `bash`, `npm`, `python3`, `git` at minimum) in
`runtimes/claude-code.md`'s `## Headless` section, and have
`reference.md`'s Headless fallback (reference.md:915) section reference
it by name rather than restate or reconstruct an allowlist ad hoc. This
template is scoped to the per-task WORKER allowlist only — the Relaunch
command template's ORCHESTRATOR allowlist (reference.md:1069-1076) is
deliberately distinct (it grants `Task`, not build/test tools) and is out
of scope for this requirement; R1's baton-self-relaunch pre-flight covers
that allowlist separately.

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
- Mirror obligation check: any task whose `Touch:` includes EITHER
  `.claude/skills/drain/reference.md` OR `.claude/skills/drain/SKILL.md`
  must also list `antigravity/.agents/workflows/drain.md` in its own
  `Touch:`; any task whose `Touch:` includes `.claude/skills/drain/
SKILL.md` must ALSO list `codex/.agents/skills/drain/SKILL.md` in its
  own `Touch:`; any task whose `Touch:` includes `.claude/skills/
breakdown/SKILL.md` must also list `antigravity/.agents/skills/
breakdown/SKILL.md` in its own `Touch:` — verify with
  `grep -l "drain/reference.md\|drain/SKILL.md\|breakdown/SKILL.md" specs/drain-worker-dispatch-hardening/tasks/*.md` cross-checked by hand against each matching task's `Touch:` list at breakdown time (MANUAL: breakdown-time review, not a standalone runnable command, since it depends on tasks/ files that don't exist until /breakdown runs).
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
  analysis. **Resolved as non-blocking at breakdown time:** this item is
  already fully addressed by its own presence here — the spec's
  Out-of-scope section and this entry together ARE the documentation
  Solution item 5 calls for. No task file targets it; a human who wants
  to chase the root cause does so outside this spec.
- R5's `$(git merge-base …)` fix: is SKILL.md:205's Touch-enforcement
  check actually run under the same restrictive `dontAsk` permission mode
  that denies command substitution in worker prompts, or does it run
  under drain's own (typically less restrictive) orchestrator session? If
  the latter, R5 may be a non-issue and the requirement should be
  downgraded to "confirm, don't fix" at breakdown time. **Resolved at
  breakdown time:** confirmed by reading `.claude/skills/drain/SKILL.md`
  — the `$(git merge-base …)` check lives in step 3 ("Collect the
  verdict"), which drain's own orchestrator session executes when
  merging a worker's result; it is never part of a dispatched worker's
  `claude -p` prompt or its restrictive `--permission-mode dontAsk`
  invocation (`reference.md`'s "Headless fallback" section, ~line 924).
  So it does NOT run under the restrictive mode the Problem section's
  shell-pattern evidence describes. Per R5's own stated fork, this
  downgrades R5 to "confirm, don't fix": the closing task documents this
  finding at SKILL.md:205 rather than rewriting a check that already
  runs safely.
