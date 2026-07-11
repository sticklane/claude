# Task 03: Closing gate — shadow-copy cleanup and conditional mirror/bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: done
Depends on: 01, 02
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirements R1/R3 cross-cutting acceptance)
Touch: antigravity/.agents/skills/, .claude-plugin/plugin.json, .claude/agents/

## Goal

The spec's cross-cutting ship obligations are closed: any stale shadow
agent copies task 02 flagged are deleted (after confirming they shadow the
plugin per the no-shadow-copies rule), and IF tasks 01–02 edited any
`.claude/agents/*.md` file, the antigravity mirror and
`.claude-plugin/plugin.json` bump ship together with `claude plugin
validate .` green. If nothing conditional triggered, this task closes as
a verified no-op with evidence.

## Touch

Mirror, manifest, agents dir (deletion/mirroring only — no new content
authoring). Shadow copies outside this repo (e.g. `~/.claude/agents/`)
may be deleted only if task 02's evidence shows they shadow a plugin
agent by identical name; anything ambiguous goes to ## Deferred questions
for the human.

## Steps

1. Read tasks 01–02's ## Progress sections and
   `git -C /Users/sjaconette/claude log --oneline -- .claude/agents/` for
   this spec's commits.
2. Delete confirmed shadow copies task 02 flagged; cite the
   no-shadow-copies rule and the evidence for each deletion.
3. If any `.claude/agents/*.md` changed in this spec: port to the
   antigravity mirror (`antigravity/.agents/skills/<agent>/SKILL.md`,
   paraphrased — content-coverage, not byte-identity), bump `version` in
   `.claude-plugin/plugin.json`, run `claude plugin validate .`. The bump
   is race-safe against the other agentprof-spec drains: `git pull
   --rebase` immediately before bumping, read the version from HEAD, set
   next patch, commit, push; on a rejected push or version-line conflict,
   take the highest version present and increment once more, then retry.
   Never resolve by reverting another spec's bump.
4. If nothing triggered: record the verification commands showing no
   agent-def edits and no confirmed shadow copies, and close.

## Acceptance

- [x] `git -C /Users/sjaconette/claude log --oneline -- .claude/agents/` filtered to this spec's commits (match the spec slug / task numbers in messages) — if any exist, mirror + plugin.json bump landed in the same shipping commit and `cd /Users/sjaconette/claude && claude plugin validate .` → pass; if none, evidence line stating the no-op (never bound the check with a fixed HEAD~N window)
  - Evidence: NO-OP. `git log --oneline --grep='agent-tier-leak' -- .claude/agents/` → empty; no agents-dir commit matches this spec's slug or task numbers. Both content commits confirmed touching zero agent defs: task 01 (5aa2a91) → only `docs/memory/verifier-tier-leak.md` (+ task/evidence), message states "verifier.md intentionally left untouched (outcome (a) → no agent-def edit, avoiding task-03 mirror/bump obligation)"; task 02 (6272e48) → only `agentprof/README.md` (+ task/evidence). No `.claude/agents/*.md` edited in this spec → mirror port + plugin.json bump NOT triggered; `claude plugin validate .` not required.
- [x] Every shadow copy flagged by task 02 is either deleted (with evidence) or explicitly deferred to the human with reason
  - Evidence: task 02 flagged ZERO shadow copies. Its evidence (specs/agent-tier-leaks/evidence/02-namespace-attribution.md, Step-3 check) and task file (02-namespace-attribution.md L61) both record `~/.claude/agents/` present but EMPTY and `~/hub/.claude/agents/` absent — "No stale shadow copies of toolkit agents found; nothing to flag for deletion." Nothing to delete or defer, so the no-shadow-copies rule (CLAUDE.md) is already satisfied.
