Status: done
Discovered-from: specs/drain-multi-spec-swarm/tasks/03-mirror-and-version-bump.md
Spec: ../SPEC.md
Priority: P2
Touch: antigravity/.agents/skills/drain/admission.py, antigravity/.agents/skills/drain/drain_frontier.py, antigravity/.agents/skills/drain/README.md, antigravity/.agents/skills/_shared/touch_disjoint.py, codex/.agents/skills/drain/admission.py, codex/.agents/skills/drain/drain_frontier.py
Blocking: no

# Ship admission.py/drain_frontier.py copies in the antigravity script bundle

`antigravity/.agents/skills/drain/` (the script-bundle convention its
README documents, used by `screen-stub.sh`) carried no `admission.py` or
`drain_frontier.py` copy, so the drain workflow's mirrored shell-out
took the documented by-hand fallback until copies shipped; the codex
overlay inherited the same gap. (Worker-reported discovery from the task
03 mirror port; a 2026-07-20 `bin/human-followups` antigravity live
cross-reference sweep confirmed `.agents/skills/drain/admission.py` as
BROKEN — cited by `antigravity/.agents/workflows/drain.md` and
`codex/.agents/skills/drain/SKILL.md` but absent from both mirrored
trees.)

Fix: verbatim-copied `admission.py` and `drain_frontier.py` from
`.claude/skills/drain/` into `antigravity/.agents/skills/drain/`
(matching the existing `screen-stub.sh` mirror convention) and into
`codex/.agents/skills/drain/` (real content there, not a symlink, per
CLAUDE.md's port-chain bullet). `admission.py`'s only cross-module
dependency, `touch_disjoint.py`, was copied into
`antigravity/.agents/skills/_shared/` — codex inherits it automatically
since `codex/.agents/skills/_shared` already symlinks to antigravity's
`_shared/`. `drain_frontier.py`'s dependency, `headers.py`, was already
present in `_shared/` under both trees. The README was updated to
document all three mirrored scripts and their `_shared/` dependencies.

## Acceptance

- [x] `test -f antigravity/.agents/skills/drain/admission.py && test -f
    antigravity/.agents/skills/drain/drain_frontier.py && test -f
    antigravity/.agents/skills/_shared/touch_disjoint.py && test -f
    codex/.agents/skills/drain/admission.py && test -f
    codex/.agents/skills/drain/drain_frontier.py` → all five exist
- [x] `diff .claude/skills/drain/admission.py
    antigravity/.agents/skills/drain/admission.py` → empty (verbatim
      mirror, matching the `screen-stub.sh` convention); same for
      `drain_frontier.py` and for both codex copies
- [x] `python3 antigravity/.agents/skills/drain/admission.py --help` and
      `python3 codex/.agents/skills/drain/admission.py --help` both exit
      0 (dependency on `../_shared/touch_disjoint.py` resolves through
      the real copy / symlink respectively)
- [x] `python3 antigravity/.agents/skills/drain/drain_frontier.py --help`
      and the codex equivalent both exit 0
- [x] `for t in tests/test_antigravity_parity.sh tests/test_codex_parity.sh
    tests/test_antigravity_content_parity.sh
    tests/test_mirror_procedure_coverage.sh tests/test_screen_stub.sh; do
    bash "$t"; done` → all exit 0
- [x] Re-running `bin/human-followups --skip-pull --skip-eval`'s agy
      sweep reports `RESOLVES .agents/skills/drain/admission.py` (no
      BROKEN lines), confirmed live 2026-07-20
