# Task 02: bin/install-vale + tracked config + House vocabulary

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
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

- [x] `bash bin/install-vale && vale --version` → exits 0 — verifier: exit 0, `vale version 3.15.1` (evidence/02-vale-install.md)
- [x] `bash bin/install-vale` (second run) → no-op, exits 0 — verifier: exit 0, `~/.vale.ini` and `vale/styles/Google` mtimes unchanged (genuine no-op)
- [x] `test -f ~/.vale.ini && grep -q '/vale/styles' ~/.vale.ini` → absolute path present — verifier: exit 0, absolute StylesPath rendered
- [x] `git check-ignore vale/styles/Google >/dev/null` → synced payload ignored; `git ls-files vale/ | grep -q accept.txt` → vocab tracked — verifier: both exit 0; 0 Google files tracked, template + accept.txt tracked

## Discovered

- 2026-07-11 — Worker's in-worktree `bin/install-vale` run left `~/.vale.ini` StylesPath pointing at the ephemeral worktree; the installer's exists-and-differs guard then preserved the stale path. RESOLVED at merge: drain re-ran `bash bin/install-vale --force` from the main checkout (StylesPath now /Users/sjaconette/claude/vale/styles). No follow-up work; noted as a known side effect of worktree-isolated installer runs.
