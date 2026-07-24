# Task 05: Update doctrine and reference docs to describe the bd-native handoff mechanism

Status: pending
Depends on: none
Priority: P2
Budget: 25 turns
Spec: ../SPEC.md (requirement R8)
Touch: .claude/rules/token-discipline.md, docs/guides/context-management.md, AGENTS.md, docs/external-playbooks.md

## Goal

Every doc that currently describes `/handoff` as writing a markdown file
now describes the bd-native mechanism instead, without disturbing
unrelated content — `docs/external-playbooks.md`'s cited primary-source
quotes are never edited, only its own reconciliation prose.

## Steps

1. `.claude/rules/token-discipline.md`: reword "write a handoff file and
   restart from it" (line ~264) and any other literal "handoff file"
   phrasing (Session hygiene / Session refresh sections, 3 mentions
   total, case-insensitive) to describe parking state via `/handoff`
   without naming a file format.
2. `docs/guides/context-management.md`: its "## Handoff artifacts and
   session hygiene" section (lines ~67-77) currently reads "`/handoff`
   writes a self-contained handoff file" and "writes the resumable
   handoff artifact" — reword both to describe the bd-native mechanism
   (park state via `bd comment`/a `handoff`-labeled bd issue).
3. `AGENTS.md`: line ~31 currently reads "In-flight session handoffs land
   as `HANDOFF.md` next to the active task/spec file ... each carrying a
   `Tracked:` header naming the bd issue(s) for the parked work" — the
   `Tracked:`-header concept retires entirely once there's no file to put
   a header on; reword to describe the bd-native detection (an open
   `handoff`-labeled bd issue). Check the other 2 case-insensitive
   "handoff" mentions in this file too.
4. `docs/external-playbooks.md`'s "## Handoffs" section (lines 548-610):
   this is a `/factcheck`-cited section quoting external primary sources
   verbatim (URLs and quoted text) — **never edit a quote or its citation**.
   Only reword the three "→" reconciliation lines that assert a HANDOFF
   file exists: ~line 565 ("the HANDOFF file never carries state the
   tracker doesn't"), ~line 577 ("the HANDOFF file is this repo's
   structured note, not its queue"), and ~line 608 ("Don't reach for a
   handoff file when `--resume` or compaction suffices" — reword to
   reference "the `/handoff` skill" instead of "a handoff file"). Each
   reword should still make sense as a reconciliation of the quote it
   follows — read the full bullet before rewording, not just the flagged
   clause.

## Acceptance

- [ ] `grep -ci "handoff file\|HANDOFF\.md" .claude/rules/token-discipline.md AGENTS.md docs/external-playbooks.md` → 0 in each
- [ ] `awk '/^## Handoff artifacts/,/^## [^H]/' docs/guides/context-management.md | grep -c "bd comment\|bd issue\|bd list --label handoff"` → ≥ 1
- [ ] `grep -c "https://" docs/external-playbooks.md` → unchanged from the value at this task's base commit (confirms no quote/citation URL was touched — compare via `git show <base-commit>:docs/external-playbooks.md | grep -c "https://"`)
