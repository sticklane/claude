# Verification: Task 02 — workboard remove static-HTML fallback

Verdict: PASS

## Scope check

- Base commit: f433ee3. Commits under test: 926d436, 7f5f01a.
- `git show --stat` for both commits: only `.claude/skills/workboard/workboard.py`
  (926d436: +9/-969) and `.claude/skills/workboard/SKILL.md` (7f5f01a: +7/-3)
  were touched. Matches Touch exactly. No other files changed.
- Task file diff (`git diff f433ee3 -- specs/.../02-....md`): only the
  `<!-- PLAN ... -->` comment block was added after the header fields. Status
  line unchanged ("in-progress"), acceptance checkboxes unchanged (still
  `- [ ]`, unticked). This is an allowed append (plan comment block); no
  criterion text, Touch line, or other prose was altered.

## Acceptance criteria

1. `grep -n "render_html\|build_actions_script\|--out\|--actions-out" .claude/skills/workboard/workboard.py`
   → exit 1, no matches. **PASS**

2. `grep -n "^TEMPLATE = " .claude/skills/workboard/workboard.py`
   → exit 1, no match. **PASS**

3. Saved SPEC.md's "## Reachability check script" verbatim to
   `/tmp/orphan_check_v.py`, ran
   `python3 /tmp/orphan_check_v.py .claude/skills/workboard/workboard.py`
   → printed `clean`, exit 0. **PASS**

4. `grep -n "Fallback (machines without agent-console)" .claude/skills/workboard/SKILL.md`
   → exit 1, no match. **PASS**

5. `git grep -c 'fleet/reference\.md' .claude/skills/workboard/workboard.py`
   → exit 1 (grep -c prints nothing / no match, i.e. 0 occurrences).
   **PASS**

6. `python3 .claude/skills/workboard/workboard.py --json` → ran to completion
   (exit 0, printed scan progress lines to stderr-like status then JSON to
   stdout); piped output through `json.load()` → parsed successfully as a
   dict. **PASS**

## Independent checks

(a) `python3 -c "import ast; ast.parse(open('.claude/skills/workboard/workboard.py').read())"`
→ "parses ok", no SyntaxError. **PASS**

(b) SKILL.md diff (7f5f01a) confirmed: the "Fallback (machines without
agent-console)" bullet was replaced with "If the live server genuinely
cannot start ... report the startup error and what to check ... Do not
fall back to writing a static HTML file — the scanner has no
file-output mode; its only outputs are `--json` ... and a one-line
summary." Matches the task's Step 5 / Goal instruction. **PASS**

(c) No genuine keeper over-deleted: criterion 3's reachability check (clean,
exit 0) and criterion 6 (--json runs, valid JSON, no NameError) jointly
prove no live code path references a deleted name. Spot-checked
remaining top-level defs/constants in workboard.py (SCRIPT,
STALE_DAYS_DEFAULT, DRAIN_WINDOW_DEFAULT, find_repos, default_roots,
git_info, scan_toolkit_specs, ready_items, scan_kiro_specs,
scan_handoffs, resolve_repo_runtime, etc.) — all plausible live
scan/json-path helpers, nothing render/HTML-related remains. File is
1959 lines (was 2928 pre-edit per the -969 delta), consistent with only
the HTML path being removed.

## Out of scope (not graded, per instructions)

`test_workboard_render.sh`, `test_workboard_actionability.sh`,
`test_workboard.py`'s render_html-calling methods, and
`test_antigravity_content_parity.sh`/`test_fleet_css_drift.sh` were not run
— they belong to sibling tasks 03/04/05 and are expected to be broken by
this task's deletions.

## Overall

All 6 acceptance criteria PASS. All 3 independent checks PASS. Touch scope
respected exactly. Task file append-only (plan block added only). No scope
creep detected.
