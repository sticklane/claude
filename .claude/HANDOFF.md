# Handoff: research → specs sweep + drain-wake-cost re-verification + local-install sync

## Task

Two `/deep-research` passes (AI writing/UX/web-design/TDD best practices;
context self-management) were requested to be "turned into specs." That
led into a chain: draft/critique/breakdown a prose-review spec, re-verify
an already-shipped drain fix with fresh `agentprof` data, register a
built-but-unwired safety hook, and write a plugin-refresh script — all
committed. Nothing is currently in flight; this is a clean stopping point
forced by the session-refresh hook (this session hit p90_ctx > 250k twice).

## State — all done, all committed

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
   10/10 passed, and it fired for real on this session within minutes of
   registration. Tasks 06-07 of that spec were NOT reviewed this
   session — worth a look before assuming the spec is fully closed.

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

## Not done / open

- Local repo has NOT been pushed to `sticklane/claude` this session — `bin/submit` has never actually been exercised against a real push. First real use will be the real test.
- `specs/drain-wake-cost` task 05 is unstarted — needs real transcript reading, not more agentprof aggregate stats.
- `specs/session-refresh-automation` tasks 06-07 (draft) unreviewed.
- The two deep-research reports that started this session are NOT saved as standalone artifacts anywhere — their substance is now embedded in the specs above; if the raw reports are wanted later, they'd need to be re-run (Workflow run IDs were `wf_6aa6da24-48f` and `wf_4d2242c0-5a0`, but workflow transcripts are session-scoped and may not be resumable from a fresh session).

## Gotchas

- `agentprof` binary is NOT on PATH — always pass `AGENTPROF_BIN=/Users/sjaconette/claude/agentprof/agentprof` (or build it fresh: `cd agentprof && go build -o agentprof .`).
- agentprof's `sessions` summary section has fields `p50_ctx`/`p90_ctx`/`calls`/`cost_microusd`/`project` only — NOT a per-session `reprime_count` (that has to be computed by scanning the raw JSONL for `labels.reprime == "true"` per session yourself; the summary's top-level `reprime` block is aggregate-only).
- `claude plugin marketplace update` / `claude plugin install` pull from the GitHub remote for a GitHub-sourced marketplace — local uncommitted or unpushed commits are invisible to it. This is why `bin/refresh-plugins` is a no-op until you've actually pushed.
- Git has no native post-push hook — don't try to build one; `bin/submit`'s push-then-refresh wrapper is the correct shape.
- This repo regularly has multiple concurrent Claude Code sessions in the same checkout — `.claude/HANDOFF.md` is a single rolling slot; this overwrote a stale handoff from an already-merged prior session (its referenced commits were already in `git log` at this session's start).

## Verification

- prose-review spec: critic verdict READY (with one non-blocking nit, fixed); re-critique confirmed READY. Not yet built/implemented.
- drain-wake-cost: new evidence numbers reproduced once via a fresh `agentprof claude --days 7` run this session; not independently re-verified by anyone else.
- session-refresh hook: `bash hooks/session-refresh/test.sh` → 10 passed, 0 failed. Live-fired on this session (confirmed via the injected directive text appearing in context).
- `bin/refresh-plugins` / `bin/submit`: `bash -n` syntax check only — never run end-to-end.
