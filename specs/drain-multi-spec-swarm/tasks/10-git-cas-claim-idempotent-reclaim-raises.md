Status: draft
Discovered-from: specs/drain-multi-spec-swarm/evidence/spec-review.md
Spec: ../SPEC.md
Blocking: no

# git_cas_claim can raise uncaught on an idempotent re-claim

`.claude/skills/drain/admission.py`'s `git_cas_claim` (around line 262)
commits via `_git(..., check=True)` with no output capture. If invoked
when DRAIN-OWNER.md already holds byte-identical content at HEAD (same
run_token/generation/spec, i.e. re-affirming a lease this run already
owns), `git commit` exits non-zero ("nothing to commit") and the call
raises an uncaught `CalledProcessError` instead of returning True/treating
it as "already own it". Not reached by `admission.py`'s own `main()`
(which never calls `git_cas_claim`) or by any current test fixture (each
uses a distinct token), so exposure depends on how an orchestrator retries
lease-claim calls in practice — not confirmed to be hit in production, but
plausible on any re-claim-after-batch-interview or re-entry path.
Suggested guard: treat a no-op commit as success (check `git diff --cached
--quiet` before committing, or catch the nothing-to-commit case and fall
through to the confirm-read) rather than letting the exception propagate.
(Reported by the drain-multi-spec-swarm spec-completion review; vet/
rewrite before promoting.)

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
