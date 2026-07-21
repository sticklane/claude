# Task 03: Mirror the trigger fix into antigravity + bump plugin.json

Status: in-progress
Depends on: 01
Priority: P2
Budget: 18 turns
Spec: ../SPEC.md (requirements R4, R5)
Touch: antigravity/.agents/workflows/drain.md, .claude-plugin/plugin.json

## Goal

`antigravity/.agents/workflows/drain.md`'s mirrored "Name the run" section
gets the same re-scoped trigger task 01 wrote for
`.claude/skills/drain/reference.md`, adapted to that file's own phrasing —
covering the WHOLE section (header, opening, closing), not just the
closing clause, since this mirror (unlike the source) bakes gen-1 framing
into each advisory's own self-contained block rather than a shared
umbrella paragraph. `.claude-plugin/plugin.json`'s `"version"` is bumped,
since this spec changes `/drain`'s behavior in both the `.claude/` source
and its `antigravity/` mirror.

## Touch

Only `antigravity/.agents/workflows/drain.md` and
`.claude-plugin/plugin.json`. Do not touch
`.claude/skills/drain/reference.md` (already landed by task 01 — read it,
don't edit it) or `.claude/skills/drain/SKILL.md` (task 02).

## Steps

1. Read task 01's landed wording in `.claude/skills/drain/reference.md`'s
   "Name the shell" section (this task depends on 01).
2. In `antigravity/.agents/workflows/drain.md`'s "Name the run (gen 1,
   best-effort)" section (~line 42-49), edit all three parts together so
   the section doesn't end up self-contradictory (per SPEC.md's R4):
   - Header: `**Name the run (gen 1, best-effort).**` — drop or requalify
     the "(gen 1, ...)" tag.
   - Opening: `At gen-1 startup, if the run/tab has no custom name
already, name it...` — replace with the re-scoped trigger: fires once
     per session, the first time this run reaches step 1, regardless of
     the adopted **owner lease's** `Generation:` number (same "owner
     lease's Generation" phrasing as task 01's reference.md wording), since
     a resumed run's own tab has never yet been named.
   - Closing: `skip silently where none exists, and never re-name on baton
generations.` — replace with: skip if already named this run, or if
     no naming surface exists (a headless baton self-relaunch or an
     awaited subagent spawn has neither).
     Do not touch the "Startup session sweep" or "Hub-economics" sections
     immediately after/before it — their own gen-1-only framing is
     unchanged (out of scope per SPEC.md).
3. Before editing `.claude-plugin/plugin.json`, capture its current
   `"version"` value. Bump the version (increment the patch component) so
   the file's `"version"` value differs from its pre-task value.

## Acceptance

- [x] `grep -c "regardless of the adopted owner lease's" antigravity/.agents/workflows/drain.md` → ≥ 1
      — evidence: returns 1 (edited opening line 51).
- [x] `grep -c 'never re-name' antigravity/.agents/workflows/drain.md` → 0
      (anchored on this single-line substring since the full old phrase is
      line-wrapped in the file; returns 1 today)
      — evidence: returns 0 (old "never re-name on baton generations"
      closing replaced by the naming-surface-existence criterion).
- [x] `sed -n '/\*\*Name the run/,/\*\*Startup session sweep/p' antigravity/.agents/workflows/drain.md | grep -c 'gen-1 startup'`
      → 0 (section-scoped so it doesn't touch the unrelated "Startup
      session sweep"/"Hub-economics" advisories; returns 1 today — the
      section's own opening must no longer assert unqualified gen-1-only)
      — evidence: returns 0 (opening no longer says "At gen-1 startup";
      the "Hub-economics advisory (gen 1, ...)" section is untouched and
      out of section scope).
- [x] `grep -c 'Name the run (gen 1, best-effort)' antigravity/.agents/workflows/drain.md`
      → 0 (returns 1 today — the header's "(gen 1, ...)" tag must be
      dropped or requalified, part of the same contradiction as the prior
      check)
      — evidence: returns 0 (header now `**Name the run (best-effort).**`).
- [x] `grep -c '"version"' .claude-plugin/plugin.json` → 1 (still exactly
      one version field), AND its value differs from the value at this
      task's own base commit: `git show $(git merge-base main HEAD):.claude-plugin/plugin.json | grep '"version"'`
      compared against the current file's `"version"` line — they must not
      match. Do not hard-code a specific from/to version string; compare
      against your own branch's base commit so a sibling task's concurrent
      bump never false-fails this check.
      — evidence: exactly one `"version"` field; base commit (merge-base
      4b01bae) = `0.9.24`, current = `0.9.26` — differ. Pre-task working
      value was `0.9.25` (task 02's bump); patch-incremented to `0.9.26`.
- [x] End-to-end (semantic, not just phrase-presence — a fresh reader with
      no other context than the updated "Name the run" section can
      correctly classify): (a) "a human resumes a stalled run in a new
      terminal, adopting an existing owner lease at `Generation: 3`" →
      proposes a name; (b) "drain's own baton mechanism self-relaunches a
      successor generation with no naming surface available" → does not
      propose. Record both classifications as evidence.
      — evidence: (a) PROPOSES — the section fires "once per session, the
      first time this run reaches step 1, regardless of the adopted owner
      lease's `Generation:` number"; the new terminal is unnamed and has a
      naming surface, and the parenthetical names the `Generation: 3`
      resume case explicitly ("still proposes on its first pass"). (b) DOES
      NOT PROPOSE — closing says "Skip ... if no naming surface exists — a
      headless baton self-relaunch ... has neither." The section is no
      longer self-contradictory: the header/opening/closing all now gate on
      surface-existence + not-yet-named, never on generation number.
