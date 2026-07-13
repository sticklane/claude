# VCS-agnostic instructions across the toolkit

Breakdown-ready: true
Status: open
Priority: P2

## Problem

This toolkit hardcodes "git" throughout skill bodies, rules, and agent
definitions, on the assumption that git is the only version control system
any executing agent will ever meet. That assumption is already false:
Antigravity CLI's own changelog documents native Jujutsu (jj) support,
prioritizing `.jj` over `.git` in colocated repos, and Antigravity is one of
this toolkit's two shipped runtimes (`antigravity/.agents/**`).

A direct-grep survey of `/Users/sjaconette/claude` (2026-07-11) found the
hardcoding splits into six genuinely different problems that must not be
conflated into one blanket "reword everything" pass:

1. **A concrete, already-latent break, not just wording.** `.claude/agents/critic.md`
   and `.claude/agents/scout.md` scope their `tools:` frontmatter to literal
   Bash prefixes — `Bash(git diff *)`, `Bash(git log *)`, `Bash(git blame *)`,
   `Bash(git show *)`. Claude Code's permission matcher checks the literal
   command prefix, so in a jj-colocated repo these agents are structurally
   unable to run `jj log` / `jj diff` / `jj show` — the permission grant
   doesn't cover it, independent of any prose fix. `.claude/agents/verifier.md`
   has the same assumption in prose (`git checkout`/`git restore`/`git diff`).
   This is real today for anyone who colocates jj in a repo this toolkit
   operates on, even though no repo on this machine currently does (`jj` is
   not installed; no `.jj` directory exists in this repo, confirmed by direct
   check).
