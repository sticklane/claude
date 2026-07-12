# Retrofit evidence: ~/tdd-git-hooks orientation docs

Task 11 (spec prose-review, R9). /prose-review procedure applied manually
(nine-item rubric + Vale/Google + reader test) to ~/tdd-git-hooks.

Work done in a `git worktree` of ~/tdd-git-hooks on branch
`task/11-retrofit-tdd-git-hooks` (live checkout untouched). Toolkit
bookkeeping on toolkit branch `task/11-retrofit-tdd-git-hooks`.

## CI-precondition check (before any commit)

- `ls ~/tdd-git-hooks/.github/workflows/` → **none**. No `.gitlab-ci.yml`,
  `.circleci`, `Jenkinsfile`, or any `*.yml`/`*.yaml` CI config anywhere in
  the repo.
- **Result: no push-triggered CI exists.** Precondition satisfied — a
  docs-only commit triggers no metered runner, so committing is allowed
  (task step 3: "If there's no push-triggered CI ... proceed to commit").
- Repo's own git hooks: no non-sample hooks installed in the shared
  `.git/hooks/` (repo has no `package.json`), so no pre-commit AI review or
  test run fires on commit — no `--no-verify` bypass needed.

## Target docs (scope)

Orientation docs = README.md, plus AGENTS.md if present, else docs/*.md.
No AGENTS.md present → targets are **README.md** and **docs/TASKS.md**.

## Vale counts (BEFORE → AFTER)

Vale 3.15.1, global `~/.vale.ini` (Vale + Google packages, `*.md`).

| File | BEFORE (err/warn/sugg) | AFTER (err/warn/sugg) |
| --- | --- | --- |
| README.md | 4 / 24 / 21 | 3 / 9 / 18 |
| docs/TASKS.md | 2 / 1 / 6 | 2 / 1 / 6 (unchanged) |

README warnings dropped 24→9 (heading sentence-case, will, colons resolved);
the one BEFORE error removed was the stray exclamation (Google.Exclamation).
One spaced-em-dash error (Google.EmDash) was accidentally introduced mid-edit
and removed before commit — final AFTER errors are all pre-existing jargon.

## Rubric findings (nine-item AI-antipattern pass)

BEFORE (README):
- Item 4/5/9 (over-formatting / clichéd filler / self-celebratory): stray
  exclamation "Contributions welcome!" and "(no skipped tests!)".
- Google-essentials (audience-first / concrete): Quick Start offered three
  install methods with no recommended default; prerequisites hardcoded a
  personal absolute path `/Users/sjaconette/.local/bin/claude`.
- Google-style mechanics (Vale-backed but rubric-visible): Title Case
  headings throughout; passive voice ("the commit is aborted", "All code
  reviews are saved"); "will" future tense.
- Item 1 (list overuse): NOT flagged — Features / NEVER-bypass lists are
  genuinely discrete/enumerable (carve-out applies).

AFTER (README): rubric findings resolved —
- Exclamations removed (declarative statements).
- Recommended default install method added ("Option 1 suits most projects").
- Personal path replaced with generic `~/.local/bin/claude` default +
  configurable pointer.
- Section headings sentence-cased; passive→active ("Git aborts the commit",
  "The hooks save all code reviews"); "will"→"performs these steps".

docs/TASKS.md: no rubric antipatterns. It is an enumerable tech-debt
checklist (item-1 carve-out) — left unchanged.

## Reader test (cold fresh-context read of README)

Ran one fresh-context agent. Prose-fixable stumbles addressed above
(no recommended install default; personal path in prerequisites). Remaining
stumbles are content gaps, not prose antipatterns, and were NOT auto-fixed
(out of a prose review's confident-rewrite scope; would need author input):
- Clone URL placeholder `YOUR_USERNAME` (template repo).
- Hook-edit instructions cite line numbers ("line 17", "line 206",
  "line 30-135") without showing the referenced excerpt.
- CLAUDE.md listed in File structure but its role never explained.
- The AI review's CRITICAL-vs-medium severity mechanism is never described.

These are recorded here for a future content pass; the retrofit's charter is
prose/style, not filling doc content gaps.

## Residual Vale findings (AFTER) — itemized, justified as domain jargon / quoted / structural

README.md (3 err / 9 warn / 18 sugg):
- Vale.Spelling `npm` (28), `pkill` (179), `claude` (188) — real
  commands/tool names; domain jargon, correct as written.
- Google.Headings `TDD Git Hooks` (1) — H1 project title/brand; kept.
- Google.Headings `pre-commit` (87), `pre-commit-review` (98),
  `post-commit` (108) — literal hook filenames; false positive (they are
  code identifiers, already lowercase).
- Google.Headings `Configure Claude Code path` (148) — "Claude Code" is a
  proper noun correctly capitalized; Vale false positive.
- Google.Colons `: E` (96) — bold run-in label followed by a full
  imperative sentence; acceptable.
- Google.WordList `kill` (177,179), `disable` (180) and Google.Acronyms
  `NEVER` (177-180) and Google.Passive `are broken` (183) — all inside the
  quoted "TDD best practices" blockquote; quoted material, not edited.
- Google.Acronyms `TDD` (1), `MIT` (247) — standard, widely understood;
  TDD is expanded on first use (line 3). `NEVER` emphasis intentional.
- Google.Parens (many, all suggestions) — concise, judicious parentheticals.

docs/TASKS.md (2 err / 1 warn / 6 sugg), unchanged:
- Vale.Spelling `npm` (18, 19) — command name; jargon.
- Google.Parens (6 suggestions) + 1 warning — enumerable checklist items
  with judicious parentheticals; acceptable for a tech-debt tracker.
