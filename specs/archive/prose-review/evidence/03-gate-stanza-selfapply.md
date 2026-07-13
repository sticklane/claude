# Verification: specs/prose-review/tasks/03-gate-stanza-selfapply.md

Verdict: PASS

## C1 — gate template stanza (opt-in, commented-out, orientation-docs only)

Command: `grep -qi 'Vale prose lint' templates/*check*` → HIT.

```
templates/check.sh.tmpl:20:# --- Vale prose lint (opt-in) ------------------
templates/check.sh.tmpl:27:#   run_stage "vale prose lint" vale README.md AGENTS.md docs
```

Read `templates/check.sh.tmpl` lines 20-28: the entire stanza is a `#`-commented
block ("Uncomment to enforce it as a check stage"), the invocation targets only
`README.md AGENTS.md docs` (orientation docs), and it sits above the
`@STAGES@` placeholder so it is inert by default. PASS.

## C2 — `vale README.md AGENTS.md` exits 0 in THIS repo, Google.EmDash active

Command (per caller's environment note, since the machine-global `~/.vale.ini`
points at the canonical checkout, not this worktree):

```
vale --config=/private/tmp/claude-501/-Users-sjaconette-claude/2ef60b45-2141-4410-8eb4-a2985babd531/scratchpad/wt.vale.ini --minAlertLevel=error README.md AGENTS.md
```

Output:
```
✔ 0 errors, 0 warnings and 0 suggestions in 2 files.
EXIT: 0
```
PASS — 0 error-level alerts, exit 0.

Fix mechanism verified (not a rule disable):
- `git diff 162f4d3 HEAD -- README.md AGENTS.md`: 55 insertions / 55 deletions,
  all spaced em-dashes (`word — word`) rewritten to Google's unspaced
  `word—word` style (e.g. `# Agentic development toolkit — orientation` →
  `# Agentic development toolkit—orientation`). Confirmed no remaining
  spaced-em-dash pattern in either file (`grep -noE '[[:alnum:]] — [[:alnum:]]'
  README.md AGENTS.md` → no matches).
- `git diff 162f4d3 HEAD -- vale/styles/config/vocabularies/House/accept.txt`:
  new terms added (Agentic, allowlist, Anthropic('s), Antigravity('s),
  changelog, configs, evals?, gofmt, learnings, OTel, parallelization, pprof,
  profiler, py_compile, Repo/Repos, rulebook, runtimes, Subagent(s), etc.) —
  vocabulary tuning only, no rule suppression syntax.
- `git diff 162f4d3 HEAD` grepped case-insensitively for "emdash" → **no
  hits anywhere in the diff**. Google.EmDash is not disabled or downgraded.
- `git diff 162f4d3 HEAD --name-only`: `AGENTS.md`, `README.md`,
  `templates/check.sh.tmpl`, `vale/styles/config/vocabularies/House/accept.txt`.
  **`vale/.vale.ini.template` is NOT in the diff** — the prior failed path was
  avoided.

All within Touch (`templates/, .claude/skills/gate/,
vale/styles/config/vocabularies/House/accept.txt, README.md, AGENTS.md`) —
`.claude/skills/gate/` shows no diff but is listed in Touch, not a problem.
PASS.

## C3 — e2e report exists and substantively covers all three passes

Command: `test -s specs/prose-review/evidence/e2e-readme-review.md` → exists,
110 lines, non-empty. PASS (existence).

Content check (manual, read in full):
- **Pass 1 — Vale (deterministic): PASS** — cites `vale README.md AGENTS.md`
  exit 0, explicitly states Google.EmDash stays active and explains the
  unspaced-em-dash rewrite + vocabulary tuning (not rule suppression), and
  notes the canonical-checkout `~/.vale.ini` StylesPath caveat the same way
  this verification had to.
- **Pass 2 — Rubric (nine-item AI-antipattern): PASS** — walks all 9 rubric
  items individually with a verdict and rationale for each, plus two
  low-severity (non-blocking) observations.
- **Pass 3 — Reader test (cold-read, fresh-context agent): PASS with
  stumbles** — answers "what is this / what would I do first", and reports
  six ranked stumbles in a table (location/kind/reason/suggested rewrite)
  plus one open question.
- Verdict section ties all three together.

All three passes are substantively present with concrete evidence, not
placeholders. PASS.

## Append-only task-file check (vs base 162f4d3)

`git diff 162f4d3 -- specs/prose-review/tasks/03-gate-stanza-selfapply.md` →
**empty** (file byte-identical to base). Confirmed with
`git show 162f4d3:<path> | diff - <path>` → `FILES IDENTICAL`. Trivially
append-only-compliant (no edits at all), so no violation.

**Observation (not a criterion failure):** the task file's `Status:` line is
still `in-progress` and none of the three acceptance checkboxes are ticked,
even though the underlying implementation (commits `4a078d4`
"feat(gate): add opt-in Vale prose lint stanza to check template" and
`6c84840` "style: adopt Google unspaced em-dash house style + tune House
vale vocab") is present and all three criteria verify green. The e2e evidence
file itself is untracked/uncommitted (`git status --short` shows only `??
specs/prose-review/evidence/e2e-readme-review.md`). This looks like the
worker completed the work but never closed out the task-file bookkeeping or
committed the evidence file — worth flagging to the orchestrator so the task
record and evidence get committed/updated, but it is not one of the three
acceptance criteria and does not constitute an append-only violation (since
no edit was made at all).

## Scope check

`git diff 162f4d3 HEAD --name-only`: `AGENTS.md`, `README.md`,
`templates/check.sh.tmpl`, `vale/styles/config/vocabularies/House/accept.txt`
— all inside Touch. No scope creep. The untracked `vale/styles/Google/`
directory noted by the caller is gitignored and not part of the diff.

## Gates

Repo-wide `scripts/check.sh` not run (out of scope for these three specific,
narrowly-scoped criteria and not requested); the acceptance-criteria commands
above are the specified gates for this task and all pass.
