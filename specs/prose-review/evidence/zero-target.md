# R9 zero-target evidence

The R9 retrofit wave runs `/prose-review` over each `std`-marked repo's
orientation docs (README.md, plus AGENTS.md when present, else `docs/*.md`)
and records before/after finding counts. A repo with none of these targets
SKIPS with a zero-target entry — retrofit never authors new docs (SPEC R9).

This file records the zero-target repos: `std`-marked repos that expose no
orientation-doc target, so no `/prose-review` pass ran and no docs were
authored or changed.

## ~/automation

- **Status:** zero-target — skipped, no docs authored.
- **Targets checked:** README.md, AGENTS.md, `docs/*.md`.
- **Result:** none of the orientation-doc targets are present, so there is
  nothing for `/prose-review` to review. Per R9 ("a repo with none of these
  SKIPS with a zero-target evidence entry — retrofit never authors new
  docs"), the repo is recorded here rather than having docs created for it.
- **Docs authored/changed:** none.
- **CI paths-ignore precondition:** not applicable — no docs-only commit is
  made against this repo (nothing to commit), so no push-triggered CI run is
  billed.

## ~/dev-agents

- **Status:** zero-target — skipped, no docs authored.
- **Targets checked:** README.md, AGENTS.md, `docs/*.md`.
- **Result:** none of the orientation-doc targets are present, so there is
  nothing for `/prose-review` to review. Recorded as a zero-target skip under
  R9 rather than authoring new orientation docs.
- **Docs authored/changed:** none.
- **CI paths-ignore precondition:** not applicable — no docs-only commit is
  made against this repo (nothing to commit), so no push-triggered CI run is
  billed.
