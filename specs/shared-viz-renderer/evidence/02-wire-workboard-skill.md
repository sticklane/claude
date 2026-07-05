# Evidence: 02-wire-workboard-skill

Verifier: agentic:verifier, base commit 05d8d36786cd1c9d9d51abd450e3a645faa3ddd3, verdict PASS.

- `python3 -m pytest .claude/skills/workboard/test_workboard.py` → 39 passed, including
  `TestSessionStartTs`, `TestSessionTimelineRendering`, `TestSpecDagRendering`.
- End-to-end smoke render (`workboard.py . --out ... --quiet --stale-days 7`) on the real
  repo tree: `viz-bar`=9, `<path`=1, `var(--viz-`=6 hits in the rendered HTML.
- workboard.py diff confirmed: `sys.path.insert(0, str(SCRIPT.parent.parent / "_shared"))`
  + `import viz`; both the per-repo Sessions table and the orphan-sessions table replaced by
  `viz.timeline()` (`_session_timeline_html`); per-spec `viz.dag()` SVGs via `_spec_dag_html`;
  `viz.VIZ_CSS` injected into `<style>` via the `viz_css` template placeholder.
- Touch constraint honored: diff vs base touches only workboard.py, test_workboard.py, and
  this task file — no changes to `.claude/skills/_shared/` or `.claude/skills/fleet/reference.md`.
- Pre-existing gate `tests/test_workboard_render.sh` still fails with exactly the same two
  known pre-existing assertions ("code.cmd with no adjacent copy button", "cmd is not
  cwd-independent") — no new failures introduced.
