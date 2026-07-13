# Antigravity mirror: fix broken/unmirrored file references found by live testing

Breakdown-ready: true
Priority: P1

## Problem

The existence-only gate (`tests/test_antigravity_parity.sh`, spec
`antigravity-parity-gate`) proves every `.claude/` skill/agent name has a
mirror counterpart, and the planned content-parity gate (spec
`codequality-antigravity-content-parity`, still open) will catch `.py`
byte-drift. Neither gate can catch a mirrored file that *reads fine but
points at a path that doesn't exist in a standalone Antigravity install* —
that requires actually exercising the mirror's cross-references. This
session did that two ways: manual inspection, then a live pass through the
real `antigravity-cli` binary (`agy`, installed via `brew install --cask
antigravity-cli`, authenticated against a real Google account, pointed at
a scratch fixture seeded with this mirror) — including running its
`critic` skill mirror on an earlier draft of this very spec, which
surfaced additional real gaps folded in below (items 4 and 6). Findings:

1. **`antigravity/.agents/skills/workboard/reference.md:13`** instructs:
   `python3 -m unittest discover -s .claude/skills/workboard`. A user who
   followed `antigravity/README.md`'s own install steps
   (`cp -r ~/agentic-toolkit/antigravity/.agents .`) has no `.claude/` tree
   in their project — only `.agents/skills/workboard`. The command as
   written finds nothing. Verified: the tests exist and pass fine when
   pointed at the right path (`cd antigravity/.agents/skills/workboard &&
   python3 -m pytest -q` → 93 passed) — this is a stale copy-paste path in
   the doc, not a functional break in the skill itself.

