# Task 02: `workboard.py` per-runtime baton parsing

Status: in-progress
Depends on: 01
Priority: P1
Budget: 40 turns
Spec: ../SPEC.md (requirements R3, R4, R5, R9, R10, R11)
Touch: .claude/skills/workboard/workboard.py, .claude/skills/workboard/test_workboard.py, runtimes/fake-runtime.md

## Goal

`workboard.py` replaces its single hardcoded `BATON_CMD_RE`
(`re.compile(r'claude\s+-p\s+"[^"]*"')`, line ~557) with a per-runtime regex
table built from `runtimes/*.md` via `runtimes/parse_headless.py` (task 01).
Scanning a repo's `DRAIN-BATON.md`, it resolves that repo's active runtime
(reading its `.claude/runtime.md`, defaulting to `claude-code`), tries that
runtime's regex first, then falls back through the other known runtimes'
regexes. A `gemini -p`-shaped baton now extracts correctly instead of
producing an empty `command`. A runtime with no fenced Headless template
(Antigravity) sets a `manual_relaunch` field instead of leaving `command`
silently `""`, and the HTML rendering (~line 1569) shows that phrase. A
baton matching no known shape at all sets a `parse_warning` field that
plugs into the existing needs-attention inbox mechanism (`attention_items()`
~line 987, promoted to inbox ~lines 1177-1188) instead of vanishing
silently. Per `docs/memory/workboard-mirror-verbatim.md`, this task's
`workboard.py`/`test_workboard.py` changes must be mirrored byte-identical
to `antigravity/.agents/skills/workboard/` and the plugin version bumped —
but that mirror sync and bump are deliberately **not** done in this task
(see task 05): task 03 also changes a `.claude/skills/` file
(`drain/reference.md`) and runs concurrently with this task, so bumping
`plugin.json` here would either race task 03's own skills change or force
task 03 to touch a file outside its `Touch:` list. Task 05 depends on both
02 and 03 and owns the single closing mirror-sync + version-bump commit.

## Touch

Do not touch `.claude/skills/drain/reference.md` or `evals/run.sh` — those
are tasks 03 and 04, disjoint files. Do not touch `runtimes/parse_headless.py`
itself (task 01) — import and call it. Do not touch
`antigravity/.agents/skills/workboard/` or `.claude-plugin/plugin.json` —
those belong to task 05, which runs after this task and task 03 both land.
`antigravity/.agents/workflows/drain.md` is out of scope entirely: per scout
research, Antigravity's baton relaunch section is a deliberately divergent
paraphrase (Antigravity has no self-relaunch capability), not a mirror of
`reference.md`'s content.

## Steps

1. Write failing tests first in `test_workboard.py`:
   - A `DRAIN-BATON.md` fixture containing a `gemini -p "..."`-shaped
     relaunch command, repo's `.claude/runtime.md` naming `gemini-cli` →
     `command` is extracted correctly (not empty).
   - A fixture for a repo on the `antigravity` runtime (no fenced Headless
     template) → `manual_relaunch` field is set (not a blank `command`).
   - A fixture whose relaunch command matches no known runtime's shape at
     all → `command` stays `""`, but `parse_warning` is set, and it surfaces
     via `attention_items()` / the needs-attention inbox.
   - A fixture whose repo's `.claude/runtime.md` names a runtime with no
     matching `runtimes/<name>.md` file → falls back to `claude-code`'s
     regex, no exception raised (R11).
   - Run these, confirm they fail (current code doesn't have this logic).
2. Implement the per-runtime regex table: for each `runtimes/*.md` file,
   call `runtimes/parse_headless.py`'s functions to get the joined template
   and derived regex; skip runtimes where the template is `NONE` (no regex
   to build, but keep the runtime name known as "manual relaunch only").
3. Add a helper to resolve a scanned repo's active runtime name from its
   `.claude/runtime.md` (default `claude-code` if absent), matching drain's
   existing resolution rule (see `.claude/skills/drain/reference.md:704-708`,
   read-only reference for this task — don't edit that file here).
4. Replace the `BATON_CMD_RE.search` call (~line 583) with: try the
   resolved runtime's regex first, then the other runtimes' regexes in some
   stable order; on total miss, set `parse_warning` instead of leaving bare
   `""`. When the resolved runtime's template is `NONE`, skip regex
   matching entirely and set `manual_relaunch` (e.g. `"No scriptable
   relaunch for <runtime> — reopen from <runtime>'s Agent Manager"") instead
   of attempting a match.
5. Update the HTML rendering (~line 1569 and the `needs_attention`
   extraction/promotion path ~lines 589-591, 987, 1177-1188) to show
   `manual_relaunch` text when present, and to promote a set
   `parse_warning` into the needs-attention inbox the same way
   `needs_attention` is promoted today.
6. Run tests, confirm green.
7. End-to-end demonstration of R9/R10: add `runtimes/fake-runtime.md` to
   this checkout with a conforming `## Headless` section using a distinct
   invocation shape (e.g. `fakecli run "<prompt>"`). Add one more test that
   builds a scratch repo (tempdir) whose `.claude/runtime.md` names
   `fake-runtime` and whose `DRAIN-BATON.md` contains a `fakecli run
   "..."`-shaped command, and asserts `workboard.py` extracts it correctly
   — with zero changes needed to `workboard.py` itself beyond what this
   task already wrote (i.e., this last test only adds the fixture + test,
   touching no additional parsing logic).

Do not mirror this task's changes to `antigravity/.agents/skills/workboard/`
or bump `.claude-plugin/plugin.json` — task 05 does both, once, after this
task and task 03 have both landed.

## Acceptance

- [ ] `python3 -m unittest discover -s .claude/skills/workboard` → all
      tests pass, including the new gemini-cli, antigravity,
      unrecognized-shape, unresolvable-runtime, and fake-runtime cases
