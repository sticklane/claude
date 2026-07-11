# Task 01: Drain skill-text edits — dual baton trigger, verdict cap, merge-step ban, wake economics

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: pending
Depends on: none
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R6)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

Drain's SKILL.md and reference.md carry the five prose contracts from the
spec: a context-budget baton trigger alongside the ~4-verdict generation
boundary (R1), the ≤2k-token verdict cap in the worker final-message
contract AND the SKILL.md verdict line (R2), the merge-step MUST NOT with
its full exemption list (R3), the wake-economics doctrine paragraph with
the cost model (R4), and the session-model sentence (R6). No behavioral
machinery changes — window admission, merge order, CAS, whitelist diff,
and baton grammar all stay as shipped.

## Touch

Only the two drain skill files. Do NOT touch `.claude/rules/`, CLAUDE.md
(task 02 owns doctrine), `antigravity/`, `.claude-plugin/plugin.json`, or
`evals/` (task 03 owns the ship gate). Do NOT alter the rolling-window
admission rules, merge serialization, CAS flip, or whitelist content diff
— R3 only adds a scoped prohibition + exemptions around them.

## Steps

1. Read ../SPEC.md and ../EVIDENCE.md in full, then the current
   `.claude/skills/drain/SKILL.md` (baton section ~305–336, rolling window
   ~121–159, merge step ~200–223) and `reference.md` worker final-message
   contract (~522–538).
2. R1: extend the generation boundary to "after ~4 verdicts OR when the
   hub's context is heavy, whichever comes first". Decide the heaviness
   signal: if the harness exposes a reliable in-session context indicator
   the hub can check, use it; otherwise adopt the spec's deterministic
   fallback — baton after `max(2, 6 − W)` verdicts. Record which was
   chosen and why in one sentence in the baton section, and note the
   decision under this task's ## Progress when reporting.
3. R2: in reference.md's worker final-message contract, cap the verdict at
   ≤ 2k tokens (status, merged-commit/branch, per-criterion pass/fail with
   one-line evidence, deferred items; transcripts/full diffs/test output
   excluded). Attach the cap textually to the final-message/verdict
   wording so the spec's acceptance grep discriminates from the
   pre-existing assessor line at ~962. Name the same cap in SKILL.md's
   "structured verdict + evidence, never its transcript" line.
4. R3: in the merge step, add the MUST NOT — the hub never pulls the
   worker's code diffs or the worker's own check/test output into its
   context; path-scoped `git diff --stat` + the verdict is the ceiling;
   scouts fetch file contents when genuinely needed. List the exemptions
   verbatim: the append-only whitelist content diff over `tasks/`, CAS
   re-reads of `Status:` header lines, `## Progress`/`## Deferred`/
   `## Decisions` append edits, and the hub's own post-merge gate run
   (pass/fail + the bounded output tail per reference.md ~609).
5. R4: add the wake-economics paragraph near the rolling-window section:
   awaited workers outlive the 5-minute cache TTL, so every verdict wake
   re-caches the whole hub context at 1.25× input rate — hub size, not
   wake count, is the cost lever; include the cost model
   (context_tokens × input_rate × 1.25 per wake) and the measured shape
   (median 187k-token rewrites, $587/week — cite ../EVIDENCE.md).
6. R6: one sentence recommending the default (opus) tier or below for
   dedicated drain hub sessions, since hub judgment lives in task files
   and pinned worker tiers.
7. Keep SKILL.md well under 500 lines and execution-critical contracts in
   its first 30 lines intact; run the acceptance checks.

## Acceptance

- [ ] `grep -qiE 'context.{0,40}(budget|heavy|trigger)' /Users/sjaconette/claude/.claude/skills/drain/SKILL.md` → exit 0, and the baton section states the dual trigger as one evaluable rule (cite the line in evidence)
- [ ] `grep -qiE 'final message.{0,120}2k tokens|verdict.{0,120}2k tokens|2k tokens.{0,120}(final message|verdict)' /Users/sjaconette/claude/.claude/skills/drain/reference.md` → exit 0
- [ ] `grep -qiE '2k tokens' /Users/sjaconette/claude/.claude/skills/drain/SKILL.md` → exit 0
- [ ] `grep -q '1\.25' /Users/sjaconette/claude/.claude/skills/drain/SKILL.md && grep -qiE 'TTL' /Users/sjaconette/claude/.claude/skills/drain/SKILL.md` → exit 0
- [ ] Merge step contains the MUST NOT with all four exemptions (quote the passage as evidence)
- [ ] Session-model sentence present in SKILL.md (quote as evidence)
- [ ] `bash /Users/sjaconette/claude/evals/lint-ultra-gate.sh` → exit 0
