# Critique findings — workboard-auto-triage

Verdict: NOT READY (drain gen 7 critique intake, 2026-07-12)

1. **Missing antigravity mirror + plugin.json bump obligation (conf 95).** Spec
   changes `.claude/skills/workboard/SKILL.md` and `workboard.py` + tests but has
   zero mention of `antigravity/` or `plugin.json`. A workboard antigravity mirror
   exists (`antigravity/.agents/skills/workboard/{SKILL.md,workboard.py,test_workboard.py}`);
   CLAUDE.md requires the mirror update + `plugin.json` version bump in some task's
   `Touch:`. Without it `/breakdown` ships the classifier/SKILL changes un-mirrored
   and un-bumped. Fix: add a closing task/AC whose `Touch:` includes the four
   `antigravity/.agents/skills/workboard/*` files and `.claude-plugin/plugin.json`
   (bump) plus the mirror cross-ref sweep.

2. **R4's line citations are wrong (conf 88).** R4 says `active_toplevels` is at
   `workboard.py:818-819` (actually inside `_live_session_ids_from_pids`; real build
   is ~line 1292) and that the launch toplevel is "computed the same way
   workboard.py:961 does" (961 is unrelated Fleet status code; the only
   `--show-toplevel` call is line 1839). A worker reads the wrong code. `_actively_covered`
   (1256) is the one accurate anchor. Fix: correct refs to 1292; note launch-cwd
   toplevel must be newly computed via `run_git(launch_cwd,"rev-parse","--show-toplevel")`.

3. **R0 is stale — module already exists (conf 70).** `.claude/skills/_shared/spec_readiness.py`
   and `test_spec_readiness.py` already exist on disk, so R0's "if it does not yet
   exist, this spec creates it… sequence them" apparatus is dead weight and may cause
   `/breakdown` to invent a false cross-spec ordering constraint. Fix: collapse R0 to
   "import the existing `open_questions_unresolved` from `_shared/spec_readiness.py`;
   do not re-touch it," drop the sequencing clause.

Non-blocking confirmations: workboard is not ultra-path (no lint-ultra-gate needed);
new literals `triage`/`breakdown_gate`/`verify_archive` absent from workboard.py;
end-to-end criterion correctly human-run.