2. **`antigravity/.agents/workflows/drain.md` (stub-intake section, ~line
   663)** describes the deterministic prompt-injection screen ("the hard
   layer... Promotion of injectable text can never rest on a model's
   judgment of it") as invoking `.claude/skills/drain/screen-stub.sh`
   directly, rather than restating its regex list. Confirmed via `find`:
   that script is **never mirrored anywhere under `antigravity/`**. In a
   standalone Antigravity install this is a hard dependency on a file that
   does not exist — the mandatory security gate is unimplementable as
   written. This is more severe than #1: it's a described security control
   with no ported implementation, not just a stale doc path.

3. **`antigravity/.agents/skills/prioritize/`** contains
   `prioritize_scan.py` + `test_prioritize_scan.py` but **no `SKILL.md`**.
   Its four disable-model-invocation siblings in `.claude/skills/`
   (`build`, `autopilot`, `evals`, `drain`) correctly have **no `skills/`
   directory at all** in the mirror — they're workflow-only, per the
   "human-only skills → workflows" convention (CLAUDE.md). `prioritize` is
   also `disable-model-invocation: true` in `.claude/skills/prioritize/SKILL.md`,
   so it should follow the same workflow-only shape; instead it has a
   half-populated `skills/` directory that reads as an incomplete skill
   port. It isn't one — `antigravity/.agents/workflows/prioritize.md`
   (unlike the thin one-line pointers used by `breakdown`, `idea`, etc.)
   is a full standalone port that shells out to
   `.agents/skills/prioritize/prioritize_scan.py` for the deterministic
   scan — but nothing marks that directory as "script bundle for the
   workflow, not a skill," so it silently violates the sibling pattern.

4. **Three mirrored test-file docstring headers carry the same stale
   `.claude/` run instructions as #1** — this is a class of bug, not a
   one-off:
   - `antigravity/.agents/skills/workboard/test_workboard.py:3` —
     `Run: python3 -m unittest discover -s .claude/skills/workboard`
   - `antigravity/.agents/skills/list-specs/test_list_specs.py:3-4` —
     same pattern for `.claude/skills/list-specs`
   - `antigravity/.agents/skills/prioritize/test_prioritize_scan.py:3-4` —
     same pattern for `.claude/skills/prioritize`
   All three should read `.agents/skills/<name>` instead. (The mirror's
   `workboard/reference.md:13`, item #1, is a fourth instance of this same
   class — fix all four together.)

5. **`antigravity/.agents/workflows/drain.md` has two more stale
   `.claude/rules/*.md` references beyond the `screen-stub.sh` one (item
   #2)**: line 84 cites `.claude/rules/concurrent-sessions.md` and line
   181 cites `.claude/rules/token-discipline.md` — neither exists in the
   mirror. Per `antigravity/README.md`'s own mapping table, `CLAUDE.md` +
   `rules/token-discipline.md` maps to `AGENTS.md` (always-on by
   definition) on the Antigravity side, so these should point at the
   corresponding `AGENTS.md` section instead of a nonexistent `.claude/`
   path.

6. **`antigravity/.agents/skills/prioritize/prioritize_scan.py:18`**
   carries the docstring comment `See specs/prioritize/SPEC.md (R1, R2)
   for the requirements this implements.` — correct in the source toolkit
   repo (that spec exists at `specs/prioritize/`), but meaningless in a
   standalone Antigravity install, which has its own unrelated `specs/`.
   Low severity (a comment, not a functional dependency) — worth a pass
   while touching this file for item #4, not urgent enough to justify a
   separate task.

Also verified clean, for the record (don't re-verify these):
- `tests/test_antigravity_parity.sh` passes (exit 0) — name-level mirror
  coverage is complete.
- All four mirrored Python suites pass: `prioritize` (17), `list-specs`
  (30), `workboard` (93), `_shared` (22) — 162 tests, 0 failures.
- Every thin-pointer workflow (`breakdown`, `critique`→`critic`, `design`,
  `distill`, `gate`, `handoff`, `idea`, `onboard`) resolves to a real
  `SKILL.md` — none are broken.
- The 3 JSON examples in `gate/reference.md` (hooks.json shape) are valid
  JSON.
- The "7 skills exist as both a skill and a workflow" ambiguity flagged as
  open in spec `antigravity-parity-gate` is, on inspection, intentional:
  each workflow is either a thin pointer to the skill body (auto-trigger
  version) for explicit `/command` invocation, or (for `critique`,
  `breakdown`, `prioritize`) adds genuine Antigravity-specific procedural
  notes on top. Not drift — no action needed here.

## Approach

All fixes happen in this toolkit repo (the source of truth); nothing here
requires a standalone consumer install to reproduce or verify — the
`tests/` and `specs/` referenced below are this repo's own.

1. Fix the four stale `.claude/skills/<name>` run instructions (item #1's
   `workboard/reference.md:13`, plus item #4's three test-file docstring
   headers) to read `.agents/skills/<name>`.
2. For the `screen-stub.sh` gap, default to (a): mirror the script
   verbatim to `antigravity/.agents/skills/drain/screen-stub.sh` — under
   `skills/`, not `workflows/` (workflows are prose-only by convention;
   scripts live in `skills/`, matching `prioritize/prioritize_scan.py`'s
   precedent) — and update `drain.md`'s reference path. Since `drain` is
   disable-model-invocation and otherwise has no `skills/` directory in
   the mirror (item #3's pattern), also add the same `README.md`-form
   workflow-support marker step 4 uses for `prioritize/` into the new
   `skills/drain/` — otherwise this fix recreates the exact incomplete-port
   appearance item #3 exists to correct. Only fall back to
   (b) — inlining the regex list directly into `drain.md` — if a
   maintainer decides duplicating the pattern list is preferable to
   shipping a second copy of the script; either way, `bash
   tests/test_antigravity_parity.sh` must still pass afterward (it doesn't
   currently check script-level paths, so this won't regress it either
   way — flagging so whoever picks this up doesn't assume the gate covers
   it).
3. Fix item #5: point `drain.md`'s two `.claude/rules/*.md` references at
   the corresponding `AGENTS.md` section instead — line 84
   (`concurrent-sessions.md`) → `AGENTS.md` § Concurrent sessions
   (`antigravity/AGENTS.md:147`); line 181 (`token-discipline.md`) →
   `AGENTS.md` § Dispatch authoring.
4. For `prioritize/`, add a one-line marker as a short `README.md` in the
   directory (prefer this over an in-file `NOTE` comment — a `README.md`
   states "script bundle for `workflows/prioritize.md`, not a triggerable
   skill" without adding another byte-divergence to `prioritize_scan.py`
   on top of the item-#6 comment fix below). Do not add a `SKILL.md`
   (that would make it model-invocable, contradicting its
   `disable-model-invocation: true` source). While in this file, also fix
   item #6's stale `specs/prioritize/SPEC.md` comment (drop it or reword
   to reference the source toolkit repo explicitly). Use the same
   `README.md`-only approach for the `skills/drain/` marker in step 2 —
   `screen-stub.sh` itself carries no internal `.claude/`-rooted content,
   so the marker file is the only new file needed there.

## Out of scope

- The already-tracked `_shared/test_viz.py` coverage drift and the
  content-parity gate itself — that's spec
  `codequality-antigravity-content-parity`, still open; don't duplicate it
  here.
- Any further live-testing sweep of the rest of the mirror's prose bodies
  for broken cross-references — this spec fixes the six found this
  session. A systematic reference-checker (grep every `.claude/`-rooted
  path mentioned in `antigravity/.agents/**` and assert it resolves under
  `antigravity/` instead) is a reasonable follow-up gate but is its own
  spec, not folded in here.
- Updating the content-parity gate itself. Fixing items #4/#6
  intentionally breaks `.py` byte-parity on 4 files, always — regardless of
  the drain/prioritize marker form chosen in steps 2/4: `test_workboard.py`,
  `test_list_specs.py`, and `test_prioritize_scan.py` diverge via item #4's
  run-instruction fix, and `prioritize_scan.py` diverges via item #6's
  docstring-comment fix (that one's divergence is unconditional — it isn't
  the marker, it's the `specs/prioritize/SPEC.md` comment on line 18, and
  the `README.md`-vs-`NOTE` choice only affects whether a *second*,
  avoidable divergence gets added on top). All 4 are currently
  byte-identical between `.claude/skills/` and `antigravity/.agents/skills/`.
  Spec `codequality-antigravity-content-parity` (still open) plans a `.py`
  `diff -q`-based gate premised on "every mirrored `.py` file is currently
  byte-identical" — that premise goes false for these 4 files once this
  spec lands. Whoever implements that gate needs to path-normalize or
  exempt: the run-instruction lines in the first three files, *and*
  the `specs/`-reference comment line in `prioritize_scan.py` (a docstring
  comment, not a run-instruction — don't miss it under a narrower
  "run-instruction lines only" reading) — rather than demand raw `diff -q`
  on any of the 4; noting the collision here so it isn't rediscovered as a
  regression.

## Acceptance criteria

- [ ] The following returns nothing (all four should read
      `.agents/skills/<name>`):
      ```
      grep -rn '\.claude/skills/' \
        antigravity/.agents/skills/workboard/reference.md \
        antigravity/.agents/skills/workboard/test_workboard.py \
        antigravity/.agents/skills/list-specs/test_list_specs.py \
        antigravity/.agents/skills/prioritize/test_prioritize_scan.py
      ```
- [ ] `cd antigravity/.agents/skills/workboard && python3 -m pytest -q`,
      likewise for `list-specs` and `prioritize`, all still pass (140
      tests total across these three suites — `_shared`'s 22 are a
      separate suite, not run by any of these three commands).
- [ ] `find antigravity -iname "screen-stub*"` finds a mirrored script
      under `.agents/skills/` (if approach (a) chosen), or `drain.md`'s
      stub-intake section no longer references a `.claude/`-rooted path
      (if approach (b) chosen).
- [ ] If approach (a): `antigravity/.agents/skills/drain/` contains a
      `README.md` workflow-support marker and no `SKILL.md` (same check as
      the `prioritize/` one below, applied to the new `drain/` dir).
- [ ] `grep -n 'screen-stub' antigravity/.agents/workflows/drain.md`
      shows no `.claude/`-rooted path — holds under either approach.
- [ ] `grep -n '\.claude/rules' antigravity/.agents/workflows/drain.md`
      returns nothing.
- [ ] `bash tests/test_antigravity_parity.sh` still exits 0 (unaffected).
- [ ] `antigravity/.agents/skills/prioritize/` contains a note/README
      identifying it as workflow-support, not a skill; no `SKILL.md` was
      added; the `specs/prioritize/SPEC.md` comment in
      `prioritize_scan.py` no longer implies that spec ships with the
      mirror.
- [ ] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`
      prints no FAIL lines.

## Parallelization

Tasks 01-03 are disjoint in `Touch` (different files, no shared undecided
design — the marker form, screen-stub target path, and AGENTS.md section
targets are all pinned above) and free of shared undecided design, so they
run concurrently. Task 04 is a closing gate depending on all three.

- Group: 01, 02, 03

## Closure (2026-07-13 verification sweep)

Original fixes verified correct. Two were later clobbered by unmirrored edits
and re-applied 2026-07-13 (8b0e0b4, cf8e2b3). Closed verified.
