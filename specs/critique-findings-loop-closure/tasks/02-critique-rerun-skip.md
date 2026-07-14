# Task 02: Critique re-run skip, replacing drain's commit-hash short-circuit (R5, R6)

Status: in-progress
Depends on: 01
Priority: P1
Budget: 26 turns
Spec: ../SPEC.md (requirements R5, R6)
Touch: .claude/skills/critique/SKILL.md, .claude/skills/drain/reference.md, docs/memory/drain-dispatch-lessons.md

## Goal

`/critique` becomes the sole owner of `specs/<slug>/critique-findings.md`.
On every NOT READY or READY WITH NITS verdict against a `SPEC.md` target,
`/critique` writes (creating the file if absent) or updates a header
recording the content hash of the exact `SPEC.md` content that verdict was
produced from, together with the verdict, then appends the findings in a
dated section — written atomically with the findings so the hash can never
desync from what it describes. Before dispatching the critic agent,
`/critique` compares `SPEC.md`'s current content hash against that recorded
header hash; if unchanged and a verdict is already recorded, it skips the
critic dispatch and relays the recorded verdict instead. A missing or
unparseable recorded hash (every `critique-findings.md` written before this
task ships) always means "run the critic" — never treat a missing hash as
a match. This skip applies only to `SPEC.md` targets; a plan or diff
invocation always runs the critic (no findings file to compare against).

This requirement **replaces** drain's existing "cheap-before-expensive
short-circuit" in `.claude/skills/drain/reference.md`'s Critique intake
section (the `git log -1 --format=%H` comparison, and the NOT-READY step's
own `critique-findings.md` write) — both are removed from `reference.md`.
Drain's critique intake goes back to unconditionally invoking `/critique`,
which now performs the equivalent skip and the findings-file write
internally, keyed on content hash rather than commit hash (a commit hash
stops resolving across a squash or rebase — the exact fragility this
change fixes).

`docs/memory/drain-dispatch-lessons.md`'s "Critique intake: skip the
critic..." entry is updated to point at the shipped `/critique` mechanism
instead of documenting the manual `git log -1` recipe.

## Touch

`.claude/skills/critique/SKILL.md` (builds on task 01's triage loop — this
task adds the hash-check-and-skip step plus the `critique-findings.md`
write; do not re-litigate task 01's MECHANICAL/JUDGMENT classification,
only integrate the file-write around it), `.claude/skills/drain/
reference.md` (remove the "Cheap-before-expensive short-circuit" and its
`critique-findings.md` write from the Critique intake section only — do
not touch the worker-prompt DEFERRED-verdict text near line ~590, that is
task 03's scope), `docs/memory/drain-dispatch-lessons.md` (update the one
entry named above only). Do not touch mirrors or `plugin.json` — task 04
carries those.

## Steps

1. Read `.claude/skills/critique/SKILL.md` as task 01 left it, and
   `.claude/skills/drain/reference.md`'s "Critique intake" section
   (currently ~line 1120-1163, "Cheap-before-expensive short-circuit"
   ~1134-1154) to see exactly what's being removed.
2. In `/critique`, add: before dispatching the critic, compute
   `SPEC.md`'s current content hash (e.g. `sha256sum` or equivalent) and
   compare against the header hash recorded in the target's
   `critique-findings.md` (if present). Missing/unparseable header → treat
   as changed, dispatch the critic. Matching header + a recorded verdict →
   skip dispatch, relay the recorded verdict and findings instead.
3. Add the write: on a NOT READY or READY WITH NITS verdict against a
   `SPEC.md` target, write/update `critique-findings.md`'s header with the
   content hash of the `SPEC.md` content the verdict was just produced
   from, and append the findings in a dated section (follow the existing
   format in `specs/build-doc-currency-check/critique-findings.md`).
4. In `.claude/skills/drain/reference.md`, delete the
   "Cheap-before-expensive short-circuit" bullet and its
   `critique-findings.md`-writing NOT-READY step from the Critique intake
   section; drain now just invokes `/critique` unconditionally (the
   "Otherwise, invoke `/critique`..." bullet already there becomes the only
   path).
5. Update `docs/memory/drain-dispatch-lessons.md`'s "Critique intake: skip
   the critic when SPEC.md is unchanged since a recorded NOT READY" entry:
   replace the manual `git log -1 --format=%ct` recipe with a pointer to
   `/critique`'s R5 mechanism (the entry should read as "mechanized in
   /critique" rather than a standalone lesson).

## Acceptance

- [ ] `grep -c "hash" .claude/skills/critique/SKILL.md` → ≥ 1 (today: 0,
      confirmed absent)
- [ ] `grep -c "Cheap-before-expensive short-circuit" .claude/skills/drain/reference.md` → 0
      (today: 1, confirmed present — this proves removal, not mere
      supplementation)
- [ ] `grep -c "mechanized in /critique" docs/memory/drain-dispatch-lessons.md` → ≥ 1
      (today: 0, confirmed absent)
- [ ] `grep -rn "NOT-READY specs (critique intake) | \`decide\` | §4" .claude/skills/drain/reference.md`
      still matches (the routing-table entry itself must survive the
      short-circuit removal untouched)
- [ ] `bash evals/lint-ultra-gate.sh` → exits 0
- [ ] MANUAL: exercise R1/R2 end to end via **drain's critique-intake path**
      (not a direct `/critique` call) on a real NOT-READY spec with a
      findable mechanical finding, and confirm the finding is applied
      without a human touching `SPEC.md` by hand — this only reliably
      exercises the drain path once this task's short-circuit removal
      lands (before that, an unchanged already-NOT-READY spec would hit
      the old short-circuit and never reach `/critique` at all).
- [ ] MANUAL: run `/critique` twice in a row on the same unchanged
      `SPEC.md` with a recorded NOT READY or READY WITH NITS verdict and
      confirm the second run skips the critic dispatch and relays the
      recorded verdict from `critique-findings.md` — then edit `SPEC.md`
      and confirm a third run dispatches the critic for real.
