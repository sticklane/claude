# Enforce code-mediated control flow for skill-to-skill chaining

Status: open
Priority: P2

## Problem

`specs/critique-breakdown-self-chain-gap` fixed one instance of a bug
class: critique's `SKILL.md` documented a hand-off marker only as prose
("this is the token another stage reads to auto-invoke itself") with no
explicit self-chain imperative of its own, and a live session read the
ambiguity, invented a permission gate that doesn't exist in this repo's
doctrine, and stalled a pipeline that should have auto-continued.

Mining this repo's own past session transcripts (scoped strictly to this
project's own logs; every finding below is generalized and anonymized —
no personal, financial, or unrelated-project content is quoted) found one
further genuine instance of the same failure class, in a different
session, after the corrected gating doctrine (`/build`, `/drain`,
`/prioritize` only) was already in the codebase: an assistant turn lumped
one genuinely gated stage together with two ungated, model-invocable
stages in a single sentence ("running stage-b, then stage-c +
stage-gated — none of these are auto-launched per this repo's gating
rules"), obscuring which stage the gate actually binds and treating all
three as equally gated. The same search also surfaced two correct
counter-examples worth keeping as positive controls: one session that
reasoned "isn't gated so I'll continue straight into it" under the same
ambiguous conditions, and one that correctly cited a skill's literal
`disable-model-invocation: true` frontmatter key as an unambiguous,
machine-checkable gate declaration (predating this repo's later switch to
the narrower launch-authorization contract for that same distinction).

The common thread across both real instances: the condition for whether a
skill hands off to another is expressed as free-text prose a model must
interpret, not as a mechanical predicate or an unambiguous imperative
tied to it. `docs/external-playbooks.md`'s "Skill chaining" section now
records why every comparable framework treats this as settled: LangGraph
routes exclusively through code — routing functions and, for LLM-decided
hand-offs, a structured `Command` object selecting among a closed,
code-declared destination set, never free text; CrewAI's `Process` is a
typed enum with explicit task dependencies, not natural language;
Anthropic's own published criterion is that a "well-defined" step
sequence should be hardcoded, reserving model-driven judgment for
genuinely unpredictable problems (cited there, not restated here). A
skill-to-skill hand-off gated on a mechanical predicate over committed
file state (a `Status:` value, a completion marker) is exactly Anthropic's
"hardcode it" case; leaving it as interpretable prose applies a
judgment-call escape hatch to a decision that isn't a judgment call.

`tests/test_skill_chain_determinism.sh` (already committed, currently RED
— `evals/lint-skill-chain-determinism.sh` does not exist yet) defines the
target contract with four fixtures generalized from the findings above:
two that must be flagged (marker-only mention with no self-chain
imperative; ambiguous multi-stage grouping) and two positive controls
that must pass (an explicit, close-proximity self-chain imperative; a
skill correctly absent from the manifest because it's genuinely
human-gated). This spec builds the gate the test already specifies.

## Solution

1. Add `.claude/rules/deterministic-chaining.md`, a new cross-cutting rule
   (matching this repo's existing `.claude/rules/*.md` pattern —
   `mirror-procedure-discipline.md` is the closest structural precedent)
   stating the invariant: a skill-to-skill hand-off gated on a mechanical
   predicate over committed file state must express that predicate and
   its resulting action as an unambiguous, close-proximity imperative
   (e.g. "invoke `/breakdown` via the Skill tool now"), not as descriptive
   prose about a marker's existence. Cite `docs/external-playbooks.md`'s
   "Skill chaining" section for the cross-framework grounding rather than
   restating it. State explicitly, per this repo's own convention for
   heuristic gates (`mirror-procedure-discipline.md`'s "coverage gate is a
   heuristic with two blind spots" section is the model to follow): the
   mechanical gate below catches known-shaped ambiguity, not full semantic
   equivalence, and a skill with a genuine judgment call in its hand-off
   (not a mechanical predicate) is correctly out of the gate's scope —
   never force a judgment-call hand-off into this mechanism.
2. Build `evals/lint-skill-chain-determinism.sh`, matching the CLI
   contract `tests/test_skill_chain_determinism.sh` already defines:
   invoked as `evals/lint-skill-chain-determinism.sh <manifest-file>`,
   where each manifest line is
   `<skill-md-path>|<condition-substring>|<required-imperative-substring>|<window-lines>`;
   for each line, if `condition-substring` appears in `skill-md-path`,
   `required-imperative-substring` must appear within `window-lines` of
   it, else the gate prints `file:line` and exits non-zero. Style-match
   `evals/lint-ultra-gate.sh` (self-contained, awk-based line-window
   check, `set -u`).
3. Build `tests/skill-chain-manifest.txt`, the real manifest (format
   matching `tests/mirror-procedure-manifest.txt`'s seeded-comment
   convention), with one entry per currently-known self-chain
   relationship: `drain` → `/distill` (terminal capture), `idea` →
   `/design`, `idea` → `/breakdown`, `qa-sweep` → `/critique`, and
   `critique` → `/breakdown` once `specs/critique-breakdown-self-chain-gap`
   lands (cited, not re-specified here — if that spec hasn't merged yet
   when this one is worked, add the manifest line in the same commit that
   adds critique's imperative, not before).
4. Update CLAUDE.md's "Skills may self-chain" bullet to add one sentence
   pointing at `.claude/rules/deterministic-chaining.md` for HOW a
   mechanical-predicate hand-off must be expressed, without altering the
   bullet's existing (a)/(b)/(c) self-chain conditions — this is an
   addition to the bullet, not a rewrite.
5. Add one sentence to `.claude/skills/workflow-author/SKILL.md`'s scoping
   language acknowledging that a mechanical skill-to-skill chain (not a
   judgment-call one) is a legitimate future candidate for conversion into
   a real `.claude/workflows/*.js` script — the stronger enforcement tier
   above the lint gate, following `deep-research.js`'s existing precedent
   — without committing this spec to converting any chain today (see Out
   of scope).
6. Wire `evals/lint-skill-chain-determinism.sh` into CLAUDE.md's "Testing
   changes" section the same way `evals/lint-ultra-gate.sh` is already
   documented there: run it before committing changes to any `SKILL.md`
   with an entry in `tests/skill-chain-manifest.txt`.

## Out of scope

- Converting any existing skill-to-skill chain into an actual
  `.claude/workflows/*.js` script — R5 above only notes the possibility
  in `workflow-author`'s scoping language; doing the conversion is a
  natural, separately-spec'd follow-up once the gate exists and the
  manifest names every mechanical chain explicitly.
- Re-deriving or duplicating the critique→breakdown fix itself — that
  stays `specs/critique-breakdown-self-chain-gap`'s job; this spec only
  adds critique to the manifest once that fix lands.
- Retrofitting an equivalent gate onto the `antigravity/` or `codex/`
  mirrors — those runtimes express hand-offs through their own
  mechanisms (no Skill tool primitive; see `mirror-procedure-discipline.md`
  on load-bearing runtime divergence), and this spec's gate is
  Claude-Code-Skill-tool-specific.
- Adopting the "Stop-hook chain enforcement" or "context-fork" primitives
  `docs/external-playbooks.md`'s "Skill chaining" section already lists as
  available-but-unadopted — both remain deliberately unadopted; this spec
  doesn't reopen that decision.

## Acceptance criteria

- [ ] `bash tests/test_skill_chain_determinism.sh` exits 0 (all five
      assertions pass, including the "gate script exists" precondition —
      currently exits 1).
- [ ] `test -f evals/lint-skill-chain-determinism.sh && test -x evals/lint-skill-chain-determinism.sh`.
- [ ] `test -f tests/skill-chain-manifest.txt` and
      `grep -c '|' tests/skill-chain-manifest.txt` → at least 4 (one per
      known self-chain relationship in Solution item 3, minus critique if
      its own spec hasn't landed yet).
- [ ] `test -f .claude/rules/deterministic-chaining.md` and
      `grep -qi "docs/external-playbooks.md" .claude/rules/deterministic-chaining.md`
      (cites, doesn't restate, per this repo's convention).
- [ ] `grep -c "deterministic-chaining" CLAUDE.md` → at least 1 (currently
      0; confirmed absent at authoring time).
- [ ] `grep -c "skill-to-skill" .claude/skills/workflow-author/SKILL.md` →
      at least 1 (currently 0; confirmed absent at authoring time).
- [ ] `grep -q "lint-skill-chain-determinism" CLAUDE.md` — the gate is
      wired into "Testing changes" alongside `lint-ultra-gate.sh`.
