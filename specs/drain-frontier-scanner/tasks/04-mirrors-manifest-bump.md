# Task 04: Codex/antigravity mirrors, manifest seed, version bump (closing)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: pending
Depends on: 01, 02
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R5)
Touch: codex/.agents/skills/drain/SKILL.md, antigravity/.agents/workflows/drain.md, tests/mirror-procedure-manifest.txt, .claude-plugin/plugin.json

## Goal

The codex drain wrapper carries the invoke-with-fallback procedure; the
antigravity drain workflow port receives the change with its divergence
explicitly classified (load-bearing if that runtime cannot invoke the
script — then model-derived procedure with fallback wording stays;
incidental otherwise) per `.claude/rules/mirror-procedure-discipline.md`
and the `.claude/rules/mirror-verification.md` live check, recorded as
evidence. The manifest gains ONE seeded codex line with the
runtime-neutral bare token `drain_frontier` — never a path-bearing
phrase, never an antigravity line. plugin.json version bumped.

## Steps

1. Read task 02's landed diff, both mirror files, and the manifest's
   line format (`<source>|<mirror>|<phrase>`).
2. Port the procedure to the codex wrapper; classify and port (or
   record load-bearing divergence for) the antigravity workflow.
3. Seed `\.claude/skills/drain/SKILL.md|codex/.agents/skills/drain/SKILL.md|drain_frontier`
   into the manifest; run the coverage gate.
4. Bump plugin.json version; run the mirror-verification sweep and
   record evidence.

## Acceptance

- [ ] `grep -c 'drain_frontier' codex/.agents/skills/drain/SKILL.md` →
      ≥ 1 (0 today, verified 2026-07-19)
- [ ] `grep -c 'codex/.agents/skills/drain/SKILL.md.*drain_frontier'
    tests/mirror-procedure-manifest.txt` → ≥ 1 and `bash
    tests/test_mirror_procedure_coverage.sh` → exit 0
- [ ] Antigravity divergence classification recorded in
      `specs/drain-frontier-scanner/evidence/` (load-bearing or
      incidental, with the live-check result). Depth ceiling:
      classification is a judgment record — behavioral complement is
      the mirror-verification live check itself, evidence-recorded.
- [ ] `git show <this task's own commit> -- .claude-plugin/plugin.json |
    grep -q '^+.*"version"'` → exit 0
