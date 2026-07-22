# Task 03: Mirror prose wiring into antigravity/codex, manifest entries, version bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01, 02
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirements R5, R6)
Touch: antigravity/.agents/workflows/build.md, antigravity/.agents/workflows/drain.md, codex/.agents/skills/build/SKILL.md, codex/.agents/skills/drain/SKILL.md, tests/mirror-procedure-manifest.txt, .claude-plugin/plugin.json

## Goal

Task 02's two prose changes (the build sibling-scan grep, the drain
doctrine pointer) are mirrored into their real (non-symlinked) antigravity
and codex counterparts, coverage-checked via the mirror-procedure test
manifest, and `.claude-plugin/plugin.json`'s version is bumped.

## Touch

Exactly the files listed above. `drain_frontier.py`'s three-tree identity
was already established by task 01 (a `cp`, not a paraphrase) — do not
re-touch it here. Do not touch `.claude/skills/build/SKILL.md` or
`.claude/skills/drain/SKILL.md` themselves (task 02's scope, already
landed).

## Steps

1. Confirm task 01 and task 02 are both `Status: done` before starting
   (this task's `Depends on:` names them).
2. Port task 02's build change into
   `antigravity/.agents/workflows/build.md` — a paraphrased port (this is
   prose, not a byte-identical `cp`; word it in antigravity's own voice,
   same content: header-only check via grep, not `Read`, for the
   sibling-status scan). `antigravity/.agents/skills/build/` does not
   exist — do not create it; the procedural home is the workflow file.
3. Port task 02's drain doctrine line into
   `antigravity/.agents/workflows/drain.md` (same paraphrased-port
   approach; `antigravity/.agents/skills/drain/` holds only bundled
   scripts, no procedural SKILL.md — do not add one).
4. Apply the same two changes directly to `codex/.agents/skills/build/SKILL.md`
   and `codex/.agents/skills/drain/SKILL.md` (confirmed real-content
   wrappers, not symlinks).
5. Add two new lines to `tests/mirror-procedure-manifest.txt` in its
   existing `<source>|<mirror>|<phrase>` format: one for the build
   sibling-scan phrase (source `.claude/skills/build/SKILL.md`, mirror
   `antigravity/.agents/workflows/build.md`), one for the drain doctrine
   phrase (source `.claude/skills/drain/SKILL.md`, mirror
   `antigravity/.agents/workflows/drain.md`).
6. Bump `.claude-plugin/plugin.json`'s `version` (skill behavior changed
   in drain and build).

## Acceptance

- [x] `bash tests/test_mirror_procedure_coverage.sh` passes.
- [x] `grep -n "grep -l.*Status" codex/.agents/skills/build/SKILL.md`
      returns a match.
- [x] `grep -n "status.sh" codex/.agents/skills/drain/SKILL.md` returns a
      match (anchored on `status.sh` alone — confirmed absent there today;
      `drain_frontier` already appears pre-existing 2× in this file and is
      not a safe anchor).
- [x] `grep -n "grep -l.*Status" antigravity/.agents/workflows/build.md`
      returns a match covering the ported concept (content-coverage check,
      not a byte-diff — this is a paraphrased port per
      `docs/memory/workboard-mirror-verbatim.md`'s distinction between
      byte-identical `.py` mirrors and paraphrased prose mirrors). Anchored
      on `grep -l.*Status` alone — `sibling` already appears pre-existing
      2× in this file and is not a safe anchor.
- [x] `grep -n "status.sh" antigravity/.agents/workflows/drain.md` returns
      a match covering the ported doctrine pointer (anchored on
      `status.sh` alone — confirmed absent there today; `drain_frontier`/
      `header-only` are not safe anchors in this file).
- [x] Confirm whether any of `antigravity/.agents/skills/design/reference.md`,
      `antigravity/.agents/skills/qa-sweep/SKILL.md`, or
      `antigravity/.agents/skills/harness-audit/SKILL.md` (the antigravity
      files that already cite token-discipline content inline) need task
      02's new header-only-check carve-out added to their citation. If
      none do (likely, since antigravity has no standalone `rules/`
      directory these citations stand in for), note that explicitly in
      `## Progress` rather than leaving R5's confirm-step silently
      unassigned; if one does, add the line and list that file in
      `Touch:` before editing it.
- [x] The commit modifying `.claude-plugin/plugin.json` shows the version
      line changed in its own diff (`git show <this-commit> --
      .claude-plugin/plugin.json | grep -q '^+.*"version"'`) — not a
      pinned before/after literal, since a sibling spec may have already
      bumped the same line.

## Progress

- 2026-07-21: DONE. All 6 acceptance criteria verified against merged main (merge commit e3b2126e, worker commit b696240f). R5 confirm-step: neither `antigravity/.agents/skills/design/reference.md` nor `antigravity/.agents/skills/harness-audit/SKILL.md` cite token-discipline's "Delegation defaults" section; `antigravity/.agents/skills/qa-sweep/SKILL.md` does cite it, but generically ("cited, not restated") rather than by enumerating bullets, so task 02's new header-only-check carve-out is already transitively covered — no file needed an added line.
