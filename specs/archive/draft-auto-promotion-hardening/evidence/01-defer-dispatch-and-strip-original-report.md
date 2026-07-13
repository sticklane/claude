# Verification: Task 01 — defer stub-intake promotions, strip Original report

Verdict: PASS (with one finding — uncommitted straggler edit, non-blocking)

Base commit for task-file diff: 5ec656e5f8792cffedb83c84eb24ec10faac5f87
Repo state checked: working tree at commit bd79be7 (`feat: defer stub-intake
promotions past authoring run; strip Original report at conversion`) plus one
uncommitted hunk in `antigravity/.agents/workflows/drain.md` (adds "(the
`git fetch` reconciliation)" clarifier). Both states were inspected.

## Per-criterion evidence

1. **Act step writes Promotion-ready:true + Promoted-by-run:<run-token>, not
   Status:pending flip, persists across re-entries/generations.** ✓
   `git diff $(git merge-base main HEAD)..HEAD -- .claude/skills/drain/reference.md`
   — lines ~981-991: "PASS → ... does **NOT** flip `draft` → `pending` in
   this run. Instead it leaves `Status: draft` and adds two committed header
   lines: `Promotion-ready: true` ... `Promoted-by-run: <run-token>` ...
   persist with the same durability as `Stub-intake-failed:` — across every
   step-1 re-entry ... and every baton generation of the authoring run."

2. **In-scope definition excludes Status:draft + Promotion-ready:true.** ✓
   reference.md diff lines ~930-938: "The in-scope set narrows to exclude an
   already-promoted stub: a `Status: draft` stub already carrying
   `Promotion-ready: true` ... is EXCLUDED from stub intake's scan from the
   moment of promotion onward."

3. **Owner-lease re-claim invariant (existing token, never fresh).** ✓
   reference.md diff lines ~51-59: "Re-claim invariant (the `Run-token:`
   never rotates within a run). Only a genuinely fresh launch — no baton to
   adopt — mints a new `Run-token:` ... Every OTHER path ... writes the
   session's EXISTING held `Run-token:` back unchanged."

4. **Step-1 conversion gated ONLY on Run-token mismatch (not baton
   presence), after remote-divergence check + owner-lease claim.** ✓
   reference.md diff lines ~279-297 (Promotion-ready conversion section):
   "convert only when THIS invocation's own `Run-token:` differs from the
   stub's `Promoted-by-run:` value. This discriminator is explicitly NOT
   `DRAIN-BATON.md` presence/absence" and "Ordering. ... runs AFTER the
   remote-divergence check and AFTER this invocation's owner-lease claim
   succeeds ... never before the lease claim."

