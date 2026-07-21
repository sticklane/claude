# agentprof skillcheck — skill trigger + outcome audit

## Problem

Skill authors in this repo iterate on a `SKILL.md`'s `description` (trigger
phrases) and body procedure by hand: run it in a fresh session, watch where
it stalls, guess whether the wording will generalize to real usage. There is
no repeatable way to check, from actual accumulated session history, whether
a skill under development (a) is triggering on the phrasing its author
intended — not misfiring on unrelated requests, not silently missed on
requests that should have matched — and (b) is actually landing successful
outcomes when it does run, as opposed to ending in a state the transcript's
own closing message makes sound fine but wasn't. `evals/` fixtures test
prepared scenarios; nothing today looks at the noisy reality of how a skill
actually got used across real sessions. This spec adds a `skillcheck`
subcommand to the existing `agentprof` CLI (Go, `agentprof/`) that reads this
machine's Claude Code transcripts, classifies every `Skill` tool invocation
found, flags likely misses, and reports per-skill trigger-accuracy and
outcome-success stats a skill author reads while iterating — the same way
they'd read `agentprof`'s existing cost report.

## Solution

Add `agentprof/cmd_skillcheck.go` (+ `cmd_skillcheck_test.go`), registered in
`agentprof/main.go`'s subcommand switch (`agentprof/main.go:26-36` pattern)
alongside the existing `claude`/`gcp`/`vertex`/`otel`/`antigravity`/`build`
cases, as `case "skillcheck":`. **It does NOT reuse `internal/claude`'s
unexported parsing internals as-is** — `transcriptLine`, `turnRec`,
`commandSkillFrame`, and friends are unexported to `internal/claude`, and
`cmd_skillcheck.go` lives in `package main`, so none of that struct surface
is reachable from it. That package's only exported entrypoint today
(`Collect*(...) → ([]schema.Sample, []Turn, Stats)`) is cost/attribution-
shaped and carries none of what classification needs: the raw `Skill`
`tool_use` block (`input.skill`/`input.args`) paired with its `tool_result`,
per-turn user↔assistant adjacency (needed for self-chain detection), or the
per-turn `<command-name>` tag (needed for slash-command detection). This
spec therefore REQUIRES adding new exported accessors to `internal/claude`
— a `SkillInvocations(...)` (or similarly-named) function returning, per
invocation: the skill name/args, its paired result, the preceding
`<command-name>` tag if any, and whether an intervening user turn preceded
it — and `cmd_skillcheck.go` consumes that new exported API. This is
real, budgeted implementation work (part of R2 below), not free reuse of
existing internals; only the JSONL-file-walking/subagent-linking underneath
that new accessor is genuinely shared with the `claude` subcommand's
existing code path. It is a read-only reporting tool: it never mutates a
transcript, a `SKILL.md`, or any repo file other than writing its own
report output.

For each transcript session (main + linked subagent files), `skillcheck`:

1. Walks `tool_use` blocks named `Skill` (per scout report: `{"type":
"tool_use", "name": "Skill", "input": {"skill": "<name>", "args": "..."}}`)
   and their paired `tool_result`.
