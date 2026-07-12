# Task 02: Fix the toolkit-owned dispatch sources

Status: done
Depends on: 01
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirement R2)
Touch: .claude/skills/, .claude/agents/, antigravity/, codex/.agents/skills/, .claude-plugin/plugin.json, specs/untyped-agent-fanout/EVIDENCE.md

## Goal

Every toolkit-owned dispatch site EVIDENCE.md names has a landed text
fix — a typed pinned agent named, or an explicit model/effort override —
referenced by commit in EVIDENCE.md; every non-toolkit site (harness
default, one-off human prompt) has a written no-fix disposition there
instead.

## Touch

Skill/agent text and mirrors only, driven by EVIDENCE.md's list. Do NOT
edit `.claude/rules/token-discipline.md` — task 03 owns the doctrine, and
this task's fixes are site-local text changes. If a fix edits any
`.claude/skills/*` or `.claude/agents/*` file, the same commit carries
the `antigravity/` mirror and the plugin version bump (CLAUDE.md mirror
rule); prose-skill mirrors get paraphrased ports with content-coverage
checks, never byte-diffs.

## Steps

1. Read EVIDENCE.md; list the toolkit-owned sites.
2. Per site: apply the tier-appropriate fix per token-discipline's
   "Freehand fan-out" and "Model and effort matching" rungs; mirror; note
   the commit hash back in EVIDENCE.md's row.
3. For non-toolkit sites, write the disposition rows.
4. If any `.claude/agents/*.md` changed, remember agents are enumerated
   in plugin.json (schema requirement).

## Acceptance

- [x] Every EVIDENCE.md toolkit-owned row carries a commit hash; every other row a disposition (`grep -c 'unresolved\|no-fix\|[0-9a-f]\{7\}' specs/untyped-agent-fanout/EVIDENCE.md` covers all rows — verify by reading, cite the count) — verifier PASS (evidence/02-fix-dispatch-sources.md): grep→149; all 137 per-chain rows carry either `0ceb3e3` (129 Site-1) or `no-fix` (8 Site-2), 0 bare; Site 1 section cites commit `0ceb3e3`, Site 2 section states the no-fix disposition + reasoning.
- [x] If `.claude/skills/*` or `.claude/agents/*` changed: mirrors updated (content-coverage grep per changed artifact, stated in EVIDENCE.md), `git show $(git merge-base HEAD main):.claude-plugin/plugin.json | grep '"version"'` differs from the working-tree value, and `claude plugin validate .` → passes — verifier PASS: drain/reference.md changed; EVIDENCE states hub-tier doctrine present in both mirrors (codex SKILL L146, antigravity workflow L60) and reference.md has no ported mirror; plugin 0.8.53→0.8.54 (differs); `claude plugin validate .` → "✔ Validation passed".
- [x] If any of `.claude/skills/{drain,build,autopilot,evals}/SKILL.md` changed: the matching `codex/.agents/skills/<name>/SKILL.md` (real content, not a symlink) updated in the same commit (CLAUDE.md codex leg) — N/A: verifier confirms `git diff --name-only ed7c305 HEAD` touched no such SKILL.md (only drain/reference.md), so the codex-leg trigger does not fire.
- [x] `bash evals/lint-ultra-gate.sh` → passes if any of the four ultra-path skills (critique, drain, build, idea) were among the fixed sites — verifier PASS: drain was fixed; `bash evals/lint-ultra-gate.sh` → "OK — all ultra mentions gated in 4 files", exit 0.

## Decisions

- Site 1 relaunch tier: pinned the successor generation to deep-tier `opus`
  (drain-hub default, "or below" a repo's `.claude/runtime.md` pins) per the
  Wake-economics section already in reference.md, rather than another tier.
  Reversible: re-edit the `<tier alias>` bullet in reference.md L1057-1069.
- Site 2 classified no-fix (not a text fix): the traced dispatches are freehand
  home-orchestrator invocations, not toolkit skill dispatch sites, and the
  toolkit points governing that class (assessor scout-tier, gate critic,
  prose-review reader-test session-tier) are already correctly tiered; the
  governing freehand-fan-out doctrine is task 03's `token-discipline.md` (out
  of this task's Touch). Reversible: replace the Site 2 EVIDENCE disposition
  with a landed fix if a skill dispatch site is later identified.
