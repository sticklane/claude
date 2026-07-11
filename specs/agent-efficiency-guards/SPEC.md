# Agent efficiency guards: patch six measured antipatterns into skill text

Status: open
Priority: P1
Breakdown-ready: true

## Problem

Transcript mining over the 2026-07-11 drain runs (see EVIDENCE.md; main
hub session + 7 worker/verifier/scout sidecars + one parallel-dispatch
turn) found six recurring antipatterns that no current skill text
addresses. Each is cheap to prevent with one or two lines at the right
spot; together they burned measurable turns/calls today:

1. **Permission-denial grinding.** 87 denied-Bash tool_results across one
   drain tree ("don't ask mode" denials on chained/compound commands);
   one verifier mutated the same command through 9+ syntax variants (30
   denials) before a bare single command worked.
2. **Sleep-polling loophole.** After the harness blocked a `sleep 30`
   with an explicit "don't chain shorter sleeps" message, an agent chained
   23 × `sleep 1` to wait on background scouts anyway (91s of polling);
   a second agent did the same.
3. **Re-read churn.** Files re-read whole with no intervening edits:
   one worker read the same Go file 6× consecutively before its first
   edit; a spec-writer re-read SPEC.md 25× across critique rounds; the
   highest-volume waste by call count in every transcript sampled.
4. **Worktree-path trap.** A worker edited the main-checkout path from
   inside its isolated worktree, errored, and burned a turn discovering
   the worktree prefix the dispatch prompt could have stated.
5. **Scout scope creep.** 3 of ~10 scouts ran 17–21 model calls (target
   3–10): failed targeted greps escalated into repo-wide
   `grep -r` fishing plus duplicate file reads inside one scout.
6. **Full-file doctrine reads.** The hub read drain/reference.md whole
   (1,117 lines / 71KB) and a worker read the antigravity drain port
   whole (57KB) when each needed one section; the skill pointers imply
   full reads instead of a section lookup.

Verified NON-problems today (structure that held, no change needed):
verdict caps ≤2k tokens, one verifier per task, no transcript pasting
into hub context, no formatter fights, no test-suite thrashing, disjoint
parallel dispatch.

## Solution

Six targeted text patches — five in the toolkit's dispatch surfaces
(drain worker prompt, verifier + scout agent defs, token-discipline
dispatch-authoring rules, drain SKILL.md pointers) and their antigravity
content-equivalents where a port exists — each a one-to-three-line rule
stating the stop condition, not an essay. No code, no new mechanisms.

## Requirements

- R1 **Bash-denial stop rule.** The drain worker prompt
  (`.claude/skills/drain/reference.md`, "Worker prompt") and the verifier
  agent def (`.claude/agents/verifier.md`) gain: on a Bash permission
  denial, retry ONCE as a bare single command (no chaining, no
  redirection tricks); if still denied, stop and report the blocked
  command in the verdict — never iterate syntax variants.
- R2 **No sleep-polling.** `.claude/rules/token-discipline.md` "Dispatch
  authoring" gains a bullet: await background children via the harness's
  completion notifications (or a Monitor until-loop where the harness
  offers it); chained short sleeps are the blocked-sleep antipattern in
  chunks and are banned. The drain worker prompt gains the same rule in
  one line, and both lines contain the literal phrase "chained short
  sleeps" (the acceptance anchor).
- R3 **Re-read discipline.** The drain worker prompt gains: read a file
  at most once per edit round; after your own successful Edit/Write the
  harness confirms state — do not re-read to verify; re-read only the
  region another writer changed. The critique skill
  (`.claude/skills/critique/SKILL.md`) gains one line for multi-round
  flows: between rounds the author re-reads only the sections the critic
  named, never the whole artifact.
