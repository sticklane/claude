# Model- and runtime-agnostic toolkit (Claude defaults)

## Problem

The toolkit hard-codes its model choices and its runtime CLI in ~15 places
(scout pins `model: haiku`; Haiku named in token-discipline, README,
autopilot and gate references; `claude -p` command templates in the drain
and autopilot references and `evals/run.sh`), so using it with another
runtime — Antigravity beyond the existing port, gemini-cli, whatever comes
next — means hand-editing prose across many files. The antigravity port
already invented the needed abstraction ("Flash-class model") but only on
its side of the mirror. Users want Claude models as the default with the
ability to select other models/runtimes per repo.

## Solution

A runtime-profile layer, decided with the maintainer (all four interview
recommendations adopted): core skills/agents speak two abstract tiers —
`scout-tier` (cheap, fast, read-only reconnaissance) and `session-tier`
(the conversation's model) — and defer concrete model names and headless
command templates to one profile file per runtime under `runtimes/`.
`runtimes/claude-code.md` ships as the default and reproduces today's
exact behavior; consuming repos select another profile with a one-line
`.claude/runtime.md`; `evals/run.sh` gains two environment overrides
(`RUNNER_CMD` for the headless command, `EVALS_ROOT` for scenario
discovery) so portability is testable with a stub CLI and a throwaway
scenario tree, never touching the real evalsets. Core prose is de-Clauded
to tier language with the Claude default named inline; a `docs/porting.md`
guide maps toolkit concepts onto other runtimes. New marker phrases
("scout-tier", "active runtime profile", "RUNNER_CMD", "EVALS_ROOT") do
not exist in the repo today, so the acceptance greps below cannot pass
vacuously. Product-internal models the toolkit does not choose (the
`/goal` transcript evaluator) are explicitly NOT tier vocabulary.

## Requirements

- R1: `runtimes/claude-code.md`, `runtimes/antigravity.md`, and
  `runtimes/gemini-cli.md` exist, each with the same three sections:
  `## Tiers` (scout-tier and session-tier mapped to concrete models —
  Claude: Haiku + effort low / inherit; Antigravity: Flash-class /
  session model; gemini-cli: its flash / pro equivalents), `## Headless`
  (the runtime's non-interactive command template with placeholders for
  prompt, allowlist, and turn/step cap — Antigravity: states none exists,
  Agent Manager launches instead), and `## Notes` (config file locations,
  permission-mode equivalents, and for gemini-cli a line recording how
  the command syntax was verified, or that it requires verification
  before first use).
- R2: `.claude/agents/scout.md` keeps `model: haiku` (the Claude default)
  and gains a body line naming its tier, phrased fallback-safe:
  "scout-tier — mapping for other runtimes in `runtimes/` (toolkit repo;
  absent in plugin installs and eval fixtures, where the claude-code
  defaults above apply)". `critic.md` and `verifier.md` need no change
  (`model: inherit` is already tier-neutral).
- R3: prose model mentions in exactly two files become tier language
  with the Claude default in parentheses, using the phrase "scout-tier"
  verbatim — all four Haiku mentions, no others:
  `.claude/rules/token-discipline.md` line ~10 (the scout definition)
  and line ~21 ("Mechanical or lookup work → scout-tier (Claude default:
  Haiku at low effort)"), and `README.md`'s scout table row and
  token-cost bullet. The autopilot and gate references' Haiku mentions
  are NOT tier vocabulary — they describe Claude Code's built-in `/goal`
  transcript evaluator, which no profile selects; reword those two lines
  as "the runtime's built-in transcript evaluator (Claude Code: Haiku)"
  without the word scout-tier.
