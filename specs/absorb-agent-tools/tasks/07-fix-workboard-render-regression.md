Status: draft
Discovered-from: specs/absorb-agent-tools/tasks/03-repo-wiring-and-pointers.md
Spec: ../SPEC.md
Blocking: yes

# Fix tests/test_workboard_render.sh regression (copy button / cwd-independent cmd)

`tests/test_workboard_render.sh` fails on `main` at both `b92f98f` (wcc-01 merge point) and current HEAD — `.claude/skills/workboard/workboard.py`'s rendered actions-script command (`bash <tmpdir>/a.sh`) has no adjacent copy button and isn't recognized as cwd-independent by the test's regex (`^(cd /|claude |python3 /|git -C /)`), a real regression in previously-verifier-PASSed wcc-01 work that blocks any task whose acceptance runs the full `tests/test_*.sh` suite.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
