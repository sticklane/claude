# Task 04 evidence — codex/antigravity mirrors, manifest seed, version bump

Ports task 02's `drain_frontier.py` invoke-with-fallback procedure into the
two drain mirrors, seeds ONE codex manifest line, and bumps plugin.json.

## What was ported

Task 02 (commit `bb8160f`) added two things to the source
`.claude/skills/drain/SKILL.md`:

1. **Inventory step** — invoke `python3 .claude/skills/drain/drain_frontier.py
<spec-dir>` per spec dir, treat its output as authoritative for the
   dispatchable set and ordering; missing script or non-zero exit → today's
   header read verbatim, quoting the scanner's stderr in the fallback log line.
2. **Tie-break step** — dispatch in the scanner's emitted order; a fallback
   read applies the same Priority → unblocking-power → lexicographic-path
   triple by hand.

Both were ported into:

- `codex/.agents/skills/drain/SKILL.md` (inventory ~line 126, tie-break
  ~line 189) — the invocation path is `.agents/skills/drain/drain_frontier.py`
  (the codex/antigravity script-bundle layout), matching the existing
  `admission.py` shell-out convention already in the file.
- `antigravity/.agents/workflows/drain.md` (inventory step 1, tie-break
  step 2) — same procedure, same `.agents/skills/drain/drain_frontier.py`
  path.

## Antigravity divergence classification: INCIDENTAL

Per `.claude/rules/mirror-procedure-discipline.md`, every divergence is
classified load-bearing (a runtime mechanism forces it) or incidental
(prose-level drift in what should be the same procedure).

The antigravity divergence here is **INCIDENTAL**, not load-bearing:

- The Goal's load-bearing test is "if that runtime cannot invoke the script."
  Antigravity **can** invoke the script — its own drain workflow already
  shells out to `python3 .agents/skills/drain/admission.py --frontier <path>`
  from the repo root, and `admission.py` CONSUMES `drain_frontier.py`'s JSON.
  A runtime that already runs one Python scanner in the same step can run the
  other. So the scanner invocation is portable, and the model-derived-fallback
  wording is NOT the primary procedure — the invoke-then-fallback procedure is
  ported verbatim in shape.
- The only genuine divergence is the **path prefix**
  (`.claude/skills/drain/` → `.agents/skills/drain/`), which IS load-bearing
  (the runtime's file layout forces it) but is a cross-reference difference,
  not a procedural one — governed by `mirror-verification.md`, not the
  procedure rule. The steps, order, and stated conditions (invoke per
  spec-dir → treat as authoritative → missing/non-zero → header-read fallback
  quoting stderr → emitted-order dispatch with by-hand triple fallback) are
  identical across all three files.

Because the divergence is incidental (path-only), the procedure was **ported**
into antigravity rather than left as a recorded load-bearing gap.

Per the task, NO antigravity manifest line is seeded (the manifest seeds only
the runtime-neutral bare token `drain_frontier` on the codex leg; an
antigravity line would be path-bearing / out of scope). The antigravity leg's
regression coverage rides the closure-triggered live cross-reference check
below, per `mirror-verification.md`.

## Live cross-reference check (mirror-verification.md)

The primary sweep tool for this pair is `bin/human-followups` step 3, which
runs an `agy -p` antigravity headless relaunch. That interactive relaunch was
**not** run here: per the auto-memory note (feedback_antigravity_cli.md) and
`.claude/rules/mirror-verification.md`'s manual-pending escape, the real `agy`
binary is unsafe for isolated/unattended fixture use (it corrupted real repo
files in a prior live test), so an unattended worker in an isolated worktree
does not exercise it. The human-owned deep behavioral relaunch remains
available via `bin/human-followups` post-merge.

The **static cross-reference resolution** — the exact gap
`mirror-verification.md` says a structural/content gate leaves open ("whether
the mirror's cross-references still resolve … a path valid in the source
runtime can point at nothing under the target runtime") — was run by hand and
**RESOLVES**:

    RESOLVES  antigravity/.agents/skills/drain/drain_frontier.py
    RESOLVES  antigravity/.agents/skills/drain/admission.py
    RESOLVES  codex/.agents/skills/drain/drain_frontier.py
    RESOLVES  codex/.agents/skills/drain/admission.py

The `.agents/skills/drain/drain_frontier.py` invocation path that the ported
procedure names exists in both mirror trees (mirrored under commit `eb433aa`),
so the port's new cross-reference resolves under both target runtimes. No
BROKEN reference.

## Gate results

- `grep -c 'drain_frontier' codex/.agents/skills/drain/SKILL.md` → 2 (was 0).
- `grep -c 'codex/.agents/skills/drain/SKILL.md.*drain_frontier'
tests/mirror-procedure-manifest.txt` → 1.
- `bash tests/test_mirror_procedure_coverage.sh` → exit 0.
- `bash evals/lint-ultra-gate.sh` (drain is an ultra-path skill) → OK, exit 0.
- `.claude-plugin/plugin.json` version `0.9.24` → `0.9.25` (patch bump; skill
  behavior text changed in the codex/antigravity drain mirrors).
