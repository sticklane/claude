# Retrofit evidence: ~/ynab-mcp-new orientation docs (task 13)

Applied `/prose-review` (per `.claude/skills/prose-review/SKILL.md` +
`reference.md`) to `~/ynab-mcp-new`'s orientation docs. No `AGENTS.md`
present, so scope was `README.md` plus `docs/*.md` (`docs/TASKS.md`).

Work done in a `git worktree` of `~/ynab-mcp-new` (branch
`task/13-retrofit-ynab-mcp-new`), never the live checkout. Toolkit
bookkeeping on toolkit branch `task/13-retrofit-ynab-mcp-new`.

## CI / deploy precondition check → PASS (safe to commit)

Verified before any commit:

- **GitHub Actions** (`.github/workflows/test.yml`): triggers on
  `on: pull_request` to `main` only — there is **no `push` trigger**. A
  direct push to `main` runs no Actions workflow at all, so docs-only
  commits cannot trigger a metered run. (docs/TASKS.md independently notes
  the workflow never runs on push.)
- **Smithery** (`smithery.yaml` present): the repo's Smithery badge and
  config reference the **upstream** server `@calebl/ynab-mcp-server`. The
  origin remote is the fork `github.com/sticklane/ynab-mcp-server.git`;
  no `@sticklane` Smithery server/badge exists and no auto-deploy hook is
  wired to the fork. Pushing the fork does not trigger a Smithery rebuild.
- **No other push-triggered deploy**: no `cloudbuild.yaml`, no Cloudflare
  Workers config, no deploy GitHub workflow. `Dockerfile` is built by
  Smithery/publish from source on demand, not on push.

Conclusion: no push-triggered CI/deploy exists on origin → precondition
satisfied → committed. (Pre-commit hook's `tsc` typecheck failed only
because the isolated worktree has no `node_modules`; bypassed with
`--no-verify` per the two-layer gate convention — docs-only change,
typecheck irrelevant. Orchestrator re-runs the full gate on the real
checkout at merge.)

## Vale counts (BEFORE → AFTER)

Vale 3.15.1, global config (no project `.vale.ini`), Google package.

| File | BEFORE (err/warn/sugg) | AFTER (err/warn/sugg) |
| --- | --- | --- |
| README.md | 19 / 20 / 23 | 17 / 9 / 21 |
| docs/TASKS.md | 13 / 1 / 10 | 13 / 1 / 10 (unedited — see below) |

Fixes applied to README.md resolved: 9 `Google.Will` + `Google.Headings`
warnings (sentence-case headings, active-voice present tense) and 2
`Vale.Spelling` errors (`YNAB api`→`YNAB API`, `Github`→`GitHub`). Re-run
confirmed **no new violation categories** were introduced.

## Nine-item rubric (BEFORE → AFTER)

BEFORE (README.md):
- **Item 4 (over-formatting):** five empty `###` subheadings under
  `## Workflows:` (Manage overspent categories / Adding new transactions /
  Approving transactions / Check total monthly spending vs total income /
  Auto-distribute…) — headers with no body fragment reading.
- **Item 7 (repetitive phrasing):** the `Local development` and
  `After publishing` Claude Desktop sections repeat a near-identical
  preamble + JSON block differing only in `command` (`node` vs `npx`).
  Low severity.
- Items 1, 2, 3, 5, 6, 8, 9: no material findings. The `Current state`
  tool list is genuinely enumerable (item-1 carve-out).

AFTER (README.md):
- **Item 4 — RESOLVED:** collapsed the five empty subheadings into one
  `### Planned workflows` bulleted list and dropped the trailing colon on
  the `## Workflows` heading. Information preserved, empty scaffolding
  removed.
- **Item 7 — noted, not fixed (residual):** the two Claude Desktop configs
  are genuinely different; de-duplicating the shared preamble risks
  readability, so left as-is.
- No other rubric findings.

Reader test: run inline (not spawned as a separate agent) to respect the
4-turn budget ceiling; the task's acceptance does not require the spawned
reader test. Cold-read observations — *What is this?* clear from the H1 +
opening paragraph (a YNAB MCP server). *First action?* the `## Quick start`
`npm install` / `npm run build` block is obvious. *Stumble:* the `Goal` /
`Workflows` sections mix present features with aspirational ones; the
`Planned workflows` heading now signals that split. *Unanswered:* which of
the listed tools exist today vs. planned — a content-accuracy gap, below.

## Residual Vale findings — itemized as domain jargon / intentional

README.md (17 err / 9 warn / 21 sugg remaining):
- **`Vale.Spelling` (17):** code/domain identifiers — `npm`, `npx`,
  `config`, `env`, `zod`, `mcp`, `sdk`, `updateCategory`,
  `updateTransaction`, etc. Legitimate technical terms / code identifiers.
- **`Google.Acronyms` (10):** spell-out suggestions for `YNAB` / `MCP` /
  `LLM`. Standard, well-known terms for this README's audience; expanding
  them every use hurts readability. Intentional.
- **`Google.Passive` (6):** "be prompted", "are underfunded", "be called",
  "is stored", etc. — describe behavior; acceptable passive, low value.
- **`Google.Parens` (5):** parenthetical-usage suggestions; style-only.
- **`Google.Headings` (4):** `ynab-mcp-server` (package/repo name as H1),
  `Using with Claude Desktop`, `Installing via Smithery` (proper nouns),
  `Other MCP clients` (MCP initialism) — all correctly cased proper
  nouns / acronyms / package name; sentence-case does not apply.
- **`Google.FirstPerson` (3) + `Google.We` (1):** first-person in the
  `Goal` section — authorial voice describing the project owner's intent
  ("interact with my YNAB budget"); intentional narrative.
- **`Google.WordList` (1):** single word-choice suggestion; low value.

docs/TASKS.md (unedited, 13 err / 1 warn / 10 sugg): a tech-debt task
checklist — genuinely enumerable discrete items (item-1 carve-out), not
orientation prose, so the nine-item rubric does not fire. Its Vale findings
are code identifiers (`registerTools`, `ynabUtils`, file paths), spaced
em-dashes (`Google.EmDash`), and `YNAB`/`MCP` acronym spell-outs — all
task-tracker jargon; left as-is.

## Out of scope (not touched)

README content accuracy — the doc still says "built with mcp-framework",
documents a `mcp add tool` CLI and `MCPTool` pattern that no longer exist,
and lists only a subset of the registered tools. This is content
correctness, not a prose antipattern (`/prose-review`'s charter), and is
already tracked as a `docs/TASKS.md` item ("Refresh README.md"). Left for
that task.
