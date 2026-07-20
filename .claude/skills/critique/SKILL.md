---
name: critique
description: Runs an adversarial review of a spec, plan, or diff via the critic agent and relays ranked findings. Use before implementing a spec or plan, before committing a nontrivial change, or when the user asks "review this", "poke holes", or "is this ready?". Not the tool for working-diff bug hunts (/code-review), GitHub pull requests (/review), or exercising runtime behavior (the verifier agent).
argument-hint: "[path/to/artifact | 'diff']"
---

Get an adversarial second opinion on $ARGUMENTS. If no argument: an
uncommitted diff exists → review that; otherwise the most recently touched
SPEC.md or plan.

**SPEC.md re-run skip (checked first, before step 1's dispatch).** When the
target is a `SPEC.md`, compute the content hash of its current bytes (e.g.
`sha256sum specs/<slug>/SPEC.md`) and compare it against the hash recorded in
the target's `specs/<slug>/critique-findings.md` header (if that file exists
and carries a parseable hash). If the hash matches **and** a verdict is
already recorded, skip the critic dispatch entirely and relay that recorded
verdict and its findings from `critique-findings.md` (step 2) — the answer is
already computed against byte-identical content. A missing
`critique-findings.md`, a missing header hash, or a hash that fails to parse
always means "run the critic" — never treat an absent or unparseable hash as
a match (every findings file written before this skip shipped has no hash, so
it always re-runs). This skip is `SPEC.md`-only: a plan or diff target has no
`critique-findings.md` to compare against and always dispatches the critic.
`/critique` is the sole owner of `critique-findings.md` — step 6 writes it.

1. Spawn the `critic` agent with a POINTER to the artifact (file path, or a
   pointer to the working diff — e.g., under git: `git diff HEAD`), never the
   pasted content — the critic
   reads it in its own context. Include one line on what "wrong" looks like
   here (e.g., "this spec feeds /breakdown; ambiguity is the enemy"). If the
   artifact touches auth, payments, secrets, or user-data handling, name
   security in that line so the critic reviews with a security lens — and
   for a working diff, also point the user at the built-in /security-review.
2. Relay the verdict and findings verbatim in ranked order. Don't soften
   NOT READY.
3. If the artifact is a `SPEC.md`: on READY, write `Breakdown-ready: true` as
   a header line under the spec's title (above the first `##`) — this is the
   token `/drain` reads to auto-invoke `/breakdown` on specs with no `tasks/`
   yet (docs/human-gates.md has the rationale, cited not restated). On NOT
   READY, remove a stale `Breakdown-ready:` line if one is present — a spec
   that regressed shouldn't keep an old authorization. Never write or remove
   this marker for a plan or diff target.
4. **Triage the findings** when the verdict is NOT READY or READY WITH NITS.
   Classify each finding as MECHANICAL — an edit with no judgment call: a
   stale path/line reference, a non-deterministic or under-scoped acceptance
   command, a missing runnable check, a format/header contract violation — or
   JUDGMENT — an ambiguity, a scope question, a missing design decision, a
   contested tradeoff, or a gameability finding: gameable criteria are JUDGMENT-class, never MECHANICAL —
   swapping what a criterion checks changes what the spec verifies (a
   spec-meaning change), so a trivially-satisfiable/gameable criterion is
   never the MECHANICAL bullet's "under-scoped acceptance command" and is
   routed to JUDGMENT. MECHANICAL findings are applied _unconditionally_,
   without the user-ask/pipeline gate that governs the rest of this step:
   edit the target file directly, commit (`fix: apply mechanical critique
findings` or similar), and re-run the critic — this apply→recheck loop is
   bounded to the 2-4 cycle evaluator-optimizer cap in
   `.claude/rules/token-discipline.md`'s "Dispatch authoring" (cited, not
   restated). Auto-apply is scoped to the prose target only — a `SPEC.md`, or
   the plan file when `/critique` reviewed a plan document; a working-diff or
   code target is never auto-edited. For the JUDGMENT findings (and any
   MECHANICAL finding still open after the loop bound): a reviewer told to
   find gaps will always find some — recommend fixing the ones that change
   behavior or block verification, flag style-level ones as optional, and
   apply _these_ only if the user asks or the pipeline step you're in requires
   READY. Nothing is dropped silently — every finding still open after the
   bound, plus every JUDGMENT finding from the first pass, is relayed via
   step 2.
5. After fixes, re-run the critic on the changed artifact — a critique you
   didn't re-check is a claim, not a verification. Between rounds the author
   re-reads only the sections the critic named, never the whole artifact.
6. **Persist the findings for a `SPEC.md` target** (skip for a plan or diff,
   and skip when the re-run gate above already relayed a recorded verdict —
   nothing was re-derived to record). Once the verdict has settled (after any
   step-4 apply→recheck loop and step-5 re-run), if the settled verdict
   against the `SPEC.md` is **NOT READY or READY WITH NITS**, write or update
   `specs/<slug>/critique-findings.md` in one atomic write: a header
   recording the content hash of the exact current `SPEC.md` bytes the
   settled verdict was produced from together with that verdict, and the
   findings appended as a dated section (the format
   `specs/build-doc-currency-check/critique-findings.md` establishes). Header
   hash and findings are written together so the recorded hash can never
   desync from the findings it describes; the hash is what the next
   invocation's re-run skip compares against. A plain READY (no nits) records
   no findings — step 3's `Breakdown-ready:` marker is its only artifact.

## Ultra path

When the active runtime profile documents an orchestration section AND
ultracode is opted in (keyword, session flag, or explicit ask), critique may
run a panel instead of one critic; otherwise, and always when the profile is
silent, the single-critic path above is the only path. The active runtime
profile carries the workflow-script template — this skill only points at it.

Panel: 3–5 lens-diverse critics (correctness, security, verification-gaps,
scope, cost-if-missed) run in parallel over the same artifact POINTER.
Findings are deduped, then adversarially verified — a finding dies on a
majority refute — before any relay. Ranking, the marker-write step, and the
fix-recommendation rule above are unchanged — the panel still resolves to one
verdict that step 3 acts on.

Worth the 10×+ token cost only for pre-implementation specs, security-
sensitive diffs, or an explicit "be thorough" ask. Never auto-triggered.
