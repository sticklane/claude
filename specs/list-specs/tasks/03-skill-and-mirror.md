# Task 03: `/list-specs` SKILL.md + antigravity mirror + plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: deferred
Depends on: 02
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (Solution, Disambiguation, acceptance criterion on SKILL.md frontmatter)
Touch: .claude/skills/list-specs/SKILL.md, antigravity/.agents/skills/list-specs/SKILL.md, antigravity/.agents/skills/list-specs/list_specs.py, antigravity/.agents/skills/list-specs/test_list_specs.py, antigravity/.agents/skills/_shared/spec_readiness.py, antigravity/.agents/skills/_shared/test_spec_readiness.py, .claude-plugin/plugin.json

## Goal

`/list-specs` exists as a thin, model-invocable wrapper skill that runs
`list_specs.py` against the cwd and presents its stdout table as the
response — and this task is the spec's closing task, so it also lands the
antigravity mirror + plugin.json version bump for every file this spec
touched (CLAUDE.md's mirror convention: same commit, this is the
designated closing task).

## Touch

The seven paths above only. Do not re-implement `list_specs.py` or
`spec_readiness.py` logic here — Tasks 01/02 already landed those; this
task only copies them verbatim into the antigravity tree.

## Steps

1. Write `.claude/skills/list-specs/SKILL.md`. Frontmatter: `name:
   list-specs`; a `description:` stating what the skill does (per-repo
   spec status + next-command table) AND explicitly naming `/prioritize`
   as the "reorder work, not report the next command" alternative (the
   reciprocal half of the Disambiguation section in `../SPEC.md`); no
   `disable-model-invocation` field (this skill is read-only, stays
   model-invocable, per Solution); no `argument-hint` (R6: always cwd, no
   arguments). Body: run `python3 .claude/skills/list-specs/list_specs.py`
   against the cwd and present its stdout table as the response; note
   that it never auto-invokes the suggested next command (Out of scope).
   Close with a `Next stage:` line — this skill is terminal and must never
   self-chain (Out of scope explicitly forbids auto-invoking the
   suggested command), so write `Next stage: none — the table's Next
   command column names a per-spec next step; the human decides which to
   run.`
2. Read an existing model-invocable skill's antigravity mirror (e.g.
   `antigravity/.agents/skills/workboard/SKILL.md`) to match this repo's
   paraphrased-port conventions and frontmatter shape, then write a
   paraphrased (not verbatim) port to
   `antigravity/.agents/skills/list-specs/SKILL.md` covering the same
   description, disambiguation from `/prioritize`, and behavior.
3. Byte-copy the two files Task 02 landed into the antigravity mirror:
   `cp .claude/skills/list-specs/list_specs.py antigravity/.agents/skills/list-specs/list_specs.py`
   and the matching test file. Byte-copy the two files Task 01 landed:
   `cp .claude/skills/_shared/spec_readiness.py antigravity/.agents/skills/_shared/spec_readiness.py`
   and its test file. Confirm each pair with `diff -q`.
4. Run the mirrored test suites to confirm they pass identically:
   `python3 -m pytest antigravity/.agents/skills/list-specs/test_list_specs.py antigravity/.agents/skills/_shared/test_spec_readiness.py`.
5. Bump `.claude-plugin/plugin.json`'s `"version"` field (patch bump).
6. Commit the SKILL.md, the full antigravity mirror, and the plugin.json
   bump together — this is the single commit CLAUDE.md's mirror
   convention requires.

## Acceptance

