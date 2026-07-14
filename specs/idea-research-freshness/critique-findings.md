# Critique findings — idea-research-freshness

Verdict: **NOT READY** (drain gen 4 critique intake, 2026-07-12; Run-token e83f34f07094a4fa)

The spec ships freshness fixtures but no deterministic checker over them (its
core deliverable), and gates most acceptance on running `/idea` end-to-end, which
an unattended drain worker cannot do. R7/R8/R9 authoring conventions ARE pinned
(mirror, plugin bump, first-30-lines, Next stage) — no finding there. Needs a
human revision before breakdown. Note: sibling `domain-knowledge-base` depends on
this spec's `Verified:` convention, so this must be settled first.

## Ranked findings (from the critic agent)

1. **Criteria 3-6 gate on running `/idea` end-to-end; no manual-pending path
   (conf 92).** SPEC.md:134-152 require a fresh agent running `/idea` (interview +
   deep-research dispatch + self-chain) — barred for drained workers by
   CLAUDE.md:110-114 and token-discipline.md (background workers can't interview).
   Fix: replace with a deterministic freshness-checker over fixtures + grep checks
   on SKILL.md step text; keep at most ONE end-to-end criterion, explicitly
   manual-pending.

2. **No runnable freshness check exists — the 90-day decision lives only in
   `/idea`'s model behavior (conf 88).** Fixtures (fresh/stale/no-stamp,
   SPEC.md:117-121) ship with no checker. Fix: add
   `.claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh <dir>`
   that greps `Verified:`, parses the date, compares a 90-day window (injectable
   reference date), prints fresh/stale/absent; assert its output per fixture. This
   also gives the sibling spec a mechanical convention to rely on.

3. **Inserting a step "between 1 and 2" breaks ~12 internal `step N`
   cross-references (conf 82).** SKILL.md cross-references steps heavily
   (:79,:89,:98,:119,:129, many "step 3"). Fix: state the insertion form
   (renumber 2-6 AND update all references) and add a criterion asserting
   cross-reference consistency.

4. **Absolute-dated fixtures rot (conf 76).** A hardcoded `Verified: 2026-07-12`
   in fresh/ passes today, fails in ~90 days. Fix: stamp fixtures relative to run
   time or have the checker accept `--today`.

5. **"immediately under its heading" implementable two ways (conf 65).**
   SPEC.md:22-24. Fix: pin the exact regex/placement (next non-blank line under the
   `##` heading, `Verified: YYYY-MM-DD`).

6. **Nit (conf 55): conditional criterion 1** (SPEC.md:123-129) depends on external
   repo state; make the grep-guard explicit.

## Next step

Human revises SPEC.md: add the deterministic `check-freshness.sh` + fixture
assertions, replace the run-`/idea` criteria with grep/manual-pending, pin the
step renumbering + cross-reference criterion, make fixtures date-relative, and
pin the stamp placement regex. Then re-run /critique. Do not /breakdown until
READY. (Ship this before domain-knowledge-base.)

## Triage 2026-07-13 (attended; Steven approved REVISE)