2. **Scopes the trigger-correctness audit to model-decided auto-triggers
   only** — invocations where the model itself chose to fire a skill based
   on its `description`. This EXCLUDES two populations that are not a model
   trigger decision and would corrupt the stats if audited as
   correct/misfired: (a) explicit slash-command invocations, detectable by
   a preceding `<command-name>` tag in the triggering user turn (per this
   spec's scout report on the transcript format); (b) skill self-chains,
   detectable as a `Skill` tool_use occurring inside an assistant turn with
   no new user message directly preceding it (the existing skill's own turn
   invoking the next one). Both excluded populations are still counted and
   reported (as `explicit_invocation`/`self_chained` in the per-skill
   aggregate) but never scored `correctly-triggered`/`misfired`. A skill
   carrying `disable-model-invocation: true` is additionally exempt from
   trigger-correctness scoring outright (per CLAUDE.md's authoring
   convention, cited not restated) — it never auto-triggers, so it has no
   model-trigger population to audit; every one of its invocations counts
   as `explicit_invocation`.
3. For the model-auto-trigger population, reads the invoked skill's own
   `description:` frontmatter as the trigger-correctness reference, resolved
   in this fixed order: (a) `.claude/skills/<name>/SKILL.md` relative to the
   transcript's recorded `cwd`; (b) if absent, the plugin cache path
   `~/.claude/plugins/<marketplace>/<plugin>/skills/<name>/SKILL.md` (the
   installed-plugin layout `.claude-plugin/plugin.json`'s `skills:` field
   points at, resolved the same way the harness resolves a plugin skill at
   runtime); (c) if neither resolves — the skill was renamed or removed
   since the transcript was recorded — classify the invocation `unresolvable`
   (a third trigger verdict alongside correctly-triggered/misfired, reported
   separately, never silently dropped). Classifies each resolved invocation
   **correctly-triggered** or **misfired** by comparing the description's
   stated trigger phrases/use-cases against the preceding user turn(s), via
   an LLM judge call (see Trigger judge below).
4. Separately scans user turns that did NOT result in a `Skill` call against
   every **currently-installed** skill's description (the skill set as of
   when `skillcheck` runs, not as of when the transcript was recorded — a
   skill added after a transcript's session obviously couldn't have fired in
   it, but auditing "would this NEW skill's description match this OLD
   transcript" is exactly the forward-looking signal a skill author
   iterating on a new/changed description wants), flagging **possible
   misses** via a **keyword match only** (substring/phrase match between the
   skill's declared trigger phrases and the user turn's text — deterministic,
   no LLM call, no embeddings) — reported separately from confirmed
   misfires/triggers and clearly labeled as needing manual review, never
   asserted as fact.
5. For each `correctly-triggered` invocation (never for `misfired` or
   `unresolvable` ones — there is no successful outcome to score for an
   invocation that shouldn't have fired), an outcome judge scores
   **success**, **failure**, or **unknown** against the skill's
   `outcome-rubric:` frontmatter text when the skill declares one, else the
   fixed generic rubric (below) — the custom rubric REPLACES the generic one
   for that skill's invocations, it is never both at once.

### Trigger judge and outcome judge (research-grounded design)

Per this spec's research pass (frontier literature on trajectory evaluation,
Anthropic's "Demystifying evals for AI agents," and agent-benchmark tool-use
evaluation practice — synthesized fresh for this spec, no prior in-repo
`Verified:` stamp existed on this topic):

- **Trigger and outcome are two separately-scored axes**, never merged into
  one holistic verdict — this mirrors the established split between
  "tool-selection appropriateness" and "outcome quality" the research found
  converging across an academic tool-use survey and Anthropic's own agent
  eval guidance.
- **Each judge call is scoped to one dimension** (a per-rubric-line
  isolated call, not one prompt asking for everything at once), matching
  Anthropic's documented recommendation, and **every judge call may answer
  `unknown`** rather than being forced to pick success/failure — this is
  the specific mechanism Anthropic's own guidance uses to suppress judge
  hallucination under uncertainty.
