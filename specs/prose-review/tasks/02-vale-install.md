# Task 02: bin/install-vale + tracked config + House vocabulary

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 6 turns
Spec: ../SPEC.md (requirement R7)
Touch: bin/install-vale, vale/, .gitignore

## Goal

`bin/install-vale` idempotently installs Vale (brew), writes `~/.vale.ini`
from `vale/.vale.ini.template` substituting the ABSOLUTE resolved
StylesPath (`<this repo>/vale/styles`), sets `Packages = Google` +
vocabulary `House`, runs `vale sync`, and never clobbers a user-customized
`~/.vale.ini` without `--force`. Tracked: the template +
`vale/styles/config/vocabularies/House/accept.txt` (seed with toolkit
jargon: drain, baton, worktree, agentprof, Diátaxis, subagent, worktrees,
frontmatter, ...); synced Google payload gitignored.

## Acceptance

- [ ] `bash bin/install-vale && vale --version` → exits 0
- [ ] `bash bin/install-vale` (second run) → no-op, exits 0
- [ ] `test -f ~/.vale.ini && grep -q '/vale/styles' ~/.vale.ini` → absolute path present
- [ ] `git check-ignore vale/styles/Google >/dev/null` → synced payload ignored; `git ls-files vale/ | grep -q accept.txt` → vocab tracked
