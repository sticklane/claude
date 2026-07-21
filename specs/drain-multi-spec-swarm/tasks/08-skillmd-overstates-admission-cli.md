Status: draft
Discovered-from: specs/drain-multi-spec-swarm/evidence/spec-review.md
Spec: ../SPEC.md
Blocking: no

# SKILL.md overstates what the admission.py CLI actually does

`.claude/skills/drain/SKILL.md`'s "Claim the owner lease" paragraph says
`python3 .claude/skills/drain/admission.py --frontier <...>` "executes the
DRAIN-OWNER.md git-CAS lease claim ... AND the two cross-spec checks it
owns." In fact `admission.py`'s `main()` only calls `claim_specs` +
`admit_tasks` and prints `{claimed_specs, admitted_tasks}` JSON — it never
calls `git_cas_claim`/`format_owner` or writes DRAIN-OWNER.md.
reference.md's own "Admission command" paragraph already states the
narrower, correct scope ("The module owns ONLY R1 spec-claim eligibility
and the R2 two-level cap"). Risk: an orchestrator taking SKILL.md
literally could believe the lease file is written by this one CLI call
when it is not. (Reported by the drain-multi-spec-swarm spec-completion
review; vet/rewrite before promoting — the correct minimal wording
depends on whether the orchestrator is meant to call `git_cas_claim`
separately, which needs `run_token`/`owner_text`/`spec_dir` the CLI
doesn't currently accept.)

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
