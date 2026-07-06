# workboard auto-triage: dispatch critique/breakdown/verify+archive without per-spec manual commands

## Problem

`/workboard`'s inbox already surfaces, cross-repo, exactly which specs are
"needs-review" (all tasks done, waiting on a verifier + archive) or sitting
unbroken-down with no `tasks/` yet. Today a human has to read that inbox
and, one spec at a time, type `/critique`, `/breakdown`, or dispatch a
verifier and `git mv` the spec into `archive/`. A single run of `/workboard`
just showed 10 all-done specs and several not-yet-decomposed ones across
three repos — that's a dozen-plus manual commands for state changes that
are individually low-risk and mechanically decidable from the spec's own
files. Two prior scouts confirmed: (a) `/breakdown` is a pure
text-decomposition step that never touches source/business logic — "safe
for blind auto-triggering" — and (b) no automation in this repo currently
takes action on specs; `workboard.py`'s `build_actions_script` only ever
writes a human-reviewed shell script.

## Solution

Extend `/workboard` (`.claude/skills/workboard/SKILL.md` +
`.claude/skills/workboard/workboard.py`) with an **opt-in auto-triage
mode**, gated by an explicit trigger phrase so it never fires from routine
`/workboard` usage:

- **Classification stays in Python, testable.** `workboard.py` gains a
  `triage` field on every spec dict returned by `--json`, computed by two
  new pure functions:
  - `breakdown_gate` — no `tasks/` dir (or an empty one) AND
    `open_questions_unresolved()` is false (reusing the shared helper,
    `.claude/skills/_shared/spec_readiness.py`, that `specs/list-specs`
    also depends on — see R0 below for ownership).
  - `verify_archive` — `tasks/` has ≥1 file AND every task's status is
    `done` or `skipped` (the same `done_like` category `specs/list-specs`
    defines — duplicated here as a ~5-line literal-set check rather than
    importing list_specs.py, since list_specs.py is a CLI script, not a
    library, and this is the only place besides list-specs that needs it).
  - Both are `None` (no triage) for every other spec state — a spec with
    any `deferred`/`blocked`/`in-progress`/`pending` task can never match
    either bucket (their preconditions already exclude it), so nothing
    mid-drain or awaiting a human answer is ever touched.
  - A spec with unresolved `## Open questions` and no `tasks/` gets
    neither bucket (matches list-specs' rule 1: it needs a human-run
    `/critique`-and-fix cycle, not an auto gate — auto-triage cannot
    safely guess answers to a spec's own declared open questions).
- **Dispatch stays in the orchestrating session's prose** (SKILL.md),
  because only the live session can spawn agents, run git, and observe
  cost. See Requirements for the exact flow, cap, and safety rules.

## Requirements

- **R0 (shared-module ownership)**: This spec depends on
  `.claude/skills/_shared/spec_readiness.py` (contract defined in
  `specs/list-specs`'s R0) existing. Since these are independent sibling
  specs with no enforced build order: if `.claude/skills/_shared/
  spec_readiness.py` already exists when this spec is implemented, import
  it as-is and do not re-touch it; if it does not yet exist, this spec's
  implementation creates it, exporting exactly
  `open_questions_unresolved(spec_md_text: str) -> bool`, and — to avoid
  two independently-invented placeholder-resolution behaviors — its
  test suite lives in the single shared file
  `.claude/skills/_shared/test_spec_readiness.py`, whose required cases
  are defined once, in `specs/list-specs`'s R0 (not restated here). This
  spec's own acceptance criterion is simply that
  `test_spec_readiness.py` passes — whichever spec authors the module
  first is the one whose implementation must satisfy that one shared
  test file; the other spec only imports it. **This coordination only
  holds for sequential landing** — this spec's task and `specs/
  list-specs`'s task must not be dispatched in the same parallel drain
  wave (both could otherwise race to create the same file); sequence
  them, or make one explicitly depend on the other, at breakdown time.
- **R1 (trigger gate)**: The auto-triage flow in workboard/SKILL.md only
  runs when the invoking message, trimmed of leading/trailing whitespace,
  matches the command form `/workboard auto-triage` or
  `/workboard --auto-triage` (case-insensitive), or the skill was invoked
  via the Skill tool with `args` exactly `"auto-triage"` /
  `"--auto-triage"`. This is a strict command-form match, not a substring
  search — a message like "don't auto-triage anything, just show me the
  inbox" contains the phrase but does not match the required command
  form, so it correctly falls through to today's read-only report instead
  of firing the mutate-and-push flow. Any other phrasing, however close,
  runs today's existing read-only report and never reaches this flow.
- **R2 (candidate selection + hard cap)**: Scan with today's existing root
  resolution (cross-repo: configured code dirs + cwd + every repo any
  Claude Code session has touched). Collect every spec across every repo
  where `triage` is `breakdown_gate` or `verify_archive`. Sort candidates
  by `(repo path, spec slug)` ascending and take the first **20**
  (combined across both buckets). Before dispatching anything, print one
  log line: total candidates found, how many are `breakdown_gate` vs
  `verify_archive`, and — if candidates exceed 20 — the slug of every
  candidate past the cap under a "not processed this run, re-run
  auto-triage to continue" note. This line is unconditional: it prints
  even when the count is small, so spend is always visible before it's
  incurred, per `.claude/rules/token-discipline.md`'s dispatch-authoring
  and the Workflow tool's "no silent caps" doctrine (cite, don't restate).
- **R3 (breakdown_gate dispatch)**: For each selected `breakdown_gate`
  spec, dispatch one fresh `critic` agent against its `SPEC.md` (no
  session context carried in — matches the critic agent's normal
  standalone use).
  - READY verdict → dispatch one fresh agent to run the `/breakdown`
    procedure against that spec (invoking the Skill tool for `breakdown`
    inside that subagent, or an equivalent self-contained prompt covering
    the same procedure) so `specs/<slug>/tasks/` gets created, then
    `git add specs/<slug>/tasks` and commit
    (`chore: breakdown <slug> via auto-triage`) — every other terminal
    action in this flow commits its result; this path is not an exception.
  - NOT READY verdict → do **not** attempt to fix the spec. Append the
    critic's findings verbatim under a new `## Auto-triage findings
    (<date>)` section in the spec's `SPEC.md`, commit that single-file
    change, and do not proceed to breakdown for this spec. This is a
    deliberate limit: a subagent auto-fixing genuine spec ambiguity would
    be guessing at decisions that need human judgment (the same reasoning
    `/idea`'s own interview step exists for) — auto-triage only acts where
    the classification is already unambiguous from the files themselves.
- **R4 (verify_archive dispatch)**: For each selected `verify_archive`
  spec, first apply workboard.py's existing `_actively_covered(rp, r,
  active_toplevels, drain_window)` predicate to that spec's repo, with
  **one adjustment, and no session-identity lookup needed**: when
  `rp == ` the auto-triage flow's own launch repo, evaluate only the
  function's drain-worktree half (a `task/*`-branch worktree with
  activity inside `drain_window`) and skip the `rp in active_toplevels`
  half for that one repo. This is sufficient and needs no "which session
  is me" logic: `active_toplevels` is a set of repo-toplevel path
  strings (workboard.py:818-819), and the launch repo's own toplevel
  (computed the same way workboard.py:961 does — `git rev-parse
  --show-toplevel` of the launch cwd, NOT the raw launch cwd string
  itself, which won't match `active_toplevels`' entries if launched from
  a subdirectory) is
  the *only* toplevel this flow's own session could ever contribute to
  that set — so skipping the toplevel check there costs nothing except
  the (separately-covered) case of a stray plain interactive session,
  while every genuinely dangerous case — a live `/drain` mid-bookkeeping,
  which always shows as a `task/*` worktree — is still caught by the
  half that stays active. For every other repo in the cross-repo scan,
  apply `_actively_covered` unmodified (both halves; a live session there
  cannot be this flow's own). If either half is true for the applicable
  repo, **skip this spec for this run** (log it under the R5 report as
  "skipped — live session/drain detected, re-run later") and do not
  dispatch a verifier for it. Otherwise, dispatch one fresh `verifier`
  agent against the spec's acceptance criteria.
  - PASS verdict → `git mv specs/<slug> specs/archive/<slug>` (which
    stages both the deletion and the addition), then commit **only those
    two paths** — `git commit specs/<slug> specs/archive/<slug> -m
    "chore: archive verified spec <slug>"` — never `git commit -a` or
    `git add -A`, so any unrelated dirty state in the working tree is
    never swept into this commit. Then push `main` following the exact
    push guard `/drain`'s reference.md documents (upstream configured →
    push; no upstream → skip silently; rejected/offline → warn and
    continue; never `--force`) — cite that guard, don't restate its
    mechanics here.
  - FAIL verdict → do not archive. Append the verifier's findings under
    `## Auto-triage findings (<date>)` in the spec's `SPEC.md`, commit
    that single file only, and leave the spec in place.
- **R5 (final report)**: After all dispatches complete, print a summary
  table: spec, bucket, verdict, action taken (broken down / archived /
  findings appended / not processed — over cap). This is the only output
  presented to the user for this run besides the R2 pre-dispatch line.
- **R6 (no double-processing)**: This flow never touches a spec whose
  `triage` is `None`. Additionally, before dispatching for any selected
  candidate, check whether its `SPEC.md` already contains a
  heading starting with `## Auto-triage findings` (from a prior run — the
  match is a starts-with/substring test against the heading line, not
  exact-line equality, since the real heading carries a trailing
  `(<date>)`); if so, **skip it
  entirely for this run** (log under R5 as "skipped — has unresolved
  auto-triage findings, needs human action") rather than re-dispatching
  a critic/verifier — a NOT-READY or FAIL verdict already told a human
  what to fix, and re-running the same agent against the same
  unaddressed spec only re-spends tokens for the same answer. Once a
  human resolves the finding and removes that heading (or the spec's
  state changes such that it no longer matches `breakdown_gate`/
  `verify_archive`), a later run re-evaluates it normally — no separate
  reflect that — no separate idempotency tracking needed).
- **R7 (deterministic test seam)**: Dispatch and action-taking (R3/R4)
  live in SKILL.md prose, not in the pure Python classifier, and real
  critic/verifier/breakdown agents are non-deterministic — so this flow
  honors an environment variable, `WORKBOARD_AUTOTRIAGE_STUB`, that when
  set to a file path makes the flow read that path as JSON
  (`{"<slug>": "READY" | "NOT READY" | "PASS" | "FAIL"}`) and, for that
  slug, skip **every** agent dispatch R3/R4 would otherwise make —
  including the critic/verifier call AND, for a `breakdown_gate` spec
  under a `READY` stub verdict, the subsequent `/breakdown`-procedure
  dispatch too. Under stub `READY`, instead of invoking a live breakdown
  agent, the flow copies a fixed fixture task file (a single
  `00-stub-task.md` with a minimal valid `Status: pending` header) into
  `specs/<slug>/tasks/` — this keeps the READY→breakdown acceptance
  criterion fully deterministic. In every stubbed case the flow still
  performs the exact same file/git actions (commits, `git mv`, findings
  append) that R3/R4 specify for that verdict. Every acceptance criterion
  below that says "critic mock" or "verifier mock" means: set
  `WORKBOARD_AUTOTRIAGE_STUB` to a fixture JSON file mapping the fixture
  spec's slug to the desired verdict. This is the only supported test
  seam — no other mocking mechanism is in scope, and it is never honored
  outside of test runs (the flow does not document any "production"
  reason to set this env var).

## Out of scope

- Any confirmation pause before the very first-ever auto-triage dispatch —
  the opt-in trigger phrase is the authorization, every run, no special
  first-run gate.
- Raising or configuring the cap of 20 — fixed for this spec; a follow-up
  can add a `Budget:`-style override if it proves too small.
- Auto-fixing a NOT-READY critique or FAILed verification — always
  surfaced as findings for a human, never guessed at.
- Any change to `/critique`'s or `/breakdown`'s own gating
  (`disable-model-invocation` stays unset on both — unchanged).
- A fully unattended cron/launchd sweep with no human-typed trigger —
  explicitly rejected in favor of the opt-in-phrase model.

## Acceptance criteria

- [ ] `pytest .claude/skills/workboard/` covers `breakdown_gate` /
      `verify_archive` / `None` classification for: no `tasks/` dir +
      empty Open Questions → `breakdown_gate`; no `tasks/` dir + unresolved
      Open Questions → `None`; all tasks `done`/`skipped` → `verify_archive`;
      one `deferred` task among otherwise-done tasks → `None`; one
      `blocked` task → `None`; one `in-progress`/`claimed` task → `None`.
- [ ] `pytest .claude/skills/_shared/test_spec_readiness.py` passes
      (whether `.claude/skills/_shared/spec_readiness.py` was authored by
      this spec or by `specs/list-specs`, per R0) before this spec's
      other criteria are exercised.
- [ ] Fixture run with 25 combined candidates → the pre-dispatch log line
      names exactly the 5 over-cap slugs as not processed, and the final
      report lists only the 20 processed.
- [ ] A fresh agent given only workboard/SKILL.md and the prompt
      `/workboard` (no opt-in phrase) does not dispatch any subagent or
      mutate any file.
- [ ] A fresh agent given workboard/SKILL.md and the prompt "don't
      auto-triage anything, just show me the inbox" does not dispatch any
      subagent or mutate any file (R1's strict command-form match, not a
      substring search).
- [ ] A fresh agent given workboard/SKILL.md and the prompt
      `/workboard auto-triage` against a fixture repo with one
      `breakdown_gate` spec, `WORKBOARD_AUTOTRIAGE_STUB` pointing at a
      fixture mapping that spec's slug to `"NOT READY"`: the spec's
      `SPEC.md` gains a `## Auto-triage findings` section, no `tasks/` dir
      is created, and `git log` shows exactly one commit touching only
      that `SPEC.md`.
- [ ] Same setup with the stub verdict `"READY"`: no live breakdown agent
      is dispatched; `specs/<slug>/tasks/00-stub-task.md` (the fixed
      fixture file, per R7) exists, and `git log` shows a commit touching
      only `specs/<slug>/tasks/`.
- [ ] Fixture spec whose `SPEC.md` already contains a `## Auto-triage
      findings` heading from a prior run, still classified as
      `breakdown_gate` or `verify_archive`: no agent is dispatched for
      it, and the R5 report lists it as skipped for that reason (R6).
- [ ] Fixture repo that IS the auto-triage flow's own launch repo
      (`rp ==` the git toplevel of the launch cwd — not the raw cwd
      string), with one `verify_archive` spec and a
      simulated *other* interactive session sharing that same toplevel
      (no `task/*` worktree activity): the spec is NOT skipped — the
      toplevel/session-liveness half is deliberately not applied to the
      launch repo, so stub verdict `"PASS"` archives it normally.
- [ ] Same launch-repo fixture, but with a `task/*`-branch worktree whose
      activity is inside `drain_window`: the spec IS skipped as "live
      session/drain detected" — the drain-worktree half still applies to
      the launch repo.
- [ ] Fixture repo that is NOT the launch repo, with one `verify_archive`
      spec and a simulated live session (any sid) sharing that repo's
      toplevel: the spec IS skipped — the full `_actively_covered` check
      (both halves) applies to every repo except the launch repo.
- [ ] Fixture repo with one `verify_archive` spec, no live session
      detected, stub verdict `"PASS"`: `specs/<slug>` no longer exists,
      `specs/archive/<slug>/SPEC.md` does, and the archive commit's
      changed-files list is exactly those two paths (nothing else, even
      when another file in the fixture repo is left dirty).
- [ ] Same setup with stub verdict `"FAIL"`: the spec directory is
      unchanged in location, and its `SPEC.md` gains a `## Auto-triage
      findings` section.
- [ ] Fixture repo with one `verify_archive` spec AND a simulated live
      Claude Code session/agent in that repo (per workboard's existing
      liveness detection): no verifier is dispatched, no `git mv` occurs,
      and the R5 report lists the spec as skipped with the live-session
      reason.
- [ ] End-to-end (human-run, not scripted): `/workboard auto-triage` in
      this machine's real repo set produces the pre-dispatch count line,
      processes at most 20 candidates, and its final report accounts for
      every spec workboard's own inbox currently lists as needs-review or
      not-yet-decomposed.

## Open questions

(none)
