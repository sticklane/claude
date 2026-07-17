# Human-blocker entries: plain language + stated impact

Breakdown-ready: true

## Problem

`HUMAN.md`'s `## Agent-filed blockers` section is the durable queue of
things only a human can do, filed by `/drain` (and read by `/human-tasks`
and any human skimming the repo). Today's grammar
(`.claude/rules/human-blockers.md`) is a single terse line:

```
- [ ] <ISO date> · <source path> · <ask|run|provision|decide> — <one-line action>
```

The `<one-line action>` text is copied close to its source (a deferred
question, an `Unblock:` line, a stub's assess-stage reason, a NOT-READY
critique finding) rather than authored for a reader who hasn't opened that
source file — it can carry task IDs, internal jargon, and file paths with no
surrounding context. It also never states impact: a human scanning the
section has no way to tell, without opening the source file and tracing
`Depends on:` edges by hand, what stays stuck if this particular item sits
unanswered. The current repo's own `HUMAN.md` has exactly one live entry
(the `trajectory-evals` NOT-READY line) and it exhibits both problems: it
assumes familiarity with "R4 and R5", "the codex mirror", and "the approved
edit list", and never says what remains blocked.

## Solution

Add a `Blocks:` clause to the entry grammar and tighten drain's HUMAN.md
filing procedure (`.claude/skills/drain/reference.md`'s "HUMAN.md filing
(R2)" section) so every newly filed entry states its impact, computed
mechanically where the queue already has the data.

**The row split (pinned, by drain reference.md's six mapping-table rows —
`.claude/skills/drain/reference.md:1732-1739`):** the deciding factor is
whether the row's source is a **task file** carrying `Status:` (which has
real `Depends on:` dependents somewhere in the queue) or something that
isn't a node in that dependency graph at all (a draft stub, or a whole
spec). That split is:

