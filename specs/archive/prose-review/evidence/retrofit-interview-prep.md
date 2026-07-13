# Retrofit evidence: interview-prep orientation docs

Task: specs/prose-review/tasks/08-retrofit-interview-prep.md (requirement R9).
Target repo: ~/interview-prep. Work done in a `git worktree` on branch
`task/08-retrofit-interview-prep`; live checkout untouched.
Target docs: `README.md` + `AGENTS.md` (AGENTS.md present, so the "else
docs/*.md" fallback did not apply).

## CI precondition check (before any commit) — SATISFIED

The retrofit commit was gated on: does the repo have push-triggered CI, and
if so does it skip docs-only pushes? Result: **no push-triggered CI exists**,
so committing docs is safe.

- `find . -name '*.yml' -o -name '*.yaml'` (excluding `.git`) → no matches.
- `.github/` directory does not exist (no `.github/workflows/`).

With zero push-triggered workflows there is nothing to gate a `**.md` push, so
the precondition passes vacuously and the retrofit proceeded to commit.

## Vale counts

`vale README.md AGENTS.md`, run in the worktree.

| State  | Errors | Warnings | Suggestions |
| ------ | ------ | -------- | ----------- |
| BEFORE | 29     | 4        | 52          |
| AFTER  | 26     | 4        | 49          |

Delta: -3 errors, -3 suggestions. Fixes applied (all clean, deterministic
Google-style mechanics; no judgment risk):

- **Google.AMPM** (2 errors): `7:00am` → `7:00 AM` in README (jobhunt
  schedule) and AGENTS (State). 
- **Google.Quotes** (1 error): AGENTS `"what do I do today".` → period moved
  inside the quotation marks.
- **Google.Contractions** (2 suggestions): AGENTS `has not` → `hasn't`,
  `are not` → `aren't`.
- **Google.Passive** (1 suggestion): AGENTS `has not yet been observed
  firing` → `hasn't fired yet` (rewrite dropped the passive alongside the
  contraction).

## Rubric pass (nine-item AI-antipattern rubric)

Both docs read as competent, human-written orientation docs. Applying the
nine items:

- **Item 1 (list/bullet overuse):** No violation. README's three-track table
  and the plans/layout bullet lists, and AGENTS' Map list, are genuinely
  enumerable reference content — item-1 carve-out applies.
- **Item 2 (hedging / AI reminders):** None.
- **Item 3 (sycophancy):** None.
- **Item 4 (over-formatting):** Mild. Bold is used to flag status/date markers
  ("**Parked 2026-07-06**", "**the operative daily protocol**"); it guides
  scanning rather than fragmenting reading. Not flagged as a fix — acceptable
  for a status-carrying orientation doc.
- **Item 5 (purple prose / clichés):** Low. "North star:" (AGENTS) and "the
  graph completes itself" (README) are mild; both are clear and concrete in
  context. Not worth churn; left as-is.
- **Item 6 (stock acknowledgments):** None.
- **Item 7 (repetitive / redundant):** None within either doc. README and
  AGENTS overlap by design (human README vs. agent orientation map) —
  different audiences, not redundancy.
- **Item 8 (vague / blurry language):** None — the docs are concrete (paths,
  dates, commands, comp figures).
- **Item 9 (self-celebratory language):** None; progress is reported as fact
  ("parked", "has run manually", "not yet imported").

Net: no nine-item antipattern required a fix. The AFTER state carries zero
unresolved rubric findings.

## Reader-test pass (cold read)

Applied inline rather than via a separate fresh-context agent (budget ceiling
of 4 turns; both docs are short — 58 and 42 lines — and self-contained).
Observations:

- **What is this?** Clear from the first line of each: a one-repo interview
  campaign vault targeting a specific Optiver role.
- **First action?** Obvious — both point the reader at `Daily Flow.md` as the
  operative daily protocol.
- **Stumbles:** The Obsidian-domain acronym **MOC** (Map of Content) appears
  undefined. For the actual audience (the repo owner, who authored the vault)
  this is known jargon, so it was left rather than glossed — see residuals.
- **Unanswered question:** None blocking.

## Residual Vale findings (not fixed — itemized + justified)

Remaining errors (26) and the bulk of suggestions are correct-as-written
domain jargon, proper nouns, or a consistent house style. None is a genuine
prose defect.

**Vale.Spelling (19 errors) — proper nouns / domain jargon, all correct:**

- Proper nouns: `Optiver` (target company, ×5 across both docs), `Exercism`,
  `Protohackers` (drill/training platforms).
- Domain / technical terms: `Kata`/`kata` (fluency-drill term), `launchd`
  (macOS service manager, ×2), `wikilinks`, `MOCs`/`MOC` (Obsidian "Map of
  Content", ×2), `watchlist`, `intel`, `Signedness`, `Numerics`, `PDFs`.

These are spelled correctly for their domain; "fixing" them would corrupt
proper nouns or technical vocabulary. A repo-local Vale `accept.txt`
vocabulary could silence them, but that is out of this task's scope (it edits
Vale config, not the target docs).

**Google.EmDash (7 errors) — house style, deliberately not changed:**

- README 3:32, 13:56, 24:98, 31:318, 56:469; AGENTS 1:17, 15:103.

The repo uses spaced em-dashes (` — `) consistently across the entire vault
(every doc), so these two files are internally consistent with the rest.
Converting only the two orientation docs to unspaced em-dashes would make
them inconsistent with the ~30 sibling notes, and one flagged instance
(README 56:469, "LeetCode 75 — Index") is a reference to an actual note
**filename** (`LeetCode 75 — Index.md`) — unspacing it there would break the
reference. This is a repo-wide style decision the owner should make globally
(and one flagged em-dash is a proper-noun filename), not a per-doc prose
defect, so it is left unchanged.

**Google.Acronyms (suggestions) — domain acronyms for a domain audience:**

- `HFT`, `MOC`, `SWE`, `TCO`, `HEAD`. All are standard vocabulary for the
  audience (the repo owner / interview-prep readers). Left unglossed.

**Google.Parens / Google.Semicolons / Google.Headings / Google.Colons /
Google.FirstPerson (suggestions/warnings) — style preferences, kept:**

- Heavy but well-formed parenthetical asides and semicolons suit a dense
  orientation doc; rewriting them all would add churn without improving
  clarity.
- `Google.FirstPerson` (AGENTS 11:175) fires inside the quoted reader
  question `"what do I do today"` — a legitimate quotation, not authorial
  first person.
- `Google.Headings`/`Google.Colons` fire on the project display name
  ("Interview Prep") and the job title after a colon ("Senior Software
  Engineer") — title/proper-noun casing, kept intentionally.

## Decisions

- Fixed only clean, deterministic Google-style mechanics (AM/PM, quotes,
  contractions/passive). Left house-style em-dashes and domain jargon as
  residuals rather than imposing vault-wide restyling from two files —
  reversible; the owner can restyle globally if desired.
- Ran the reader test inline instead of via a separate fresh-context agent
  (short docs + 4-turn budget ceiling), and documented the one stumble (MOC).
