# Retrofit evidence: dnd-spellbook-manager orientation docs

Task: specs/prose-review/tasks/05-retrofit-dnd-spellbook-manager.md (R9).
Target repo: ~/dnd/dnd-spellbook-manager. Work done in an isolated `git
worktree` on branch `task/05-retrofit-dnd-spellbook-manager`; live checkout
untouched. Vale run via the toolkit's `~/.vale.ini` (Google package + House
vocab), same config `vale/.vale.ini.template` produces.

Scope (per task): README.md + the secondary orientation doc. No AGENTS.md
present, so `docs/*.md` = `docs/TASKS.md`.

## CI precondition check — PASS (safe to commit)

Checked before any commit in the target repo:

- No `.github/workflows/` directory (no GitHub Actions).
- No `.gitlab-ci.yml`, `.circleci/`, or `.travis.yml`.
- `git remote -v` is empty — **no remote configured at all**, so no push
  can trigger anything (confirmed live: the post-commit hook printed
  "No remote repository configured. Skipping push").
- `cloudbuild.yaml` exists but is invoked manually via `gcloud builds
  submit` (deploy-cloud-run.sh / deploy-local-build.sh), not a push trigger.

Conclusion: no push-triggered metered CI exists. The precondition (push
workflows must ignore docs-only commits, or use a docs-safe path) is
satisfied vacuously. Proceeded to commit.

Note: the repo's local `pre-commit` hook runs a staged-file `tsc` typecheck,
which cannot run in a `git worktree` (node_modules is not present in a
worktree). Since this is a markdown-only change, the commit used
`--no-verify`, the repo's own sanctioned escape hatch, documented in the
commit message. This is a local hook, not push-triggered CI.

## Vale counts — BEFORE → AFTER

| File | BEFORE (e/w/s) | AFTER (e/w/s) |
| --- | --- | --- |
| README.md | 21 / 9 / 19 | 18 / 4 / 18 |
| docs/TASKS.md | 6 / 0 / 4 | 3 / 0 / 3 |
| **Combined** | **27 / 9 / 23** | **21 / 4 / 21** |

(e = errors, w = warnings, s = suggestions; `vale README.md docs/TASKS.md`.)

Vale findings actually fixed: 6 errors + 5 warnings + 2 suggestions cleared —
the fixable/mechanical subset (sentence-case headings, `50ms`→`50 ms`
nonbreaking space, exclamation points, passive voice, spaced→unspaced
em-dashes). The residual delta is entirely domain jargon + stylistic
suggestions (itemized below), deliberately not "fixed".

## Rubric findings — BEFORE (nine-item AI-antipattern rubric)

README.md:
- Item 5 (purple prose): "Works **beautifully** on desktop, tablet, and
  mobile" — hyperbolic adverb.
- Item 9 (self-celebratory) + exclamation: heading "Phase 1: MVP ✅
  **Complete!**" narrates progress as celebration.
- Item 5 (exclamation): "suggestions and feedback are welcome**!**".
- Item 7 (repetition): "**Comprehensive** Testing" / "**Comprehensive**
  documentation" / "**comprehensive** test coverage" — the word three times.
- Accuracy/staleness (surfaced by the reader test + git log): "Automated
  code review via Claude Code integration" — the AI review step was removed
  from the hooks in commits `92b9822` / `ccaafca`, so the claim was stale.

docs/TASKS.md:
- Item 1 carve-out honored: it is a genuinely enumerable task checklist, not
  narrative-fragmented prose — NOT flagged as list overuse.
- Passive voice (Google essentials): "the storage.service versions **are
  referenced** only by their own tests".

## Rubric findings — AFTER (all resolved)

- "beautifully" removed → "Works on desktop, tablet, and mobile".
- Heading → "Phase 1: MVP (complete)" (no exclamation, no celebration emoji).
- "welcome!" → "welcome.".
- "comprehensive" reduced from 3 occurrences to 1 (the bolded feature
  label); the two prose occurrences reworded.
- Stale automated-code-review bullet deleted.
- SRD spelled out on first use: "from the System Reference Document (SRD)".
- Passive → active: "only their own tests reference the storage.service
  versions".

Reader-test residual (content gap, not a prose antipattern, not invented
away): the README never states whether the app is deployed/live anywhere.
Left for the maintainer — filling it would require inventing a fact.

## Residual Vale findings — itemized, justified as domain jargon / style

Not fixed because each is a legitimate proper noun, tech term, D&D-domain
word, or a purely stylistic suggestion; "fixing" them would require adding
entries to the toolkit's House vocab (out of scope for this repo's docs) or
would degrade meaning.

- **Vale.Spelling (21):** `Spellbook`, `spellbooks` (the product's core
  domain noun), `Vite`, `npm`, `Workbox`, `dev`, `Utils`, `formatters`
  (build-tooling / code identifiers), `unvalidated`, `hardcodes`, `foosball`
  (a proper noun naming another GCP project) — all correct as written.
- **Google.Acronyms (10):** `SRD` (now expanded on first use), `PWA`
  (expanded as "Progressive Web App" in the intro line), `MVP`, `CRUD`,
  `GCP`, `MIT`, `OGL` — standard/domain acronyms; expanding every reuse
  would add noise, not clarity. Suggestion-level only.
- **Google.Parens (11):** "use parentheses judiciously" — the parentheticals
  are concise clarifications (version notes, aside references); reasonable as
  written. Suggestion-level only.
- **Google.WordList (2):** 'tablet'→'device' (tablet is a deliberately
  specific form factor in "desktop, tablet, and mobile"); 'Cloud'→'GCP'
  (refers to the roadmap "Cloud sync" feature, generic cloud, not GCP).
- **Google.Headings (2):** "Phase 1: MVP (complete)" flags because of the
  `MVP` acronym; the heading is otherwise sentence-case. Acronym-driven
  false positive, left as-is.

## Commit

Target repo worktree branch `task/05-retrofit-dnd-spellbook-manager`,
commit `02a4cc9` "docs: prose-review retrofit of orientation docs"
(2 files, +17/-18). Not pushed (orchestrator merges/pushes at collect time).
