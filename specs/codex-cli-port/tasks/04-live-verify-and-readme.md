# Task 04: Live verification script + codex/README.md

Status: pending
Depends on: 01, 02, 03
Priority: P1
Budget: 65 turns
Spec: ../SPEC.md (requirements R1, R5; Solution items 1c, 5)
Touch: codex/README.md, codex/verify-live.sh, .agents

## Goal

`codex/verify-live.sh` exists as a runnable, re-runnable script that
live-tests, from this repo's actual root: (a) whether skill discovery is
relative to the `--cd`/cwd directory or the git repo root, applying the
documented fallback (root-level `.agents -> codex/.agents` symlink) if the
cwd-relative reading turns out wrong; (b) that `codex exec` auto-triggers an
already-symlinked skill (e.g. `list-specs`) via a natural-language prompt;
(c) that a plain natural-language prompt does NOT trigger one of the four
new skills (e.g. `drain`) while explicit `$drain`-style invocation DOES read
its `SKILL.md`. `codex/README.md` documents the reuse-not-copy approach,
states the fixed invocation convention actually confirmed to work, has a
"What degrades on Codex" section, and records the actual (a)/(b)/(c)
results.

## Touch

`codex/README.md` and `codex/verify-live.sh` unconditionally. The
repo-root `.agents` path is listed for the conditional fallback in Step 4
only — touch it ONLY if R5(a) shows discovery is git-root-relative rather
than cwd-relative; otherwise leave it untouched. This task reads (but does
not modify beyond that conditional symlink) the structure built by tasks
01-03.

## Steps

1. Confirm a `codex` binary is on PATH: `which codex && codex --version`.
   (A `codex-cli 0.144.1` binary was confirmed present in this environment
   during spec authoring — if it is genuinely absent when this task runs,
   stop, mark the R5 check manual-pending in this task's evidence, and do
   not fabricate output, per docs/memory/unattended-worker-tool-limits.md.)
2. Write `codex/verify-live.sh` performing, in order:
   a. An R5(a) discovery-root test: run `codex exec --cd codex
      --skip-git-repo-check "<natural-language prompt matching an existing
      skill>"` from the repo root, and determine whether discovery is
      cwd-relative or git-root-relative (the spec's caveat: the prior
      scratch-repo test couldn't distinguish these because its `--cd`
      happened to equal the git root; this repo's `codex/.agents/` is a
      subdirectory of the git root, which only the cwd-relative reading
      supports without a fallback).
   b. If cwd-relative works: an R5(b) test — natural-language prompt
      matching `list-specs`'s description, confirming its `SKILL.md` was
      read/followed.
   c. An R5(c) pair: one natural-language prompt matching `drain`'s
      description (expect NO auto-trigger, since its `agents/openai.yaml`
      sets `allow_implicit_invocation: false`), and one explicit
      `$drain`-style invocation (expect its `SKILL.md` IS read) — using
      whichever mechanism step (a) established works.
3. Run the script for real against this repo's actual root (this doubles
   as the spec's end-to-end acceptance criterion — not a scratch copy).
4. If R5(a) shows discovery is git-root-relative rather than cwd-relative,
   create the documented fallback — a root-level relative symlink
   `.agents -> codex/.agents` — and re-run (b)/(c) using the fallback
   invocation (interactive `codex` or `codex exec` from the repo root with
   no `--cd`).
5. Write `codex/README.md`: reuse-not-copy approach, the invocation
   convention actually confirmed to work (`--cd codex` or the root-symlink
   fallback), a "What degrades on Codex" section (mirror
   `antigravity/README.md`'s "What degrades" section shape/tone — no custom
   slash commands; Subagents ≠ workflow launcher; explicit-invocation-only
   skills are experimental per open upstream issues openai/codex #19695,
   #10585, #23454), and the recorded (a)/(b)/(c) results (works / partially
   works / does not work / manual-pending). A negative (b) or (c) result is
   an acceptable, documented outcome — write it down rather than omitting
   or softening it.
6. Commit.

## Acceptance

- [ ] `test -f codex/README.md` and it names the confirmed invocation
  convention and contains a "What degrades" heading
- [ ] `test -f codex/verify-live.sh` and it is executable
  (`test -x codex/verify-live.sh`)
- [ ] Running `./codex/verify-live.sh` from the repo root exits, and its
  output is reflected in `codex/README.md`'s verification section
- [ ] End-to-end: the exact invocation documented in `codex/README.md`, run
  fresh from the repo root, returns a correct scoped result for a
  list-specs-shaped prompt (or the manual-pending note is present if no
  `codex` binary is available)
