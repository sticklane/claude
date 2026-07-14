# Task 01: Build the harness-audit skill

Status: in-progress
Depends on: none
Priority: P1
Budget: 30 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4)
Touch: .claude/skills/harness-audit/SKILL.md, .claude/skills/harness-audit/reference.md

## Goal

A new read-only skill, `.claude/skills/harness-audit/SKILL.md` (optionally
paired with a `reference.md` for detailed check commands per the repo's
"Reference files over 100 lines open with a table of contents" and "SKILL.md
bodies stay well under 500 lines" conventions), that audits an
already-onboarded repo's harness health and emits a ranked findings report.
Modeled structurally on `.claude/skills/qa-sweep/SKILL.md` and
`.claude/skills/gate/SKILL.md` (frontmatter -> execution-critical contract ->
numbered procedure, with heavy reference material split out).

## Touch

This task owns only the new skill's own files -- it does not touch
`.claude-plugin/plugin.json` or any `antigravity/` mirror (that's task 02,
which depends on this one). Do not edit any other skill's files.

## Steps

1. Write the skill frontmatter (name, description with concrete trigger
   phrases per CLAUDE.md's authoring conventions -- e.g. "audit this repo's
   harness", "check the harness", "harness health check", "is the harness
   drifted").
2. State the read-only contract explicitly and early (R1): no edits, no
   installs -- the skill only reads, executes read-only+allowlisted commands,
   and inspects (never executes) mutating commands.
3. Write the numbered procedure covering all five checklist areas from
   SPEC.md's Solution section, each producing either findings or an explicit
   "clean" line (R2):
   - Command currency -- mutation-class-scoped as SPEC.md's Solution item 1
     describes: execute only commands that are both read-only AND allowlisted
     (allowlist membership alone is insufficient); mutating commands are
     inspected only (existence + referenced-target validity), never executed.
   - Gate coverage -- if `.claude/settings.json` / Stop hook is installed,
     confirm the checks it references still exist and pass on a clean tree;
     if not installed, say so once (not per file).
   - Evalset presence -- skills changed since the last eval run, or with no
     evalset at all.
   - Memory hygiene -- `docs/memory.md` index entries resolve to files in
     `docs/memory/` and vice versa; stale-dated entries flagged.
   - Allowlist drift -- permission entries granted but unused in recent
     transcripts, and prompts that recur without an entry.
4. Write the ranking/synthesis step: blocking -> advisory, each finding names
   its file and a one-line fix (R3). State explicitly that a finding's next
   step is a normal task/spec, never an in-audit edit.
5. Write the dispatch-tier instruction (R4): mechanical checks (command
   execution, file-existence greps) are dispatched to scout-tier agents per
   `.claude/rules/token-discipline.md`'s "Dispatch authoring" section (cite,
   don't restate); only the final ranking/synthesis step runs on the session
   model. Follow the dispatch-authoring conventions for capped returns and
   tier selection.
6. Close with the standard `Next stage:` line per CLAUDE.md's authoring
   conventions -- a findings report has no fixed next skill (each finding
   routes to its own task/spec), so use the "genuinely a user action" form:
   `Next stage: none -- file findings as tasks/specs per normal pipeline`.

## Acceptance

- [ ] `grep -qi "read-only" .claude/skills/harness-audit/SKILL.md` (R1)
- [ ] `F=.claude/skills/harness-audit/SKILL.md; grep -qi "command currency" $F && grep -qi "gate coverage" $F && grep -qi "evalset" $F && grep -qi "memory hygiene" $F && grep -qi "allowlist" $F` (R2)
- [ ] `grep -qi "dispatch authoring\|scout-tier\|scout agent" .claude/skills/harness-audit/SKILL.md` (R4)
- [ ] Fresh-session manual test on this repo with one seeded defect (a fake
      stale command in a scratch copy of CLAUDE.md, outside the repo's
      tracked tree): invoking the skill reports it as a finding naming the
      file and a one-line fix, and `git status` is clean afterward (R1-R3).
      Manual per CLAUDE.md's testing convention -- record the transcript
      excerpt or a one-line evidence note in this task file.
