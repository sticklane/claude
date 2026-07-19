# Task 02: Drain/build commit formats, mirrors, plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: 01
Priority: P2
Budget: 16 turns
Spec: ../SPEC.md (requirements R5, R6, R7, R8, R9)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, .claude/skills/build/SKILL.md, antigravity/.agents/workflows/drain.md, antigravity/.agents/workflows/build.md, codex/.agents/skills/drain/SKILL.md, codex/.agents/skills/build/SKILL.md, .claude-plugin/plugin.json

## Goal

Drain and build prescribe explicit commit formats where they are silent
today: drain's step-3 merge instruction pins
`merge: <spec-slug> task NN — <short what>` with riders/audit
notes/evidence in the body; drain's §3a baton-pass step and reference.md's
bookkeeping guidance state the same subject/body split (short subject,
verdict/lease detail in the body); build's commit bullet points at
quality-discipline.md's `## Commits` doctrine. The two pinned messages —
the in-progress flip contract and the auto-breakdown message — survive
verbatim. All drain/build edits are ported into the four mirror files and
`plugin.json`'s version is bumped.

## Touch

All eight header paths land in ONE commit (CLAUDE.md mirror mandate: skill
change + mirrors + bump ride together). The mirrors are paraphrased ports —
carry the same rules in each file's own voice, never byte-copy
(`.claude/rules/mirror-procedure-discipline.md`;
docs/memory/workboard-mirror-verbatim.md). Do NOT touch
`.claude/rules/quality-discipline.md` or `antigravity/AGENTS.md` (task 01's
scope). Adjacent-but-forbidden: the pinned flip contract at
`.claude/skills/drain/SKILL.md:166` and the auto-breakdown message at
`.claude/skills/drain/reference.md:1570` are read-only — edit near them,
never reword them. `specs/narrow-autopilot/tasks/07` (a draft stub) also
names `antigravity/.agents/workflows/build.md`; it is not dispatchable
while draft, but keep this task's edits to that file scoped to
commit-format guidance only.

## Steps

1. In `.claude/skills/drain/SKILL.md`'s step-3 merge instruction (~line
   207), add the merge-commit format: subject
   `merge: <spec-slug> task NN — <short what>` (target ≤72 chars, hard cap
   100 per quality-discipline.md), with ratified riders, audit notes, and
   acceptance evidence in the commit body — use the literal phrase
   "subject/body".
2. In the same file's §3a baton-pass step (~line 290), add the same
   subject/body split for baton-pass and bookkeeping commits: short
   subject, verdict/lease detail in the body — again using the literal
   phrase "subject/body".
3. In `.claude/skills/drain/reference.md`, add the subject/body split to
   its bookkeeping-commit guidance (the push-guard/bookkeeping region),
   using the literal phrase "subject/body". Leave the auto-breakdown
   message at line 1570 verbatim.
4. In `.claude/skills/build/SKILL.md`'s commit bullet (the "Commit code +
   task file..." bullet, ~line 247), add the doctrine reference: a
   type-prefixed subject per quality-discipline.md's `## Commits`, detail
   in the body. The reference must sit within the bullet (within 3 lines of
   "Commit code").
5. Port steps 1–4 into the four mirrors:
   `antigravity/.agents/workflows/drain.md`,
   `antigravity/.agents/workflows/build.md`,
   `codex/.agents/skills/drain/SKILL.md`,
   `codex/.agents/skills/build/SKILL.md` — each carries the "subject/body"
   guidance adapted to its runtime's voice.
6. Bump `version` in `.claude-plugin/plugin.json` (skill behavior changed).
7. Run every acceptance command below; tick each box with one line of
   evidence. Commit all eight files in one commit that itself follows the
   new doctrine (subject ≤72, detail in body).

## Acceptance

