# Shared header parsing: one Priority regex and one module loader for the skill scripts

Status: open

## Problem

The same `Priority:` task-file header is parsed by two different regexes
in the toolkit's own scripts:

- `.claude/skills/prioritize/prioritize_scan.py:31` —
  `re.compile(r"^Priority:\s*(P[0-3])", re.MULTILINE)` (no brackets).
- `.claude/skills/workboard/workboard.py:229` —
  `PRIORITY_RE = re.compile(r"^Priority:\s*\[?(P\d)\]?", re.MULTILINE)`
  (optional brackets, any digit).

A header written `Priority: [P1]` — the bracketed shape `STATUS_RE` on the
line above it explicitly tolerates for `Status:` — reads as P1 in
`/workboard` but silently falls through to the `P2 (default)` in
`/prioritize`. The same header must not read two ways across the toolkit;
`prioritize_scan.py` already imports `STATUS_RE` from workboard
(`prioritize_scan.py:47`), so the divergence is accidental, not a design
choice.

Second, the importlib bootstrap is copy-pasted: `_load_module` is
byte-identical in `.claude/skills/list-specs/list_specs.py:24-28` and
`.claude/skills/prioritize/prioritize_scan.py:35-39`, and both then repeat
the same `spec_from_file_location(... "workboard/workboard.py")` dance to
reach `scan_toolkit_specs`/`read_text`/`STATUS_RE`. Loading `workboard.py`
also executes its top-level side effects (`sys.path.insert` + `import viz`,
`workboard.py:44-45`), which every consumer silently inherits.
`.claude/skills/_shared/` already exists precisely to hold shared logic
(`spec_readiness.py`'s own docstring says its purpose is avoiding drift).

## Approach

1. Move the header regexes (`STATUS_RE`, `PRIORITY_RE`, and workboard's
   other `Key: value` header regexes as far as consumers need them) and a
   single `_load_module`/loader helper into `.claude/skills/_shared/`
   (new module, e.g. `_shared/headers.py`), imported by workboard,
   list_specs, and prioritize_scan the same way `viz`/`spec_readiness` are.
2. `prioritize_scan.py` adopts the shared (bracket-tolerant) Priority
   regex; add a regression test with a `Priority: [P1]` fixture to
   `test_prioritize_scan.py`, and keep a symmetric fixture in
   `test_workboard.py` so the two suites pin the same reading.
3. Mirror all touched `.py` files to `antigravity/.agents/skills/` in the
   same commit and bump `.claude-plugin/plugin.json` version, per
   CLAUDE.md's mirror convention (a task's `Touch:` must list the mirror
   paths).

Note for breakdown: run pytest scoped to `.claude/skills` only — the
antigravity mirrors reuse the same test basenames, and one pytest run
spanning both trees collides on module names.

## Out of scope

- Changing what any header *means* (P0–P3 semantics, defaults) — this is
  parse-consistency only.
- agent-console's parsers (it imports workboard already and follows along
  for free).

## Acceptance criteria

- [ ] `grep -rn "Priority:" .claude/skills/*/[a-z_]*.py | grep -c "re.compile"`
      returns 1 — a single compiled Priority regex definition, in
      `_shared/`, imported everywhere else.
- [ ] A fixture task file containing `Priority: [P1]` yields P1 (not the
      P2 default) from both `prioritize_scan.py` and `workboard.py`
      scanning code paths, asserted by named tests in both test files.
- [ ] `grep -c "def _load_module" .claude/skills/list-specs/list_specs.py .claude/skills/prioritize/prioritize_scan.py`
      shows 0 for both (loader lives in `_shared/` only).
- [ ] `python3 -m pytest .claude/skills` exits 0 (do not widen the run to
      `antigravity/` — mirror basenames collide).
- [ ] `diff -r` of every touched `.py` against its
      `antigravity/.agents/skills/` counterpart is empty, and
      `.claude-plugin/plugin.json` version is bumped in the same change.