- R4: the headless command templates in
  `.claude/skills/drain/reference.md` and
  `.claude/skills/autopilot/reference.md` are introduced by the phrase
  "active runtime profile": one sentence stating the template below is
  the Claude Code profile's rendering and other runtimes substitute
  their profile's `## Headless` template, phrased fallback-safe per R5's
  citation rule. The concrete `claude -p` blocks stay as-is (they ARE
  the default profile's rendering).
- R5: runtime selection: a consuming repo may create `.claude/runtime.md`
  whose first non-comment line is `runtime: <profile-name>`; absent file
  means `claude-code`. The convention is documented in one place —
  `runtimes/README.md` — and cited (not restated) by the drain and
  autopilot references. Every citation of `runtimes/` from files that
  ship in the plugin (scout.md, the two skill references) must carry the
  fallback clause: the directory lives in the toolkit repo, is absent in
  plugin installs and eval fixtures, and its absence means the
  claude-code defaults apply. No new unresolvable pointers.
- R6: evals runner parameterization, fully specified:
  - `evals/run.sh` honors `RUNNER_CMD` (env): when set, the runner
    executes it word-split, inside the existing `cd "$EVAL_DIR"` +
    `timeout 900` wrapper, with the scenario's prompt appended as the
    final argument; the scenario's resolved allowlist is exported to the
    child as `ALLOWED_TOOLS` (custom runners consume or ignore it —
    documented either way). Because execution happens inside the fixture
    dir, `RUNNER_CMD`'s first word must be absolute or PATH-resolvable —
    documented next to the override. When unset, behavior is byte-identical to
    today's `claude -p … --allowed-tools …` invocation.
  - `evals/run.sh` honors `EVALS_ROOT` (env): scenario discovery scans
    `$EVALS_ROOT/<skill>/<NN-name>/` instead of the toolkit's `evals/`;
    default is today's location. Skill provisioning still sources from
    the toolkit checkout.
  - `evals/stub-cli.sh` ships: a no-model shell stub that reads its
    final argument (the prompt) and writes the fixture artifact the
    selftest's assert expects.
  - `evals/runner-selftest.sh` ships: builds a throwaway scenario tree
    under `mktemp -d` (naming a real, small toolkit skill — e.g.
    handoff — so provisioning succeeds), then invokes
    `EVALS_ROOT=<tmp> RUNNER_CMD="${RUNNER_CMD:-$(pwd)/evals/stub-cli.sh}"
    ./evals/run.sh <skill>` and asserts the runner's pass/fail plumbing
    (PASS line, exit 0; then a deliberately failing assert → FAIL line,
    exit 1). The selftest scenario is never discoverable by a plain
    `./evals/run.sh` (it lives only in the temp tree).
- R7: `docs/porting.md` exists: a concept-mapping table (skills, agents,
  rules, hooks, headless, permission modes) with columns for Claude Code,
  Antigravity (citing the existing `antigravity/` port), and gemini-cli
  (citing its extension/GEMINI.md equivalents), plus a short "to add a
  runtime" checklist: write `runtimes/<name>.md`, port or map each
  concept, run `evals/runner-selftest.sh` with the runtime's CLI in
  `RUNNER_CMD`.
- R8: antigravity mirrors: `antigravity/AGENTS.md` adopts the same
  tier phrasing for its token-discipline section ("scout-tier"), and
  `antigravity/README.md`'s mapping table gains a row pointing at
  `runtimes/antigravity.md`.
- R9: README gains a short "Other runtimes and models" subsection under
  Install: Claude models are the default; select another runtime via
  `.claude/runtime.md` + `runtimes/`; porting guide at `docs/porting.md`.
  `CLAUDE.md`'s conventions gain one bullet, worded to match the
  deliverables: "concrete model names and CLI command templates appear
  in core files only as the inline Claude default; the mappings for
  other runtimes live in `runtimes/` profiles — new skills use tier
  language plus the inline default, never a bare model name."
- R10: `.claude-plugin/plugin.json` version bumped (0.3.x → 0.4.0) by
  this spec — it owns the bump for this change.

## Out of scope

- A gemini-cli port directory (antigravity-style) — the porting guide is
  the v1 deliverable; a full port is its own future spec.
- Shipping `runtimes/` or `docs/` inside the plugin (plugin component
  paths cover skills/agents only) — which is exactly why R2/R4/R5
  mandate fallback-safe citations rather than bare pointers.
- Auto-detecting the runtime; selection is explicit config only.
- Changing the antigravity port's structure (it remains the reference
  port; profiles describe it, they don't replace it).
- Per-invocation runtime flags (per-repo config only in v1).
- Fixing the pre-existing headless-template defects found by the branch
  code review (unresolvable /agentic:build pointer, Budget free-text →
  --max-turns, allowlist coverage) — those are review findings with their
  own fix path; this spec only wraps the templates in profile language
  without changing their contracts.

## Acceptance criteria

- [ ] `test -f runtimes/claude-code.md && test -f runtimes/antigravity.md && test -f runtimes/gemini-cli.md && for f in runtimes/claude-code.md runtimes/antigravity.md runtimes/gemini-cli.md; do grep -q "^## Tiers" $f && grep -q "^## Headless" $f && grep -q "^## Notes" $f || exit 1; done` (R1)
- [ ] `grep -q "scout-tier" .claude/agents/scout.md && grep -q "model: haiku" .claude/agents/scout.md && grep -qi "absent in plugin installs" .claude/agents/scout.md` (R2)
- [ ] `grep -q "scout-tier" .claude/rules/token-discipline.md && grep -q "scout-tier" README.md` (R3)
- [ ] `grep -qi "built-in transcript evaluator" .claude/skills/autopilot/reference.md && grep -qi "built-in transcript evaluator" .claude/skills/gate/reference.md && ! grep -qi "scout-tier" .claude/skills/autopilot/reference.md && ! grep -qi "scout-tier" .claude/skills/gate/reference.md` (R3 — evaluator lines reworded, no tier mislabel)
- [ ] `grep -q "active runtime profile" .claude/skills/drain/reference.md && grep -q "active runtime profile" .claude/skills/autopilot/reference.md && grep -q "claude -p" .claude/skills/drain/reference.md` (R4)
- [ ] `test -f runtimes/README.md && grep -q "runtime:" runtimes/README.md && grep -q ".claude/runtime.md" runtimes/README.md` (R5)
- [ ] `grep -q "absent in plugin installs" .claude/skills/drain/reference.md && grep -q "absent in plugin installs" .claude/skills/autopilot/reference.md` (R5 fallback clauses in the plugin-shipped citers; scout.md's is checked under R2)
- [ ] `grep -q "RUNNER_CMD" evals/run.sh && grep -q "EVALS_ROOT" evals/run.sh && grep -q "ALLOWED_TOOLS" evals/run.sh && bash -n evals/run.sh` (R6)
- [ ] `test -x evals/stub-cli.sh && test -x evals/runner-selftest.sh && bash -n evals/stub-cli.sh && bash -n evals/runner-selftest.sh` (R6)
- [ ] `./evals/runner-selftest.sh` exits 0 on a machine with no model access (uses the shipped stub by default; both the PASS and FAIL plumbing paths asserted) (R6 end-to-end)
- [ ] `test -f docs/porting.md && grep -qi "gemini" docs/porting.md && grep -qi "antigravity" docs/porting.md && grep -q "runner-selftest" docs/porting.md` (R7)
- [ ] `grep -q "scout-tier" antigravity/AGENTS.md && grep -q "runtimes/antigravity.md" antigravity/README.md` (R8)
- [ ] `grep -qi "Other runtimes" README.md && grep -q "runtimes/" CLAUDE.md` (R9)
- [ ] `python3 -c "import json,sys; v=json.load(open('.claude-plugin/plugin.json'))['version']; sys.exit(0 if tuple(map(int,v.split('.')))>=(0,4,0) else 1)"` (R10)
- [ ] End to end: `./evals/run.sh breakdown` still passes with both env vars unset (no behavior change for the Claude default), and `./evals/runner-selftest.sh` proves a non-Claude command drives the same harness without touching the committed evalsets.

## Open questions

(none — the four interview decisions are recorded in Solution; the
maintainer approved the recommended option for each and may flip any
before implementation.)
