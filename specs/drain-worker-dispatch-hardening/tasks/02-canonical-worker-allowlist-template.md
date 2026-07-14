# Task 02: Canonical worker allowlist template

Status: in-progress
Depends on: 01
Priority: P2
Budget: 15 turns
Spec: ../SPEC.md (requirement R2)
Touch: runtimes/claude-code.md, .claude/skills/drain/reference.md, antigravity/.agents/workflows/drain.md

## Goal

One canonical, tool-complete WORKER allowlist template for compute-heavy
specs (`go`, `bash`, `npm`, `python3`, `git` at minimum) exists in
`runtimes/claude-code.md`'s `## Headless` section, and drain's Headless
fallback section references it by name instead of restating an allowlist
ad hoc.

## Touch

Depends on task 01 landing first: both tasks edit the same "Headless
fallback" section of `reference.md` (01 adds a pre-flight paragraph, this
task replaces the bare allowlist placeholder with a named reference) —
serialize to avoid stacking conflicting edits on the same lines. This
task's scope is the per-task WORKER allowlist only; the ORCHESTRATOR
allowlist (task 01's pre-flight next to the Relaunch command template,
reference.md:~1059-1085) is out of scope here.

Closure-time check (not this task's job, but flag it): the "canonical
worker allowlist" phrase this task ports into
`antigravity/.agents/workflows/drain.md` will reference a template that
lives only in `runtimes/claude-code.md` — a Claude-runtime-specific file
with no antigravity equivalent. Confirm at task 05's closing sweep (or
sooner, if you notice it here) that this reference resolves sensibly for
an antigravity reader rather than pointing at a file antigravity has no
reason to open; per `.claude/rules/mirror-verification.md` a phrase-grep
passing is not the same as the cross-reference actually resolving.

## Steps

1. Read `runtimes/claude-code.md`'s `## Headless` section (the file that
   already defines the `<allowlist>` placeholder shape used elsewhere).
2. Add a canonical, tool-complete WORKER allowlist template there for
   compute-heavy specs, covering at minimum `go`, `bash`, `npm`,
   `python3`, `git`, following the existing
   `Bash(<verified test/lint/build cmds>)` placeholder convention. Use the
   literal phrase "canonical worker allowlist" in this addition (the
   spec's acceptance criterion greps for it in both this file and
   reference.md).
3. In `.claude/skills/drain/reference.md`'s "Headless fallback" section
   (reference.md:~924's ad hoc `--allowedTools` placeholder), replace the
   restated allowlist with a reference to the new canonical template by
   name — also using the literal phrase "canonical worker allowlist".
4. Port the reference.md change into `antigravity/.agents/workflows/drain.md`'s
   corresponding Headless-fallback-equivalent section.
5. Commit.

## Acceptance

- [ ] `grep -c "canonical worker allowlist" runtimes/claude-code.md` → at least 1
- [ ] `grep -c "canonical worker allowlist" .claude/skills/drain/reference.md` → at least 1
- [ ] `grep -n "allowedTools" .claude/skills/drain/reference.md` (Headless fallback section) shows a reference to the named template, not a re-listed ad hoc tool string
- [ ] `grep -c "canonical worker allowlist" antigravity/.agents/workflows/drain.md` → at least 1
