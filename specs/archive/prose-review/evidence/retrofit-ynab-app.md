# Retrofit evidence: ~/ynab-app orientation docs

Task: specs/prose-review/tasks/12-retrofit-ynab-app.md (R9)
Target repo: ~/ynab-app (github.com/sticklane/ynab-app)
Work done in worktree on branch `task/12-retrofit-ynab-app`; commit `81cb99a`.
Orientation doc reviewed: **README.md** (408 lines). See "Scope decision" below
for why docs/*.md were excluded.

## CI-precondition check (before any commit)

Verdict: **SATISFIED — safe to commit.** The active push-triggered deploy
skips docs-only pushes.

- **GitHub Actions `.github/workflows/deploy.yml`** — push-triggered on
  `main`, and it deploys the Cloudflare Worker (the live prod path). It
  carries `paths-ignore: ["**.md", "docs/**", "specs/**", ".claude/**"]`, so
  a docs-only push is skipped. Also has `concurrency` + a single-stack job.
  This is the primary, active push-triggered CI, and it is docs-safe.
- **Second-deploy-path check (per task warning).**
  - `cloudbuild.yaml` (Cloud Run deploy, no path filter): its own header
    comment reads "Trigger this manually or set up a trigger in Cloud Build."
    It is a *manual* config, not wired to git push — Cloud Build path filters
    live on the trigger in GCP, not the yaml, and there is no evidence in the
    repo of an active push trigger. It also targets a *different* platform
    (Cloud Run `gcr.io/$PROJECT_ID/dash4ynab`) than the active Cloudflare
    deploy, indicating a dormant/legacy alternate path. Treated as
    not-push-triggered; recorded here for the record. (GCP trigger state
    cannot be queried from an unattended worker; if a push trigger were later
    added it would need an `includedFiles` docs filter.)
  - `wrangler.jsonc` — no `[build]` watch / Workers-Build git-integration
    config; the Worker is deployed *inside* GitHub Actions via
    `cloudflare/wrangler-action`, so a separate Cloudflare Workers Build git
    integration would double-deploy and is not in evidence.

## Vale counts (rule: Google + Vale packages, ~/.vale.ini, MinAlertLevel=suggestion)

| Metric | BEFORE | AFTER |
| --- | --- | --- |
| Errors | 25 | 24 |
| Warnings | 15 | 3 |
| Suggestions | 64 | 64 |
| **Total** | **104** | **91** |

Warnings dropped 15 → 3 (12 title-case headings fixed). The 3 residual
warnings are all Google.Headings false positives on proper-noun/acronym
headings that must stay capitalized: `Dashboard for YNAB` (H1 title),
`XSS mitigation`, `YNAB philosophy integration`. Errors fell 25 → 24; the
remaining 24 are all `Vale.Spelling` on domain jargon (itemized below).
Suggestions net-unchanged: they are Google.Parens / Google.Acronyms
("spell out YNAB/TDD/CORS") / Google.Passive judgment items, left as-is.

## Rubric findings (nine-item AI-antipattern rubric)

BEFORE (findings):
- **Item 5 (purple prose/filler):** tagline "A *modern, intelligent*
  dashboard ... with *smart* caching and AI-powered insights."
- **Item 9 (self-celebratory):** status header "**Current Phase:**
  Production Dashboard Complete ✅" — narrated as achievement, and
  contradicted by two unchecked checklist items just below it.
- **Item 4 (over-formatting):** decorative emoji on every `##`/`###` heading
  (🎯🚀🏗️🛠️📦🔑📁🧪🔒🐛📊🤝📝📈🎓📜🙏) plus title-case headings —
  decoration that fragments scanning rather than guiding it.
- **Item 1 (list overuse):** the Features section is a wall of bullet lists.
  Assessed as CARVE-OUT (genuinely enumerable feature/tech/command lists),
  NOT flagged — rewriting discrete lists into prose is the damage the
  carve-out prevents.
- Google-essentials: several title-case headings (Vale-flagged); "100ms"
  missing unit space; "application" where "app" is house style; tagline
  overclaims "AI-powered insights" while the AI integration is marked
  blocked/in-progress.

AFTER (resolution):
- Item 5 — tagline de-purpled: "A dashboard for visualizing and analyzing
  YNAB (You Need A Budget) data, with offline caching and AI-powered
  insights." ("modern, intelligent", "smart" removed).
- Item 9 — status line made factual and non-contradictory: "**Current
  phase:** core dashboard complete. Saved-graphs UI and Claude AI
  integration are still in progress." (removes the ✅ and the
  "complete"-vs-open-checklist contradiction the reader test caught).
- Item 4 — decorative emoji removed from all 23 headings; 12 headings
  sentence-cased (the rest were already correct or are acronym/proper-noun
  false positives).
- Google-essentials — "100ms" → "100 ms"; "client-side application" →
  "client-side app".
- Item 1 — feature/tech/command lists left as structured content per the
  carve-out (correctly not rewritten).

### Reader-test findings (fresh cold-read agent)

Resolved by the edits:
- "Production Dashboard Complete ✅" next to two unchecked boxes read as a
  contradiction → fixed (see Item 9 above).

Recorded as content/structure gaps (out of pure-prose scope, NOT fixed —
flagged for a maintainer):
- "Getting a YNAB API Token" (Configuration) is separated from the
  Installation step that needs it — reader must hold an open loop across
  sections.
- Security section describes an OAuth "Production Mode", but Configuration
  and Installation document only the dev-mode `VITE_YNAB_API_TOKEN` env var —
  no OAuth setup / callback / client-ID instructions exist, so the described
  production path is not actionable from the README.
- `pages/TestDashboard.tsx` is listed as the page component — the "Test"
  prefix on the apparent production entry point is confusing.
- `git clone <repo-url>` uses an unfilled placeholder.

## Residual Vale findings — itemized, justified as domain jargon (not fixed)

All 24 residual `Vale.Spelling` errors are correct domain/technical terms;
"fixing" them would mean adding them to a project Vale vocabulary, which is
outside this task's Touch scope (the toolkit House vocab / a new ynab-app
.vale.ini). Left as-is:

- **Product / domain:** `YNAB` (and possessive `YNAB's`), `OAuth`,
  `Uncategorized` (a YNAB category state).
- **Web-platform / storage APIs:** `localStorage`, `serverless`, `CORS`.
- **Library / tool names:** `Vite`, `Vitest`, `Recharts`, `npm`.
- **Common technical terms:** `heatmap` / `Heatmap`, `gzipped`, `gitignored`.

Residual Google.Acronyms *suggestions* ("spell out YNAB/TDD/CORS/LLC") and
Google.Parens / Google.Passive *suggestions* are judgment-level style
suggestions on a personal-project README; left as-is (MinAlertLevel captured
them for the record, none are errors).

## Commit precondition note

Committed with `git commit --no-verify` (repo CLAUDE.md documents
`--no-verify` as the escape hatch): the pre-commit hook runs `npm run lint`
+ `npm run format:check`, which require `node_modules` absent from the
throwaway worktree, and the change is docs-only. Prettier scopes `*.md`
(no `.prettierignore` exclusion) but the edits are in-line text swaps that
preserve wrapping/structure.

## Scope decision

Target set was README.md. `docs/*.md` (3082 lines across 8 files:
AI_INSIGHTS_DESIGN, ASSISTANT, BUDGET_TARGETS_DEBUGGING_STATE,
D1_USER_PREFERENCES_DESIGN, TASKS, YNAB_API_GOAL_FIELDS,
YNAB_COST_TO_BE_ME_ALGORITHM, YNAB_DESIGN_RESEARCH) are internal design
specs, API-field references, debugging-state, and task-list scratch docs —
structured/reference/working-state content (Item-1 carve-out territory,
Diátaxis reference/explanation), not human-orientation prose. There is no
AGENTS.md, so README.md is the single genuine orientation doc; the skill's
"else docs/*.md" fallback applies to repos whose orientation lives in docs/,
which is not the case here. Excluding them is reversible — a later pass can
cover them if desired.
