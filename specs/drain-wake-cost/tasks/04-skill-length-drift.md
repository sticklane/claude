# Task 04: extract drain SKILL.md heavy prose to reference.md (< 500 lines)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Promotion-ready: true
Promoted-by-run: attended-2026-07-12-sjaconette
Discovered-from: specs/drain-wake-cost/tasks/01-drain-skill-text.md
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, antigravity/.agents/workflows/drain.md, codex/.agents/skills/drain/SKILL.md, .claude-plugin/plugin.json

## Goal

drain SKILL.md (665 lines today) drops below 500 by RELOCATING heavy
prose to reference.md — content-equivalent moves with section-lookup
pointers left behind (the "load only the named section" pattern the
skill already uses, 3 sites today), never deletion of machinery.
Maintainer decision 2026-07-12 (Steven, interview): extraction
authorized; the alternative (documented exemption) was rejected.
Candidate relocations: long rationale/economics passages whose
procedures stay, verbose sub-procedures already summarized at their call
sites. Execution-critical contracts stay in the first 30 lines per
conventions. The antigravity and codex ports get content-equivalent
pointer adjustments ONLY where their text mirrors a relocated passage
(paraphrased ports — content coverage, not byte-diff). Run the critic on
the diff before close-out (docs/memory/skill-retirement-checklist.md
pattern: a clean grep does not prove semantic completeness).

<!-- PLAN (worker, task 04):
Goal: shrink .claude/skills/drain/SKILL.md 665 -> <500 by RELOCATING heavy
rationale/economics prose + already-summarized sub-procedures to reference.md,
leaving section-lookup pointers. No machinery deleted. First 30 lines + all
load-bearing procedure stay in SKILL.md.
Relocation candidates:
  M1 Name-the-shell (52-57) -> reference.md new "Startup advisories" + pointer
  M2 Startup session sweep (59-64) -> same reference section + pointer
  M3 Hub-economics advisory (66-77) -> same reference section + pointer
  M4 Wake economics block (162-175) -> reference.md new "Wake economics" + summary/pointer in step2
  M5 max(2,6-W) rationale (382-389) -> reference.md "Baton pass" + rule stays
  M6 Spec-completion review detail (517-576) -> compress to contract+pointer (detail already in reference "Spec-completion review worker")
  M7 Stub intake bullets (446-490) -> compress to contract+pointer (detail already in reference "Stub intake")
  M8 DONE-bullet wake/push-guard prose (254-289) -> trim rationale, keep contract
Rule: only remove SKILL text that is (a) relocated verbatim/equiv to reference.md
or (b) already present in reference.md (verified before removal).
Ports: antigravity + codex get pointer/paraphrase sync ONLY where they mirror a moved passage.
Gates: wc -l <500; evals/lint-ultra-gate.sh OK; claude plugin validate .; awaited critic READY; plugin.json 0.8.50 -> 0.8.51.
-->

## Original report

> `.claude/skills/drain/SKILL.md` is now 547 lines, over the "well under
> 500 lines" CLAUDE.md convention — it was already 510 before this task,
> and R3/R4/R6 required additive prose while forbidding machinery
> removal, so it couldn't be reduced here; a future pass could relocate
> some heavy prose to reference.md, but that would alter what the SKILL
> body teaches and is out of this task's scope. Worth tracking as drift
> on the drain skill.

## Acceptance

- [x] `wc -l < .claude/skills/drain/SKILL.md` → < 500 (665 at authoring) — now 495
- [x] `bash evals/lint-ultra-gate.sh` → OK AND `claude plugin validate .` → passes — both green (ultra markers untouched at Ultra path; plugin validate: "Validation passed")
- [x] Every relocated passage reachable via a SKILL.md pointer naming its reference.md heading — critic verified all pointers resolve to existing reference.md headings (Gen-1 startup advisories, Wake economics, Push guard (canonical), Rolling-window admission & merge (R1–R4), Exit checklist (seven sections), plus pre-existing Owner lease / Worker prompt / Tournament / Baton pass / Stub intake / Spec-completion review worker)
- [x] Awaited critic on the diff returns READY (no semantic-loss findings) — READY; one low-confidence note (tournament role markers templated to tN) closed by enumerating the three explicit markers in reference.md's Tournament "Generate" block
- [x] `git show HEAD -- .claude-plugin/plugin.json | grep -q '^+.*"version"'` right after this task's commit → version bumped relative to base — 0.8.50 → 0.8.51, in HEAD
