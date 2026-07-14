# Retire /autopilot, fold its distinct capability + reusable reference content into /build

Status: open
Breakdown-ready: true

## Problem

`/autopilot`'s mechanism table (`autopilot/SKILL.md:39-46`) has four rows.
Three overlap with capabilities `/drain` now covers at least as well
("fire-and-forget, this machine" and "CI/scripts" are `/drain`'s dispatch
mechanisms with retry ladders and verification gates autopilot lacks — its
"background worktree agent" row is, concretely, the same
worktree+Agent-tool+verdict-only pattern `/drain` already runs per queued
task). The fourth — never-auto-push, human-reviews-every-PASS — was
confirmed in conversation to be a _negative_, not a selling point, for a
user who values `/drain`'s auto-landing. That leaves exactly one
genuinely distinct capability worth keeping: same-session, `/goal`-bounded
runs with a pre-cap baton hand-off. `/goal` itself is a **runtime
built-in** (Claude Code's own transcript-evaluator command, not a
`.claude/skills/` file) that wraps _around_ any procedure — autopilot
never implemented it, it only documented the pattern of wrapping its own
walk-away contract in a `/goal` invocation. `autopilot/reference.md` also
holds content with live consumers elsewhere: `onboard/SKILL.md:78-79` points
users at its scoped-permissions JSON template, and `drain/reference.md:1007`
cites "the autopilot reference's headless rule" as the source of truth for
headless dispatch. Deleting autopilot without relocating that content
breaks both citations. (Anchors refreshed 2026-07-14 against HEAD;
re-verify at implementation time — `drain/reference.md` in particular
shifts often — rather than trusting these numbers blindly.)

**Sequencing note (hard constraint, not just context)**: `specs/
build-doc-currency-check` also edits `build/SKILL.md` (a citation/
documentation addition near its "Close out" section). This spec must land
**first** — it restructures `build/SKILL.md` (a new classification gate
near the top, shifting every line after it), so `build-doc-currency-check`'s
anchors are written to be found by section content, not a stale line
number, and should be re-verified against whatever this spec leaves
behind. `specs/build-doc-currency-check` is **NOT READY** as of 2026-07-13
(its own `critique-findings.md` records an unresolved NOT READY verdict
and it has no `tasks/` yet), so there is no live concurrent-edit conflict
today — but `/breakdown` and `/drain` must not decompose or drain both
specs concurrently against `build/SKILL.md` regardless of when
`build-doc-currency-check` later clears critique; a human sequences the
two deliberately rather than an unattended drain landing a skill deletion
in isolation of the sibling edit (critique-findings.md finding 6).

## Solution

Delete `.claude/skills/autopilot/` (SKILL.md _and_ reference.md) and
create `.claude/skills/build/reference.md` (new file) as the new home for
everything in the old reference.md that still has live consumers:

- **Scoped permissions JSON template** — moves verbatim. `onboard/
SKILL.md:78-79`'s pointer is updated to `build/reference.md`.
- **Bounded goals (`/goal` pattern)** — moves verbatim, documenting that
  `/goal` is the _runtime's_ mechanism: a human wraps `/build`'s own
  procedure in a `/goal "<criteria>, or stop after N turns"` invocation.
  `/build` itself parses no new flag and needs no code change to
  "support" this — bounded mode is a documented usage pattern, not a new
  code path.
- **Containment ladder** — moves verbatim.
- **Failure recovery** — moves verbatim into `build/reference.md`
  alongside the walk-away contract's escalation triggers (R2) — it's the
  same doctrine (a failed/capped run is evidence about the task file, not
  a debugging invitation: fix the spec, discard the branch, relaunch
  clean), directly relevant to bounded mode's failure path.
- **Headless template** — moves verbatim (becoming the canonical copy);
  `drain/reference.md:1007`'s citation is updated to point at
  `build/reference.md`.
