# The workboard skill's antigravity mirror is a verbatim copy

**Trigger:** editing `.claude/skills/workboard/` (workboard.py or
test_workboard.py) and about to port the change to the antigravity mirror;
or writing a task's acceptance criteria (in `/breakdown`) for any task whose
`Touch:` includes `antigravity/` mirror paths.

Unlike the prose skills (whose `.claude/skills/*/SKILL.md` and
`antigravity/.agents/workflows/*.md` mirrors are *paraphrased* ports that must
be hand-edited), the workboard skill's two Python files are kept **byte-for-byte
identical** across the two trees:

- `.claude/skills/workboard/workboard.py` ≡ `antigravity/.agents/skills/workboard/workboard.py`
- `.claude/skills/workboard/test_workboard.py` ≡ `antigravity/.agents/skills/workboard/test_workboard.py`

So port a change by copying, not re-implementing:

```
cp .claude/skills/workboard/workboard.py        antigravity/.agents/skills/workboard/workboard.py
cp .claude/skills/workboard/test_workboard.py   antigravity/.agents/skills/workboard/test_workboard.py
```

Then confirm lockstep with `diff -q` on both pairs and run the mirror suite:
`python3 -m unittest discover -s antigravity/.agents/skills/workboard`.
Both changes still land in the **same commit** (CLAUDE.md mirror convention),
plus the `.claude-plugin/plugin.json` version bump.

Tests are stdlib-only and construct repo/session records directly (see
`make_repo_record` / `make_session`), so coverage logic is asserted at the
`attention_items()` return-value level — no real git or `~/.claude` paths.

## A new import in workboard.py can break the copy silently

If a change to `.claude/skills/workboard/workboard.py` adds a new import
resolved via a path computed from `__file__`'s own depth (e.g.
`Path(__file__).resolve().parents[N]`), check that N still lands on the
right directory once copied to `antigravity/.agents/skills/workboard/` —
the two trees are NOT the same depth from repo root
(`.claude/skills/workboard/` is 3 levels down; `antigravity/.agents/skills/workboard/`
is 4). Observed 2026-07-11: a `parents[3] / "runtimes"` import worked at
the `.claude/` location (resolves to the real repo-root `runtimes/`) but
broke at the antigravity mirror (resolved to a nonexistent
`antigravity/runtimes/`), silently `ModuleNotFoundError`-ing the entire
mirrored test suite after an otherwise-correct byte-for-byte `cp`. Fixed
by symlinking `antigravity/runtimes -> ../runtimes` (reuse, not a second
copy of the dependency) — the same reuse-via-symlink pattern the `codex/`
overlay uses for its skill directories. When a workboard.py change adds a
dependency the mirror doesn't already have a path to, a symlink at the
antigravity root is the fix, not adjusting the copied file's own path math
(which would make the two files byte-diverge).
