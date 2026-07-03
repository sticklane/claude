# Task 06: Evals runner robustness — nullglob, guards, git isolation, cleanup trap, FAIL forensics

Status: done
Depends on: none
Budget: 30 turns
Spec: ../SPEC.md (cluster 06)

## Goal

`evals/run.sh` hardened against its verified failure modes: unmatched
globs iterating literally, unknown skill names silently passing, the
user's global git config (signing, hooks) leaking into fixtures, orphaned
fixture dirs on interrupt, and zero forensics on FAIL. Plus the breakdown
scenario's allowlist is missing scout's `Bash(ls *)` / `Bash(wc *)`
grants, so scout fan-out prompts for permission mid-eval.

## Touch

- `evals/run.sh`
- `evals/breakdown/01-small-spec/allowed-tools.txt`

## Steps

1. Add `shopt -s nullglob` near the top of `evals/run.sh`.
2. Guard the skill argument: `[ -d "$ROOT/.claude/skills/$skill" ]` or
   FAIL with "unknown skill".
3. Isolate git: every setup.sh and claude invocation runs with
   `GIT_CONFIG_GLOBAL=/dev/null` in the environment and
   `-c commit.gpgsign=false` on git commands (or `GIT_CONFIG_COUNT`-style
   injection for commands run inside claude).
4. Add `trap 'rm -rf "$EVAL_DIR"' EXIT INT TERM` so interrupted runs don't
   orphan fixtures — then make the trap conditional on outcome per step 5.
5. FAIL forensics: tee the claude session output to a per-scenario log
   inside the fixture; on FAIL, keep the fixture (clear the trap or move
   the dir) and print its path; delete only on PASS.
6. Append `Bash(ls *)` and `Bash(wc *)` to
   `evals/breakdown/01-small-spec/allowed-tools.txt` (scout's grants).
7. Smoke-test: `bash -n evals/run.sh`, then run the runner with a bogus
   skill name and confirm the "unknown skill" FAIL path.

## Acceptance

- [x] `bash -n evals/run.sh` → exit 0 — verified, evidence/06-evals-runner-robustness.md
- [x] `grep -q "shopt -s nullglob" evals/run.sh` → exit 0 — line 12, evidence/06-evals-runner-robustness.md
- [x] `grep -q "unknown skill" evals/run.sh && grep -qF '.claude/skills/$skill' evals/run.sh` → exit 0 (guard present) — pre-loop arg guard + per-scenario check, evidence/06-evals-runner-robustness.md
- [x] `grep -q "GIT_CONFIG_GLOBAL=/dev/null" evals/run.sh && grep -q "commit.gpgsign=false" evals/run.sh` → exit 0 — exported env forced an unsigned commit under gpgsign=true in verifier's end-to-end test, evidence/06-evals-runner-robustness.md
- [x] `grep -qE "trap .rm -rf .\\\$EVAL_DIR" evals/run.sh` → exit 0 (cleanup trap installed) — interrupt cleanup and kept-on-FAIL survival behaviorally verified, evidence/06-evals-runner-robustness.md
- [x] `grep -q "tee" evals/run.sh` → exit 0 (per-scenario session log) — teed to $EVAL_DIR/session.log with pipefail, evidence/06-evals-runner-robustness.md
- [x] `grep -qF "Bash(ls *)" evals/breakdown/01-small-spec/allowed-tools.txt && grep -qF "Bash(wc *)" evals/breakdown/01-small-spec/allowed-tools.txt` → exit 0 — evidence/06-evals-runner-robustness.md
- [x] `bash evals/run.sh no-such-skill 2>&1 | grep -qi "unknown skill"` → exit 0 (FAIL path exercised) — prints "unknown skill: no-such-skill", exit 1, no fixture created, evidence/06-evals-runner-robustness.md
