# Task 03: Deferred-verdict premise-contradiction flag and blocked re-dispatch (R3, R4)

Status: in-progress
Depends on: none
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirements R3, R4)
Touch: .claude/skills/drain/reference.md, .claude/skills/drain/SKILL.md

## Goal

A drained worker's DEFERRED verdict gains an optional
`Contradicts-premise: true` marker it sets alongside its question when its
finding empirically refutes the SPEC's or task's stated root cause — not
merely an open information gap. Setting the marker requires naming which
artifact it contradicts (`SPEC.md` or the task file itself) and quoting the
exact contradicted excerpt verbatim, as a single clause or sentence (short
enough to substring-match reliably — never a multi-paragraph span). Drain
records the flag, the named artifact, the quoted excerpt, and the
contradicting evidence under the task's `## Deferred questions`.

For a task flagged this way, drain's batch-interview answer flow (step 4)
must not flip `Status: deferred` back to `pending` on a plain human answer
alone. It additionally requires the named artifact to no longer contain
the quoted excerpt unchanged — checked as a whitespace-normalized substring
match (collapse runs of whitespace/newlines in both the recorded excerpt
and the artifact's current full text before comparing, so an untouched
reflow doesn't spuriously register as a change and a genuinely edited
excerpt can't hide behind line-based wrapping). Until the excerpt is
observed absent post-normalization, the task (and any dependent) stays
non-dispatchable, and its HUMAN.md entry types as `decide` ("spec amendment
needed" or "task amendment needed", matching the named artifact) rather
than `ask`.

## Touch

`.claude/skills/drain/reference.md` — the worker prompt's DEFERRED-verdict
instructions (currently around "stop with verdict DEFERRED and put the
exact question, self-contained, in your final message", ~line 590) gain
the optional `Contradicts-premise: true` marker and its naming/quoting
requirement. `.claude/skills/drain/SKILL.md` — step 4's batch interview
("`Status: deferred` tasks exist: collect their `## Deferred questions`
blocks...", ~line 454) gains the substring-match gate before flipping
`Status: deferred` back to `pending`. Do not touch the "Critique intake"
section or the "Cheap-before-expensive short-circuit" in `reference.md` —
that is task 02's scope; if task 02 lands first or concurrently, rebase
around its changes rather than re-deriving them.

## Steps

1. Read `.claude/skills/drain/reference.md`'s worker-prompt section
   (`## Worker prompt (verbatim, fill the <>)`) around the DEFERRED
   instructions, and `.claude/skills/drain/SKILL.md`'s step 4 (`## 4. The
batch interview`) and its `Status: deferred` handling in step 3.
2. Add the `Contradicts-premise: true` marker to the worker prompt's
   DEFERRED path: when a worker's finding empirically refutes (not merely
   questions) the SPEC's or task's stated root cause, it sets this marker
   alongside its question, names the artifact (`SPEC.md` or the task file),
   and quotes the exact contradicted clause/sentence verbatim.
3. Update drain's DEFERRED-recording behavior (step 3, "## Deferred
   questions") to capture the flag, named artifact, and quoted excerpt
   when present.
4. In step 4's batch interview, add the gate: before flipping a
   `Contradicts-premise: true` task from `deferred` to `pending` on a
   human answer, check whether the named artifact's current content still
   contains the quoted excerpt (whitespace-normalized substring match). If
   it does, do not flip the status — file the task as HUMAN.md `decide`
   ("spec amendment needed" / "task amendment needed") per
   `.claude/rules/human-blockers.md`'s grammar instead of `ask`.
5. Leave the existing plain-DEFERRED (no `Contradicts-premise`) flow
   unchanged — a plain human answer still flips `Status: deferred` to
   `pending` exactly as today.

## Acceptance

- [ ] `grep -c "Contradicts-premise" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md`
      → ≥ 1 combined (today: 0 in both, confirmed absent)
- [ ] `bash evals/lint-ultra-gate.sh` → exits 0
- [ ] MANUAL: exercise R3/R4 with a synthetic DEFERRED verdict carrying
      `Contradicts-premise: true` (naming `SPEC.md` as the contradicted
      artifact and quoting a real excerpt from it) and confirm the batch
      interview's plain-answer flow refuses to flip the task back to
      `pending` until that exact quoted excerpt is no longer present
      unchanged in `SPEC.md` — then edit `SPEC.md` to remove/alter the
      excerpt and confirm the flip is permitted.
