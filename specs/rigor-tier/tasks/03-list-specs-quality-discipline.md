# Task 03: /list-specs displays the tier; quality-discipline.md scopes TDD to production-rigor

Status: in-progress
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirements R5, R7, R8)
Touch: .claude/skills/list-specs/SKILL.md, .claude/skills/list-specs/list_specs.py, .claude/skills/list-specs/test_list_specs.py, .claude/rules/quality-discipline.md, antigravity/.agents/skills/list-specs/SKILL.md, antigravity/.agents/skills/list-specs/list_specs.py, antigravity/.agents/skills/list-specs/test_list_specs.py

<!-- PLAN (delete at close-out)
Order: test (RED) -> feat (GREEN) -> antigravity port -> docs.
- test_list_specs.py: 2 rigor tests via scan_and_classify+render_table;
  Rigor: prototype spec renders "[prototype]" on Spec cell; no-header spec
  renders no marker. (RED)
- list_specs.py: RIGOR_RE local regex; scan_and_classify parses tier from
  spec text, adds row["rigor"]; render_table annotates Spec cell only for
  prototype rows (.get so classify_spec-only rows stay safe). (GREEN)
- Port list_specs.py + tests + SKILL.md to antigravity/.agents/skills/list-specs.
- SKILL.md prose: mention prototype annotation. quality-discipline.md: 1 line
  scoping TDD to Rigor: production, citing rigor-tier.
Choice: prototype rows get "[prototype]" annotation; production/absent
  unchanged (no marker) — kept consistent per step 1.
Risk: render_table must use row.get("rigor") since classify_spec unit tests
  build rows without the key.
-->

## Goal

`/list-specs`'s rendered table shows each spec's `Rigor:` tier, not just a
prose mention — `list_specs.py`'s `render_table` (SKILL.md just runs this
scanner and prints its stdout) gains a column or per-row annotation
surfacing the tier read from each spec/task's header — parse `Rigor:`
from each spec's SPEC.md `text` in `scan_and_classify` (list_specs.py
~line 250) and add it to the row dict, the same place `Status` is
already parsed (note: `list_specs.py` does NOT currently read
`Priority:` at all — don't go looking for that precedent, it isn't
there). `.claude/rules/quality-discipline.md`
gains one line scoping its TDD mandate to production-rigor work, citing
this mechanism. The antigravity list-specs mirror (its own
`list_specs.py` + `SKILL.md`) carries the equivalent display change.

## Touch

Do not touch `.claude/skills/idea/SKILL.md`, `.claude/skills/breakdown/SKILL.md`,
`.claude/skills/build/SKILL.md`, `.claude/skills/drain/SKILL.md`, or their
mirrors — those belong to tasks 01 and 02. Do not touch
`.claude-plugin/plugin.json`.

## Steps

1. Write a failing test in `.claude/skills/list-specs/test_list_specs.py`:
   a fixture spec/task carrying `Rigor: prototype` in its header renders
   with the tier visible in `render_table`'s output; a spec with no
   `Rigor:` header renders with no tier marker (or an explicit
   "production" marker — pick one and keep it consistent).
2. Make it pass: `list_specs.py` reads the `Rigor:` header via
   `scan_and_classify`, the same place `Status` is parsed (see Goal
   above), and `render_table` (around line 256-259,
   columns `Spec | Status | Next command`) surfaces the tier — either as
   a new column or an inline annotation on the `Spec` cell for
   prototype-tagged rows only (production/absent rows stay unchanged, so
   existing fixtures don't need updating).
3. Update `.claude/skills/list-specs/SKILL.md`'s prose to mention the new
   column/annotation.
4. Add one line to `.claude/rules/quality-discipline.md` scoping its
   unconditional TDD mandate to `Rigor: production` work (absent means
   production), citing the rigor-tier mechanism rather than restating it.
5. Port steps 1-3 into `antigravity/.agents/skills/list-specs/list_specs.py`,
   its `test_list_specs.py`, and `SKILL.md` (paraphrased port, match the
   behavior — these are the real ported content, not a symlink).

## Acceptance

- [ ] `python3 -m pytest .claude/skills/list-specs/test_list_specs.py -k rigor`
      passes (the new fixture test from step 1)
- [ ] `grep -qi "rigor" .claude/skills/list-specs/list_specs.py`
- [ ] `grep -qi "rigor" .claude/rules/quality-discipline.md`
- [ ] `python3 -m pytest antigravity/.agents/skills/list-specs/test_list_specs.py -k rigor`
      passes
- [ ] `grep -qi "rigor" antigravity/.agents/skills/list-specs/list_specs.py`
