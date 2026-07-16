# Handoff — session over wake budget (277,976 tokens, past 250k threshold)

Refresh-over-carry per `.claude/rules/token-discipline.md`, "Session refresh".
This session did NOT re-prime the cache (0 re-primes) but exceeded the
context-size threshold, so it's refreshing rather than continuing. NOTE:
the wake-budget hook fired TWICE (269,680, then 277,976 tokens) because the
prior handoff's `/clear` instruction wasn't followed before the next
message — if you're reading this in yet another non-cleared continuation,
`/clear` now before doing anything else.

## Update: item 5 is DONE — specs/prompt-tweaking-roi/SPEC.md landed

Commit `50bec3e`, pushed to `origin/main`. Conclusion: dynamic mid-flow
prompt injection is worth it only for genuinely time-varying,
state-dependent content that can't be known at system-prompt-authoring
time, and only when the hook stays silent unless that state actually
changed — static always-fires reminders belong in CLAUDE.md/rules
instead (written once, cached, not re-paid every turn). This repo's own
three hooks (`hooks/handoff-resume/`, `hooks/plugin-staleness/`,
`hooks/session-refresh/`) already follow this correctly by convention;
the gap was that nothing wrote the rule down — exactly the shape the
now-disabled `prompt-improver` plugin violated. `Priority: P3`, one
concrete action: a new sourced bullet in
`.claude/rules/token-discipline.md`'s "Cache economics" section. Sources
cited in the spec: Anthropic's "Effective context engineering for AI
agents" (2025), Liu et al. "Lost in the Middle" (arXiv:2307.03172), and
Claude's prompt-caching + hooks-reference docs.

**Next stage for this spec**: `/critique specs/prompt-tweaking-roi/SPEC.md`
— can run alongside `/critique specs/drain-hub-context-discipline/SPEC.md`
(item 2 above), then both through `/breakdown`.

## Task

Two threads were open at handoff time, both started from the same
originating request: a `/drain` run on `specs/rigor-tier`, followed by a
meta-discussion of why the session's own context grew so large.

## State

### 1. Drain run — paused at baton, awaiting user re-authorization

`specs/rigor-tier` fully drained THIS run: all 4 tasks done (build/drain
Rigor-tier gate scaling, `/idea`+`/breakdown` Rigor header, `/list-specs`
tier display + quality-discipline scoping, closing version bump
0.9.14→0.9.15), spec-completion review clean (0 findings,
`specs/rigor-tier/evidence/spec-review.md`), lease released. All merges
clean, all project gates green throughout (specs/status.sh, claude plugin
validate, tests/test_*.sh, bin/check-agent-model-pins,
evals/lint-ultra-gate.sh, evals/lint-skill-size-gate.sh).

**Baton**: `specs/drain-worker-dispatch-hardening/DRAIN-BATON.md`,
`Run-token: c11f6ca343ed7836`, `Generation: 2`.

**Orchestrator isolation**: `.claude/worktrees/drain-orchestrator`, branch
`drain-orchestrator-run`, in sync with `origin/main` as of this handoff.

**Remaining scope** (in dispatch-order):

1. `specs/drain-worker-dispatch-hardening` — task 03 (P2, dep 02 done) →
   task 05 (P1, gates 01-04).
2. `specs/context-blowout-subagent-guards` — task 01 (P2, no deps).
3. Stub intake (6 draft stubs): `narrow-autopilot/tasks/07`,
   `shared-viz-renderer/tasks/05`, `shared-viz-renderer/tasks/06`,
   `trajectory-evals/tasks/05`, `trajectory-evals/tasks/06`,
   `trajectory-evals/tasks/07`.
4. 3b auto-breakdown: `specs/codebase-context-tree` (Breakdown-ready:
   true, no tasks/ yet) — **CAVEAT**: `main` was found 23 commits behind
   `origin/main` mid-session; the pull included "Merge pull request #18
   ... codebase-context-tree-design" which touched
   `specs/codebase-context-tree/SPEC.md` and `CUJS.md`. Re-read that
   SPEC.md's current state before attempting auto-breakdown — it may
   already be handled.

19 of 26 in-scope specs are already done/obsolete — no work needed there.

**Resuming this drain requires the user's next live message to name/
re-authorize it** (a "continue" or equivalent) — this is a continuation of
an already-authorized run, not a fresh launch, so the bar is a live
instruction, not a full re-launch.

### 2. New spec authored this session

`specs/drain-hub-context-discipline/SPEC.md` (commit `c8b5d02`, pushed to
`main`). Written after reviewing why THIS drain run's hub context grew
large. Requirements:

- **R1**: `.claude/skills/drain/reference.md` did a full sequential
  1744-line `Read` instead of `Grep`-then-offset-`Read` of just the needed
  section, despite the file's own "load only the named section" note.
  Fix: state the Grep+offset procedure explicitly near the TOC; have
  SKILL.md's existing pointers cite it.