2. **A cosmetic-but-pervasive wording problem** in most skill/reference
   prose: literal git syntax (`git worktree add -b task/NN-<slug>`, `git
   commit --no-verify -m "wip(rescue): ..."`, `git diff $(git merge-base
   ...)`, and — per the critic pass on this spec's first draft — also
   `checkout`, `rev-parse`, `fetch`, `remote`, `stash`, `clean` — is baked
   into the instruction text as the *only* phrasing, rather than describing
   intent ("isolate a worktree for this task", "commit the staged evidence")
   and trusting the executing agent to invoke whatever VCS is present.
3. **One line of internal plumbing with no clean cross-VCS concept at
   all.** `drain/reference.md:158` — `` `git update-ref
   refs/remotes/origin/main <default-branch>` `` — resyncs git's own
   remote-tracking-ref data structure, a git-specific storage detail (not
   "a commit" or "a branch") that jj does not model the same way. This one
   line is exempt from intent-level rewriting; everything else attributed to
   "drain plumbing" in an earlier draft of this spec (`git reset --hard`,
   `git fetch`, `git remote -v`, `git show`, `git rebase`, `git merge
   --abort`/`--ff-only`, `git checkout`, `git clean`, `git diff --stat`, log
   range queries) names ordinary VCS concepts (restore, fetch, inspect a
   remote, show a snapshot, rebase, abort a merge, restore a path, clean
   untracked files, diff stats, log ranges) that jj has direct equivalents
   for, so those get normal decision-1 intent-level rewriting like any other
   prose in the file, not a carve-out.
4. **Permission-grant strings that are structurally identical to the agent
   frontmatter case in (1), just written inline in skill bodies instead of
   `tools:` frontmatter.** `drain/reference.md:732` (`--allowedTools
   "...,Bash(git add *),Bash(git commit *)"`, a headless-dispatch template)
   and `autopilot/reference.md:23-28` (a `permissions.allow`/`deny` JSON
   example listing `Bash(git add *)`, `Bash(git commit *)`,
   `Bash(git worktree *)`, `Bash(git push *)`) are literal Bash
   permission-prefix strings, not prose describing an action — the same
   reasoning in (1) applies: rewording the surrounding prose doesn't change
   what the string itself grants, and widening it to also grant `jj`
   equivalents is the same permission-surface decision deferred in decision
   2. These strings are exempt from intent-level rewriting for the same
   reason (1)'s frontmatter is; only the prose immediately around them may
   note that the grant is git-specific.
5. **A mechanism gap, not a wording gap.** `.claude/skills/gate/SKILL.md`
   installs a **git pre-commit hook** as its literal mechanism; for a
   non-git-colocated jj repo there is no direct equivalent. This is
   documented as a limitation, not solved here (see Decisions, Out of
   scope).
6. **Executable test-fixture code that happens to shell out to git, not
   instruction prose at all.** `.claude/skills/evals/reference.md`'s
   `setup.sh` (lines 22, 26, 72–73) builds a real git repo — `git init -q`,
   `git add -A`, `git -c user.name=eval ... commit -qm "..."` — as an eval
   test fixture, plus an unrelated `Bash(git *)` permission string at line
   113 for the eval harness's own dispatch. None of this is prose describing
   an action to an executing agent; it is a bash script whose entire purpose
   is to build a git repo to test against. Out of scope entirely (see
   Decisions, Out of scope).

File-level inventory (verified via direct grep, not estimated):

| Area | Files | Hits (approx) |
|---|---|---|
| `.claude/skills/*/SKILL.md` + `reference.md` | drain/reference.md (20), drain/SKILL.md (8), autopilot/reference.md (6), gate/SKILL.md (3), build/SKILL.md (4), breakdown/SKILL.md (1 — missed in the first survey pass, added after the critic caught its antigravity counterpart being unexplained), onboard/SKILL.md (1), evals/reference.md (4 — executable fixture script + 1 permission string, see Decisions item 6), fleet/SKILL.md (1), gate/reference.md (1), critique/SKILL.md (1) | 47 |
| `.claude/agents/*.md` | critic.md (frontmatter + prose), scout.md (frontmatter), verifier.md (prose) | structural + prose |
| `.claude/rules/*.md` | concurrent-sessions.md (`git worktree list`, `git status` as pre-flight commands) | 2 |
| `/Users/sjaconette/claude/CLAUDE.md` | none — verified clean | 0 |
| `/Users/sjaconette/CLAUDE.md`, `/Users/sjaconette/.claude/CLAUDE.md` | both describe the gate as "the git pre-commit hook ... bypass with `--no-verify`" | 1 each |
| `antigravity/.agents/**` mirror | workflows/drain.md (19, same plumbing/prose split as items 2–4 above), skills/workboard/workboard.py + test_workboard.py (~15, includes Python `.git/`-detection logic, not just prose), skills/verifier/SKILL.md (3), workflows/build.md (2), workflows/autopilot.md (2), skills/breakdown/SKILL.md (2), skills/onboard/SKILL.md (0 — mirrors onboard/SKILL.md's 1 hit; no independent git mention of its own, still listed since R6 maps it), skills/critic/SKILL.md (1 prose mention, no `tools:`-frontmatter equivalent to Claude Code's restriction — see R6 note), skills/scout/SKILL.md (0 hits currently), skills/workboard/reference.md (2), skills/gate/reference.md (`.git/*` glob + `git push` deny pattern), README.md (1, install instructions) | ~46 |

Per this repo's CLAUDE.md authoring conventions, `.claude/` is source of truth
and `antigravity/.agents/**` is a mirrored port: any change to a
`.claude/skills/` or `.claude/rules/` file in this spec's scope must land in
the same commit as its `antigravity/.agents/**` mirror update, and
`.claude-plugin/plugin.json`'s `version` must bump in the closing task's
`Touch:` list — this is the model `workboard-cli`'s closing task 04 already
established. Not every `.claude/` file in scope has an antigravity
counterpart to mirror into — the reconciled mapping in R6 states exactly
which do and which don't, verified directly against the actual
`antigravity/.agents/**` tree rather than assumed.

### Decisions (defaulted — no interactive AskUserQuestion session was available; flagged here for override)

1. **Phrasing convention: intent-level, git command syntax dropped from
   instruction text; conceptual VCS nouns retained.** The user's own
   framing — "relying on the agent to use the appropriate skills" — signals
   trust in the executing agent, not a dual-naming hedge ("git commit, or jj
   commit"). Convention, with the bright line the critic pass asked for
   made explicit: conceptual nouns that name a VCS concept generically
   (worktree, branch, commit, diff, log, blame, merge, rebase, push, pull)
   are retained as vocabulary — jj has direct or near-direct analogues for
   all of them (jj calls a worktree a "workspace," but the instruction can
   still say "worktree" as the generic term this toolkit already uses
   elsewhere). What gets dropped or relabeled is **shell-executable command
   strings** — anything of the form `git <subcommand> <flags>` written as
   if it were the only correct incantation (`git worktree add -b
   task/NN-<slug>`, `git diff $(git merge-base ...)`, `git commit
   --no-verify -m "..."`). Where a concrete example materially helps (e.g.
   drain's push-rejection detection heuristic, or a literal path template
   like `task/NN-<slug>`), it is kept but reframed as a worked example under
   the git case specifically, labeled as such ("e.g., under git: `git push`
   fails with a rejection"), never as the instruction's only phrasing.
2. **Agent tool-permission widening: out of scope for this spec.** Widening
   `.claude/agents/critic.md` / `scout.md` frontmatter to grant
   `Bash(jj log *)` / `Bash(jj diff *)` / `Bash(jj show *)` alongside the
   existing git grants is a permission-surface change, which this toolkit's
   own safety posture treats as sensitive. Defaulting to no speculative
   permission widening until jj is actually in use in a repo this toolkit
   operates on avoids growing Bash grant surface for a VCS with zero current
   usage on this machine. This spec instead documents the gap explicitly (in
   agent prose and in this spec) so a future task can widen the grant the
   day it's actually needed, without silently leaving it undocumented.
3. **gate/SKILL.md's git pre-commit hook: documented limitation, not solved
   here.** No git-agnostic drop-in replacement is assumed. The fix is to
   state the limitation explicitly in gate/SKILL.md ("this hook mechanism is
   git-specific; non-colocated jj repos need an equivalent jj hook or a
   different enforcement point") rather than word the whole skill as if it
   were VCS-agnostic when its actual mechanism isn't. Note: antigravity's own
   gate mirror (`antigravity/.agents/skills/gate/SKILL.md`) already installs
   hooks through Antigravity's own harness-native hook mechanism (`.agents/
   hooks.json` + `.agents/hooks/*.sh`), not a git pre-commit hook — so this
   limitation is specific to the Claude Code gate skill and does not need an
   equivalent callout added to antigravity's gate/SKILL.md. Its
   `gate/reference.md` mirror does still carry a `.git/*` protected-path glob
   and a `git push` deny-pattern string, which get the same
   documented-as-git-specific treatment as the Claude Code copy (R5).
4. **drain/reference.md:158's single plumbing line (Problem item 3): kept as
   a labeled git-specific mechanic, not abstracted.** `` `git update-ref
   refs/remotes/origin/main <default-branch>` `` is exempt from R1's "no bare
   git command as sole phrasing" bar and stays as-is, labeled
   ("git-specific mechanic — a jj-based drain would need an equivalent
   tracking-ref/force-sync step, not yet designed") so a reader isn't misled
   into thinking it was overlooked. Every other git command in drain's files
   (`reset --hard`, `fetch`, `remote -v`, `show`, `rebase`, `merge --abort`/
   `--ff-only`, `checkout`, `clean`, `diff --stat`, log ranges) gets normal
   decision-1 intent-level rewriting — the first draft of this spec
   over-broadly exempted all of drain's plumbing by operation-type, which
   the critic pass found undecidable for an implementer; anchoring the
   exemption to one named line fixes that.
5. **Permission-grant strings (Problem item 4): exempt from rewriting, same
   treatment as decision 2.** `drain/reference.md:732`'s `--allowedTools`
   template and `autopilot/reference.md:23-28`'s `permissions.allow`/`deny`
   JSON example keep their literal `Bash(git add *)` / `Bash(git commit *)`
   / `Bash(git worktree *)` / `Bash(git push *)` strings unchanged — these
   are permission prefixes, not prose, and widening them to grant jj
   equivalents is out of scope for the same permission-surface reason as
   decision 2. The prose immediately around each may note the grant is
   git-specific, but the strings themselves are not touched.
6. **evals/reference.md's `setup.sh` fixture builder and its `Bash(git *)`
   dispatch permission (Problem item 6): out of scope entirely, not
   touched.** Its `git init -q` (line 26) / `git add -A` (line 72) / `git -c
   user.name=eval ... commit -qm "..."` (line 73) lines are executable bash
   that builds a real git repo as an eval test fixture, and line 113's
   `Bash(git *)` is the eval harness's own dispatch permission — neither is
   instruction prose, and rewording either would either do nothing (still
   bash) or break the fixture/permission. See Out of scope.

If the user disagrees with any of these six defaults, they supersede this
spec's text before implementation.

## Solution

Replace git-specific command syntax in instruction prose with VCS-agnostic,
intent-level phrasing, per decision 1, across the inventory below — except
the three carve-outs (drain's one plumbing line, decision 4; permission-grant
strings in drain/reference.md and autopilot/reference.md, decision 5; the
evals fixture script and its permission string, decision 6), which are left
alone. Leave the two structural/mechanism gaps (agent tool-permission
scoping, gate's pre-commit-hook mechanism) explicitly documented rather than
silently resolved, per decisions 2–3. Mirror every applicable `.claude/`
change into `antigravity/.agents/**` in the same commit, per CLAUDE.md's
authoring conventions (cited, not restated), using the reconciled mapping in
R6 — not every file has a mirror counterpart, and R6 says exactly which do.

Concretely:

- **Prose rewrite** (intent-level phrasing, decision 1) in:
  `.claude/skills/drain/SKILL.md` and `.claude/skills/drain/reference.md`
  (excluding the single line carved out by decision 4 and the permission
  string carved out by decision 5), `.claude/skills/autopilot/reference.md`
  (excluding its permission-grant JSON block, decision 5),
  `.claude/skills/build/SKILL.md`, `.claude/skills/breakdown/SKILL.md`,
  `.claude/skills/onboard/SKILL.md`, `.claude/skills/fleet/SKILL.md`,
  `.claude/skills/gate/reference.md`, `.claude/skills/critique/SKILL.md`,
  `.claude/rules/concurrent-sessions.md`, `.claude/agents/verifier.md`.
- **Not touched** (decision 6): `.claude/skills/evals/reference.md`
  entirely (fixture script and its permission string).
- **Documented limitation, no mechanism change**: `.claude/skills/gate/SKILL.md`
  gets a callout that its hook mechanism is git-specific (decision 3).
- **Documented gap, no permission change**: `.claude/agents/critic.md` and
  `.claude/agents/scout.md` get a one-line note next to their `tools:`
  frontmatter that the grant is git-specific and jj equivalents are an
  intentionally deferred follow-up (decision 2) — the frontmatter values
  themselves are unchanged. Same treatment, no string change, for the
  permission-grant strings named in decision 5.
- **Mirror**: every file in R6's reconciled mapping table gets a matching
  edit in its `antigravity/.agents/**` counterpart in the same commit, plus
  a `.claude-plugin/plugin.json` version bump. Files with no counterpart
  (see R6) get no mirror edit — that's not a gap, it's the correct outcome.
- **Global user CLAUDE.md files** (`/Users/sjaconette/CLAUDE.md`,
  `/Users/sjaconette/.claude/CLAUDE.md`) are outside this repo and outside
  this toolkit's mirror convention — reword their one line each
  ("the git pre-commit hook ... bypass with `--no-verify`") to intent-level
  phrasing as a courtesy pass, but they are not gated on this spec's
  acceptance criteria since they aren't part of this repo.
- **`antigravity/.agents/skills/workboard/workboard.py`** needs an actual
  code change, not just prose: the `.git/` directory-detection logic (`if
  (Path(dirpath) / ".git").exists()`) should also detect `.jj/` as a valid
  repo root, since this is executable logic that will misdetect jj-only
  repos as "not a repo" today. `test_workboard.py` gets a new test for it.
- **`antigravity/README.md`** gets its one-line install instruction
  (`git add .agents AGENTS.md && git commit -m "..."`) reworded to
  intent-level phrasing, matching the R8 treatment of the global CLAUDE.md
  files.

## Requirements

R1. Every `.claude/skills/*/SKILL.md` and `reference.md` file listed in the
    inventory above — **excluding** drain/reference.md:158 (decision 4) and
    the permission-grant strings named in decision 5 (drain/reference.md:732,
    autopilot/reference.md:23-28), and **excluding** evals/reference.md
    entirely (decision 6) — describes VCS actions in intent-level language
    per decision 1's bright line: no backtick-wrapped `` `git <subcommand>
    ...` `` shell-executable command span is left on a line without either
    (a) an "e.g., under git:" (or equivalent explicit label) on that same
    line, or (b) being one of the named decision-4/5 exempt lines. Bare
    mentions of VCS nouns in running prose that are not backtick-wrapped
    command syntax (e.g. "a git commit", "if git still preserves...") are
    not subject to this bar at all — decision 1 retains them as vocabulary.
    This includes `.claude/skills/breakdown/SKILL.md`'s `git show
    <base-commit>:<path>` example (line 98) — missed in the initial survey
    pass, caught via its antigravity mirror during the second critic pass,
    and folded into the inventory table above.

R2. `.claude/rules/concurrent-sessions.md`'s pre-flight collision checks are
    phrased as VCS-agnostic intent ("check for another checkout of this
    worktree", "check for unexplained working-tree changes"), with the git
    commands kept only as a labeled example.

R3. `.claude/agents/verifier.md`'s prose no longer assumes git as the only
    VCS for its "restoring a path reverts the file" caution.

R4. `.claude/agents/critic.md` and `.claude/agents/scout.md` each carry a
    one-line note (outside the `tools:` frontmatter, which stays unchanged
    per decision 2) stating the Bash grant is git-specific and that jj
    equivalents are a deferred follow-up, not silently missing. Their
    antigravity mirrors (`skills/critic/SKILL.md`, `skills/scout/SKILL.md`)
    have no equivalent `tools:`-frontmatter restriction to annotate — verified
    directly, `skills/critic/SKILL.md` has one prose mention ("use git
    blame/log for context") and `skills/scout/SKILL.md` has none — so R4's
    specific frontmatter-note does not apply to the mirrors; any prose git
    mention there gets ordinary decision-1 rewriting instead (tracked under
    R6, not R4).

R5. `.claude/skills/gate/SKILL.md` states explicitly that its pre-commit-hook
    installation is git-specific and that non-colocated jj repos need a
    different enforcement point (decision 3) — no mechanism change required.
    `.claude/skills/gate/reference.md` (and its antigravity mirror,
    `antigravity/.agents/skills/gate/reference.md`) get a one-line note next
    to their `.git/*` glob and `git push` deny-pattern that these are
    git-specific pattern strings, not VCS-agnostic — no pattern change
    required.

R6. Reconciled mirror mapping — each `.claude/` file below gets a matching
    edit in its listed `antigravity/.agents/**` counterpart, landed in the
    same commit, with `.claude-plugin/plugin.json`'s `version` bumped in
    that commit. Files marked "no counterpart" get no mirror edit — this is
    the correct, verified outcome, not an oversight:

    | `.claude/` file | `antigravity/.agents/**` counterpart |
    |---|---|
    | skills/drain/SKILL.md + skills/drain/reference.md | workflows/drain.md (single merged file; carries the same decision-4/5 exempt lines) |
    | skills/autopilot/reference.md | workflows/autopilot.md (carries the same decision-5 exempt permission block) |
    | skills/build/SKILL.md | workflows/build.md |
    | skills/breakdown/SKILL.md | skills/breakdown/SKILL.md |
    | skills/onboard/SKILL.md | skills/onboard/SKILL.md |
    | skills/gate/SKILL.md | skills/gate/SKILL.md (decision 3 note: no git-hook callout needed there — different, harness-native mechanism) |
    | skills/gate/reference.md | skills/gate/reference.md |
    | skills/critique/SKILL.md | workflows/critique.md (verified 0 git hits in the mirror already — confirm still 0 after the Claude-side edit; no edit needed unless the rewrite introduces a mismatch) |
    | agents/verifier.md | skills/verifier/SKILL.md |
    | agents/critic.md | skills/critic/SKILL.md (R4 note: frontmatter-restriction annotation does not apply here — see R4) |
    | agents/scout.md | skills/scout/SKILL.md (R4 note: frontmatter-restriction annotation does not apply here — see R4) |
    | skills/fleet/SKILL.md | **no counterpart** — antigravity has no fleet skill or workflow |
    | rules/concurrent-sessions.md | **no counterpart** — antigravity has no `.agents/rules/` directory at all |
    | skills/evals/reference.md | **not touched** (decision 6) — antigravity's `workflows/evals.md` has 0 git hits and no separate reference.md; nothing to mirror |

R7. `antigravity/.agents/skills/workboard/workboard.py`'s repo-root detection
    treats a directory containing `.jj/` the same as one containing `.git/`
    (actual code change, covered by a new test in `test_workboard.py`).

R8. The two global user files (`/Users/sjaconette/CLAUDE.md`,
    `/Users/sjaconette/.claude/CLAUDE.md`) have their one git-specific line
    each reworded to intent-level phrasing ("the VCS's pre-commit hook").

R9. `antigravity/README.md`'s one-line install instruction is reworded to
    intent-level phrasing (e.g. "commit the `.agents` directory and
    `AGENTS.md` to your repo") instead of a bare `git add`/`git commit`
    example as the only phrasing.

## Out of scope

- Widening any `.claude/agents/*.md` `tools:` frontmatter, or the
  decision-5 permission-grant strings in drain/reference.md and
  autopilot/reference.md, to add jj (or any non-git) Bash permission grants
  (decisions 2 and 5) — tracked as explicit documented gaps (R4), not
  implemented here.
- Building or wiring an actual jj-native pre-commit-hook-equivalent mechanism
  for `.claude/skills/gate` (decision 3) — documented as a limitation (R5),
  not implemented here.
- Rewriting `.claude/skills/evals/reference.md` at all — neither its
  `setup.sh` fixture builder nor its `Bash(git *)` dispatch permission
  (decision 6) — it is executable test-fixture code that legitimately
  builds a real git repo for eval purposes, not instruction prose; making the
  eval harness itself multi-VCS is a separate, unscoped feature.
- Rewriting drain/reference.md:158's `git update-ref` line (decision 4) into
  VCS-agnostic phrasing — it gets a one-line "git-specific mechanic" label
  instead, in both `.claude/skills/drain/reference.md` and its antigravity
  mirror. (Every *other* git command in drain's files — `reset --hard`,
  `fetch`, `remote -v`, `show`, `rebase`, `merge --abort`/`--ff-only`,
  `checkout`, `clean`, `diff --stat`, log ranges — is explicitly IN scope
  for R1's normal rewrite, per decision 4's narrowing; it is not exempt.)
- Adding jj (or any other VCS) detection/dispatch logic to any `.claude/`
  skill's runtime behavior beyond the `workboard.py` repo-root detection fix
  (R7) — this spec is a documentation/phrasing pass plus one narrow code fix
  where the existing code is objectively wrong (misdetecting jj repos as
  non-repos), not a general multi-VCS feature build.
- Any change to `.claude/skills/*/templates/` hook script contents themselves
  (e.g. the pre-commit hook template gate installs) — only the SKILL.md prose
  describing them changes (R5).
- Rewriting this spec's own inventory scout results into a persisted
  docs/memory.md entry — that's a `/distill` follow-up if warranted after
  implementation, not part of this spec.

## Acceptance criteria

- [ ] For each R1-scope file, `` rg -Un --pcre2 '`git[^`]*`' <file> `` — a
      multiline-aware match from an opening to closing backtick, so it
      catches the full command span regardless of line wraps (verified
      against real cases: catches `breakdown/SKILL.md:98-99`'s `` `git show
      <base-commit>:<path> | grep ``…`` version` ``, and
      `drain/reference.md:188-189`'s `` `git -C <worktree>``…``status
      --porcelain` `` where the flag and subcommand are split across lines;
      correctly excludes bare non-backticked prose like
      `drain/reference.md:453`'s "a git commit"). This lists every
      backtick-wrapped git-command span with its starting line. A hit passes
      only if its span's starting line contains the literal substring "e.g.,
      under git:", or its starting line is one of the two explicitly named
      exempt lines (drain/reference.md:158 for decision 4;
      drain/reference.md's `--allowedTools` line and autopilot/reference.md's
      `permissions.allow`/`deny` block for decision 5). Any hit whose
      starting line matches none of those fails the check. A plain
      `grep`-based version of this check is line-oriented and known to miss
      multi-line spans (an earlier draft's did) — `rg -U --pcre2` (or an
      equivalent multiline regex tool) is required, not optional, for this
      criterion (R1).
- [ ] `diff <(git show <base>:.claude/skills/evals/reference.md) .claude/skills/evals/reference.md`
      (or the repo's VCS-agnostic equivalent: compare the file's content
      before and after this spec's implementation commit) is empty —
      confirms decision 6's carve-out was respected, not silently "fixed."
- [ ] `grep -n 'git worktree list\|git status' .claude/rules/concurrent-sessions.md`
      — if any hits remain, each is inside a labeled example, with
      intent-level phrasing preceding it (R2).
- [ ] `grep -n 'jj\|git-specific' .claude/agents/critic.md .claude/agents/scout.md`
      returns at least one hit each, confirming the deferred-gap note was
      added (R4).
- [ ] `grep -n 'git-specific\|pre-commit hook' .claude/skills/gate/SKILL.md`
      shows the limitation callout (R5); `grep -n 'git-specific'
      .claude/skills/gate/reference.md antigravity/.agents/skills/gate/reference.md`
      shows the pattern-string note in both copies (R5).
- [ ] For each row of R6's mapping table with a listed counterpart, the
      counterpart file's diff in the same commit is non-empty; for each row
      marked "no counterpart," the acceptance check confirms no mirror
      directory/file was created for it (R6).
- [ ] `python3 antigravity/.agents/skills/workboard/test_workboard.py` (or the
      project's test runner) passes, including a new test asserting a
      directory containing only `.jj/` is detected as a repo root (R7).
- [ ] `grep -n 'git pre-commit hook' /Users/sjaconette/CLAUDE.md /Users/sjaconette/.claude/CLAUDE.md`
      returns no hits after the reword (R8).
- [ ] `grep -n 'git add .agents\|git commit -m' antigravity/README.md` returns
      no hits after the reword (R9).
- [ ] End-to-end: a fresh reviewer reading `.claude/skills/drain/SKILL.md` and
      `.claude/skills/gate/SKILL.md` cover-to-cover can correctly describe,
      for a hypothetical jj-colocated repo, (a) what drain would do for
      committing/pushing/isolating worktrees, (b) which specific lines are
      git-specific plumbing that would need separate jj design work, and (c)
      that gate's hook mechanism is a known gap for that case — without
      needing to already know git syntax to parse the instructions.

## Open questions

(none — the human-only decisions were defaulted above, per decisions 1–6, in
the absence of an available interactive AskUserQuestion session; override
before implementation if the defaults are wrong)

## Addendum (found during /breakdown's critic pass)

The original survey's inventory and R6/R7 never listed
`.claude/skills/workboard/` at all — only its antigravity mirror. Per
`docs/memory/workboard-mirror-verbatim.md`, workboard's two `.py` files are
byte-identical across trees and `.claude/` is the source of truth, so R7's
jj-detection fix belongs in `.claude/skills/workboard/workboard.py` first,
ported verbatim to the antigravity copy — fixing only the mirror (as R7's
literal text names) would leave the real source-of-truth file broken.
`.claude/skills/workboard/reference.md` and its antigravity mirror also
carry git-command-syntax hits (`` `git -C <repo> …` ``, `` `git rev-parse
--show-toplevel` ``) missed by the original inventory; these get ordinary
decision-1 rewriting. Folded into task 05 rather than reworking R7's text
here, following the same precedent as R1's breakdown/SKILL.md:98 callout.

## Parallelization

Tasks 01–06 each own a disjoint `Touch` set (no two tasks edit the same
`.claude/` file, mirror, or standalone file) and share no undecided design —
decision 1's phrasing convention is already fixed by this spec, so each task
applies it rather than inventing it. They pass the decision-coupling test
and are parallel-safe. Task 07 is the closing verification + plugin.json
version-bump task; it depends on all six and runs solo after they land,
per this repo's CLAUDE.md convention of a single closing task carrying the
version bump rather than every mirror-touching task bumping it.

- Group: 01, 02, 03, 04, 05, 06
