# Verification: Task 01 — drain-skill-text

Verdict: **PASS**

## Per-criterion

1. Dual trigger as one rule (SKILL.md baton section) — PASS
   `grep -qiE 'context.{0,40}(budget|heavy|trigger)' .../SKILL.md` → exit 0.
   SKILL.md:342-353 states the trigger literally as: `max(2, 6 − W)` recorded
   verdicts, "whichever comes first with the ~4-verdict boundary", explains
   this is a "deterministic, size-adaptive stand-in for the one-rule ideal
   'after ~4 verdicts OR when the hub's context is heavy, whichever comes
   first'", and records the chosen heaviness signal + why: "the harness
   exposes no reliable in-session context-size signal the hub can check, so
   a wider window W ... batons sooner". Matches PLAN step 4 exactly.

2. reference.md 2k cap attached to worker final-message/verdict contract,
   not satisfiable by pre-existing assessor line — PASS
   `grep -qiE 'final message.{0,120}2k tokens|verdict.{0,120}2k tokens|2k tokens.{0,120}(final message|verdict)' .../reference.md` → exit 0.
   Match location confirmed via `grep -noE ...`: only line 522 ("final
   message must be only (and capped at ≤ 2k tokens ..."). The pre-existing
   assessor line (965: "capped return 1–2k tokens") does not contain
   "verdict" or "final message" on the same line, so it cannot satisfy this
   line-based grep — confirmed by direct match-location check, not just
   inference.

3. SKILL.md names the same 2k cap — PASS
   `grep -qiE '2k tokens' .../SKILL.md` → exit 0. SKILL.md:107-108: "returning
   only a structured **verdict + evidence** capped at ≤ 2k tokens, never its
   transcript ... The cap is enforced in the worker prompt itself
   (reference.md's final-message contract)".

4. Wake-economics paragraph (cost model, 1.25, TTL) — PASS
   `grep -q '1\.25' ... && grep -qiE 'TTL' ...` → exit 0. SKILL.md:130-141
   contains the paragraph: 5-minute cache TTL, "re-caches the whole hub
   context at the 1.25× cache-write input rate", cost model
   `context_tokens × input_rate × 1.25`, "median rewrite 187k tokens, 268
   TTL-expiry wakes costing $587 in one week" citing ../EVIDENCE.md.

5. Merge step MUST NOT + all four exemptions — PASS (manual read)
   SKILL.md:225-234 quote: "**MUST NOT (wake economics): at merge/verdict
   time the hub never pulls the worker's *code diffs* or the *worker's own
   check/test output* into its own context — a path-scoped `git diff
   --stat` plus the ≤ 2k-token verdict is the ceiling; when the hub
   genuinely needs file contents it dispatches a scout, never reading them
   inline.** Explicitly EXEMPT (shipped machinery this ban must not
   weaken): the append-only whitelist content diff over `tasks/` (the diff
   just above), CAS re-reads of `Status:` header lines (step 2), `##
   Progress` / `## Deferred` / `## Decisions` append edits, and the hub's
   OWN post-merge project-gate run — its pass/fail plus the bounded output
   tail already specified for relaunch evidence (reference.md's
   Relaunch-with-evidence prompt, ~609)." All four named exemptions present
   verbatim per task spec.

6. Session-model sentence (SKILL.md) — PASS (manual read)
   SKILL.md:140-141 quote: "Because the hub's judgment lives in the task
   files and pinned worker tiers rather than in the hub session's own
   model, run a dedicated drain hub on the default (`opus`) tier or below:
   a frontier hub model roughly doubles wake cost for no quality gain."

7. `bash evals/lint-ultra-gate.sh` — PASS
   Ran against worktree copy: `lint-ultra-gate: OK — all ultra mentions
   gated in 4 files`, exit 0.

8. Append-only task-file discipline — PASS
   `git diff 0a5bcf3 -- 'specs/*/tasks/*.md'` shows only an added `<!--
   PLAN (delete at close-out): ... -->` comment block inserted after the
   header fields. Status line unchanged ("in-progress"), no checkbox ticks
   yet, no Goal/Steps/Touch/Budget/Acceptance text altered. Fully within
   the worker's allowed append-only set.

9. Behavioral machinery textually intact (only additive scoping) — PASS
   Diff review of SKILL.md: window-admission text (W default, top-up-on-
   verdict) unchanged aside from the new wake-economics paragraph inserted
   before it; merge-step whitelist-diff-check sentence and "Then merge the
   task branch" flow unchanged, with the MUST NOT+exemptions block spliced
   in between (additive); CAS/Status-header mechanics untouched; baton
   trigger text was rewritten per R1's explicit instruction (task Step 2),
   not incidental machinery — the ~4-verdict boundary is preserved and
   referenced, not removed. No merge-order, CAS-flip, or whitelist-diff
   *mechanism* changes found.

10. Touch discipline — PASS
    `git diff 0a5bcf3 --name-only`: only `.claude/skills/drain/SKILL.md`,
    `.claude/skills/drain/reference.md`,
    `specs/drain-wake-cost/tasks/01-drain-skill-text.md`. No edits to
    `.claude/rules/`, CLAUDE.md, `antigravity/`, `.claude-plugin/`, or
    `evals/`.

## Gates
- `bash evals/lint-ultra-gate.sh` → exit 0 (see #7).
- No repo-wide check.sh present for this toolkit repo per known convention
  (~/claude has no scripts/check.sh gate); lint-ultra-gate.sh is the
  standalone gate for this skill family and was run.

## Scope-creep findings
None. Diff is limited to the two Touch-listed skill files plus the
worker's own task file (append-only PLAN block only).

## Overall verdict: PASS
