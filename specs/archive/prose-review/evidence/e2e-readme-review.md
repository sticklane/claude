# End-to-end /prose-review — README.md

Spec: prose-review, end-to-end criterion (task 03). Target: `README.md`.
Run: 2026-07-12. Mode: review (read-only; no `--fix`).

This is the spec's end-to-end exercise: all three prose-review passes run
over README.md — the deterministic Vale pass, the nine-item rubric pass, and
the cold-read reader test — merged into one ranked report. Outcome: **all
three passes green** (zero blocking findings); low-severity observations
recorded below.

## Pass 1 — Vale (deterministic): PASS

Command (resolved against THIS repo's own Vale styles — see note):

```
vale README.md AGENTS.md   # → exit 0
vale README.md             # → 0 errors, 3 warnings, 20 suggestions
```

- **0 error-level alerts** over README.md and AGENTS.md → exit 0. This is the
  gate: Google.EmDash stays active (not disabled or downgraded); the repo's
  spaced em-dashes were rewritten to Google's unspaced `word—word` house
  style, and the repo's jargon was added to the central House vocabulary
  (`vale/styles/config/vocabularies/House/accept.txt`) rather than suppressing
  any rule.
- Non-blocking, left as-is (suggestions/warnings do not fail the gate):
  Google.Parens (parenthetical asides), Google.Semicolons, Google.Passive
  (2), Google.Will, Google.WordList ("CLI" → "command-line tool"; "above" →
  "preceding"), Google.Acronyms ("ALL"), Google.Contractions. These are
  stylistic suggestions the house voice deliberately keeps; none is an error.

Note — how "this repo" was resolved: the machine-global `~/.vale.ini`
(written by `bin/install-vale`) pins `StylesPath` to the canonical checkout,
so a bare `vale` invoked inside an isolated worktree reads that checkout's
vocabulary, not the worktree's. The pass above was therefore verified with
Vale pointed at THIS tree's `vale/styles` (the repo's own
`.vale.ini.template` resolved to this tree). Once merged, the canonical
checkout carries the updated `accept.txt`, so the bare
`vale README.md AGENTS.md` exits 0 there with no override.

## Pass 2 — Rubric (nine-item AI-antipattern): PASS

No blocking antipattern found. Item-by-item:

- **1 List/bullet overuse** — carve-out applies. The feature table, install
  options, and the "Why this shape" practice bullets are genuinely discrete,
  enumerable items, not narrative fragmented into bullets. Not flagged.
- **2 Hedging / disclaimers / AI-reminders** — none.
- **3 Sycophancy** — none.
- **4 Over-formatting** — bold lead-ins in "Why this shape" and "Token-cost
  design" are dense but each guides scanning to a discrete practice; below the
  flag bar (low-severity note only).
- **5 Purple prose / clichés** — none; phrasing ("deliberately cheap on
  tokens", "slot machine") is concrete/idiomatic, not hyperbolic.
- **6 Stock acknowledgments** — none.
- **7 Repetitive phrasing** — the "fresh, cheap session" theme recurs, but
  each instance carries new information (a different stage/mechanism). Below
  the flag bar.
- **8 Vague / blurry language** — none; the doc favors concrete commands and
  paths.
- **9 Self-celebratory language** — none; framing is factual ("modeled on how
  Anthropic's own teams use Claude Code").

Low-severity observations (not blocking, not fixed in this task — this task's
scope was the em-dash/vocab self-application, and review mode is read-only):
the "Why this shape" bullet list (lines ~64–95) could read as flowing prose;
bold density in that section and "Token-cost design" is near the
over-formatting line.

## Pass 3 — Reader test (cold-read, fresh-context agent): PASS with stumbles

One fresh-context agent read README.md cold, once, and answered:

- **What is this?** — Correctly identified: Claude Code skills and subagents
  that turn a raw idea into agent-executed work through a spec-driven,
  verification-gated pipeline (idea → spec → design → breakdown →
  build/drain/autopilot → distill), modeled on Anthropic's own practice. The
  document's purpose is clear on a cold read.
- **What would I do first?** — Not surfaced up front. The actionable start
  (`/onboard`, then `/idea`) lives in the "Verify" note at the end of Install
  (~lines 165–168), after four install options, rather than as a "start here"
  line near the top.

Stumbles (ranked by how badly each blocks a first reader):

| Location | Kind | Reason | Suggested rewrite |
| --- | --- | --- | --- |
| Diagram line ~15 vs its parenthetical | reader-test stumble | Diagram shows `/design` inline in the chain while the adjacent text says it's conditional ("only if an approach or stack choice is open") — reads as contradictory | Mark `/design` visually optional in the diagram (e.g. dashed/parenthesized) to match the text |
| Pipeline diagram (lines ~10–31) | reader-test stumble | Dense ASCII with nested branches; matching `/build`/`/drain`/`/autopilot` to their arrows needs a slow re-read | Add a one-line legend, or a "start here" pointer above the diagram |
| Install ordering (top of §Install) | reader-test stumble | No "start here" first action; the concrete first command is buried after four options | Lead Install (or the intro) with a single "Fastest path: install the plugin, then `/onboard`, then `/idea`" line |
| Line ~124 rules-don't-ship aside | reader-test stumble | Stated as an aside; unclear whether skipping it breaks things | State the consequence explicitly (what degrades without the rules) |
| Lines ~159–163 project-scoped-rules note | reader-test stumble | Appears only under Option C but seems to apply to A/B too | Hoist the note so its scope is unambiguous |
| Lines ~184–188 codex leg; `allow_implicit_invocation: false` | reader-test stumble | Second port chain introduced late and tersely; the flag is unexplained jargon | One clause on what the flag does, or link to the codex README |

- **Unanswered question the reader noticed:** the doc stops at "point it at a
  real repo" without showing what a first `/idea` invocation or its output
  looks like — a newcomer doesn't know what first-run success looks like.

These reader-test stumbles are readability findings about README's structure,
not defects in this task's em-dash/vocabulary change. They are recorded here
as the e2e deliverable; acting on them is a separate follow-up (README
restructuring), out of task 03's Touch.

## Verdict

Vale pass: green (0 errors, exit 0). Rubric pass: green (no blocking
antipattern; two low-severity notes). Reader test: ran, comprehension intact,
six ranked stumbles + one open question captured. The end-to-end
/prose-review pipeline is exercised and produces a ranked report as specified.
