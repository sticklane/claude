# Critique findings — retire-static-dashboards (NOT READY)

Recorded by drain critique intake, gen 6, Run-token e83f34f07094a4fa, 2026-07-12.
Critic verdict: **NOT READY**. Fix these, then re-run /critique to earn `Breakdown-ready: true`.

## 1. [BLOCKER, conf 92] Recursive `grep -rn '.claude/'` sweeps transient worktrees — non-deterministic, unpassable
R1 (SPEC.md:62-63) and the acceptance criterion (SPEC.md:153-158) anchor on
`grep -rn '\bfleet\b' .claude/ antigravity/ docs/ AGENTS.md CLAUDE.md .claude-plugin/`.
The recursive `.claude/` arm descends into `.claude/worktrees/` (10 live worktrees = full repo
copies). Measured: **2524** `fleet` matches under `.claude/worktrees/` vs **9** git-tracked.
The AC "shows only (a)/(b)/(c)" can never hold in the main checkout, and the R1 inventory varies
run-to-run. Smallest fix: replace every recursive `grep -rn`/`grep -rl` over `.claude/` with
`git grep -n` (auto-excludes worktrees) or add `--exclude-dir=worktrees`, in R1 and the AC.
Single-file greps (SPEC.md:144-150, 161-164) are fine as-is.

## 2. [conf 78] Two closing ACs gate on tools an unattended drain worker cannot use, no manual-pending path
- SPEC.md:170-173 ("running `/fleet` in a session with a background agent prints the markdown table,
  no file written") requires an attended session with live harness TaskList + skill invocation —
  a drained worker has none. Mark explicit manual-pending per
  docs/memory/unattended-worker-tool-limits.md.
- SPEC.md:167-169 names `bash evals/run.sh`, the paid model-session eval runner (`/evals`,
  `disable-model-invocation: true`); CLAUDE.md forbids drained tasks gating on it. Zero
  fleet/--out/--emit-fleet-css fixtures exist under evals/ (vacuous anyway). Reword to a static
  `git grep` over the evalset fixtures.

## 3. [conf 65] R1 edits drain/SKILL.md (ultra-path) but no AC requires the ultra-gate
R1 (SPEC.md:71) rewords .claude/skills/drain/SKILL.md:366. `drain` is one of the four ultra-path
skills; CLAUDE.md mandates `bash evals/lint-ultra-gate.sh` before committing. No AC carries it.
Low risk (prose far from any "ultra" marker) but the obligation is unstated. Add an AC:
`bash evals/lint-ultra-gate.sh` exits 0.

## Verified clean (no finding)
R6 mirror obligations complete (codex/antigravity drain artifacts carry no `fleet` reference, so the
drain edit needs no counterpart); all eight R1 prose anchors present; workboard/viz/fleet single-file
anchors all present as claimed; plugin.json 0.8.48 makes R7's bump satisfiable.

## Triage 2026-07-13 (attended; Steven approved REVISE)

Verdict: REVISE (smallest of the batch). Edits before re-critique: (1) replace the recursive greps with `git grep` in R1 and the AC; (2) mark the `/fleet` e2e criterion manual-pending and swap `evals/run.sh` for a static `git grep` over eval fixtures; (3) add `bash evals/lint-ultra-gate.sh` as an AC. Verified: not superseded — fleet/reference.md still exists; workboard.py still carries render_html/--out/--actions-out (lines 2444, 2841, 2915).

## Re-critique 2026-07-13 (drain critique intake, run b4adb88f) — still NOT READY, approved plan not yet applied

`git log -- specs/retire-static-dashboards/SPEC.md` shows no commit since
the triage above — SPEC.md is byte-identical to the state that produced
this file's prior NOT READY verdict. Skipping a redundant full critic
dispatch on unchanged content per token-discipline's "cheap before
expensive" — the three approved triage edits above (smallest of the batch)
are the recovery path, unchanged. This spec's critique intake is spent for
this run.
