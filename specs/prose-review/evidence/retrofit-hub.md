# Retrofit evidence: ~/hub orientation docs (task 07)

Target repo: `~/hub`. Work done in an isolated worktree
(`git worktree` on branch `task/07-retrofit-hub`), never the live checkout.
Scope: `README.md` (no `AGENTS.md` present; the other `docs/*.md` are
operational/working docs — TASKS.md, STATUS.md, deploy-todo.md,
qa-audit-2026-07.md, visual-test-log.md, portfolio-brokerage-credentials.md,
cujs.md — not human-orientation prose, so the retrofit targeted the one
orientation doc, README.md, per prose-review's scope). Vale config: hub has
no local `.vale.ini`; it resolves the global `~/.vale.ini` written by the
toolkit's `bin/install-vale` (StylesPath → `~/claude/vale/styles`, Google
package synced). Vale 3.15.1.

## CI precondition — PASS (commit permitted)

`~/hub/.github/workflows/ci.yml` is push-triggered (`on: push` to `main`) but
carries `paths-ignore: ["**.md", "specs/**", ".claude/**"]` on both `push`
and `pull_request`. A docs-only `README.md` change is therefore skipped by
CI — no metered runner burns on this commit. Precondition satisfied; commit
proceeded (branch `task/07-retrofit-hub`, commit `2fd9270`).

## Vale counts

| | errors | warnings | suggestions |
| --- | --- | --- | --- |
| BEFORE | 27 | 7 | 25 |
| AFTER  | 18 | 7 | 23 |

Errors resolved: all 6 `Google.EmDash` (spaced → unspaced em-dash) and the 1
`Google.Latin` (`e.g.` → `for example`). Every remaining error is
`Vale.Spelling` on domain jargon (see residual list). BEFORE errors = 20
Vale.Spelling + 6 Google.EmDash + 1 Google.Latin; AFTER errors = 18
Vale.Spelling only (the em-dash join also detached two jargon tokens Vale had
double-counted). No new Vale findings were introduced by the edits (re-linted
after writing).

## Rubric findings (nine-item AI-antipattern rubric)

BEFORE: README.md is already clean against the nine-item rubric — no
list/bullet overuse (its lists are genuinely enumerable command sets and
setup steps, item-1 carve-out applies), no hedging/AI-reminders, no
sycophancy, no purple prose, no stock acknowledgments, no self-celebratory
language, no blurry placeholder words. The doc is concrete throughout (paths,
commands, IDs). No item 1–9 violation was flagged, so none needed rewriting —
reported as "no antipatterns found" rather than inventing findings.

The actionable findings came from the Google-essentials sub-checks (which the
rubric pass owns, Vale can't) and the reader test:

- **Concrete-over-abstract / undefined reference:** the bare `(R18)` marker
  was unresolvable to a cold reader. FIXED — self-contained as "spec
  requirement R18" with the reason it exists.
- **Audience-first ordering / obvious first action:** the reader test found
  no "start here" signpost and no product overview (README was entirely
  operational). FIXED (light touch) — named the concrete domains (portfolio,
  tasks, food) in the opening line and added a one-line first-action pointer
  plus a map of the sections below.
- **Passive voice:** "The D1 adapters are not covered by CI" → active "CI
  doesn't exercise the D1 adapters."

AFTER: the nine-item rubric remains clean, and the three Google-essentials /
reader-test items above are resolved. The em-dash style is now internally
consistent (all prose em-dashes unspaced, matching Google style and the
toolkit's own adopted convention).

### Reader-test findings NOT fixed (out of a prose retrofit's scope)

Recorded for the author; each is a content/structure change beyond a
style-and-comprehension pass:

- The `4b.` numbered-step label breaks the 4→4b→5 sequence. Left as-is: it is
  a deliberate later insertion, and renumbering risks external references.
- No full "what hub does for the user day-to-day" product overview. Partially
  addressed by naming the domains; a full explanation section is an authoring
  task, not a retrofit.
- The setup/deploy/import/D1 sections are not explicitly sequenced as
  one-time vs. ongoing. Partially addressed by the new section-map sentence.

## Residual Vale findings — itemized as domain jargon / intentional (not fixed)

All 18 remaining **errors** are `Vale.Spelling` on legitimate technical terms
not in the toolkit's House vocab (hub has no vocab of its own; adding hub
jargon to the toolkit's shared vocab is out of this task's scope):

`pnpm`, `npm`, `corepack`, `monorepo`, `tsconfig`, `ESLint`, `Vitest`,
`OAuth`, `localStorage`, `devtools`, `devDependency`, `gitignored`,
`login_uri`, `config`, `toolchain`/`Toolchain`, `affordance`.

Residual **warnings/suggestions** left as intentional/domain style:

- `Google.Acronyms` (8): `GSI`, `JWKS`, `MCP`, `ENAM`, plus `AND`/`NOT`/`AM`
  false positives on emphasis words and a DB region code — all domain terms
  or intentional emphasis, not reader-unfamiliar acronyms worth expanding.
- `Google.WordList` (5): `CLI` (standard, matches the tools' own naming),
  `Cloud` (part of the proper name "Google Cloud console"), `disabled` (UI
  state term). Domain-appropriate; rewriting would reduce accuracy.
- `Google.Parens` (8) / `Google.Semicolons` (4): judicious-use *suggestions*
  on parentheticals and semicolons that aid scanning in dense setup prose;
  left deliberately.
- `Google.Passive` (2), `Google.Contractions` (1), `Google.Headings` (2):
  low-value stylistic suggestions on `is named`/`is needed`, one `are not`,
  and product-name headings (`hub`, `Post-deploy D1 ritual`) where the
  flagged token is a proper noun. Left as intentional.
