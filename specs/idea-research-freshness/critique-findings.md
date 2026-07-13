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
