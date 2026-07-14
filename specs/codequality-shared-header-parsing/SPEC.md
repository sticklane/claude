# Shared header parsing: one Priority regex and one module loader for the skill scripts

Status: open
Breakdown-ready: true

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
   (new module, `_shared/headers.py`). Pin the import mechanism: workboard,
   list_specs, and prioritize_scan all reach `headers.py` via
   `sys.path.insert(0, .../_shared)` + `import headers` — the same
   mechanism workboard.py already uses to reach `viz`/`spec_readiness` —
   never via path-loading (`_load_module`-by-path), which would need a
   loader to load the loader. `list_specs.py` and `prioritize_scan.py`
   still need to reach `workboard.py` itself (not in `_shared`); they do
   this by importing `_load_module` from `headers` (regular import, per
   above) and calling it on `workboard.py`'s path, same as today, so
   neither file defines its own `_load_module` anymore.
2. Pin the shared regex to `\[?(P[0-3])\]?` — bracket-tolerant like
   workboard's current `PRIORITY_RE`, but range-restricted to P0-P3 (the
   toolkit's defined priority range), fixing workboard's current
   `\[?(P\d)\]?` which incorrectly accepts any digit. `prioritize_scan.py`
   adopts this shared regex in place of its own `P[0-3]` (no brackets);
   add a regression test with a `Priority: [P1]` fixture to
   `test_prioritize_scan.py`, and keep a symmetric fixture in
   `test_workboard.py` so the two suites pin the same reading. Add a range
   fixture too — `Priority: P7` — to both suites asserting it does NOT
   match (falls through to the `P2 (default)` behavior), pinning the P0-P3
   range against future widening.
3. Mirror all touched `.py` files to `antigravity/.agents/skills/` in the
   same commit and bump `.claude-plugin/plugin.json` version, per
   CLAUDE.md's mirror convention (a task's `Touch:` must list the mirror
   paths).

Note for breakdown: run pytest scoped to `.claude/skills` only — the
antigravity mirrors reuse the same test basenames, and one pytest run
spanning both trees collides on module names.

## Out of scope

- Changing what any header _means_ (P0–P3 semantics, defaults) — this is
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
      `antigravity/.agents/skills/` counterpart is empty, with one named
      exception: `prioritize_scan.py`'s module docstring may keep its
      existing standalone-install note (the sanctioned port divergence
      already live at `prioritize_scan.py:18-20` vs its antigravity
      mirror) — this is the sole permitted divergence; every other line,
      including all regex definitions, the `_load_module` import, and any
      other docstring content, must diff empty. `.claude-plugin/plugin.json`
      version is bumped in the same change.

## Parallelization

Task 02 depends on task 01 (it mirrors task 01's finalized file content) —
no parallel groups; both run solo, serialized.
