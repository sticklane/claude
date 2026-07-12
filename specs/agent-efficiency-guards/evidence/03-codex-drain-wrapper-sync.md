# Verification: 03-codex-drain-wrapper-sync

Verdict: PASS

## Scope / diff check

`git diff main --numstat` (base commit 43191b2c):
```
26	1	codex/.agents/skills/drain/SKILL.md
```
Only file touched matches the task's `Touch:` list exactly. No plugin
manifest, `.claude/`, or `antigravity/` files changed.

`git status --short`: ` M codex/.agents/skills/drain/SKILL.md` — no untracked
files, no stray edits.

Append-only task-file check: `git diff 43191b2cc099e52ffa0e8afafd56c613e1854359 -- '*/tasks/*.md'`
→ empty output. No task file (this task's or any other's) was modified —
zero drift, nothing to flag as a violation of the append-only contract
(worker did not tick the checkbox or add evidence-citation lines, which is
conservative, not a foul).

## Criterion 1 — anchor greps

Command:
```
grep -qi 'load only the named section' codex/.agents/skills/drain/SKILL.md && \
grep -qi 'bare single command' codex/.agents/skills/drain/SKILL.md && \
grep -qi 'once per edit round' codex/.agents/skills/drain/SKILL.md && \
grep -qi 'under your worktree root' codex/.agents/skills/drain/SKILL.md
```
Result: all four grep -qi checks succeeded; combined AND chain printed
`ALL HIT`.

Verdict: PASS

## Criterion 2 — MANUAL: run/tab-naming step, Codex-adapted

Read `codex/.agents/skills/drain/SKILL.md` lines 52-59 (new "Name the run
(gen 1, best-effort)" paragraph) and compared against source
`.claude/skills/drain/SKILL.md` lines 52-57 ("Name the shell (gen 1,
best-effort)").

Source: sets terminal tab title via ANSI escape sequence to
`<repo> · drain: <slugs>`, once, never re-set on baton generations, skip
silently with no TTY.

Wrapper: labels the run via "Codex's Agent Manager naming surface" (the
Codex-native equivalent of a terminal-tab title in the Agent Manager UI) or,
in a `codex exec`/TUI shell that owns a TTY, falls back to the same ANSI
tab-title escape sequence — same naming scheme (`repo · drain: <slugs>`),
same "once, never re-set on baton generations" rule, same silent-skip
fallback. This is a genuine content-equivalent, correctly Codex-adapted (adds
the Agent Manager surface that has no Claude Code counterpart, rather than
blindly copying the TTY-only mechanism).

Verdict: PASS (manual judgment)

## Criterion 3 — plugin validate

Command: `claude plugin validate .`
Output:
```
Validating marketplace manifest: .../.claude-plugin/marketplace.json
✔ Validation passed
```
Exit code 0.

Verdict: PASS

## Content-equivalence judgment (Goal)

Compared wrapper diff against source `.claude/skills/drain/SKILL.md` and
`reference.md`'s Worker-prompt guard blockquote (lines ~467-512 of
reference.md).

- **Placement**: the three worker-dispatch guards ("under your worktree
  root", "bare single command", "once per edit round") are inserted
  immediately after "Launch ONE worker agent ... Await it and collect its
  verdict — never fire-and-forget" (SKILL.md lines 148-163) — i.e. exactly
  where the wrapper embeds worker-dispatch guidance, matching the source's
  placement of the same rules inside the worker-prompt blockquote in
  reference.md.
- **Content**: each guard is a faithful paraphrase, not a bare anchor drop:
  - worktree root: "every path you Read/Edit/Write must be under your
    worktree root (your shell's initial $PWD) — the main-checkout path is
    handed to you only for copying gitignored files in, and editing it
    errors and wastes a turn" — matches reference.md's "Every path you
    Read/Edit/Write must be under your worktree root ... never edit a
    main-checkout path from inside the worktree, since editing it errors
    and wastes a turn."
  - bare single command: "on a Bash permission denial, retry ONCE as a bare
    single command (no chaining, pipe, or redirection tricks) and, if still
    denied, stop and report the blocked command rather than iterating syntax
    variants" — matches reference.md's Bash-denial retry rule verbatim in
    substance.
  - once per edit round: "read a file at most once per edit round — after
    your own successful Edit/Write the harness confirms the new state, so
    never re-read to verify, re-reading only the region another writer
    changed" — matches reference.md's "Read a file at most once per edit
    round: after your own successful Edit/Write the harness confirms the new
    state ... re-read only the region another writer changed."
- **Section-lookup pointer**: "load only the named section" instruction
  (SKILL.md lines 136-140) is a genuine section-lookup pointer — "consult
  the longer shared drain doctrine (docs/human-gates.md, the antigravity
  reference this Codex leg overlays): load only the named section — locate
  its heading with a `grep -n` and read that slice, not the whole file" —
  mirrors the source's identical instruction pattern used three times in
  `.claude/skills/drain/SKILL.md` (e.g. lines 90-92, 146-148, 403-405).

No anchor was dropped in an unrelated location; all four anchors sit inside
genuinely Codex-adapted, content-equivalent paraphrases at structurally
matching positions.

## Gates

No repo-wide `scripts/check.sh` applies to `.claude`-toolkit-repo prose
changes (per CLAUDE.md, "~/claude has no scripts/check.sh gate" convention);
`claude plugin validate .` is the closest applicable gate and passed (see
Criterion 3).

## Scope-creep check

`git diff main --numstat` shows exactly one file changed, matching Touch.
No version bump, no plugin.json edit, no antigravity/ mirror edit — correctly
scoped since `codex/.agents/skills/{drain,build,autopilot,evals}/SKILL.md`
are real content (not symlinks) and this task's Touch list names only the
drain wrapper.

## Overall verdict: PASS

All three acceptance criteria pass; content-equivalence to the source's
reference.md Worker-prompt guard rules and SKILL.md section-lookup/naming
steps is genuine (Codex-adapted paraphrase, correctly placed), not a
keyword-stuffing pass. Diff is scoped to exactly the Touch list. No
task-file drift.
