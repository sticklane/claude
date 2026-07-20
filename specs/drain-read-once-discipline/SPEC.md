# Drain read-once discipline

Breakdown-ready: true

## Problem

A recently-merged spec (`drain-hub-context-discipline`) fixed a _width_
problem: `reference.md` getting read as one long sequential `Read` of the
whole ~1,867-line file instead of the named Grep-then-offset section slice.
That fix landed — `reference.md:19-25` now instructs "Grep-then-offset reads
(do this before every reference.md read)" with a linked table of contents at
lines 3-13, and SKILL.md's section pointers cite it rather than restating it.

A manual 11-transcript audit of recent `/drain` sessions (2026-07-19, across
the `claude`, `hub`, `fooszone`, and personal-vault repos) found a narrower,
still-live _repetition_ problem the width fix doesn't touch: even when
Grep-then-offset is used correctly, the _same already-loaded section_ (or an
overlapping line range) gets Grep'd/Read a second or third time later in the
same session, with no edit to the file and no new information gained.
Evidence:

- `claude/23ba3781` (drain, 3-spec merge): `reference.md`'s full initial read
  (no offset) followed by two more `Read` calls at `offset:970/limit:550` and
  `offset:1520/limit:330` — both ranges the first read already covered, ~57KB
  of pure duplication.
- `claude/66412fbf`: `specs/*/SPEC.md` files each read in full, then re-read
  at an offset, then read a third time before the eventual `Edit` — nothing
  changed between any of the three reads.
- personal-vault `c126a74b`: two consecutive `sed -n` slices of
  `reference.md` over nearly the same line range, back to back.
- `fooszone/71294ab5`: `reference.md` read 6 times at creeping offsets in one
  session, including 3 near-duplicate greps iterating toward a search term
  instead of converging in one pass.
- `hub/9d679a37`: `CLAUDE.md` read in full, grepped for text already visible
  from that read, then read in full again immediately before an `Edit`.

`.claude/rules/token-discipline.md:243-244` already states the general rule
("Don't re-run searches or re-read files already established this session")
but it isn't holding in practice — especially for drain's own long-running
orchestrator sessions, which return to `reference.md` at many separate
decision points (Owner lease, Baton pass, Stub intake, Auto-breakdown,
Spec-completion review, …) and have no mechanism forcing reuse of a section
already pulled into context earlier in the same run.

## Solution

Two doctrine edits plus one enforced behavioral check, scoped to what the
audit actually evidenced (drain's `reference.md` reads) while generalizing
the stated rule so other skills can pattern-match it:

1. **Extend `reference.md`'s Grep-then-offset instruction block (current
   lines 19-25)** with an explicit already-loaded check, using this exact
   canonical phrase — verbatim, not paraphrased — since R4 and R5 below
   depend on grepping for it byte-for-byte: **"already loaded this section
   this session"**. The added sentence: "Before Grep-then-offset: check
   whether you have already loaded this section this session with no edit to
   reference.md since — if so, reuse it from context instead of
   re-Grep/re-Read." State the boundary explicitly: this targets
   `reference.md`'s own largely-static content, not the task-file /
   owner-lease re-read machinery in "Wake economics" / "Owner lease"
   (`reference.md:132-277`), which already has its own correctness-motivated
   re-read requirements (CAS confirmation, the merge-time re-read ban) and is
   untouched by this spec.

2. **Strengthen `token-discipline.md`'s Session hygiene bullet
   (`token-discipline.md:243-244`)** with the general form of the same guard,
   plus the one legitimate exemption already evidenced elsewhere in this
   repo — the immediate re-read-before-a-Status-flip concurrency guard
   (`docs/task-tracking-design-research-2026-07.md:90`; `reference.md`'s CAS
   re-read at lines 270-277) — so the strengthened rule can't be
   misread as banning that correctness-required re-read. Name this exemption
   with one exact canonical phrase, verbatim — **"Status-flip concurrency
   guard"** — the same way R1 names its own canonical phrase, so the
   acceptance check can grep for it precisely rather than an alternation of
   near-synonyms. Point to `reference.md`'s now-concrete instruction as the
   worked example.

