---
name: example-corpus
description: Captures a bad writing or bad code example the moment one arises — from a review finding, a user correction, or a caught AI-tell — pairs it with an agreed better version, and appends the approved pair to a corpus future agents load as calibration. Use when the user says "add this to the bad examples", "capture this as a bad example", "save this as a writing/code example", or when a review surfaces a teachable bad-vs-better pair worth keeping. NOT for general lessons or conventions (/distill routes those to CLAUDE.md/rules/skills) — this skill stores only concrete before/after example pairs.
---

Two corpora live in this directory, one per domain:

- [writing-examples.md](writing-examples.md) — bad prose → approved rewrite
- [code-examples.md](code-examples.md) — bad code → approved fix

Consumers read APPROVED entries only, and each corpus holds at most 10
approved entries — the cap keeps the per-invocation token cost of every
consumer flat. Entries are append-only with one exception: curation. Adding
an entry that would exceed the cap must prune or merge a weaker entry in
the same edit (the one sanctioned rewrite of existing entries).

## Procedure

1. **Capture verbatim.** Copy the bad example exactly as found, with its
   source (file/PR/session, date). Never paraphrase the bad half — the
   point is the real artifact.
2. **Diagnose.** Name the principle violated, citing the existing doctrine
   rather than restating it: writing → /prose-review's rubric or
   anti-ai-slop-writing's banned-words reference; code → the
   self-documenting-code section of `.claude/rules/quality-discipline.md`
   or the convention the code breaks.
3. **Propose.** Draft 1–2 better versions that fix only the diagnosed
   problem — a rewrite that also restyles everything else teaches nothing.
4. **Approve.**
   - Attended: present bad/better via `AskUserQuestion` (pick a version,
     edit, or reject). Approved entries append with `Status: approved`.
   - Unattended: append with `Status: proposed` AND file the approval in
     bd — `bd create "approve corpus entry <ENN>" --deps
discovered-from:<current-id>` — so the pending entry is discoverable
     from `bd ready`, not buried in a file (CLAUDE.md's Beads section).
     Approval later flips the Status line and closes the issue.
5. **Append** using the entry grammar below. Renumber nothing; new entries
   take the next ENN.

## Entry grammar

```markdown
### E<NN> — <principle slug> (<YYYY-MM-DD>, <source>) — Status: approved|proposed

**Bad:**
<fenced block, verbatim>

**Better:**
<fenced block, the approved version>

**Why:** <one line naming the violated principle, citing its doctrine home>
```

## Consumers

- Writing: /prose-review and anti-ai-slop-writing point here for
  calibration examples.
- Code: /build's simplification pass and the self-documenting-code rule
  point here.

`Next stage: none — a human approves proposed entries (tracked in bd)`.
