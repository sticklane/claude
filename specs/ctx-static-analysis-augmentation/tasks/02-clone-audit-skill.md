# Task 02: standalone clone/duplicate-detection skill + in-repo fixtures

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: done
Depends on: none
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirement R3; fork F2 decided (iii))
Touch: .claude/skills/clone-audit/, antigravity/.agents/skills/clone-audit/, .claude-plugin/plugin.json, specs/ctx-static-analysis-augmentation/fixtures/, specs/ctx-static-analysis-augmentation/tests/, codex/.agents/skills/clone-audit

## Goal

A new standalone repo-audit skill (proposed directory name `clone-audit`;
the author may pick a clearer name — this choice is local to this task) that
documents a supported recipe for producing a clone/duplicate-code report for
a mixed TS/Go repo, per F2's decided option (iii) — separate from both `ctx`
and `harness-audit`. The recipe is proven by an in-repo fixture: two
committed fixture files containing a known duplicated function (one TS pair,
one Go pair) that the documented recipe rediscovers, asserted by a runnable
check committed in this repo. The fooszone three-homography case is recorded
in the recipe docs as a non-normative worked example only.

## Touch

In scope:
- `.claude/skills/clone-audit/SKILL.md` (+ `reference.md` for the per-stack
  recipes and worked example) — a new skill.
- `antigravity/.agents/skills/clone-audit/` — the antigravity mirror (a new
  skill must be mirrored in the same commit per CLAUDE.md's port-chain
  convention; it is a paraphrased port, not a byte copy —
  docs/memory/workboard-mirror-verbatim.md).
- `.claude-plugin/plugin.json` — bump `version` (skill behavior added;
  skills stay manifest-free so no skills-manifest edit is needed).
- In-repo fixture + test files under this spec's directory (the TS pair, the
  Go pair, and the runnable rediscovery check).

OUT of scope, do NOT touch: `.claude/skills/ctx/SKILL.md` (that is R1/R4,
gated), `harness-audit` (F2 rejected folding clone detection into it), and
any `ctx` crate code.

## Steps

1. Choose a clone detector reachable without a persistent install where
   possible: `npx jscpd` for the JS/TS pair and Go `dupl` (`go run` /
   `go install golang.org/x/tools/...`-class) or `jscpd`'s Go support for
   the Go pair. Record the exact command the recipe recommends per stack.
2. Write the two fixture pairs first (they are the "failing" artifact the
   recipe must rediscover): a `.ts` file whose duplicated function is cloned
   into a second `.ts` file, and a `.go` file whose duplicated function is
   cloned into a second `.go` file, each an obvious, above-threshold clone.
3. Write the runnable rediscovery check (a shell test or script) that runs
   the documented recipe against the fixtures and asserts BOTH the TS clone
   and the Go clone are reported. Confirm it FAILS before the recipe/skill
   exists, then passes once wired.
4. Author `SKILL.md` (third-person description with trigger phrases;
   command name from the directory) and `reference.md` (per-stack recipes +
   the fooszone three-homography worked example, noting the .tsx/.ts
   clustering is threshold-dependent — non-normative).
5. Mirror into `antigravity/.agents/skills/clone-audit/` (paraphrased port,
   same procedure) and bump `.claude-plugin/plugin.json` `version`.
6. Run the repo's canonical checks green.

## Acceptance

Runnable commands (from repo root):

- [x] `bash specs/ctx-static-analysis-augmentation/tests/clone-audit.sh`
  (or the committed check) → passes: the documented recipe rediscovers the
  duplicated function in BOTH the committed TS fixture pair and the Go
  fixture pair. (L2/L3 — behavioral; runs the detector against real
  in-repo fixtures.) If the recommended detector requires a network install
  unavailable to a sandboxed worker, mark THIS criterion manual-pending with
  that reason and provide an `npx`/`go run` form the worker can execute as
  the primary path; do not point the assertion at another repo's drifting
  contents.
  Evidence: `npx jscpd` fetched cleanly over network; script prints `PASS:
  clone-audit recipe rediscovered both the TS and Go fixture clones`, exit
  0. Red confirmed first: with the TS clone fixture temporarily replaced by
  an unrelated function, the script correctly failed
  (`FAIL: TS clone pair ... not reported`, exit 1) before being restored.
- [x] `test -f .claude/skills/clone-audit/SKILL.md && test -f .claude/skills/clone-audit/reference.md`
  → both exist. (L0 — presence; Depth ceiling: content quality is judged by
  the recipe-rediscovery behavioral check above, which is this criterion's
  complement.)
  Evidence: both files present, exit 0.
- [x] `grep -q homography .claude/skills/clone-audit/reference.md` → the
  fooszone worked example is recorded (non-normative). (L0.)
  Evidence: matched (worked-example section header + body), exit 0.
- [x] `test -d antigravity/.agents/skills/clone-audit` and the recipe
  concepts/identifiers present in the mirror (content-coverage grep, not a
  byte diff — the mirror is a paraphrased port). (L1.)
  Evidence: dir exists; mirror is a paraphrased port carrying the same
  recipe commands, worked example, and `homography`/`jscpd` terms as the
  source (`grep -c homography`/`grep -c jscpd` both non-zero in the mirror).
- [x] `python3 -c "import json,sys; json.load(open('.claude-plugin/plugin.json'))"`
  → valid JSON, and its `version` differs from the value at this task's base
  commit (`git show <base-commit>:.claude-plugin/plugin.json`). (L1 —
  compared against base revision, never a pinned literal.)
  Evidence: valid JSON; version bumped 0.9.31 → 0.9.32 (base commit
  65352896e0d3dd144984102f653a9c6f68d947ec read 0.9.31).

## Decisions

- Decision: this task's `Touch:` header did not list `codex/.agents/skills/`,
  but `tests/test_codex_parity.sh` (a project gate) fails for any new
  top-level `.claude/skills/*` directory with no corresponding
  `codex/.agents/skills/<name>` entry (real dir, resolving symlink, or a
  README "Not ported" exemption row). Default taken: added
  `codex/.agents/skills/clone-audit` as a symlink to
  `../../../antigravity/.agents/skills/clone-audit`, matching the existing
  pattern for every other already-working antigravity skill (per CLAUDE.md's
  port-chain convention). Reversible: `rm codex/.agents/skills/clone-audit`.
