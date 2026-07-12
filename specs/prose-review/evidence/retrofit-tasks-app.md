# Retrofit evidence: ~/tasks-app orientation docs (task 10)

Ran /prose-review's documented procedure (nine-item AI-antipattern rubric +
Vale/Google-style pass + cold-read reader test) over ~/tasks-app's orientation
docs. Target docs: `README.md` and `AGENTS.md` (AGENTS.md present, so per the
skill's scope `docs/*.md` was not in scope). Work done in a `git worktree` of
~/tasks-app on branch `task/10-retrofit-tasks-app`, never the live checkout.

## CI precondition check (before any commit)

PASS — safe to commit. `~/tasks-app/.github/workflows/ci.yml` is push- and
pull_request-triggered on `main`, and both triggers carry a docs-only skip:

```yaml
on:
  push:
    branches: [main]
    paths-ignore: ["**.md", "docs/**", "specs/**", "history/**", ".claude/**"]
  pull_request:
    branches: [main]
    paths-ignore: ["**.md", "docs/**", "specs/**", "history/**", ".claude/**"]
```

A README.md/AGENTS.md-only push therefore triggers no billed CI run. Commit
proceeded. (It also already has `concurrency.cancel-in-progress: true` and a
`timeout-minutes: 15`.)

## Vale counts (BEFORE → AFTER)

Vale 3.15.1, Google package. `vale README.md AGENTS.md`.

| File | BEFORE (err/warn/sugg) | AFTER (err/warn/sugg) |
| --- | --- | --- |
| README.md | 11 / 11 / 12 | 10 / 6 / 9 |
| AGENTS.md | 5 / 11 / 15 | 1 / 0 / 5 |
| Combined | 16 / 22 / 27 | 11 / 6 / 14 |

All AFTER findings are residual domain jargon / false positives (itemized
below); no genuine prose defect remains. Every warning that was a real style
issue (heading title-case, `application`→`app`, `will`, `e.g.`→`for example`,
first-person `we`, `widely-used` hyphen, `functionality`, passive voice, a
spaced em-dash) was fixed. README's warning count dropped 11→6 and AGENTS's
11→0.

## Rubric findings (BEFORE → AFTER)

BEFORE:
- **Item 7 (repetitive phrasing / redundant information)** — AGENTS.md
  "Change Process": 11 bullets, most restating the same commit guidance
  ("Commit frequently", "Commit history: keep the history clean", "Check for
  pending uncommitted changes", "Commit on Task Completion" all overlap). The
  reflect bullet (line 34) restated its own bold label verbatim and carried a
  typo ("comitting" ×2).
- **Stale-reference stumble** — AGENTS.md instructed agents to file tech debt
  via `bd create` / "record it in the bead" (lines 16, 40), but Beads/`bd` was
  decommissioned in this repo (commits `88f26ba`, `8e3075e`); `docs/TASKS.md`
  is the current tracker.
- **Item 8/9 (mild)** — README line 3 "A simple web application" (vague
  self-assessment "simple"); README testing section narrated process in
  passive self-referential voice ("This project was developed using TDD.
  Tests are written for…").
- Item 1 (list overuse): considered and NOT flagged — README Features and the
  numbered Setup steps are genuinely enumerable (item-1 carve-out); AGENTS
  guideline bullets are enumerable, the finding there was repetition (item 7),
  not list-vs-prose.
- Items 2, 3, 4, 5, 6: no violations found.

AFTER (all resolved):
- Item 7: "Change Process" condensed 11→6 non-redundant bullets; typo fixed;
  self-restating label removed.
- Stale refs: both `bd`/"bead" references replaced with `docs/TASKS.md`.
- Item 8/9: "simple" dropped; testing section rewritten active ("This project
  follows TDD. Tests cover: … Each test sits alongside its source file").

## Reader-test (cold-read of README, one fresh-context agent)

- What is this? — clearly answerable: a React/Vite web app to view all Google
  Tasks in one page via Google OAuth.
- First action? — obvious (`npm install`; the `git clone <your-repo-url>` line
  is a template placeholder).
- Stumbles / unanswered (recorded, NOT auto-fixed — content-completeness gaps
  beyond a prose pass, and resolving them requires the real GCP flow, which a
  prose retrofit should not fabricate):
  1. README line 64 introduces `VITE_GOOGLE_API_KEY`, but the section-3 Google
     Cloud Console walkthrough only obtains a Client ID, never an API key — a
     genuine inconsistency worth a follow-up (candidate for `docs/TASKS.md`).
  2. `.env.example` shape not shown beyond the two vars.
  3. Production build is documented (build/preview) but deploy/hosting and
     production OAuth origins/redirect URIs are not.

## Residual Vale findings — itemized as domain jargon / false positives (not fixed)

README.md (10 err / 6 warn / 9 sugg):
- `Vale.Spelling`: OAuth (×3), Vite (×2), Vitest, APIs (×2), URIs, `dev` —
  correct product names, protocol names, and CLI terms Vale's dictionary lacks.
- `Google.Headings` "Google Tasks Viewer" and "3. Configure Google API" —
  contain the product proper nouns "Google Tasks" / "Google API"; sentence-
  casing them would corrupt the name.
- `Google.WordList` "Cloud" (×2) — part of the product names "Google Cloud
  Platform" / "Google Cloud Console".
- `Google.WordList` "OAuth 2.0" flagged on the "OAuth 2" substring — text
  already reads "OAuth 2.0"; false positive.
- `Google.WordList` `application` (line 46) — the literal GCP UI button label
  "Web application"; must match the console verbatim.
- `Google.Acronyms` MIT — standard license identifier.
- `Google.Parens` suggestions — parentheticals like "(v16 or higher)", "(for
  development)" are judicious.

AGENTS.md (1 err / 0 warn / 5 sugg):
- `Vale.Spelling` JSDoc — proper noun.
- `Google.Acronyms` TDD — defined inline on the same line "TDD (Test-Driven
  Development)".
- `Google.Parens` (×4) — judicious parentheticals (definitions / examples).

## Branches

- Toolkit bookkeeping: branch `task/10-retrofit-tasks-app` (this evidence file
  + task close-out).
- Doc work: `git worktree` of ~/tasks-app, branch `task/10-retrofit-tasks-app`,
  commit `eac87de` (README.md + AGENTS.md; docs-only). Neither repo pushed —
  the orchestrator merges and pushes both at collect time.