- [ ] `grep -c 'merge: <spec' .claude/skills/drain/SKILL.md` → ≥ 1
      (count 0 at spec-authoring time, verified 2026-07-17; still 0,
      re-verified 2026-07-19). Depth ceiling: L0 on skill prose — the
      skill's behavior is a live drain session's commits, not testable
      unattended; behavioral complement is a manual-pending human read of
      the first post-change drain merge commit, confirming its subject
      matches `merge: <spec-slug> task NN — <short what>` with detail in
      the body.
- [ ] `grep -ci 'subject/body' .claude/skills/drain/SKILL.md` → ≥ 2 — one
      hit in the step-3 merge instruction, one in §3a; a single hit means
      one edit was skipped (count 0 at spec-authoring time; still 0,
      re-verified 2026-07-19). Depth ceiling: same complement as the
      merge-format check above (the post-change drain commit read covers
      the baton-pass/bookkeeping subjects too).
- [ ] `grep -ci 'subject/body' .claude/skills/drain/reference.md` → ≥ 1
      (count 0 at spec-authoring time; still 0, re-verified 2026-07-19)
- [ ] `grep -c 'drain: <spec-slug> task NN in-progress' .claude/skills/drain/SKILL.md` → ≥ 1 —
      the pinned flip contract survives verbatim (count 1 today at
      SKILL.md:166)
- [ ] `grep -c 'drain: auto-breakdown specs/<slug>' .claude/skills/drain/reference.md` → ≥ 1 —
      the auto-breakdown message survives verbatim (count 1 today at
      reference.md:1570)
- [ ] `grep -A3 'Commit code' .claude/skills/build/SKILL.md | grep -c 'quality-discipline'` → ≥ 1
      (piped count 0 at spec-authoring time; still 0, re-verified
      2026-07-19). Depth ceiling: L0/L1 (position-scoped presence) on
      skill prose — behavioral complement is a manual-pending human read
      of the first post-change /build commit, confirming a type-prefixed
      ≤72-char subject with detail in the body.
- [ ] `grep -li 'subject/body' antigravity/.agents/workflows/drain.md antigravity/.agents/workflows/build.md codex/.agents/skills/drain/SKILL.md codex/.agents/skills/build/SKILL.md | wc -l` → 4
      (phrase absent from all four at spec-authoring time; still 0 of 4,
      re-verified 2026-07-19). Depth ceiling: L0 per-file mirror anchors —
      behavioral complement is the closure-triggered cross-reference sweep
      of `.claude/rules/mirror-verification.md` plus a
      procedural-equivalence read of the four ports per
      `.claude/rules/mirror-procedure-discipline.md`.
- [ ] `grep -o '"version": "[^"]*"' .claude-plugin/plugin.json` → a version
      different from the value at this task's own base commit
      (`git show <base-commit>:.claude-plugin/plugin.json | grep '"version"'`
      — record the base commit hash in the evidence line). The original
      "strictly greater than 0.9.16" half is already satisfied by sibling
      bumps (current value 0.9.19, verified 2026-07-19) and so proves
      nothing about this task; the changed-from-base comparison is the
      sole operative check, per the memory doc's version-bump pattern.
- [ ] The R8 end-to-end check exits 0 (run verbatim from the repo root;
      verified runnable and exit 0 on the current tree 2026-07-19 — it is
      a guard over the templates this task adds, not a proof-of-work
      check, so passing today is expected):

      ```sh
      grep -rhoE '`(drain|merge|feat|fix|test|refactor|docs|style|perf|chore|spec|breakdown): [^`]+`' \
        .claude/rules/quality-discipline.md antigravity/AGENTS.md \
        .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md \
        .claude/skills/build/SKILL.md \
        antigravity/.agents/workflows/drain.md \
        antigravity/.agents/workflows/build.md \
        codex/.agents/skills/drain/SKILL.md \
        codex/.agents/skills/build/SKILL.md \
        | awk '{ if (length($0) > 102) { print; bad=1 } } END { exit bad }'
      ```
