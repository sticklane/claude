---
description: Interview-driven reprioritization of the current repo's open work - scan every pending/blocked/deferred/draft task plus every spec with no tasks/ breakdown yet across specs/, present the table, take one free-form reply, and rewrite the named tasks' (or SPEC.md's) Priority: headers in one commit. Reorders work; it does not report the next pipeline command (for that, list-specs). Human-launched only, since it mutates task files and commits.
---

Reorder a repo's pending work by rewriting `Priority:` headers, driven by
one interview turn. This is a human-launched workflow (it mutates task files
and commits). It applies exactly what the human states — it never invents or
suggests an ordering. Contracts, top-first:

- **Scope is the current repo's `specs/`** (excludes `archive/`): every
  `pending`/`blocked`/`deferred`/`draft` task, plus one row per spec with no
  `tasks/` breakdown yet (its `SPEC.md` stands in). The deterministic scan
  is `prioritize_scan.py`, the interview is this prose.
- **Ask exactly ONE free-form question** (the R3 wording below), never a
  fixed-option picker — an option list can't represent an arbitrary
  re-ranking.
- **Validate before editing**: a `Ref` must match a scanned row and a target
  must normalize to `P0`-`P3`; anything else is reported "not applied", never
  guessed.
- **Commit only when ≥1 change applied**; "none" or all-invalid makes no
  commit and no edits.

## Procedure

1. **Run the scanner.** Print a one-line plain-text lead-in to the user
   BEFORE the scanner call (e.g. "Scanning specs/ for reorderable work…") —
   the invocation must never be silent from the user's side. Then, from the
   repo root, run `python3 <this workflow's skill dir>/prioritize_scan.py` —
   the scanner ships in the mirrored skill directory
   `.agents/skills/prioritize/prioritize_scan.py`. If it prints
   `nothing to reprioritize`, relay that line to the user as the turn's
   closing message and stop — no interview, no commit; never end the turn
   without reporting it.

2. **Present the table and ask one question.** Lead with a short plain-text
   line (e.g. "Here's what's open:") before the table — some terminal
   clients have been observed to drop markdown tables that immediately
   follow a tool call in the same turn, and the lead-in line gives the
   renderer a plain-text anchor first. Then relay the scanner's markdown
   table (`| Ref | Title | Status | Priority |`) verbatim, then ask exactly
   this, as a plain conversational question (not a fixed-option picker):

   > What changes should I make? Reference tasks by their `Ref` (e.g. 'make
   > drain-sweep-preservation/03-worker-commits.md P0'). Say 'none' if you're
   > done looking.

   The table and the question must be the turn's final message, with no
   tool calls after them — text emitted between tool calls in the same turn
   may never be rendered to the user at all, which reads as the workflow
   producing no output.

   Interpret the free-form reply the way you would any natural-language
   instruction — there is no rigid grammar.

3. **Validate each proposed change.** For every task the reply names with a
   target priority: the `Ref` must match a row from step 1's table, and the
   target must normalize to one of `P0`/`P1`/`P2`/`P3` (case-insensitive →
   uppercase). A `Ref` not in the table, or a target outside `P0`-`P3`, is
   **not applied** and **not guessed**: collect it to report back as
   `not applied: <reason>`. A reply of "none" (or equivalent — "no changes",
   "looks fine") means zero changes; skip to step 6.

4. **Apply each validated change.** Edit only the `Priority:` header of each
   named file (a task file, or a `SPEC.md` when the `Ref` points at one):
   - if a `Priority:` line already exists, replace its value in place;
   - else insert `Priority: <PX>` immediately below the `Status:` line when
     one exists;
   - else, for a task file with neither header, insert it as the first
     header line, above the first `#`/`##` heading (matching a
     drain-discovered task file's header-before-title shape);
   - else, for a headerless `SPEC.md`, insert it immediately below the
     `# Title` line instead — every real `SPEC.md` in this repo puts its
     title first, so inserting above it would put `Priority:` before the
     file's own heading.

   Touch no other line in the file.

5. **Commit.** If at least one change was applied, stage every edited task
   file and commit them together with exactly:

   ```
   chore: reprioritize <N> task(s) across <M> spec(s) per interview
   ```

   where `<N>` is the number of task files edited and `<M>` the number of
   distinct specs they span. Make no commit when the reply was "none" or
   every proposed change failed step 3's validation.

6. **Report and exit.** State what was applied and list any
   `not applied: <reason>` items. On "none" or all-invalid, exit cleanly —
   no edits, no commit.

Next stage: none — the human decides what to /build or /drain next.
