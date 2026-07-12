# /prose-review: house technical-writing system (Diátaxis + Vale/Google + AI-antipattern rubric + reader test)

Status: open
Priority: P1

## Problem

The toolkit's technical writing reads badly and nothing checks it. Steven's
verdict (2026-07-11): "I just don't like how any of our tech writing comes
out" — /idea output excepted. The failure mode is structural: agent-written
docs optimize for coverage and correctness, producing dense inventories —
parenthetical cite-chains, changelog-speak, bullets where paragraphs belong
— because no skill reviews prose quality and no framework guides authoring.
`/code-review` and `/simplify` are code-only; `/critique` reviews a spec's
*content*, not its *style*.

Three public, battle-tested frameworks cover the layers we lack, and one
session-verified rubric covers the AI-specific failure modes:

**Structure — Diátaxis** (diataxis.fr): the tutorials / how-to / reference /
explanation quadrant framework, adopted by Django, Canonical, Cloudflare,
and Python. Its core claim matches our failure mode exactly: mixing
explanation into reference makes both worse.

**Sentences — Google Developer Documentation Style Guide**
(developers.google.com/style), enforced mechanically by **Vale** (vale.sh,
brew 3.15.1, verified available 2026-07-11; not currently installed — no
binary, no `~/.vale.ini`): a prose linter whose ready-made Google package
turns the style guide into a deterministic gate, matching this repo's
gates-beat-prose-rules doctrine.

