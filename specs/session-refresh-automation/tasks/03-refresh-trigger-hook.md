# Task 03: Refresh trigger hook

Status: done
Depends on: 01, 02
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirement R2)
Touch: hooks/session-refresh/

## Goal

A toolkit-shipped hook script under a new `hooks/session-refresh/`
directory that, on prompt-submit, reads the session id from the hook
stdin payload, shells out to the `agentprof` binary for that session's
`reprime_count` and `p90_ctx` (the task-02 fields), and prints the
over-budget directive when either R1 arm (≥3 re-primes or p90_ctx ≥250k)
trips. Silent (empty output, exit 0) under budget, on any agentprof
error, or when the binary is absent. A README in the same directory
documents the one-step global wiring into `~/.claude/settings.json`
(user-run, not automated by this task).

## Touch

Everything lives in `hooks/session-refresh/` (script, tests, README,
fixtures). Do NOT edit `.claude/settings*.json`, `.claude/skills/`, or
`.claude/rules/` — installation is a documented user step, and the
doctrine landed in task 01.

## Steps

1. Write the failing tests first (bash or pytest, one runner file):
   over-budget fixture → directive on stdout; under-budget → empty, exit
   0; agentprof binary absent from PATH → empty, exit 0. Fixtures are
   synthetic transcripts/summaries, never real session data.
2. Implement the script: parse stdin JSON for the session id, invoke
   agentprof (per ../SPEC.md R2a: `--since` + jq on the summary; a
   `--session` filter flag is sanctioned only if this proves too slow —
   if you add it, it belongs in a follow-up task, not silent scope
   creep), compare both arms, emit the directive text naming /handoff.
3. Write the README wiring section (exact settings.json JSON lives
   there, per CLAUDE.md's config-in-reference convention).

## Acceptance

- [x] `bash hooks/session-refresh/test.sh` (or the pytest equivalent) → all three cases pass — verifier: 10/10 passed, exit 0 (evidence/03-refresh-trigger-hook.md)
- [x] `grep -c '/handoff' hooks/session-refresh/*.sh` (or `.py`) → ≥ 1 (directive names the skill) — verifier: refresh-check.sh:2
- [x] `grep -ci 'settings.json' hooks/session-refresh/README.md` → ≥ 1 (wiring documented) — verifier: 2
- [x] Directive text appears ONLY on the over-budget path — under-budget and no-binary runs produce zero bytes on stdout (asserted by the tests) — verifier: under/absent/session-absent/error cases assert empty stdout; manual double-check under.json→0 bytes, over→371 bytes with /handoff
