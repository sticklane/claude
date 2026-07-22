# Task 03: Judge input assembly and blinding

Status: in-progress
Depends on: 02
Priority: P1
Budget: 16 turns
Rigor: prototype
Spec: ../SPEC.md (design statement 6; controls; acceptance criterion 4)
Touch: evals/headtohead/run.sh, evals/headtohead/judge-rubric.md, evals/headtohead/lib/

## Goal

`run.sh --dump-judge-input` assembles the single-call rubric-judge input for a
run and prints it instead of scoring. The assembled input contains the run's diff
and the canonical, keyword-stripped brief — and NOTHING that leaks the arm: no
word-boundary match for the ultracode keyword, no arm name, and no occurrence of
this plugin's name. Blinding is asserted by the script against the ASSEMBLED
input (not the template). The rubric is a single-call 1-5 maintainability judge,
correctness-independent, that never sees cost, wall-clock, or arm.

## Touch

Owns the judge path in `run.sh` and the rubric file. Do NOT touch the dry-run/
config core (01), the session-run/results path internals (02) beyond consuming
the diff a run produces, or the real fixtures (04-06).

## Steps

1. Write `judge-rubric.md`: single-call 1-5 maintainability rubric; inputs are
   the diff + canonical keyword-stripped brief only.
2. Implement judge-input assembly: take a run's diff and the canonical brief
   (the arm-neutral brief, never either arm's as-run brief text) and build the
   judge prompt.
3. Implement `--dump-judge-input`: print the assembled input and assert it holds
   no word-boundary match for the ultracode keyword, any arm name, or the plugin
   name; exit non-zero if any leaks.
4. Mechanical acceptance run (prototype rigor) — confirm the commands below.

## Acceptance

- [ ] `bash evals/headtohead/run.sh --task fixture --arm U --seeds 1 --dump-judge-input` → the assembled judge input contains no word-boundary match for the ultracode keyword, any arm name, or the plugin's name (asserted by the script); exits 0
- [ ] the same dumped judge input contains the run's diff and the canonical keyword-stripped brief (structural presence check on the dump)
