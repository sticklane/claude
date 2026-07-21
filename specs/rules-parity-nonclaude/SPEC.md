# Rules parity: bind Claude-only doctrine to the non-Claude runtimes

Status: open
Priority: P2

## Problem

The toolkit's always-on governance is Claude-only. `.claude/rules/*.md`
(eight files: quality-discipline, token-discipline, concurrent-sessions,
human-blockers, mirror-procedure-discipline, mirror-verification,
untrusted-data, browser-automation-handoffs) and `CLAUDE.md`'s
`## Authoring conventions` have **no ported counterpart** under `antigravity/`
or `codex/`. `antigravity/AGENTS.md` re-expresses the *spirit* of a few
(quality, untrusted-data, concurrent-sessions) inline, reworded for its
runtime; `codex/AGENTS.md` defers to Antigravity only for "shared pipeline
orientation." So a rule that should bind every agent — e.g. untrusted-data
(a prompt-injection defense) or the human-launch gates — binds Claude agents
and silently skips Antigravity/Gemini and Codex/GPT agents.

This was surfaced while shipping `specs/agentic-prose-tells` (which closes the
gap for its own writing doctrine only, R4 there); this spec addresses the
systemic case the operator asked to close: "ensure all the rules etc apply
equally to non-claude agents."

## Solution

Two stages. First, an audit that produces a coverage matrix — each rule /
convention × each runtime × {binds natively | absorbed in spirit | absent} —
so the decision is evidence-based, not guessed. Second, port the load-bearing
rules that are absent or only spirit-absorbed into each runtime's real
governance doc (`antigravity/AGENTS.md`; `codex/AGENTS.md` where its deferral
does not reach), classifying every divergence load-bearing vs incidental per
`.claude/rules/mirror-procedure-discipline.md`, and seeding parity-manifest
entries so the gate holds them in lockstep.

A rule that is genuinely Claude-mechanism-specific (e.g. cache-economics tied
to Claude prompt-caching, or hooks in Claude's JSON shape) is recorded as
load-bearing-divergent and NOT ported — the audit must distinguish "should
bind everywhere but doesn't" from "correctly Claude-only."

## Requirements

- **R1**: A coverage matrix is written (in this spec dir or `docs/`) listing
  every `.claude/rules/*.md` file and every `## Authoring conventions` bullet
  against the three runtimes, each cell classified binds-natively /
  absorbed-in-spirit / absent, with a one-line "should this bind here?"
  verdict.
- **R2**: Every rule the matrix marks "should bind but is absent/spirit-only"
  is ported into the appropriate non-Claude governance doc, preserving the
  procedure (not a paraphrase that drops steps or conditions) per the mirror
  discipline, and adapted only where a runtime mechanism forces it.
- **R3**: Rules correctly Claude-specific are recorded as intentional
  divergences with the forcing reason, so a later reader knows they were
  checked, not skipped (the DeepMind-note pattern from prose-review).
- **R4**: Ported doctrine gets `tests/mirror-procedure-manifest.txt` entries
  and passes `tests/test_mirror_procedure_coverage.sh`.
- **R5**: `codex/AGENTS.md`'s deferral is made explicit about what it does and
  does NOT inherit from Antigravity, so no rule is silently assumed-covered.

## Out of scope

- The prose/writing doctrine itself — owned by `specs/agentic-prose-tells`.
- Changing rule *content*; this is a porting/parity effort, not a rewrite of
  what the rules say for Claude.

## Acceptance criteria

- [ ] coverage matrix file exists and lists all 8 rules + the authoring
  conventions across 3 runtimes (reviewer confirms completeness)
- [ ] `bash tests/test_mirror_procedure_coverage.sh` exits 0 with the new
  ported-rule manifest entries present
- [ ] every non-ported rule has a stated forcing reason in the matrix

Note: needs `/critique` before `/breakdown` (no Breakdown-ready flag yet).
