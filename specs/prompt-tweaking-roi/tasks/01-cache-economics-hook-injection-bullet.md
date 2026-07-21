# Task 01: Add the hook-injection bullet to Cache economics

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P3
Budget: 6 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4)
Touch: .claude/rules/token-discipline.md

## Goal

`.claude/rules/token-discipline.md`'s "Cache economics" section (~line 273) gains one new bullet: a hook earns its per-turn cost only when its
injected content is genuinely time-varying (state that can't be known at
prompt-authoring time) and must be silent when that state hasn't changed;
a reminder that would read the same every turn belongs in CLAUDE.md or a
rule file instead. The bullet names this repo's three compliant hooks
(`hooks/handoff-resume/`, `hooks/plugin-staleness/`,
`hooks/session-refresh/`) as worked examples and cites at least one named,
URL-backed research source from the spec's Problem section.

## Touch

This task touches only `.claude/rules/token-discipline.md`'s "Cache
economics" section — do not restructure or rename any other section, and
do not touch the three named hook files (`hooks/handoff-resume/`,
`hooks/plugin-staleness/`, `hooks/session-refresh/`) themselves; the spec's
Non-goals explicitly rule out changing their behavior; this task only
names them as examples in prose.

## Steps

1. Read the spec's Solution section (the exact bullet text is drafted
   there) and its three cited sources (Anthropic's context-engineering
   post, the "Lost in the Middle" paper, Claude's prompt-caching docs, and
   Claude Code's hooks reference) — pick at least one to cite by name +
   URL inline in the new bullet, per R2.
2. Append the new bullet to the end of `.claude/rules/token-discipline.md`'s
   "Cache economics" section (after its existing three bullets), stating:
   the time-varying/silent-when-unchanged rule (R1), a citation (R2), the
   three named hooks as compliant examples, and — since it must not
   duplicate the section's existing three bullets (R4) — a framing that
   extends rather than restates static-content-at-front /
   mid-session-edit-invalidation / tool-set-churn.
3. Confirm no other section was touched: `grep -c "^## "
.claude/rules/token-discipline.md` still returns the same count as
   before this edit (R3).
4. Run the acceptance commands below; tick each box with one line of
   evidence.

## Acceptance

- [ ] `grep -c "genuinely time-sensitive\|genuinely time-varying" .claude/rules/token-discipline.md` → ≥ 1
      (count 0 today, verified 2026-07-19)
- [ ] `grep -c "silent when nothing changed\|silent when that state hasn't changed" .claude/rules/token-discipline.md` → ≥ 1
      (count 0 today, verified 2026-07-19)
- [ ] `grep -c "hooks/handoff-resume" .claude/rules/token-discipline.md` → ≥ 1
      (count 0 today, verified 2026-07-19)
- [ ] `grep -c "hooks/plugin-staleness" .claude/rules/token-discipline.md` → ≥ 1
      (count 0 today, verified 2026-07-19)
- [ ] `grep -c "hooks/session-refresh" .claude/rules/token-discipline.md` → ≥ 1
      (count 0 today, verified 2026-07-19 — use the `hooks/session-refresh`
      path form specifically; the bare `session-refresh` string already
      matches the file's existing "## Session refresh" section twice and
      would pass vacuously)
- [ ] `grep -n "^## Cache economics" .claude/rules/token-discipline.md` → exactly one match
- [ ] `grep -c "^## " .claude/rules/token-discipline.md` → 8 (re-verify
      against `git show HEAD:.claude/rules/token-discipline.md | grep -c
  '^## '` at dispatch time in case another spec landed a section first)
- [ ] MANUAL: a human or reviewing agent reads the new bullet and confirms
      it cites at least one named, URL-backed source (R2) and does not
      duplicate the section's existing three bullets (R4) — mark
      manual-pending if dispatched unattended.
