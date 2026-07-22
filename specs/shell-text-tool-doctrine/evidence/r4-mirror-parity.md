# R4 — rules-file mirror parity finding

`.claude/rules/*.md` files are not mirrored to `antigravity/` or `codex/`.

Verified: neither tree contains a `rules` directory.

```
$ find antigravity -iname 'rules' -maxdepth 3
$ find codex -iname 'rules' -maxdepth 3
```

Both commands returned no matches. `mirror-procedure-discipline.md` and
`mirror-verification.md` govern skill/procedure mirroring
(`.claude/` → `antigravity/` → `codex/`); rules files sit outside that
port chain entirely — there is no rules mirror to keep in lockstep.

Conclusion: this task's new file, `.claude/rules/shell-text-tools.md`,
rides no mirror. No `antigravity/` or `codex/` change is required or
created by this task.
