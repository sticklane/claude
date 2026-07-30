# Human-filed blockers

Things only a human can do — a question to answer, a command to run, an
access to provision, a decision to make — go in the repo-root `HUMAN.md`
under a single machine-owned section so they survive the session that
found them. That section is `## Agent-filed blockers`. Any hand-written
narrative in the same file lives above it and is human-owned.

## Entry grammar

Each open blocker is one checkbox line under the section:

```
- [ ] <ISO date> · <source path> · <ask|run|provision|decide> — <plain-language action> — Blocks: <impact> — Still-blocked: <probe name> [arg …]
```

The type mirrors the `Unblock:` types so nothing new is invented: `ask` =
a question needing an answer; `run` = a command a human must run;
`provision` = credentials, access, or a purchase; `decide` = a
decision-shaped item (a stub or spec).

The `<plain-language action>` clause must be **readable and actionable
without opening the source file**: it is authored for a human skimming the
section, not copied verbatim from a deferred question, an `Unblock:` line, a
stub reason, or a critique finding. Expand jargon and task-ID shorthand into
what it actually means — say what task 09 _does_, don't just name it; name
the source file as a pointer, never as the explanation. The reader needs no
other context to act on it.

The `Blocks:` clause states what stays stuck while the item sits
unresolved, so a human scanning the section can tell the item's cost without
opening the source file and tracing `Depends on:` edges by hand. It names
the downstream work the entry gates — the blocked task names (e.g. "Blocks:
task 09 (notes CRUD), task 11 (MCP server)"), "Blocks: no other pending
task" when nothing depends on it, or the one fixed stage a source type
always gates (e.g. "Blocks: promotion of this stub to a dispatchable task").

The `Still-blocked:` clause is mandatory and is the final element of the
line, so an entry can be re-checked against the world instead of sitting
until someone re-reads it. It is the text following the **last** occurrence
of ` — Still-blocked: ` on the line, through end of line; the last
occurrence is the parse rule because the `<plain-language action>` prose
already contains ` — ` internally, so position alone cannot find it.

The clause names a probe script and its literal arguments — never a command
line. `<probe name>` matches `^[a-z0-9][a-z0-9-]*$` and resolves to
`scripts/blocker-probes/<name>` relative to the git root holding this
`HUMAN.md`, where it must exist as a regular executable file; a name that
does not resolve, or resolves to something not executable, is a violation.
Arguments are split with POSIX shell-word lexing and handed to the script as
argv, which is run directly with that git root as its cwd — never through a
shell, so `;` and `|` inside an argument are inert bytes reaching reviewed
code. An unbalanced quote or an ASCII control character is a violation. The
name `none` is reserved: `Still-blocked: none — <reason>` is the only legal
escape from naming a probe.

The probe's exit code is a three-value contract: **0 = still blocked**,
**3 = cannot determine**, any other nonzero = stale. Three exists so that
"I could not tell" cannot collapse into "the blocker dissolved" — a reader
of the section withholds stale entries, so mapping an unreachable checkout
onto stale would hide a live blocker. `bin/check-human-blockers` runs the
probes and sorts the section into still-blocked, stale, unknown, unprobed,
and violation.

## Rules

- **Open items only, not a log.** The section lists blockers still open.
  A resolved item is deleted, never checked-off-and-kept. (A human may
  tick `- [x]` to hand deletion to a later sweep; tools skip checked
  entries.)
- **File and resolve in the same commit.** The commit that resolves the
  source removes (or ticks) its entry; an agent that files a blocker and
  later clears it within one commit removes the entry rather than leaving
  a stale one.
- **Bootstrap on first file.** A repo with no `HUMAN.md` gets one created
  with a title line and the `## Agent-filed blockers` section — nothing
  else.
- **Section-scoped edits only.** Agents touch only inside
  `## Agent-filed blockers`. Prose above or below it is human-owned and
  never edited by an agent.
- **Append, don't reorder.** New entries append to the section; existing
  entries are not rewritten or reordered, only added or removed.
- **Adding a missing `Still-blocked:` clause is the one sanctioned
  rewrite.** It is the single exception to "append, don't reorder": an entry
  that predates the clause requirement, or that arrives by merge without
  one, is repaired in place rather than left as a permanent violation. The
  requirement is retroactive — every unchecked entry needs a clause,
  whenever it was filed — and `none — <reason>` is always available when no
  runnable signal exists.
- **`Blocks:` is mandatory.** Every entry filed after this change carries a
  `Blocks:` clause stating its impact; the clause is never omitted. A filer
  that cannot determine the impact writes `Blocks: unclear — <one-line
reason>` rather than dropping the clause.