5. **Same commit strips ## Original report; audit-trail-via-earlier-commit
   rationale stated explicitly.** ✓
   reference.md diff lines ~299-315: "Strip `## Original report` in the SAME
   commit. ... This must be the conversion commit, not a separate worktree
   edit: the dispatched worker's first action is `git reset --hard
   <default-branch>`, which discards any uncommitted worktree edit ... The
   audit trail is NOT lost: the original text remains fully inspectable via
   `git log`/`git show` on the EARLIER commit that wrote it."

6. **SKILL.md exit-checklist §5 excludes Promotion-ready drafts; only in §6,
   labeled distinctly; still a fixed seven-section checklist, numbers
   unchanged.** ✓
   `grep -n "seven-section" .claude/skills/drain/SKILL.md` → line 463: "the
   final message is a fixed seven-section checklist." Sections still
   numbered 1–7 (`grep -n "^[0-9]\. \*\*"` → 1 Deferred questions ... 7 Next
   commands, unchanged count). §5 text: "each `Status: draft` stub that does
   NOT carry `Promotion-ready: true` ... `Promotion-ready: true` drafts are
   EXCLUDED here ... they appear only in section 6." §6: "each stub marked
   `Promotion-ready: true` ... labeled addendum ... NOT 'awaiting your
   promotion.'"

7. **Two terminal readings updated so an all-Promotion-ready queue reads
   drained.** ✓
   reference.md diff lines ~217-231: "a draft carrying `Promotion-ready:
   true` is NOT awaiting a human ... So a queue whose only drafts ALL carry
   `Promotion-ready: true` ... reports as genuinely drained" and "Where every
   such `draft` dependency carries `Promotion-ready: true`, this is likewise
   genuinely drained."

8. **§6 "Promoted this run" includes literal `Demoted:` line text.** ✓
   SKILL.md diff: "print the exact `Demoted:` line a human would paste into
   that task file to reverse the promotion, e.g. `Demoted: <ISO-date> —
   <one-line reason>`."

9. **Fixture (a): gen1 PASS, baton to gen2 same run → still draft +
   Promotion-ready at gen2 step 1, not pending.** ✓ by construction: the
   re-claim invariant (criterion 3) states a baton pass preserves the
   session's existing `Run-token:`; the conversion procedure (criterion 4)
   converts only on a `Run-token:` mismatch. Since gen2's token == gen1's
   token == `Promoted-by-run:`, no conversion fires. reference.md explicitly
   states this: "a baton hop within the same run → same token ... → never
   converts" and "a stub promoted in generation 1 and carried into
   generation 2 by a baton pass is byte-identical at generation 2."

10. **Fixture (b): PASS at exhaustion trigger, same-generation re-entry via
    batch interview → still draft because re-entry's Run-token matches
    Promoted-by-run.** ✓ reference.md's conversion procedure explicitly
    enumerates "every one of its OWN step-1 re-entries (the deferred-answer
    loop, 3b's loop-back, critique intake's loop-back, the parked-liveness
    sweep) — all inside the SAME run ... with no baton and no human" and
    states re-entries never mint a new token (criterion 3), so Run-token
    still equals Promoted-by-run at re-entry → stays draft.

11. **`git diff $(git merge-base main HEAD)..HEAD -- antigravity/` shows
    drain.md changed, content-coverage: fetch, Promotion-ready,
    Promoted-by-run, Run-token-mismatch conversion, Original-report
    strip.** ~ PASS with a finding. Ran exactly:
    `git diff $(git merge-base main HEAD)..HEAD -- antigravity/`
    → 126 lines changed in `antigravity/.agents/workflows/drain.md`,
    covering Promotion-ready, Promoted-by-run, Run-token-mismatch-gated
    conversion (explicitly "not gated on DRAIN-BATON.md"), and the
    Original-report strip-in-same-commit language, in paraphrased voice
    mirroring reference.md. The literal word "fetch" is NOT present in this
    committed diff — the committed text uses "remote-divergence check" (the
    same term reference.md itself uses, which is itself never spelled out
    as "fetch" in its own diff either — "remote-divergence check" is the
    established term elsewhere in both files for the `git fetch <remote>`
    step). **Finding:** there is a one-line UNCOMMITTED edit in the working
    tree (`git diff -- antigravity/.agents/workflows/drain.md`, 5 lines)
    that inserts "(the `git fetch` reconciliation)" right at this spot —
    apparently added to close this exact literal-token gap — but it has not
    been committed, so the criterion's literal command (against HEAD) does
    not yet show the word "fetch." The semantic content (remote-divergence
    check, ordering after it) is present either way. This is a commit-
    discipline gap (uncommitted work), not a missing-content gap.

12. **plugin.json version increased.** ✓
    `git diff $(git merge-base main HEAD)..HEAD -- .claude-plugin/plugin.json | grep '"version"'`
    → `-  "version": "0.8.30", / +  "version": "0.8.31",`.

13. **docs/human-gates.md diff empty.** ✓
    `git diff $(git merge-base main HEAD)..HEAD -- docs/human-gates.md` →
    empty output.

14. **screen-stub.sh diff empty.** ✓
    `git diff $(git merge-base main HEAD)..HEAD -- .claude/skills/drain/screen-stub.sh`
    → empty output.

15. **Task-file append-only check.** ✓
    `git diff $(git merge-base main HEAD)..HEAD -- specs/draft-auto-promotion-hardening/tasks/`
    → touches only `01-defer-dispatch-and-strip-original-report.md`, and the
    only change is the addition of the `<!-- PLAN (delete at close-out): ...
    -->` comment block (an allowed plan-comment addition) immediately after
    the `Touch:` header. `Status:` line is unchanged (still `in-progress`),
    no acceptance checkboxes ticked, no evidence-citation lines added yet
    (this file is being generated as the evidence artifact now), no other
    task files touched, and no Goal/Steps/Touch/Acceptance text altered.

## Internal-contradiction sweep

`grep -n "flip.*draft.*pending\|promotes.*draft.*pending"` across
reference.md, SKILL.md, antigravity/drain.md found two remaining "promotes
... draft → pending" high-level summary lines (reference.md:914,
antigravity/drain.md:593) in the critique-intake overview paragraph
pointing forward to "stub intake (next section)". Read in context, neither
asserts in-run timing — they're the permitted one-line pointer describing
stub intake as the overall promotion path (task instructions explicitly
allow this). No contradiction found asserting an in-authoring-run flip.

## Gates

`bash evals/lint-ultra-gate.sh` → `lint-ultra-gate: OK — all ultra mentions
gated in 4 files` (drain.md/SKILL.md/reference.md/antigravity mirror are
"ultra-path" gated files; check passes).

## Scope-creep check

`git diff --stat $(git merge-base main HEAD)..HEAD` (excluding the task-file
plan-comment addition) touches exactly the four Touch-listed files:
`.claude-plugin/plugin.json`, `.claude/skills/drain/SKILL.md`,
`.claude/skills/drain/reference.md`, `antigravity/.agents/workflows/drain.md`.
No files outside Touch were modified. No version bumps beyond plugin.json,
no unrelated formatting sweeps observed in the diffs reviewed.

## Overall

14/15 criteria unambiguously verified via exact evidence. Criterion 11
(antigravity content-coverage) is satisfied on a reasonable reading of
"content coverage" (the remote-divergence-check concept and its ordering
are present, matching reference.md's own vocabulary), but the literal token
"fetch" only exists in an UNCOMMITTED edit — the implementer left one hunk
uncommitted, which is a commit-discipline issue (CLAUDE.md: "never leave
finished work uncommitted") rather than a missing-content issue. Since
Status is still `in-progress`, this looks like a legitimate to-be-finished
state, not a shipped-and-claimed-done state. Recommend: commit the pending
`antigravity/.agents/workflows/drain.md` hunk before flipping Status to
done/complete.
