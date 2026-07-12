# Evidence — task 09: retrofit portfolio-tracker orientation docs

Target repo: `~/portfolio-tracker` (worked in a `git worktree`, never the live
checkout). Orientation docs: `README.md` (no `AGENTS.md` present) plus
`docs/*.md`. Tools: Vale 3.15.1 (Google package), the nine-item AI-antipattern
rubric, and a reader-test read of `README.md`.

## CI / auto-deploy precondition — FAIL (did NOT commit)

**Verdict: FAIL — no provable clean docs-only exclusion across all
push-triggered deploy paths, so no commit was made in the target repo.**

`~/portfolio-tracker` auto-pushes on commit (`.git/hooks/post-commit` runs
`git push`), and CLAUDE.md states hosting is "auto-deployed on push to main".
Two push-triggered deploy mechanisms exist:

1. **GitHub Actions `.github/workflows/deploy-api.yml`** (Cloudflare Workers) —
   `on: push` to `main` with a `paths:` allowlist of `src/**`, `frontend/**`,
   `tests/**`, `wrangler.toml`, `package.json`, `package-lock.json`,
   `tsconfig.json`. `README.md` and `docs/**` match none of these, so a
   docs-only push does NOT trigger this workflow. This path is cleanly
   excluded. ✅

2. **`cloudbuild.yaml`** (GCP Cloud Build → Cloud Run) — its own header reads
   "Triggered automatically on push to main branch or manually via gcloud
   builds submit". It has **no path/`includedFiles` filter** in the repo, so as
   documented, ANY push to main — including a docs-only one — would trigger a
   Cloud Run deploy. ❌

The Cloud Build trigger state could not be verified: `gcloud` is authed to
project `fooszone` (`gcloud builds triggers list` → "Listed 0 items"), but
`fooszone` is not portfolio-tracker's deploy project (its Cloud Run service is
`portfolio-tracker` under `$PROJECT_ID`, unknown from the repo). Because the
in-repo `cloudbuild.yaml` documents a push-to-main auto-deploy with no
docs-only exclusion and its active state cannot be disproven, the precondition
is NOT satisfiable. Per the task's mandatory precondition, fixes were applied
on disk in the worktree for evidence but **not committed**; the orchestrator /
a human must confirm the Cloud Build trigger is disabled or docs-filtered
before any commit is pushed.

## BEFORE counts (Vale, at worktree base cc0b6d8)

Vale `Google` package over the target docs:

- `README.md`: **7 errors, 10 warnings, 15 suggestions**
- `docs/*.md` (9 files, aggregate): **187 errors, 158 warnings, 493
  suggestions**

## Rubric findings (nine-item AI-antipattern rubric)

`README.md` — **no rubric antipatterns found.** The `## Architecture` bullet
list enumerates genuinely discrete stack components (backend / frontend /
database / data provider) and the env-var tables are reference material — both
fall under item-1's carve-out for structured/enumerable content, so neither is
"list/bullet overuse". No hedging (2), sycophancy (3), over-formatting (4),
purple prose (5), stock acknowledgments (6), repetition (7), vague language
(8), or self-celebration (9). Structure fits Diátaxis (how-to + reference for
an orientation README); audience-first ordering (what-it-is → quick start →
config → deploy) is already correct.

`docs/*.md` are reference/research documents (DATA_MODEL, data-sources,
allocation-reference, research summaries); their high Vale counts are dominated
by domain jargon and first-person-plural style, not narrative-fragmentation
antipatterns.

Reader test (`README.md`, cold read): "What is this?" answerable from line 3
("A full-stack portfolio tracking application built with Hono / React").
"First action?" obvious — the `## Quick start` fenced block. No blocking
stumbles; the doc reads cleanly.

## AFTER-on-disk counts (uncommitted, README.md, evidence only)

Six confident Google-style fixes applied to `README.md` in the worktree
(NOT committed): four sentence-case heading fixes (`Quick Start`→`Quick
start`, `Environment Variables`→`Environment variables`, `Secrets
Setup`→`Secrets setup`, `Database Setup`→`Database setup`) and two
`e.g.,`→`for example,` (Google.Latin).

- `README.md` after: **5 errors, 6 warnings, 15 suggestions** (from
  7/10/15) — 2 errors and 4 warnings cleared.

## Residual Vale findings on README.md — itemized as domain jargon / false positives

- **Vale.Spelling (5 errors)** — all product/tool names or dev shorthand:
  `Hono` (web framework), `Vite` (×2, build tool), `dev` (×2, standard
  abbreviation). Not misspellings; correct as written.
- **Google.Headings (6 warnings)** — proper-noun product titles Vale reads as
  non-sentence-case: H1 `Portfolio Tracker` (product name), `Cloudflare
  Workers (primary)`, `Frontend (build-time via Vite)`. Left as-is; forcing
  sentence case would corrupt product names.
- **Google.Parens (15 suggestions)** — "use parentheses judiciously"; the
  parentheticals clarify env-var examples and are appropriate. Judgment
  suggestions, left unchanged.

`docs/*.md` residuals (not itemized per-line here) are dominated by the same
classes: `Vale.Spelling` on finance/data jargon (backtest, countercyclical,
EODHD, Damodaran, ticker symbols) and `Google.We` first-person-plural in
internal research prose.
