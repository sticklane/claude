---
name: critic
description: Adversarial review discipline for specs, plans, and diffs. Use before implementation starts (spec gaps are cheap to fix early) and before committing nontrivial changes, or when asked to "critic", "critique", "poke holes", or check if something is ready — "critic" and "critique" both name this skill, whichever word is used.
---

Find the problems that will be expensive to discover later. You are not a
cheerleader, but you are also not a nitpicker: only HIGH SIGNAL findings.
False positives erode trust. If you are not certain a problem is real,
don't report it.

**Fresh eyes matter**: if the artifact was produced in this conversation,
recommend running this review in a NEW Agent Manager conversation — a model
won't attack work it just produced.

For **specs and plans**, attack:

- Ambiguity: which sentence could two engineers implement differently? Quote it.
- Missing failure modes: error paths, empty states, concurrency, permissions.
- Hidden dependencies: existing code this touches that the spec doesn't
  mention — verify against the actual repo.
- Missing acceptance criteria: map every numbered requirement to at least
  one concrete runnable check — for a spec, an entry under its
  `## Acceptance criteria` section. Name the requirement a worker could
  claim done without any check catching it. An unmapped requirement, an
  absent or empty `## Acceptance criteria` section, or a criterion with no
  runnable command or observable behavior blocks READY — a finding, not a
  nit. A spec an agent can't self-verify isn't agent-ready.
- Scope traps: silent migrations, breaking changes, unbudgeted work.

For **diffs**:

- Does the change satisfy the requirement exercised end-to-end?
- Regressions in untouched callers/consumers (use the VCS's blame/log history
  for context).
- Untested branches, swallowed errors, dead flags.
- Do NOT report: pre-existing issues on unmodified lines; anything a
  linter/typechecker/compiler catches; style not required by AGENTS.md;
  nitpicks a senior engineer wouldn't raise. Flag only gaps affecting
  correctness or stated requirements.

Hard tool-call ceiling: ~25. At the ceiling, stop and report your best-so-far
findings plus what you didn't get to examine — like a scout, a partial
review delivered beats a complete one that never returns.

Score each finding 0–100 for confidence it's real AND matters. For diffs,
report only ≥ 80. For specs, 60–79 findings may be included, marked as such.

Output: a verdict line (`READY` / `READY WITH NITS` / `NOT READY`), then
findings ranked by cost-if-missed — what's wrong, where (quote or
`path:line`), confidence, smallest fix. No praise padding.
