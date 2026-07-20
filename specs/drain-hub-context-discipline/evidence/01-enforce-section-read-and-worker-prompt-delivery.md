# Verification: task 01 enforce-section-read-and-worker-prompt-delivery

Verdict: PASS

Branch: task/01-enforce-section-read-and-worker-prompt-delivery
Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a022de8e15f15284d
Base for task-file diff: 51aae98
Implementation commit: c33824c (HEAD)

## Per-criterion results

1. `grep -c "Grep-then-offset" .claude/skills/drain/reference.md`
   Output: `2` → PASS (≥1)

2. `grep -c "path-pointer" .claude/skills/drain/reference.md`
   Output: `3` → PASS (≥1)

3. Manual prose read of SKILL.md's "load only the named section" call sites.
   `grep -n "load only the named" .claude/skills/drain/SKILL.md` shows 5
   direct hits (lines wrap, so a single-line "load only the named section"
   grep undercounts); cross-checked against `grep -n "Grep-then-offset"
.claude/skills/drain/SKILL.md` which shows 7 hits (lines 55, 77, 125,
   300, 354, 406, 458) — matching the plan's "7 sites" claim. Diffing
   51aae98..c33824c confirms all 7 pre-existing "load only the named
   section" pointers (Gen-1 startup advisories; Remote divergence check;
   Worker prompt and Status field semantics — rewritten below; Baton pass;
   Stub intake; Spec-completion review worker; Exit checklist) now end with
   ", Grep-then-offset)" or "(Grep-then-offset)" immediately adjacent to the
   pointer, naming the new reference.md procedure rather than only
   repeating the passive note. The 4th site (SKILL.md line ~164, step-2
   dispatch) was rewritten more substantially: it no longer uses the "load
   only the named section" phrase at all, replaced with explicit
   path-pointer delivery language ("delivering the Worker prompt section in
   reference.md by path-pointer — resolve it to a concrete reference.md
   path the worker reads and follows verbatim, never pasting its body into
   the dispatch call"), which satisfies acceptance criterion 3's intent (and
   task Step 4) even more directly than a citation would.

   reference.md's new procedure block (added right after the existing
   "Loaded on demand" paragraph, before "## Drain-readiness gate", i.e. near
   the TOC) reads:
   "**Grep-then-offset reads (do this before every reference.md read).**
   ... First `Grep -n '^## '` reference.md to list its section headers,
   locate the target section's start line and the next header's line, then
   `Read` with `offset`/`limit` bounded to that range — the Grep-then-offset
   procedure. SKILL.md's "load only the named section" pointers each name a
   section here and invoke exactly this procedure; they cite it rather than
   restating it."
   This defines Grep-headers → offset/limit Read as required. PASS
   (verified directly, not manual-pending, since I am not an unattended
   worker in this verification context).

4. `bash evals/lint-ultra-gate.sh`
   Output: `lint-ultra-gate: OK — all ultra mentions gated in 4 files`
   Exit code: 0 → PASS

5. `bash evals/lint-skill-size-gate.sh`
   Output: `lint-skill-size-gate: OK — all skill docs within size/TOC
conventions`
   Exit code: 0 → PASS
   `wc -l < .claude/skills/drain/SKILL.md` → `498` → PASS (≤500)

6. `wc -l < .claude/skills/drain/reference.md` → `1866` (recorded, no
   ceiling per criterion).

## Diff scope check

`git diff 51aae98 -- .` touches exactly three files:

- `.claude/skills/drain/SKILL.md` (in Touch list)
- `.claude/skills/drain/reference.md` (in Touch list)
- `specs/drain-hub-context-discipline/tasks/01-enforce-section-read-and-worker-prompt-delivery.md`
  (the task file itself, currently uncommitted in the working tree — the
  implementation commit c33824c itself touched only the two Touch-listed
  files, per `git show --stat c33824c`).

No mirror files (`antigravity/…`, `codex/…`) or
`tests/mirror-procedure-manifest.txt` were touched — consistent with the
task's Touch/scope note deferring those to task 02.

## Append-only task-file check

`git diff 51aae98 -- specs/.../01-enforce-section-read-and-worker-prompt-delivery.md`
(working tree, uncommitted) shows two hunks:

1. Addition of the `<!-- PLAN (build step 1 — delete at close-out): ... -->`
   comment block, immediately above `## Goal` — an allowed plan-comment-block
   addition.
2. A **whitespace-only** change to one acceptance-criterion line: the
   continuation line
   `  .claude/skills/drain/SKILL.md\`) now cite the new reference.md`had its leading 2-space indent removed, becoming`.claude/skills/drain/SKILL.md\`) now cite the new reference.md`.
   This is inside criterion 3's read-only acceptance-criterion text. It is a
   pure Markdown line-continuation indentation change (no wording/meaning
   change — same criterion, same commands, same rendered text) but is,
   strictly, an edit to text that CLAUDE.md's append-only-for-workers rule
   marks read-only ("The text of ... every acceptance criterion is
   read-only to workers"). Flagging as a minor process finding — not
   grounds for FAIL since it does not alter content or intent, but it is a
   literal touch of criterion text outside the allowed
   Status/checkbox/evidence/plan-comment set.

No other lines were changed: Status line remains `in-progress` (as
expected, pre-close-out), acceptance checkboxes remain unticked (expected
per verifier instructions), Goal/Steps/Touch/Budget bodies are untouched.

## Scope creep

None found in the two implementation files beyond what Steps 1-4 called
for. Both additions in reference.md land in their specified locations
(near TOC / "Loaded on demand" note; and in "## Worker prompt", just above
its body). SKILL.md's 7 citation edits are minimal, in-place phrase
additions; the step-2 dispatch rewrite (line ~164-172) matches Step 4's
"make the ... pointer explicitly path-pointer delivery, not inlined"
instruction. Net diff is small (+30/-9 across two files) and matches the
task's stated plan exactly.

## Gates

- `bash evals/lint-ultra-gate.sh` → exit 0 (criterion 4, see above).
- `bash evals/lint-skill-size-gate.sh` → exit 0 (criterion 5, see above).

## Overall verdict: PASS

All six acceptance criteria are satisfied, diff scope is limited to the two
Touch-listed files (plus an allowed plan-comment addition to the task file),
and both gates pass. One minor finding: a whitespace-only edit crept into
acceptance-criterion text in the task file (see Append-only section above) —
does not change meaning/commands, but is technically outside the
worker-allowed-edit set; call it out to the closing task/human rather than
treat it as blocking.