- **Dependency-bearing (4 rows) — derive `Blocks:` from `Depends on:`
  edges:** "Deferred questions still unanswered", "`Contradicts-premise`
  deferred", "`Unblock: ask:` blocked tasks", "`Unblock: run:` blocked
  tasks". All four are filed from a task file whose `Status:` is `deferred`
  or `blocked`; that task file is a valid `Depends on:` target, so other
  pending tasks may name it. Derive the task-name set from the exact same
  lookup `/drain`'s SKILL.md step 2 dispatch tie-break already computes
  ("count of still-`pending` tasks whose `Depends on:` names this task,
  resolved as the dispatchability check does" — `.claude/skills/drain/SKILL.md:130`)
  — that computation already walks the full candidate set to produce a
  count; expose the underlying task-name set it counts, not just the
  count, and render `Blocks:` from the names. Render as the blocked task
  names/paths (e.g. "Blocks: task 09 (notes CRUD), task 11 (MCP server)"),
  or "Blocks: no other pending task" when the set is empty.
- **Fixed-phrase (2 rows) — a literal, per-row string, not derived:**
  - "Decision-shaped or gate-refused stubs" → `Blocks: promotion of this
stub to a dispatchable task`
  - "NOT-READY specs (critique intake)" → `Blocks: breakdown of this spec
into dispatchable tasks`

  These two sources are not task files with `Depends on:` dependents (a
  draft stub and a whole spec aren't queue nodes other tasks point at the
  same way), so there is nothing to traverse — the phrase names the one
  fixed downstream stage that source type always blocks.

The action clause itself also gets an explicit plain-language rule: it must
be readable and actionable without opening the source file — expand task
IDs into what they actually do, name the file only as a pointer, not as the
explanation.

Retrofit is in scope: the repo's current live `HUMAN.md` entry is rewritten
to the new grammar as part of this work (if it has since resolved and been
removed by the time this is implemented, that's a no-op, not a failure —
the acceptance check below is conditioned on the entry still being present
and unmodified; if present but its text has changed since this spec was
written, retrofit whatever current text is found, don't insist on the
original wording).

## Requirements

R1: `.claude/rules/human-blockers.md`'s entry grammar line is extended with
a `Blocks:` clause: `- [ ] <ISO date> · <source path> · <ask|run|provision|decide>
— <plain-language action> — Blocks: <impact>`.

R2: `.claude/rules/human-blockers.md` states the plain-language rule for the
action clause explicitly: readable and actionable without opening the
source file; expand jargon/task-ID shorthand into what it actually means.

R3: `.claude/skills/drain/reference.md`'s "HUMAN.md filing (R2)" section
states, per row of its six-row mapping table, how `Blocks:` is derived —
for the four dependency-bearing rows ("Deferred questions still
unanswered", "`Contradicts-premise` deferred", "`Unblock: ask:`",
"`Unblock: run:`"): the mechanical `Depends on:` task-name derivation
citing SKILL.md step 2's existing "unblocking-power" computation (not a
new traversal); for the two fixed-phrase rows ("Decision-shaped or
gate-refused stubs", "NOT-READY specs"): their literal phrase, verbatim as
pinned in the Solution section above.

R4: The two fixed impact phrases are written into `.claude/skills/drain/reference.md`
verbatim as pinned above — `Blocks: promotion of this stub to a
dispatchable task` for the stub row, `Blocks: breakdown of this spec into
dispatchable tasks` for the NOT-READY-spec row — each appearing next to
its own row, not merged into one shared sentence.

R5: The repo's current `HUMAN.md` `## Agent-filed blockers` entry (the
`trajectory-evals` NOT-READY line, present as of this spec's authoring) is
rewritten to follow the new grammar, IF that entry is still present in
`HUMAN.md` when this work is implemented (if it has already resolved and
been removed, this requirement is satisfied vacuously — do not re-add a
resolved entry; if present but reworded by another session, retrofit
whatever text is actually found).

R6: `.claude/rules/human-blockers.md`'s "Rules" list gets one new bullet
stating the `Blocks:` clause is mandatory on every new entry filed after
this change — a filer that cannot determine impact writes "Blocks:
unclear — <one-line reason>" rather than omitting the clause.

R7: `antigravity/.agents/workflows/drain.md`'s mirrored "HUMAN.md filing
(R2)" section (~line 1162-1178) gets the same `Blocks:` derivation guidance
added, scoped to the five checklist-source rows that file's text already
enumerates: the mechanical `Depends on:` derivation citation for its three
`ask`/`run` rows ("deferred questions still unanswered", "`Unblock: ask:`
blocked tasks", "`Unblock: run:` blocked tasks"), and the two literal fixed
phrases from R4 for its two `decide` rows ("decision-shaped or
gate-refused stubs", "NOT-READY specs"). This mirrors CLAUDE.md's rule
that a spec touching `.claude/skills/*` content must carry the
`antigravity/` mirror update in the same spec (cited, not restated).

R8: `.claude-plugin/plugin.json`'s `"version"` is bumped past its value AT
IMPLEMENTATION TIME (0.9.17 as of this spec's authoring — re-check the
current value before implementing, since other concurrent work bumps it
independently; the requirement is "bumped from whatever it currently is,"
not "bumped from 0.9.17 specifically") per CLAUDE.md's "bump version in
plugin.json whenever skill behavior changes" rule, since R3/R4/R7 change
`/drain`'s HUMAN.md-filing behavior in both the `.claude/` source and its
`antigravity/` mirror.

## Out of scope

- Fixing the pre-existing mirror gap where `antigravity/.agents/workflows/drain.md`'s
  HUMAN.md-filing text already omits a `Contradicts-premise`-deferred row
  that `.claude/skills/drain/reference.md`'s table carries separately (five
  enumerated rows there vs. six in the source). That is a pre-existing
  content-parity gap unrelated to this spec's `Blocks:` change — R7 only
  adds `Blocks:` guidance to the rows the antigravity file already
  enumerates; it does not add the missing row.

- Building a mechanical linter/test that validates `HUMAN.md`'s grammar
  (none exists today for the file at all — confirmed no
  `tests/test_human_blockers*.sh` or equivalent). This spec only changes
  the authoring rule and drain's filing procedure; automated grammar
  enforcement is a separate future spec if wanted.
- Changing the six-row checklist-source-to-HUMAN.md-type mapping itself
  (`ask`/`run`/`provision`/`decide`) — only the entry's content grammar and
  filing procedure change, not the type-classification logic.
- Any skill besides `/drain` that might file into `HUMAN.md` in the future
  — scouting confirmed `/drain` is the only current filer. A future filer
  inherits the updated rule automatically since it's centralized in
  `.claude/rules/human-blockers.md`.
- Retrofitting entries in any repo other than this one.

## Acceptance criteria

- [ ] `grep -c 'Blocks: <impact>' .claude/rules/human-blockers.md` → 1 (R1's
      grammar-line token specifically — the literal placeholder appears only
      there, so this can't pass off R6's fallback text alone; absent today,
      verified via `grep -c` returning 0)
- [ ] `grep -n 'readable and actionable' .claude/rules/human-blockers.md`
      → at least one match (R2's plain-language rule specifically — this
      phrase does not appear in R1's grammar line, so it can't pass
      vacuously off R1 alone; absent today)
- [ ] `grep -c 'promotion of this stub to a dispatchable task' .claude/skills/drain/reference.md`
      → 1 (the stub-row fixed phrase, exact string; absent today)
- [ ] `grep -c 'breakdown of this spec into dispatchable tasks' .claude/skills/drain/reference.md`
      → 1 (the NOT-READY-spec-row fixed phrase, exact string; absent today
      — note `evals/lint-ultra-gate.sh` scope doesn't apply here, this is a
      plain string count)
- [ ] `grep -c 'unblocking-power' .claude/skills/drain/reference.md` → ≥ 1
      in the HUMAN.md filing (R2) section specifically (i.e. the four
      dependency-bearing rows reference the cited SKILL.md step 2
      computation by name, not just by accident elsewhere in the file —
      confirm the match's line number falls within the "HUMAN.md filing
      (R2)" section's line range, not `.claude/skills/drain/SKILL.md`'s own
      unrelated usage)
- [ ] If `HUMAN.md`'s `## Agent-filed blockers` section still contains an
      entry whose `<source path>` is `specs/trajectory-evals/critique-findings.md`
      at implementation time: that specific line contains `Blocks:` (e.g.
      `grep 'trajectory-evals/critique-findings.md' HUMAN.md | grep -c 'Blocks:'`
      → 1). If no such entry exists (already resolved and removed), this
      check is skipped, not failed — note which case applied in the task's
      evidence.
- [ ] `grep -c 'Blocks: unclear' .claude/rules/human-blockers.md` → ≥ 1
      (the R6 fallback grammar; absent today, verified via `grep -c`
      returning 0)
- [ ] `grep -c 'promotion of this stub to a dispatchable task' antigravity/.agents/workflows/drain.md`
      → 1, and `grep -c 'breakdown of this spec into dispatchable tasks' antigravity/.agents/workflows/drain.md`
      → 1 (R7's mirrored fixed phrases; both absent today)
- [ ] R8, version-agnostic: before editing, capture the current value with
      `grep -n '"version"' .claude-plugin/plugin.json`; after editing,
      `grep -c '"version"' .claude-plugin/plugin.json` → 1 (still exactly
      one version line) AND that line's value differs from the captured
      pre-edit value (confirms an actual bump happened, robust to
      concurrent version changes from unrelated work landing between spec
      authoring and implementation — do not hardcode a specific from/to
      version string in this check).
- [ ] End-to-end: a human reading `.claude/rules/human-blockers.md`'s
      updated grammar section, with no other context, can state in one
      sentence what a `Blocks:` clause on a hypothetical filed entry would
      mean — exercised by pasting the updated section to a fresh reader (or
      a fresh agent session with no other repo context) and confirming
      their one-sentence paraphrase names both the ask and its impact.

## Open questions

(none)
