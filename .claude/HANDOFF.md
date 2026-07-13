# Handoff (merged — three independent, unfinished threads)

This file was briefly overwritten mid-session, losing Thread A's still-open
next steps even though its own commits had already landed on `main` — a
handoff's "Not done / open" section can stay live long after its "State"
section's commits are merged, so "commits already in git log" is NOT the
same as "nothing left to do." Restored from `git show 72d140d:.claude/HANDOFF.md`
and merged with Thread B below. Thread C appended the same way (not
overwritten) after reading this file's own "merge, don't clobber" gotcha.
Pick up whichever thread is relevant; they don't touch the same files.

---

## Thread A: cross-runtime (claude/codex/antigravity) parity testing

### Task

User ask (repeated verbatim twice): "perform a thorough test that
functionality is the same across codex, agy, and claude. find a
lightweight way to automatically test that" — freehand work, no spec/task
file. All work is on `main` directly (not a spec/task branch), committed
and pushed through `1dd1417`.

### State — done, with evidence

1. **`tests/test_codex_parity.sh`** (commit `a05c5bc`) — structural +
   symlink-resolution gate for `codex/.agents/skills/`, sibling to the
   pre-existing `tests/test_antigravity_parity.sh`. Found and fixed two
   real bugs: missing `prose-review` symlink (added), and `critique`/
   `fleet`/`workflow-author` had no exemption (added a "What's not
   ported" table to `codex/README.md`). Green.

2. **`runtimes/codex.md`** (commit `c4229d8`) — new runtime profile;
   codex had a working port but no profile, so `evals/run.sh`'s existing
   generic runtime dispatch (via `runtimes/parse_headless.py`) had
   nothing to resolve. Headless template `codex exec --skip-git-repo-check
   --ephemeral --sandbox workspace-write "<prompt>"`, confirmed live via
   `codex/verify-live.sh`'s pre-existing results (not re-tested by me
   this session). Known limitation, already documented: the four
   launch-gated skills' explicit `$name` invocation is unreliable on
   Codex (upstream bugs openai/codex #19695/#10585/#23454) — auto-trigger
   works fine.

3. **`evals/run.sh` provisioning** (commit `c4229d8`, further generalized
   by another concurrent session in `4a58ecd` with `SKILLS_ROOT`/
   `AGENTS_ROOT`/`MAX_TURNS` — compatible, not conflicting) — every
   fixture now gets BOTH `.claude/skills/` and `.agents/skills/` layouts
   unconditionally, so a fixture is runtime-portable without
   re-provisioning.

4. **4 new evalsets** (commit `6a8fd6c`): `evals/build/01-single-task/`,
   `evals/autopilot/01-security-refusal/`, `evals/critique/01-clean-spec/`,
   `evals/evals/01-scaffold-new-skill/`. Coverage went from 2 skills
   (breakdown, drain) to 6. Each verified structurally: `setup.sh` runs
   clean, `assert.sh` correctly RED pre-skill (except autopilot, whose
   correct behavior is a no-op — verified RED by simulating a wrongful
   launch instead). **None of the 4 new evalsets have been run live**
   (real paid model spend) — only structural/RED-state verification.
   `./evals/run.sh <skill>` fires real spend; that's a user decision.

5. **Antigravity doctrine — corrected TWICE this session** (commits
   `686da64`, `1dd1417`):
   - First wrong claim: "Antigravity has no headless harness at all." I'd
     tested the wrong binary — `~/.antigravity/antigravity/bin/agy`
     (the Antigravity.app bundle's OWN launcher script) shadows
     `/opt/homebrew/bin/agy` (the REAL `antigravity-cli` Homebrew
     package) on PATH. The impostor's `chat` subcommand just opens a GUI
     window and returns instantly with empty stdout.
   - Second, bigger finding: the REAL `agy -p "<prompt>"` genuinely
     blocks and prints to stdout (confirmed live: a plain reply, AND a
     real skill auto-trigger — `list-specs` ran its bundled
     `specs/status.sh` correctly). BUT wiring it into `evals/run.sh`
     end-to-end, it did NOT confine itself to the isolated `$EVAL_DIR`
     — it edited real tracked files elsewhere in this actual checkout
     instead (`tests/fixtures/workboard/demo-repo/...`), apparently
     reusing a stale workspace from an earlier manual test. **Caught
     immediately, reverted cleanly** (`git checkout --` + `rm` the new
     file; `tests/test_workboard_render.sh` still passes). This is a
     real, reproduced risk, not theoretical.
   - Net result: `runtimes/antigravity.md` now documents `agy -p`
     accurately (real, live-tested, but flagged **UNSAFE for
     isolated/unattended use**). `evals/run.sh` **hard-blocks**
     `.claude/runtime.md: antigravity` with a clear error (not just a
     doc warning — one already wasn't enough). Antigravity functional
     parity stays blocked, now for a precise, live-verified reason
     (workspace isolation) instead of a wrong one (no CLI).
   - `runtimes/test_parse_headless.py`'s NONE-sentinel tests were moved
     off antigravity onto a new synthetic fixture,
     `runtimes/fake-runtime-no-headless.md`, since antigravity no longer
     exemplifies "no headless template."

### Design direction for next session: sync via genericity, not just gates

User's explicit ask when handing this off: don't just keep adding
parity *tests* that catch drift after the fact — also make skills
generic enough that drift is structurally harder to introduce in the
first place, so the three runtimes stay in sync with less mirroring
effort to maintain. This session added detection (test_codex_parity.sh,
the evalsets); it did NOT address the underlying cause. Concretely, for
a future session to investigate:

- **Audit where the port chain (`.claude/` → `antigravity/` → `codex/`)
  carries runtime-specific content that COULD be runtime-agnostic
  instead.** E.g., the four launch-gated skills (`drain`/`build`/
  `autopilot`/`evals`) are real, separately-maintained content in all
  three trees today (Claude Code SKILL.md, antigravity workflow +
  skill, codex real-content wrapper) specifically because each runtime's
  launch-gating mechanism differs (`disable-model-invocation` vs.
  `allow_implicit_invocation: false` vs. Antigravity's human-launched
  workflow convention) — that's inherent, not accidental duplication.
  But other divergences may be incidental: e.g., the antigravity-mirrored
  `evals.md` I just edited twice this session (manual-launch vs.
  scripted `agy -p`) is exactly the kind of runtime-specific procedural
  detail that drifts because it's spelled out per-runtime rather than
  factored into something shared.
- **Look at what `runtimes/*.md` already generalizes well as a model**:
  the tier language (scout/session/deep/frontier) plus the `## Headless`
  contract shape already let ONE mechanism (`parse_headless.py`) serve
  claude-code/antigravity/codex/gemini-cli without per-consumer
  special-casing — new runtime, no consumer edits. Where else in the
  skill bodies themselves (not just the runtime-profile layer) could a
  similar abstraction replace three hand-maintained copies of the same
  procedure with one procedure plus a thin per-runtime adapter?
- **This is a real architecture investigation, not a quick fix** — don't
  start it inside an already-over-budget session. Likely shape: a scout
  pass cataloging every place `.claude/skills/*/SKILL.md`,
  `antigravity/.agents/{skills,workflows}/*`, and
  `codex/.agents/skills/*` diverge in PROCEDURE (not just existence),
  then a design pass on which divergences are load-bearing
  (runtime-mechanism differences) vs. incidental (would read identically
  if factored out), consistent with `docs/anthropic-playbook.md` and
  this repo's own `/design` skill for exactly this kind of
  architecture-choice work.

### Next step (if continuing this exact ask)

Untested candidate fix for antigravity's workspace-isolation bug:
`agy`'s `--new-project` flag ("Create a new project for this session") —
NOT tried yet, deliberately, to avoid a second uncontrolled file
mutation while investigating. If picking this up:
1. Test `--new-project` in an isolated scratch dir FAR from any real repo
   first (e.g. `/tmp/agy-isolation-test`), never directly against
   `$EVAL_DIR` inside `~/claude` again without that isolation proven.
2. If it reliably confines `agy -p` to the invoking directory, update
   `runtimes/antigravity.md`'s Headless template to add `--new-project`,
   remove the hard-block in `evals/run.sh`, and restore the automated
   run step in `antigravity/.agents/workflows/evals.md` (currently
   reverted to manual Agent Manager launch).
3. If `--new-project` doesn't fix it, that's a legitimate place to stop
   — antigravity's functional parity remains manual-pending per this
   repo's own `mirror-verification.md` doctrine (a documented, accepted
   escape for runtimes without a safe scriptable relaunch).

Other legitimate next steps, not started: live-run the 4 new evalsets
(real spend, user's call); author evalsets for more of the remaining
~13 skills not yet covered; verify `--model`/`--mode` flag *values* on
`agy` live (only flag *existence* was confirmed, per `runtimes/
antigravity.md`'s own "unverified" caveats).

### Files touched (Thread A)

- `tests/test_codex_parity.sh` (new), `codex/README.md`,
  `codex/.agents/skills/prose-review` (new symlink)
- `runtimes/codex.md` (new), `runtimes/antigravity.md` (rewritten twice),
  `runtimes/README.md`, `runtimes/fake-runtime-no-headless.md` (new),
  `runtimes/test_parse_headless.py`
- `evals/run.sh` (provisioning + antigravity hard-block),
  `.claude/skills/evals/SKILL.md` (doc fix)
- `evals/build/01-single-task/*`, `evals/autopilot/01-security-refusal/*`,
  `evals/critique/01-clean-spec/*`, `evals/evals/01-scaffold-new-skill/*`
  (all new)
- `.claude/rules/mirror-verification.md` (stale citation fixed)
- `antigravity/.agents/workflows/evals.md` (reverted to manual launch,
  with the finding cited)

### Gotchas learned the hard way (Thread A)

- **`agy`/`antigravity` name collision is real on this machine**:
  `~/.antigravity/antigravity/bin` precedes `/opt/homebrew/bin` in
  `$PATH`. Always verify `agy --version` (one line = real
  `antigravity-cli`, three lines = the app-bundle impostor) or use the
  absolute path. Personal memory file saved:
  `~/.claude/projects/-Users-sjaconette-claude/memory/feedback_antigravity_cli.md`.
- **Never trust "has a headless template" as "safe for isolated use"**
  without a live end-to-end test through the actual isolated-fixture
  path — the raw CLI working in a scratch dir does NOT prove it stays
  confined to that dir under different invocation patterns.
- This repo has multiple concurrent Claude Code sessions active in the
  same checkout regularly (confirmed via `claude agents --json` and live
  file changes mid-session) — commit+push immediately after each small
  chunk rather than batching, to surface collisions early
  (`~/.claude/.../memory/feedback_commit_push_cadence.md`).

### Verification (Thread A)

- `for t in tests/test_*.sh; do bash "$t"; done` — all green as of
  `1dd1417`.
- `python3 -m pytest runtimes/test_parse_headless.py -q` — 13 passed.
- `bash evals/runner-selftest.sh` — OK.
- `bash tests/test_doc_links.sh` — pass: 16 fail: 0.
- `./bin/check-agent-model-pins`, `claude plugin validate .`,
  `./specs/status.sh` — all OK (run mid-session, not re-verified at
  final commit but no touched file should affect them).

---

## Thread B: research → specs sweep + drain-wake-cost re-verification + local-install sync

### Task

Two `/deep-research` passes (AI writing/UX/web-design/TDD best practices;
context self-management) were requested to be "turned into specs." That
led into a chain: draft/critique/breakdown a prose-review spec, re-verify
an already-shipped drain fix with fresh `agentprof` data, register a
built-but-unwired safety hook, and write a plugin-refresh script — all
committed. Nothing is currently in flight; this is a clean stopping point
forced by the session-refresh hook (this session hit p90_ctx > 250k
repeatedly, including a false start where its own handoff overwrote
Thread A above without merging — now fixed).

### State — all done, all committed

1. **`specs/prose-review-writing-research/`** (commit `dae5455`) — SPEC.md
   READY (`Breakdown-ready: true`), one task
   (`tasks/01-adopt-doctrine.md`). Six doctrine additions to
   `.claude/skills/prose-review/reference.md`: style-guide priority
   hierarchy, reader-test inverted-pyramid/subheading scoring, antipattern
   rubric citations (Morkes & Nielsen), "Learn More"-style accessibility
   framing, a NEW acronym/jargon first-use-only convention (Steven decided:
   keep first-use-only, just note NN/g's tension as a caveat — do NOT
   change it to every-occurrence), and a new `## Why this matters` DORA
   citation section. **Next step**: `/build
   specs/prose-review-writing-research/tasks/01-adopt-doctrine.md` or
   `/drain specs/prose-review-writing-research` (human-launched).

2. **`specs/drain-wake-cost/`** (commit `d869a18`) — reopened. Task 01's
   shipped "dual baton trigger" (2026-07-11) does NOT prevent reprime
   pileup: post-fix sessions hitting >=3 reprimes rose 26.4%->29.4%
   (EVIDENCE.md "Follow-up (2026-07-12)"). New **task 05** (pending,
   P1, 20 turns) diagnoses whether the trigger is evaluated-but-too-loose
   or never re-checked between verdicts, and ships a fix. Requires reading
   real drain transcripts from sessions `55ae834e`/`80161f1c`/`c2cec1dd`
   (match by session-ID prefix under `~/.claude`) — don't re-derive from
   reasoning alone, the task's acceptance criteria require it.

3. **`specs/session-refresh-automation/`** — NOT touched by this session
   (already had tasks 01-05 done, 06-07 still draft), but its shipped hook
   was **registered** for the first time: `~/.claude/settings.json` now has
   a `UserPromptSubmit` hook pointing at
   `hooks/session-refresh/refresh-check.sh` with
   `AGENTPROF_BIN=/Users/sjaconette/claude/agentprof/agentprof` inline (not
   on PATH). Verified: valid JSON, smoke-tested, hook's own test suite
   10/10 passed, and it fired for real on this session repeatedly within
   minutes of registration (this is the hook that forced this handoff).
   Tasks 06-07 of that spec were NOT reviewed this session — worth a look
   before assuming the spec is fully closed.

4. **`bin/refresh-plugins` + `bin/submit`** (commit `81eb20a`) — new,
   untested end-to-end (syntax-checked only; never actually run against a
   real push, since nothing had been pushed yet this session). Claude
   Code's plugin cache is GitHub-marketplace-sourced
   (`~/.claude/plugins/cache/agentic-toolkit/agentic/<version>/`,
   currently `0.8.50`, stale vs. repo's `plugin.json` at `0.8.55`) — the
   refresh only sees content that's actually on the remote, hence the
   push-then-refresh wrapper instead of a pre-push hook. Antigravity and
   Codex are confirmed live-file runtimes (no cache) — their steps in the
   script are intentional no-ops, not gaps.

### Not done / open (Thread B)

- ~~Local repo has NOT been pushed to `sticklane/claude` this session —
  `bin/submit` has never actually been exercised against a real push.~~
  **VERIFIED 2026-07-13**: `bin/submit` ran end-to-end for real (pushed
  `5bddb80`, marketplace refresh + plugin reinstall check OK). One gap
  found: `bin/refresh-plugins` printed "could not determine current
  installed version; skipping stale-cache prune" — version detection
  needs a fix before the prune step ever runs.
- `specs/drain-wake-cost` task 05 is unstarted — needs real transcript
  reading, not more agentprof aggregate stats.
- `specs/session-refresh-automation` tasks 06-07 (draft) unreviewed.
- The two deep-research reports that started this session are NOT saved
  as standalone artifacts anywhere — their substance is now embedded in
  the specs above; if the raw reports are wanted later, they'd need to be
  re-run (Workflow run IDs were `wf_6aa6da24-48f` and `wf_4d2242c0-5a0`,
  but workflow transcripts are session-scoped and may not be resumable
  from a fresh session).

### Gotchas (Thread B)

- `agentprof` binary is NOT on PATH — always pass
  `AGENTPROF_BIN=/Users/sjaconette/claude/agentprof/agentprof` (or build
  it fresh: `cd agentprof && go build -o agentprof .`).
- agentprof's `sessions` summary section has fields
  `p50_ctx`/`p90_ctx`/`calls`/`cost_microusd`/`project` only — NOT a
  per-session `reprime_count` (that has to be computed by scanning the
  raw JSONL for `labels.reprime == "true"` per session yourself; the
  summary's top-level `reprime` block is aggregate-only).
- `claude plugin marketplace update` / `claude plugin install` pull from
  the GitHub remote for a GitHub-sourced marketplace — local uncommitted
  or unpushed commits are invisible to it. This is why
  `bin/refresh-plugins` is a no-op until you've actually pushed.
- Git has no native post-push hook — don't try to build one;
  `bin/submit`'s push-then-refresh wrapper is the correct shape.
- **A handoff's "Not done / open" section can outlive its "State"
  section's commits.** Don't treat "the referenced commits are already
  in `git log`" as proof a handoff is stale and safe to overwrite —
  check whether its open next-steps were ever separately picked up
  before replacing it. Merge, don't clobber.

### Verification (Thread B)

- prose-review spec: critic verdict READY (with one non-blocking nit,
  fixed); re-critique confirmed READY. Not yet built/implemented.
- drain-wake-cost: new evidence numbers reproduced once via a fresh
  `agentprof claude --days 7` run this session; not independently
  re-verified by anyone else.
- session-refresh hook: `bash hooks/session-refresh/test.sh` → 10
  passed, 0 failed. Live-fired on this session repeatedly (confirmed via
  the injected directive text appearing in context).
- `bin/refresh-plugins` / `bin/submit`: `bash -n` syntax check only at
  handoff time; run end-to-end for real 2026-07-13 (see "Not done" above —
  works, minus the stale-cache prune).

---

## Thread C: handoff-resume SessionStart hook

### Task

User asked for "a skill that does both /clear and resumes from
handoff." Freehand work, no spec/task file. Done, committed, pushed as
commit `6395889`.

### State — done

`hooks/handoff-resume/` (new): `resume-check.sh` (the hook), `README.md`,
`test.sh` (11/11 passing). A `SessionStart` hook that searches the
project for any file named `HANDOFF.md` and, if found, injects "read it
and continue" — the actual mechanism, since `/clear` is a hard reset
nothing can trigger-and-then-continue-past in one action. `/handoff` and
`/clear` were deliberately left untouched/separate per explicit user
correction mid-task. Wired into `~/.claude/settings.json`'s
`SessionStart` hooks (global, mirrors how `hooks/session-refresh/` is
wired). Found and fixed one real bug while testing: the hook initially
false-positived on `tests/fixtures/workboard/demo-repo/HANDOFF.md` (a
workboard-dashboard test double, not a real handoff) — now excludes
`fixtures`/`test_fixtures` dirs too.

### Not done / open (Thread C)

- ~~The hook has NOT fired for real yet~~ **VERIFIED 2026-07-13**: fired
  live on a fresh session launch — its SessionStart output injected the
  multi-HANDOFF.md pointer (listing this file plus the plugin-cache
  mirrors) and the session read this file from it. Works as designed.
  Possible refinement: it also surfaces HANDOFF.md copies inside
  `~/.claude/plugins/cache|marketplaces/` mirrors, which are never
  resumable work — could exclude those roots.
- No cleanup/archival for a consumed `HANDOFF.md` — deliberate, stays the
  resuming session's own job per the README.
- The Thread A "sync via genericity, not just gates" design direction
  (above) is still fully open and is the larger, more valuable next step
  if choosing between threads.

### Verification (Thread C)

- `bash hooks/handoff-resume/test.sh` → 11 passed, 0 failed.
- `for t in tests/test_*.sh; do bash "$t"; done` → all green as of
  `6395889`.
- `python3 -c "import json; json.load(open('/Users/sjaconette/.claude/settings.json'))"` → valid.
- Live smoke test against the real repo → correctly identifies this file.