- **The outcome judge is explicitly instructed not to trust the invocation's
  own closing message as evidence of success.** This is the single most
  load-bearing finding from the research: LLM judges anchor on confident,
  assertive closing language as a completion signal, which causes them to
  badly under-detect "false success" (an agent's own transcript claiming
  done when the actual work wasn't) — a failure mode measured at 13-79% of
  failures depending on model family, not a rare edge case. The judge prompt
  must ask for concrete evidence in the transcript body (a verifier's PASS,
  a passing test run, a merged commit, ticked acceptance boxes with cited
  commands) rather than accepting the invocation's self-report, and must be
  told this explicitly.
- **Generic outcome rubric** (applied when a skill declares no custom one):
  did the invocation reach a terminal, non-error state (not left mid-flight,
  not silently abandoned); was there an explicit error/blocked/deferred/
  DEFERRED signal in the transcript; was there a user correction or redo of
  the same request shortly after (a strong signal the first attempt did not
  actually satisfy the user, independent of how the transcript's own closing
  message framed it).
- **Skill-specific rubric (optional).** A `SKILL.md` may declare its own
  success criteria via an `outcome-rubric:` frontmatter field (short prose:
  what "done well" looks like for THIS skill specifically — e.g. drain's
  rubric names a merged branch + green gates, critique's rubric names a
  ranked findings list with no vague/unconfirmed items). When present, it
  REPLACES the generic rubric for that skill's invocations (never both at
  once — see step 5); when absent, the generic rubric applies. This is an
  additive, optional frontmatter field — no existing `SKILL.md` needs to
  change for `skillcheck` to work.
- **Judge invocation mechanism: mirror `agentprof/internal/naming`'s
  pattern, not a new one.** `agentprof` already shells out to a Claude judge
  process for its turn-naming feature via
  `agentprof/internal/naming/cli.go` (`claude -p <prompt> --model <tier>
--output-format json`, with `CLAUDE_CONFIG_DIR` exported to a scratch
  directory so judge sessions never write into the very `~/.claude/projects`
  tree `skillcheck` is scanning — self-pollution the naming feature already
  solved once and this spec must not reintroduce). `skillcheck`'s trigger
  and outcome judges use the same subprocess-invocation shape and the same
  scratch-`CLAUDE_CONFIG_DIR` isolation, and are abstracted behind a judge
  interface mirroring `naming.Namer`/`naming.CLINamer` — a fake
  implementation satisfies this interface for the deterministic unit tests
  in the Acceptance criteria (see below); production code uses the real
  CLI-backed implementation.
- **Judge model tier: scout-tier by default, configurable, with a pinned
  tier→model map.** `--judge-tier` accepts the same tier vocabulary as
  `.claude/rules/token-discipline.md` (`scout`, `session`, `deep`,
  `frontier`); `skillcheck` resolves each tier to a concrete `--model` value
  via the same mapping table `runtimes/claude-code.md` already pins for
  this toolkit's tier language (cited, not restated — `skillcheck` reads or
  mirrors that table rather than inventing its own tier-to-model constants).
  Default tier: `scout` — a fresh `claude -p` judge subprocess has nothing
  to inherit, so `session-tier`'s `inherit` mapping is not a usable
  `--model` value here; `internal/naming/cli.go` hits the same constraint
  and hardcodes a concrete cheap model rather than "inherit", which this
  spec follows.

### Report shape

`agentprof skillcheck [--days N | --since RFC3339] [--skill <name>] [--judge-tier <tier>] [-o path.json]`
(flag shape matches the existing `claude` subcommand's `--days`/`--since`/`-o`
conventions). Output: one JSON report (default) or a human-readable table
(`--format table`), grouped per skill:

```json
{
  "skill": "drain",
  "invocations": 12,
  "trigger": { "correct": 10, "misfired": 2, "possible_misses": 1 },
  "outcome": { "success": 9, "failure": 2, "unknown": 1 },
  "findings": [
    {
      "session": "<sessionId>",
      "verdict": "misfired",
      "evidence": "...",
      "transcript_ref": "<path>:<line>"
    }
  ]
}
```

Every non-obvious verdict (misfired, possible-miss, failure, unknown) carries
a one-line evidence citation pointing back at the source transcript
(path + line), so a skill author can jump straight to the real conversation
rather than trusting the verdict blind — this is the same "evidence over
assertion" principle `docs/anthropic-playbook.md`'s verification-first
section already states for this repo's own review/verification practice
(cited, not restated).

## Requirements

- R1: `agentprof skillcheck` is a registered subcommand in `agentprof/main.go`'s
  switch, following the existing `claude`/`gcp`/`vertex`/`otel`/`antigravity`/
  `build` pattern.