**AI-writing antipatterns** — six vendors' own published guidance, verified
this session, converges on a checkable rubric:
- **Anthropic**: avoid list/bullet overuse ("DO NOT use ordered lists...
  unless... discrete items" — write "flowing prose using complete
  paragraphs"), avoid over-formatting ("avoids over-formatting with bold
  emphasis, headers, lists"), avoid self-celebratory language ("fact-based
  progress reports rather than self-celebratory updates"), sycophancy is
  a named, measured problem. (platform.claude.com/docs)
- **OpenAI** (Model Spec, model-spec.openai.com): avoid "purple prose,
  hyperbole, self-aggrandizing, and clichéd phrases"; avoid "excessive
  hedging... disclaimers... reminders that it's an AI"; avoid sycophancy
  ("not... flatter them or agree with them all the time"); prefer "plain
  paragraphs as the default format"; avoid "stock acknowledgments like
  'Got it'".
- **DeepSeek**: repetition and language-mixing are named, documented
  failure modes of raw model output (DeepSeek-R1 README/paper), addressed
  via explicit reward-shaping for readability.
- **Amazon**: narrative, non-bulleted writing is core culture ("we don't
  do PowerPoint... narratively structured six-page memos"); "verbosity
  hacking" (length exploding without quality) is a named failure mode in
  their own RFT best-practices post.
- **Mistral**: avoid vague/blurry language ("avoid blurry words like
  'things', 'stuff'... state exactly what you mean"); `frequency_penalty`/
  `presence_penalty` exist specifically to reduce repetition.
- **DeepMind**: no primary source names specific antipatterns (only
  Workspace style-*matching* features and generic prompt-clarity advice)
  — contributes no rubric items, noted honestly rather than padded.

**Comprehension — the reader test**, distilled from Anthropic's official
`doc-coauthoring` skill (github.com/anthropics/skills): a fresh-context
agent reads the doc cold and reports where it stumbles. Distilled, not
installed — it is a procedure, not code, and a plugin dependency would add
per-session token load for one stage (decision: Steven, 2026-07-11
interview).

System-wide application comes free: the skill ships in the `agentic`
plugin, which every session on this machine loads; the Vale config is
user-level (`~/.vale.ini`). No per-repo setup beyond the optional gate.

## Solution

One skill, `/prose-review`, in `.claude/skills/prose-review/`, with the
doctrine in its `reference.md` — no research dispatched at invocation; the
rubric and style bindings are stable, verified content (like `/simplify`'s
fixed checklist, unlike `/domain-knowledge`'s live research).

Two faces, one skill: **review mode** (the default and the only
model-invocable behavior) runs Vale first (deterministic pass), then the
nine-item rubric (judgment pass), then — for orientation docs — the reader
test, reporting findings ranked by severity in `/code-review`'s reporting
shape. **Authoring doctrine** (the rest of reference.md) is what an agent
loads *before* writing human-facing docs: the Diátaxis quadrant bound to
this machine's doc locations, and the Google-style essentials Vale can't
check (audience-first ordering, one-idea paragraphs).

Mechanics: `bin/install-vale` (idempotent) installs Vale via Homebrew,
writes `~/.vale.ini` pointing at this repo's `vale/` StylesPath — the
installer substitutes the ABSOLUTE resolved path (Vale resolves
StylesPath relative to the config file's directory, so a relative value
would break runs from other repos; the tracked template is a substitution
target, never copied verbatim) — and runs `vale sync` to pull the Google
package; the repo tracks the config template and the House vocabulary
(accept list for toolkit jargon: drain, baton, worktree, agentprof,
Diátaxis, ...) and gitignores the synced package payload. No per-repo
setup is REQUIRED; a repo MAY layer its own domain vocabulary (a local
`.vale.ini` extending the global styles) when its jargon would otherwise
drown the signal. The gate skill's check template gains an OPT-IN vale
stanza; machine-parsed prose (task files, specs/, SKILL.md bodies) is
exempt by default — Vale targets human-orientation docs (README.md,
AGENTS.md, docs/*.md).

A bulk retrofit wave (decision: Steven, 2026-07-11 interview) brings every
`std`-marked repo in `~/REPOS.md` up to the standard: one task per repo,
run the review, apply fixes to that repo's orientation docs, commit there.

## Requirements

- **R1 (rubric)**: `.claude/skills/prose-review/reference.md` documents
  exactly these nine rubric items, each with its source vendor(s) and the
  verified quote backing it (from Problem): (1) list/bullet overuse where
  prose reads better, (2) excessive hedging/disclaimers/AI-reminders,
  (3) sycophancy, (4) over-formatting (bold/headers beyond what aids
  scanning), (5) purple prose/clichéd filler, (6) stock acknowledgments,
  (7) repetitive phrasing/redundant information, (8) vague/blurry language
  lacking concrete specifics, (9) self-celebratory language. DeepMind is
  noted as contributing no rubric item, not silently omitted. **Rubric
  item 1 explicitly excludes structured technical documents** — a spec's
  `## Requirements`/`## Acceptance criteria` sections, API references, or
  any list whose items are genuinely discrete/enumerable are not "list
  overuse"; item 1 targets narrative/explanatory prose fragmented into
  bullets where flowing paragraphs would read better, per Anthropic's own
  carve-out ("unless... you're presenting truly discrete items").
- **R2 (review mode)**: `.claude/skills/prose-review/SKILL.md` takes a
  target (file path / diff / pasted text) and reports findings ranked by
  severity — file:line (or quoted excerpt), which rubric item or Vale rule,
  a one-line reason, and a suggested rewrite. The Vale pass runs FIRST when
  the target is a file and `vale` is installed (its findings merge into the
  report, attributed to their Vale rule); Vale absent → judgment passes
  still run, with one line noting the deterministic pass was skipped. Zero
  findings is a valid, explicitly reported outcome.
- **R3 (--fix)**: read-only by default. An optional `--fix` flag applies
  suggested rewrites directly; `--fix` requires a file-path target — given
  a diff or pasted text it errors rather than guessing where to write.
- **R4 (invocation gate)**: the read-only report mode is model-invocable —
  same risk class as `/critique`/`/simplify`. **`--fix` is human-typed
  only** (never inferred/added by the model from a vague request) — a
  SKILL.md behavioral instruction, since a flag cannot distinguish
  human-typed from model-typed arguments; auto-rewriting from a subjective
  rubric is real mutation risk (a misjudged item-1 carve-out could damage
  structured spec content).
- **R5 (authoring doctrine)**: reference.md carries a Diátaxis section
  binding the four quadrants to this machine's doc locations (README.md =
  explanation + how-to for humans; AGENTS.md = reference/orientation map;
  docs/ = explanation and reference; SKILL.md bodies = how-to/reference
  for agents — each with the "what does the reader need RIGHT NOW"
  question that picks the quadrant), plus the Google-style essentials Vale
  cannot check. SKILL.md's description carries authoring trigger phrases
  ("write the README", "draft docs", "improve this doc") in addition to
  review triggers, and instructs loading the doctrine BEFORE writing.
  Root CLAUDE.md gains one pointer line citing the skill for human-facing
  doc edits.
- **R6 (reader test)**: reference.md documents the distilled reader-test
  procedure — spawn one fresh-context agent (session tier, no prior
  context) that reads the target cold and answers: what is this, what
  would I do first, where did I stumble, what question is unanswered; its
  stumble report merges into the review findings. Review mode runs it for
  orientation docs (README/AGENTS.md) by default, skips it for diffs and
  pasted text.
- **R7 (Vale install)**: `bin/install-vale` idempotently: installs Vale
  via Homebrew when absent, writes `~/.vale.ini` from the repo's tracked
  template (StylesPath in this repo's `vale/`, `Packages = Google`,
  vocabulary `House`), and runs `vale sync`. The repo tracks
  `vale/.vale.ini.template` and
  `vale/styles/config/vocabularies/House/accept.txt` (toolkit jargon);
  synced package payload is gitignored. Re-running the installer is safe
  (idempotent, never clobbers a user-customized `~/.vale.ini` without a
  `--force` flag).
- **R8 (gate opt-in + self-application)**: the gate skill's check-script
  template gains an optional, commented-out vale stanza (lint
  orientation docs only — README.md, AGENTS.md, docs/*.md — never task
  files, specs/, or skill bodies). This repo opts in: after vocabulary
  tuning, `vale README.md AGENTS.md` exits 0 here.
- **R9 (retrofit wave)**: one task per `std`-marked repo in `~/REPOS.md`
  (enumerated at /breakdown time): run `/prose-review` over that repo's
  orientation docs, apply the fixes IN that repo (its own commit
  conventions), and record before/after finding counts — BOTH the Vale
  pass AND the nine-item rubric pass — in this spec's evidence/, with any
  residual Vale findings itemized (domain jargon a central vocabulary
  should not absorb is an acceptable, listed residue; "after" must show
  rubric findings resolved and Vale findings reduced to that listed
  residue — exit-0 is NOT the green condition). Target selection per
  repo: README.md, plus AGENTS.md when present, else `docs/*.md`; a repo
  with none of these SKIPS with a zero-target evidence entry — retrofit
  never authors new docs. Dispatch precondition per repo: confirm the
  repo's push-triggered workflows ignore docs-only commits
  (`paths-ignore: **.md` or equivalent) or use its documented docs-safe
  path BEFORE committing — auto-deploying repos (e.g. portfolio-tracker's
  push-on-commit) must not bill a CI run for a docs retrofit
  (~/.claude/CLAUDE.md CI cost discipline). Repos already clean produce a
  zero-findings evidence entry, not silence.
- **R10 (mirror + plugin)**: `antigravity/.agents/skills/prose-review/`
  is created in the same commit as the skill with content-equivalent
  doctrine (plain review/authoring skill, ports cleanly);
  `.claude-plugin/plugin.json` version bumped in the closing task's own
  commit. The codex leg needs no wrapper (not one of the four
  explicit-invocation stages; it reaches Codex via the antigravity
  symlink overlay automatically).

## Out of scope

- A global PostToolUse hook linting every `*.md` edit machine-wide
  (decided against, 2026-07-11 interview — noise on machine-parsed files;
  no user-level hook surface exists today and this spec does not create
  one).
- Installing Anthropic's `doc-coauthoring` plugin or adding the
  anthropics/skills marketplace (reader test is distilled instead).
- Auto-triggering `/prose-review` from within `/build`'s or `/idea`'s own
  flow — wiring it into other skills' completion steps is follow-up work.
- Re-researching the rubric at invocation time — vendor style doctrine is
  not a fast-moving fact set; revisiting it is a human call.
- Reviewing code comments or docstrings — code stays `/code-review`'s job.
- Task files, specs/, and other machine-parsed prose as Vale targets.
- Non-orientation documents in retrofit repos (only README/AGENTS.md/
  CLAUDE.md-adjacent orientation prose).

## Acceptance criteria

- [ ] `grep -qi 'DeepMind' .claude/skills/prose-review/reference.md` AND
  `grep -c 'developers.google.com/style\|diataxis.fr' .claude/skills/prose-review/reference.md`
  ≥ 2 AND MANUAL: all nine rubric items present with vendor quotes, item-1
  carve-out stated (R1) — phrases verified absent from the (nonexistent)
  target today: the skill directory does not exist yet, so no criterion
  here can pass vacuously
- [ ] MANUAL: review of a fixture doc seeded with known violations (one
  per rubric item) reports ≥7 of 9 with correct item attribution; a clean
  fixture reports "no antipatterns found" (R2)
- [ ] MANUAL: `--fix` on a pasted-text target errors; `--fix` never
  applied without the human having typed it (R3, R4)
- [ ] `grep -qi 'right now' .claude/skills/prose-review/reference.md` AND
  `grep -q 'prose-review' CLAUDE.md` (0 hits today — verified) AND
  MANUAL: Diátaxis quadrant table binds all four quadrants to house doc
  locations (R5)
- [ ] `grep -qi 'stumble' .claude/skills/prose-review/reference.md` AND
  MANUAL: reader-test procedure spawns a fresh-context agent and merges
  its report (R6)
- [ ] `bash bin/install-vale && vale --version` exits 0; run twice —
  second run is a no-op (idempotent); `test -f ~/.vale.ini` (R7)
- [ ] `vale README.md AGENTS.md` exits 0 in this repo after tuning (the
  toolkit's own jargon lives in the central House vocabulary, so exit-0
  IS reachable here, unlike retrofit repos); `grep -qi 'Vale prose lint'`
  hits in the gate skill's check template (anchor phrase absent today —
  bare 'vale' false-hits "equivalent") (R8)
- [ ] One evidence file per retrofitted repo under
  specs/prose-review/evidence/ recording before/after Vale AND rubric
  finding counts with residual Vale findings itemized; skipped/no-docs
  repos have zero-target entries; every retrofit commit preceded by the
  CI paths-ignore check recorded in its evidence entry (R9)
- [ ] `claude plugin validate .` passes; antigravity mirror dir exists
  with content-equivalent doctrine (content-coverage grep on 'Diátaxis'
  there); plugin version line modified in the closing task's own commit
  (`git show <closing-commit> -- .claude-plugin/plugin.json | grep -q '^+.*"version"'`)
  (R10)
- [ ] End-to-end: `/prose-review README.md` in this repo produces a
  ranked findings report (or explicit zero-findings) that includes the
  Vale pass, the rubric pass, and a reader-test stumble report

## Open questions

(none — enforcement mode, dependency handling, retrofit scope, and spec
shape all resolved in the 2026-07-11 interview; Vale config layout decided
in Solution: user-level `~/.vale.ini` pointing at this repo's tracked
`vale/` StylesPath)

## Parallelization

(/breakdown owns the task map; likely shape: skill+doctrine → vale
install/config → gate/self-application → retrofit fan-out (one task per
repo, cross-repo Touch per docs/memory/drain-dispatch-lessons.md) →
closing mirror/bump gate.)