- R4 **Worktree prefix stated at dispatch.** The drain worker prompt's
  worktree preamble states explicitly: every path you Read/Edit/Write
  must be under your worktree root (your shell's initial $PWD) — the
  literal phrase "under your worktree root" is the acceptance anchor;
  the main checkout path (given for gitignored-file copies only) must
  never be edited — editing it errors and wastes a turn.
- R5 **Scout stop-and-report rule.** `.claude/agents/scout.md` gains:
  if 3 targeted greps/globs don't locate the answer, report "not found
  where expected" with what WAS checked — never widen to repo-wide
  scans; never read the same file twice in one run.
- R6 **Section-lookup pointers.** Exactly three drain SKILL.md pointers —
  the ones citing reference.md's "Worker prompt", "Owner lease", and
  "Baton pass" sections — gain the instruction to load only the named
  section (locate the heading via `grep -n`, read that slice), instead of
  implying a full read of a 1,100-line file. The added instruction
  contains the literal phrase "load only the named section" at least once
  (the acceptance anchor). The FIRST pointer citing each section receives
  the instruction; other pointers are untouched.
- R7 **Mirror + plugin hygiene.** Content-equivalent lines land in the
  antigravity drain workflow port for R1/R3/R4 (paraphrased port —
  content-coverage grep, not byte-diff); `.claude-plugin/plugin.json` is
  bumped in the closing task's own commit (`git show <closing-commit> --
  .claude-plugin/plugin.json | grep -q '^+.*"version"'`) and
  `claude plugin validate .` passes.

## Out of scope

- Harness changes (the sleep guard, permission modes, Edit errors are
  harness-owned; these rules teach agents to stop fighting them).
- Retuning scout/worker budgets or tiers.
- The hub-economics advisories (specs/drain-hub-economics owns those).
- Re-litigating the clean areas listed in the Problem section.

## Acceptance criteria

- [ ] `grep -qi 'bare single command' .claude/skills/drain/reference.md && grep -qi 'bare single command' .claude/agents/verifier.md`
  (phrase absent from both today) AND MANUAL: the rule caps retries at
  one and requires reporting the blocked command (R1)
- [ ] `grep -qi 'chained short sleeps' .claude/rules/token-discipline.md && grep -qi 'chained short sleeps' .claude/skills/drain/reference.md`
  (phrase absent from both today) (R2)
- [ ] `grep -qi 'once per edit round' .claude/skills/drain/reference.md && grep -qi 'sections the critic named' .claude/skills/critique/SKILL.md`
  (both phrases absent today) (R3)
- [ ] `grep -qi 'under your worktree root' .claude/skills/drain/reference.md`
  (phrase absent today — the pre-existing "worktree root" text at
  reference.md:192 is a different section and does not match this longer
  anchor) AND MANUAL: the preamble bans editing main-checkout paths (R4)
- [ ] `grep -qi 'not found where expected' .claude/agents/scout.md`
  (phrase absent today) (R5)
- [ ] `grep -qi 'load only the named section' .claude/skills/drain/SKILL.md`
  (phrase absent today) AND MANUAL: exactly the "Worker prompt", "Owner
  lease", and "Baton pass" pointers carry it, first citation of each (R6)
- [ ] `grep -qi 'bare single command' antigravity/.agents/workflows/drain.md && grep -qi 'once per edit round' antigravity/.agents/workflows/drain.md && grep -qi 'under your worktree root' antigravity/.agents/workflows/drain.md`
  (content-coverage for the R1, R3, AND R4 port lines — each anchored)
  AND `claude plugin validate .` passes AND the closing commit modifies
  the plugin version line (R7)
- [ ] `bash agentprof/scripts/check.sh` untouched-green (no code changed
  by this spec; guard against accidental code edits)

## Open questions

- None; every rule is a stop condition with a measured incident behind it.

## Parallelization

Task map: 01 = R1–R6 (single writer across small files), 02 = R7 closing
gate (mirror lines + bump + validate), depends on 01. Serialized — no
Group lines (format grammar per specs/drain-rolling-window/SPEC.md's
Parallelization section).

Cross-spec contention: specs/drain-hub-economics's closing task also
bumps `.claude-plugin/plugin.json` (single version line). Both closing
tasks list it in `Touch:`, so drain's Touch-disjoint admission rule
serializes them mechanically; each bumps RELATIVE to the version it
reads at its own base (never a pinned literal), so whichever lands
second still bumps cleanly after a rebase.
