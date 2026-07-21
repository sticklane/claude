# Verification: task 07 — mirror script-bundle admission.py/drain_frontier.py copies

Verdict: PASS

## Per-criterion

1. Files exist — ✓
   `test -f antigravity/.agents/skills/drain/admission.py && test -f
antigravity/.agents/skills/drain/drain_frontier.py && test -f
antigravity/.agents/skills/_shared/touch_disjoint.py && test -f
codex/.agents/skills/drain/admission.py && test -f
codex/.agents/skills/drain/drain_frontier.py` → all five exist

2. Verbatim mirrors — ✓
   `diff .claude/skills/drain/admission.py
antigravity/.agents/skills/drain/admission.py` → empty
   `diff .claude/skills/drain/drain_frontier.py
antigravity/.agents/skills/drain/drain_frontier.py` → empty
   `diff .claude/skills/drain/admission.py codex/.agents/skills/drain/admission.py` → empty
   `diff .claude/skills/drain/drain_frontier.py codex/.agents/skills/drain/drain_frontier.py` → empty
   `diff .claude/skills/_shared/touch_disjoint.py
antigravity/.agents/skills/_shared/touch_disjoint.py` → empty

3. Scripts execute from their mirrored location — ✓
   `python3 antigravity/.agents/skills/drain/admission.py --help` → exit 0
   `python3 codex/.agents/skills/drain/admission.py --help` → exit 0
   `python3 antigravity/.agents/skills/drain/drain_frontier.py --help` → exit 0
   `python3 codex/.agents/skills/drain/drain_frontier.py --help` → exit 0
   (confirms `admission.py`'s `sys.path.insert(0, .../_shared)` resolves
   `touch_disjoint` both via the real antigravity copy and via codex's
   `_shared` symlink to it)

4. Mirror-parity test suite — ✓
   `for t in tests/test_antigravity_parity.sh tests/test_codex_parity.sh
tests/test_antigravity_content_parity.sh
tests/test_mirror_procedure_coverage.sh tests/test_screen_stub.sh; do
bash "$t"; done` → all exit 0

5. Live cross-reference sweep — ✓
   Re-ran `bin/human-followups --skip-pull --skip-eval` (agy sweep only).
   Prior run (before this fix) reported:
   `BROKEN .agents/skills/drain/admission.py (b) The file does not exist
at the cited path in the repo (it only exists under
.claude/skills/drain/admission.py).`
   Post-fix run reports:
   `RESOLVES .agents/skills/drain/admission.py Exists at
antigravity/.agents/skills/drain/admission.py relative to the bundle
root, and the workflow's fallback clause (lines 232-234) handles its
absence as a claim failure rather than crashing.`
   No BROKEN lines in the post-fix sweep (4/4 references RESOLVE).

## Touch-scope check

Changed files:

```
antigravity/.agents/skills/_shared/touch_disjoint.py   (new)
antigravity/.agents/skills/drain/admission.py           (new)
antigravity/.agents/skills/drain/drain_frontier.py      (new)
antigravity/.agents/skills/drain/README.md              (edited — documents the new mirrors)
codex/.agents/skills/drain/admission.py                 (new)
codex/.agents/skills/drain/drain_frontier.py             (new)
specs/drain-multi-spec-swarm/tasks/07-mirror-script-bundle-admission-copies.md (promoted draft → done)
specs/drain-multi-spec-swarm/evidence/07-mirror-script-bundle-admission-copies.md (this file)
```

Matches the task's `Touch:` header plus the task/evidence files themselves.
No `.claude/` source files touched (mirrors only), no unrelated files
changed.

## Gates

Full repo test suite (`for t in tests/test_*.sh; do bash "$t"; done`) run
as part of closing this task — see session log; all green.
