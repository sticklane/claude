# Task 04: Reference-file TOCs + context-management research record

Status: done
Depends on: ../../model-agnostic/tasks/02-core-tier-language.md, ../../code-vs-llm/tasks/01-ladder.md
Budget: 30 turns
Spec: ../SPEC.md (requirements R2-impl, R7; R9 note)

## Goal

Every reference file currently over 100 lines opens with a table of
contents: drain (205 lines), fleet (182), gate (167), autopilot (110),
evals (110). The TOC must be greppable as "contents" or "TOC" within the
first 5 lines of each file — put a Contents line/heading directly under
the H1. `docs/external-playbooks.md` gains a "Context management"
section recording the research: what was adopted (R1–R6 mapped to
sources), what was already covered (attention budget, JIT retrieval,
subagent isolation with the 1,000–2,000-token summary validation of
scout budgets, progressive disclosure), where the toolkit leads
(tool-result size discipline — no vendor guidance found), and what was
deliberately skipped (ADK scope tiers, artifact versioning, OpenAI
verbatim-minus-tools handoffs — one-line reasons each), with source
links (Anthropic context-engineering post and Claude Code docs, ADK
sessions/memory whitepaper, OpenAI caching and prompting guides).
Antigravity has no mirrors of these reference files, so no mirror edits.
Do NOT bump plugin.json — the combined bump (R9) is owned by global
task 99 in specs/review-fixes.

## Touch

- `.claude/skills/drain/reference.md`
- `.claude/skills/fleet/reference.md`
- `.claude/skills/gate/reference.md`
- `.claude/skills/autopilot/reference.md`
- `.claude/skills/evals/reference.md`
  - Cross-spec (all five reference files): also edited by review-fixes,
    model-agnostic, chaining-antipatterns — see
    specs/QUEUE.md
- `docs/external-playbooks.md` — Cross-spec: also edited by all other
  feature queues — see specs/QUEUE.md

## Steps

1. For each of the five reference files, add a short TOC of the file's
   `##` sections immediately after the title line (keep it inside the
   first 5 lines so the acceptance loop's `head -5` grep sees it).
   Content is otherwise unchanged.
2. Append the "Context management" section to
   `docs/external-playbooks.md` per R7 (adopted / already covered /
   toolkit leads / deliberately skipped, with source links); it must
   contain the phrase "tool-result size". Follow that file's existing
   convention: state the rule pointers, keep research there.

## Acceptance

- [x] `for f in .claude/skills/*/reference.md; do [ "$(wc -l < "$f")" -le 100 ] || head -5 "$f" | grep -qi "contents\|TOC" || exit 1; done` (R2 — every >100-line reference file opens with a TOC) — exit 0; all five files carry a `Contents:` line at line 3 matching their real `##` headings (../evidence/04-reference-tocs-research-record.md)
- [x] `grep -qi "context management" docs/external-playbooks.md && grep -qi "tool-result size" docs/external-playbooks.md` (R7) — exit 0; section covers adopted/already-covered/leads/skipped with source links (../evidence/04-reference-tocs-research-record.md)
