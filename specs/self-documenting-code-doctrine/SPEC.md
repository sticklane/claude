# Self-documenting code: inline comments are a smell

Status: open
Priority: P2

## Problem

The toolkit's code-quality doctrine (`.claude/rules/quality-discipline.md`,
and the `/code-review` and `/simplify` skills) says nothing about comments.
The operator's standing rule (2026-07-21): comments belong on
modules/classes/objects/functions/methods — documenting intent, contract, and
the non-obvious *why* — NOT inline within a function body. An inline comment
is almost always a sign the code itself is unclear; the fix is to rewrite it
clear, idiomatic, and self-documenting (better names, extracted functions),
not to annotate it. Inline commentary is **meta-discourse in code** — the
same antipattern the writing doctrine targets for prose
(`specs/agentic-prose-tells`), applied doubly to comments. Agents currently
scatter explanatory inline comments with no doctrine discouraging it, and no
review check flags them.

## Solution

State the doctrine once in `.claude/rules/quality-discipline.md` (a
"Comments and self-documenting code" section) and have `/code-review` and
`/simplify` cite it as a review dimension rather than restating it. Mirror the
rule's spirit into `antigravity/AGENTS.md`'s quality section so it binds the
non-Claude runtimes too (cross-runtime, per the operator's equal-application
ask). The doctrine is a smell heuristic, not an absolute ban: an inline
comment explaining a genuinely non-obvious *why* (a workaround, a subtle
invariant, a citation) is allowed when the code cannot carry it — the default
is refactor, the exception is documented.

## Requirements

- **R1**: `.claude/rules/quality-discipline.md` gains a concise "Comments and
  self-documenting code" section: declaration-level comments for intent/
  contract/why; inline comments treated as a refactor trigger (rename,
  extract), not a documentation tool; the narrow non-obvious-why exception
  named.
- **R2**: `/code-review` (and `/simplify` where it fits) cites the new section
  as a review dimension — flag inline comments that narrate what the code does
  and propose the refactor — without restating the rule.
- **R3**: The doctrine is mirrored in spirit into `antigravity/AGENTS.md`'s
  quality-discipline register so non-Claude agents are bound; cross-references
  resolve under each runtime.
- **R4**: Cross-references the meta-discourse writing tell
  (`specs/agentic-prose-tells`, T1) as the shared root antipattern.

## Out of scope

- Docstring style/format conventions (Google/NumPy/etc.) — this is about
  inline-comment discipline, not docstring formatting.
- A mechanical lint that bans all inline comments — the non-obvious-why
  exception makes a blunt lint wrong; this stays a review-judgment dimension.

## Acceptance criteria

- [ ] `grep -qi 'self-documenting' .claude/rules/quality-discipline.md` and the
  section names the inline-comment-as-refactor-trigger heuristic
- [ ] `/code-review` reference/skill cites the new section (grep for the
  section anchor)
- [ ] `antigravity/AGENTS.md` quality section carries the doctrine in its
  register
- [ ] cross-reference to the meta-discourse tell present

Note: needs `/critique` before `/breakdown` (no Breakdown-ready flag yet).
