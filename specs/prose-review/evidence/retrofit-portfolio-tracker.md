# Evidence — task 09: retrofit portfolio-tracker orientation docs

Target repo: `~/portfolio-tracker` (worked in a `git worktree` under the
session scratchpad, never the live checkout). Orientation docs: `README.md`
(no `AGENTS.md` present) plus `docs/*.md`. Tools: Vale 3.15.1 (Google
package), the nine-item AI-antipattern rubric, and a cold reader-test read of
`README.md`.

Attempt 2 (2026-07-12): CI precondition re-verified as SATISFIED, the 6
Google-style README fixes re-derived and applied, committed, and pushed to
`origin/main`. Supersedes attempt 1's FAIL record.

## CI / auto-deploy precondition — PASS (re-verified in-worktree)

Both push-triggered deploy paths are docs-safe for a `README.md`-only commit:

1. **GitHub Actions `.github/workflows/deploy-api.yml`** (Cloudflare Workers,
   the PRIMARY deploy) — `on: push` to `main` with a `paths:` allowlist of
   `src/**`, `frontend/**`, `tests/**`, `wrangler.toml`, `package.json`,
   `package-lock.json`, `tsconfig.json`. GitHub's `paths:` is an INCLUDE
   filter: the workflow runs only when a changed file matches a listed
   pattern. `README.md` and `docs/**` match none, so a docs-only push does
   NOT trigger it. Verified from config. PASS.
2. **`cloudbuild.yaml`** (GCP Cloud Build -> Cloud Run, the ALTERNATIVE) — has
   no `includedFiles`/path filter, so if its trigger were active ANY push to
   main would deploy. But no active trigger exists: `gcloud builds triggers
   list` returned zero for `fooszone` (global + `us-central1`) and for every
   other accessible project (`steady-anchor-243ch`, `nextup-483100`,
   `deepflow-482717`, `dnd-spellbook-478304`, `ai-agents-451316`,
   `mindful-furnace-274014`) — no `portfolio-tracker` trigger anywhere. This
   matches the human's recorded answer ("the trigger is disabled"). PASS.

**Verification method relied on:** independent gcloud confirmation (no active
trigger found in any accessible project) for the Cloud Build path, PLUS direct
config inspection of the GitHub Actions `paths:` allowlist for the Cloudflare
path. The human's "trigger is disabled" answer corroborates the Cloud Build
finding but was not the sole basis. **Post-push confirmation:** after pushing
`main`, `gh run list` showed the most recent workflow run dated 2026-07-04 —
no run fired for the 2026-07-12 docs push, empirically confirming the
path-filter exclusion.

The post-commit hook (`git push`) is present but was harmless: the worktree
branch had no upstream, so the hook's `git push` failed with "no upstream" and
never touched `main`. `main` was then advanced by `git merge --ff-only`
(creates no commit -> fires no post-commit hook, per
docs/memory/drain-dispatch-lessons.md) and pushed with an explicit
`git push origin main`.

## BEFORE counts (Vale, at worktree base 7623b79 = current portfolio-tracker main)

Vale `Google` package over the target docs:

- `README.md`: **8 errors, 14 warnings, 17 suggestions**
- `docs/*.md` (9 files, aggregate): **158 errors, 158 warnings, 493
  suggestions** (predominantly Vale.Spelling false-positives on research-note
  jargon; these are personal research notes, not orientation prose)

## Fixes applied (6, all in README.md — the orientation doc)

All 6 are unambiguous Google-style corrections Vale flags as error/warning with
no proper-noun ambiguity:

1. L12 `## Quick Start` -> `## Quick start` (Google.Headings, sentence case)
2. L36 `## Environment Variables` -> `## Environment variables` (Google.Headings)
3. L45 `(e.g., ...)` -> `(for example, ...)` (Google.Latin, error)
4. L56 `(e.g., ...)` -> `(for example, ...)` (Google.Latin, error)
5. L72 `## Database Setup` -> `## Database setup` (Google.Headings)
6. L97 `### Secrets Setup` -> `### Secrets setup` (Google.Headings)

## Rubric findings (nine-item AI-antipattern rubric)

`README.md` — no rubric antipatterns beyond the heading/Latin style issues Vale
already caught (rubric item 4 over-formatting / item 5 Latinism map onto the
Google.Headings + Google.Latin fixes above). The `## Architecture` bullets and
env-var tables are genuinely enumerable structured/reference content — item-1
carve-out, not list overuse. No hedging (2), sycophancy (3), purple prose (5),
stock acknowledgments (6), repetition (7), vague language (8), or
self-celebration (9). Structure fits Diátaxis (how-to + reference); ordering is
audience-first (what-it-is -> quick start -> config -> deploy).

Reader test (cold read of README): "What is this?" answered in line 1 (a
full-stack portfolio tracker on Hono/Cloudflare Workers + React). "First
action?" clear — the `## Quick start` block. Dual deploy targets are clearly
labeled `(primary)` / `(alternative)`, no stumble. No blocking unanswered
question.

## AFTER counts (Vale, at portfolio-tracker commit 913a433)

- `README.md`: **6 errors, 10 warnings, 17 suggestions**
  - errors 8 -> 6 (both Google.Latin `e.g.` errors cleared)
  - warnings 14 -> 10 (all four fixed Google.Headings title-case warnings cleared)
  - suggestions unchanged (all Google.Parens judgment suggestions, left)
- `docs/*.md`: unchanged (out of practical scope — research notes, not
  orientation prose; no fixes applied there)

### Residual README Vale findings — itemized (all correctly left)

- **6 errors, all Vale.Spelling false-positives on legitimate product/technical
  terms:** `Hono` (L3), `Vite` (L8, L51), `dev` (L9, L34), `Postgres` (L116).
- **10 warnings, all judgment-left:** Google.WordList "Cloud"->"GCP" on the
  proper product names `Cloud Run` / `Cloud Build` (L9, L105, L108, L114,
  L115); Google.Headings on product-name headings (`Portfolio Tracker` H1,
  `Cloudflare Workers (primary)`, `Cloud Run (alternative)`, `Frontend
  (build-time via Vite)`); Google.WordList `application`->`app` (L3).
- **17 suggestions:** all Google.Parens ("use parentheses judiciously") — style
  suggestions, left.

None of the residuals are genuine antipatterns: they are product names, a Vale
dictionary gap, and subjective style suggestions.

## Result

- portfolio-tracker commit pushed to `origin/main`: **913a433** (README.md, 6
  insertions / 6 deletions).
- No deploy triggered (confirmed via `gh run list`).
