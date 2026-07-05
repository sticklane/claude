# Task 01: agentprof skill-frame normalization

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R1)
Touch: agentprof/internal/claude/

## Goal

agentprof's existing skill frame (sourced from the transcript's per-line
`attributionSkill` field) is normalized: a leading `<plugin>:` namespace is
stripped and the frame renders as `skill:<name>`, so `agentic:build` and
bare `build` samples collapse into ONE `skill:build` frame. Lines without
`attributionSkill` keep the existing `(no skill)` frame unchanged. The
change lands at the single point where the skill value is derived (in
`internal/claude/claude.go`, where empty `AttributionSkill` currently
defaults to `(no skill)`), so it flows into every consumer.

## Touch

Only `agentprof/internal/claude/` (implementation + test fixtures). Do NOT
touch the CLI surface, other sources (gcp/vertex/otel), output writers, or
anything outside `agentprof/`.

## Steps

1. Write the failing test first: a fixture transcript with three assistant
   lines — `attributionSkill: "agentic:build"`, `attributionSkill: "build"`,
   and one with no attributionSkill — asserting both skill lines produce
   the single frame `skill:build` and the third produces `(no skill)`.
2. Implement the normalization helper at the derive point (strip through
   the first `:`, prefix `skill:`; empty stays `(no skill)`).
3. `cd agentprof && bash scripts/check.sh` green; commit.

## Acceptance

- [ ] `cd agentprof && go test ./internal/claude/ -run SkillFrame -v` → PASS (fixture covers namespaced, bare, and absent attributionSkill)
- [ ] `cd agentprof && bash scripts/check.sh` → exit 0
- [ ] `cd agentprof && go run . claude --days 7 -o /tmp/sp-norm.jsonl && grep -c '"skill:' /tmp/sp-norm.jsonl` → ≥ 1, and `grep -cE '"(agentic:)?build"' /tmp/sp-norm.jsonl` shows no bare/namespaced skill frame names surviving (record both in evidence)
