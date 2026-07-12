---
name: prose-review
description: Reviews human-facing technical writing (a file, a diff, or pasted text) against a nine-item AI-antipattern rubric, the Google style guide via Vale, and a reader test — reporting findings ranked by severity, read-only by default. Also the doctrine an agent loads BEFORE writing docs (Diátaxis structure + Google essentials). Trigger phrases - "/prose-review", "review this doc", "check the writing", "is this README well-written", "prose review this", and for authoring "write the README", "draft the docs", "improve this doc". Not for code or docstrings (that is /code-review) or a spec's content and completeness (that is /critique).
argument-hint: "[path/to/doc | 'diff' | pasted text] [--fix]"
---

Review the human-facing prose in $ARGUMENTS for the writing antipatterns this
toolkit's docs fall into. This is review of *style and comprehension*, the gap
`/code-review` (code only) and `/critique` (a spec's content, not its prose)
leave open. The doctrine — the nine-item rubric with vendor quotes, the
Diátaxis quadrant table, the Google essentials, the reader-test procedure —
lives in [reference.md](reference.md), loaded on demand; load the section a
pass needs, not the whole file.

**Scope.** Target human-orientation docs: README.md, AGENTS.md, docs/*.md,
and human-facing prose in a diff or pasted snippet. Never machine-parsed
prose — task files, specs/, or SKILL.md bodies — and never code comments or
docstrings (those stay `/code-review`'s job).

**Invocation gate.** The read-only report mode is model-invocable — same risk
class as `/critique` and `/simplify`. **`--fix` is human-typed only:** never
infer or add it from a vague request ("clean up this doc" is a review
request, not a `--fix` authorization). A flag cannot distinguish a
human-typed argument from a model-added one, so this is a behavioral rule, not
a mechanism — auto-rewriting from a subjective rubric is real mutation risk (a
misjudged item-1 carve-out could damage structured content). This skill is
not an execution stage and self-chains nothing.

## Review mode (default)

Run the passes in order and merge every finding into one report.

1. **Vale pass (deterministic) — first, when the target is a file AND `vale`
   is installed.** Run `vale <file>`; merge its findings, each attributed to
   its Vale rule (e.g. `Google.Passive`). If `vale` is absent (soft
   dependency — the installer ships in a separate task), skip this pass and
   note one line in the report: "Vale not installed — deterministic pass
   skipped; run bin/install-vale to enable." For a diff or pasted-text target
   there is no file to lint, so this pass does not apply.

2. **Rubric pass (judgment) — always.** Read reference.md's nine-item rubric
   and flag violations. Honor item 1's carve-out: structured technical
   content (a spec's Requirements/Acceptance sections, API references,
   genuinely enumerable lists) is not "list overuse" — when unsure, do not
   flag it.

3. **Reader test — for orientation docs (README.md, AGENTS.md) by default.**
   Spawn one fresh-context agent per reference.md's "reader test" procedure
   (session tier, awaited child, capped return) and merge its stumble report.
   Skip it for diffs and pasted text — a fragment has no cold-read context to
   test.

### Report

Findings ranked by severity, most-blocking first, in a table:

| Location | Rule | Reason | Suggested rewrite |
| --- | --- | --- | --- |
| `file:line` or quoted excerpt | rubric item N, or Vale rule, or reader-test stumble | one line | the concrete rewrite |

Reader-test answers (what is this / first action / stumbles / unanswered
question) go above the table when the reader test ran. **Zero findings is a
valid, explicit outcome** — report "No antipatterns found" rather than
inventing findings; a reviewer told to find something always will.

## --fix mode (human-typed only)

With `--fix`, apply the suggested rewrites directly to the file after the
review. `--fix` **requires a file-path target** — given a diff or pasted
text it errors ("--fix needs a file path to write to") rather than guessing
where the text lives. Apply only rubric/Vale rewrites you are confident of;
leave item-1-carve-out judgment calls in the report unapplied. Re-run the
Vale pass after writing to confirm no new violations were introduced.

## Authoring doctrine (load before writing)

Before writing or substantially reshaping a human-facing doc (README.md,
AGENTS.md, docs/*.md), load reference.md's Diátaxis and Google-essentials
sections FIRST: pick the quadrant from "what does the reader need RIGHT NOW",
order audience-first, one idea per paragraph. This is what makes the review
pass on the first draft instead of the third.

Next stage: none — the author applies the report's rewrites (or reruns with
`--fix`), or loads the doctrine and writes (human-launched).
