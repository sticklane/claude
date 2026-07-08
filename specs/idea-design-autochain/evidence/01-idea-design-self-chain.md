# Verification evidence: 01-idea-design-self-chain

Verdict: PASS (static prose-inspection scope only — live multi-turn /idea
run criteria explicitly excluded from this pass per caller instruction)

## Per-criterion results

1. New step exists between spec-write and /critique, gated on `## Open
   questions`, announce + Skill-tool invoke (R1) — PASS.
   `Read .claude/skills/idea/SKILL.md` shows new `## 4. Resolve open
   technology/architecture choices` inserted between `## 3. Write the spec`
   and `## 5. Adversarial pass`. Text: "does the spec's `## Open questions`
   section name a technology or architecture choice?" ... "Announce it in
   one line — ... then invoke the Skill tool for `design` with argument
   `specs/<slug>/SPEC.md`, blocking until it returns."

2. Same check re-runs after every /critique fix wave, single mechanism
   (R1b) — PASS. Step 4 preamble: "re-run the *identical* check after every
   `/critique` fix wave inside step 5's loop, not only once here. It is one
   file check re-evaluated at both points, never a separate judgment over
   critic findings." Step 5 also cross-references: "After each fix wave,
   re-run step 4's `## Open questions` design check before re-invoking
   `/critique`." No semantic-critic-read branch present.

3. R2 (ignore Next-stage line; resume correctly at both entry points) —
   PASS. Step 4.2: "**Ignore that line**... resume step 5: proceed to
   `/critique` if this was the post-step-3 check, or continue the fix loop
   (without restarting from step 3) if this was a mid-loop re-check."

4. Once-per-session cap + fallback on second occurrence (R5) — PASS. Step
   4.3: "**Once per session.** ... If `/design` has already run once this
   session and `## Open questions` names a technology/architecture choice
   again ... do NOT invoke `/design` a second time — take the
   printed-pointer fallback below."

5. R4 fallback stated for BOTH entry points — PASS. Step 4.4: "for the
   post-step-3 check, do not proceed to the first `/critique` invocation;
   for a mid-loop re-check, abort the fix loop rather than continuing it."

6. Hand-off step (now `## 6. Hand off`) has zero technology-choice /design
   references; non-technology fallback intact — PASS.
   Command: `awk '/^## 6\. Hand off/,/^## Ultra path/' .claude/skills/idea/SKILL.md | grep -in design`
   → no matches (exit 1).
   Diffed against base step 5 text (`git show 51cba13:.claude/skills/idea/SKILL.md`):
   base had "...or a technology/architecture choice is still open (run
   `/design specs/<slug>/SPEC.md` first; open /design choices stop the
   chain)." and a second closing line "— or, on the /design fallback,
   `Next stage: /design specs/<slug>/SPEC.md (human-launched)`." Both are
   absent from the new step 6. Retained: "the user asked for the spec
   only, or non-interactive doubt (answers you had to infer rather than
   get)" and the single `Next stage: /breakdown ...` close line.

7. plugin.json version bumped (R6) — PASS.
   Command: `git diff 51cba13 -- .claude-plugin/plugin.json`
   Output: `-  "version": "0.8.21",` / `+  "version": "0.8.22",`

8. Out-of-scope files untouched — PASS.
   `git diff 51cba13 -- antigravity/` → empty.
   `git diff 51cba13 -- antigravity/.agents/skills/idea/SKILL.md` → empty
   (explicit check per spec's antigravity acceptance criterion).
   `git diff 51cba13 -- .claude/skills/design/SKILL.md .claude/skills/critique/SKILL.md .claude/skills/breakdown/SKILL.md` → empty.

9. Task-file diff vs 51cba13 is append-only — PASS, with a process note.
   `git diff 51cba13 -- specs/idea-design-autochain/tasks/01-idea-design-self-chain.md`
   shows exactly one hunk: insertion of the `<!-- PLAN (build step 1): ...
   -->` comment block after the header fields. No edits to Goal / Steps /
   Touch / Budget / Acceptance text. This is within the allowed set
   (plan comment block).
   NOTE (finding, not a criterion failure): the diff contains no Status
   line flip, no ticked checkboxes, and no evidence-citation lines — the
   task file still reads `Status: in-progress` and all eight acceptance
   boxes remain `- [ ]` unchecked, even though the underlying SKILL.md and
   plugin.json edits are complete and (per this review) correct. The task
   file under-reports its own completion state.

## Gate / scope-creep check

Touch list is `.claude/skills/idea/SKILL.md, .claude-plugin/plugin.json`.
`git diff 51cba13 --stat` (full repo) confirms only those two files plus
the task file itself changed — no scope creep.

## Not exercised (explicitly out of scope for this pass per caller)

- Live `/idea` end-to-end run criteria (spec's last three acceptance
  bullets: transcript shows `design` Skill-tool invocation before
  `/critique`; resumes to `/critique` without surfacing /design's "Next
  stage" line; fixture where /design leaves Open questions non-empty stops
  before /critique; a no-open-choice run behaves unchanged). These require
  a live multi-turn agent session and were called out by the dispatcher as
  exercised separately.

## Commands run

```
git diff 51cba13 -- .claude-plugin/plugin.json
git diff 51cba13 -- antigravity/
git diff 51cba13 -- antigravity/.agents/skills/idea/SKILL.md
git diff 51cba13 -- .claude/skills/design/SKILL.md .claude/skills/critique/SKILL.md .claude/skills/breakdown/SKILL.md
git diff 51cba13 -- specs/idea-design-autochain/tasks/01-idea-design-self-chain.md
awk '/^## 6\. Hand off/,/^## Ultra path/' .claude/skills/idea/SKILL.md | grep -in design
grep -c '## Open questions' .claude/skills/idea/SKILL.md
git show 51cba13:.claude/skills/idea/SKILL.md   # for base-text comparison
```