3. **Add a new eval scenario `evals/drain/02-reference-reread/`** (same
   directory shape as `evals/drain/01-rolling-window/`: `setup.sh`,
   `prompt.txt`, `allowed-tools.txt`, `assert.sh` — NOT the same _mechanism_:
   `01-rolling-window/assert.sh` inspects git history and never reads
   `$EVAL_TRANSCRIPT`, so it is not a template for transcript parsing here).
   The new `assert.sh` parses `$EVAL_TRANSCRIPT` (JSONL; use `python3`, the
   same parser `runtimes/parse_headless.py` already relies on elsewhere in
   `evals/`) and applies this precise, `Read`-only match predicate — `Grep`
   calls are excluded, since a grep pattern has no offset/limit interval to
   compare: two `Read` tool_use calls both targeting `reference.md` whose
   intervals overlap, with no `Edit` tool_use targeting `reference.md`
   between them, is a violation. The interval for a given `Read` call is
   total over every shape the tool allows: both `offset` and `limit` present
   → `[offset, offset+limit)`; neither present → the full-file interval;
   `offset` present with no `limit` → `[offset, EOF)`; `limit` present with
   no `offset` → `[0, limit)`. `assert.sh` exits non-zero on the first
   violation found, 0 otherwise.

   The scenario ships two fixture transcripts alongside the usual
   `setup.sh`/`prompt.txt` machinery — `fixtures/good.jsonl` (two `Read`s of
   _disjoint_ `reference.md` ranges) and `fixtures/bad.jsonl` (two `Read`s of
   _overlapping_ ranges, no `Edit` between) — so the predicate itself is
   testable deterministically via
   `EVAL_TRANSCRIPT=fixtures/good.jsonl bash assert.sh` (expect exit 0) and
   `EVAL_TRANSCRIPT=fixtures/bad.jsonl bash assert.sh` (expect non-zero),
   without depending on a live model choosing (or failing) to re-read on any
   given run. A live end-to-end run via `evals/run.sh drain/02-reference-reread`
   against a real dispatched session is valuable _evidence_ but is NOT a
   required acceptance gate: per CLAUDE.md, a drained task must not gate
   acceptance on `/evals` (human-launch-only, spawns paid headless sessions;
   also non-deterministic here since the live model's actual behavior is
   exactly what's under test) — mark that live run manual-pending per
   `docs/memory/unattended-worker-tool-limits.md`.

## Requirements

- R1: `reference.md`'s Grep-then-offset instruction block states the exact
  canonical phrase **"already loaded this section this session"** and the
  exemption boundary, in the file's own words (not by cross-reference alone
  — this is the canonical instruction all of SKILL.md's "load only the named
  section" pointers already point to), positioned inside the Grep-then-offset
  block itself (current lines 19-25), not elsewhere in the file.
- R2: `token-discipline.md`'s Session hygiene bullet is strengthened with the
  concurrency-guard exemption — naming it with the exact canonical phrase
  **"Status-flip concurrency guard"**, verbatim — and a pointer to
  `reference.md`'s guard as the concrete worked example.
- R3: `evals/drain/02-reference-reread/` exists per the Solution's mechanism
  above: a `Read`-overlap match predicate in `assert.sh`, parsed with
  `python3`, verified deterministically against the `good.jsonl`/`bad.jsonl`
  fixtures (not against a live run).
- R4: The change is ported to both drain mirrors in the same commit, per
  CLAUDE.md's "when a skill changes here, mirror the change into
  `antigravity/` in the same commit" and the port-chain rule for `codex/`:
  `antigravity/.agents/workflows/drain.md` and
  `codex/.agents/skills/drain/SKILL.md` (both already contain
  "Grep-then-offset" text today — confirmed via `grep -rl`) get the
  equivalent addition, classified as _incidental_ (same procedure, must
  carry) per `.claude/rules/mirror-procedure-discipline.md`. Unlike ordinary
  mirror prose (which legitimately diverges in wording per
  `mirror-procedure-discipline.md`), R1's canonical phrase **"already loaded
  this section this session" is divergence-exempt** — both mirrors must
  reproduce it verbatim, because R5's coverage check depends on grepping the
  identical substring in source and mirror alike.
- R5: `tests/mirror-procedure-manifest.txt` gets a new
  `<source>|<mirror>|<phrase>` entry using that same verbatim phrase. Because
  `test_mirror_procedure_coverage.sh` silently skips (does not fail) any
  manifest line whose phrase is absent from the source file — so "the test
  passes" is not by itself evidence the entry was added correctly — the
  acceptance check below verifies the phrase's presence directly in all
  three files rather than relying on the coverage test's exit code alone.
- R6: `.claude-plugin/plugin.json`'s `version` field is bumped, per CLAUDE.md's
  "Bump `version` in `plugin.json` whenever skill behavior changes."

## Out of scope

- SPEC.md/CLAUDE.md re-read fixes for skills _other than_ drain — the audit
  evidence for those was thinner (both non-drain-reference.md instances,
  `claude/66412fbf`'s SPEC.md re-reads and `hub/9d679a37`'s CLAUDE.md
  re-read, occurred _inside_ drain orchestrator sessions, not other skills),
  and R2's strengthened general rule covers them at the doctrine level
  without a drain-specific enforced mechanism. A dedicated eval for those is
  a follow-up if the pattern recurs after this ships.
- Re-architecting `reference.md`'s section structure or table of contents —
  this is additive guard language, not a restructuring (the width-side
  restructuring was `drain-hub-context-discipline`'s job and is done).
- The stale-plugin-cache-version-path issue from the same audit (two
  independent sessions guessed `agentic/0.9.19/...` before finding the
  actual `0.9.20/`) — a distinct root cause (a hardcoded/remembered version
  number, not a re-read), tracked as a separate spec
  (`drain-plugin-path-resolution`).
- Cross-generation (baton-pass) read caching. `DRAIN-BATON.md`'s Anomalies
  section could theoretically carry "sections already read" state across a
  baton pass, but a fresh generation legitimately starts with empty context
  and _must_ re-read to operate at all — this spec only targets re-reads
  _within_ one continuous orchestrator/worker session.

## Acceptance criteria

- [ ] `sed -n '19,35p' .claude/skills/drain/reference.md | grep -c "already loaded this section this session"`
      → 0 today (verified 2026-07-19; whole-file `grep -c` for the same
      string is also 0 today), ≥1 after the fix — R1, windowed to the
      Grep-then-offset block itself so the phrase can't satisfy this
      criterion from an unrelated/decorative location. Depth ceiling: this
      is a prose/doctrine change to an operating manual; an L0 grep is the
      correctness-checkable floor for the instruction text itself, and R3's
      eval scenario is the behavioral complement.
- [ ] `grep -c "Status-flip concurrency guard" .claude/rules/token-discipline.md`
      → 0 today (verified 2026-07-20), ≥1 after the fix — R2, pinned to the
      exact verbatim phrase rather than an alternation of near-synonyms.
      Same Depth-ceiling rationale as R1.
- [ ] `EVAL_TRANSCRIPT=evals/drain/02-reference-reread/fixtures/good.jsonl bash evals/drain/02-reference-reread/assert.sh`
      exits 0, and
      `EVAL_TRANSCRIPT=evals/drain/02-reference-reread/fixtures/bad.jsonl bash evals/drain/02-reference-reread/assert.sh`
      exits non-zero — R3, the deterministic behavioral complement to
      R1/R2's L0 grep checks. (`bash evals/run.sh drain/02-reference-reread`
      against a live model is valuable corroborating evidence but is
      manual-pending, not a required gate — see Solution point 3.)
- [ ] `grep -c "already loaded this section this session" antigravity/.agents/workflows/drain.md codex/.agents/skills/drain/SKILL.md`
      shows ≥1 in each file (both currently 0, verified 2026-07-19) — R4,
      checking the verbatim divergence-exempt phrase directly rather than
      the looser pre-existing "Grep-then-offset" string both files already
      contain today.
- [ ] `grep -c "already loaded this section this session" .claude/skills/drain/reference.md antigravity/.agents/workflows/drain.md codex/.agents/skills/drain/SKILL.md`
      shows ≥1 in all three files, AND
      `bash tests/test_mirror_procedure_coverage.sh` passes — R5. The triple
      grep is the actual, non-vacuous check; the coverage-test run is
      corroborating (see Solution's R5 note on why the coverage test alone
      cannot be trusted as the sole gate).
- [ ] `grep -n '"version"' .claude-plugin/plugin.json` shows a value greater
      than `0.9.20` (today's value, verified 2026-07-19) — R6.
- [ ] End-to-end: a fresh `/drain` session run against
      `evals/drain/02-reference-reread`'s fixture (manual-pending, per
      Solution point 3) shows no repeated `Read` of the same `reference.md`
      line range in its transcript.

## Open questions

(none — resolve any that surface during critique before breakdown starts)
