# Task 01: import agentprof as a top-level component

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 14 turns
Spec: ../SPEC.md (requirements R1, R7)
Touch: agentprof/

## Goal

`agentprof/` exists at the repo root containing a fresh copy of
`~/agentprof`'s tracked files at HEAD — excluding `.git/`, any nested
`.claude/` directory, and `specs/` (its archived spec/evidence files embed
`/Users/sjaconette/...` paths) — and `bash agentprof/scripts/check.sh`
passes from the new location. No personal data, rendered plists, caches,
or profile artifacts are committed.

## Touch

Only the new `agentprof/` tree. Do NOT touch `AGENTS.md`,
`.claude/skills/**`, `antigravity/**`, or `.claude-plugin/**` — task 03
owns repo wiring. Do NOT modify the source repo at `~/agentprof`.

## Steps

1. From `~/agentprof`, list tracked files at HEAD (`git ls-files`) and
   copy them into `<repo>/agentprof/`, skipping `.claude/` and `specs/`
   paths. Copy is content-only — no `.git`.
2. Confirm `docs/TASKS.md` came along (open tech-debt travels with the
   code) and `go.mod` still declares `github.com/sticklane/agentprof`
   (module path stays; binary-only, no external importers).
3. Run `bash agentprof/scripts/check.sh` from the toolkit repo. Fix only
   path assumptions the relocation breaks (nothing functional).
4. Run the personal-data sweep and artifact checks below.
5. Commit the new tree as one commit.

## Acceptance

- [ ] `bash agentprof/scripts/check.sh` → exit 0
- [ ] `test ! -d agentprof/specs && test ! -d agentprof/.claude && test -f agentprof/docs/TASKS.md` → exit 0
- [ ] `grep -rn "sjaconette\|Jaconette" agentprof/ | wc -l` → 0
- [ ] `find agentprof -name "*.pb.gz" -o -name "*.plist" ! -name "*.tmpl" | wc -l` → 0
- [ ] `head -1 agentprof/go.mod` → `module github.com/sticklane/agentprof`