- **R2**: The hub hand-pasted reference.md's ~700-word Worker-prompt
  template into all 6 dispatch calls instead of pointing the worker at
  the file by path (matching the pattern reference.md's own
  `<build-skill-path>` substitution already uses).
- **R3** (doc-only): Document the `isolation: worktree` CLAUDE.md/rules
  re-injection cost in "Wake economics" as accepted, not a bug.
- **R4**: Port R1/R2 into `antigravity/.agents/workflows/drain.md` and
  `codex/.agents/skills/drain/SKILL.md` per
  `.claude/rules/mirror-procedure-discipline.md`.

Explicitly OUT OF SCOPE (spec's own Non-goals section): the
prompt-improver plugin (see #3 below — a global plugin issue, not
drainable), and the hub's-own-gate-output-in-context pattern (already
correct per Wake economics' existing exemption — verified, not a gap).

**Next stage**: `/critique specs/drain-hub-context-discipline/SPEC.md`,
then `/breakdown`. The in-flight research (#4 below) should inform this
critique/breakdown pass before it runs.

### 3. prompt-improver plugin — found and disabled

Global user-scope community plugin (`severity1-marketplace`, v0.6.1,
installed 2026-07-11). Its `UserPromptSubmit` hook wrapped every prompt —
including system-generated background task-notifications — in up to 5
stacked nudge blocks; the "improve" nudge duplicates the entire original
prompt/notification text verbatim inside an `Original user request: "..."`
wrapper. Confirmed via `~/.claude/plugins/installed_plugins.json` and the
plugin's own `hooks/hooks.json` + `scripts/nudge_builtins.py`. Account
history showed 27,508+ firings across 463 startups on this install alone.

**User chose "disable entirely."** Done: `claude plugin disable
prompt-improver@severity1-marketplace`, confirmed `false` in
`~/.claude/settings.json`'s `enabledPlugins` map. Takes effect on a
**fresh session** (hooks bind at session start) — it kept firing for the
remainder of the disabling session, which is expected, not a failure.
**No further action needed on this thread** — just confirm on first
resumed turn that the "PROMPT EVALUATION" wrapper is gone.

### 4. Research in flight

A `deep-research` Workflow on "frontier best practices for multi-agent
task decomposition (granularity, dependency modeling, decision-coupling)
and agent dispatch/kickoff (self-containment vs reference-by-path,
context provisioning, boilerplate duplication, structured verdict
contracts, post-completion verification)" — compared against this repo's
own `/breakdown`/`/drain` conventions to find concrete gaps.

- Task ID: `wzr2ypji2`
- Run ID: `wf_b73bd4af-0a9`
- Transcript dir: `/Users/sjaconette/.claude/projects/-Users-sjaconette-claude/b98d4ebc-910f-4c79-9dcf-f0ce1c032ae5/subagents/workflows/wf_b73bd4af-0a9`

**Completed** (109 agents, 923s, 5.57M subagent tokens, 0 errors) — but the
returned top-level result looks BUGGY, not just large: `summary` and
`findings` are literal placeholder text (`"summary":"test"`,
`findings:[{"claim":"test claim","sources":["https://example.com"],...}]`,
`"caveats":"test caveat"`) instead of a real synthesized report. The
`refuted` array (16 entries) and `sources` array (15 entries) DO contain
real substantive research — real arXiv/Anthropic/framework-doc URLs and
claims about task granularity, dependency-graph modeling, context
isolation between concurrent agents, etc. — so the fan-out/search/verify
stages worked; only the final synthesize stage's output looks wrong
(possibly a template/schema default that never got overwritten with the
real synthesis). Before trusting or acting on this research: **read
`/Users/sjaconette/.claude/projects/-Users-sjaconette-claude/b98d4ebc-910f-4c79-9dcf-f0ce1c032ae5/subagents/workflows/wf_b73bd4af-0a9/journal.jsonl`**
(one `{"type":"result",...}` line per completed agent — the real per-agent
findings are almost certainly intact there even though the top-level
rollup is stubbed), or resume the workflow's synthesize stage via
`Workflow({scriptPath: '/Users/sjaconette/.claude/projects/-Users-sjaconette-claude/b98d4ebc-910f-4c79-9dcf-f0ce1c032ae5/workflows/scripts/deep-research-wf_b73bd4af-0a9.js', resumeFromRunId: 'wf_b73bd4af-0a9'})`
to re-run just the broken step (earlier stages replay from cache). This
bug is itself worth a quick note to the user — the `deep-research` skill's
own workflow script may have a synthesis-stage defect worth its own
follow-up task.

Once a clean synthesis is in hand, its findings should feed into refining
`specs/drain-hub-context-discipline/SPEC.md`'s requirements before
`/critique` runs on it — don't critique that spec off the stubbed "test"
result.

### 5. Unstarted — the very next user request

Right as the wake-budget hook fired, the user asked a **second, separate**
research question: frontier-lab (Anthropic/OpenAI/etc.) recommendations on
whether/when "prompt tweaking" (mid-flow prompt engineering, dynamic
prompt rewriting/injection — as opposed to a static system prompt) is
worth doing versus being wasteful overhead. This is a direct follow-on
from the prompt-improver finding (#3) — effectively "was that plugin's
whole category of approach even sound, or is prompt-injection-based
nudging inherently low-value."

**This is the first thing to do on resume.** The question is specific
enough already (no clarifying questions needed) — launch a second
`deep-research` Workflow call, same shape as #4 (5 search angles,
adversarial verify, synthesized cited report). Do NOT reuse #4's args —
this is a distinct question.

## Files touched this session

- `specs/rigor-tier/tasks/{01,02,03,04}-*.md` — Status → done, evidence
  cited (merged to main).
- `specs/rigor-tier/evidence/{02,03}-*.md`, `specs/rigor-tier/evidence/spec-review.md` — new (merged to main).
- `.claude/skills/{build,drain,idea,breakdown,list-specs}/SKILL.md`,
  `.claude/rules/quality-discipline.md`, `CLAUDE.md`,
  `antigravity/.agents/{workflows/{build,drain}.md,skills/{idea,breakdown,list-specs}/*}`,
  `codex/.agents/skills/{build,drain}/SKILL.md`,
  `.claude/skills/list-specs/{list_specs.py,test_list_specs.py}`,
  `.claude-plugin/plugin.json` (0.9.14→0.9.15) — all from rigor-tier's 4
  tasks, merged to main.
- `specs/drain-worker-dispatch-hardening/DRAIN-BATON.md` — new, this
  run's baton (merged to main).
- `specs/drain-hub-context-discipline/SPEC.md` — new spec (merged to
  main, commit `c8b5d02`).
- `~/.claude/settings.json` — `prompt-improver@severity1-marketplace: false`
  (global, outside this repo).
- `.claude/worktrees/drain-orchestrator/` — this run's isolated
  orchestrator checkout, branch `drain-orchestrator-run`, currently in
  sync with `main`. A resumed drain generation should re-verify liveness
  before reusing it (per `.claude/rules/concurrent-sessions.md`) rather
  than assuming it's still valid.

## Gotchas

- `git merge-base <local-main> <branch>` gave WRONG (too-old) results
  twice this session because local `main` in the orchestrator worktree
  context wasn't fast-forwarded to match `origin/main`/current `HEAD` —
  always compute the append-only whitelist diff's merge-base against
  current `HEAD` (or `origin/main`), never a possibly-stale local `main`
  ref.
- `git log --grep=... -- <pathspec>` combined with `--reverse` silently
  dropped a real match in one case (a commit that clearly touched the
  pathspec) — when hunting for a specific flip commit, verify with a
  no-pathspec `git log --grep=...` first before trusting the
  pathspec-filtered + `--reverse` combination.
- Running `pytest a_test.py b_test.py` together across two same-named
  test modules (`.claude/.../test_list_specs.py` and
  `antigravity/.../test_list_specs.py`) throws a module-mismatch
  collection error — not a real test failure. Run each file's suite in
  its own `pytest` invocation.
- A worker accidentally `cd`'d into the shared main checkout once and
  created a stray branch there before self-correcting — always
  independently verify a worker's "I fixed it" claim about the shared
  tree (`git status`, `git worktree list`) rather than trusting the
  verdict text, per `.claude/rules/concurrent-sessions.md`.
- The `claude agents --json` startup sweep showed a long-lived
  (~12-day-old) `background`/`blocked` session named "Drain hub specs"
  whose `cwd` did not resolve into this repo — treated as non-live and
  ignored (no lease file contested it), and it never manifested as a
  real collision. Worth a glance on resume if odd concurrent activity
  appears again, but not something that needs active handling.

## Verification

Rigor-tier's 4 tasks and its spec-completion review were each verified
independently as part of drain's own procedure — every DONE verdict
cited an independent `verifier` agent PASS (not self-reported by the
implementing worker), and the spec-completion review's independent critic
pass returned READY / 0 findings. Project gates (listed above) were
re-run and confirmed green by the hub itself after every merge, not just
trusted from worker output. No additional verifier pass was spawned at
handoff time — re-verifying already-independently-verified, already-merged
work would spend more of this over-budget session's remaining tokens for
no new information; if the resumed session wants extra assurance, a cheap
option is a single fresh `verifier` pass over the cumulative
`c4caf838e07e7a9fe1690aadf32d7e818efd89be..main` diff restricted to
rigor-tier's union Touch paths (same ref range the spec-completion review
already used).

The two new artifacts (`specs/drain-hub-context-discipline/SPEC.md`, the
baton file) are plain committed docs, not code — nothing to verify beyond
"they're on `main`," confirmed above.

Next stage: none — /clear and resume from the handoff file.
