Status: pending
Depends on: none
Priority: P0
Budget: 10 turns
Discovered-from: specs/absorb-agent-tools/tasks/02-import-agent-console-deduped.md
Spec: ../SPEC.md
Touch: .claude/skills/workboard/workboard.py, agent-console/agent-console.py
Blocking: no

# Workboard per-spec Priority select always shows unset

`render_workboard`'s per-spec `Priority:` `<select>`
(`agent-console/agent-console.py:1219`, via `_prio_select` at lines
763-774) always shows the blank "—" default, since
`workboard.py`'s `scan_toolkit_specs()`
(`.claude/skills/workboard/workboard.py:212-263`) defines `STATUS_RE`,
`DEPENDS_RE`, `TITLE_RE` but no `PRIORITY_RE` — it never extracts a
spec's `Priority:` header, so the spec dict it returns has no priority
field for the adapter to read. `agent-console.py:624` already documents
the gap inline (`"priority": "", # not tracked by workboard.py's scan`).
Confirmed not fixable within the adapter alone: the adapter
(`_adapt_board`, lines 581-718) is a pure translation layer with no
source to read a priority from until `workboard.py` provides one.

## Steps

1. Add a `PRIORITY_RE` pattern to `workboard.py` (same style as the
   existing `STATUS_RE`/`DEPENDS_RE`) that extracts a spec's top-level
   `Priority: PN` header from its SPEC.md text.
2. Add the extracted value to the spec dict `scan_toolkit_specs()`
   returns (absent header → same default the other optional headers use,
   e.g. empty string or "P2" — match this repo's "absent means P2"
   convention documented in CLAUDE.md's authoring conventions).
3. Update `agent-console.py:624`'s adapter to read this new field instead
   of hardcoding `""`.

## Acceptance

- [ ] `grep -n 'PRIORITY_RE' .claude/skills/workboard/workboard.py` → pattern definition present
- [ ] `grep -n '"priority"' agent-console/agent-console.py` shows the adapter reading the scanned value, not a hardcoded `""` with the "not tracked" comment
- [ ] `cd agent-console && python3 -m pytest tests/test_parsers.py -v` → all pass, including a new test asserting a spec with `Priority: P1` in its SPEC.md renders `<option value="P1" selected>` in `_prio_select`'s output, not the blank default
