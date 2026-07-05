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