Verdict: REVISE. Edits before re-critique: (1) add `check-freshness.sh` (injectable `--today`, date-relative fixtures) and assert its fresh/stale/absent output per fixture; (2) replace the run-`/idea` criteria with grep checks on SKILL.md text plus one explicit manual-pending e2e; (3) pin the stamp regex/placement and a step-renumbering criterion. Verified: `docs/guides/model-routing.md` target headings landed (R1's conditional resolves); no grounding step or test-fixtures/ exists yet; 11 `step N` cross-references confirm the renumbering risk.

## Re-critique 2026-07-13 (drain critique intake, run b4adb88f) — still NOT READY, approved plan not yet applied

`git log -- specs/idea-research-freshness/SPEC.md` shows no commit since the
triage above — SPEC.md is byte-identical to the state that produced this
file's prior NOT READY verdict. Skipping a redundant full critic dispatch on
unchanged content per token-discipline's "cheap before expensive" — the
three approved triage edits above are the recovery path, unchanged. This
spec's critique intake is spent for this run.

## Re-critique 2026-07-13 (after applying the approved REVISE edits) — still NOT READY

Applied exactly the three approved edits from the 2026-07-13 triage above:
(1) added `check-freshness.sh` (injectable `--today`, date-relative
fixtures) with acceptance criteria asserting its fresh/stale/absent output
per fixture; (2) replaced the run-`/idea`-end-to-end criteria (old 3-6)
with grep checks on SKILL.md text plus exactly one explicit MANUAL-PENDING
end-to-end criterion; (3) pinned the stamp regex/placement
(`^Verified: \d{4}-\d{2}-\d{2}$`, next non-blank line after the `##`
heading) and added a step-renumbering cross-reference-consistency
criterion.

Full critic dispatch verdict: **NOT READY**. The three prior blockers are
confirmed closed. One new gap surfaced, introduced by this round's own
edit:

1. **(conf 78) The renumbering instruction ("today's steps 2-6 renumber to
   3-7") and its cross-reference criterion target `.claude/skills/idea/
SKILL.md` (6 steps) only.** `antigravity/.agents/skills/idea/SKILL.md`
   has only 5 steps (its own numbering: Adversarial pass is step 4, Hand
   off is step 5) with one internal `step 5` reference. R7 already
   requires mirroring the grounding-check step into antigravity, but
   neither R2/R7 nor the acceptance criteria say how antigravity's own
   steps renumber (2-5→3-6) or that its lone `step 5` reference must
   become `step 6` — a worker applying the `.claude`-shaped instruction
   literally to the 5-step mirror has no correct action, and nothing
   catches a stale reference there. Fix: state antigravity's own
   renumbering explicitly in R7, and add a parallel cross-reference
   criterion for the mirror.
2. **(conf 62, nit) `check-freshness.sh`'s per-heading output line format
   is unpinned** — "prints `fresh`" is checkable as a bare word or as
   `<heading>: fresh`; pin the exact line shape.
3. **(conf 60, nit) No fixture exercises the exact 90-day boundary** (91
   vs 90 days) — only "within 90" and "100+"; a `<`-vs-`<=` bug would pass
   all three current fixtures.
4. **(conf 52, mention-only) Date-diff portability** (GNU `date -d` vs BSD
   `date -j`) isn't called out; worth a one-line implementation note so
   breakdown budgets a portable approach.

Per this task's scope (apply only the previously-approved edit list, don't
invent new changes), finding 1 was not fixed in this pass — it needs a
human decision on how R7/the antigravity mirror should state its own
renumbering. `Breakdown-ready:` is not set; do not `/breakdown` until a
human resolves finding 1 (2-4 are nits, fixable in the same pass).

## Triage 2026-07-13 (attended; Steven approved, walk-through item 20)

Verdict: REVISE, applied directly. Resolves finding 1 (the only blocker;
2-4 were nits, left as-is per the prior pass's scoping decision):

R7 now states antigravity's own renumbering explicitly instead of
implicitly reusing `.claude`'s 6-step instruction: antigravity's
`SKILL.md` has its own independent 5-step numbering (confirmed via grep —
Scout/Interview/Write the spec/Adversarial pass/Hand off); inserting the
grounding-check step the same way (between antigravity steps 1 and 2)
renumbers its steps 2-5 to 3-6, and its one internal cross-reference
("step 5's hand-off" in step 4) must become "step 6's hand-off". Also
confirmed `antigravity/.agents/workflows/idea.md` has zero step-text
occurrences (a launcher stub, nothing to mirror there), closing the R7
parenthetical's open conditional. Added a parallel cross-reference AC
(`grep -c "step 6's hand-off"`, confirmed absent today) mirroring the
`.claude` leg's consistency check.

Ready for re-critique.