- R2: Adds a new exported accessor to `agentprof/internal/claude` (e.g.
  `SkillInvocations`) that returns, per invocation, the skill name/args, its
  paired `tool_result`, the preceding `<command-name>` tag if any, and
  whether an intervening user turn preceded it — built on top of that
  package's existing JSONL-file-walking and subagent-linking machinery
  (genuinely shared, not re-implemented) rather than a second independent
  parser. `cmd_skillcheck.go` consumes only this new exported surface, never
  the package's unexported internals directly.
- R3: Classifies every model-decided auto-trigger `Skill` tool_use found in
  the scanned transcripts (excluding explicit slash-command invocations and
  skill self-chains, per the Solution's population definition) as
  `correctly-triggered`, `misfired`, or `unresolvable` (skill's SKILL.md not
  found at either resolution path), citing the invoked skill's own
  `description:` frontmatter as the reference when resolved.
- R3a: Explicit-invocation and self-chained `Skill` tool_use instances are
  still counted and reported (as `explicit_invocation`/`self_chained`) but
  never scored `correctly-triggered`/`misfired`.
- R4: A skill with `disable-model-invocation: true` has every invocation
  counted as `explicit_invocation`, never scored for trigger-correctness.
- R5: Separately flags `possible-miss` candidates for user turns with no
  matching `Skill` call, via a deterministic keyword/phrase match (no LLM
  call) against every currently-installed skill's declared trigger phrases
  — clearly distinguished from confirmed misfires in the report.
- R6: For each `correctly-triggered` invocation, scores outcome as
  `success` / `failure` / `unknown`, using a skill's own `outcome-rubric:`
  frontmatter value when present (replacing, never supplementing, the
  generic rubric) and the generic rubric otherwise. `misfired` and
  `unresolvable` invocations are never outcome-scored.
- R7: The outcome judge prompt explicitly instructs the judge not to trust
  the invocation's own closing-message framing as evidence of success, and
  to require concrete in-transcript evidence.
- R8: Every judge call is scoped to a single rubric dimension and may return
  `unknown`.
- R9: `--judge-tier` overrides the default `scout` judge tier (matching
  `internal/naming/cli.go`'s own precedent of hardcoding a concrete cheap
  model rather than "inherit" for a subprocess judge call — `session-tier`
  maps to `inherit` in `runtimes/claude-code.md`'s tier table, which is not
  a usable `--model` value for a fresh `claude -p` subprocess with nothing
  to inherit from); each tier resolves to a concrete model via the same
  mapping table (cited, not restated).
- R10: Report output includes a per-skill aggregate (counts per
  trigger/outcome/population category — `correct`, `misfired`,
  `unresolvable`, `explicit_invocation`, `self_chained`, `possible_misses`,
  `success`, `failure`, `unknown`) and a per-finding list with a transcript
  path+line evidence citation for every verdict other than `correct` or
  `success`.
- R11: `--days`/`--since`/`-o` flags match the existing `claude` subcommand's
  flag shape and defaults.
- R12: Both judges (trigger and outcome) are invoked via a subprocess
  mechanism mirroring `agentprof/internal/naming/cli.go`'s pattern (`claude
-p ... --model <tier> --output-format json`), with `CLAUDE_CONFIG_DIR` set
  to a scratch directory so judge sessions never write into the
  `~/.claude/projects` tree being scanned, abstracted behind a judge
  interface (mirroring `naming.Namer`/`naming.CLINamer`) that a fake
  implementation can satisfy for tests.
- R13: `--format` accepts `json` (default) or `table`; `table` renders the
  same per-skill aggregate as human-readable columns rather than the JSON
  shape in Report shape above.

## Out of scope

- No cross-run trend tracking / persistent history database — each run is a
  fresh snapshot over whatever transcripts it's pointed at; comparing two
  runs by eye (before/after a `SKILL.md` edit) is the user's job, not the
  tool's.
- No auto-suggested description/wording fixes — the tool reports where a
  skill misfired, was missed, or failed; it never proposes replacement
  trigger-phrase text.
- No real-time/live monitoring — batch/on-demand only, run manually during
  skill development.
- No non-Claude-Code transcript sources for v1 — reads this machine's
  `~/.claude/projects/*/*.jsonl` only (matching the `claude` subcommand's
  existing default source); `antigravity`/other-runtime transcript support
  is a natural follow-on given `agentprof antigravity` already exists as a
  sibling subcommand, but is not part of this spec.
- No fix to the possible-miss detector's precision beyond "clearly labeled
  low-confidence" — it is a manual-review aid, not asserted as ground truth,
  and this spec does not commit to a specific accuracy bar for it.

## Acceptance criteria

- [ ] `cd agentprof && go build ./...` succeeds (compiles cleanly with the
      new subcommand).
- [ ] `cd agentprof && go test ./... -run TestSkillcheck` passes — unit
      tests over the deterministic parts, using a **fake judge**
      implementation (satisfying the R12 judge interface) so the tests never
      make a network/subprocess call and are fully deterministic: - Skill tool_use detection and population classification (auto-trigger
      vs `explicit_invocation` vs `self_chained`) against small synthetic
      fixture transcripts covering each population. - SKILL.md resolution order (personal path, then plugin-cache path,
      then `unresolvable`) against fixtures exercising all three. - `disable-model-invocation: true` exemption. - **The fake judge records what it was called with**: the test asserts
      the outcome-judge call for a rubric-bearing skill's invocation
      received that skill's exact `outcome-rubric:` text (not the generic
      rubric), and that a non-rubric skill's invocation received the
      generic rubric text — proving R6's replace behavior from the judge's
      actual input, not from report output a worker could hardcode. - The outcome-judge prompt string passed to the judge interface
      contains the R7 "do not trust the closing message; require concrete
      in-transcript evidence" instruction, asserted by substring match on
      the prompt the fake judge received — not on any report field. - Keyword-match possible-miss detection against a fixture with a known
      matching phrase and a fixture with none. - Report JSON shape (R10's category set) and evidence-citation
      (path+line) formatting.
      TDD red-first per this spec's Production rigor.
- [ ] `agentprof skillcheck --help` documents `--days`, `--since`, `--skill`,
      `--judge-tier`, `-o`, `--format`.
- [ ] A command-construction test (no subprocess executed — mirroring
      `internal/naming/cli_test.go`'s pattern of asserting on the built
      `*exec.Cmd` without running it) asserts the real CLI-backed judge
      implementation's built command carries `CLAUDE_CONFIG_DIR=<scratch>`
      in its environment, proving the self-pollution guard R12 requires is
      actually wired into the production path, not just the fake used by
      the other unit tests.
- [ ] `agentprof skillcheck --format table` over a fixture with known
      trigger/outcome counts emits output that a small parser (e.g. split
      on whitespace/columns) confirms contains R10's category counts —
      parse-then-assert, not a substring/exact-string match — proving R13's
      `table` format actually renders the aggregate rather than merely being
      an accepted flag value.
- [ ] MANUAL-PENDING (requires a live `claude -p` judge call and real
      accumulated history — not runnable by an unattended worker; a human
      or an attended session runs this and records the result): run
      `agentprof skillcheck` against this machine's real accumulated
      `~/.claude/projects/-Users-sjaconette-claude/*.jsonl` history and
      manually confirm at least 5 distinct verdicts (spanning trigger and
      outcome categories) against their cited evidence lines are plausible
      on read.
- [ ] MANUAL-PENDING (same reason as above): a `SKILL.md` with an
      `outcome-rubric:` frontmatter field, when included in the real
      end-to-end run above, produces a report whose per-finding evidence for
      that skill's invocations reflects the custom rubric having been
      applied (cross-checked against the unit test's judge-input assertion
      above, which is the automated proof; this manual step is a real-world
      sanity read, not the primary verification).

## Open questions

(none — resolved via interview + research above)
