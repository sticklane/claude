# Task 03: gate template Vale stanza + toolkit self-application + e2e

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 01, 02
Priority: P1
Budget: 5 turns
Spec: ../SPEC.md (requirement R8 + end-to-end criterion)
Touch: templates/, .claude/skills/gate/, vale/styles/config/vocabularies/House/accept.txt

## Goal

The gate skill's check-script template gains an OPT-IN, commented-out
stanza titled with the literal anchor "Vale prose lint" (orientation docs
only: README.md, AGENTS.md, docs/*.md — never task files, specs/, or
skill bodies). The toolkit repo self-applies: tune the House accept list
until `vale README.md AGENTS.md` exits 0 here (this repo's jargon
belongs in the central vocabulary). Then run the spec's end-to-end check:
/prose-review over README.md producing a ranked report (or explicit
zero findings) with Vale pass + rubric pass + reader-test stumble
report, saved to ../evidence/e2e-readme-review.md.

## Acceptance

- [ ] `grep -qi 'Vale prose lint' templates/*check*` (or the gate
  template's actual location under .claude/skills/gate/ — anchor 0-hit
  everywhere today) → hit
- [ ] `vale README.md AGENTS.md` → exit 0 in this repo
- [ ] `test -s specs/prose-review/evidence/e2e-readme-review.md` → e2e report exists with all three passes (MANUAL: content)

## Progress

- 2026-07-11 — Attempt 1 (opus) returned DONE with all 3 criteria passing, but FAILED merge on R4 runtime Touch enforcement: branch changed `vale/.vale.ini.template` (6 lines, Google.EmDash disable) which is outside Touch (`templates/, .claude/skills/gate/, vale/styles/config/vocabularies/House/accept.txt`). Worker's own rationale: bare `vale README.md AGENTS.md` cannot exit 0 without centrally disabling Google.EmDash (22 errors from the house spaced-em-dash style), and accept-vocab cannot suppress a rule-level check. Done: stanza in templates/check.sh.tmpl, accept.txt tuning, e2e evidence. Remaining: achieve C2 within Touch or defer the Touch-amendment question. Branch discarded per slot machine.
