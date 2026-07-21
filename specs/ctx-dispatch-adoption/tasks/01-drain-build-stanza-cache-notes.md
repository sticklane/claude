# Task 01: drain/build dispatch stanza, worktree cache warmth, notes nudge

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (requirements R1, R4, R6)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, .claude/skills/build/SKILL.md, .claude/skills/build/reference.md, antigravity/.agents/workflows/drain.md, antigravity/.agents/workflows/build.md, codex/.agents/skills/drain/SKILL.md, codex/.agents/skills/build/SKILL.md, tests/mirror-procedure-manifest.txt

## Goal

Drain's and build's worker dispatch prompt templates carry a
"Structure lookups (ctx)" stanza (emitted when the target checkout has
`.context/` at its root) naming `tree`, `sig`, `refs`, `deps` with one
example each and the index-first rule as a procedure step; the worktree
creation procedure copies the main checkout's `.context/cache/` into new
worktrees (copy, never symlink); and /build's attended completion step
offers `ctx notes add` when a symbol-anchored, code-comment-bar fact was
learned. All three changes are mirrored to the antigravity and codex
legs and pinned in the mirror-procedure manifest.

## Touch

R1+R4+R6 are one task because they edit the same four `.claude` files
(the spec's "Intra-spec file sharing" note). Do NOT touch
`.claude-plugin/plugin.json` — task 06 owns the closing version bump.
Do NOT reference `ctx show` in the stanza (specs/ctx-query-ergonomics
has not landed). The stanza must be self-contained: no reference to the
"reading ladder" by name (dispatched workers don't have the ctx
SKILL.md loaded).

## Steps

1. Locate the worker dispatch prompt template sections in
   `.claude/skills/drain/reference.md` (worker prompt, ~line 16 and the
   dispatch-prompt blocks) and build's SKILL.md/reference.md.
2. Add the "Structure lookups (ctx)" stanza per SPEC R1: conditional on
   `.context/` at the target checkout root; commands tree/sig/refs/deps
   with one example each; the rule "for a definition, caller, signature,
   or outline question, run the ctx query BEFORE any Grep/Read; fall
   back to Grep for content/text questions (bodies, literals, patterns)
   and Read a file only when about to edit it" as a procedure step
   inside the template text, not a surrounding narrative.
3. Add the worktree cache-copy step per SPEC R4 to drain's (and build's,
   where it isolates) worktree-creation procedure: copy
   `.context/cache/` from the main checkout when present; copy, never
   symlink (SQLite two-writer corruption risk); absent cache = lazy
   build unchanged.
4. Add the R6 notes nudge to /build's attended completion step:
   in an indexed repo, offer `ctx notes add <symbol> "<text>" --kind
   gotcha|invariant|rationale|todo` when the task surfaced a
   symbol-anchored fact meeting the code-comment bar.
5. Port all three changes to `antigravity/.agents/workflows/drain.md` +
   `build.md` and `codex/.agents/skills/drain/SKILL.md` +
   `build/SKILL.md` — paraphrased ports, procedure preserved
   (`.claude/rules/mirror-procedure-discipline.md`); content-coverage,
   not byte-diff (docs/memory/workboard-mirror-verbatim.md).
6. Add `<source>|<mirror>|Structure lookups (ctx)` lines to
   `tests/mirror-procedure-manifest.txt` — one per source→mirror pair,
   source field naming the specific file the stanza landed in.
7. Run `bash tests/test_mirror_procedure_coverage.sh` and
   `bash evals/lint-ultra-gate.sh` (drain/build are ultra-path skills).

## Acceptance

- [ ] `grep -rl 'Structure lookups (ctx)' .claude/skills/drain/ | head -1` → non-empty
- [ ] `grep -rl 'Structure lookups (ctx)' .claude/skills/build/ | head -1` → non-empty
- [ ] `grep -l 'Structure lookups (ctx)' antigravity/.agents/workflows/drain.md antigravity/.agents/workflows/build.md codex/.agents/skills/drain/SKILL.md codex/.agents/skills/build/SKILL.md | wc -l` → 4
- [ ] `grep -c 'Structure lookups (ctx)' tests/mirror-procedure-manifest.txt` → ≥4
- [ ] `grep -rl '\.context/cache' .claude/skills/drain/ | head -1` → non-empty
- [ ] `grep -c 'ctx notes add' .claude/skills/build/SKILL.md` → ≥1
- [ ] `grep -rc 'ctx show' .claude/skills/drain/ .claude/skills/build/ | grep -v ':0' | wc -l` → 0 (no reference to the unlanded verb)
- [ ] `bash tests/test_mirror_procedure_coverage.sh` → exit 0
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
- [ ] Live worktree check scripted per SPEC R4: from an indexed repo, create a scratch worktree following the amended procedure and `test -f <worktree>/.context/cache/index.sqlite` → exit 0 (clean up the scratch worktree after)

Depth ceiling: the stanza/nudge criteria are L0/L1 greps on prose — the
artifact is dispatch-prompt doctrine; the behavioral complement is task
04's adoption telemetry (subagent ctx invocations per session, baseline
0), which measures whether the stanza actually converts. The R4 cache
criterion is L2 (live worktree check).