- [ ] `grep -n "disable-model-invocation" .claude/skills/list-specs/SKILL.md` → no match.
- [ ] `grep -n "/prioritize" .claude/skills/list-specs/SKILL.md` → present in the frontmatter description.
- [ ] `grep -n "list_specs.py" .claude/skills/list-specs/SKILL.md` → the body invokes the script at the correct relative path (`.claude/skills/list-specs/list_specs.py`), not a typo'd or stale path — this is the only check that would catch a wrapper pointing at the wrong file, since Task 02's acceptance only runs the script directly.
- [ ] `diff .claude/skills/list-specs/list_specs.py antigravity/.agents/skills/list-specs/list_specs.py` → no output.
- [ ] `diff .claude/skills/list-specs/test_list_specs.py antigravity/.agents/skills/list-specs/test_list_specs.py` → no output.
- [ ] `diff .claude/skills/_shared/spec_readiness.py antigravity/.agents/skills/_shared/spec_readiness.py` → no output.
- [ ] `diff .claude/skills/_shared/test_spec_readiness.py antigravity/.agents/skills/_shared/test_spec_readiness.py` → no output.
- [ ] `grep -n "/prioritize" antigravity/.agents/skills/list-specs/SKILL.md` → the paraphrased mirror also carries the reciprocal disambiguation (content-coverage check, not a byte diff — this file is a paraphrased port).
- [ ] `python3 -m pytest antigravity/.agents/skills/list-specs/test_list_specs.py antigravity/.agents/skills/_shared/test_spec_readiness.py` → passes.
- [ ] `git diff HEAD~1 -- .claude-plugin/plugin.json` (once committed) shows the version field changed.

## Deferred questions

Steps 1-3 done and verified in the worker's worktree (both SKILL.md files
written; all four byte-copies — `list_specs.py`, `test_list_specs.py`,
`spec_readiness.py`, `test_spec_readiness.py` — `diff -q` clean against
their `.claude/skills/` originals). Step 4's mirrored pytest run fails:

`python3 -m pytest antigravity/.agents/skills/list-specs/test_list_specs.py antigravity/.agents/skills/_shared/test_spec_readiness.py`
→ 1 failed, 37 passed. Failure:
`CliSubprocessTestCase::test_this_repo_produces_table_no_archive_rows_no_crash`
— `AssertionError: '| Spec | Status | Next command |' not found in 'no
specs/ directory found\n'`.

Root cause: `test_list_specs.py` (from Task 02, line 261) computes
`repo_root = Path(__file__).resolve().parents[3]` to find the repo root
from the test file's own location. That's correct only when the file
sits exactly 3 parents below repo root — true at its home path
`.claude/skills/list-specs/test_list_specs.py` (2 path components —
`.claude`, `skills` — before `list-specs`). The antigravity mirror path
`antigravity/.agents/skills/list-specs/test_list_specs.py` has 3
components (`antigravity`, `.agents`, `skills`) before `list-specs` —
one level deeper — so in the mirror location `parents[3]` resolves to
`.../antigravity` instead of the true repo root, the subprocess runs
against a directory with no `specs/`, and the assertion fails. This is
structural: every skill mirrored under `antigravity/.agents/skills/`
sits one directory deeper than under `.claude/skills/`, so any test
using this repo-root-from-self-path pattern fails identically once
mirrored.

This task's own acceptance criteria are mutually exclusive given that
fixed `parents[3]` assumption: the byte-identity checks (criteria 4-5)
require `test_list_specs.py` to be an unmodified copy, while the
mirrored-suite-passes check (criterion on line 74) requires that same
copy to pass in a location where its repo-root arithmetic is wrong. The
worker had no `Touch` access to fix the root cause
(`.claude/skills/list-specs/test_list_specs.py` belongs to Task 02's
already-merged commit).

**Question:** which should win?
(a) Keep byte-identity; treat this one CLI-subprocess test as an
    accepted, documented mirror-environment exception (amend this
    task's acceptance to allow that specific failure in the antigravity
    copy).
(b) Patch the antigravity copy's repo-root calculation to account for
    the extra nesting level (breaks byte-copy-verbatim for this file
    only).
(c) Fix the depth-assumption bug at the source in
    `.claude/skills/list-specs/test_list_specs.py` (e.g. walk up to a
    `.git` marker instead of a fixed parent count) as a follow-up task,
    then re-copy verbatim — since Task 02 is already merged, this needs
    a task/spec amendment or a new discovered task ahead of this one.
