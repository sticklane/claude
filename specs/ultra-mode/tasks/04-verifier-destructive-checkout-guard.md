# Task 04: guard the "delete marker → re-run → restore" test pattern against uncommitted work

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: done
Depends on: none
Spec: ../SPEC.md
Discovered-by: 02-skill-ultra-paths.md

## Goal

verbatim worker report — vet/rewrite before promoting:

> The verifier agent's "delete the marker, re-run, restore with `git
> checkout`" test pattern is destructive when run against *uncommitted*
> work (HEAD == base): the checkout permanently discarded an in-progress
> `## Ultra path` section during the first verification pass (it bit both
> my own acceptance-check block and the verifier). It matters because
> `/build`'s step-3 verification routinely runs before the implementation
> is committed — the acceptance criterion's "restore after" wording
> silently assumes committed state. Worth a guard note in the verifier
> agent or lint-test guidance (stash/copy instead of `git checkout` on a
> possibly-dirty tree).

## Resolution (done)

Added a guard to step 2 of both the verifier agent (`.claude/agents/verifier.md`)
and its antigravity mirror (`antigravity/.agents/skills/verifier/SKILL.md`, same
commit per the mirror convention): when exercising a criterion means mutating a
tracked file (deleting a marker to prove it regenerates, rewriting a fixture),
restore it by copying it aside and moving it back — never `git checkout` /
`git restore <file>`, which reverts the entire file to its committed state and
silently discards the uncommitted implementation `/build` is verifying. An
adversarial review confirmed the guard is technically sound, the copy-aside
alternative is safe and sufficient (correctly not `git stash`, which is broader),
and the two copies are semantically equivalent.
