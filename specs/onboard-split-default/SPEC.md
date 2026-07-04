# /onboard writes the orientation split by default

## Problem

/onboard today writes an all-in-one CLAUDE.md and offers a root AGENTS.md only
as an optional, pointer-only interop file (`.claude/skills/onboard/SKILL.md:67`).
The repo-orientation spec landed the better pattern in this repo itself: a root
AGENTS.md carrying orientation (map, state, verified commands) with CLAUDE.md
holding conventions plus an `@AGENTS.md` bridge — one source of truth read
natively by Codex/Jules/Kiro/Copilot and imported by Claude Code. Owner decision
2026-07-03, after a four-vendor guidance review (evidence/vendor-research.md,
which extends docs/external-playbooks.md with GitHub Copilot coding-agent
specifics): the split is the standard for every repo the toolkit onboards, not
an offer. /onboard should produce it by default.

## Solution

Rewrite /onboard's deliverable definition: the default output of an onboard run
is the pair — root `AGENTS.md` (purpose paragraph, `## Repo map` with one pointer
line per top-level dir and generated/vendored dirs marked "generated — don't
read", `## Commands` verified by running, `## State` pointing at docs/TASKS.md
or specs/ or "no task tracking" — same section names the repo-orientation spec
landed in this repo's own AGENTS.md) and `CLAUDE.md` (conventions, gotchas, checks,
with the `@AGENTS.md` bridge line in its first 10 lines). Both ≤200 lines. The
step-5 "offer AGENTS.md" bullet is replaced; the verify-by-running doctrine and
the per-line pruning test are unchanged and apply to both files. Mirror the
change into the Antigravity port's onboard skill, where AGENTS.md is already
the native context file (its guidance becomes: same structure, no bridge line
needed).

## Requirements

- R1: `.claude/skills/onboard/SKILL.md` defines the default deliverable as the
  AGENTS.md+CLAUDE.md split described above, including the four `## Repo map` /
  `## Commands` / `## State` / bridge-line requirements; the phrase
  "pointer-only" no longer appears in the file (marker: it appears once today,
  so the grep cannot pass vacuously).
- R2: onboarding an already-onboarded repo (CLAUDE.md exists, no AGENTS.md, or
  a template-debris AGENTS.md lacking `## Repo map`) is covered by an explicit
  migration note: move orientation content out of CLAUDE.md into AGENTS.md,
  add the bridge line, delete duplicated prose.
- R3: `antigravity/.agents/skills/onboard/SKILL.md` mirrors R1/R2 with the
  bridge-line requirement replaced by one sentence noting AGENTS.md is
  Antigravity's native context file.
- R4: `specs/onboard-split-default/evidence/vendor-research.md` records the
  2026-07-03 four-vendor research (already written; committed with this spec).
- R5: `plugin.json` minor version bumps by one from the value found, unless
  landing in a commit-set already carrying a combined bump.

## Out of scope

- Any repo outside this toolkit: rolling the split out to the owner's active
  repos is machine-personal work driven by running /onboard there, tracked by
  the owner's local repo-index audit — no repo list or rollout state belongs in
  this repo.
- Changes to /gate, bin/install-gates, or check.sh templates.
- The toolkit repo's own AGENTS.md/CLAUDE.md (already conformant via
  repo-orientation).

## Acceptance criteria

- [ ] `grep -c 'pointer-only' .claude/skills/onboard/SKILL.md` outputs 0 (R1)
- [ ] `grep -q '## Repo map' .claude/skills/onboard/SKILL.md && grep -q '## Commands' .claude/skills/onboard/SKILL.md && grep -q '## State' .claude/skills/onboard/SKILL.md && grep -q '@AGENTS.md' .claude/skills/onboard/SKILL.md` (R1)
- [ ] `grep -qi 'migration' .claude/skills/onboard/SKILL.md || grep -qi 'already-onboarded' .claude/skills/onboard/SKILL.md` (R2)
- [ ] `grep -q '## Repo map' antigravity/.agents/skills/onboard/SKILL.md && grep -qi 'native' antigravity/.agents/skills/onboard/SKILL.md` (R3)
- [ ] `test -s specs/onboard-split-default/evidence/vendor-research.md` (R4)
- [ ] plugin.json minor version strictly greater than pre-implementation value, in the implementing task's evidence (R5)
- [ ] End to end: run /onboard against a scratch repo (e.g. a temp dir with a
  small Node or Go project); the run produces AGENTS.md with all three sections
  and verified commands, CLAUDE.md with the bridge line, both ≤200 lines.

## Open questions

(none — the split-as-default decision is the owner's, recorded 2026-07-03.)

## Parallelization

Decomposed 2026-07-03 into a single task (tasks/01) — the mirror convention
("mirror the change there in the same commit") fuses skill edit, antigravity
mirror, and version bump into one reviewable commit. Wave placement lives in
[specs/QUEUE.md](../QUEUE.md) (single copy, per convention): osd 01 serializes
behind wte 05 on the plugin.json bump chain; no queue-2 task touches the
onboard skill files (verified by Touch-header grep; chaining-antipatterns 02,
the previous collision, is done).