- **Pre-cap baton boundary** — moves verbatim (unchanged: it already cites
  `/drain`'s baton grammar rather than restating it).
- **"Background worktree agent" section is dropped, not moved** — it's the
  redundant-with-`/drain` capability the Problem section identifies;
  `build/reference.md` instead has one line pointing unattended
  fire-and-forget work at `/drain`.

`.claude/skills/build/SKILL.md` gains, near its start, the go/no-go
classification gate (autopilot's step 1: peripheral/prototype/
mechanically-verifiable is fine for a `/goal`-bounded run; core business
logic, security-sensitive code, or "looks right"-only verification is
not — use unbounded attended `/build`, today's default, instead) and the
walk-away contract's escalation triggers (same-step-fails-twice; reaching
a high-risk action), with a pointer to `build/reference.md` for the
concrete mechanism templates.

## Requirements

- **R1**: `.claude/skills/autopilot/` (SKILL.md and reference.md) is
  deleted; `.claude/skills/build/reference.md` is created with the six
  relocated sections named in Solution (permissions, `/goal` pattern,
  containment ladder, headless template, pre-cap baton, failure
  recovery), each moved verbatim, not summarized.
- **R2**: `.claude/skills/build/SKILL.md` gains: the go/no-go
  classification gate, the walk-away contract's two escalation triggers,
  and a pointer to `build/reference.md`'s pre-cap baton section for long
  `/goal`-bounded runs. Neither `/build` nor the old `/autopilot` ever
  carried `disable-model-invocation: true` — both are, and remain, gated
  by the launch-authorization contract in their SKILL.md's first 30 lines
  (model-invocable only on explicit user authorization in the live
  conversation; only `/evals` carries the hard flag), per the
  post-2026-07-11 boundary in docs/human-gates.md. This fold-in changes
  nothing about that contract: `/build`'s existing first-30-lines
  authorization block is untouched, and the new classification-gate and
  escalation-trigger content added by this requirement lands after it,
  not inside it.
- **R3**: `onboard/SKILL.md:78-79`'s pointer to the scoped-permissions
  template is updated from `autopilot/reference.md` to `build/
reference.md`. `drain/reference.md` has TWO separate `/autopilot`
  mentions, both updated (line numbers are snapshots as of 2026-07-14,
  not a contract — find them by section content, not by re-reading stale
  numbers): `:1007`'s citation of "the autopilot reference's headless
  rule" is updated to cite `build/reference.md`; `:158`'s "Orchestrator
  isolation (default ON)" paragraph ("Build/autopilot worktrees...")
  drops the `/autopilot` mention, the same treatment R6's whole-repo
  sweep gives every other passing reference.
- **R4**: Every skill with a `Next stage:` line naming `/autopilot` gets a
  concrete replacement, not a deletion that leaves it dangling:
  - `gate/SKILL.md` has TWO separate `/autopilot` mentions, not one — its
    closing `Next stage: /autopilot specs/<slug>/tasks/NN-*.md
(human-launched)` becomes `Next stage: /build specs/<slug>/tasks/NN-*.md
(human-launched; /goal-bound it per build/reference.md for an
unattended-feeling run)`; separately, the prose sentence just above
    it ("...with gates in place, tasks qualify for `/autopilot`. Close
    with:") is reworded to "...with gates in place, tasks qualify for an
    unattended `/goal`-bounded `/build` run (or `/drain` for a queue).
    Close with:" — the antigravity mirror's gate workflow has only the
    `Next stage:` line, not this extra sentence, so this second mention
    is a `.claude`-leg-only fix.
  - `breakdown/SKILL.md:166`'s routing sentence recommending `/autopilot`
    "for unattended execution of peripheral tasks" is reworded to
    recommend `/drain` for queue/unattended work and `/build` (optionally
    `/goal`-bounded) for a single task.
- **R5**: `docs/human-gates.md` already reflects the post-2026-07-11
  launch-authorization-contract boundary (one skill, `/evals`, carries
  `disable-model-invocation: true`; the rest are model-invocable only on
  explicit live-conversation authorization) — it does **not** contain a
  stale "Four skills carry `disable-model-invocation`" framing or a
  "gated five" count to correct. Its two remaining `/autopilot` mentions
  are corrected in place (confirmed present as of 2026-07-13; re-verify
  at implementation time with `grep -n autopilot docs/human-gates.md`):
  - The opening list of execution stages model-invocable under the
    launch-authorization contract ("`/build`, `/autopilot`, `/drain`,
    `/prioritize` — are model-invocable since 2026-07-11") drops
    `/autopilot`, becoming "`/build`, `/drain`, `/prioritize`".
  - Reason 2's "`/autopilot` and `/drain` open with ... a classification
    gate" becomes "`/build`'s bounded mode and `/drain` open with ... a
    classification gate".
- **R6**: Every reference to `/autopilot` across all shipped/consumed
  trees — including `codex/` and `antigravity/`, not just the
  `.claude`-leg paths, but excluding `specs/` (planning artifacts,
  re-verified at their own implementation time rather than swept here) —
  is updated or removed, EXCEPT the two real-content mirror files R7/R7a
  handle by deletion+fold-in below (their own paths are excluded from this
  grep-and-reword treatment; they don't get "reworded in place," they stop
  existing). The verifying grep is
  `git grep -ln '\bautopilot\b' -- .claude/ docs/ CLAUDE.md .claude-plugin/ codex/ antigravity/ evals/ runtimes/ README.md AGENTS.md bin/ tests/ agent-console/`
  (tracked files only — a plain recursive `grep -rln` over the same paths
  also matches every transient `.claude/worktrees/agent-*/` drain
  worktree, which is non-deterministic across checkout states; `git grep`
  scopes to tracked content). This path list — not the narrower `.claude/
docs/ CLAUDE.md .claude-plugin/ codex/ antigravity/` set an earlier
  draft of this requirement used — is the actual scope this
  requirement's own prose promises: the narrower set silently excluded
  `evals/`, `runtimes/`, `README.md`, `AGENTS.md`, `bin/`, `tests/`, and
  `agent-console/`, each confirmed today to hold a living `/autopilot`
  reference no earlier round caught (a worker could pass every other AC
  in this spec while leaving all of them stale). Known hits, confirmed
  present today, beyond `.claude/skills/autopilot/{SKILL,reference}.md`,
  `onboard/SKILL.md`, `drain/reference.md`, `gate/SKILL.md`,
  `breakdown/SKILL.md`, `docs/human-gates.md` (handled by R1-R5), and
  `antigravity/.agents/workflows/autopilot.md` /
  `codex/.agents/skills/autopilot/` (handled by R7/R7a below):
  - `docs/external-playbooks.md` (the `/drain`-and-`/autopilot`
    worker-prompt hardening clause, and a citation pointer to autopilot's
    walk-away contract), `docs/decisions/orchestrator-context.md`,
    `docs/decisions/orchestration.md`, `docs/memory/
unattended-worker-tool-limits.md`, `docs/memory/
worktree-base-tracking-ref.md`, `docs/memory/
skill-retirement-checklist.md`, `.claude/skills/fleet/SKILL.md` (its
    frontmatter description's trigger phrase "watch a /drain or /autopilot
    dispatch," and a body mention), `.claude/skills/gate/reference.md`
    ("workers (drain/autopilot dispatch, and the verifier)") — each is
    updated to describe `/build`'s bounded mode where it previously
    described `/autopilot`.
  - `CLAUDE.md` has three separate `/autopilot` mentions, not one: the
    execution-stages doctrine line — its CURRENT text (verify fresh at
    implementation time, this doctrine line has already drifted once)
    reads "Execution stages (`/build`, `/autopilot`, `/drain`,
    `/prioritize`) are model-invocable ONLY on explicit user
    authorization..."; drop `/autopilot` only, leaving "`/build`,
    `/drain`, `/prioritize`" — **not** `/evals`, which this same doctrine
    block explicitly carves out as the one stage that stays
    `disable-model-invocation: true` (never model-invocable) three
    sentences later; adding it to the model-invocable list here would
    corrupt that doctrine — and — a distinct doctrine
    point, easy to miss because it reads as a passing mention rather than
    a rule — the codex-leg authoring convention naming autopilot as one of
    "the four explicit-invocation-only skill wrappers — drain/build/
    autopilot/evals" and "the four `.claude/skills/{drain,build,autopilot,
evals}/SKILL.md` files": both become the **three**-skill set
    (drain/build/evals), reflecting R7a's codex deletion below — this is a
    doctrine change, not a find-and-replace of the word "autopilot".
  - `.claude/skills/resume-handoff/SKILL.md`'s "four gated execution
    stages (`/build`, `/autopilot`, `/drain`, `/prioritize`)" enumeration
    drops `/autopilot`, becoming the three-stage list — a list-membership
    hit, not reworded to "build's bounded mode" (there's nothing to
    reword, autopilot is simply no longer one of the gated stages).
  - `docs/TASKS.md`'s item "`build`, `drain`, and `autopilot` SKILL.md
    files have no `Next stage:` line" drops "and `autopilot`" — the same
    list-membership treatment (autopilot no longer exists to have this
    problem).
  - `docs/memory/multi-runtime-live-testing.md`'s "the disable-model-
    invocation tier: `drain`/`build`/`autopilot`/`evals`" enumeration
    drops `autopilot`, becoming the three-skill set — same treatment as
    CLAUDE.md's codex-convention mentions above (this file documents that
    same convention).
  - `codex/AGENTS.md`, `codex/README.md` (5 mentions: lines 17, 22, 89,
    121, 129 as of this spec's authoring — re-verify at implementation time,
    backstopped either way by AC7's whole-file sweep), `codex/.agents/
skills/drain/SKILL.md`, and `codex/.agents/skills/evals/SKILL.md` all
    name autopilot as one of "the four" launch-gated/real-content codex
    skills — each becomes the three-skill set, mirroring R7a below.
  - `antigravity/README.md` (2 mentions), `antigravity/.agents/skills/
gate/SKILL.md`'s `Next stage:` line, `antigravity/.agents/skills/
resume-handoff/SKILL.md`'s stage enumeration, `antigravity/.agents/
workflows/drain.md`, and `antigravity/.agents/skills/qa-sweep/SKILL.md`
    (its "(build/autopilot/drain/prioritize), so no live-request naming it
    is required" parenthetical — landed after this spec's own authoring,
    via the `qa-sweep-skill-promotion` spec's antigravity mirror; drops
    to the three-stage set the same way) all reference autopilot — each
    updated the same way its `.claude`-leg counterpart is (R3/R4/R5),
    mirroring R7 below. `antigravity/.agents/skills/onboard/SKILL.md` and
    `antigravity/.agents/skills/breakdown/SKILL.md` — the mirrors of the
    two `.claude`-leg files R3 and R4 rework — were checked directly and
    carry no `/autopilot` mention or reworked pointer/routing content to
    begin with, so they need no parallel edit; this is confirmed, not
    assumed.
  - Outside the six trees the earlier draft of this requirement swept,
    confirmed today: `evals/autopilot/01-security-refusal/` (a whole
    evalset directory — `prompt.txt`, `setup.sh`, `assert.sh` — that
    grades an `/autopilot` run; deleted outright, the same "nothing left
    to assert against" treatment R8 gives `/fleet`'s old tests in the
    sibling `retire-static-dashboards` spec — an evalset for a skill that
    no longer exists has no reason to survive). `runtimes/codex.md`'s
    "the four launch-gated skills (`drain`/`build`/`autopilot`/`evals`,
    `allow_implicit_invocation: false`)" becomes the three-skill set,
    the identical doctrine change CLAUDE.md's codex-convention mention
    gets above. `runtimes/README.md`'s two mentions ("the drain and
    autopilot references," "the drain/autopilot headless fallbacks") and
    `runtimes/claude-code.md`'s "the drain and autopilot headless
    fallbacks" (citing `drain/reference.md` as the authoritative copy)
    all reword `autopilot` → `build`, since R1 moves the canonical
    headless template into `build/reference.md`, which is what these
    generic examples should now be citing. `README.md` has four separate
    spots: the pipeline-stage ASCII diagram (line ~20) drops the
    `/autopilot` column entirely; the command-reference table (line ~49)
    loses its `/autopilot` row outright; the launch-authorization
    sentence (line ~85) drops `/autopilot` from the parenthetical stage
    list, same three-skill set as CLAUDE.md/human-gates.md; the
    codex-wrapper paragraph (line ~186) becomes the three-skill set.
    `AGENTS.md`'s `codex/` bullet ("four real-content wrappers
    (drain/build/autopilot/evals)") becomes the three-skill set, same
    treatment as its CLAUDE.md/docs/memory counterparts. `agent-console/
agent-console.py`'s comment citing "the drain/autopilot reference
    docs" rewords to "drain/build" (both now hold the canonical headless
    dispatch documentation this comment points at). `bin/
check-token-discipline`'s `IN_SCOPE` list drops its two
    `.claude/skills/autopilot/{SKILL,reference}.md` lines outright — R1
    deletes both paths, so leaving them in a gate script's scope list
    points the gate at nonexistent files. `tests/
mirror-procedure-manifest.txt`'s source→mirror pairing line
    (`.claude/skills/autopilot/SKILL.md|antigravity/.agents/workflows/
autopilot.md|bounded goal`) is deleted outright — both sides of the
    pairing are removed by R1/R7, so the entry has nothing left to pair.
    A new pairing line is added in its place: `.claude/skills/build/
SKILL.md|antigravity/.agents/workflows/build.md|Two triggers escalate to
a human` — the canary is that literal sentence, not the paraphrase
    "escalation triggers": it's the one line the walk-away contract's
    text actually contains verbatim, unwrapped, in both the `.claude` and
    antigravity autopilot sources today, so it survives R1/R2/R7's
    verbatim move into both `build` legs. R2 and R7 fold the walk-away
    contract's classification gate and escalation triggers into both
    mirror legs, so this is a procedure that _moved_ rather than one that
    disappeared, and
    `.claude/rules/mirror-procedure-discipline.md`'s coverage manifest is
    required to track a moved procedure, not just shrink when one is
    deleted.
    **Exempted**: files that are explicitly historical research dumps or bug
    citations rather than living doctrine — `docs/orchestration-research-
2026-07.md` (a research record), `.claude/rules/
mirror-procedure-discipline.md:55` (cites "the codex-autopilot
    content-swap fix" as a past-incident example, not a description of
    autopilot's current role), `tests/mirror-procedure-manifest.txt`'s
    OTHER `autopilot` mentions beyond the deleted pairing line above (its
    header-comment citing "codex-autopilot's content-swap" and a
    long-form note mentioning "autopilot.md and drain.md do the same" in
    passing while describing an unrelated skill's port — both are
    incident/example citations about other skills' mirror history, not
    descriptions of autopilot's current role), and `tests/
test_check_token_discipline.sh:113`'s comment citing
    `autopilot/reference.md`'s "relaunch clean" rule as a past design
    example — these keep their `/autopilot` mentions
    unchanged; list any file treated as exempt in the implementation's own
    evidence so the exemption is a visible decision, not a silent skip.
- **R7**: `antigravity/.agents/workflows/autopilot.md` — confirmed real
  content (90 lines: classification gate, containment ladder, escalation
  triggers) via direct inspection, not the absent `antigravity/.agents/
skills/autopilot/` the original hedge checked for (autopilot is a
  human-launched execution stage, so per CLAUDE.md's port-chain
  convention it's mirrored as a **workflow**, not a skill — the earlier
  "confirm before implementation" language checked the wrong path and
  concluded no mirror existed, which is wrong) — is deleted; its
  classification-gate and escalation-trigger content, and only what
  actually applies given antigravity's own human-gate model (per
  `antigravity/README.md`'s gotchas), is folded into `antigravity/.agents/
workflows/build.md`, mirroring R1/R2's `.claude`-leg treatment.
- **R7a**: `codex/.agents/skills/autopilot/` — real content per CLAUDE.md's
  codex port-chain convention (`SKILL.md`, 110 lines, plus `agents/
openai.yaml`; confirmed not a symlink) — is deleted; its content is
  folded into `codex/.agents/skills/build/SKILL.md` (codex has no
  `reference.md` pattern the way the `.claude` leg does — everything
  folds into the one SKILL.md file, the same file R7a's codex-doctrine
  fixes in R6 above also touch).
- **R8**: `.claude-plugin/plugin.json`'s `version` is bumped.

## Out of scope

- Any change to `/drain`'s own mechanics — this spec only removes
  autopilot's redundant overlap with it and redirects docs, not `/drain`
  itself.
- Reworking `/build`'s unbounded (default) behavior.
- Migrating in-flight autopilot runs — none expected at merge time; flag
  rather than silently discard if one is found.
- Building any new code path in `/build` to parse a `--goal`/turn-cap
  argument — per Solution, `/goal` is a runtime feature applied _around_
  `/build`'s invocation, not a flag `/build` itself implements.

## Acceptance criteria

- [ ] `.claude/skills/autopilot/` does not exist.
- [ ] `.claude/skills/build/reference.md` exists and contains the six
      named sections (permissions template, `/goal` pattern, containment
      ladder, headless template, pre-cap baton, failure recovery), checked
      per section rather than as one whole-file diff: - Five sections (permissions template, `/goal` pattern, containment
      ladder, headless template, pre-cap baton) move strictly verbatim:
      for each, extract the section's text from
      `git show HEAD:.claude/skills/autopilot/reference.md` by its
      heading and diff it against the corresponding section in
      `build/reference.md` — the diff must be empty. - Failure recovery is exempt from the strict empty-diff check: per
      Solution, it moves into `build/reference.md` _alongside_ the
      walk-away contract's escalation triggers (R2), so its content may
      be adjacent to new material rather than byte-identical in
      isolation — the check is that the failure-recovery doctrine's
      full text is present verbatim somewhere in `build/reference.md`
      (a substring match against the extracted old-reference.md
      section), not that the section boundary is unchanged. - The "background worktree agent" section is exempt from presence
      entirely — confirmed dropped, not moved: `build/reference.md`
      must NOT contain it, only the one-line pointer to `/drain` named
      in Solution.
- [ ] `.claude/skills/build/SKILL.md` contains the classification gate and
      the two escalation triggers, plus a pointer to
      `build/reference.md`'s baton section.
- [ ] `grep -qF 'Two triggers escalate to a human' .claude/skills/build/SKILL.md`
      (pins the literal sentence the mirror-manifest canary at R6/AC below
      depends on: the coverage test skips silently if its _source_ leg
      lacks the phrase, so R2's fold-in must preserve it verbatim, not
      just convey the same meaning in different words).
- [ ] `onboard/SKILL.md` and `drain/reference.md` point at
      `build/reference.md`, not `autopilot/reference.md`.
- [ ] `gate/SKILL.md` and `breakdown/SKILL.md` close with the replacement
      `Next stage:`/routing text named in R4 — neither is left pointing
      at a deleted skill.
- [ ] `docs/human-gates.md`'s opening list of launch-authorization-contract
      stages reads `/build`, `/drain`, `/prioritize` (no `/autopilot`), and
      Reason 2 reads "`/build`'s bounded mode and `/drain`" (no
      `/autopilot`) — `grep -c autopilot docs/human-gates.md` returns 0.
- [ ] `git grep -ln '\bautopilot\b' -- .claude/ docs/ CLAUDE.md .claude-plugin/ codex/ antigravity/ evals/ runtimes/ README.md AGENTS.md bin/ tests/ agent-console/`
      returns exactly the 4 files R6 lists as exempt
      (`docs/orchestration-research-2026-07.md`,
      `.claude/rules/mirror-procedure-discipline.md`,
      `tests/mirror-procedure-manifest.txt`,
      `tests/test_check_token_discipline.sh`) — every other hit has
      either been reworded (R6) or deleted entirely: R1 × `.claude`,
      R7 × antigravity, R7a × codex (`.claude/
skills/autopilot/{SKILL,reference}.md`, `antigravity/.agents/
workflows/autopilot.md`, `codex/.agents/skills/autopilot/SKILL.md`),
      plus R6's own `evals/autopilot/` directory deletion.
      Deliberately NOT gated on a specific tracked-file count (the mirror
      set churns day to day, e.g. it moved 31→32 between this spec's
      authoring and its 2026-07-14 re-critique when qa-sweep's antigravity
      mirror landed) — the exactly-these-4-exempt-files check is the
      robust, count-independent assertion; re-derive the informational
      count at implementation/breakdown time if useful, never pin it.
      (Deterministic across checkout state because it scopes to tracked
      files, unlike a plain recursive `grep -rln` over the same paths,
      which also matches transient `.claude/worktrees/agent-*/` drain
      worktrees.)
- [ ] `antigravity/.agents/workflows/autopilot.md` does not exist, and
      `antigravity/.agents/workflows/build.md` contains the folded-in
      classification-gate and escalation-trigger content that applies
      under antigravity's own human-gate model (R7).
- [ ] `codex/.agents/skills/autopilot/` does not exist, and
      `codex/.agents/skills/build/SKILL.md` contains the folded-in content
      (R7a).
- [ ] `[ ! -d evals/autopilot ]` (R6 — the orphaned evalset for a deleted
      skill is removed, not left grading a nonexistent command).
- [ ] `! grep -q '\.claude/skills/autopilot/SKILL\.md\|\.claude/skills/autopilot/reference\.md' bin/check-token-discipline`
      (R6 — the gate script's `IN_SCOPE` list no longer names either
      deleted path).
- [ ] `! grep -q '^\.claude/skills/autopilot/SKILL\.md|' tests/mirror-procedure-manifest.txt`
      (R6 — the dead source→mirror pairing line is removed; the file's
      other, exempted `autopilot` mentions are unaffected and still
      present, per R6's exemption list).
- [ ] `grep -qF '.claude/skills/build/SKILL.md|antigravity/.agents/workflows/build.md|Two triggers escalate to a human' tests/mirror-procedure-manifest.txt`
      (R6 — the moved-procedure pairing line replaces the deleted
      autopilot→autopilot.md line, so the coverage manifest keeps tracking
      the classification-gate/escalation-trigger procedure once it lives
      in `build`; the canary is the literal unwrapped sentence confirmed
      present in both fold-in sources, not a paraphrase).
- [ ] `grep -c autopilot CLAUDE.md` returns 0, and CLAUDE.md's codex-leg
      authoring convention names the three-skill set (`drain`/`build`/
      `evals`), not four (R6).
- [ ] `grep -qc '`/build`, `/drain`, `/prioritize`' CLAUDE.md && ! grep -qc
'`/build`, `/drain`, `/evals`' CLAUDE.md` — confirms the
      execution-stages doctrine line's model-invocable list reads the
      three-skill set that actually stays model-invocable —
      `/prioritize`, not `/evals` — after `/autopilot` is dropped (R6;
      confirmed both phrases absent today, so this is non-vacuous; a
      worker misreading the stale-quote warning above could otherwise
      corrupt this line to include `/evals`, which this same doctrine
      block elsewhere pins as never model-invocable).
- [ ] `.claude-plugin/plugin.json`'s `version` is higher than before.
- [ ] `bash evals/lint-ultra-gate.sh` exits 0. `.claude/skills/build/
SKILL.md` is one of the four ultra-path skills the script checks
      (`critique`, `drain`, `build`, `idea`); this spec edits it directly
      (R2) and edits `drain/reference.md` (R3), so per CLAUDE.md's
      standalone ultra-gate check this must run and pass before commit —
      run it as part of the implementation's own verification, not only
      relying on a Stop-hook check.
- [ ] **Sequencing**: before this spec's tasks are marked complete, confirm
      `specs/build-doc-currency-check` has no task `in-progress` or merged
      against `build/SKILL.md` concurrently with this spec's own edits to
      that file — check its `SPEC.md`/`tasks/` state directly. If one is
      found, stop and flag it to a human rather than merging around it
      (Problem section's sequencing note; critique-findings.md finding 6).
      `/breakdown` and `/drain` must not auto-decompose or auto-drain both
      specs concurrently against `build/SKILL.md`.
- [ ] **Manual-pending** (not verifiable by an unattended worker — `/build`
      requires live-conversation launch authorization, not something an
      unattended worker holds): a human wraps `/build` against a fixture
      task in `/goal "tests pass, or stop after 5 turns"` and confirms it
      completes within the cap, following the classification gate and
      escalation triggers now documented in `build/SKILL.md` — recorded as
      evidence, not an automated check.

## Open questions

(none)
