# Task 03: mirror Step 1 only (antigravity, codex) + manifest entry

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 01
Priority: P2
Budget: 14 turns
Spec: ../SPEC.md (requirements R5, R6)
Touch: antigravity/.agents/workflows/drain.md, codex/.agents/skills/drain/SKILL.md, tests/mirror-procedure-manifest.txt

## Goal

Only the runtime-neutral procedural line — pinned exact text: **"resolve
once per session, never reuse a version number seen elsewhere in
context"** — is added to each mirror, near each runtime's own existing
path-pointer resolution mention. The Claude-Code-specific plugin-cache
path construction (task 01's Step 2) is NOT copied into either mirror.
`tests/mirror-procedure-manifest.txt` gets a matching entry so the
coverage gate tracks this phrase.

## Touch

Do not touch `.claude/skills/drain/reference.md` (task 01's file) beyond
reading it for context. Do not touch any `.claude/skills/*` file — that's
task 02's scope, not this task's.

## Steps

1. Add the pinned phrase "resolve once per session, never reuse a version
   number seen elsewhere in context" to
   `antigravity/.agents/workflows/drain.md`, near its existing worker-launch
   path-pointer resolution mention (`grep -n "resolved at dispatch" antigravity/.agents/workflows/drain.md`
   to locate it — verify the exact line first rather than trusting a
   hard-coded number, since content may have shifted since this task was
   authored). This is an ADDITION to existing prose — antigravity has no
   documented plugin-cache install mode today, so word it to note that
   absence rather than describing a mechanism that doesn't exist.
2. Add the same pinned phrase to `codex/.agents/skills/drain/SKILL.md`,
   near its existing /build dispatch path-pointer mention (`grep -n
"resolve it to a concrete build-skill path" codex/.agents/skills/drain/SKILL.md`
   to locate it), worded to fit codex's own install layout.
3. Add a new `<source>|<mirror>|<phrase>` line to
   `tests/mirror-procedure-manifest.txt` using
   `.claude/skills/drain/reference.md` as source and the pinned phrase
   above (verbatim, matching what you actually wrote in steps 1-2) —
   follow the file's existing line format exactly.
4. Confirm the Claude-Code-specific cache-path literal
   (`plugins/cache/agentic-toolkit`) is NOT present in either mirror file.

## Acceptance

- [ ] `bash tests/test_mirror_procedure_coverage.sh` passes.
- [ ] `grep -c "resolve once per session, never reuse a version number seen elsewhere in context" .claude/skills/drain/reference.md antigravity/.agents/workflows/drain.md codex/.agents/skills/drain/SKILL.md`
      shows 1+ in all three files (the source already carries it from
      task 01's recipe text — confirm task 01 landed first via `Depends
    on: 01`).
- [ ] `grep -c "plugins/cache/agentic-toolkit" antigravity/.agents/workflows/drain.md codex/.agents/skills/drain/SKILL.md`
      shows 0 in both — confirms the load-bearing Step 2 literal was
      correctly excluded from both mirrors.
