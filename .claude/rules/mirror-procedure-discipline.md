# Mirror procedure discipline

A mirror is a port, not a copy: prose legitimately diverges between runtimes.
The PROCEDURE a skill instructs — its sequence of steps, decision points, and
stated conditions — is not supposed to diverge, except where a runtime's own
mechanism forces it. This rule states the discipline that keeps the same
algorithm from being re-derived, abbreviated, or reordered three times by
hand (the gap `specs/mirror-procedure-discipline` opened; `.claude/` →
`antigravity/` → `codex/` is the port chain).

## Classify every divergence: load-bearing or incidental

When authoring or editing a mirror, classify each place its procedure
differs from the source into exactly one of two buckets before deciding
whether to leave it:

- **Load-bearing** — a difference a runtime's own mechanism forces: a
  different launch-gating primitive, a different dispatch tool, a different
  headless invocation shape, or a capability the target runtime genuinely
  lacks. This divergence is correct; leave it.
- **Incidental** — prose-level drift in what is supposed to be the same
  procedure: a dropped step, a lost condition, a reordered decision, a
  missing count or checklist item. Nothing forces it. Fix it with a small,
  targeted edit (same steps, same order, same stated conditions), never a
  rewrite.

Write invariant procedural content once and carry it faithfully, the same
discipline skills already apply to rule content — cite `.claude/rules/*.md`
rather than restating it (`runtimes/README.md`'s guiding principle for tier
language, applied to procedure).

## Scope: procedure, not cross-references

This rule governs procedural/behavioral content — the steps and decisions a
skill instructs. It is distinct from `mirror-verification.md`, which governs
cross-reference resolution: whether a link, path, command, or tool name
still resolves under the target runtime. Neither rule supersedes the other;
a mirror edit that touches both needs both checks. Semantic
procedural-equivalence checking stays a by-hand or agent-driven read, on
`mirror-verification.md`'s closure-triggered sweep cadence (cited, not
duplicated).

## The coverage gate is a heuristic with two blind spots

`tests/test_mirror_procedure_coverage.sh` greps a curated manifest of
`<source>|<mirror>|<phrase>` lines and fails when a phrase is present in the
source but absent from the mirror. It is a coverage heuristic, not a
semantic-equivalence checker, and by construction cannot catch:

- **Ordering-only divergence** — a phrase that moved position but did not
  change is present in both files, so a presence check sees no gap (the
  `build.md` reorder fix this session is exactly this shape).
- **Mirror-adds-content divergence** — the check only catches
  source-has/mirror-lacks, never the reverse: a mirror asserting content
  the source does not contain (e.g. the codex-autopilot content-swap fix)
  slips through, because the manifest greps for source phrases in mirrors,
  not the other way around.

A passing gate therefore means "no seeded phrase was re-dropped," not "the
mirrors are procedurally equivalent." The manifest grows every time a
session finds and fixes a real procedural gap; it never shrinks silently.
